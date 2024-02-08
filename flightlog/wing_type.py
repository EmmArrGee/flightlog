from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

wing_type = Blueprint("wing_type", __name__)


@wing_type.route("/")
def index():
    db = get_db()
    types = db.execute(
        """
            SELECT
                wt.id as id,
                wt.name as name,
                wm.name as manufacturer,
                COUNT(f.id) as total_flights
            FROM wing_type wt
                JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
                LEFT JOIN wing w ON wt.id = w.wing_type_id
                LEFT JOIN flight f ON w.id = f.wing_id
            GROUP BY wt.id
            ORDER BY
                wm.name ASC,
                wt.name ASC
        """
    ).fetchall()

    return render_template("wing_type/index.html", types=types)


@wing_type.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        name = request.form["name"]
        manufacturer_id = int(request.form["manufacturer_id"])

        db = get_db()
        db.execute(
            """
            INSERT INTO wing_type (name, wing_manufacturer_id)
            VALUES (?, ?)
            """,
            (name, manufacturer_id),
        )
        db.commit()

        return redirect(url_for("wing_type.index"))

    db = get_db()
    manufacturers = db.execute(
        """
        SELECT
            wm.id as id,
            wm.name as name
        FROM wing_manufacturer wm
        ORDER BY wm.name ASC
        """
    ).fetchall()

    return render_template("wing_type/create.html", manufacturers=manufacturers)
