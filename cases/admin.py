from django.contrib import admin
from .models import Caso

@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'data_creazione', 'stato')
    list_filter = ('stato', 'data_creazione')
    search_fields = ('titolo', 'descrizione')
    readonly_fields = ('data_creazione',)
    fieldsets = (
        ('Informazioni Principali', {
            'fields': ('titolo', 'descrizione', 'stato', 'data_creazione')
        }),
        ('Analisi', {
            'fields': ('analisi_ai', 'riferimenti_legali'),
            'classes': ('collapse',)
        }),
    )
