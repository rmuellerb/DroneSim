from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from simulator.serializers import DroneDetailsSerializer, DroneTypeSerializer, DroneOverviewSerializer
from simulator.models import Drone, Dronetype
from rest_framework.decorators import action
from rest_framework.response import Response

# REST API views
class DroneOverviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for drone overviews
    """
    queryset = Drone.objects.all().order_by('id')
    serializer_class = DroneOverviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(methods=['GET'], detail=True)
    def details(self, request, pk):
        detaildrone = self.get_object()
        serializer = DroneDetailsSerializer(instance=detaildrone, context={'request': request})
        return Response(serializer.data)

class DroneTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for dronetypes
    """
    queryset = Dronetype.objects.all().order_by('id')
    serializer_class = DroneTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class DroneDetailsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for single drone views
    """
    queryset = Drone.objects.all().order_by('id')
    serializer_class = DroneDetailsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# Create your views here.

def index(request):
    return HttpResponse("Hello Simulator")

