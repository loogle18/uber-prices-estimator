from flask import Flask, request, render_template, make_response, redirect, flash, url_for, session
from flask_httpauth import HTTPBasicAuth
from config import app_user_login, app_user_password, debug_mode, app_secret_key
from base64 import b64decode, b64encode
from price_estimator import get_estimates_from_addresses, get_estimates_and_send_email
from concurrent.futures import ThreadPoolExecutor


app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
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
                    session["start"]["address"] = start
                    session["start"]["coordinates"] = start_location
                    session["end"]["address"] = end
                    session["end"]["coordinates"] = end_location
                    session["mean_eta"] = mean_eta
                else:
                    flash(error, "error")

                return redirect(url_for("index"))
    else:
        return redirect("/", code=302)


@app.route("/low_price_eta", methods=["POST"])
def low_price_eta():
    if _check_token(request.cookies.get("token")):
        form = request.form
        if form:
            email, timeout, rebate = form["email"], form["timeout"], form["rebate"]
            if email and timeout and rebate:
                if session["mean_eta"] and int(rebate) < session["mean_eta"]:
                    executor.submit(get_estimates_and_send_email,
                                    email, int(timeout), int(rebate),
                                    session["city"], session["start"],
                                    session["end"], session["mean_eta"])
                    flash("Запит на перевірку успішно відправлено. Після закінчення Ви отримаєте лист.",
                          "success-low-eta")
                elif session["mean_eta"] and int(rebate) >= session["mean_eta"]:
                    flash("Некоректні дані. Знижка має бути нижча за поточну середню ціну.",
                          "error")
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
        credentials = b64decode(token).decode("utf-8").split(":")
        return user.get(credentials[0]) == credentials[1]
    else:
        return False


if __name__ == "__main__":
    app.run(debug=debug_mode)
