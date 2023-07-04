from django.urls import path

from base import views

app_name = 'base'
urlpatterns = [
    path('', views.handshake),
    path('load/', views.load_models),
    path('test/', views.test),
]