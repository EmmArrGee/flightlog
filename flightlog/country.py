from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

country = Blueprint("country", __name__)


@country.route("/")
def index():
    sort_criteria = request.args.get("sort")
    sort_criteria_dict = {
        "name": ("c.name", "ASC"),
        "shorty": ("c.shorty", "ASC"),
        "flights": ("total_flights", "DESC"),
        "time": ("SUM(f.duration_minutes)", "DESC"),
        "date": ("last_visited", "DESC"),
    }
    sort_criteria = sort_criteria_dict.get(sort_criteria, ("c.name", "ASC"))

    db = get_db()
    countries = db.execute(
        f"""
        SELECT
            c.id as id,
            c.name as name,
            c.shorty as shorty,
            COUNT(DISTINCT f.id) as total_flights,
            (SUM(f.duration_minutes) / 60) || 'h ' || (SUM(f.duration_minutes) % 60) || 'm' as total_flight_time,
            MAX(f.date) as last_visited
        FROM country c
            LEFT JOIN site s ON c.id = s.country_id
            LEFT JOIN flight f ON s.id = f.launch_site_id OR s.id = f.landing_site_id
        GROUP BY c.id
        ORDER BY
            {sort_criteria[0]} {sort_criteria[1]},
            c.name ASC,
            c.shorty ASC,
            total_flights DESC,
            SUM(f.duration_minutes) DESC,
            last_visited DESC
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
