import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("news", "0006_editorial_profile_and_article_authors")]

    operations = [
        migrations.AddField(
            model_name="article",
            name="hero_zoom",
            field=models.PositiveSmallIntegerField(
                default=100,
                validators=[django.core.validators.MinValueValidator(100), django.core.validators.MaxValueValidator(300)],
                verbose_name="Zoom (%)",
            ),
        ),
        migrations.AddConstraint(
            model_name="article",
            constraint=models.CheckConstraint(condition=models.Q(hero_zoom__range=(100, 300)), name="article_zoom_bounds"),
        ),
    ]
