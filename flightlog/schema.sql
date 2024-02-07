DROP TABLE IF EXISTS flight;
DROP TABLE IF EXISTS wing;
DROP TABLE IF EXISTS wing_type;
DROP TABLE IF EXISTS wing_manufacturer;
DROP TABLE IF EXISTS site;
DROP TABLE IF EXISTS country;
DROP TABLE IF EXISTS flight_type;


CREATE TABLE flight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    wing_id INTEGER NOT NULL,
    launch_site_id INTEGER NOT NULL,
    landing_site_id INTEGER NOT NULL,
    flight_type_id INTEGER NOT NULL,
    comment TEXT,
    hike_and_fly INTEGER NOT NULL,
    with_skies INTEGER NOT NULL,
    duration_minutes INTEGER,
    FOREIGN KEY (wing_id) REFERENCES wing (id),
    FOREIGN KEY (launch_site_id) REFERENCES site (id),
    FOREIGN KEY (landing_site_id) REFERENCES site (id),
    FOREIGN KEY (flight_type_id) REFERENCES flight_type (id)
);

CREATE TABLE wing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wing_type_id INTEGER NOT NULL,
    size_designator TEXT NOT NULL,
    size_projected_sqm REAL NOT NULL,
    FOREIGN KEY (wing_type_id) REFERENCES wing_type (id)
);

CREATE TABLE wing_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wing_manufacturer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (wing_manufacturer_id) REFERENCES wing_manufacturer (id)
);

CREATE TABLE wing_manufacturer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE site (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country_id INTEGER NOT NULL,
    elevation INTEGER NOT NULL,
    is_launch INTEGER NOT NULL,
    is_landing INTEGER NOT NULL,
    FOREIGN KEY (country_id) REFERENCES country (id)
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