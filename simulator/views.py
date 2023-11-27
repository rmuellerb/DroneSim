from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from rest_framework import viewsets, permissions
from simulator.serializers import DroneSerializer, DroneTypeSerializer, DroneDynamicsSerializer
from simulator.models import Drone, DroneType, DroneDynamics, SimulatorSettings
from rest_framework.response import Response
from .forms import ModeChooseForm
from .tasks import init_static_drones
from rest_framework.authtoken.models import Token
import logging

log = logging.getLogger(__name__)

# Permissions
# Read-Only for non-writing operations, writing operations for staff
class ReadOnlyPermissionStudents(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return False

# REST API views
class DroneViewSet(viewsets.ModelViewSet):
    """
    API endpoint for drones
    """
    queryset = Drone.objects.all().order_by('created')
    serializer_class = DroneSerializer
#    permission_classes = [ReadOnlyPermissionStudents]

class DroneTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for dronetypes
    """
    queryset = DroneType.objects.all().order_by('manufacturer')
    serializer_class = DroneTypeSerializer
#    permission_classes = [ReadOnlyPermissionStudents]

class DroneDynamicsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for drone dynamics information
    """
    queryset = DroneDynamics.objects.all().order_by('timestamp')
    serializer_class = DroneDynamicsSerializer
#    permission_classes = [ReadOnlyPermissionStudents]

# Helper for context
def create_context(request):
    token = "none"
    if request.user.is_authenticated:
        t, created = Token.objects.get_or_create(user=request.user)
        token = t.key
    context= {
            'render_button': request.user.is_staff,
            'token': token,
            }
    return context

# Views
def index(request):
    modechooseform = ModeChooseForm(request.POST or None)
    if modechooseform.is_valid():
        mode = modechooseform.cleaned_data['simulator_mode']
        settings, created = SimulatorSettings.objects.get_or_create(pk=1)
        if settings.mode != mode:
            log.debug("Changed mode from \'{}\' to \'{}\'".format(settings.mode, mode))
            settings.mode = mode
            settings.save()
            return HttpResponse('Changed mode successfully to \'{}\''.format(mode))
        log.debug("Settings not changed")
        return HttpResponse('Mode remains unchancged at \'{}\''.format(mode))
    drones = Drone.objects.all()
    context = create_context(request)
    context['drones'] = drones
    context['modechooseform'] = modechooseform
    return render(request, 'simulator/index.html', context)

def flush(request):
    if request.user.is_superuser:
        DroneType.objects.all().delete()
        log.debug("Deleted database entries")
        return HttpResponse("Successful deleted database entries")
    else:
        log.debug("Flush database not allowed")
        return HttpResponse("Not allowed")

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def drones(request):
    context = create_context(request)
    context['drones'] = Drone.objects.all()
    return render(request, 'simulator/drones.html', context)

def dronetypes(request):
    context = create_context(request)
    context['dronetypes'] = DroneType.objects.all()
    return render(request, 'simulator/dronetypes.html', context)

def dronedynamics(request):
    context = create_context(request)
    context['dronedynamics'] = DroneDynamics.objects.all()
    return render(request, 'simulator/dronedynamics.html', context)

def dynamics(request, drone_id):
    drone = get_object_or_404(Drone, pk=drone_id)
    return render(request, 'simulator/dynamics.html', {'dynamics': drone.dynamics.all(), 'drone': drone})

def init(request):
    if Drone.objects.count() > 0:
        log.error("Error initializing database: already initialized. Flush entries to reinizialize.")
        return HttpResponse("Error initializing database: already initialized. Flush entries to reinitialize.")
    init_call = init_static_drones.delay()
    log.debug("Started background task to initialize drones")
    return HttpResponse("Started background task to initialize drones")
