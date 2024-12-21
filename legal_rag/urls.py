from django.urls import path
from .views import base_views, chat_views, pdf_views, transcription_views

app_name = 'legal_rag'  # Added app_name for namespace support

urlpatterns = [
    # Base views
    path('', base_views.RagAssistantView.as_view(), name='rag_assistant'),
    path('image-pdf/', base_views.ImagePdfAssistantView.as_view(), name='image_pdf_assistant'),  # Updated name to match sidebar
    path('cassazione-search/', base_views.CassazioneSearchView.as_view(), name='cassazione_search'),
    path('penal-code-search/', base_views.PenalCodeSearchView.as_view(), name='penal_code_search'),
    
    # Penal code API endpoints
    path('api/penal-code/books/', base_views.penal_code_books, name='penal_code_books'),
    path('api/penal-code/titles/', base_views.penal_code_titles, name='penal_code_titles'),
    path('api/penal-code/articles/', base_views.penal_code_articles, name='penal_code_articles'),
    path('api/penal-code/articles/<int:article_id>/', base_views.penal_code_article_detail, name='penal_code_article_detail'),
    path('api/cassazione-search/', base_views.cassazione_search_api, name='cassazione_search_api'),

    # Chat endpoint
    path('chat/', chat_views.chat_view, name='chat'),

    # Transcription views
    path('transcription/', transcription_views.TranscriptionView.as_view(), name='transcription'),
    path('transcription/transcribe/', transcription_views.transcribe_media, name='transcribe_media'),
]
