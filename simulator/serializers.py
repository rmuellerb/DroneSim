from .models import Drone
from .models import Dronetype
from rest_framework import serializers

class DronetypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Dronetype
        fields = [
                'manufacturer',
                'typename',
                'weight',
                'maxspeed',
                'battery_capacity',
                'control_range',
                'maxcarriage',
                ]

class DroneSerializer(serializers.HyperlinkedModelSerializer):
#    manufacturer = serializers.CharField(source='dronetype.manufacturer')
#    typename = serializers.CharField(source='dronetype.typename')
#    weight = serializers.PositiveBigIntegerField(source='dronetype.weight')
#    maxspeed = serializers.PositiveIntegerField(source='dronetype.maxspeed')

    dronetype = DronetypeSerializer(many=False)

    class Meta:
        model = Drone
        fields = [
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
