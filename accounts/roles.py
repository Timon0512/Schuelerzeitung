def ensure_roles(sender=None, using="default", **kwargs):
    from django.contrib.auth.management import create_permissions
    from django.apps import apps
    from django.contrib.auth.models import Group, Permission
    for label in ("news", "submissions", "reactions"):
        create_permissions(apps.get_app_config(label), verbosity=0, using=using)
    allowed = {
        "news": {f"{action}_{model}" for action in ("view", "add", "change")
                 for model in ("article", "author", "media", "articlemedia")} | {"view_category"},
        "submissions": {"view_submission", "change_submission"},
    }
    permissions = list(Permission.objects.using(using).select_related("content_type"))
    editorial = [p for p in permissions if p.codename in allowed.get(p.content_type.app_label, set())]
    for name, publish in (("Redaktion", False), ("Veröffentlichung", True)):
        group, _ = Group.objects.using(using).get_or_create(name=name)
        group.permissions.set(editorial + ([p for p in permissions if p.content_type.app_label == "news"
                                           and p.codename == "can_publish_article"] if publish else []))
