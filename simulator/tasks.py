import logging
import math
import random
from datetime import timedelta
from math import radians

from django.db import transaction
from django.utils import timezone

from dronesim.celery import app
from simulator.models import Drone, DroneDynamics, DroneType

log = logging.getLogger(__name__)

# --- Simulationsparameter ---------------------------------------------------

BATCH_SIZE = 5000
EARTH_RADIUS_KM = 6371.0
G = 9.81                      # m/s^2

# Obergrenzen je Simulationsschritt. Die Absolutwerte sind noetig, weil der
# Standard-Tick 60 s betraegt: eine reine Rate (Grad/s) waere dabei wirkungslos.
MAX_TURN_RATE_DEG_S = 30.0    # physikalische Drehrate
MAX_TURN_PER_TICK_DEG = 45.0  # wie weit sich der Kurs pro Tick aendern darf
MAX_ACCEL_KMH_S = 5.0         # physikalische Beschleunigung
MAX_SPEED_CHANGE_PER_TICK = 10.0   # km/h, Aenderung pro Tick
MAX_ROLL_DEG = 35.0           # Querneigung in der Kurve
MAX_PITCH_DEG = 25.0          # Laengsneigung beim Beschleunigen/Bremsen

# Lage wird als Momentaufnahme waehrend des Manoevers gemeldet, nicht als
# Mittelwert ueber den ganzen Tick - sonst waeren die Werte bei 60 s Raster
# physikalisch korrekt, aber praktisch immer nahe null.
ATTITUDE_WINDOW_S = 5.0

ISSUE_PROBABILITY = 0.01              # Anteil der Ticks mit Stoerungsmeldung

# --- Energiemodell ----------------------------------------------------------
# Impulstheorie fuer Drehfluegler. Der Verbrauch haengt an Abfluggewicht
# (inkl. Zuladung) und Geschwindigkeit; die Leistungskurve ist U-foermig:
# Schweben kostet viel, Reisegeschwindigkeit wenig, Hoechstgeschwindigkeit
# wieder viel (Luftwiderstand waechst mit v^3).

AIR_DENSITY_KG_M3 = 1.225        # Normatmosphaere auf Meereshoehe

#: Flaechenbelastung der Rotorkreisflaeche. Daraus wird die Rotorflaeche
#: aus dem Leergewicht abgeleitet - die Modelle haben kein Feld dafuer.
#: 8 kg/m^2 entspricht typischen Multicoptern dieser Klassen.
DISC_LOADING_KG_M2 = 8.0

#: Gesamtwirkungsgrad Akku -> Schub (Guetegrad des Rotors, Motor, Regler).
#: Kalibriert, sodass eine DJI Phantom 4 Pro rund 25 min Schwebeflug schafft.
PROPULSION_EFFICIENCY = 0.55

#: Blattwiderstand als Anteil der induzierten Schwebeleistung.
PROFILE_POWER_FRACTION = 0.30

#: Luftwiderstand: Beiwert und Stirnflaeche als Anteil der Rotorflaeche.
DRAG_COEFFICIENT = 1.0
FRONTAL_AREA_FRACTION = 0.10

#: Grundlast fuer Sensorik, Funk und Rechner, unabhaengig vom Flug.
AVIONICS_POWER_W = 5.0

#: Zellenzahl nach Leergewicht: (max_weight_g, Zellen). Bestimmt die
#: Packspannung und damit den Energieinhalt in Wh.
CELL_COUNT_BY_WEIGHT = ((250, 1), (800, 3), (1500, 4), (10 ** 9, 6))
CELL_VOLTAGE_V = 3.7

#: Reserve: unterhalb dieses Anteils der Kapazitaet landet die Drohne.
#: Tiefentladung wuerde den Akku zerstoeren.
BATTERY_RESERVE_FRACTION = 0.10

#: Laderate. 2C entspricht Schnellladung bzw. Akkuwechsel; mit 1C waeren
#: die Drohnen rund zwei Drittel der Zeit am Boden.
CHARGE_C_RATE = 2.0

# (name, latitude, longitude)
PLACES = (
    ("Frankfurt Hauptbahnhof", 50.107185833, 8.663789667),
    ("Roemerberg", 50.110924000, 8.682127000),
    ("Palmengarten", 50.120598000, 8.657251000),
    ("Eiserner Steg", 50.107699000, 8.678109000),
    ("Goethe-Haus", 50.116536000, 8.681864000),
    ("Flughafen Frankfurt", 50.050194000, 8.570487000),
    ("Opel Zoo", 50.192078000, 8.496004000),
    ("Schloss Johannisburg", 50.039364000, 8.214841000),
    ("Mainz Dom", 49.998984000, 8.276432000),
    ("Darmstadt Mathildenhoehe", 49.870867000, 8.655013000),
)

DRONE_TYPES = (
    # (manufacturer, typename, weight_g, max_speed_kmh, battery_mah, range_m, max_carriage_g)
    ("GoPro", "Karma", 1000, 56, 5100, 1500, 400),
    ("Hubsan", "X4 H107D", 50, 32, 380, 200, 50),
    ("Walkera", "Voyager 4", 2450, 80, 7500, 5000, 800),
    ("PowerVision", "PowerEgg X", 2100, 64, 5000, 3500, 500),
    ("Blade", "Chroma Camera Drone", 1630, 65, 5400, 2500, 600),
    ("DJI", "Phantom 4 Pro", 1380, 72, 5870, 7000, 500),
    ("Yuneec", "Typhoon H Pro", 1995, 70, 5400, 2000, 100),
    ("Autel Robotics", "Evo II", 1127, 72, 7100, 9000, 800),
    ("Parrot", "Anafi", 320, 55, 2700, 4000, 200),
    ("Skydio", "Skydio 2", 775, 58, 4280, 3500, 400),
    ("Syma", "X5C", 102, 40, 500, 150, 70),
    ("Cheerson", "CX-10", 25, 20, 100, 50, 30),
    ("JJRC", "H36", 22, 30, 150, 100, 20),
    ("Eachine", "E58", 96, 35, 500, 200, 50),
    ("Holy Stone", "HS100", 700, 45, 3500, 500, 500),
    ("Ryze", "Tello", 80, 28, 1100, 100, 40),
    ("Altair Aerial", "AA108", 85, 36, 750, 300, 60),
    ("Snaptain", "S5C", 120, 40, 550, 150, 80),
    ("Potensic", "D80", 450, 50, 2800, 800, 200),
    ("Contixo", "F24 Pro", 520, 60, 2500, 1200, 250),
)


# --- Geometrie --------------------------------------------------------------

def calculate_new_coordinates(longitude, latitude, speed_kmh, heading_deg,
                              from_time, to_time):
    """
    Zielpunkt auf dem Grosskreis bei konstantem Kurs und konstanter
    Geschwindigkeit ueber das Intervall [from_time, to_time].

    heading_deg: 0 = Nord, im Uhrzeigersinn (also 90 = Ost).
    Rueckgabe: (longitude, latitude) in Grad.
    """
    elapsed_h = (to_time - from_time).total_seconds() / 3600.0
    dist_km = float(speed_kmh) * elapsed_h
    if dist_km <= 0:
        return round(float(longitude), 9), round(float(latitude), 9)

    delta = dist_km / EARTH_RADIUS_KM        # zurueckgelegter Winkel
    theta = radians(float(heading_deg))
    phi1 = radians(float(latitude))
    lam1 = radians(float(longitude))

    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta)
        + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    )
    lam2 = lam1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    # Laenge auf [-180, 180] normalisieren
    lam2 = (lam2 + 3 * math.pi) % (2 * math.pi) - math.pi

    return round(math.degrees(lam2), 9), round(math.degrees(phi2), 9)


def simulate_attitude(old_yaw_deg, new_yaw_deg, old_speed_kmh, new_speed_kmh, dt_s):
    """
    Leitet Querneigung (roll) und Laengsneigung (pitch) aus der Flugbewegung ab.

    roll:  koordinierte Kurve, tan(roll) = v * omega / g
           (v in m/s, omega = Drehrate in rad/s)
    pitch: Nase runter beim Beschleunigen, tan(pitch) = -a / g

    Rueckgabe: (roll_deg, pitch_deg), jeweils begrenzt und auf 2 Stellen gerundet.
    """
    if dt_s <= 0:
        return 0.00, 0.00

    # Das Manoever selbst dauert kuerzer als der Abtastschritt.
    window = min(dt_s, ATTITUDE_WINDOW_S)

    # kuerzester Winkelweg, damit 350 -> 10 Grad eine Drehung um +20 ist
    d_yaw = (float(new_yaw_deg) - float(old_yaw_deg) + 540.0) % 360.0 - 180.0
    omega = radians(d_yaw / window)

    v_new = float(new_speed_kmh) / 3.6
    v_old = float(old_speed_kmh) / 3.6
    v_mean = (v_new + v_old) / 2.0

    roll = math.degrees(math.atan(v_mean * omega / G))
    accel = (v_new - v_old) / window
    pitch = -math.degrees(math.atan(accel / G))

    roll = max(-MAX_ROLL_DEG, min(MAX_ROLL_DEG, roll))
    pitch = max(-MAX_PITCH_DEG, min(MAX_PITCH_DEG, pitch))
    return round(roll, 2), round(pitch, 2)


def next_yaw(current_yaw_deg, dt_s):
    """Neue Blickrichtung mit begrenzter Drehrate."""
    max_turn = min(MAX_TURN_RATE_DEG_S * dt_s, MAX_TURN_PER_TICK_DEG)
    delta = random.uniform(-max_turn, max_turn)
    return round((float(current_yaw_deg) + delta) % 360.0, 2)


def next_speed(current_speed_kmh, max_speed_kmh, dt_s):
    """Neue Geschwindigkeit mit begrenzter Beschleunigung."""
    max_delta = min(MAX_ACCEL_KMH_S * dt_s, MAX_SPEED_CHANGE_PER_TICK)
    delta = random.uniform(-max_delta, max_delta)
    new_speed = float(current_speed_kmh) + delta
    return int(max(0, min(float(max_speed_kmh), round(new_speed))))


# --- Energie ----------------------------------------------------------------

def cell_count(dronetype):
    """Zellenzahl des Akkupacks, abgeleitet aus dem Leergewicht."""
    for max_weight_g, cells in CELL_COUNT_BY_WEIGHT:
        if dronetype.weight <= max_weight_g:
            return cells
    return CELL_COUNT_BY_WEIGHT[-1][1]


def pack_voltage(dronetype):
    """Nennspannung des Akkupacks in V."""
    return cell_count(dronetype) * CELL_VOLTAGE_V


def battery_energy_wh(dronetype):
    """Energieinhalt des vollen Akkus in Wh."""
    return dronetype.battery_capacity / 1000.0 * pack_voltage(dronetype)


def rotor_area_m2(dronetype):
    """Gesamte Rotorkreisflaeche, abgeleitet aus dem Leergewicht."""
    return (dronetype.weight / 1000.0) / DISC_LOADING_KG_M2


def induced_velocity(hover_induced_v, airspeed_m_s):
    """
    Induzierte Geschwindigkeit im Vorwaertsflug.

    Loest v_i = v_h^2 / sqrt(v^2 + v_i^2) iterativ. Mit steigender
    Fluggeschwindigkeit sinkt v_i - das ist der Translationsauftrieb, der
    Vorwaertsflug billiger macht als Schweben.
    """
    v_i = hover_induced_v
    for _ in range(40):
        v_next = hover_induced_v ** 2 / math.sqrt(airspeed_m_s ** 2 + v_i ** 2)
        if abs(v_next - v_i) < 1e-9:
            return v_next
        v_i = v_next
    return v_i


def power_draw_w(dronetype, carriage_weight_g, speed_kmh):
    """
    Elektrische Leistungsaufnahme in W bei gegebener Geschwindigkeit.

    P = (P_induziert + P_Blattwiderstand + P_Luftwiderstand) / Wirkungsgrad
        + Grundlast
    """
    mass_kg = (dronetype.weight + float(carriage_weight_g or 0)) / 1000.0
    thrust_n = mass_kg * G
    area = rotor_area_m2(dronetype)
    v = max(0.0, float(speed_kmh)) / 3.6

    hover_induced_v = math.sqrt(thrust_n / (2.0 * AIR_DENSITY_KG_M3 * area))
    p_induced = thrust_n * induced_velocity(hover_induced_v, v)
    p_profile = PROFILE_POWER_FRACTION * thrust_n * hover_induced_v
    p_parasite = (0.5 * AIR_DENSITY_KG_M3 * DRAG_COEFFICIENT
                  * FRONTAL_AREA_FRACTION * area * v ** 3)

    mechanical = p_induced + p_profile + p_parasite
    return mechanical / PROPULSION_EFFICIENCY + AVIONICS_POWER_W


def consumed_mah(dronetype, carriage_weight_g, speed_kmh, dt_s):
    """Verbrauch in mAh ueber dt_s Sekunden."""
    watt = power_draw_w(dronetype, carriage_weight_g, speed_kmh)
    wh = watt * (float(dt_s) / 3600.0)
    return wh / pack_voltage(dronetype) * 1000.0


def reserve_mah(dronetype):
    """Ladestand, ab dem gelandet wird."""
    return dronetype.battery_capacity * BATTERY_RESERVE_FRACTION


def charge_mah(dronetype, dt_s):
    """Nachgeladene Menge in mAh ueber dt_s Sekunden."""
    return dronetype.battery_capacity * CHARGE_C_RATE * (float(dt_s) / 3600.0)


def endurance_minutes(dronetype, carriage_weight_g, speed_kmh):
    """Restflugzeit bei vollem Akku und konstanter Geschwindigkeit."""
    usable_wh = battery_energy_wh(dronetype) * (1.0 - BATTERY_RESERVE_FRACTION)
    return usable_wh / power_draw_w(dronetype, carriage_weight_g, speed_kmh) * 60.0


def best_endurance_speed_kmh(dronetype, carriage_weight_g):
    """Geschwindigkeit minimaler Leistungsaufnahme (laengste Flugzeit)."""
    candidates = [s / 2.0 for s in range(0, int(dronetype.max_speed * 2) + 1)]
    return min(candidates,
               key=lambda s: power_draw_w(dronetype, carriage_weight_g, s))


def best_range_speed_kmh(dronetype, carriage_weight_g):
    """Geschwindigkeit minimaler Leistung pro Strecke (groesste Reichweite)."""
    candidates = [s / 2.0 for s in range(1, int(dronetype.max_speed * 2) + 1)]
    return min(candidates,
               key=lambda s: power_draw_w(dronetype, carriage_weight_g, s) / s)


def create_serial_number(dronetype):
    name = dronetype.manufacturer[0:2] + dronetype.typename[0:2]
    year = str(random.randint(2020, 2031))
    serial = ("%06x" % random.randrange(16 ** 6)).upper()
    return "-".join([name, year, serial])


# --- Simulationsschritte ----------------------------------------------------

def create_initial_drone_dynamics(drone, place_id=-1, timestamp=None):
    """
    Erzeugt den ersten DroneDynamics-Datensatz einer Drohne.
    place_id = -1 waehlt einen zufaelligen Startort aus PLACES.
    Das Objekt ist noch nicht gespeichert.
    """
    if timestamp is None:
        timestamp = timezone.now()
    place = PLACES[place_id] if place_id >= 0 else random.choice(PLACES)

    return DroneDynamics(
        drone=drone,
        timestamp=timestamp,
        last_seen=timestamp,
        speed=drone.dronetype.max_speed,
        align_roll=0.00,
        align_pitch=0.00,
        align_yaw=round(random.uniform(0, 360), 2),
        longitude=place[2],
        latitude=place[1],
        battery_status=drone.dronetype.battery_capacity,
        status=DroneDynamics.STATUS_ONLINE,
    )


def _carry_over(previous, timestamp, status, battery_status=None, last_seen=None):
    """Datensatz ohne Ortsveraenderung - fuer Ladepausen und Stillstand."""
    return DroneDynamics(
        drone=previous.drone,
        timestamp=timestamp,
        last_seen=last_seen if last_seen is not None else previous.last_seen,
        speed=0,
        align_roll=0.00,
        align_pitch=0.00,
        align_yaw=previous.align_yaw,
        longitude=previous.longitude,
        latitude=previous.latitude,
        battery_status=(previous.battery_status if battery_status is None
                        else battery_status),
        status=status,
    )


def simulate_dynamics(previous, timestamp=None, yaw=None):
    """
    Erzeugt den naechsten DroneDynamics-Datensatz aus dem vorherigen.

    Der uebergebene Datensatz wird NICHT veraendert und NICHT gespeichert -
    die Historie bleibt damit unveraenderlich. Rueckgabe ist ein noch nicht
    gespeichertes Objekt.

    Zeitbasis ist previous.timestamp. last_seen wird nur fortgeschrieben,
    wenn die Drohne im Intervall tatsaechlich Kontakt hatte.
    """
    if timestamp is None:
        timestamp = timezone.now()

    dt_s = (timestamp - previous.timestamp).total_seconds()
    if dt_s <= 0:
        raise ValueError(
            "timestamp (%s) liegt nicht nach previous.timestamp (%s)"
            % (timestamp, previous.timestamp)
        )

    dronetype = previous.drone.dronetype
    battery = float(previous.battery_status)
    capacity = float(dronetype.battery_capacity)

    # --- Am Boden: laden, bis der Akku wieder voll ist
    if previous.status == DroneDynamics.STATUS_OFFLINE:
        charged = min(capacity, battery + charge_mah(dronetype, dt_s))
        if charged >= capacity:
            return _carry_over(previous, timestamp,
                               status=DroneDynamics.STATUS_ONLINE,
                               battery_status=int(capacity),
                               last_seen=timestamp)
        return _carry_over(previous, timestamp,
                           status=DroneDynamics.STATUS_OFFLINE,
                           battery_status=int(charged))

    # --- Neue Lage bestimmen
    new_yaw = next_yaw(previous.align_yaw, dt_s) if yaw is None else round(float(yaw) % 360, 2)
    new_speed = next_speed(previous.speed, dronetype.max_speed, dt_s)

    # Bewegung mit genau der Geschwindigkeit, die auch gemeldet wird:
    # Studenten koennen so Distanz == speed * dt nachrechnen.
    new_long, new_lat = calculate_new_coordinates(
        previous.longitude, previous.latitude,
        new_speed, new_yaw,
        previous.timestamp, timestamp,
    )

    new_roll, new_pitch = simulate_attitude(
        previous.align_yaw, new_yaw, previous.speed, new_speed, dt_s
    )

    # --- Verbrauch: haengt an Abfluggewicht und Geschwindigkeit
    used = consumed_mah(dronetype, previous.drone.carriage_weight,
                        (float(previous.speed) + new_speed) / 2.0, dt_s)
    new_battery = max(0.0, battery - used)

    # --- Status und Kontakt
    if new_battery <= reserve_mah(dronetype):
        # Reserve erreicht: die Drohne landet und beginnt zu laden.
        return _carry_over(previous, timestamp,
                           status=DroneDynamics.STATUS_OFFLINE,
                           battery_status=int(new_battery),
                           last_seen=timestamp)

    if random.random() < ISSUE_PROBABILITY:
        status = DroneDynamics.STATUS_ISSUES
        last_seen = previous.last_seen          # Telemetrie unvollstaendig
    else:
        status = DroneDynamics.STATUS_ONLINE
        last_seen = timestamp

    return DroneDynamics(
        drone=previous.drone,
        timestamp=timestamp,
        last_seen=last_seen,
        speed=new_speed,
        align_roll=new_roll,
        align_pitch=new_pitch,
        align_yaw=new_yaw,
        longitude=new_long,
        latitude=new_lat,
        battery_status=int(new_battery),
        status=status,
    )


# --- Celery-Task ------------------------------------------------------------

@app.task
def init_static_drones(init_delta_min=2880, tick_delta_sec=60, n=30):
    """
    Befuellt die Datenbank mit n Drohnen und deren Telemetrie der letzten
    init_delta_min Minuten im Raster von tick_delta_sec Sekunden.

    Default: 48h Fenster, 60s Raster -> 2880 Datensaetze pro Drohne.
    """
    if DroneType.objects.count() == 0:
        DroneType.objects.bulk_create([
            DroneType(manufacturer=m, typename=t, weight=w, max_speed=s,
                      battery_capacity=b, control_range=r, max_carriage=c)
            for (m, t, w, s, b, r, c) in DRONE_TYPES
        ])
    dronetypes = list(DroneType.objects.order_by("id"))

    drones = []
    for _ in range(n):
        dronetype = random.choice(dronetypes)
        carriage_type = random.choice([Drone.CARRIAGE_SENSORS,
                                       Drone.CARRIAGE_ACTUATORS,
                                       Drone.CARRIAGE_NOTHING])
        carriage_weight = (0 if carriage_type == Drone.CARRIAGE_NOTHING
                           else random.randint(0, dronetype.max_carriage))
        drones.append(Drone(dronetype=dronetype,
                            serialnumber=create_serial_number(dronetype),
                            carriage_weight=carriage_weight,
                            carriage_type=carriage_type))
    Drone.objects.bulk_create(drones)
    drones = list(Drone.objects.select_related("dronetype").order_by("-id")[:n])

    init_delta = timedelta(minutes=init_delta_min)
    tick_delta = timedelta(seconds=tick_delta_sec)
    start_time = timezone.now() - init_delta
    steps = int(init_delta.total_seconds() // tick_delta.total_seconds())

    current = [create_initial_drone_dynamics(d, timestamp=start_time) for d in drones]
    with transaction.atomic():
        DroneDynamics.objects.bulk_create(current, batch_size=BATCH_SIZE)

    batch = []
    simulated_time = start_time
    for _ in range(steps):
        simulated_time += tick_delta
        current = [simulate_dynamics(dyn, timestamp=simulated_time) for dyn in current]
        batch.extend(current)
        if len(batch) >= BATCH_SIZE:
            with transaction.atomic():
                DroneDynamics.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            batch = []

    if batch:
        with transaction.atomic():
            DroneDynamics.objects.bulk_create(batch, batch_size=BATCH_SIZE)

    log.info("Init succeeded! %d drones, %d ticks, %d datasets", len(drones), steps, len(drones) * (steps + 1))
