from django.urls import path
from . import views

app_name = 'testsite'

urlpatterns = [
    path('', views.autorizacija, name='autorizacija'),
    path('registracija/', views.registracija, name='registracija'),
    path('sakumlapa/', views.sakumlapa, name='sakumlapa'),
    path('aizmirsu-paroli/', views.aizmirsu_paroli, name='aizmirsu-paroli'),
    path('meklesana/', views.meklesana, name='meklesana'),
    path('profils/', views.profils, name='profils'),
]