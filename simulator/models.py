from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

# Create authentication token for new users
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class SimulatorSettings(models.Model):
    mode = models.CharField(max_length=10, choices=[('static', 'Static'), ('live', 'Live')])

class DroneType(models.Model):
    def __str__(self):
        return self.manufacturer + ": " + self.typename

    manufacturer = models.CharField(max_length=100)
    typename = models.CharField(max_length=100)
    weight = models.PositiveIntegerField(help_text="Weight in g")
    max_speed = models.PositiveIntegerField(help_text="Maximum speed in km/h")
    battery_capacity = models.PositiveIntegerField(help_text="Battery capacity in mAh")
    control_range = models.PositiveIntegerField(help_text="Control range in m")
    max_carriage = models.PositiveIntegerField(default=0, help_text="Maximum carriage in g")

class Drone(models.Model):
    def __str__(self):
        return "Drone: " + self.serialnumber + " (created: {})".format(self.created)
    dronetype = models.ForeignKey(DroneType, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    serialnumber = models.CharField(max_length=200, unique=True, help_text="Must be a unique text within all drones")
    carriage_weight = models.PositiveIntegerField(default=0, help_text="Current additional carriage in g")

    CARRIAGE_SENSORS = "SEN"
    CARRIAGE_ACTUATORS = "ACT"
    CARRIAGE_NOTHING = "NOT"
    CARRIAGE_CHOICES = [
            (CARRIAGE_SENSORS, "Sensors"),
            (CARRIAGE_ACTUATORS, "Actuators"),
            (CARRIAGE_NOTHING, "Nothing"),
            ]
    carriage_type = models.CharField(max_length=3, choices=CARRIAGE_CHOICES, default=CARRIAGE_NOTHING, help_text="Type of carriage. SEN for sensor, ACT for actuator, and NOT for nothing.")

class DroneDynamics(models.Model):
    def __str__(self):
        return "[{}] Status: {}, coordinates: {}/{}, speed: {}/{}, battery: {}/{}".format(self.timestamp, self.status, self.longitude, self.latitude, self.speed, self.drone.dronetype.max_speed, self.battery_status, self.drone.dronetype.battery_capacity)
    
    # ToDo: Barometric height (relative to start), GPS height 
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE, related_name="dynamics")
    timestamp = models.DateTimeField(help_text="Timestamp of this data")
    speed = models.PositiveIntegerField(help_text="Current speed in km/h")
    align_roll = models.DecimalField(max_digits=5, decimal_places=2, default=000.00, help_text="Current alignment on x-axis")
    align_pitch = models.DecimalField(max_digits=5, decimal_places=2, default=000.00, help_text="Current algnment on y-axis")
    align_yaw = models.DecimalField(max_digits=5, decimal_places=2, default=000.00, help_text="Current alignment on z-axis")
    longitude = models.DecimalField(max_digits=12, decimal_places=9, help_text="Current position longitude with a precision of 6 decimal places")
    latitude = models.DecimalField(max_digits=12, decimal_places=9, help_text="Current position latitude with a precision of 6 decimal places")
    battery_status = models.PositiveIntegerField(help_text="Current battery charge in mAh")
    last_seen = models.DateTimeField(help_text="Last contact to drone")
    STATUS_ONLINE = "ON"
    STATUS_OFFLINE = "OF"
    STATUS_ISSUES = "IS"
    STATUS_CHOICES = [
            (STATUS_ONLINE, "Online"),
            (STATUS_OFFLINE, "Offline"),
            (STATUS_ISSUES, "Issues"),
            ]
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=STATUS_OFFLINE, help_text="Status of the drone. ON for online, OF for offline, IS for issues.")
