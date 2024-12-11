from django.db import models


class Caso(models.Model):
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField()
    data_creazione = models.DateTimeField(auto_now_add=True)
    analisi_ai = models.TextField(blank=True)
    riferimenti_legali = models.TextField(blank=True)
    stato = models.CharField(max_length=50)

    def __str__(self):
        return self.titolo

    @property
    def documenti_count(self):
        return self.documentary_evidences.count()

    @property
    def messaggi_count(self):
        return self.chat_messages.count()

    @property
    def progresso(self):
        if self.stato == 'Completato':
            return 100
        elif self.stato == 'In corso':
            return 50
        return 0

    class Meta:
        verbose_name = 'Caso'
        verbose_name_plural = 'Casi'


class ChatMessage(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField()
    is_ai = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{'AI' if self.is_ai else 'User'} message for {self.caso.titolo}"


class DocumentaryEvidence(models.Model):
    DOCUMENT_TYPE_CHOICES = [
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
    ]

    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='documentary_evidences')
    exhibit_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    document_file = models.FileField(upload_to='documentary_evidences/')
    document_type = models.CharField(
        max_length=100,
        choices=DOCUMENT_TYPE_CHOICES,
        default='altro',
        verbose_name='Tipo Documento'
    )
    authentication_status = models.CharField(max_length=50, choices=[
        ('pending', 'In attesa di autenticazione'),
        ('authenticated', 'Autenticato'),
        ('not_required', 'Autenticazione non necessaria')
    ], default='pending')
    authentication_notes = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    ai_analysis_json = models.JSONField(blank=True, null=True)
    ai_analysis_text = models.TextField(blank=True)

    class Meta:
        ordering = ['exhibit_number']
        unique_together = ['caso', 'exhibit_number']
        verbose_name = 'Produzione Documentale'
        verbose_name_plural = 'Produzioni Documentali'

    def __str__(self):
        return f"Doc. {self.exhibit_number} - {self.title}"


class StudioLegale(models.Model):
    SPECIALIZATION_CHOICES = [
        ('civile', 'Diritto Civile'),
        ('penale', 'Diritto Penale'),
        ('amministrativo', 'Diritto Amministrativo'),
        ('lavoro', 'Diritto del Lavoro'),
        ('famiglia', 'Diritto di Famiglia'),
        ('societario', 'Diritto Societario'),
        ('tributario', 'Diritto Tributario'),
        ('immobiliare', 'Diritto Immobiliare')
    ]

    nome = models.CharField(max_length=200, verbose_name='Nome Studio')
    logo = models.ImageField(upload_to='studio_logos/', blank=True, null=True)
    indirizzo = models.CharField(max_length=200)
    citta = models.CharField(max_length=100)
    cap = models.CharField(max_length=10)
    provincia = models.CharField(max_length=2)
    paese = models.CharField(max_length=100, default='Italia')
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    fax = models.CharField(max_length=20, blank=True)
    specializzazioni = models.JSONField(default=list)

    # AI Settings
    ai_suggestions_enabled = models.BooleanField(default=True, verbose_name='Suggerimenti IA')
    ai_analysis_enabled = models.BooleanField(default=True, verbose_name='Analisi Automatica')
    ai_templates_enabled = models.BooleanField(default=True, verbose_name='Generazione Modelli')

    data_creazione = models.DateTimeField(auto_now_add=True)
    data_modifica = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Studio Legale'
        verbose_name_plural = 'Studi Legali'

    def __str__(self):
        return self.nome
