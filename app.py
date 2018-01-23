from flask import Flask, request, render_template, make_response, redirect
from flask_httpauth import HTTPBasicAuth
from config import app_user_login, app_user_password, debug_mode
from base64 import b64decode, b64encode
from price_estimator import get_estimations


app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

auth = HTTPBasicAuth()
user = {app_user_login: app_user_password}


@auth.get_password
def get_pw(username):
    return user.get(username)


@app.route("/", methods=["GET"])
@auth.login_required
def index():
    response = make_response(render_template("index.html", args={}))

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
                args = {"eta_text": None, "error": None}
                high_eta, low_eta, error = get_estimations(start=city + " " + start,
                                                           end=city + " " + end)
                args["error"] = error
                if not error:
                    args["eta_text"] = "Приблизна вартість від {} до {} грн.\n Середня: {} грн." \
                    .format(low_eta, high_eta, int((high_eta + low_eta) / 2))

                return render_template("index.html", args=args)
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
    app.run(host="0.0.0.0", debug=debug_mode)
