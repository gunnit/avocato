from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_casi, name='lista_casi'),
    path('nuovo/', views.nuovo_caso, name='nuovo_caso'),
    path('caso/<int:caso_id>/', views.dettaglio_caso, name='dettaglio_caso'),
    path('caso/<int:caso_id>/rigenera/', views.rigenera_analisi, name='rigenera_analisi'),
    path('caso/<int:caso_id>/chat/', views.chat_caso, name='chat_caso'),
    path('caso/<int:caso_id>/memoria-difensiva/', views.memoria_difensiva, name='memoria_difensiva'),
]
