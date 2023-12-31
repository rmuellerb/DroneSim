# Generated by Django 4.2.7 on 2023-11-18 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulator', '0009_alter_dronedynamics_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drone',
            name='carriage_type',
            field=models.CharField(choices=[('SEN', 'Sensors'), ('ACT', 'Actuators'), ('NOT', 'Nothing')], default='NOT', help_text='Type of carriage. SEN for sensor, ACT for actuator, and NOT for nothing.', max_length=3),
        ),
        migrations.AlterField(
            model_name='dronedynamics',
            name='status',
            field=models.CharField(choices=[('ON', 'Online'), ('OF', 'Offline'), ('IS', 'Issues')], default='OF', help_text='Status of the drone. ON for online, OF for offline, IS for issues.', max_length=2),
        ),
    ]
