from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0003_documentaryevidence'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentaryevidence',
            name='ai_analysis_json',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='documentaryevidence',
            name='ai_analysis_text',
            field=models.TextField(blank=True),
        ),
    ]
