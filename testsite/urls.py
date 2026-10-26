from django.urls import path
from . import views

app_name = 'testsite'

urlpatterns = [
    path('', views.autorizacija, name='autorizacija'),
    path('registracija/', views.registracija, name='registracija'),
    path('registracija/nosutita/', views.registracija_nosutita, name='registracija_nosutita'),
    path('logout/', views.logout_view, name='logout'),
    path('sakumlapa/', views.sakumlapa, name='sakumlapa'),
    path('meklesana/', views.meklesana, name='meklesana'),
    path('profils/', views.profils, name='profils'),
    path('profils_fotogr/', views.profils_fotogr, name='profils_fotogr'),
    path('profils_fotogr_klienta/', views.profils_fotogr_klienta, name='profils_fotogr_klienta'),
    path('profila_regid/', views.profila_regid, name='profila_regid'),
    path('portfolio_regid/', views.portfolio_regid, name='portfolio_regid'),
    path('terzetava/', views.terzetava, name='terzetava'),
    path('report_submission/', views.report_submission, name='report_submission'),
    path('admin_panel/', views.admin_panel, name='admin_panel'),
]