# Generated by Django 4.2 on 2024-11-22 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0006_remove_documentaryevidence_document_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentaryevidence',
            name='document_type',
            field=models.CharField(choices=[('atto_citazione', 'Atto di Citazione'), ('comparsa_costituzione', 'Comparsa di Costituzione'), ('memoria_183', 'Memoria ex art. 183'), ('doc_contabili', 'Documenti Contabili'), ('perizia_tecnica', 'Perizia Tecnica'), ('corrispondenza', 'Corrispondenza'), ('contratto', 'Contratto'), ('doc_amministrativo', 'Documento Amministrativo'), ('verbale', 'Verbale'), ('sentenza', 'Sentenza'), ('altro', 'Altro')], default='altro', max_length=100, verbose_name='Tipo Documento'),
        ),
    ]
