from django.urls import path

from . import views

app_name = 'simulator'
urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start, name='start'),
    path('init/', views.init, name='init'),
]
