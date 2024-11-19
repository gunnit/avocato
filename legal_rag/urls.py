from django.urls import path
from . import views

app_name = 'legal_rag'

urlpatterns = [
    path('', views.RagAssistantView.as_view(), name='index'),
    path('chat/', views.chat_view, name='chat'),
    path('image-pdf/', views.ImagePdfAssistantView.as_view(), name='image_pdf'),
    path('process-image-pdf/', views.process_image_pdf, name='process_image_pdf'),
]
