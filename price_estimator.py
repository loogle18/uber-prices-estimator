from re import sub as re_sub
from requests import session as requests_session
from urllib.parse import urlencode
from uber_rides.session import Session
from uber_rides.client import UberRidesClient
from config import uber_client_token, google_api_key


BASE_GEOCODE_URL = "https://maps.google.com/maps/api/geocode/json?"
ADDRESS_CLEANER_PATTERN = "(?![\, ])(?!-)+\W"


def get_estimates_from_addresses(start, end):
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
        high_eta, low_eta, error = get_estimates_from_coordinates(
            slat=start_location["lat"], 
            slon=start_location["lng"], 
            elat=end_location["lat"], 
            elon=end_location["lng"]
        )

    return (high_eta, low_eta, error)


def get_estimates_from_coordinates(slat, slon, elat, elon):
    high_eta = None
    low_eta = None
    error = None
    session = Session(server_token=uber_client_token)
    client = UberRidesClient(session)

    try:
        estimation = client.get_price_estimates(
            start_latitude=slat,
            start_longitude=slon,
            end_latitude=elat,
            end_longitude=elon,
            seat_count=1
        )
        high_eta = int(estimation.json["prices"][0]["high_estimate"])
        low_eta = int(estimation.json["prices"][0]["low_estimate"])
    except Exception as e:
        print(e)
        error = "Щось пішло не так. Неможливо знайти координати." +\
        "Перевірте правильність написання."

    return (high_eta, low_eta, error)


def _get_coordinates_for(address):
    formatted_address = re_sub(ADDRESS_CLEANER_PATTERN, "", address.strip())
    city = formatted_address.split(" ")[0]

    if not re_sub("(%s|\W)" % city, "", formatted_address):
        return

    params = {
        "address": formatted_address,
        "sensor": "false",
        "key": google_api_key
    }
    url = BASE_GEOCODE_URL + urlencode(params)
    session = requests_session()
    session.headers["Connection"] = "close"
    response = session.get(url)
    if response.status_code == 200:
        try:
            return response.json()["results"][0]["geometry"]["location"]
        except LookupError:
            return None
