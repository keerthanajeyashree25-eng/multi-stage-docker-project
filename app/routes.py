import psycopg
from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from app.database import check_database, create_record, get_records

bp = Blueprint("main", __name__)
MAX_NAME_LENGTH = 120


def _record_json(record):
    return {
        "id": record["id"],
        "name": record["name"],
        "created_at": record["created_at"].isoformat(),
    }


def _valid_name(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= MAX_NAME_LENGTH


@bp.get("/")
def index():
    database_connected = False
    records = []

    try:
        records = get_records()
        database_connected = True
    except psycopg.Error:
        current_app.logger.exception("Could not retrieve records from PostgreSQL")

    notice = request.args.get("notice", "")
    if notice not in {"created", "invalid", "unavailable"}:
        notice = ""

    return render_template(
        "index.html",
        application_status="Running",
        database_connected=database_connected,
        records=records,
        notice=notice,
    )


@bp.post("/records")
def create_record_from_form():
    name = request.form.get("name", "").strip()
    if not _valid_name(name):
        return redirect(url_for("main.index", notice="invalid"))

    try:
        create_record(name)
    except psycopg.Error:
        current_app.logger.exception("Could not create a record from the dashboard")
        return redirect(url_for("main.index", notice="unavailable"))

    return redirect(url_for("main.index", notice="created"))


@bp.get("/health")
def health():
    try:
        check_database()
    except psycopg.Error:
        current_app.logger.exception("Health check could not reach PostgreSQL")
        return jsonify(
            status="degraded",
            application="healthy",
            database="unavailable",
        ), 503

    return jsonify(
        status="ok",
        application="healthy",
        database="connected",
    ), 200


@bp.get("/api/records")
def api_get_records():
    try:
        records = get_records()
    except psycopg.Error:
        current_app.logger.exception("API could not retrieve records from PostgreSQL")
        return jsonify(error="The database is temporarily unavailable."), 503

    return jsonify(records=[_record_json(record) for record in records]), 200


@bp.post("/api/records")
def api_create_record():
    if not request.is_json:
        return jsonify(error="Send a JSON object with a name field."), 400

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not _valid_name(payload.get("name")):
        return jsonify(
            error=f"Name is required and must be at most {MAX_NAME_LENGTH} characters."
        ), 400

    try:
        record = create_record(payload["name"].strip())
    except psycopg.Error:
        current_app.logger.exception("API could not create a record")
        return jsonify(error="The database is temporarily unavailable."), 503

    return jsonify(record=_record_json(record)), 201