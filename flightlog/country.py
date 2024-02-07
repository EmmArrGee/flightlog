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
            c.name as name,
            c.shorty as shorty
        FROM country c
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
