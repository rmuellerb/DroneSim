from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from simulator.serializers import DroneSerializer
from simulator.models import Drone

# REST API views
class DroneViewSet(viewsets.ModelViewSet):
    """
    API endpoint for drones
    """
    queryset = Drone.objects.all().order_by('status')
    serializer_class = DroneSerializer
    permission_classes = [permissions.IsAuthenticated]

# Create your views here.

def index(request):
    return HttpResponse("Hello Simulator")

