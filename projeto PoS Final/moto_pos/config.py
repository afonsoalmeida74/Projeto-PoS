"""Configuração e validação de opções de execução."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_database_path() -> Path:
    configured = os.environ.get("DATABASE_PATH", "instance/moto_pos.sqlite3")
    path = Path(configured)
    return path if path.is_absolute() else BASE_DIR / path


def get_secret_key() -> str:
    secret = os.environ.get("SECRET_KEY", "")
    if not secret and os.environ.get("FLASK_DEBUG") == "1":
        return "development-only-secret-do-not-deploy"
    if len(secret) < 32:
        raise RuntimeError("Defina SECRET_KEY com pelo menos 32 caracteres.")
    return secret
