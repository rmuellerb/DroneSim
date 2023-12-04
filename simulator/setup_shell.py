from simulator import views
from simulator.models import Drone, DroneType, DroneDynamics
from datetime import datetime, timedelta
from simulator import views

# Setup test data for one drone including type and dynamics
type1 = DroneType(manufacturer="GoPro", typename="Karma", weight=1000, max_speed=56, battery_capacity=5100, control_range=1500, max_carriage=400)
drone1 = Drone(dronetype=type1, serialnumber=views.create_serial_number(type1), carriage_weight=200, carriage_type="SEN")
dynamics1 = views.create_initial_drone_dynamics(drone1, place_id=0)

print("Setup drone successful! You can use type1, drone1, dynamics1 now.")
