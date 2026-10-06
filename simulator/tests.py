"""
Tests for DroneSim.
Execute:  docker compose run --rm web python manage.py test simulator -v 2
"""
from datetime import timedelta
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from simulator.models import Drone, DroneDynamics, DroneType
from simulator.tasks import init_static_drones

User = get_user_model()

DYNAMICS_FIELDS = {
    "drone", "timestamp", "speed", "align_roll", "align_pitch", "align_yaw",
    "longitude", "latitude", "battery_status", "last_seen", "status",
}
DRONE_FIELDS = {
    "id", "dronetype", "created", "serialnumber", "carriage_weight", "carriage_type",
}
DRONETYPE_FIELDS = {
    "id", "manufacturer", "typename", "weight", "max_speed",
    "battery_capacity", "control_range", "max_carriage",
}


def drone_id_from_url(url):
    """'https://host/api/drones/7/?format=json' -> 7"""
    return int(urlparse(url).path.rstrip("/").split("/")[-1])


def make_fleet(n_drones=3, n_ticks=5):
    """
    Legt n_drones Drohnen mit je n_ticks Datensaetzen an. Alle Drohnen teilen
    sich dieselben Zeitstempel - genau wie bei init_static_drones. Das ist der
    Fall, in dem eine Sortierung nur nach timestamp nicht eindeutig ist.
    """
    dronetype = DroneType.objects.create(
        manufacturer="TestCorp", typename="T1", weight=1000, max_speed=50,
        battery_capacity=5000, control_range=1000, max_carriage=200,
    )
    start = timezone.now() - timedelta(minutes=n_ticks)
    drones = []
    for i in range(n_drones):
        drone = Drone.objects.create(dronetype=dronetype, serialnumber=f"SN-{i}")
        drones.append(drone)
    rows = []
    for t in range(n_ticks):
        ts = start + timedelta(minutes=t)
        for drone in drones:
            rows.append(DroneDynamics(
                drone=drone, timestamp=ts, last_seen=ts, speed=10,
                longitude="8.682127000", latitude="50.110924000",
                battery_status=4000, status=DroneDynamics.STATUS_ONLINE,
            ))
    # Einfuegen in umgekehrter Reihenfolge, damit die Tabellenreihenfolge
    # nicht zufaellig schon der erwarteten Sortierung entspricht.
    DroneDynamics.objects.bulk_create(reversed(rows))
    return drones


class ApiAuthTests(TestCase):
    def setUp(self):
        make_fleet()
        self.client = APIClient()

    def test_requires_authentication(self):
        for url in ("/api/drones/", "/api/dronetypes/", "/api/dronedynamics/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)

    def test_token_authentication_works(self):
        user = User.objects.create_user("student", password="x")
        token = Token.objects.get(user=user)  # per post_save-Signal angelegt
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        self.assertEqual(self.client.get("/api/drones/").status_code, 200)

    def test_students_cannot_write(self):
        user = User.objects.create_user("student", password="x")
        self.client.force_authenticate(user)
        drone = Drone.objects.first()
        self.assertEqual(self.client.post("/api/dronetypes/", {}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/drones/{drone.pk}/").status_code, 403)
        self.assertTrue(Drone.objects.filter(pk=drone.pk).exists())


class ApiContractTests(TestCase):
    """Feldnamen und Paging-Struktur, wie sie in der Projektbeschreibung stehen."""

    def setUp(self):
        self.drones = make_fleet()
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user("student", password="x"))

    def test_paginated_envelope(self):
        data = self.client.get("/api/dronedynamics/?format=json").json()
        self.assertEqual(set(data), {"count", "next", "previous", "results"})
        self.assertEqual(len(data["results"]), 10)  # PAGE_SIZE

    def test_dronedynamics_fields(self):
        item = self.client.get("/api/dronedynamics/?format=json").json()["results"][0]
        self.assertEqual(set(item), DYNAMICS_FIELDS)

    def test_drone_fields(self):
        item = self.client.get("/api/drones/?format=json").json()["results"][0]
        self.assertEqual(set(item), DRONE_FIELDS)

    def test_dronetype_fields(self):
        item = self.client.get("/api/dronetypes/?format=json").json()["results"][0]
        self.assertEqual(set(item), DRONETYPE_FIELDS)

    def test_unknown_drone_returns_404(self):
        self.assertEqual(self.client.get("/api/999999/dynamics/").status_code, 404)


class ApiLimitTests(TestCase):
    """max_limit schuetzt den Server vor ?limit=100000 (ein Request, alle Daten)."""

    def setUp(self):
        make_fleet(n_drones=11, n_ticks=100)  # 1100 Datensaetze, mehr als max_limit
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user("student", password="x"))

    def test_limit_is_capped(self):
        data = self.client.get("/api/dronedynamics/?format=json&limit=100000").json()
        self.assertEqual(len(data["results"]), 1000)
        self.assertIsNotNone(data["next"])  # Rest bleibt per Paging erreichbar
        self.assertEqual(data["count"], 1100)

    def test_limit_below_cap_is_respected(self):
        data = self.client.get("/api/dronedynamics/?format=json&limit=25").json()
        self.assertEqual(len(data["results"]), 25)


class ApiOrderingTests(TestCase):
    """
    Durchblaettern per limit/offset muss jeden Datensatz genau einmal liefern,
    auch wenn mehrere Drohnen denselben Zeitstempel haben.
    """

    def setUp(self):
        self.drones = make_fleet(n_drones=4, n_ticks=6)  # 24 Datensaetze
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user("student", password="x"))

    def collect_all(self, url):
        items, next_url = [], url
        while next_url:
            data = self.client.get(next_url).json()
            items.extend(data["results"])
            next_url = data["next"]
        return items

    def test_dronedynamics_order_is_timestamp_then_id(self):
        expected = list(DroneDynamics.objects.order_by("timestamp", "id")
                        .values_list("drone_id", "timestamp"))
        items = self.collect_all("/api/dronedynamics/?format=json&limit=5")
        self.assertEqual(len(items), DroneDynamics.objects.count())
        got = [drone_id_from_url(i["drone"]) for i in items]
        self.assertEqual(got, [drone_id for drone_id, _ in expected])

    def test_per_drone_endpoint_is_complete_and_ordered(self):
        drone = self.drones[0]
        items = self.collect_all(f"/api/{drone.pk}/dynamics/?format=json&limit=4")
        self.assertEqual(len(items), drone.dynamics.count())
        timestamps = [i["timestamp"] for i in items]
        self.assertEqual(timestamps, sorted(timestamps))


class AdminActionTests(TestCase):
    """init und flush duerfen nur per POST und nur mit den richtigen Rechten laufen."""

    def setUp(self):
        make_fleet()
        self.student = User.objects.create_user("student", password="x")
        self.staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.admin = User.objects.create_superuser("admin", password="x")

    def test_get_is_rejected(self):
        self.client.force_login(self.admin)
        for name in ("simulator:init", "simulator:flush"):
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 405)
        self.assertTrue(DroneType.objects.exists())

    def test_flush_requires_superuser(self):
        for user in (None, self.student, self.staff):
            with self.subTest(user=user):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                self.client.post(reverse("simulator:flush"))
                self.assertTrue(DroneType.objects.exists())

    def test_flush_as_superuser(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("simulator:flush"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(DroneType.objects.exists())
        self.assertFalse(DroneDynamics.objects.exists())  # per Cascade

    def test_init_requires_staff(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("simulator:init"))
        self.assertEqual(response.status_code, 302)  # Umleitung zum Login

    def test_flush_requires_csrf_token(self):
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse("simulator:flush")).status_code, 403)
        self.assertTrue(DroneType.objects.exists())


class QueryCountTests(TestCase):
    """
    Die Zahl der Queries darf nicht mit der Zahl der Drohnen bzw. Zeilen wachsen.
    Gemessen wird bei kleiner und grosser Flotte; beide Werte muessen gleich sein.
    """

    def count_queries(self, url, n_drones, login=True):
        DroneType.objects.all().delete()
        make_fleet(n_drones=n_drones, n_ticks=3)
        if login:
            self.client.force_login(User.objects.get_or_create(username="student")[0])
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(self.client.get(url).status_code, 200)
        return len(ctx.captured_queries)

    def test_index_is_constant(self):
        small = self.count_queries("/", n_drones=2, login=False)
        large = self.count_queries("/", n_drones=20, login=False)
        self.assertEqual(small, large)

    def test_dronedynamics_page_is_constant(self):
        url = reverse("simulator:dronedynamics")
        small = self.count_queries(url, n_drones=2)
        large = self.count_queries(url, n_drones=20)
        self.assertEqual(small, large)


class DronePageTests(TestCase):
    """/simulator/<id>/dynamics: paginiert, konstante Queries, nur mit Login."""

    def setUp(self):
        self.drone = make_fleet(n_drones=1, n_ticks=120)[0]  # 120 Datensaetze
        self.url = reverse("simulator:dynamics", args=[self.drone.pk])
        self.client.force_login(User.objects.create_user("student", password="x"))

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_unknown_drone_returns_404(self):
        url = reverse("simulator:dynamics", args=[999999])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_is_paginated(self):
        response = self.client.get(self.url)
        page = response.context["page_obj"]
        self.assertEqual(len(page.object_list), 50)
        self.assertEqual(page.paginator.num_pages, 3)  # 50 + 50 + 20

    def test_pages_are_ordered_and_complete(self):
        seen = []
        for number in (1, 2, 3):
            page = self.client.get(self.url, {"page": number}).context["page_obj"]
            seen.extend(dyn.pk for dyn in page.object_list)
        expected = list(self.drone.dynamics.order_by("timestamp", "id")
                        .values_list("pk", flat=True))
        self.assertEqual(seen, expected)

    def test_query_count_does_not_grow_with_page_size(self):
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(self.url)
        # Session/User, Token, Drohne+Typ, COUNT, Seite - unabhaengig von 50 Zeilen
        self.assertLessEqual(len(ctx.captured_queries), 6)


class SimulationTests(TestCase):

    def test_init_static_drones(self):
        init_static_drones(init_delta_min=10, tick_delta_sec=60, n=3)
        self.assertEqual(Drone.objects.count(), 3)
        self.assertEqual(DroneDynamics.objects.count(), 3 * (10 + 1))

    def test_dynamics_are_plausible(self):
        init_static_drones(init_delta_min=60, tick_delta_sec=60, n=5)
        for dyn in DroneDynamics.objects.select_related("drone__dronetype"):
            dronetype = dyn.drone.dronetype
            self.assertLessEqual(dyn.speed, dronetype.max_speed)
            self.assertLessEqual(dyn.battery_status, dronetype.battery_capacity)
            self.assertTrue(-90 <= dyn.latitude <= 90)
            self.assertTrue(-180 <= dyn.longitude <= 180)
            self.assertTrue(0 <= dyn.align_yaw < 360)
            self.assertLessEqual(dyn.last_seen, dyn.timestamp)
            # Frankfurt/Rhein-Main: Breite ~50, Laenge ~8 (nicht vertauscht)
            self.assertGreater(dyn.latitude, dyn.longitude)
