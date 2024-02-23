DROP TABLE IF EXISTS flight;
DROP TABLE IF EXISTS wing;
DROP TABLE IF EXISTS wing_type;
DROP TABLE IF EXISTS wing_manufacturer;
DROP TABLE IF EXISTS site;
DROP TABLE IF EXISTS country;
DROP TABLE IF EXISTS flight_type;
DROP TRIGGER IF EXISTS flight_no_generator_ins;
DROP TRIGGER IF EXISTS flight_no_generator_upd;
DROP TRIGGER IF EXISTS flight_no_generator_del;

PRAGMA foreign_keys = ON;

CREATE TABLE flight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_no INTEGER,
    date TEXT NOT NULL,
    wing_id INTEGER NOT NULL,
    launch_site_id INTEGER NOT NULL,
    landing_site_id INTEGER NOT NULL,
    flight_type_id INTEGER NOT NULL,
    comment TEXT,
    hike_and_fly INTEGER NOT NULL,
    with_skies INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL,
    FOREIGN KEY (wing_id) REFERENCES wing (id) ON DELETE RESTRICT,
    FOREIGN KEY (launch_site_id) REFERENCES site (id) ON DELETE RESTRICT,
    FOREIGN KEY (landing_site_id) REFERENCES site (id) ON DELETE RESTRICT,
    FOREIGN KEY (flight_type_id) REFERENCES flight_type (id) ON DELETE RESTRICT
);

CREATE TRIGGER flight_no_generator_ins AFTER INSERT ON flight
BEGIN
    UPDATE flight
    SET flight_no = (
        SELECT tmp.flight_no
        FROM (
            SELECT id, ROW_NUMBER() OVER(ORDER BY date ASC, id ASC) AS flight_no
            FROM flight
        ) tmp
        WHERE flight.id=tmp.id
    )
    WHERE date >= NEW.date;
END;

CREATE TRIGGER flight_no_generator_upd AFTER UPDATE ON flight
BEGIN
    UPDATE flight
    SET flight_no = (
        SELECT tmp.flight_no
        FROM (
            SELECT id, ROW_NUMBER() OVER(ORDER BY date ASC, id ASC) AS flight_no
            FROM flight
        ) tmp
        WHERE flight.id=tmp.id
    )
    WHERE date >= MIN(NEW.date, OLD.date);
END;

CREATE TRIGGER flight_no_generator_del AFTER DELETE ON flight
BEGIN
    UPDATE flight
    SET flight_no = (
        SELECT tmp.flight_no
        FROM (
            SELECT id, ROW_NUMBER() OVER(ORDER BY date ASC, id ASC) AS flight_no
            FROM flight
        ) tmp
        WHERE flight.id=tmp.id
    )
    WHERE date >= OLD.date;
END;

CREATE TABLE wing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wing_type_id INTEGER NOT NULL,
    size_designator TEXT NOT NULL,
    size_projected_sqm REAL NOT NULL,
    FOREIGN KEY (wing_type_id) REFERENCES wing_type (id) ON DELETE RESTRICT,
    UNIQUE(wing_type_id, size_designator)
);

CREATE TABLE wing_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wing_manufacturer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (wing_manufacturer_id) REFERENCES wing_manufacturer (id) ON DELETE RESTRICT,
    UNIQUE(wing_manufacturer_id, name)
);

CREATE TABLE wing_manufacturer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE site (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    country_id INTEGER NOT NULL,
    elevation INTEGER NOT NULL,
    is_launch INTEGER NOT NULL,
    is_landing INTEGER NOT NULL,
    FOREIGN KEY (country_id) REFERENCES country (id) ON DELETE RESTRICT
);

CREATE TABLE country (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    shorty TEXT UNIQUE NOT NULL
);

CREATE TABLE flight_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);