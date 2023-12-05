import requests
import urllib.parse

from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session

app = Flask(__name__)

app.secret_key = "asdasfw-12312512dasd-asd"

# GLOBAL VARIABLE
CLIENT_ID = "fe5bb242561d4631855290c61802d6ae"
CLIENT_SECRET = "bb63f09847c04a9f81fb558cc18b5a48"
REDIRECT_URI = "http://localhost:4999/callback"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"


@app.route("/")
def index():
    return "Welcome to my Spotify Recommendor <a href='/login'>Login with Spotify</a>"


@app.route("/login")
def login():
    scope = "user-read-private user-read-email"

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": REDIRECT_URI,
        "show_dialog": True,
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)


@app.route("/callback")
def callback():
    if "error" in request.args:  # CHECK FOR ERROR
        return jsonify({"error": request.args["error"]})

    if "code" in request.args:  # IF NO ERROR
        req_body = {
            "code": request.args["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session["access_token"] = token_info["access_token"]
        session["refresh_token"] = token_info["refresh_token"]
        session["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]

    return redirect("/playlists")


@app.route("/playlists")
def get_playlists():
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        print("TOKEN EXPIRED")
        return redirect("/refresh-token")

    headers = {"Authorization": f"Bearer {session['access_token']}"}

    response = requests.get(API_BASE_URL + "me/playlists", headers=headers)
    playlists = response.json()

    return jsonify(playlists)


@app.route("/refresh-token")
def refresh_token():
    if "refresh_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session["access_token"] = new_token_info["access_token"]
        session["expires_at"] = (
            datetime.now().timestamp() + new_token_info["expires_in"]
        )

        return redirect("/playlists")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=4999)
