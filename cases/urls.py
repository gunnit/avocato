from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_casi, name='lista_casi'),
    path('nuovo/', views.nuovo_caso, name='nuovo_caso'),
    path('<int:caso_id>/', views.dettaglio_caso, name='dettaglio_caso'),
    path('<int:caso_id>/chat/', views.chat_caso, name='chat_caso'),
    path('<int:caso_id>/memoria-difensiva/', views.memoria_difensiva, name='memoria_difensiva'),
    path('<int:caso_id>/memoria-difensiva/detail/', views.memoria_difensiva_detail, name='memoria_difensiva_detail'),
    path('<int:caso_id>/rigenera-analisi/', views.rigenera_analisi, name='rigenera_analisi'),
    
    # Documentary Evidence URLs
    path('<int:caso_id>/documentary-evidence/', views.documentary_evidence_list, name='documentary_evidence_list'),
    path('<int:caso_id>/documentary-evidence/add/', views.documentary_evidence_add, name='documentary_evidence_add'),
    path('<int:caso_id>/documentary-evidence/<int:doc_id>/', views.documentary_evidence_detail, name='documentary_evidence_detail'),
    path('<int:caso_id>/documentary-evidence/<int:doc_id>/edit/', views.documentary_evidence_edit, name='documentary_evidence_edit'),
]
