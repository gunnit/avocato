from django.urls import path
from . import views
from .views.documentary_evidence_views import (
    documentary_evidence_list,
    documentary_evidence_add,
    documentary_evidence_detail,
    documentary_evidence_edit,
    analyze_evidence
)
from .views.user_views import profile
from .views.landing_views import landing_view
from .views.legal_memory_views import (
    memoria_difensiva,
    memoria_difensiva_detail,
    generate_content
)

urlpatterns = [
    # Landing page
    path('', landing_view, name='landing'),
    
    # Cases URLs
    path('cases/', views.lista_casi, name='lista_casi'),
    path('cases/nuovo/', views.nuovo_caso, name='nuovo_caso'),
    path('cases/<int:caso_id>/', views.dettaglio_caso, name='dettaglio_caso'),
    path('cases/<int:caso_id>/edit/', views.edit_caso, name='edit_caso'),
    path('cases/<int:caso_id>/delete/', views.delete_caso, name='delete_caso'),
    path('cases/<int:caso_id>/chat/', views.chat_caso, name='chat_caso'),
    path('cases/<int:caso_id>/memoria-difensiva/', memoria_difensiva, name='memoria_difensiva'),
    path('cases/<int:caso_id>/memoria-difensiva/detail/', memoria_difensiva_detail, name='memoria_difensiva_detail'),
    path('cases/<int:caso_id>/generate-content/', generate_content, name='generate_content'),
    path('cases/<int:caso_id>/rigenera-analisi/', views.rigenera_analisi, name='rigenera_analisi'),
    
    # Documentary Evidence URLs
    path('cases/<int:caso_id>/documentary-evidence/', documentary_evidence_list, name='documentary_evidence_list'),
    path('cases/<int:caso_id>/documentary-evidence/add/', documentary_evidence_add, name='documentary_evidence_add'),
    path('cases/<int:caso_id>/documentary-evidence/<int:doc_id>/', documentary_evidence_detail, name='documentary_evidence_detail'),
    path('cases/<int:caso_id>/documentary-evidence/<int:doc_id>/edit/', documentary_evidence_edit, name='documentary_evidence_edit'),
    path('cases/<int:caso_id>/documentary-evidence/<int:doc_id>/analyze/', analyze_evidence, name='analyze_evidence'),

    # User URLs
    path('profile/', profile, name='profile'),
]
