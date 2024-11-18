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
