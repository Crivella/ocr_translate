from django.urls import path

from base import views

app_name = 'base'
urlpatterns = [
    path('', views.handshake),
    path('load/', views.load_models),
    path('set_lang/', views.set_lang),
    path('get_trans/', views.get_translations),
    path('run_tsl/', views.run_tsl),
    path('run_ocrtsl/', views.run_ocrtsl),
]