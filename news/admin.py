from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html
from .forms import ArticleForm, MediaForm
from .models import Article, Author, Category, Media, SiteSetting, content_lock
from .services import publish_article, withdraw_article, set_featured, save_editorial, require_publisher


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleForm
    fields = ArticleForm.Meta.fields + ["status", "published_at", "featured"]
    readonly_fields = ["status", "published_at", "featured"]
    list_display = ["title", "category", "author", "status", "published_at", "featured"]
    list_filter = ["status", "category", "featured"]
    search_fields = ["title", "excerpt", "body_text"]
    prepopulated_fields = {"slug": ("title",)}
    actions = ["publish", "withdraw", "feature"]
    change_form_template = "admin/news/article/change_form.html"

    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request, obj, **kwargs)
        class BoundForm(base):
            def __init__(self, *args, **kw):
                kw["user"] = request.user
                super().__init__(*args, **kw)
        return BoundForm

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (not obj or obj.status != "published" or request.user.has_perm("news.can_publish_article"))

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and request.user.has_perm("news.can_publish_article")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST":
            if any(name in request.POST for name in ("status", "featured", "published_at", "editor")):
                raise PermissionDenied("Status und Freigabe nur über die vorgesehenen Aktionen ändern.")
            with transaction.atomic():
                content_lock()
                return super().changeform_view(request, object_id, form_url, extra_context)
        return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        save_editorial(obj, user=request.user, images=form.cleaned_data["text_images"])

    def has_publish_permission(self, request):
        return request.user.has_perm("news.can_publish_article") and request.user.has_perm("news.change_article")

    def changelist_view(self, request, extra_context=None):
        if request.method == "POST" and request.POST.get("action") in {"publish", "withdraw", "feature"} and not self.has_publish_permission(request):
            raise PermissionDenied("Die Berechtigung zur Veröffentlichung fehlt.")
        return super().changelist_view(request, extra_context)

    def run_action(self, request, queryset, operation):
        if not self.has_publish_permission(request):
            raise PermissionDenied
        for article in queryset:
            try:
                operation(article.pk, user=request.user)
                self.log_change(request, article, operation.__name__)
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
    list_display = ["alt_text", "caption", "created_at", "width", "height"]
    search_fields = ["alt_text", "caption"]
    fields = ["file", "alt_text", "caption", "preview", "width", "height", "size"]
    readonly_fields = ["preview", "width", "height", "size"]

    def is_live(self, obj):
        return obj.hero_articles.filter(status="published").exists() or obj.articles.filter(status="published").exists() or SiteSetting.objects.filter(logo=obj).exists()

    @admin.display(description="Bildansicht")
    def preview(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener">Bild geschützt öffnen</a>', reverse("private_media", args=[obj.pk])) if obj.pk else "Nach dem Speichern verfügbar"

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
            kwargs["queryset"] = Media.objects.filter(submission__isnull=True)
            kwargs["help_text"] = "Dieses Logo wird öffentlich ausgeliefert. Private Einsendungsbilder sind ausgeschlossen."
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def is_live(self, obj):
        return True

    def has_add_permission(self, request):
        return super().has_add_permission(request) and request.user.has_perm("news.can_publish_article")
