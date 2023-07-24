from .models import Drone
from .models import DroneType
from .models import DroneDynamics
from rest_framework import serializers

class DroneTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DroneType
        fields = [
                'id',
                'manufacturer',
                'typename',
                'weight',
                'max_speed',
                'battery_capacity',
                'control_range',
                'max_carriage'
                ]

class DroneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Drone
        fields = [
                'id',
                'dronetype',
                'created',
                'serialnumber',
                'carriage_weight', 
                'carriage_type'
                ]

class DroneDynamicsSerializer(serializers.HyperlinkedModelSerializer):
    #drone = DroneSerializer(many=False)

    class Meta:
        model = DroneDynamics
        fields = [
                'drone',
                'timestamp', 
                'speed', 
                'align_roll', 
                'align_pitch', 
                'align_yaw', 
                'longitude', 
                'latitude', 
                'battery_status', 
                'last_seen', 
                'status'
                ]
