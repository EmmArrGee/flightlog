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
                wm.id as id,
                wm.name as name,
                COUNT(f.id) as total_flights
            FROM wing_manufacturer wm
                LEFT JOIN wing_type wt ON wm.id = wt.wing_manufacturer_id
                LEFT JOIN wing w ON wt.id = w.wing_type_id
                LEFT JOIN flight f ON w.id = f.wing_id
            GROUP BY wm.id
            ORDER BY wm.name ASC
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
