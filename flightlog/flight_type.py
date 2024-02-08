from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

flight_type = Blueprint("flight_type", __name__)


@flight_type.route("/")
def index():
    db = get_db()
    flight_types = db.execute(
        """
        SELECT
            ft.id as id,
            ft.name as name,
            COUNT(*) as total_flights
        FROM flight_type ft
            JOIN flight f on f.flight_type_id = ft.id
        GROUP BY ft.id
        ORDER BY ft.name ASC
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
