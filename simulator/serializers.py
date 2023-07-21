from .models import Drone
from .models import Dronetype
from rest_framework import serializers

class DroneTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Dronetype
        fields = [
                'id',
                'manufacturer',
                'typename',
                'weight',
                'maxspeed',
                'battery_capacity',
                'control_range',
                'maxcarriage',
                ]

class DroneOverviewSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Drone
        fields = [
                'id',
                'dronetype',
                'serialnumber',
                ]

class DroneDetailsSerializer(serializers.HyperlinkedModelSerializer):
    dronetype = DroneTypeSerializer(many=False)

    class Meta:
        model = Drone
        fields = [
                'id',
                'dronetype',
                'serialnumber', 
                'carriage_weight', 
                'carriage_type', 
                'speed', 
                'align_roll', 
                'align_pitch', 
                'align_yaw', 
                'longitude', 
                'latitude', 
                'battery_status', 
                'last_seen', 
                'status', 
                ]
