from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

# ─── RapidAPI Configuration ──────────────────────────────────────────────────
RAPIDAPI_KEY  = "0ad40cc796msh21064d379debff2p1db11cjsn390e5c16bc31"   # ⚠️  Replace with your new key from RapidAPI
RAPIDAPI_HOST = "cricket-api-free-data.p.rapidapi.com"
BASE_URL      = f"https://{RAPIDAPI_HOST}"

HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
    "Content-Type":    "application/json",
}


def api_get(endpoint, params=None):
    """Helper: call the RapidAPI and return parsed JSON, or raise on error."""
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def website():
    return render_template("index.html")


@app.route("/live")
def live_matches():
    """Return live match scores."""
    try:
        data = api_get("cricket-livescores")
        return jsonify(data)
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Failed to fetch live scores: {str(e)}"}), 500


@app.route("/schedule")
def schedule():
    """Return upcoming match schedule."""
    try:
        data = api_get("cricket-schedule")
        return jsonify(data)
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Failed to fetch schedule: {str(e)}"}), 500


@app.route("/players/<player_name>")
def get_player(player_name):
    """Search for a player by name and return their stats."""
    try:
        data = api_get("cricket-players", params={"name": player_name})
        if not data:
            return jsonify({"error": f"No player found for '{player_name}'"}), 404
        return jsonify(data)
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Failed to fetch player data: {str(e)}"}), 500


@app.route("/team/<team_id>")
def get_team_players(team_id):
    """Return all players for a given team ID (e.g. /team/2)."""
    try:
        data = api_get("cricket-players", params={"teamid": team_id})
        if not data:
            return jsonify({"error": f"No players found for team ID '{team_id}'"}), 404
        return jsonify(data)
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Failed to fetch team players: {str(e)}"}), 500


@app.route("/series")
def get_series():
    """Return list of cricket series/tournaments."""
    try:
        data = api_get("cricket-series")
        return jsonify(data)
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Failed to fetch series: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
