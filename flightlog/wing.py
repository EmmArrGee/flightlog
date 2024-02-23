from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

wing = Blueprint("wing", __name__)


@wing.route("/")
def index():
    sort_criteria = request.args.get("sort")
    sort_criteria_dict = {
        "manufacturer": ("wm.name", "ASC"),
        "type": ("wt.name", "ASC"),
        "size": ("w.size_projected_sqm", "ASC"),
        "flights": ("total_flights", "DESC"),
        "time": ("SUM(f.duration_minutes)", "DESC"),
        "date": ("last_flown", "DESC"),
    }
    sort_criteria = sort_criteria_dict.get(sort_criteria, ("wm.name", "ASC"))

    db = get_db()
    wings = db.execute(
        f"""
        SELECT
            w.id as id,
            wm.name as manufacturer,
            wt.name as type,
            w.size_designator as size_designator,
            w.size_projected_sqm as size_projected_sqm,
            COUNT(f.id) as total_flights,
            (SUM(f.duration_minutes) / 60) || 'h ' || (SUM(f.duration_minutes) % 60) || 'm' as total_flight_time,
            MAX(f.date) as last_flown
        FROM wing as w
            JOIN wing_type wt ON w.wing_type_id = wt.id
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
            LEFT JOIN flight f ON w.id = f.wing_id
        GROUP BY w.id
        ORDER BY
            {sort_criteria[0]} {sort_criteria[1]},
            wm.name ASC,
            wt.name ASC,
            w.size_projected_sqm ASC,
            total_flights DESC,
            SUM(f.duration_minutes) DESC,
            last_flown DESC
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


def get_wing(id):
    wing = (
        get_db()
        .execute(
            """
        SELECT
            w.id as id,
            wm.id as manufacturer_id,
            wt.id as wing_type_id,
            w.size_designator as size_designator,
            w.size_projected_sqm as size_projected_sqm
        FROM wing as w
            JOIN wing_type wt ON w.wing_type_id = wt.id
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
        WHERE w.id = ?
        """,
            (id,),
        )
        .fetchone()
    )

    if wing is None:
        abort(404, f"Wing ID {id} doesn't exist.")

    return wing


@wing.route("/<int:id>/update", methods=("GET", "POST"))
def update(id):
    wing = get_wing(id)

    if request.method == "POST":
        wing_type_id = int(request.form["wing_type_id"])
        size_designator = request.form["size"]
        size_projected_sqm = float(request.form["projected_area"])

        db = get_db()
        db.execute(
            """
            UPDATE wing
            SET
                wing_type_id = ?,
                size_designator = ?,
                size_projected_sqm = ?
            WHERE id = ?
            """,
            (
                wing_type_id,
                size_designator,
                size_projected_sqm,
                id,
            ),
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
        """
    ).fetchall()
    can_delete = (
        db.execute(
            """
        SELECT
            COUNT(*)
        FROM wing w
        WHERE w.wing_type_id = ?
        """,
            (id,),
        ).fetchone()[0]
        == 0
    )

    return render_template("wing/update.html", wing=wing, types=types, can_delete=can_delete)


@wing.route("/<int:id>/delete", methods=("POST",))
def delete(id):
    get_wing(id)
    db = get_db()
    db.execute("DELETE FROM wing WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("wing.index"))
