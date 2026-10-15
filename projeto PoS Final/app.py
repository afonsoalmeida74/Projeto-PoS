"""WSGI entrypoint for Vercel's Flask runtime."""

from moto_pos.app import create_app

app = create_app()
