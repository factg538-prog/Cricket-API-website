from flask import Flask, jsonify
import lxml
import requests
from bs4 import BeautifulSoup
import re
import time
from flask import Response
import json
from googlesearch import search #pip install googlesearch-python
from flask import render_template

app = Flask(__name__)

# ─── Common headers to mimic a real browser (fixes Cricbuzz blocking) ───────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive",
}


@app.route('/players/<player_name>', methods=['GET'])
def get_player(player_name):
    query = f"{player_name} cricbuzz"
    profile_link = None
    try:
        results = search(query, num_results=5)
        for link in results:
            if "cricbuzz.com/profiles/" in link:
                profile_link = link
                print(f"Found profile: {profile_link}")
                break

        if not profile_link:
            return jsonify({"error": "No player profile found"}), 404

    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

    try:
        # Get player profile page
        c = requests.get(profile_link, headers=HEADERS, timeout=10).text
        cric = BeautifulSoup(c, "lxml")
        profile = cric.find("div", id="playerProfile")

        if not profile:
            return jsonify({"error": "Player profile page could not be parsed. Cricbuzz may have blocked the request."}), 503

        pc = profile.find("div", class_="cb-col cb-col-100 cb-bg-white")

        # Name, country and image
        name = pc.find("h1", class_="cb-font-40").text
        country = pc.find("h3", class_="cb-font-18 text-gray").text
        image_url = None
        images = pc.findAll('img')
        for image in images:
            image_url = image['src']
            break  # Just get the first image

        # Personal information and rankings
        personal = cric.find_all("div", class_="cb-col cb-col-60 cb-lst-itm-sm")
        role = personal[2].text.strip()

        icc = cric.find_all("div", class_="cb-col cb-col-25 cb-plyr-rank text-right")
        # Batting rankings
        tb  = icc[0].text.strip()   # Test batting
        ob  = icc[1].text.strip()   # ODI batting
        twb = icc[2].text.strip()   # T20 batting

        # Bowling rankings
        tbw  = icc[3].text.strip()  # Test bowling
        obw  = icc[4].text.strip()  # ODI bowling
        twbw = icc[5].text.strip()  # T20 bowling

        # Summary of the stats
        summary = cric.find_all("div", class_="cb-plyr-tbl")
        batting = summary[0]
        bowling = summary[1]

        # Batting statistics
        bat_rows = batting.find("tbody").find_all("tr")
        batting_stats = {}
        for row in bat_rows:
            cols = row.find_all("td")
            format_name = cols[0].text.strip().lower()
            batting_stats[format_name] = {
                "matches":       cols[1].text.strip(),
                "runs":          cols[3].text.strip(),
                "highest_score": cols[5].text.strip(),
                "average":       cols[6].text.strip(),
                "strike_rate":   cols[7].text.strip(),
                "hundreds":      cols[12].text.strip(),
                "fifties":       cols[11].text.strip(),
            }

        # Bowling statistics
        bowl_rows = bowling.find("tbody").find_all("tr")
        bowling_stats = {}
        for row in bowl_rows:
            cols = row.find_all("td")
            format_name = cols[0].text.strip().lower()
            bowling_stats[format_name] = {
                "balls":                 cols[3].text.strip(),
                "runs":                  cols[4].text.strip(),
                "wickets":               cols[5].text.strip(),
                "best_bowling_innings":  cols[9].text.strip(),
                "economy":               cols[7].text.strip(),
                "five_wickets":          cols[11].text.strip(),
            }

        player_data = {
            "name":    name,
            "country": country,
            "image":   image_url,
            "role":    role,
            "rankings": {
                "batting": {"test": tb,  "odi": ob,  "t20": twb},
                "bowling": {"test": tbw, "odi": obw, "t20": twbw},
            },
            "batting_stats": batting_stats,
            "bowling_stats": bowling_stats,
        }

        return jsonify(player_data)

    except Exception as e:
        return jsonify({"error": f"Failed to fetch player data: {str(e)}"}), 500


@app.route('/schedule')
def schedule():
    try:
        link = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/international"
        source = requests.get(link, headers=HEADERS, timeout=10).text
        page = BeautifulSoup(source, "lxml")

        if not page:
            return jsonify({"error": "Failed to load schedule page. Cricbuzz may have blocked the request."}), 503

        match_containers = page.find_all("div", class_="cb-col-100 cb-col")
        matches = []

        for container in match_containers:
            date       = container.find("div", class_="cb-lv-grn-strip text-bold")
            match_info = container.find("div", class_="cb-col-100 cb-col")

            if date and match_info:
                match_date    = date.text.strip()
                match_details = match_info.text.strip()
                matches.append(f"{match_date} - {match_details}")

        if not matches:
            return jsonify({"error": "No schedule data found. Cricbuzz HTML structure may have changed."}), 503

        return jsonify(matches)

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except Exception as e:
        return jsonify({"error": f"Failed to fetch schedule: {str(e)}"}), 500


@app.route('/live')
def live_matches():
    try:
        link = "https://www.cricbuzz.com/cricket-match/live-scores"
        source = requests.get(link, headers=HEADERS, timeout=10).text
        page = BeautifulSoup(source, "lxml")

        container = page.find("div", class_="cb-col cb-col-100 cb-bg-white")

        if not container:
            return jsonify({"error": "Failed to load live scores. Cricbuzz may have blocked the request."}), 503

        matches = container.find_all("div", class_="cb-scr-wll-chvrn cb-lv-scrs-col")

        live_matches = [match.text.strip() for match in matches]

        if not live_matches:
            return jsonify({"message": "No live matches at the moment."}), 200

        return jsonify(live_matches)

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except Exception as e:
        return jsonify({"error": f"Failed to fetch live scores: {str(e)}"}), 500


@app.route('/')
def website():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
