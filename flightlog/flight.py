from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
from datetime import datetime

from flightlog.db import get_db

flight = Blueprint("flight", __name__)


@flight.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    page_size = 10

    db = get_db()
    num_flights = db.execute(
        """
        SELECT COUNT(*)
        FROM flight
        """
    ).fetchone()[0]
    page = min(max(1, page), num_flights // page_size + 1)

    flights = db.execute(
        """
        SELECT
            f.id as id,
            f.flight_no as flight_no,
            f.date as date,
            wm.name as wing_manufacturer,
            wt.name as wing_name,
            w.size_designator as wing_size, 
            laus.name as launch_site,
            lans.name as landing_site,
            laus.elevation - lans.elevation as descent,
            (f.duration_minutes / 60) || "h " || (f.duration_minutes % 60) || "m" as duration,
            ft.name as flight_type,
            f.hike_and_fly as hike_and_fly,
            f.with_skies as with_skies,
            f.comment as comment
        FROM flight f
            JOIN wing w ON f.wing_id = w.id
            JOIN wing_type wt ON w.wing_type_id = wt.id
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
            JOIN site laus ON f.launch_site_id = laus.id
            JOIN site lans ON f.landing_site_id = lans.id
            JOIN flight_type ft ON f.flight_type_id = ft.id
        ORDER BY
            flight_no DESC
        LIMIT ? OFFSET ?
        """,
        (page_size, (page - 1) * page_size),
    ).fetchall()

    first_flight_no = flights[0]["flight_no"] if len(flights) > 0 else 0
    last_flight_no = flights[-1]["flight_no"] if len(flights) > 0 else 0

    return render_template(
        "flight/index.html",
        flights=flights,
        first_item_no=first_flight_no,
        last_item_no=last_flight_no,
        total_items=num_flights,
        current_page=page,
        total_pages=(num_flights // page_size + 1),
        other_params={},
    )


@flight.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        date = request.form["date"]
        amount = int(request.form["amount"])
        wing_id = int(request.form["wing"])
        launch_site_id = int(request.form["launch_site"])
        landing_site_id = int(request.form["landing_site"])
        flight_type_id = int(request.form["flight_type"])
        hike_and_fly = True if "hike_and_fly" in request.form else False
        with_skies = True if "with_skies" in request.form else False
        comment = request.form["comment"]
        duration = None if int(request.form["duration"]) == 0 else int(request.form["duration"])

        db = get_db()
        for _ in range(amount):
            db.execute(
                """
                INSERT INTO flight (date, wing_id, launch_site_id, landing_site_id, flight_type_id, hike_and_fly, with_skies, duration_minutes, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    date,
                    wing_id,
                    launch_site_id,
                    landing_site_id,
                    flight_type_id,
                    hike_and_fly,
                    with_skies,
                    duration,
                    comment,
                ),
            )
        db.commit()
        return redirect(url_for("flight.index"))

    db = get_db()
    wings = db.execute(
        """
        SELECT
            w.id as id,
            wm.name as manufacturer,
            wt.name as type,
            w.size_designator as size_designator
        FROM wing w
            JOIN wing_type wt ON w.wing_type_id = wt.id
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
            LEFT JOIN (
                SELECT
                    w2.id as wing_id,
                    MAX(f2.date) || '-' || MAX(f2.id) as last_used
                FROM flight f2
                    JOIN wing w2 ON f2.wing_id = w2.id
                GROUP BY wing_id
            ) ranking ON ranking.wing_id = w.id
        ORDER BY ranking.last_used DESC, wm.name ASC, wt.name ASC
        """
    ).fetchall()
    launch_sites = db.execute(
        """
        SELECT
            s.id as id,
            s.name as name,
            c.shorty as country,
            s.elevation as elevation
        FROM site s
            JOIN country c ON s.country_id = c.id
            LEFT JOIN (
                SELECT
                    s2.id as site_id,
                    MAX(f.date) || '-' || MAX(f.id) as last_visited
                FROM flight f
                    JOIN site s2 on f.launch_site_id = s2.id
                WHERE
                    s2.is_launch = 1
                GROUP BY site_id
            ) ranking ON ranking.site_id = s.id
        WHERE
            s.is_launch = 1
        ORDER BY ranking.last_visited DESC, s.name ASC, c.shorty ASC
        """
    ).fetchall()
    landing_sites = db.execute(
        """
        SELECT
            s.id as id,
            s.name as name,
            c.shorty as country,
            s.elevation as elevation
        FROM site s
            JOIN country c ON s.country_id = c.id
            LEFT JOIN (
                SELECT
                    s2.id as site_id,
                    MAX(f.date) || '-' || MAX(f.id) as last_visited
                FROM flight f
                    LEFT JOIN site s2 on f.landing_site_id = s2.id
                WHERE
                    s2.is_landing = 1
                GROUP BY site_id
            ) ranking ON ranking.site_id = s.id
        WHERE
            s.is_landing = 1
        ORDER BY ranking.last_visited DESC, s.name ASC, c.shorty ASC
        """
    ).fetchall()
    flight_types = db.execute(
        """
        SELECT
            ft.id, ft.name
        FROM flight_type ft
            LEFT JOIN (
                SELECT
                    ft2.id as flight_type_id,
                    MAX(f.date) || '-' || MAX(f.id) as last_flight
                FROM flight f
                    JOIN flight_type ft2 on f.flight_type_id = ft2.id
                GROUP BY flight_type_id
            ) ranking ON ranking.flight_type_id = ft.id
        ORDER BY ranking.last_flight DESC, ft.name ASC
        """
    ).fetchall()

    return render_template(
        "flight/create.html",
        wings=wings,
        launch_sites=launch_sites,
        landing_sites=landing_sites,
        flight_types=flight_types,
        today=datetime.now().strftime("%Y-%m-%d"),
    )


def get_flight(id):
    flight = (
        get_db()
        .execute(
            """
        SELECT
            f.id as id,
            f.flight_no as flight_no,
            f.date as date,
            w.id as wing_id,
            laus.id as launch_site_id,
            lans.id as landing_site_id,
            ft.id as flight_type_id,
            f.hike_and_fly as hike_and_fly,
            f.with_skies as with_skies,
            f.duration_minutes as duration_minutes,
            f.comment as comment
        FROM flight f
            JOIN wing w ON f.wing_id = w.id
            JOIN wing_type wt ON w.wing_type_id = wt.id
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
            JOIN site laus ON f.launch_site_id = laus.id
            JOIN site lans ON f.landing_site_id = lans.id
            JOIN flight_type ft ON f.flight_type_id = ft.id
        WHERE f.id = ?
        """,
            (id,),
        )
        .fetchone()
    )

    if flight is None:
        abort(404, f"Flight ID {id} doesn't exist.")

    return flight


@flight.route("/<int:id>/update", methods=("GET", "POST"))
def update(id):
    flight = get_flight(id)

    if request.method == "POST":
        date = request.form["date"]
        wing_id = int(request.form["wing"])
        launch_site_id = int(request.form["launch_site"])
        landing_site_id = int(request.form["landing_site"])
        flight_type_id = int(request.form["flight_type"])
        hike_and_fly = True if "hike_and_fly" in request.form else False
        with_skies = True if "with_skies" in request.form else False
        comment = request.form["comment"]
        duration = None if request.form["duration"] == "" else int(request.form["duration"])

        db = get_db()
        db.execute(
            """
                UPDATE flight
                SET date = ?,
                    wing_id = ?,
                    launch_site_id = ?,
                    landing_site_id = ?,
                    flight_type_id = ?,
                    hike_and_fly = ?,
                    with_skies = ?,
                    duration_minutes = ?,
                    comment = ?
                WHERE id = ?
            """,
            (
                date,
                wing_id,
                launch_site_id,
                landing_site_id,
                flight_type_id,
                hike_and_fly,
                with_skies,
                duration,
                comment,
                id,
            ),
        )
        db.commit()
        return redirect(url_for("flight.index"))

    db = get_db()
    wings = db.execute(
        """
        SELECT
            w.id as id,
            wm.name as manufacturer,
            wt.name as type,
            w.size_designator as size_designator
        FROM wing w
            JOIN wing_type wt ON w.wing_type_id = wt.id
            JOIN wing_manufacturer wm ON wt.wing_manufacturer_id = wm.id
        ORDER BY wm.name ASC, wt.name ASC, w.size_designator ASC
        """
    ).fetchall()
    launch_sites = db.execute(
        """
        SELECT
            s.id as id,
            s.name as name,
            c.shorty as country,
            s.elevation as elevation
        FROM site s
            JOIN country c ON s.country_id = c.id
        WHERE
            s.is_launch = 1
        ORDER BY s.name ASC, c.shorty ASC
        """
    ).fetchall()
    landing_sites = db.execute(
        """
        SELECT
            s.id as id,
            s.name as name,
            c.shorty as country,
            s.elevation as elevation
        FROM site s
            JOIN country c ON s.country_id = c.id
        WHERE
            s.is_landing = 1
        ORDER BY s.name ASC, c.shorty ASC
        """
    ).fetchall()
    flight_types = db.execute(
        """
        SELECT
            ft.id, ft.name
        FROM flight_type ft
        ORDER BY ft.name ASC
        """
    ).fetchall()

    return render_template(
        "flight/update.html",
        flight=flight,
        wings=wings,
        launch_sites=launch_sites,
        landing_sites=landing_sites,
        flight_types=flight_types,
    )


@flight.route("/<int:id>/delete", methods=("POST",))
def delete(id):
    get_flight(id)
    db = get_db()
    db.execute("DELETE FROM flight WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("flight.index"))
