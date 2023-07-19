from django.db import models

# Create your models here.
class Dronetype(models.Model):
    def __str__(self):
        return self.manufacturer + ": " + self.typename

    manufacturer = models.CharField(max_length=200)
    typename = models.CharField(max_length=200)
    weight = models.PositiveBigIntegerField()
    maxspeed = models.PositiveIntegerField()
    battery_capacity = models.PositiveBigIntegerField()
    control_range = models.PositiveBigIntegerField()
    maxcarriage = models.PositiveBigIntegerField()

class Drone(models.Model):
    def __str__(self):
        return "Drone: " + self.serialnumber
    dronetype = models.ForeignKey(Dronetype, on_delete=models.CASCADE)
    serialnumber = models.CharField(max_length=200, unique=True)
    carriage_weight = models.PositiveBigIntegerField(default=0)

    CARRIAGE_SENSORS = "SEN"
    CARRIAGE_ACTUATORS = "ACT"
    CARRIAGE_NOTHING = "NOT"
    CARRIAGE_CHOICES = [
            (CARRIAGE_SENSORS, "Sensors"),
            (CARRIAGE_ACTUATORS, "Actuators"),
            (CARRIAGE_NOTHING, "Nothing"),
    ]
    carriage_type = models.CharField(max_length=3, choices=CARRIAGE_CHOICES, default=CARRIAGE_NOTHING)
    speed = models.PositiveBigIntegerField()
    align_roll = models.DecimalField(max_digits=3, decimal_places=2, default=000.00)
    align_pitch = models.DecimalField(max_digits=3, decimal_places=2, default=000.00)
    align_yaw = models.DecimalField(max_digits=3, decimal_places=2, default=000.00)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    battery_status = models.PositiveBigIntegerField()
    last_seen = models.DateTimeField()
    
    STATUS_ONLINE = "ON"
    STATUS_OFFLINE = "OF"
    STATUS_ISSUES = "IS"
    STATUS_CHOICES = [
        (STATUS_ONLINE, "Online"),
        (STATUS_OFFLINE, "Offline"),
        (STATUS_ISSUES, "Issues"),
    ]
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=STATUS_OFFLINE)

