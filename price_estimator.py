from time import sleep
from re import sub as re_sub
from requests import session as requests_session
from urllib.parse import urlencode
from uber_rides.session import Session
from uber_rides.client import UberRidesClient
from config import uber_client_token, google_api_key
from email_sender import send_email_message


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
            slng=start_location["lng"],
            elat=end_location["lat"],
            elng=end_location["lng"]
        )

    return (high_eta, low_eta, start_location, end_location, error)


def get_estimates_from_coordinates(slat, slng, elat, elng):
    high_eta = None
    low_eta = None
    error = None
    session = Session(server_token=uber_client_token)
    client = UberRidesClient(session)

    try:
        estimation = client.get_price_estimates(
            start_latitude=slat,
            start_longitude=slng,
            end_latitude=elat,
            end_longitude=elng,
            seat_count=1
        )
        high_eta = int(estimation.json["prices"][0]["high_estimate"])
        low_eta = int(estimation.json["prices"][0]["low_estimate"])
    except Exception as e:
        print(e)
        error = "Щось пішло не так. Неможливо знайти координати."
        error += "Перевірте правильність написання."

    return (high_eta, low_eta, error)


def get_estimates_and_send_email(email, timeout, rebate, city, start, end, mean_eta):
    timer = 1
    mean_prices = [mean_eta]
    success_message = None
    ride_address = "м. %s від %s до %s" % (city, start["address"], end["address"])

    while timer <= timeout:
        high_eta, low_eta, error = get_estimates_from_coordinates(
            slat=start["coordinates"]["lat"],
            slng=start["coordinates"]["lng"],
            elat=end["coordinates"]["lat"],
            elng=end["coordinates"]["lng"]
        )
        if not error:
            new_mean_eta = int((high_eta + low_eta) / 2)
            if mean_eta - new_mean_eta >= rebate:
                success_message = "Знайдено необхідну нижчу ціну для поїздки %s. " % ride_address
                success_message += "Нова вартість: %s грн." % new_mean_eta
                success_message += "\nПочаткова вартість була %s." % mean_eta
                break
            mean_prices.append(new_mean_eta)

        print("Checked %s times for email: %s and route: %s." % (timer, email, ride_address))
        sleep(60)
        timer += 1

    last_price = mean_pricesp[-1]
    mean_prices.sort()
    min_price = mean_prices[0]
    unsuccess_message = "Не вийшло знайти необхідну нижчу ціну (%s грн i нижче) для поїздки %s." % (mean_eta - rebate + 1, ride_address)
    unsuccess_message += "\nНайменша вартість поїздки, яку вдалось знайти, була %s грн." % min_price
    unsuccess_message += "\nОстання вартість поїздки була %s грн." % last_price
    unsuccess_message += "\nПочаткова вартість була %s грн." % mean_eta
    message = success_message or unsuccess_message
    send_email_message(mailto=email, message=message)


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
