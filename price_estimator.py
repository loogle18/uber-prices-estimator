from requests import session as requests_session
from urllib.parse import urlencode
from uber_rides.session import Session
from uber_rides.client import UberRidesClient
from config import uber_client_token, google_api_key


BASE_GEOCODE_URL = "https://maps.google.com/maps/api/geocode/json?"


def get_estimations(start, end):
    start_location = get_coordinates_for(start)
    end_location = get_coordinates_for(end)
    if start_location and end_location:
        session = Session(server_token=uber_client_token)
        client = UberRidesClient(session)
        
        return client.get_price_estimates(
            start_latitude=start_location["lat"],
            start_longitude=start_location["lng"],
            end_latitude=end_location["lat"],
            end_longitude=end_location["lng"],
            seat_count=1
        )


def get_coordinates_for(address):
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
