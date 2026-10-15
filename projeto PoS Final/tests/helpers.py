from __future__ import annotations

import re
from pathlib import Path

from moto_pos.db import connect


def csrf(client, path="/login"):
    response = client.get(path)
    token = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert token
    return token.group(1).decode()


def login(client):
    token = csrf(client)
    return client.post(
        "/login",
        data={"csrf_token": token, "username": "admin", "password": "test-password-123"},
    )


def seed_sale_data(app, *, status="disponivel"):
    with connect(Path(app.config["DATABASE"])) as database:
        user_id = database.execute("SELECT id FROM users WHERE username='admin'").fetchone()[0]
        bike = database.execute(
            "INSERT INTO motorcycles(make,model,year,vin,condition,price_cents,status) VALUES (?,?,?,?,?,?,?)",
            ("Honda", "CB500", 2022, "VIN12345", "usada", 550000, status),
        )
        customer = database.execute(
            "INSERT INTO customers(name,email) VALUES (?,?)", ("Ana Silva", "ana@example.test")
        )
        return bike.lastrowid, customer.lastrowid, user_id
