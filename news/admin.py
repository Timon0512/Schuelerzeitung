from django.contrib import admin, messages
from django.conf import settings
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.views.decorators.debug import sensitive_post_parameters
from .forms import ArticleForm, EditorialProfileForm, MediaForm
from .models import Article, Author, Category, EditorialProfile, Media, SiteSetting, content_lock
from .services import publish_article, withdraw_article, set_featured, save_editorial, require_publisher, selectable_media
from .uploads import MAX_BYTES, MAX_PIXELS
from .views import private_headers


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleForm
    readonly_fields = ["status", "published_at", "featured"]
    list_display = ["title", "status", "category", "author_names", "last_edited", "lead_mark"]
    list_filter = ["status", "category", "featured"]
    ordering = ["-updated_at", "-pk"]
    list_per_page = 30
    show_facets = admin.ShowFacets.NEVER
    search_fields = ["title", "excerpt", "body_text"]
    prepopulated_fields = {"slug": ("title",)}
    actions = ["publish", "withdraw", "feature"]
    change_form_template = "admin/news/article/change_form.html"
    change_list_template = "admin/editorial_list.html"

    def get_fieldsets(self, request, obj=None):
        media_fields = ["hero_image"]
        if obj is None or self.has_change_permission(request, obj):
            media_fields += ["hero_focus_image", "hero_focus_x", "hero_focus_y", "hero_zoom"]
        return [
            ("Artikelinhalt", {"fields": ["title", "excerpt", "body"], "classes": ["article-writing"]}),
            ("Redaktion", {"fields": [
                *media_fields, "category", "authors",
            ], "classes": ["article-details"]}),
            ("Weitere Einstellungen", {"fields": ["slug", "published_at"], "classes": ["collapse", "article-settings"]}),
        ]

    def get_urls(self):
        return [
            path("add/bilder/", self.admin_site.admin_view(self.media_picker), name="news_article_add_media"),
            path("<int:object_id>/bilder/", self.admin_site.admin_view(self.media_picker), name="news_article_media"),
            path("<int:object_id>/status/", self.admin_site.admin_view(self.article_status), name="news_article_status"),
        ] + super().get_urls()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category").prefetch_related(
            Prefetch("authors", queryset=Author.objects.order_by("display_name", "pk"))
        )

    @admin.display(description="Autorendarstellungen")
    def author_names(self, obj):
        return ", ".join(author.display_name for author in obj.authors.all()) or None

    @admin.display(description="Zuletzt bearbeitet", ordering="updated_at")
    def last_edited(self, obj):
        return localtime(obj.updated_at).strftime("%d.%m.%Y, %H:%M")

    @admin.display(description="Aufmacher", ordering="featured")
    def lead_mark(self, obj):
        return "Aufmacher" if obj.featured else None

    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request, obj, **kwargs)

        class BoundForm(base):
            def __init__(self, *args, **kw):
                kw["user"] = request.user
                kw["publishing"] = request.method == "POST" and "_publish" in request.POST
                super().__init__(*args, **kw)

        return BoundForm

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (not obj or obj.status != "published" or request.user.has_perm("news.can_publish_article"))

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and request.user.has_perm("news.can_publish_article")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = {
            **(extra_context or {}),
            "editor_may_publish": self.has_publish_permission(request),
            "editor_has_media": request.user.has_perm("news.view_media"),
            "editor_may_upload": request.user.has_perm("news.add_media"),
            "editor_upload_bytes": min(MAX_BYTES, settings.IMAGE_MAX_BYTES),
            "editor_upload_megapixels": f"{min(MAX_PIXELS, settings.IMAGE_MAX_PIXELS) / 1_000_000:g}",
        }
        if request.method == "POST":
            if any(name in request.POST for name in ("status", "featured", "published_at", "editor")):
                raise PermissionDenied("Status und Freigabe nur über die vorgesehenen Aktionen ändern.")
            if "_publish" in request.POST and not self.has_publish_permission(request):
                raise PermissionDenied("Die Berechtigung zur Veröffentlichung fehlt.")
            with transaction.atomic():
                content_lock()
                return super().changeform_view(request, object_id, form_url, extra_context)
        return super().changeform_view(request, object_id, form_url, extra_context)

    @method_decorator(sensitive_post_parameters())
    def media_picker(self, request, object_id=None):
        if request.method not in {"GET", "POST"}:
            return HttpResponseNotAllowed(["GET", "POST"])
        if not request.user.has_perm("news.view_media"):
            raise PermissionDenied
        if object_id is None:
            article = None
            if not self.has_add_permission(request):
                raise PermissionDenied
        else:
            article = self.get_object(request, object_id)
            if article is None or not self.has_change_permission(request, article):
                raise PermissionDenied
        if request.method == "POST":
            if not request.user.has_perm("news.add_media"):
                raise PermissionDenied
            if list(request.FILES) != ["file"] or len(request.FILES.getlist("file")) != 1:
                response = JsonResponse({"errors": {"file": ["Bitte genau ein Foto auswählen."]}}, status=400)
            else:
                form = MediaForm(request.POST, request.FILES)
                if form.is_valid():
                    image = form.save(commit=False)
                    image.uploaded_by = request.user
                    image.save()
                    self.log_addition(request, image, "Aus der Artikelbearbeitung hochgeladen.")
                    response = JsonResponse(self.media_item(image), status=201)
                else:
                    errors = {field: list(messages) for field, messages in form.errors.items()}
                    response = JsonResponse({"errors": errors}, status=400)
        else:
            query = request.GET.get("q", "").strip()[:300]
            images = selectable_media(request.user, article)
            if not request.user.has_perm("submissions.view_submission"):
                images = images.filter(submission__isnull=True, submission_origin=False)
            if query:
                images = images.filter(Q(alt_text__icontains=query) | Q(caption__icontains=query))
            page = Paginator(images.order_by("-created_at", "-pk"), 24).get_page(request.GET.get("page", 1))
            response = JsonResponse({
                "images": [self.media_item(image) for image in page],
                "page": page.number,
                "pages": page.paginator.num_pages,
            })
        return private_headers(response)

    @staticmethod
    def media_item(image):
        return {
            "id": str(image.pk),
            "alt": image.alt_text,
            "caption": image.caption,
            "thumb": reverse("private_media_variant", args=[image.pk, "small"]),
            "src": reverse("private_media_variant", args=[image.pk, "large"]),
        }

    def save_model(self, request, obj, form, change):
        save_editorial(
            obj, user=request.user, images=form.cleaned_data["text_images"], authors=form.cleaned_data["authors"]
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if "_publish" in request.POST:
            publish_article(form.instance.pk, user=request.user)
            form.instance.refresh_from_db()
            self.log_change(request, form.instance, "Veröffentlicht")

    def response_add(self, request, obj, post_url_continue=None):
        if "_publish" in request.POST:
            return self.published_response(request, obj)
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if "_publish" in request.POST:
            return self.published_response(request, obj)
        return super().response_change(request, obj)

    def published_response(self, request, obj):
        self.message_user(request, "Der Artikel wurde veröffentlicht.", messages.SUCCESS)
        return redirect("admin:news_article_change", obj.pk)

    def article_status(self, request, object_id):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        if not self.has_publish_permission(request):
            raise PermissionDenied
        operation = {"withdraw": withdraw_article, "feature": set_featured}.get(request.POST.get("editor_action"))
        if operation is None:
            raise PermissionDenied
        with transaction.atomic():
            content_lock()
            queryset = self.get_queryset(request).filter(pk=object_id)
            article = queryset.first()
            if not article or not self.has_change_permission(request, article):
                raise PermissionDenied
            if operation is withdraw_article and article.status != Article.Status.PUBLISHED:
                self.message_user(request, "Der Artikel ist bereits offline.", messages.INFO)
            else:
                self.run_action(request, queryset, operation)
        return redirect("admin:news_article_change", object_id)

    def has_publish_permission(self, request):
        return request.user.has_perm("news.can_publish_article") and request.user.has_perm("news.change_article")

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["editor_public_article"] = bool(obj and not add and Article.objects.public().filter(pk=obj.pk).exists())
        return super().render_change_form(request, context, add, change, form_url, obj)

    def changelist_view(self, request, extra_context=None):
        if request.method == "POST" and request.POST.get("action") in {"publish", "withdraw", "feature"} and not self.has_publish_permission(request):
            raise PermissionDenied("Die Berechtigung zur Veröffentlichung fehlt.")
        return super().changelist_view(request, {**(extra_context or {}), "title": "Artikel"})

    def run_action(self, request, queryset, operation):
        if not self.has_publish_permission(request):
            raise PermissionDenied
        for article in queryset:
            try:
                operation(article.pk, user=request.user)
                self.log_change(request, article, operation.__name__)
                self.message_user(request, f"„{article}“ wurde aktualisiert.", messages.SUCCESS)
            except ValidationError as exc:
                self.message_user(request, f"{article}: {' '.join(exc.messages)}", messages.ERROR)

    @admin.action(description="Veröffentlichen", permissions=["publish"])
    def publish(self, request, queryset):
        self.run_action(request, queryset, publish_article)

    @admin.action(description="Zurückziehen (als Entwurf)", permissions=["publish"])
    def withdraw(self, request, queryset):
        self.run_action(request, queryset, withdraw_article)

    @admin.action(description="Als Aufmacher setzen", permissions=["publish"])
    def feature(self, request, queryset):
        if queryset.count() != 1 or not queryset.public().exists():
            self.message_user(request, "Bitte genau einen bereits sichtbaren Artikel auswählen.", messages.ERROR)
            return
        self.run_action(request, queryset, set_featured)


class ProtectedRelatedAdmin(admin.ModelAdmin):
    """Editing shared live metadata would otherwise bypass publication approval."""
    def is_live(self, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (not obj or not self.is_live(obj) or request.user.has_perm("news.can_publish_article"))

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST":
            with transaction.atomic():
                content_lock()
                return super().changeform_view(request, object_id, form_url, extra_context)
        return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if change and self.is_live(obj):
            require_publisher(request.user)
        super().save_model(request, obj, form, change)


@admin.register(Media)
class MediaAdmin(ProtectedRelatedAdmin):
    form = MediaForm
    list_display = ["thumbnail", "alt_text", "caption", "created_at", "width", "height"]
    list_display_links = ["thumbnail", "alt_text"]
    ordering = ["-created_at", "-pk"]
    list_per_page = 30
    change_list_template = "admin/editorial_list.html"
    search_fields = ["alt_text", "caption"]
    fields = ["file", "alt_text", "caption", "preview", "width", "height", "size"]
    readonly_fields = ["preview", "width", "height", "size"]

    def get_queryset(self, request):
        images = super().get_queryset(request)
        if not request.user.has_perm("submissions.view_submission"):
            return images.filter(submission_origin=False, submission__isnull=True)
        return images

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, {**(extra_context or {}), "title": "Bilder"})

    @admin.display(description="Foto")
    def thumbnail(self, obj):
        return format_html(
            '<img class="admin-thumbnail" src="{}" alt="" loading="lazy" width="68" height="48">',
            reverse("private_media_variant", args=[obj.pk, "small"]),
        )

    def is_live(self, obj):
        return (
            obj.hero_articles.filter(status="published").exists()
            or obj.articles.filter(status="published").exists()
            or obj.editorial_profiles.exists()
            or SiteSetting.objects.filter(logo=obj).exists()
        )

    @admin.display(description="Bildansicht")
    def preview(self, obj):
        if not obj.file:
            return "Nach dem Speichern verfügbar"
        return format_html(
            '<img class="admin-photo-preview" src="{}" alt="{}"><br><a href="{}" target="_blank" rel="noopener">Bild geschützt öffnen</a>',
            reverse("private_media_variant", args=[obj.pk, "large"]), obj.alt_text, reverse("private_media", args=[obj.pk]),
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Author)
class AuthorAdmin(ProtectedRelatedAdmin):
    fields = ["display_name", "slug", "bio", "is_public"]
    list_display = ["display_name", "is_public"]
    prepopulated_fields = {"slug": ("display_name",)}
    def is_live(self, obj):
        return obj.articles.filter(status="published").exists()


@admin.register(Category)
class CategoryAdmin(ProtectedRelatedAdmin):
    list_display = ["name", "sort_order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}

    def is_live(self, obj):
        return obj.article_set.filter(status="published").exists()


@admin.register(SiteSetting)
class SiteSettingAdmin(ProtectedRelatedAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "logo":
            kwargs["queryset"] = Media.objects.filter(submission__isnull=True, submission_origin=False)
            kwargs["help_text"] = "Dieses Logo wird öffentlich ausgeliefert. Private Einsendungsbilder sind ausgeschlossen."
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def is_live(self, obj):
        return True

    def has_add_permission(self, request):
        return super().has_add_permission(request) and request.user.has_perm("news.can_publish_article")


@admin.register(EditorialProfile)
class EditorialProfileAdmin(ProtectedRelatedAdmin):
    form = EditorialProfileForm

    def is_live(self, obj):
        return True

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            and request.user.has_perm("news.can_publish_article")
            and not EditorialProfile.objects.exists()
        )
