# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0004_add_ai_analysis_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentaryevidence',
            name='document_type',
            field=models.CharField(
                max_length=100,
                choices=[
                    ('atto_citazione', 'Atto di Citazione'),
                    ('comparsa_costituzione', 'Comparsa di Costituzione'),
                    ('memoria_183', 'Memoria ex art. 183'),
                    ('doc_contabili', 'Documenti Contabili'),
                    ('perizia_tecnica', 'Perizia Tecnica'),
                    ('corrispondenza', 'Corrispondenza'),
                    ('contratto', 'Contratto'),
                    ('doc_amministrativo', 'Documento Amministrativo'),
                    ('verbale', 'Verbale'),
                    ('sentenza', 'Sentenza'),
                    ('altro', 'Altro')
                ],
                default='altro',
                verbose_name='Tipo Documento'
            ),
        ),
    ]
