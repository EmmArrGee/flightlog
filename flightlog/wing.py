from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

wing = Blueprint("wing", __name__)


@wing.route("/")
def index():
    db = get_db()
    wings = db.execute(
        """
        SELECT
            wm.name as manufacturer,
            wt.name as type,
            w.size_designator as size_designator,
            w.size_projected_sqm as size_projected_sqm,
            COUNT(f.id) as total_flights
        FROM wing as w
            JOIN wing_type wt ON w.wing_type_id = wt.id
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
            LEFT JOIN flight f ON w.id = f.wing_id
        GROUP BY w.id
        ORDER BY
            wm.name ASC,
            wt.name ASC,
            w.size_projected_sqm ASC
        """
    ).fetchall()
    return render_template("wing/index.html", wings=wings)


@wing.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        wing_type_id = int(request.form["wing_type_id"])
        size_designator = request.form["size"]
        size_projected_sqm = float(request.form["projected_area"])

        db = get_db()
        db.execute(
            """
            INSERT INTO wing (wing_type_id, size_designator, size_projected_sqm)
            VALUES (?, ?, ?)
            """,
            (wing_type_id, size_designator, size_projected_sqm),
        )
        db.commit()
        return redirect(url_for("wing.index"))

    db = get_db()
    types = db.execute(
        """
        SELECT
            wt.id as id,
            wt.name as name,
            wm.name as manufacturer
        FROM wing_type wt
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
        ORDER BY
            wm.name ASC,
            wt.name ASC
        """
    ).fetchall()

    return render_template("wing/create.html", types=types)
