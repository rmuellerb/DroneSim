from django.urls import path

from . import views

app_name = 'simulator'
urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start, name='start'),
    path('init/', views.init, name='init'),
    path('flush/', views.flush, name='flush'),
    path('drones/', views.drones, name='drones'),
    path('dronetypes/', views.dronetypes, name='dronetypes'),
    path('dronedynamics/', views.dronedynamics, name='dronedynamics'),
    path('<int:drone_id>/dynamics', views.dynamics, name='dynamics'),
]
