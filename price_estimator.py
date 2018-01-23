from requests import session as requests_session
from urllib.parse import urlencode
from uber_rides.session import Session
from uber_rides.client import UberRidesClient
from config import uber_client_token, google_api_key


BASE_GEOCODE_URL = "https://maps.google.com/maps/api/geocode/json?"


def get_estimations(start, end):
    start_location = _get_coordinates_for(start)
    end_location = _get_coordinates_for(end)
    error = None
    high_eta = None
    low_eta = None
    if not start_location or not end_location:
        error = "Неможливо знайти координати для початкової та кінцевої точки."
        if not start_location and end_location:
            error = "Неможливо знайти координати для початкової точки."
        elif start_location and not end_location:
            error = "Неможливо знайти координати для кінцевої точки."
        error += " Перевірте правильність написання."
    else:
        session = Session(server_token=uber_client_token)
        client = UberRidesClient(session)
        try:
            estimation = client.get_price_estimates(
                start_latitude=start_location["lat"],
                start_longitude=start_location["lng"],
                end_latitude=end_location["lat"],
                end_longitude=end_location["lng"],
                seat_count=1
            )
            high_eta = estimation.json["prices"][0]["high_estimate"]
            low_eta = estimation.json["prices"][0]["low_estimate"]
        except Exception as e:
            error = e

    return (high_eta, low_eta, error)


def _get_coordinates_for(address):
    params = {"address": address, "sensor": "false", "key": google_api_key}
    url = BASE_GEOCODE_URL + urlencode(params)
    session = requests_session()
    session.headers["Connection"] = "close"
    response = session.get(url)
    if response.status_code == 200:
        try:
            return response.json()["results"][0]["geometry"]["location"]
        except LookupError:
            return None
