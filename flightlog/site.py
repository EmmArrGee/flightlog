from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

site = Blueprint("site", __name__)


@site.route("/")
def index():
    sort_criteria = request.args.get("sort")
    sort_criteria_dict = {
        "name": ("s.name", "ASC"),
        "country": ("c.name", "ASC"),
        "elevation": ("s.elevation", "DESC"),
        "flights": ("total_flights", "DESC"),
        "time": ("SUM(f.duration_minutes)", "DESC"),
        "date": ("last_visited", "DESC"),
    }
    sort_criteria = sort_criteria_dict.get(sort_criteria, ("s.name", "ASC"))

    db = get_db()
    sites = db.execute(
        f"""
        SELECT
            s.id as id,
            s.name as name,
            c.shorty as country,
            s.elevation as elevation,
            s.is_launch as is_launch,
            s.is_landing as is_landing,
            COUNT(DISTINCT f.id) as total_flights,
            (SUM(f.duration_minutes) / 60) || 'h ' || (SUM(f.duration_minutes) % 60) || 'm' as total_flight_time,
            MAX(f.date) as last_visited
        FROM site s
            JOIN country c ON s.country_id = c.id
            LEFT JOIN flight f ON f.launch_site_id = s.id OR f.landing_site_id = s.id
        GROUP BY s.id
        ORDER BY
            {sort_criteria[0]} {sort_criteria[1]},
            s.name ASC,
            s.elevation DESC,
            total_flights DESC,
            SUM(f.duration_minutes) DESC,
            last_visited DESC
        """
    ).fetchall()
    return render_template("site/index.html", sites=sites)


@site.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        name = request.form["name"]
        country_id = int(request.form["country"])
        elevation = int(request.form["elevation"])
        is_launch = True if "is_launch" in request.form else False
        is_landing = True if "is_landing" in request.form else False

        db = get_db()
        db.execute(
            """
            INSERT INTO site (name, country_id, elevation, is_launch, is_landing)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, country_id, elevation, is_launch, is_landing),
        )
        db.commit()
        return redirect(url_for("site.index"))

    db = get_db()
    countries = db.execute(
        """
        SELECT
            c.id as id,
            c.name as name,
            c.shorty as shorty
        FROM country c
        ORDER BY c.name ASC
        """
    ).fetchall()

    return render_template("site/create.html", countries=countries)
