# Generated by Django 4.2.3 on 2023-07-31 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulator', '0008_alter_dronedynamics_latitude_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dronedynamics',
            name='timestamp',
            field=models.DateTimeField(help_text='Timestamp of this data'),
        ),
    ]
