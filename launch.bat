CALL .venv\Scripts\activate
start "" http://127.0.0.1:5000
start npm run create-css
flask --app flightlog run --debug