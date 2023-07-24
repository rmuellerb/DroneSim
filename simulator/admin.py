from django.contrib import admin
from .models import DroneType, Drone, DroneDynamics

# Register your models here.
admin.site.register(DroneType)
admin.site.register(DroneDynamics)
admin.site.register(Drone)
