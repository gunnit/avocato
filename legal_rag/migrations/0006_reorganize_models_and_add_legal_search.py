# Generated by Django 4.2 on 2024-12-28 17:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0013_alter_documentaryevidence_extracted_text'),
        ('legal_rag', '0005_alter_pdfanalysisresult_caso'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalSearchResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('search_query', models.JSONField(help_text='The case details used for the search')),
                ('search_results', models.JSONField(help_text='The complete search results from all sources')),
                ('search_strategy', models.JSONField(help_text='The strategy used for the search')),
                ('date_saved', models.DateTimeField(auto_now_add=True)),
                ('caso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legal_search_results', to='cases.caso')),
            ],
            options={
                'verbose_name': 'Risultato Ricerca Legale',
                'verbose_name_plural': 'Risultati Ricerche Legali',
                'ordering': ['-date_saved'],
            },
        ),
    ]