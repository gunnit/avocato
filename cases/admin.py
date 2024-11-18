from django.contrib import admin
from .models import Caso, ChatMessage, DocumentaryEvidence

@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'data_creazione', 'stato')
    search_fields = ('titolo', 'descrizione')
    list_filter = ('stato',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('caso', 'is_ai', 'timestamp')
    list_filter = ('is_ai', 'timestamp')
    search_fields = ('content',)

@admin.register(DocumentaryEvidence)
class DocumentaryEvidenceAdmin(admin.ModelAdmin):
    list_display = ('caso', 'exhibit_number', 'title', 'authentication_status', 'date_added')
    list_filter = ('authentication_status', 'date_added')
    search_fields = ('title', 'description')
    ordering = ('caso', 'exhibit_number')
