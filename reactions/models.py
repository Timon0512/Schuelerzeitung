from django.core.validators import RegexValidator
from django.db import models


class Reaction(models.Model):
    article = models.ForeignKey("news.Article", on_delete=models.CASCADE, related_name="reactions")
    visitor_token_hash = models.CharField(max_length=64, validators=[RegexValidator(r"^[0-9a-f]{64}$")])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["article", "visitor_token_hash"], name="one_heart_per_browser_article"),
            models.CheckConstraint(condition=models.Q(visitor_token_hash__regex=r"^[0-9a-f]{64}$"), name="reaction_sha256_hash"),
        ]
        indexes = [models.Index(fields=["created_at", "article"])]
