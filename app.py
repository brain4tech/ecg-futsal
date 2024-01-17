import os

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, apology

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///futsal.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    # Get Tournaments
    tournaments = db.execute(
        "SELECT * FROM tournaments ORDER BY TournamentDate DESC, TournamentId DESC")

    # Show Index page
    return render_template("index.html", tournaments=tournaments)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("geef gebruikersnaam op", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("geef wachtwoord op", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("ongeldige gebruikersnaam en/of wachtwoord", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("geef wachtwoord op", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("geef wachtwoord op", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("bevestig wachtwoord", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username is available
        if len(rows) != 0:
            return apology("gebruiker bestaat al", 400)

        # Ensure confirmation is correct
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("wachtwoorden komen niet overeen", 400)

        # Add user to the database
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            request.form.get("username"),
            generate_password_hash(request.form.get("password")),
        )

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/newtournament", methods=["GET", "POST"])
@login_required
def tournament():
    if request.method == "POST":

        # Form validation
        teams = request.form.getlist("teams")
        if len(teams) < 3:
            return apology("kies 3 of 4 teams")

        # Create new teams in DB
        team_ids = []
        for team in teams:
            team_ids.append(
                db.execute(
                    "INSERT INTO teams (TeamName, Wins, Ties, Losses, GoalsScored, GoalsConceded) VALUES (?, 0, 0, 0, 0, 0)",
                    team
                )
            )

        # Make team_ids list 4 values long by adding NULL if required
        if len(team_ids) < 4:
            team_ids.append(None)

        # Create new Tournament in DB
        tournament = db.execute(
            "INSERT INTO tournaments (TournamentDate, Rounds, Team1, Team2, Team3, Team4) VALUES (date('now'), ?, ?, ?, ?, ?)",
            request.form.get("rounds"),
            team_ids[0],
            team_ids[1],
            team_ids[2],
            team_ids[3]
        )

        # Insert tournament Id back into teams
        db.execute(
            "UPDATE teams SET TournamentId = ? WHERE TeamId in (?, ?, ?, ?)",
            tournament,
            team_ids[0],
            team_ids[1],
            team_ids[2],
            team_ids[3]
        )

        # Create match schedule
        if len(teams) == 3:
            home_sequence = [0, 1, 2]
            away_sequence = [1, 2, 0]
        elif len(teams) == 4:
            home_sequence = [1, 2, 3, 0, 3, 1]
            away_sequence = [0, 3, 1, 2, 0, 2]
        else:
            return apology("fout bij wedstrijdschema genereren")

        home_sequence = home_sequence * int(request.form.get("rounds"))
        away_sequence = away_sequence * int(request.form.get("rounds"))

        # Insert Matches in DB:
        for i in range(len(home_sequence)):
            db.execute(
                "INSERT INTO matches (TournamentId, HomeTeam, AwayTeam, time) VALUES (?, ?, ?, ?)",
                tournament,
                team_ids[home_sequence[i]],
                team_ids[away_sequence[i]],
                request.form.get("time")
        )

        # Return tournament route for this tournament
        return redirect(url_for('standings', TournamentId=tournament))

    # User reached route via GET
    else:
        return render_template("tournamentform.html")


@app.route("/standings/<int:TournamentId>", methods=["POST","GET"])
@login_required
def standings(TournamentId):
    if request.form.get("form_id") == "match":
        home_team_id = int(request.form.get("home_id"))
        away_team_id = int(request.form.get("away_id"))
        home_score = int(request.form.get("homescore"))
        print(f"CHECK STATEMENT: Home Team scored {home_score} goals")
        away_score = int(request.form.get("awayscore"))
        print(f"CHECK STATEMENT: Away Team scored {away_score} goals")

        # update match
        db.execute("UPDATE matches SET HomeTeam = ?, AwayTeam = ?, HomeGoals = ?, AwayGoals = ?, PlayedBool = 1 WHERE MatchId = ?",
            home_team_id,
            away_team_id,
            home_score,
            away_score,
            request.form.get("match_id")
        )

        # get home and away team current stats
        home = db.execute("SELECT * FROM teams WHERE TeamId = ?", home_team_id)
        away = db.execute("SELECT * FROM teams WHERE TeamId = ?", away_team_id)

        home_team_wins = int(home[0]["Wins"])
        home_team_ties = int(home[0]["Ties"])
        home_team_losses = int(home[0]["Losses"])
        home_team_scored = int(home[0]["GoalsScored"])
        home_team_conceded = int(home[0]["GoalsConceded"])

        away_team_wins = int(away[0]["Wins"])
        away_team_ties = int(away[0]["Ties"])
        away_team_losses = int(away[0]["Losses"])
        away_team_scored = int(away[0]["GoalsScored"])
        away_team_conceded = int(away[0]["GoalsConceded"])

        # update team stats
        home_team_scored += home_score
        away_team_conceded += home_score
        home_team_conceded += away_score
        away_team_scored += away_score

        if home_score == away_score:
            away_team_ties += 1
            home_team_ties += 1
        elif home_score > away_score:
            home_team_wins += 1
            away_team_losses += 1
        else:
            home_team_losses += 1
            away_team_wins += 1

        # update home team in DB
        db.execute("UPDATE teams SET Wins = ?, Ties = ?, Losses = ?, GoalsScored = ?, GoalsConceded = ? WHERE TeamId = ?",
            home_team_wins,
            home_team_ties,
            home_team_losses,
            home_team_scored,
            home_team_conceded,
            int(request.form.get("home_id"))
        )

        # update away team in DB
        db.execute("UPDATE teams SET Wins = ?, Ties = ?, Losses = ?, GoalsScored = ?, GoalsConceded = ? WHERE TeamId = ?",
            away_team_wins,
            away_team_ties,
            away_team_losses,
            away_team_scored,
            away_team_conceded,
            request.form.get("away_id")
        )

    # Get all tournament teams for rendering the standings
    teams = db.execute(
        "SELECT *, (Wins * 3 + Ties) AS Points, (GoalsScored - GoalsConceded) AS GoalBalance FROM teams WHERE TournamentId = ? ORDER BY Points DESC, GoalBalance DESC, GoalsScored DESC",
        TournamentId
    )

    # Get all remaining matches in the tournament in order
    matches = db.execute(
        "SELECT * FROM matches WHERE TournamentId = ? AND PlayedBool = 0 ORDER BY MatchId",
        TournamentId
    )


    if len(matches) != 0:
        # Get the ID for the next match
        match_id = matches[0]["MatchId"]

        # Get the team IDs for the next match
        home_team = db.execute(
            "SELECT * FROM teams WHERE TeamId = ?",
            matches[0]["HomeTeam"]
        )

        away_team = db.execute(
            "SELECT * FROM teams WHERE TeamId = ?",
            matches[0]["AwayTeam"]
        )

        # Get team names from the IDs, and format for HTML display
        home = home_team[0]["TeamName"].upper()
        away = away_team[0]["TeamName"].upper()
        next = f"Spelen: {home} vs {away}"

    else:
        # If no matches remain, display the below string in HTML
        next = "EINDSTAND"
        match_id = None

    return render_template("tournament.html",
        teams=teams, next=next, match_id=match_id,
        TournamentId=TournamentId)


@app.route("/match", methods=["POST"])
def match():
    TournamentId = request.form.get("TournamentId")
    match_id = request.form.get("match_id")
    print(f"CHECK STATEMENT: Match id for current match route {match_id}")

    if match_id == 'None':
        return redirect("/")
    # Get the match from the DB
    match = db.execute(
        "SELECT * FROM matches WHERE MatchId = ?",
        match_id
    )

    match_minutes = int(match[0]["time"])

    # Get team IDs
    home_team = db.execute(
        "SELECT * FROM teams WHERE TeamId = ?",
        match[0]["HomeTeam"]
    )
    away_team = db.execute(
        "SELECT * FROM teams WHERE TeamId = ?",
        match[0]["AwayTeam"]
    )

    # Get team names from the IDs, and format for HTML display
    home = home_team[0]["TeamName"].capitalize()
    away = away_team[0]["TeamName"].capitalize()
    home_id = home_team[0]["TeamId"]
    away_id = away_team[0]["TeamId"]

    # Render template
    return render_template("match.html",
        home=home, away=away, match_id=match_id, TournamentId=TournamentId,
        match_minutes=match_minutes,home_id=home_id, away_id=away_id)

