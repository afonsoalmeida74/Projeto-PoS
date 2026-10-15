from __future__ import annotations

import pytest

from moto_pos.app import create_app
from moto_pos.db import initialize_database


@pytest.fixture
def app(tmp_path, monkeypatch):
    database = tmp_path / "test.sqlite3"
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "test-password-123")
    initialize_database(database)
    application = create_app(
        {"TESTING": True, "SECRET_KEY": "test-secret-key-with-more-than-32-characters", "DATABASE": str(database)}
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
