from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pdfs/', views.PdfListView.as_view(), name='pdfs'),
    path('pdf/<uuid:pk>', views.PdfDetailView.as_view(), name='pdf-detail'),
    path('chatbot/', views.chatbot_view, name='chatbot_view'),
    path('query_bot/', views.chatbot_query_view, name='chatbot_query_view'),
]