import os

from flask import Flask, url_for, redirect


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flightlog.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # setup
    from . import db

    db.init_app(app)

    from . import flight, wing, wing_type, wing_manufacturer, site, country, flight_type

    @app.route("/")
    def index():
        return redirect(url_for("flight.index"))

    app.register_blueprint(flight.flight, url_prefix="/flight")
    app.register_blueprint(wing.wing, url_prefix="/wing")
    app.register_blueprint(wing_type.wing_type, url_prefix="/wing_type")
    app.register_blueprint(wing_manufacturer.wing_manufacturer, url_prefix="/wing_manufacturer")
    app.register_blueprint(site.site, url_prefix="/site")
    app.register_blueprint(country.country, url_prefix="/country")
    app.register_blueprint(flight_type.flight_type, url_prefix="/flight_type")

    return app
