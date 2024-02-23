from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from flightlog.db import get_db

wing_type = Blueprint("wing_type", __name__)


@wing_type.route("/")
def index():
    sort_criteria = request.args.get("sort")
    print(sort_criteria)
    sort_criteria_dict = {
        "name": ("wt.name", "ASC"),
        "manufacturer": ("wm.name", "ASC"),
        "flights": ("total_flights", "DESC"),
        "time": ("SUM(f.duration_minutes)", "DESC"),
        "date": ("last_flown", "DESC"),
    }
    sort_criteria = sort_criteria_dict.get(sort_criteria, ("wm.name", "ASC"))

    print(sort_criteria)

    db = get_db()
    types = db.execute(
        f"""
            SELECT
                wt.id as id,
                wt.name as name,
                wm.name as manufacturer,
                COUNT(f.id) as total_flights,
                (SUM(f.duration_minutes) / 60) || 'h ' || (SUM(f.duration_minutes) % 60) || 'm' as total_flight_time,
                MAX(f.date) as last_flown
            FROM wing_type wt
                JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
                LEFT JOIN wing w ON wt.id = w.wing_type_id
                LEFT JOIN flight f ON w.id = f.wing_id
            GROUP BY wt.id
            ORDER BY
                {sort_criteria[0]} {sort_criteria[1]},
                wm.name ASC,
                wt.name ASC,
                total_flights DESC,
                total_flight_time DESC,
                last_flown DESC
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


def get_wing_type(id):
    wing_type = (
        get_db()
        .execute(
            """
        SELECT
            wt.id as id,
            wt.name as name,
            wm.id as manufacturer_id
        FROM wing_type wt
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
        WHERE wt.id = ?
        """,
            (id,),
        )
        .fetchone()
    )

    if wing_type is None:
        abort(404, f"Wing type ID {id} doesn't exist.")

    return wing_type


@wing_type.route("/<int:id>/update", methods=("GET", "POST"))
def update(id):
    wing_type = get_wing_type(id)

    if request.method == "POST":
        manufacturer_id = int(request.form["manufacturer_id"])
        name = request.form["name"]

        db = get_db()
        db.execute(
            """
                UPDATE wing_type
                SET wing_manufacturer_id = ?,
                    name = ?
                WHERE id = ?
            """,
            (
                manufacturer_id,
                name,
                id,
            ),
        )
        db.commit()
        return redirect(url_for("wing_type.index"))

    db = get_db()
    manufacturers = db.execute(
        """
        SELECT
            wm.id, wm.name
        FROM wing_manufacturer wm
        ORDER BY wm.name ASC
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

    return render_template(
        "wing_type/update.html", wing_type=wing_type, manufacturers=manufacturers, can_delete=can_delete
    )


@wing_type.route("/<int:id>/delete", methods=("POST",))
def delete(id):
    get_wing_type(id)
    db = get_db()
    db.execute("DELETE FROM wing_type WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("wing_type.index"))
