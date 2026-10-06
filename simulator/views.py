from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework import viewsets, generics
from simulator.serializers import DroneSerializer, DroneTypeSerializer, DroneDynamicsSerializer
from simulator.models import Drone, DroneType, DroneDynamics
from .tasks import init_static_drones
from rest_framework.authtoken.models import Token
from django.db.models import OuterRef, Subquery
import logging

log = logging.getLogger(__name__)

# REST API views
class DroneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for drones
    """
    queryset = Drone.objects.all().order_by('created')
    serializer_class = DroneSerializer

class DroneTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for dronetypes
    """
    queryset = DroneType.objects.all().order_by('manufacturer')
    serializer_class = DroneTypeSerializer

class DroneDynamicsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for drone dynamics information
    """
    queryset = DroneDynamics.objects.all().order_by('timestamp', "id")
    serializer_class = DroneDynamicsSerializer

class DroneDynamicListAPIView(generics.ListAPIView):
    """
    API endpoint for drone dynamics information based on a drone id
    """
    serializer_class = DroneDynamicsSerializer

    def get_queryset(self):
        """
        This view should return a list of all the drone dynamics for
        the drone as determined by the drone id portion of the URL.
        """
        drone_id = self.kwargs['drone_id']
        drone = get_object_or_404(Drone, pk=drone_id)
        return drone.dynamics.all().order_by('timestamp')

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
    latest = (DroneDynamics.objects.filter(drone=OuterRef("pk")).order_by("-timestamp", "-id"))
    drones = (Drone.objects.select_related("dronetype").annotate(last_status=Subquery(latest.values("status")[:1]), last_timestamp=Subquery(latest.values("timestamp")[:1])))
    context = create_context(request)
    context['drones'] = drones
    return render(request, 'simulator/index.html', context)

@require_POST
@user_passes_test(lambda u: u.is_superuser)
def flush(request):
    DroneType.objects.all().delete()
    log.info("Deleted database entries from user %s", request.user)
    return HttpResponse("Successful deleted database entries")

@login_required
def drones(request):
    context = create_context(request)
    context['drones'] = Drone.objects.all()
    return render(request, 'simulator/drones.html', context)

@login_required
def dronetypes(request):
    context = create_context(request)
    context['dronetypes'] = DroneType.objects.all()
    return render(request, 'simulator/dronetypes.html', context)

@login_required
def dronedynamics(request):
    context = create_context(request)
    dronedynamics_list = (DroneDynamics.objects.select_related("drone").order_by("timestamp", "id"))
    paginator = Paginator(dronedynamics_list, 10)
    page_number = request.GET.get('page')
    context['page_obj'] = paginator.get_page(page_number)
    return render(request, 'simulator/dronedynamics.html', context)

@login_required
def dynamics(request, drone_id):
    drone = get_object_or_404(Drone.objects.select_related("dronetype"), pk=drone_id)
    paginator = Paginator(drone.dynamics.order_by("timestamp", "id"), 50)
    context = create_context(request)
    context["drone"] = drone
    context["page_obj"] = paginator.get_page(request.GET.get("page"))
    return render(request, "simulator/dynamics.html", context)

@require_POST
@staff_member_required
def init(request):
    if Drone.objects.count() > 0:
        log.error("Error initializing database: already initialized. Flush entries to reinizialize.")
        return HttpResponse("Error initializing database: already initialized. Flush entries to reinitialize.")
    init_static_drones.delay()
    log.debug("Started background task to initialize drones")
    return HttpResponse("Started background task to initialize drones")

def login_redirect(request):
    return redirect("/accounts/oidc/authentik/login/")
