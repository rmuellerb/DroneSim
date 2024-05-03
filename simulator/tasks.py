from celery import shared_task
from dronesim.celery import app
from django.utils import timezone 
from simulator.models import Drone, DroneType, DroneDynamics
from datetime import datetime, timedelta
import time
import random
from math import sin, cos, radians
import math
import logging

log = logging.getLogger(__name__)

def create_initial_drone_dynamics(drone, place_id=-1, timestamp=timezone.now()):
    """
    Creates an initial drone dynamics orm object. If the place_id is -1, a random place is chosen
    """
    places = (
            # (name, latitude, longitude)
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
    place = random.choice(places)
    if place_id != -1:
        place = places[place_id]
    return DroneDynamics(drone=drone, speed=drone.dronetype.max_speed, align_roll=0.0, align_pitch=0.0, align_yaw=0.0, longitude=place[2], latitude=place[1], battery_status=drone.dronetype.battery_capacity, last_seen=timestamp, timestamp=timestamp, status = "ON")

def calculate_new_coordinates(longitude, latitude, speed, heading, last_sighting_time, current_time):
    heading_rad = radians(heading)
    lat_rad = radians(latitude)
    long_rad = radians(longitude)
    elapsed_time = (current_time - last_sighting_time).total_seconds() / 3600
    dist = speed * elapsed_time
    earth_radius = 6371.0

    """
    FIXME
    """
    new_lat = math.asin(math.sin(lat_rad) * math.cos(dist / earth_radius) + math.cos(lat_rad) * math.sin(dist / earth_radius) * math.cos(heading))
    new_long = long_rad + math.atan2(math.sin(heading) * math.sin(dist / earth_radius) * math.cos(lat_rad), math.cos(dist / earth_radius) - math.sin(lat_rad) * math.sin(new_lat))
    
    """
    delta_longitude = (cos(heading_rad) * distance) / (111.32 * 1000)
    delta_latitude = (sin(heading_rad) * distance) / (111.32 * 1000)

    new_longitude = longitude + delta_longitude
    new_latitude = latitude + delta_latitude
    return round(new_longitude, 9), round(new_latitude, 9)
    """
    new_lat = math.degrees(new_lat)
    new_long = math.degrees(new_long)
    print("New long/lat: {} / {} ".format(new_long, new_lat))
    return new_long, new_lat

def calculate_new_battery_level(dynamics, flight_duration_hr):
    # TODO: as of today, we assume that each drone has a total battery
    # capacity for one hour flight, no matter which size, weight or speed
    # is involved.
    total_battery = dynamics.drone.dronetype.battery_capacity
    new_battery_level = dynamics.battery_status - (total_battery * flight_duration_hr)
    #print("Battery: {}/{}, reducing by {} due to {} hrs flight time".format(new_battery_level, total_battery, total_battery*flight_duration_hr, flight_duration_hr))
    return max(0, int(new_battery_level))

def create_serial_number(dronetype):
    name = dronetype.manufacturer[0:2] + dronetype.typename[0:2]
    year = str(random.randint(2020, 2031))
    serial = ('%06x' % random.randrange(16**6)).upper()
    return '-'.join([name, year, serial])

# TODO: We assume that an empty battery is reloaded after being offline for 1hr
def simulate_dynamics(dynamics, yaw=-1, timestamp=timezone.now()):
    if dynamics.battery_status <= 0:
        if timestamp - dynamics.last_seen >= timedelta(hours=1):
            dynamics.battery_status = dynamics.drone.dronetype.battery_capacity
            dynamics.last_seen = timestamp
            dynamics.save()
        else:
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

# Default time window is 48hrs with a delta of 60 secs = 2880 entries per drone. Per default, 30 drones are created
@app.task
def init_static_drones(init_delta_min=2880, tick_delta_sec=60, n=30):
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
            DroneType(manufacturer="Syma", typename="X5C", weight=102, max_speed=40, battery_capacity=500, control_range=150, max_carriage=70),
            DroneType(manufacturer="Cheerson", typename="CX-10", weight=25, max_speed=20, battery_capacity=100, control_range=50, max_carriage=30),
            DroneType(manufacturer="JJRC", typename="H36", weight=22, max_speed=30, battery_capacity=150, control_range=100, max_carriage=20),
            DroneType(manufacturer="Eachine", typename="E58", weight=96, max_speed=35, battery_capacity=500, control_range=200, max_carriage=50),
            DroneType(manufacturer="Holy Stone", typename="HS100", weight=700, max_speed=45, battery_capacity=3500, control_range=500, max_carriage=500),
            DroneType(manufacturer="Ryze", typename="Tello", weight=80, max_speed=28, battery_capacity=1100, control_range=100, max_carriage=40),
            DroneType(manufacturer="Altair Aerial", typename="AA108", weight=85, max_speed=36, battery_capacity=750, control_range=300, max_carriage=60),
            DroneType(manufacturer="Snaptain", typename="S5C", weight=120, max_speed=40, battery_capacity=550, control_range=150, max_carriage=80),
            DroneType(manufacturer="Potensic", typename="D80", weight=450, max_speed=50, battery_capacity=2800, control_range=800, max_carriage=200),
            DroneType(manufacturer="Contixo", typename="F24 Pro", weight=520, max_speed=60, battery_capacity=2500, control_range=1200, max_carriage=250),
            ]
    drones = []
    for i in range(n):
        dronetype = random.choice(dronetypes)
        serialnumber = create_serial_number(dronetype)
        carriage_type = random.choice(["SEN", "ACT","NOT"])
        carriage_weight = 0
        if carriage_type != "NOT":
            carriage_weight = random.randint(0, dronetype.max_carriage)
        drone = Drone(dronetype=dronetype, serialnumber=serialnumber, carriage_weight=carriage_weight, carriage_type=carriage_type)
        drones.append(drone)

    # Creating dynamics for the past x minutes
    init_delta = timedelta(minutes=init_delta_min)
    # Creating dynamics every x seconds
    recurring_delta = timedelta(seconds=tick_delta_sec)
    starttime = timezone.now() - init_delta
    dronedynamics = [create_initial_drone_dynamics(drones[i], -1, timestamp=starttime) for i in range(len(drones))]

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
    log.debug("Finished initialization of database")
    print("Finished initialization of database")
