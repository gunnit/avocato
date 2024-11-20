from django.urls import path
from . import views
from .views.base_views import CassazioneSearchView, cassazione_search_api

app_name = 'legal_rag'

urlpatterns = [
    path('', views.RagAssistantView.as_view(), name='index'),
    path('chat/', views.chat_view, name='chat'),
    path('image-pdf/', views.ImagePdfAssistantView.as_view(), name='image_pdf'),
    path('process-image-pdf/', views.process_image_pdf, name='process_image_pdf'),
    path('cassazione/', CassazioneSearchView.as_view(), name='cassazione_search'),
    path('cassazione-search/', cassazione_search_api, name='cassazione_search_api'),
]
