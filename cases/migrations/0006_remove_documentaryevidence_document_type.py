# Generated by Django 4.2 on 2024-11-22 22:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0005_add_document_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentaryevidence',
            name='document_type',
        ),
    ]