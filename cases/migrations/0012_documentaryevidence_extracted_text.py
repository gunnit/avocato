from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0011_add_data_modifica'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentaryevidence',
            name='extracted_text',
            field=models.TextField(blank=True, null=True, verbose_name='Testo Estratto'),
        ),
    ]
