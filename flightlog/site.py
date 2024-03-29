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
            s.is_inofficial as is_inofficial,
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
        is_inofficial = True if "is_inofficial" in request.form else False

        db = get_db()
        db.execute(
            """
            INSERT INTO site (name, country_id, elevation, is_launch, is_landing, is_inofficial)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, country_id, elevation, is_launch, is_landing, is_inofficial),
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


def get_site(id):
    site = (
        get_db()
        .execute(
            """
            SELECT
                s.id as id,
                s.name as name,
                c.shorty as country,
                s.elevation as elevation,
                s.is_launch as is_launch,
                s.is_landing as is_landing,
                s.is_inofficial as is_inofficial
            FROM site s
                JOIN country c ON s.country_id = c.id
            WHERE s.id = ?
            """,
            (id,),
        )
        .fetchone()
    )

    if site is None:
        abort(404, f"Site ID {id} doesn't exist.")

    return site


@site.route("/<int:id>/update", methods=("GET", "POST"))
def update(id):
    site = get_site(id)

    if request.method == "POST":
        name = request.form["name"]
        country_id = int(request.form["country"])
        elevation = int(request.form["elevation"])
        is_launch = True if "is_launch" in request.form else False
        is_landing = True if "is_landing" in request.form else False
        is_inofficial = True if "is_inofficial" in request.form else False

        db = get_db()
        db.execute(
            """
            UPDATE site
            SET
                name = ?,
                country_id = ?,
                elevation = ?,
                is_launch = ?,
                is_landing = ?,
                is_inofficial = ?
            WHERE id = ?
            """,
            (name, country_id, elevation, is_launch, is_landing, is_inofficial, id),
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
    can_delete = (
        db.execute(
            """
        SELECT
            COUNT(*)
        FROM flight f
        WHERE f.launch_site_id = ? OR f.landing_site_id = ?
        """,
            (
                id,
                id,
            ),
        ).fetchone()[0]
        == 0
    )

    return render_template("site/update.html", site=site, countries=countries, can_delete=can_delete)


@site.route("/<int:id>/delete", methods=("POST",))
def delete(id):
    get_site(id)
    db = get_db()
    db.execute("DELETE FROM site WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("site.index"))
