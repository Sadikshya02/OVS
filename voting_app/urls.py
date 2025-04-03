from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('vote/', views.vote, name='vote'),
    path('about/', views.about, name='about'),
    path('rules/', views.rules, name='rules'),
]
