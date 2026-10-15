from __future__ import annotations

from pathlib import Path

import pytest

from moto_pos.app import create_app
from moto_pos.db import connect, initialize_database
from tests.helpers import csrf, login, seed_sale_data


def test_dashboard_requires_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_vercel_requires_persistent_database(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        create_app()


def test_public_static_asset_is_served(client):
    response = client.get("/style.css")
    assert response.status_code == 200
    assert b".button" in response.data


def test_database_bootstrap_requires_strong_admin_password(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "short")
    with pytest.raises(RuntimeError, match="12 caracteres"):
        initialize_database(tmp_path / "weak-password.sqlite3")


def test_login_and_dashboard(client):
    response = login(client)
    assert response.status_code == 302
    assert client.get("/").status_code == 200


def test_login_rejects_invalid_csrf(client):
    response = client.post("/login", data={"csrf_token": "bad", "username": "admin", "password": "test-password-123"})
    assert response.status_code == 400


def test_motorcycle_creation_rejects_duplicate_vin(app, client):
    login(client)
    seed_sale_data(app)
    token = csrf(client, "/motas/nova")
    response = client.post(
        "/motas/nova",
        data={"csrf_token": token, "make": "Honda", "model": "CB500", "year": "2023", "vin": "VIN12345", "condition": "usada", "price": "6000,00"},
    )
    assert response.status_code == 409


def test_sale_records_receipt_and_marks_motorcycle_sold(app, client):
    bike_id, customer_id, _ = seed_sale_data(app)
    login(client)
    token = csrf(client, "/vendas/nova")
    response = client.post(
        "/vendas/nova",
        data={"csrf_token": token, "motorcycle_id": bike_id, "customer_id": customer_id, "payment_method": "transferencia"},
    )
    assert response.status_code == 302
    receipt = client.get(response.headers["Location"])
    assert receipt.status_code == 200
    assert b"5 500,00" in receipt.data
    with connect(Path(app.config["DATABASE"])) as database:
        bike_status = database.execute("SELECT status FROM motorcycles WHERE id=?", (bike_id,)).fetchone()[0]
        sales_count = database.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        audit_count = database.execute("SELECT COUNT(*) FROM audit_log WHERE action='sale.created'").fetchone()[0]
    assert bike_status == "vendida"
    assert sales_count == 1
    assert audit_count == 1


def test_cannot_sell_motorcycle_twice(app, client):
    bike_id, customer_id, user_id = seed_sale_data(app)
    with connect(Path(app.config["DATABASE"])) as database:
        database.execute(
            "INSERT INTO sales(motorcycle_id, customer_id, user_id, total_cents, payment_method) VALUES (?,?,?,?,?)",
            (bike_id, customer_id, user_id, 550000, "dinheiro"),
        )
        database.execute("UPDATE motorcycles SET status='vendida' WHERE id=?", (bike_id,))
    login(client)
    token = csrf(client, "/vendas/nova")
    response = client.post(
        "/vendas/nova",
        data={"csrf_token": token, "motorcycle_id": bike_id, "customer_id": customer_id, "payment_method": "dinheiro"},
    )
    assert response.status_code == 200
    with connect(Path(app.config["DATABASE"])) as database:
        assert database.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 1
