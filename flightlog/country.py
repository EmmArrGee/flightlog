from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

country = Blueprint("country", __name__)


@country.route("/")
def index():
    db = get_db()
    countries = db.execute(
        """
        SELECT
            c.id as id,
            c.name as name,
            c.shorty as shorty,
            COUNT(f.id) / 2 as total_flights
        FROM country c
            LEFT JOIN site s ON c.id = s.country_id
            LEFT JOIN flight f ON s.id = f.launch_site_id OR s.id = f.landing_site_id
        GROUP BY c.id
        ORDER BY c.name ASC
        """
    ).fetchall()
    return render_template("country/index.html", countries=countries)


@country.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        name = request.form["name"]
        shorty = request.form["shorty"]

        db = get_db()
        db.execute(
            """
            INSERT INTO country (name, shorty)
            VALUES (?, ?)
            """,
            (name, shorty),
        )
        db.commit()
        return redirect(url_for("country.index"))

    return render_template("country/create.html")
