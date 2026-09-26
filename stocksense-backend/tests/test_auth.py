from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.seed import seed_demo
from app.auth.users import UserRepo
from app.db.repository import PersistentStore
from app.engine import StockEngine
from app.main import create_app

pytestmark = pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SAWarning")

MANAGER = ("manager@stocksense.demo", "demo1234")
STAFF = ("staff@stocksense.demo", "demo1234")


@pytest.fixture
def client():
    eng = StockEngine(adjustment_approval_threshold=10)
    seed_demo(eng)
    return TestClient(create_app(eng, auth_required=True))


def login(c, email, password):
    r = c.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------------------------------------------------------------- login / tokens
def test_routes_need_login(client):
    assert client.get("/api/health").status_code == 200                  # public
    assert client.get("/api/dashboard/kpis").status_code == 401
    assert client.get("/api/products", headers={"X-User": "manager"}).status_code == 401
    assert client.get("/api/products",
                      headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    assert client.get("/api/products", headers=login(client, *MANAGER)).status_code == 200


def test_login_and_me(client):
    r = client.post("/api/auth/login", json={"email": "MANAGER@stocksense.demo ", "password": "demo1234"})
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role"] == "manager" and body["expires_in"] > 0
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}).json()
    assert me["email"] == "manager@stocksense.demo" and "password_hash" not in me
    assert client.post("/api/auth/login", json={"email": MANAGER[0], "password": "wrong999"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "nobody@x.com", "password": "demo1234"}).status_code == 401


def test_signup_creates_staff(client):
    r = client.post("/api/auth/signup", json={"name": "New Person", "email": "new@x.com", "password": "secret123"})
    assert r.status_code == 201 and r.json()["user"]["role"] == "staff"
    assert client.post("/api/auth/signup", json={"name": "Dup", "email": "NEW@x.com",
                                                 "password": "secret123"}).status_code == 400
    assert client.post("/api/auth/signup", json={"name": "Weak", "email": "weak@x.com",
                                                 "password": "short"}).status_code == 400
    assert client.post("/api/auth/signup", json={"name": "Bad", "email": "not-an-email",
                                                 "password": "secret123"}).status_code == 422


def test_first_user_becomes_manager():
    c = TestClient(create_app(StockEngine(), auth_required=True, users=UserRepo()))  # no users yet
    r = c.post("/api/auth/signup", json={"name": "Owner", "email": "owner@x.com", "password": "secret123"})
    assert r.json()["user"]["role"] == "manager"


# ---------------------------------------------------------------- roles
def test_staff_vs_manager_permissions(client):
    staff, mgr = login(client, *STAFF), login(client, *MANAGER)

    # staff creates a big adjustment -> needs approval; staff can't approve, manager can
    a = client.post("/api/operations/adjustments", headers=staff,
                    json={"location_id": 1, "reason": "lost", "lines": [{"product_id": 1, "qty": 0}]}).json()
    assert a["created_by"] == "staff@stocksense.demo"
    assert client.post(f"/api/operations/{a['id']}/validate", headers=staff).status_code == 403
    assert client.post(f"/api/operations/{a['id']}/approve", headers=staff).status_code == 403
    assert client.post(f"/api/operations/{a['id']}/approve", headers=mgr).json()["approved_by"] == "manager@stocksense.demo"
    assert client.post(f"/api/operations/{a['id']}/validate", headers=staff).json()["status"] == "done"

    # reverse / new location / archive / real import = managers only
    assert client.post(f"/api/operations/{a['id']}/reverse", headers=staff).status_code == 403
    assert client.post(f"/api/operations/{a['id']}/reverse", headers=mgr).status_code == 201
    assert client.post("/api/locations", headers=staff, json={"name": "X", "warehouse": "W"}).status_code == 403
    assert client.post("/api/locations", headers=mgr, json={"name": "X", "warehouse": "W"}).status_code == 201
    assert client.patch("/api/products/2", headers=staff, json={"active": False}).status_code == 403
    assert client.patch("/api/products/2", headers=staff, json={"min_qty": 12}).status_code == 200

    csv = b"name,sku\nLamp,LMP-1\n"
    files = {"file": ("p.csv", csv, "text/csv")}
    assert client.post("/api/import/products", headers=staff, files=files).status_code == 200      # preview ok
    assert client.post("/api/import/products?dry_run=false", headers=staff, files=files).status_code == 403
    assert client.post("/api/import/products?dry_run=false", headers=mgr, files=files).json()["created"] == 1


def test_user_management(client):
    staff, mgr = login(client, *STAFF), login(client, *MANAGER)
    assert client.get("/api/auth/users", headers=staff).status_code == 403
    assert len(client.get("/api/auth/users", headers=mgr).json()) == 2

    u = client.post("/api/auth/users", headers=mgr, json={
        "name": "Second Manager", "email": "m2@x.com", "password": "secret123", "role": "manager"}).json()
    assert u["role"] == "manager"
    login(client, "m2@x.com", "secret123")

    assert client.patch(f"/api/auth/users/{u['id']}", headers=mgr, json={"active": False}).json()["active"] is False
    assert client.post("/api/auth/login", json={"email": "m2@x.com", "password": "secret123"}).status_code == 403

    me_id = client.get("/api/auth/me", headers=mgr).json()["id"]
    assert client.patch(f"/api/auth/users/{me_id}", headers=mgr, json={"role": "staff"}).status_code == 400


def test_disabled_user_token_stops_working(client):
    staff, mgr = login(client, *STAFF), login(client, *MANAGER)
    staff_id = client.get("/api/auth/me", headers=staff).json()["id"]
    client.patch(f"/api/auth/users/{staff_id}", headers=mgr, json={"active": False})
    assert client.get("/api/products", headers=staff).status_code == 401


# ---------------------------------------------------------------- password reset (OTP)
def test_forgot_and_reset_password(client):
    unknown = client.post("/api/auth/forgot-password", json={"email": "nobody@x.com"}).json()
    assert unknown["demo_code"] is None                                        # doesn't leak existence

    r = client.post("/api/auth/forgot-password", json={"email": STAFF[0]}).json()
    code = r["demo_code"]
    assert len(code) == 6 and r["message"] == unknown["message"]

    bad = {"email": STAFF[0], "code": "000000" if code != "000000" else "111111", "new_password": "newpass123"}
    assert client.post("/api/auth/reset-password", json=bad).status_code == 400
    assert client.post("/api/auth/reset-password", json={**bad, "code": code, "new_password": "weak"}).status_code == 400

    ok = client.post("/api/auth/reset-password", json={**bad, "code": code})
    assert ok.status_code == 200
    assert client.post("/api/auth/login", json={"email": STAFF[0], "password": "demo1234"}).status_code == 401
    login(client, STAFF[0], "newpass123")
    assert client.post("/api/auth/reset-password", json={**bad, "code": code}).status_code == 400  # single use


def test_reset_code_expires_and_locks_after_5_tries(client):
    code = client.post("/api/auth/forgot-password", json={"email": STAFF[0]}).json()["demo_code"]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        client.post("/api/auth/reset-password", json={"email": STAFF[0], "code": wrong, "new_password": "newpass123"})
    r = client.post("/api/auth/reset-password", json={"email": STAFF[0], "code": code, "new_password": "newpass123"})
    assert r.status_code == 400 and "too many" in r.json()["detail"].lower()

    code = client.post("/api/auth/forgot-password", json={"email": STAFF[0]}).json()["demo_code"]
    acc = client.app.state.users.get_by_email(STAFF[0])
    acc.reset_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    r = client.post("/api/auth/reset-password", json={"email": STAFF[0], "code": code, "new_password": "newpass123"})
    assert r.status_code == 400


def test_change_password(client):
    staff = login(client, *STAFF)
    assert client.post("/api/auth/change-password", headers=staff,
                       json={"current_password": "nope1234", "new_password": "fresh1234"}).status_code == 400
    assert client.post("/api/auth/change-password", headers=staff,
                       json={"current_password": "demo1234", "new_password": "fresh1234"}).status_code == 200
    login(client, STAFF[0], "fresh1234")


# ---------------------------------------------------------------- users saved in the database
def test_users_persist_in_database(tmp_path):
    url = f"sqlite:///{tmp_path / 'auth.db'}"
    c = TestClient(create_app(StockEngine(store=PersistentStore(url).load()), auth_required=True))
    c.post("/api/auth/signup", json={"name": "Keeper", "email": "keep@x.com", "password": "secret123"})
    code = c.post("/api/auth/forgot-password", json={"email": "keep@x.com"}).json()["demo_code"]

    c2 = TestClient(create_app(StockEngine(store=PersistentStore(url).load()), auth_required=True))  # restart
    login(c2, "keep@x.com", "secret123")
    login(c2, *MANAGER)                                              # demo users seeded once, still there
    assert len(c2.app.state.users.all()) == 3
    # reset code issued before the restart: secret differs without JWT_SECRET, so it must be re-requested;
    # with JWT_SECRET set in .env it keeps working. Either way the account itself is intact.
    assert c2.app.state.users.get_by_email("keep@x.com").reset_code_hash is not None
