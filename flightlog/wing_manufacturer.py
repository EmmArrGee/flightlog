from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

wing_manufacturer = Blueprint("wing_manufacturer", __name__)


@wing_manufacturer.route("/")
def index():
    db = get_db()
    manufacturers = db.execute(
        """
            SELECT
                wm.name as name
            FROM wing_manufacturer wm
        """
    ).fetchall()

    return render_template("wing_manufacturer/index.html", manufacturers=manufacturers)


@wing_manufacturer.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        name = request.form["name"]

        db = get_db()
        db.execute(
            """
            INSERT INTO wing_manufacturer (name)
            VALUES (?)
            """,
            (name,),
        )
        db.commit()
        return redirect(url_for("wing_manufacturer.index"))

    return render_template("wing_manufacturer/create.html")
