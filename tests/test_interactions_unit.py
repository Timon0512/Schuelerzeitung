"""Database-free public interaction boundaries; PostgreSQL behavior is tested separately."""
from tests import test_configuration  # Configure Django without opening a database.
from io import BytesIO, StringIO
from unittest.mock import patch
from django.test import SimpleTestCase, RequestFactory, override_settings
from django.http import HttpResponse
from django.core.management import call_command, CommandError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from config.interaction_limits import InteractionLimitMiddleware
from reactions.limits import client_ip, window_key
from reactions.services import ensure_cookie, visitor_token, token_hash
from news.submission_ui import SubmissionUIForm
from news.uploads import decode_image


class InteractionUnitTests(SimpleTestCase):
    def test_untrusted_proxy_cannot_spoof_ip(self):
        request = RequestFactory().post('/', REMOTE_ADDR='192.0.2.7', HTTP_X_FORWARDED_FOR='203.0.113.8')
        self.assertEqual(client_ip(request), '192.0.2.7')
        with override_settings(TRUSTED_PROXY_NETWORKS=['192.0.2.0/24']):
            self.assertEqual(client_ip(request), '203.0.113.8')
            request.META['HTTP_X_FORWARDED_FOR'] = 'forged, 203.0.113.9, 192.0.2.8'
            self.assertEqual(client_ip(request), '203.0.113.9')
            request.META['HTTP_X_FORWARDED_FOR'] = 'invalid'
            self.assertEqual(client_ip(request), 'unknown')

    def test_window_hash_rotates_and_separates_actions(self):
        key = window_key('192.0.2.7', 'heart', 1)
        self.assertEqual(len(key), 64)
        self.assertNotIn('192.0.2.7', key)
        self.assertNotEqual(key, window_key('192.0.2.7', 'heart', 2))
        self.assertNotEqual(key, window_key('192.0.2.7', 'submission', 1))

    def test_cookie_is_random_httponly_and_secure_in_production(self):
        request = RequestFactory().get('/')
        with override_settings(HEART_COOKIE_SECURE=True):
            response = ensure_cookie(request, HttpResponse())
        cookie = response.cookies['kaktus_visitor']
        self.assertEqual(len(cookie.value), 43)
        self.assertTrue(cookie['secure'])
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Lax')
        request.COOKIES['kaktus_visitor'] = cookie.value
        self.assertEqual(visitor_token(request), cookie.value)
        self.assertNotEqual(token_hash(cookie.value), cookie.value)
        self.assertFalse(ensure_cookie(request, HttpResponse()).cookies)
        request.COOKIES['kaktus_visitor'] = 'invalid'
        self.assertIsNone(visitor_token(request))

    def test_request_size_and_rate_limit_precede_parsing(self):
        middleware = InteractionLimitMiddleware(lambda request: HttpResponse('ok'))
        with patch('config.interaction_limits.consume_attempt', return_value=(True, 60)) as consume:
            with override_settings(SUBMISSION_REQUEST_BYTES=4):
                request = RequestFactory().post('/artikel-einreichen', '12345', content_type='text/plain')
                self.assertEqual(middleware(request).status_code, 413)
            consume.assert_called_once()
            with override_settings(INTERACTION_MAX_FIELDS=1):
                self.assertEqual(middleware(RequestFactory().post('/artikel-einreichen', {'a':'1','b':'2'})).status_code, 400)
        with patch('config.interaction_limits.consume_attempt', return_value=(False, 42)):
            response = middleware(RequestFactory().post('/artikel/a/herz'))
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response['Retry-After'], '42')

    def test_bounded_read_without_length_and_normal_multipart(self):
        middleware = InteractionLimitMiddleware(lambda request: HttpResponse(request.POST.get('name', '')))
        with patch('config.interaction_limits.consume_attempt', return_value=(True, 60)):
            request = RequestFactory().post('/artikel-einreichen', {'name': 'Test'})
            self.assertEqual(middleware(request).content, b'Test')
            request = RequestFactory().post('/artikel-einreichen', '12345', content_type='text/plain')
            request.META.pop('CONTENT_LENGTH')
            with override_settings(SUBMISSION_REQUEST_BYTES=4):
                self.assertEqual(middleware(request).status_code, 413)

    def test_field_limits_honeypot_and_invalid_image(self):
        form = SubmissionUIForm()
        for field, size in [('name',120),('class_level',40),('title',200),('body',50000)]:
            with self.assertRaises(ValidationError):
                form.fields[field].clean('x' * (size + 1))
        form.cleaned_data = {'website': 'bot'}
        with self.assertRaises(ValidationError):
            form.clean_website()
        form.cleaned_data = {'image': SimpleUploadedFile('fake.png', b'<svg/>')}
        with self.assertRaises(ValidationError):
            form.clean_image()
        with override_settings(SUBMISSION_TITLE_LIMIT=20):
            self.assertEqual(SubmissionUIForm().fields['title'].max_length, 20)

    @override_settings(RETENTION_CONFIRMED=False, SUBMISSION_RETENTION_DAYS=30)
    def test_retention_cannot_execute_without_confirmation(self):
        with self.assertRaises(CommandError):
            call_command('purge_interactions', execute=True, stdout=StringIO())
