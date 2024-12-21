from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0010_alter_documentaryevidence_document_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='caso',
            name='data_modifica',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
