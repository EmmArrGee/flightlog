from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

wing_manufacturer = Blueprint("wing_manufacturer", __name__)


@wing_manufacturer.route("/")
def index():
    sort_criteria = request.args.get("sort")
    sort_criteria_dict = {
        "name": ("wm.name", "ASC"),
        "flights": ("total_flights", "DESC"),
        "time": ("SUM(f.duration_minutes)", "DESC"),
        "date": ("last_flown", "DESC"),
    }
    sort_criteria = sort_criteria_dict.get(sort_criteria, ("wm.name", "ASC"))

    db = get_db()
    manufacturers = db.execute(
        f"""
            SELECT
                wm.id as id,
                wm.name as name,
                COUNT(f.id) as total_flights,
                (SUM(f.duration_minutes) / 60) || 'h ' || (SUM(f.duration_minutes) % 60) || 'm' as total_flight_time,
                MAX(f.date) as last_flown
            FROM wing_manufacturer wm
                LEFT JOIN wing_type wt ON wm.id = wt.wing_manufacturer_id
                LEFT JOIN wing w ON wt.id = w.wing_type_id
                LEFT JOIN flight f ON w.id = f.wing_id
            GROUP BY wm.id
            ORDER BY
                {sort_criteria[0]} {sort_criteria[1]},
                wm.name ASC,
                total_flights DESC,
                SUM(f.duration_minutes) DESC,
                last_flown DESC
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


def get_wing_manufacturer(id):
    db = get_db()
    manufacturer = db.execute(
        """
        SELECT
            wm.id as id,
            wm.name as name
        FROM wing_manufacturer wm
        WHERE wm.id = ?
        """,
        (id,),
    ).fetchone()

    if manufacturer is None:
        abort(404, f"Wing manufacturer id {id} doesn't exist.")

    return manufacturer


@wing_manufacturer.route("/<int:id>/edit", methods=("GET", "POST"))
def update(id):
    wing_manufacturer = get_wing_manufacturer(id)

    if request.method == "POST":
        name = request.form["name"]

        db = get_db()
        db.execute(
            """
            UPDATE wing_manufacturer
            SET name = ?
            WHERE id = ?
            """,
            (name, id),
        )
        db.commit()
        return redirect(url_for("wing_manufacturer.index"))

    return render_template("wing_manufacturer/update.html", wing_manufacturer=wing_manufacturer)


@wing_manufacturer.route("/<int:id>/delete", methods=("POST",))
def delete(id):
    get_wing_manufacturer(id)
    db = get_db()
    db.execute("DELETE FROM wing_manufacturer WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("wing_manufacturer.index"))
