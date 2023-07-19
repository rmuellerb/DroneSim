from django.db import models

# Create your models here.
class Dronetype(models.Model):
    def __str__(self):
        return self.manufacturer + ": " + self.typename

    manufacturer = models.CharField(max_length=200)
    typename = models.CharField(max_length=200)
    weight = models.PositiveBigIntegerField(help_text="Weight in g")
    maxspeed = models.PositiveIntegerField(help_text="Maximum speed in km/h")
    battery_capacity = models.PositiveBigIntegerField(help_text="Battery capacity in mAh")
    control_range = models.PositiveBigIntegerField(help_text="Control range in m")
    maxcarriage = models.PositiveBigIntegerField(help_text="Maximum carriage in g")

class Drone(models.Model):
    def __str__(self):
        return "Drone: " + self.serialnumber + "(" + self.status + ")"
    dronetype = models.ForeignKey(Dronetype, on_delete=models.CASCADE)
    serialnumber = models.CharField(max_length=200, unique=True, help_text="Must be a unique text within all drones")
    carriage_weight = models.PositiveBigIntegerField(default=0, help_text="Current additional carriage in g")

    CARRIAGE_SENSORS = "SEN"
    CARRIAGE_ACTUATORS = "ACT"
    CARRIAGE_NOTHING = "NOT"
    CARRIAGE_CHOICES = [
            (CARRIAGE_SENSORS, "Sensors"),
            (CARRIAGE_ACTUATORS, "Actuators"),
            (CARRIAGE_NOTHING, "Nothing"),
    ]
    carriage_type = models.CharField(max_length=3, choices=CARRIAGE_CHOICES, default=CARRIAGE_NOTHING)
    speed = models.PositiveBigIntegerField(help_text="Current speed in km/h")
    align_roll = models.DecimalField(max_digits=3, decimal_places=2, default=000.00, help_text="Current alignment on x-axis")
    align_pitch = models.DecimalField(max_digits=3, decimal_places=2, default=000.00, help_text="Current algnment on y-axis")
    align_yaw = models.DecimalField(max_digits=3, decimal_places=2, default=000.00, help_text="Current alignment on z-axis")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Current position longitude with a precision of 6 decimal places")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="Current position latitude with a precision of 6 decimal places")
    battery_status = models.PositiveBigIntegerField(help_text="Current battery charge in mAh")
    last_seen = models.DateTimeField(help_text="Last contact to drone")
    
    STATUS_ONLINE = "ON"
    STATUS_OFFLINE = "OF"
    STATUS_ISSUES = "IS"
    STATUS_CHOICES = [
        (STATUS_ONLINE, "Online"),
        (STATUS_OFFLINE, "Offline"),
        (STATUS_ISSUES, "Issues"),
    ]
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=STATUS_OFFLINE)

