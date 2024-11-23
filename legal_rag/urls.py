from django.urls import path
from . import views
from .views.base_views import (
    CassazioneSearchView, 
    cassazione_search_api,
    PenalCodeSearchView,
    penal_code_search_api,
    penal_code_books,
    penal_code_titles,
    penal_code_articles,
    penal_code_article_detail
)
from .views.pdf_views import analyze_extracted_text

app_name = 'legal_rag'

urlpatterns = [
    path('', views.RagAssistantView.as_view(), name='index'),
    path('chat/', views.chat_view, name='chat'),
    path('image-pdf/', views.ImagePdfAssistantView.as_view(), name='image_pdf'),
    path('process-image-pdf/', views.process_image_pdf, name='process_image_pdf'),
    path('analyze-text/', analyze_extracted_text, name='analyze_text'),
    path('cassazione/', CassazioneSearchView.as_view(), name='cassazione_search'),
    path('cassazione-search/', cassazione_search_api, name='cassazione_search_api'),
    path('penal-code/', PenalCodeSearchView.as_view(), name='penal_code_search'),
    path('penal-code-search/', penal_code_search_api, name='penal_code_search_api'),
    
    # New API endpoints for penal code visualization
    path('books/', penal_code_books, name='penal_code_books'),
    path('titles/', penal_code_titles, name='penal_code_titles'),
    path('articles/', penal_code_articles, name='penal_code_articles'),
    path('articles/<int:article_id>/', penal_code_article_detail, name='penal_code_article_detail'),
]
