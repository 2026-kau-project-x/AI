import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.geo import haversine_m


@pytest.fixture()
def client():
    return TestClient(app)


WALKER = {"lat": 37.5600, "lng": 126.9900}
DEST = {"lat": 37.5700, "lng": 126.9900}  # 북쪽 약 1.1 km


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_haversine_one_degree_lat():
    # 위도 1도 ≈ 111.2 km
    assert haversine_m(37.0, 127.0, 38.0, 127.0) == pytest.approx(111_195, rel=1e-3)


# ---------------- /predict ----------------


def _predict(client, **overrides):
    body = {"requested_at": "2026-10-14T10:00:00+09:00", "location": WALKER} | overrides
    r = client.post("/api/v1/predict", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_predict_baseline_shape(client):
    data = _predict(client)
    # 평일 오전 10시, 맑음, 수요 정보 없음 → 기준값 그대로
    assert data["expected_wait_min"] == 30.0
    assert data["lower_min"] < data["expected_wait_min"] < data["upper_min"]
    assert data["model"].startswith("baseline")


def test_predict_rush_hour_and_snow_increase_wait(client):
    normal = _predict(client)["expected_wait_min"]
    rush = _predict(client, requested_at="2026-10-14T08:00:00+09:00")["expected_wait_min"]
    snow = _predict(client, weather="SNOW")["expected_wait_min"]
    assert rush > normal
    assert snow > normal


def test_predict_naive_datetime_is_kst(client):
    # 타임존 없는 08:00 은 KST 08:00 (출퇴근) 으로 해석돼야 한다
    aware = _predict(client, requested_at="2026-10-14T08:00:00+09:00")
    naive = _predict(client, requested_at="2026-10-14T08:00:00")
    assert aware == naive


def test_predict_demand_ratio_is_clamped(client):
    huge = _predict(client, pending_requests=1000, available_vehicles=1)["expected_wait_min"]
    assert huge == 90.0  # 30분 × 최대 3배


def test_predict_rejects_negative_demand(client):
    body = {"requested_at": "2026-10-14T10:00:00", "location": WALKER, "pending_requests": -1}
    assert client.post("/api/v1/predict", json=body).status_code == 422


# ---------------- /optimize ----------------


def _optimize(client, vehicle=None):
    body = {"walker": WALKER, "destination": DEST, "vehicle": vehicle}
    r = client.post("/api/v1/optimize", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_optimize_without_vehicle_walks_to_destination(client):
    data = _optimize(client)
    assert data["rendezvous"] == pytest.approx(DEST)
    assert data["vehicle_eta_s"] is None
    assert data["meet_eta_s"] == data["walk_eta_s"]


def test_optimize_vehicle_at_walker_meets_immediately(client):
    # 차량이 이미 보행자 옆에 있으면 그 자리(0%)에서 합류하는 게 최적
    data = _optimize(client, vehicle=WALKER)
    assert data["rendezvous"] == pytest.approx(WALKER)
    assert data["walk_distance_m"] == 0


def test_optimize_vehicle_near_destination_meets_in_between(client):
    # 차량이 목적지 너머에서 오면 보행자와 차량이 중간 어딘가에서 만나야 한다
    vehicle = {"lat": 37.5800, "lng": 126.9900}
    data = _optimize(client, vehicle=vehicle)
    assert WALKER["lat"] < data["rendezvous"]["lat"] <= DEST["lat"]
    assert data["meet_eta_s"] == max(data["walk_eta_s"], data["vehicle_eta_s"])


def test_optimize_rejects_invalid_coordinates(client):
    body = {"walker": {"lat": 200, "lng": 0}, "destination": DEST}
    assert client.post("/api/v1/optimize", json=body).status_code == 422
