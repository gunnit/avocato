# Generated by Django 4.2 on 2024-11-18 21:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0002_chatmessage'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentaryEvidence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exhibit_number', models.IntegerField()),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('document_file', models.FileField(upload_to='documentary_evidences/')),
                ('authentication_status', models.CharField(choices=[('pending', 'In attesa di autenticazione'), ('authenticated', 'Autenticato'), ('not_required', 'Autenticazione non necessaria')], default='pending', max_length=50)),
                ('authentication_notes', models.TextField(blank=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('caso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentary_evidences', to='cases.caso')),
            ],
            options={
                'verbose_name': 'Produzione Documentale',
                'verbose_name_plural': 'Produzioni Documentali',
                'ordering': ['exhibit_number'],
                'unique_together': {('caso', 'exhibit_number')},
            },
        ),
    ]
