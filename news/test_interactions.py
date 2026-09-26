"""Run only with the guarded, disposable PostgreSQL test database."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, Client, RequestFactory, override_settings
from django.utils import timezone
from news.models import Article, Author, Category, Media
from news.services import publish_article, withdraw_article, selectable_media
from reactions.limits import consume_attempt
from reactions.models import Reaction, RateLimitWindow
from reactions.services import toggle_heart, token_hash
from submissions.models import Submission
from submissions.services import convert_submission


class InteractionTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.directory.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.category = Category.objects.create(name='Schule', slug='schule')
        self.article = Article.objects.create(title='Artikel', slug='artikel', category=self.category, status='published')

    def data(self, **extra):
        return dict(name='Privater Testname', class_level='8b', title='Eingereichter Text',
                    category=self.category.pk, body='Nur Klartext <script>test</script>', authorship_confirmed='on', **extra)

    def image(self):
        data = BytesIO()
        Image.new('RGB', (12,8), 'orange').save(data, 'PNG')
        return SimpleUploadedFile('test.png', data.getvalue(), 'image/png')

    def test_submission_receipt_private_storage_and_refresh(self):
        response = self.client.post('/artikel-einreichen', self.data(image=self.image()), follow=True)
        self.assertContains(response, 'Dein Beitrag ist angekommen')
        self.assertNotContains(self.client.get('/artikel-einreichen'), 'Dein Beitrag ist angekommen')
        submission = Submission.objects.get()
        self.assertEqual(submission.status, 'new')
        self.assertTrue(submission.image.submission_origin)
        self.assertEqual(submission.image.mime_type, 'image/webp')
        self.assertEqual(self.client.get(f'/medien/{submission.image_id}').status_code, 404)
        self.assertEqual(Submission.objects.count(), 1)

    def test_invalid_fields_file_honeypot_and_category_do_not_write(self):
        inactive = Category.objects.create(name='Inaktiv',slug='inaktiv',is_active=False)
        cases = [self.data(website='bot'), {**self.data(), 'title':'x'*201},
                 {**self.data(), 'category':inactive.pk}, self.data(image=SimpleUploadedFile('fake.png', b'<svg/>')),
                 {**self.data(), 'authorship_confirmed':''}]
        for data in cases:
            response = self.client.post('/artikel-einreichen', data)
            self.assertEqual(response.status_code,400)
            self.assertContains(response, 'Privater Testname', status_code=400)
            self.assertNotContains(response, 'Dein Beitrag ist angekommen', status_code=400)
        self.assertFalse(Submission.objects.exists())
        self.assertFalse(Media.objects.exists())
        self.assertFalse(list(Path(self.directory.name).rglob('*.webp')))

    def test_csrf_and_rate_limits_count_failed_attempts(self):
        csrf = Client(enforce_csrf_checks=True)
        self.assertEqual(csrf.post('/artikel-einreichen', self.data()).status_code,403)
        csrf.get('/artikel-einreichen')
        token = csrf.cookies['csrftoken'].value
        self.assertEqual(csrf.post('/artikel-einreichen', self.data(), HTTP_X_CSRFTOKEN=token).status_code,302)
        for _ in range(3):
            self.assertEqual(csrf.post('/artikel-einreichen', {}).status_code,403)
        response = csrf.post('/artikel-einreichen', self.data(), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,429)
        self.assertTrue(int(response['Retry-After']) > 0)
        self.assertEqual(Submission.objects.count(),1)

    def test_heart_toggle_cookie_csrf_and_visibility(self):
        csrf = Client(enforce_csrf_checks=True)
        page = csrf.get('/artikel/artikel')
        cookie = csrf.cookies['kaktus_visitor'].value
        self.assertContains(page, 'aria-pressed="false"')
        self.assertEqual(csrf.post('/artikel/artikel/herz').status_code,403)
        headers = {'HTTP_X_CSRFTOKEN':csrf.cookies['csrftoken'].value}
        first = csrf.post('/artikel/artikel/herz', **headers, follow=True)
        self.assertContains(first, 'aria-pressed="true"')
        self.assertEqual(Reaction.objects.get().visitor_token_hash, token_hash(cookie))
        self.assertEqual(csrf.post('/artikel/artikel/herz', **headers).status_code,302)
        self.assertFalse(Reaction.objects.exists())
        self.assertEqual(Client().post('/artikel/artikel/herz').status_code,400)
        self.assertEqual(csrf.get('/artikel/artikel/herz').status_code,405)
        self.article.status='draft'
        self.article.save()
        self.assertEqual(csrf.post('/artikel/artikel/herz', **headers).status_code,404)

    @override_settings(HEART_RATE_LIMIT=2)
    def test_heart_limit(self):
        self.client.get('/artikel/artikel')
        for _ in range(2):
            self.assertEqual(self.client.post('/artikel/artikel/herz').status_code,302)
        self.assertEqual(self.client.post('/artikel/artikel/herz').status_code,429)
        self.assertFalse(Reaction.objects.exists())

    def test_seven_day_boundary_ties_limit_and_removal(self):
        now = timezone.now()
        articles=[]
        for index in range(7):
            article = Article.objects.create(title=str(index),slug=f'rank-{index}',category=self.category,
                status='published',published_at=now-timedelta(hours=index))
            reaction=Reaction.objects.create(article=article,visitor_token_hash='a'*64)
            Reaction.objects.filter(pk=reaction.pk).update(created_at=now-timedelta(days=7))
            articles.append(article)
        old=Reaction.objects.create(article=self.article,visitor_token_hash='b'*64)
        Reaction.objects.filter(pk=old.pk).update(created_at=now-timedelta(days=7,microseconds=1))
        with patch('news.public.timezone.now',return_value=now):
            ranked=list(self.client.get('/').context['popular'])
        self.assertEqual([a.pk for a in ranked],[a.pk for a in articles[:5]])
        Reaction.objects.filter(article=articles[0]).delete()
        with patch('news.public.timezone.now',return_value=now):
            self.assertNotIn(articles[0],list(self.client.get('/').context['popular']))

    def test_full_submission_editorial_workflow(self):
        self.client.post('/artikel-einreichen',self.data(image=self.image()))
        submission=Submission.objects.get()
        user=get_user_model().objects.create_superuser('workflow',password='test-only-password')
        self.client.force_login(user)
        admin='/admin/submissions/submission/'
        self.client.post(admin,{'action':'review','_selected_action':submission.pk})
        submission.refresh_from_db()
        self.assertEqual(submission.status,'in_review')
        self.client.post(admin,{'action':'convert','_selected_action':submission.pk})
        submission.refresh_from_db()
        article=submission.article
        self.assertEqual(convert_submission(submission.pk,user=user).pk,article.pk)
        self.assertIsNone(article.author_id)
        author=Author.objects.create(display_name='Redaktion',slug='redaktion',is_public=True)
        image=submission.image
        image.alt_text='Ein Testbild'
        image.save()
        data={'title':'Geprüfter Beitrag','slug':article.slug,'category':self.category.pk,
              'author':author.pk,'hero_image':str(image.pk),'body':'<p>Redigierter Text</p>','_save':'Speichern'}
        self.assertEqual(self.client.post(f'/admin/news/article/{article.pk}/change/',data).status_code,302)
        preview=self.client.post('/redaktion/vorschau',{**data,'article_id':article.pk})
        self.assertContains(preview,'Redigierter Text')
        self.assertIn('no-store',preview['Cache-Control'])
        publish_article(article.pk,user=user)
        anonymous=Client()
        self.assertContains(anonymous.get('/artikel/'+article.slug),'Geprüfter Beitrag')
        response=anonymous.get(f'/medien/{image.pk}')
        self.assertEqual(response.status_code,200)
        response.close()
        withdraw_article(article.pk,user=user)
        self.assertEqual(anonymous.get('/artikel/'+article.slug).status_code,404)
        self.assertEqual(anonymous.get(f'/medien/{image.pk}').status_code,404)

    @override_settings(SUBMISSION_RETENTION_DAYS=30,REACTION_RETENTION_DAYS=30,RETENTION_CONFIRMED=True)
    def test_retention_preview_removes_private_file_preserves_converted_image(self):
        user=get_user_model().objects.create_superuser('retention',password='test-only-password')
        for _ in range(2):
            self.client.post('/artikel-einreichen',self.data(image=self.image()))
        first, second=list(Submission.objects.order_by('pk'))
        article=convert_submission(first.pk,user=user)
        retained=first.image.file.path
        removed=second.image.file.path
        Submission.objects.all().update(submitted_at=timezone.now()-timedelta(days=31))
        out=StringIO()
        call_command('purge_interactions',stdout=out)
        self.assertIn('2 Einsendungen',out.getvalue())
        self.assertEqual(Submission.objects.count(),2)
        with self.captureOnCommitCallbacks(execute=True):
            call_command('purge_interactions',execute=True,stdout=StringIO())
        self.assertFalse(Submission.objects.exists())
        self.assertTrue(Path(retained).exists())
        self.assertFalse(Path(removed).exists())
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())
        self.assertTrue(Media.objects.get(pk=first.image_id).submission_origin)
        self.assertFalse(selectable_media(user).filter(pk=first.image_id).exists())
        self.assertTrue(selectable_media(user,article).filter(pk=first.image_id).exists())


class ConcurrentInteractionTests(TransactionTestCase):
    def parallel(self, fn):
        barrier=Barrier(2)
        def worker():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return fn()
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(worker) for _ in range(2)]
            return [future.result(timeout=20) for future in futures]

    def test_parallel_heart_clicks_serialize(self):
        category=Category.objects.create(name='Test',slug='test')
        article=Article.objects.create(title='Test',slug='test',category=category,status='published')
        self.parallel(lambda: toggle_heart('test','a'*43))
        self.assertEqual(Reaction.objects.filter(article=article).count(),0)

    @override_settings(HEART_RATE_LIMIT=1)
    def test_parallel_limit_and_expiry(self):
        request=RequestFactory().post('/artikel/test/herz',REMOTE_ADDR='192.0.2.1')
        results=self.parallel(lambda: consume_attempt(request,'heart')[0])
        self.assertEqual(sorted(results),[False,True])
        old_key=RateLimitWindow.objects.get().key
        later=timezone.now()+timedelta(seconds=61)
        with patch('reactions.limits.timezone.now',return_value=later):
            self.assertTrue(consume_attempt(request,'heart')[0])
        self.assertFalse(RateLimitWindow.objects.filter(pk=old_key).exists())
