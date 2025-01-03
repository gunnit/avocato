# Generated by Django 4.2 on 2024-12-25 15:32

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0013_alter_documentaryevidence_extracted_text'),
        ('legal_rag', '0003_savedsearchresult'),
    ]

    operations = [
        migrations.CreateModel(
            name='PDFAnalysisResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_file', models.FileField(upload_to='pdf_analysis/')),
                ('filename', models.CharField(max_length=255)),
                ('extracted_text', models.TextField(blank=True)),
                ('structured_content', models.JSONField(default=dict)),
                ('content_chunks', models.JSONField(default=dict)),
                ('processing_type', models.CharField(max_length=50)),
                ('dati_generali', models.JSONField(default=dict)),
                ('informazioni_legali_specifiche', models.JSONField(default=dict)),
                ('dati_processuali', models.JSONField(default=dict)),
                ('analisi_linguistica', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('processing_completed', models.BooleanField(default=False)),
                ('analysis_completed', models.BooleanField(default=False)),
                ('trace_id', models.CharField(blank=True, max_length=100)),
                ('caso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pdf_analyses', to='cases.caso')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
