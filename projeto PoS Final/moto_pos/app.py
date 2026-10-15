"""Rotas HTTP da aplicação de ponto de venda."""

from __future__ import annotations

import hmac
import os
import secrets
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import urlsplit

import click
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from moto_pos.config import get_database_path, get_secret_key
from moto_pos.db import DatabaseIntegrityError, connect, initialize_database

PAYMENT_METHODS = {"dinheiro", "cartao", "transferencia"}


def create_app(test_config: dict | None = None) -> Flask:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not test_config and os.environ.get("VERCEL") == "1" and not database_url:
        raise RuntimeError("Configure DATABASE_URL com PostgreSQL persistente antes do deploy na Vercel.")
    if database_url and not database_url.startswith(("postgres://", "postgresql://")):
        raise RuntimeError("DATABASE_URL deve usar o esquema postgres:// ou postgresql://.")
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="../public",
        static_url_path="",
    )
    app.config.from_mapping(
        SECRET_KEY=(test_config or {}).get("SECRET_KEY") or get_secret_key(),
        DATABASE=database_url or str(get_database_path()),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=3600,
    )
    if test_config:
        app.config.update(test_config)

    @app.before_request
    def open_database() -> None:
        g.db = connect(app.config["DATABASE"])
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            token = session.get("csrf_token", "")
            submitted = request.form.get("csrf_token", "")
            if not token or not submitted or not hmac.compare_digest(token, submitted):
                abort(400, description="Token de segurança inválido. Atualize a página e tente novamente.")

    @app.teardown_request
    def close_database(_error: BaseException | None) -> None:
        database = g.pop("db", None)
        if database is not None:
            database.close()

    @app.context_processor
    def csrf_context() -> dict:
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {
            "csrf_token": session.get("csrf_token", ""),
            "format_money": lambda cents: f"{cents // 100:,.0f}".replace(",", " ")
            + f",{cents % 100:02d} €",
        }

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Cria o esquema e a conta inicial a partir das variáveis de ambiente."""
        initialize_database(app.config["DATABASE"])
        click.echo("Base de dados inicializada.")

    @app.get("/login")
    def login():
        return render_template("login.html")

    @app.post("/login")
    def login_post():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = g.db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Credenciais inválidas.", "error")
            return render_template("login.html"), 401
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["csrf_token"] = secrets.token_urlsafe(32)
        destination = request.args.get("next", "")
        parsed_destination = urlsplit(destination)
        if (
            not destination.startswith("/")
            or destination.startswith("//")
            or "\\" in destination
            or parsed_destination.scheme
            or parsed_destination.netloc
        ):
            destination = url_for("dashboard")
        return redirect(destination)

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard():
        stats = {
            "available": g.db.execute(
                "SELECT COUNT(*) AS count FROM motorcycles WHERE status='disponivel'"
            ).fetchone()["count"],
            "sold": g.db.execute("SELECT COUNT(*) AS count FROM sales").fetchone()["count"],
            "revenue": g.db.execute(
                "SELECT COALESCE(SUM(total_cents), 0) AS revenue FROM sales"
            ).fetchone()["revenue"],
        }
        return render_template("dashboard.html", stats=stats)

    @app.get("/motas")
    @login_required
    def motorcycles():
        rows = g.db.execute("SELECT * FROM motorcycles ORDER BY created_at DESC, id DESC").fetchall()
        return render_template("motorcycles.html", motorcycles=rows)

    @app.route("/motas/nova", methods=["GET", "POST"])
    @login_required
    def motorcycle_new():
        if request.method == "POST":
            try:
                make = required_text("make", 80)
                model = required_text("model", 80)
                vin = required_text("vin", 32).upper()
                year = int(request.form.get("year", ""))
                condition = request.form.get("condition", "")
                price = money_to_cents(request.form.get("price", ""))
                if year < 1885 or year > datetime.now(UTC).year + 1:
                    raise ValueError("O ano indicado não é válido.")
                if condition not in {"nova", "usada"}:
                    raise ValueError("Selecione nova ou usada.")
                if not (5 <= len(vin) <= 32):
                    raise ValueError("O VIN deve ter entre 5 e 32 caracteres.")
            except (ValueError, InvalidOperation) as error:
                flash(str(error), "error")
                return render_template("motorcycle_form.html"), 400
            try:
                cursor = g.db.execute(
                    "INSERT INTO motorcycles(make, model, year, vin, condition, price_cents) VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
                    (make, model, year, vin, condition, price),
                )
            except DatabaseIntegrityError:
                flash("Já existe uma mota com esse VIN.", "error")
                return render_template("motorcycle_form.html"), 409
            audit("motorcycle.created", "motorcycle", cursor.fetchone()["id"])
            flash("Mota adicionada ao inventário.", "success")
            return redirect(url_for("motorcycles"))
        return render_template("motorcycle_form.html")

    @app.get("/clientes")
    @login_required
    def customers():
        rows = g.db.execute("SELECT * FROM customers ORDER BY LOWER(name)").fetchall()
        return render_template("customers.html", customers=rows)

    @app.route("/clientes/novo", methods=["GET", "POST"])
    @login_required
    def customer_new():
        if request.method == "POST":
            try:
                name = required_text("name", 120)
                email = request.form.get("email", "").strip()[:254] or None
                phone = request.form.get("phone", "").strip()[:40] or None
                if email and ("@" not in email or "\n" in email):
                    raise ValueError("O endereço de email não parece válido.")
            except ValueError as error:
                flash(str(error), "error")
                return render_template("customer_form.html"), 400
            cursor = g.db.execute(
                "INSERT INTO customers(name, email, phone) VALUES (?, ?, ?) RETURNING id",
                (name, email, phone),
            )
            audit("customer.created", "customer", cursor.fetchone()["id"])
            flash("Cliente registado.", "success")
            return redirect(url_for("customers"))
        return render_template("customer_form.html")

    @app.route("/vendas/nova", methods=["GET", "POST"])
    @login_required
    def sale_new():
        available = g.db.execute(
            "SELECT * FROM motorcycles WHERE status='disponivel' ORDER BY make, model"
        ).fetchall()
        customer_rows = g.db.execute("SELECT * FROM customers ORDER BY LOWER(name)").fetchall()
        if request.method == "POST":
            try:
                motorcycle_id = int(request.form.get("motorcycle_id", ""))
                customer_id = int(request.form.get("customer_id", ""))
                payment = request.form.get("payment_method", "")
                if payment not in PAYMENT_METHODS:
                    raise ValueError("Selecione um método de pagamento válido.")
                g.db.execute("BEGIN IMMEDIATE")
                bike = g.db.execute(
                    "SELECT * FROM motorcycles WHERE id=? AND status='disponivel'", (motorcycle_id,)
                ).fetchone()
                customer = g.db.execute("SELECT id FROM customers WHERE id=?", (customer_id,)).fetchone()
                if bike is None or customer is None:
                    raise ValueError("A mota já foi vendida ou o cliente não existe.")
                g.db.execute("UPDATE motorcycles SET status='vendida' WHERE id=?", (motorcycle_id,))
                cursor = g.db.execute(
                    "INSERT INTO sales(motorcycle_id, customer_id, user_id, total_cents, payment_method) VALUES (?, ?, ?, ?, ?) RETURNING id",
                    (motorcycle_id, customer_id, session["user_id"], bike["price_cents"], payment),
                )
                sale_id = cursor.fetchone()["id"]
                audit("sale.created", "sale", sale_id)
                g.db.execute("COMMIT")
                return redirect(url_for("sale_receipt", sale_id=sale_id))
            except (ValueError, DatabaseIntegrityError) as error:
                if g.db.in_transaction:
                    g.db.execute("ROLLBACK")
                flash(str(error) or "Não foi possível concluir a venda.", "error")
        return render_template("sale_form.html", motorcycles=available, customers=customer_rows)

    @app.get("/vendas/<int:sale_id>")
    @login_required
    def sale_receipt(sale_id: int):
        sale = g.db.execute(
            """SELECT s.*, m.make, m.model, m.year, m.vin, c.name AS customer_name,
                      c.email, c.phone, u.username
               FROM sales s JOIN motorcycles m ON m.id=s.motorcycle_id
               JOIN customers c ON c.id=s.customer_id JOIN users u ON u.id=s.user_id
               WHERE s.id=?""", (sale_id,)
        ).fetchone()
        if sale is None:
            abort(404)
        return render_template("receipt.html", sale=sale)

    @app.get("/vendas")
    @login_required
    def sales():
        rows = g.db.execute(
            """SELECT s.id, s.created_at, s.total_cents, s.payment_method,
                      m.make, m.model, c.name AS customer_name
               FROM sales s JOIN motorcycles m ON m.id=s.motorcycle_id
               JOIN customers c ON c.id=s.customer_id ORDER BY s.created_at DESC, s.id DESC"""
        ).fetchall()
        return render_template("sales.html", sales=rows)

    def required_text(name: str, maximum: int) -> str:
        value = request.form.get(name, "").strip()
        if not value or len(value) > maximum:
            raise ValueError(f"O campo {name} é obrigatório e tem limite de {maximum} caracteres.")
        return value

    def money_to_cents(value: str) -> int:
        amount = Decimal(value.replace(",", ".").strip())
        if not amount.is_finite() or amount < 0 or amount > Decimal("999999999.99"):
            raise ValueError("O preço deve ser um valor positivo válido.")
        quantized = amount.quantize(Decimal("0.01"))
        if quantized != amount:
            raise ValueError("O preço pode ter no máximo duas casas decimais.")
        return int(quantized * 100)

    def audit(action: str, entity_type: str, entity_id: int) -> None:
        g.db.execute(
            "INSERT INTO audit_log(user_id, action, entity_type, entity_id) VALUES (?, ?, ?, ?)",
            (session.get("user_id"), action, entity_type, entity_id),
        )

    return app
