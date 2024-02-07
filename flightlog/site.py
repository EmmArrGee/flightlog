from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

site = Blueprint("site", __name__)


@site.route("/")
def index():
    db = get_db()
    sites = db.execute(
        """
        SELECT
            s.name as name,
            c.shorty as country,
            s.elevation as elevation,
            s.is_launch as is_launch,
            s.is_landing as is_landing
        FROM site s
            JOIN country c ON s.country_id = c.id
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
        """
    ).fetchall()

    return render_template("site/create.html", countries=countries)
