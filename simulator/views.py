from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from simulator.serializers import DroneSerializer, DroneTypeSerializer, DroneDynamicsSerializer
from simulator.models import Drone, DroneType, DroneDynamics
from rest_framework.decorators import action
from rest_framework.response import Response
import random
from datetime import datetime

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

def start(request):
    return HttpResponse("Started")

def flush(request):
    DroneType.objects.all().delete()
    return HttpResponse("Successful deleted database entries")

def create_serial_number(dronetype):
    name = dronetype.manufacturer[0:2] + dronetype.typename[0:2]
    year = str(random.randint(2020, 2031))
    serial = ('%06x' % random.randrange(16**6)).upper()
    return '-'.join([name, year, serial])

def create_initial_drone_dynamics(drone, place_id=0):
    places = (
            ("Frankfurt Hauptbahnhof", 50.107185, 8.663789),
            ("Römerberg", 50.110924, 8.682127),
            ("Palmengarten", 50.120598, 8.657251),
            ("Eiserner Steg", 50.107699, 8.678109),
            ("Goethe-Haus", 50.116536, 8.681864),
            ("Flughafen Frankfurt", 50.050194, 8.570487),
            ("Opel Zoo", 50.192078, 8.496004),
            ("Schloss Johannisburg", 50.039364, 8.214841),
            ("Mainz Dom", 49.998984, 8.276432),
            ("Darmstadt Mathildenhöhe", 49.870867, 8.655013)
            )

    return DroneDynamics(
            drone=drone, 
            speed=drone.dronetype.max_speed, 
            align_roll=0.0, 
            align_pitch=0.0, 
            align_yaw=0.0, 
            longitude=places[place_id][1], 
            latitude=places[place_id][2], 
            battery_status=drone.dronetype.battery_capacity, 
            last_seen=datetime.now(),
            status = "ON",
            )

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
    dronedynamics = [create_initial_drone_dynamics(drones[i], i) for i in range(10)]

    for i in dronetypes:
        i.save()
    for i in drones:
        i.save()
    for i in dronedynamics:
        i.save()
    return HttpResponse("Initialized with {} dronetypes and {} drones each with initial drone dynamics!".format(len(dronetypes), len(drones)))


