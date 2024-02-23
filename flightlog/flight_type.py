from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

flight_type = Blueprint("flight_type", __name__)


@flight_type.route("/")
def index():
    sort_criteria = request.args.get("sort")
    sort_criteria_dict = {
        "name": ("ft.name", "ASC"),
        "flights": ("total_flights", "DESC"),
        "time": ("SUM(f.duration_minutes)", "DESC"),
        "date": ("last_flight", "DESC"),
    }
    sort_criteria = sort_criteria_dict.get(sort_criteria, ("ft.name", "ASC"))

    db = get_db()
    flight_types = db.execute(
        f"""
        SELECT
            ft.id as id,
            ft.name as name,
            COUNT(f.id) as total_flights,
            (SUM(f.duration_minutes) / 60) || 'h ' || (SUM(f.duration_minutes) % 60) || 'm' as total_flight_time,
            MAX(f.date) as last_flight
        FROM flight_type ft
            LEFT JOIN flight f on f.flight_type_id = ft.id
        GROUP BY ft.id
        ORDER BY
            {sort_criteria[0]} {sort_criteria[1]},
            ft.name ASC,
            total_flights DESC,
            total_flight_time DESC,
            last_flight DESC
        """
    ).fetchall()
    return render_template("flight_type/index.html", flight_types=flight_types)


@flight_type.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        name = request.form["name"]

        db = get_db()
        db.execute(
            """
            INSERT INTO flight_type (name)
            VALUES (?)
            """,
            (name,),
        )
        db.commit()
        return redirect(url_for("flight.create"))

    return render_template("flight_type/create.html")
