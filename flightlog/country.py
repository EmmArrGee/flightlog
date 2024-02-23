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
            COUNT(DISTINCT f.flight_id) as total_flights,
            (SUM(f.duration_minutes) / 60) || 'h ' || (SUM(f.duration_minutes) % 60) || 'm' as total_flight_time,
            MAX(f.date) as last_visited
        FROM country c
            LEFT JOIN (
                SELECT DISTINCT
                    f.id as flight_id,
                    f.duration_minutes as duration_minutes,
                    f.date as date,
                    c.id as country_id
                FROM flight f
                    JOIN site s ON f.launch_site_id = s.id OR f.landing_site_id = s.id
                    JOIN country c ON s.country_id = c.id
            ) f ON c.id = f.country_id
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


def get_country(id):
    db = get_db()
    country = db.execute(
        """
        SELECT
            c.id as id,
            c.name as name,
            c.shorty as shorty
        FROM country c
        WHERE c.id = ?
        """,
        (id,),
    ).fetchone()

    if country is None:
        abort(404, f"Country id {id} doesn't exist.")

    return country


@country.route("/<int:id>/update", methods=("GET", "POST"))
def update(id):
    country = get_country(id)

    if request.method == "POST":
        name = request.form["name"]
        shorty = request.form["shorty"]

        db = get_db()
        db.execute(
            """
            UPDATE country
            SET name = ?, shorty = ?
            WHERE id = ?
            """,
            (name, shorty, id),
        )
        db.commit()
        return redirect(url_for("country.index"))

    db = get_db()
    can_delete = (
        db.execute(
            """
        SELECT
            COUNT(*)
        FROM site s
        WHERE s.country_id = ?
        """,
            (id,),
        ).fetchone()[0]
        == 0
    )

    return render_template("country/update.html", country=country, can_delete=can_delete)


@country.route("/<int:id>/delete", methods=("POST",))
def delete(id):
    get_country(id)
    db = get_db()
    db.execute("DELETE FROM country WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("country.index"))
