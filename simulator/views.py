from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from simulator.serializers import DroneSerializer, DroneTypeSerializer, DroneDynamicsSerializer
from simulator.models import Drone, DroneType, DroneDynamics
from rest_framework.decorators import action
from rest_framework.response import Response

# REST API views
class DroneViewSet(viewsets.ModelViewSet):
    """
    API endpoint for drones
    """
    queryset = Drone.objects.all().order_by('created')
    serializer_class = DroneSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class DroneTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for dronetypes
    """
    queryset = DroneType.objects.all().order_by('manufacturer')
    serializer_class = DroneTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class DroneDynamicsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for drone dynamics information
    """
    queryset = DroneDynamics.objects.all().order_by('timestamp')
    serializer_class = DroneDynamicsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# Create your views here.

def index(request):
    drones = Drone.objects.all()
    context = {'drones': drones}
    return render(request, 'simulator/index.html', context)

