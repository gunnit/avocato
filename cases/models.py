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
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='documentary_evidences')
    exhibit_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    document_file = models.FileField(upload_to='documentary_evidences/')
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
