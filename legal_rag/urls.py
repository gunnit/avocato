from django.urls import path
from . import views

app_name = 'legal_rag'

urlpatterns = [
    path('', views.RagAssistantView.as_view(), name='index'),
    path('chat/', views.chat_view, name='chat'),
]
