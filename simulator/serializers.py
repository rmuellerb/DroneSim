from .models import Drone
from rest_framework import serializers

class DroneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Drone
        fields = ['serialnumber', 
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
