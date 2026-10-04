from django.db import migrations, models


def rename_publication(apps, schema_editor):
    SiteSetting = apps.get_model("news", "SiteSetting")
    SiteSetting.objects.using(schema_editor.connection.alias).filter(
        publication_name__iexact="Kaktus"
    ).update(publication_name="Schulgeflüster")


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0004_article_hero_focus_x_article_hero_focus_y_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesetting",
            name="publication_name",
            field=models.CharField(
                "Zeitungsname", max_length=80, default="Schulgeflüster"
            ),
        ),
        migrations.RunPython(rename_publication, migrations.RunPython.noop),
    ]
