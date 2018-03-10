from flask import Flask, request, render_template, make_response, redirect, flash, url_for, jsonify, session
from flask_httpauth import HTTPBasicAuth
from config import app_user_login, app_user_password, debug_mode, app_secret_key
from base64 import b64decode, b64encode
from price_estimator import get_estimates_from_addresses, get_estimates_and_send_email, get_estimates_from_coordinates
from concurrent.futures import ThreadPoolExecutor
from json import loads as json_loads


app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.config["JSON_AS_ASCII"] = False
app.secret_key = app_secret_key

executor = ThreadPoolExecutor(max_workers=1)
auth = HTTPBasicAuth()
user = {app_user_login: app_user_password}


@auth.get_password
def get_pw(username):
    return user.get(username)


@app.route("/", methods=["GET"])
@auth.login_required
def index():
    response = make_response(render_template("index.html"))

    credentials = request.authorization["username"] + ":" + request.authorization["password"]
    encoded_token = b64encode(credentials.encode("utf-8"))

    response.set_cookie("token", encoded_token)
    return response


@app.route("/price_eta", methods=["POST"])
def price_eta():
    if _check_token(request.cookies.get("token")):
        form = request.form
        if form:
            city, start, end = form["city"] or "Львів", form["from"], form["to"]
            if start and end:
                (high_eta, low_eta, start_location, end_location, error) = \
                get_estimates_from_addresses(start=city + " " + start,
                                             end=city + " " + end)
                if not error:
                    mean_eta = int((high_eta + low_eta) / 2)
                    eta_text = "Приблизна вартість від {} до {} грн.\n Середня: {} грн." \
                    .format(low_eta, high_eta, mean_eta)
                    flash(eta_text, "success-eta")

                    session["city"] = city
                    session["start"] = {"address": start, "coordinates": start_location}
                    session["end"] = {"address": end, "coordinates": end_location}
                    session["low_eta"] = low_eta
                    session["mean_eta"] = mean_eta
                else:
                    flash(error, "error")

                return redirect(url_for("index"))
    else:
        return redirect("/", code=302)


@app.route("/api/price_eta", methods=["POST"])
def api_price_eta():
    data = request.get_data()
    json_data = json_loads(data) if data else {}
    if _check_token(json_data.get("token")):
        slat, slng = json_data.get("slat"), json_data.get("slng")
        elat, elng = json_data.get("elat"), json_data.get("elng")

        if slat and slng and elat and elng:
            (high_eta, low_eta, error) = \
            get_estimates_from_coordinates(slat=slat, slng=slng, elat=elat, elng=elng)
            if not error:
                mean_eta = int((high_eta + low_eta) / 2)
                eta_text = "Приблизна вартість від {} до {} грн.\nСередня: {} грн." \
                .format(low_eta, high_eta, mean_eta)
                return jsonify(success=True, eta_text=eta_text)
            else:
                return jsonify(success=False, error=error)
    else:
        return jsonify(success=False, error="Необхідна авторизація!")


@app.route("/low_price_eta", methods=["POST"])
def low_price_eta():
    if _check_token(request.cookies.get("token")):
        form = request.form
        if form:
            email, timeout, rebate = form["email"], form["timeout"], form["rebate"]
            if email and timeout and rebate:
                if session["mean_eta"]:
                    executor.submit(get_estimates_and_send_email,
                                    email, int(timeout), int(rebate),
                                    session["city"], session["start"],
                                    session["end"], session["mean_eta"])
                    flash("Запит на перевірку успішно відправлено. Після закінчення Ви отримаєте лист.",
                          "success-low-eta")
                else:
                    flash("Неможливо дізнатись інформацію про попередній запит.",
                          "error")

                return redirect(url_for("index"))
    else:
        return redirect("/", code=302)


@ app.errorhandler(405)
def err_405(error):
    return redirect("/")


def _check_token(token):
    if token:
        try:
            credentials = b64decode(token).decode("utf-8").split(":")
            return user.get(credentials[0]) == credentials[1]
        except Exception as error:
            print(error)
            return False
    else:
        return False


if __name__ == "__main__":
    app.run(debug=debug_mode)
