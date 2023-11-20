from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import timezone 
from rest_framework import viewsets, permissions
from simulator.serializers import DroneSerializer, DroneTypeSerializer, DroneDynamicsSerializer
from simulator.models import Drone, DroneType, DroneDynamics, SimulatorSettings
from rest_framework.decorators import action
from rest_framework.response import Response
import random
from datetime import datetime, timedelta
from math import sin, cos, radians
import threading
import time
from .forms import ModeChooseForm
from .tasks import add

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
    permission_classes = [ReadOnlyPermissionStudents]

class DroneTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for dronetypes
    """
    queryset = DroneType.objects.all().order_by('manufacturer')
    serializer_class = DroneTypeSerializer
    permission_classes = [ReadOnlyPermissionStudents]

class DroneDynamicsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for drone dynamics information
    """
    queryset = DroneDynamics.objects.all().order_by('timestamp')
    serializer_class = DroneDynamicsSerializer
    permission_classes = [ReadOnlyPermissionStudents]

# Create your views here.
def index(request):
    print("###### Task gestartet...")
    add.delay(10,10)
    modechooseform = ModeChooseForm(request.POST or None)
    if modechooseform.is_valid():
        mode = modechooseform.cleaned_data['simulator_mode']
        settings, created = SimulatorSettings.objects.get_or_create(pk=1)
        if settings.mode != mode:
            print("Changed mode from \'{}\' to \'{}\'".format(settings.mode, mode))
            settings.mode = mode
            settings.save()
            return HttpResponse('Changed mode successfully to \'{}\''.format(mode))
        print("Settings not changed")
        return HttpResponse('Mode remains unchancged at \'{}\''.format(mode))
    drones = Drone.objects.all()
    context= {
        'drones': drones,
        'render_button': request.user.is_staff,
        'modechooseform': modechooseform,
    }
    return render(request, 'simulator/index.html', context)

def start(request):
    return HttpResponse("Started")

def flush(request):
    if request.user.is_superuser:
        DroneType.objects.all().delete()
        return HttpResponse("Successful deleted database entries")
    else:
        return HttpResponse("Not allowed")

def drones(request):
    return render(request, 'simulator/drones.html', {'drones': Drone.objects.all()})

def dronetypes(request):
    return render(request, 'simulator/dronetypes.html', {'dronetypes': DroneType.objects.all()})

def dronedynamics(request):
    return render(request, 'simulator/dronedynamics.html', {'dronedynamics': DroneDynamics.objects.all()})

def dynamics(request, drone_id):
    drone = get_object_or_404(Drone, pk=drone_id)
    return render(request, 'simulator/dynamics.html', {'dynamics': drone.dynamics.all(), 'drone': drone})

# Helpers

def create_serial_number(dronetype):
    name = dronetype.manufacturer[0:2] + dronetype.typename[0:2]
    year = str(random.randint(2020, 2031))
    serial = ('%06x' % random.randrange(16**6)).upper()
    return '-'.join([name, year, serial])

def calculate_new_coordinates(longitude, latitude, speed, heading, last_sighting_time, current_time):
    heading_rad = radians(heading)
    elapsed_time = (current_time - last_sighting_time).total_seconds() / 3600
    distance = speed * elapsed_time

    delta_longitude = (cos(heading_rad) * distance) / (111.32 * 1000)
    delta_latitude = (sin(heading_rad) * distance) / (111.32 * 1000)

    new_longitude = longitude + delta_longitude
    new_latitude = latitude + delta_latitude
    return round(new_longitude, 9), round(new_latitude, 9)

def calculate_new_battery_level(dynamics, flight_duration_hr):
    # TODO: as of today, we assume that each drone has a total battery
    # capacity for one hour flight, no matter which size, weight or speed
    # is involved.
    total_battery = dynamics.drone.dronetype.battery_capacity
    new_battery_level = dynamics.battery_status - (total_battery * flight_duration_hr)
    #print("Battery: {}/{}, reducing by {} due to {} hrs flight time".format(new_battery_level, total_battery, total_battery*flight_duration_hr, flight_duration_hr))
    return max(0, int(new_battery_level))

def simulate_dynamics(dynamics, yaw=-1, timestamp=timezone.now()):
    if dynamics.battery_status <= 0:
        return DroneDynamics(drone=dynamics.drone, speed=dynamics.speed, align_roll=dynamics.align_roll, align_pitch=dynamics.align_pitch, align_yaw=dynamics.align_yaw, longitude=dynamics.longitude, latitude=dynamics.latitude, battery_status=0, last_seen=dynamics.last_seen, timestamp=timestamp, status="OF")
    if yaw < 0:
        new_yaw = random.randint(0,360)
    else:
        new_yaw=yaw
    new_speed = random.randint(1, dynamics.drone.dronetype.max_speed)
    new_long, new_lat = calculate_new_coordinates(dynamics.longitude, dynamics.latitude, dynamics.speed, dynamics.align_yaw, dynamics.last_seen, timestamp)
    new_battery = calculate_new_battery_level(dynamics, (timestamp - dynamics.last_seen).total_seconds() / 3600)
    if new_battery > 0:
        new_status = "ON"
    else:
        new_status = "OF"
        new_speed = 0
    return DroneDynamics(drone=dynamics.drone, speed=new_speed, align_roll=0, align_pitch=0, align_yaw=new_yaw, longitude=new_long, latitude=new_lat, battery_status=new_battery, last_seen=timestamp, timestamp=timestamp, status=new_status)

def create_initial_drone_dynamics(drone, place_id=0, timestamp=timezone.now()):
    places = (
            ("Frankfurt Hauptbahnhof", 50.107185833, 8.663789667),
            ("Römerberg", 50.110924000, 8.682127000),
            ("Palmengarten", 50.120598000, 8.657251000),
            ("Eiserner Steg", 50.107699000, 8.678109000),
            ("Goethe-Haus", 50.116536000, 8.681864000),
            ("Flughafen Frankfurt", 50.050194000, 8.570487000),
            ("Opel Zoo", 50.192078000, 8.496004000),
            ("Schloss Johannisburg", 50.039364000, 8.214841000),
            ("Mainz Dom", 49.998984000, 8.276432000),
            ("Darmstadt Mathildenhöhe", 49.870867000, 8.655013000),
            )
    return DroneDynamics(drone=drone, speed=drone.dronetype.max_speed, align_roll=0.0, align_pitch=0.0, align_yaw=0.0, longitude=places[place_id][1], latitude=places[place_id][2], battery_status=drone.dronetype.battery_capacity, last_seen=timestamp, timestamp=timestamp, status = "ON")

def init(request):
    if Drone.objects.count() > 0:
        return HttpResponse("Database already initialized. Delete database before calling init")
    dronetypes = [
            DroneType(manufacturer="GoPro", typename="Karma", weight=1000, max_speed=56, battery_capacity=5100, control_range=1500, max_carriage=400),
            DroneType(manufacturer="Hubsan", typename="X4 H107D", weight=50, max_speed=32, battery_capacity=380, control_range=200, max_carriage=50),
            DroneType(manufacturer="Walkera", typename="Voyager 4", weight=2450, max_speed=80, battery_capacity=7500, control_range=5000, max_carriage=800),
            DroneType(manufacturer="PowerVision", typename="PowerEgg X", weight=2100, max_speed=64, battery_capacity=5000, control_range=3500, max_carriage=500),
            DroneType(manufacturer="Blade", typename="Chroma Camera Drone", weight=1630, max_speed=65, battery_capacity=5400, control_range=2500, max_carriage=600),
            DroneType(manufacturer="DJI", typename="Phantom 4 Pro", weight=1380, max_speed=72, battery_capacity=5870, control_range=7000, max_carriage=500),
            DroneType(manufacturer="Yuneec", typename="Typhoon H Pro", weight=1995, max_speed=70, battery_capacity=5400, control_range=2000, max_carriage=100),
            DroneType(manufacturer="Autel Robotics", typename="Evo II", weight=1127, max_speed=72, battery_capacity=7100, control_range=9000, max_carriage=800),
            DroneType(manufacturer="Parrot", typename="Anafi", weight=320, max_speed=55, battery_capacity=2700, control_range=4000, max_carriage=200),
            DroneType(manufacturer="Skydio", typename="Skydio 2", weight=775, max_speed=58, battery_capacity=4280, control_range=3500, max_carriage=400),
            ]
    drones = [
            Drone(dronetype=dronetypes[0], serialnumber=create_serial_number(dronetypes[0]), carriage_weight=200, carriage_type="SEN"),
            Drone(dronetype=dronetypes[1], serialnumber=create_serial_number(dronetypes[1]), carriage_weight=0, carriage_type="NOT"),
            Drone(dronetype=dronetypes[2], serialnumber=create_serial_number(dronetypes[2]), carriage_weight=400, carriage_type="SEN"),
            Drone(dronetype=dronetypes[3], serialnumber=create_serial_number(dronetypes[3]), carriage_weight=100, carriage_type="SEN"),
            Drone(dronetype=dronetypes[4], serialnumber=create_serial_number(dronetypes[4]), carriage_weight=300, carriage_type="ACT"),
            Drone(dronetype=dronetypes[5], serialnumber=create_serial_number(dronetypes[5]), carriage_weight=150, carriage_type="SEN"),
            Drone(dronetype=dronetypes[6], serialnumber=create_serial_number(dronetypes[6]), carriage_weight=0, carriage_type="NOT"),
            Drone(dronetype=dronetypes[7], serialnumber=create_serial_number(dronetypes[7]), carriage_weight=0, carriage_type="NOT"),
            Drone(dronetype=dronetypes[8], serialnumber=create_serial_number(dronetypes[8]), carriage_weight=0, carriage_type="NOT"),
            Drone(dronetype=dronetypes[9], serialnumber=create_serial_number(dronetypes[9]), carriage_weight=300, carriage_type="ACT"),
            ]

    # Creating dynamics for the past x minutes
    init_delta = timedelta(minutes=100)
    # Creating dynamics every x seconds
    recurring_delta = timedelta(seconds=10)
    starttime = timezone.now() - init_delta
    dronedynamics = [create_initial_drone_dynamics(drones[i], i, timestamp=starttime) for i in range(10)]

    for i in dronetypes:
        i.save()
    for i in drones:
        i.save()
    for i in dronedynamics:
        i.save()
    for i in range(int(init_delta/recurring_delta)):
        simulated_time = starttime + ((i+1)*recurring_delta)
        dronedynamics = [simulate_dynamics(j, timestamp=simulated_time) for j in dronedynamics]
        for j in dronedynamics:
            j.save()
    return HttpResponse("Initialized with {} dronetypes and {} drones each with {} initial drone dynamics values!".format(len(dronetypes), len(drones), int(init_delta/recurring_delta)))
