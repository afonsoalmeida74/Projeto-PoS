"""Idempotent database bootstrap run by the Vercel build command."""

from __future__ import annotations

import os

from moto_pos.db import initialize_database


def main() -> None:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url.startswith(("postgres://", "postgresql://")):
        raise RuntimeError("Configure uma DATABASE_URL PostgreSQL no ambiente de build da Vercel.")
    initialize_database(database_url)
    print("Esquema PostgreSQL e utilizador inicial verificados.")


if __name__ == "__main__":
    main()
