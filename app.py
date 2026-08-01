from flask import Flask, render_template, request
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

#home page

@app.route("/")
def home():
    return "It works"

@app.route("/players")
def players():
    search = request.args.get("search", "")
    letter = request.args.get("letter", "")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search:
        cursor.execute("""
            SELECT player_id, player_name, role
            FROM players
            WHERE player_name LIKE %s
            ORDER BY player_name
        """, (f"%{search}%",))

    elif letter == "0-9":
        cursor.execute("""
            SELECT player_id, player_name, role
            FROM players
            WHERE player_name REGEXP '^[0-9]'
            ORDER BY player_name
        """)

    elif letter:
        cursor.execute("""
            SELECT player_id, player_name, role
            FROM players
            WHERE player_name LIKE %s
            ORDER BY player_name
        """, (letter + "%",))

    else:
        cursor.execute("""
            SELECT player_id, player_name, role
            FROM players
            ORDER BY player_name
            LIMIT 48;
        """)

    players = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("players.html", players=players, search=search)


@app.route("/player/<int:player_id>")
def player_detail(player_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT player_id, player_name, role
        FROM players
        WHERE player_id = %s
    """, (player_id,))
    player = cursor.fetchone()

    cursor.execute("""
        SELECT
            c.champion_name,
            SUM(ps.kills) AS kills,
            SUM(ps.deaths) AS deaths,
            SUM(ps.assists) AS assists,
            SUM(ps.totalgold) AS total_gold
        FROM player_statistics ps
        JOIN champions c ON ps.champion_id = c.champion_id
        WHERE ps.player_id = %s
        GROUP BY c.champion_name
        ORDER BY kills DESC
    """, (player_id,))
    stats = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("player_detail.html", player=player, stats=stats)

@app.route("/teams")
def teams():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.team_id, t.team_name, r.region_name
        FROM teams t
        JOIN regions r ON t.region_id = r.region_id
        ORDER BY r.region_name, t.team_name
    """)
    team_rows = cursor.fetchall()

    cursor.execute("""
        SELECT
            region_name,
            COUNT(*) AS team_count
        FROM teams t
        JOIN regions r ON t.region_id = r.region_id
        GROUP BY region_name
        ORDER BY team_count DESC
    """)
    region_counts = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "teams.html",
        teams=team_rows,
        region_counts=region_counts
    )

@app.route("/champions")
def champions():
    search = request.args.get("search", "")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search:
        cursor.execute("""
            SELECT c.champion_id, c.champion_name, COUNT(*) AS games_played
            FROM player_statistics ps
            JOIN champions c ON ps.champion_id = c.champion_id
            WHERE c.champion_name LIKE %s
            GROUP BY c.champion_id, c.champion_name
            ORDER BY games_played DESC
        """, (f"%{search}%",))
    else:
        cursor.execute("""
            SELECT c.champion_id, c.champion_name, COUNT(*) AS games_played
            FROM player_statistics ps
            JOIN champions c ON ps.champion_id = c.champion_id
            GROUP BY c.champion_id, c.champion_name
            ORDER BY games_played DESC
            LIMIT 24
        """)

    champion_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("champions.html", champions=champion_rows, search=search)

@app.route("/analytics")
def analytics():
    region = request.args.get("region", "All")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT region_name FROM regions ORDER BY region_name")
    region_rows = cursor.fetchall()
    regions = ["All"] + [row["region_name"] for row in region_rows]

    region_filter = ""
    params = []

    if region != "All":
        region_filter = "WHERE r.region_name = %s"
        params = [region]

    cursor.execute(f"""
        SELECT p.player_name, SUM(ps.kills) AS total_kills
        FROM player_statistics ps
        JOIN players p ON ps.player_id = p.player_id
        JOIN teams t ON ps.team_id = t.team_id
        JOIN regions r ON t.region_id = r.region_id
        {region_filter}
        GROUP BY p.player_name
        ORDER BY total_kills DESC
        LIMIT 10
    """, params)
    top_killers = cursor.fetchall()

    cursor.execute(f"""
        SELECT c.champion_name, COUNT(*) AS games_played
        FROM player_statistics ps
        JOIN champions c ON ps.champion_id = c.champion_id
        JOIN teams t ON ps.team_id = t.team_id
        JOIN regions r ON t.region_id = r.region_id
        {region_filter}
        GROUP BY c.champion_name
        ORDER BY games_played DESC
        LIMIT 10
    """, params)
    top_champions = cursor.fetchall()

    cursor.execute(f"""
        SELECT
            team_name,
            COUNT(*) AS games_played,
            SUM(team_result) AS wins,
            COUNT(*) - SUM(team_result) AS losses,
            ROUND(AVG(team_result) * 100, 2) AS win_rate
        FROM (
            SELECT
                rd.gameid,
                rd.team_name,
                MAX(rd.result) AS team_result
            FROM raw_data rd
            JOIN teams t ON rd.team_name = t.team_name
            JOIN regions r ON t.region_id = r.region_id
            {region_filter}
            GROUP BY rd.gameid, rd.team_name
        ) AS team_results
        GROUP BY team_name
        ORDER BY win_rate DESC
        LIMIT 10
    """, params)
    team_win_rates = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "analytics.html",
        regions=regions,
        selected_region=region,
        top_killers=top_killers,
        top_champions=top_champions,
        team_win_rates=team_win_rates
    )

if __name__ == "__main__":
    app.run(debug=True)