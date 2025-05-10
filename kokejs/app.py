import sqlite3
from flask import Flask, render_template, request, redirect, url_for  # Added missing imports

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('hockey.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS Teams (
                 team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 city TEXT NOT NULL,
                 league TEXT,
                 founded_year INTEGER,
                 arena TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Players (
                 player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 first_name TEXT NOT NULL,
                 last_name TEXT NOT NULL,
                 birth_date TEXT,
                 position TEXT,
                 jersey_number INTEGER,
                 team_id INTEGER,
                 is_nhl_player BOOLEAN,
                 FOREIGN KEY (team_id) REFERENCES Teams(team_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Games (
                 game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 home_team_id INTEGER NOT NULL,
                 away_team_id INTEGER NOT NULL,
                 game_date TEXT NOT NULL,
                 game_type TEXT,
                 location TEXT,
                 score TEXT,
                 FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
                 FOREIGN KEY (away_team_id) REFERENCES Teams(team_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Statistics (
                 stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 player_id INTEGER NOT NULL,
                 game_id INTEGER NOT NULL,
                 goals INTEGER DEFAULT 0,
                 assists INTEGER DEFAULT 0,
                 plus_minus INTEGER DEFAULT 0,
                 penalty_minutes INTEGER DEFAULT 0,
                 saves INTEGER DEFAULT 0,
                 shots_against INTEGER DEFAULT 0,
                 FOREIGN KEY (player_id) REFERENCES Players(player_id),
                 FOREIGN KEY (game_id) REFERENCES Games(game_id))''')
    
    # Insert sample data if tables are empty
    if not c.execute('SELECT 1 FROM Teams LIMIT 1').fetchone():
        c.execute("INSERT INTO Teams (name, city, league, founded_year, arena) VALUES ('Dinamo Rīga', 'Riga', 'KHL', 2008, 'Arena Riga')")
        c.execute("INSERT INTO Teams (name, city, league, founded_year, arena) VALUES ('HK Liepāja', 'Liepāja', 'Latvian Hockey League', 2014, 'Liepāja Olympic Center')")
    
    if not c.execute('SELECT 1 FROM Players LIMIT 1').fetchone():
        c.execute("INSERT INTO Players (first_name, last_name, birth_date, position, jersey_number, team_id, is_nhl_player) VALUES ('Elvis', 'Merzļikins', '1994-04-13', 'Goalie', 90, 1, 1)")
        c.execute("INSERT INTO Players (first_name, last_name, birth_date, position, jersey_number, team_id, is_nhl_player) VALUES ('Rodrigo', 'Ābols', '1996-01-05', 'Forward', 9, 1, 0)")
    
    if not c.execute('SELECT 1 FROM Games LIMIT 1').fetchone():
        c.execute("INSERT INTO Games (home_team_id, away_team_id, game_date, game_type, location, score) VALUES (1, 2, '2023-10-15', 'Regular', 'Arena Riga', '4-2')")
    
    if not c.execute('SELECT 1 FROM Statistics LIMIT 1').fetchone():
        c.execute("INSERT INTO Statistics (player_id, game_id, goals, assists, plus_minus, penalty_minutes, saves, shots_against) VALUES (1, 1, 0, 0, 0, 0, 28, 30)")
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/')
def home():
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    stats = {
        'players_count': conn.execute('SELECT COUNT(*) FROM Players').fetchone()[0],
        'teams_count': conn.execute('SELECT COUNT(*) FROM Teams').fetchone()[0],
        'games_count': conn.execute('SELECT COUNT(*) FROM Games').fetchone()[0]
    }
    
    recent_games = conn.execute('''
        SELECT g.game_date, ht.name as home_team, at.name as away_team, g.score
        FROM Games g
        JOIN Teams ht ON g.home_team_id = ht.team_id
        JOIN Teams at ON g.away_team_id = at.team_id
        ORDER BY g.game_date DESC
        LIMIT 3
    ''').fetchall()
    
    conn.close()
    return render_template('index.html', stats=stats, recent_games=recent_games)

@app.route('/players')
def players():
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    players = conn.execute('''
        SELECT p.*, t.name as team_name
        FROM Players p
        LEFT JOIN Teams t ON p.team_id = t.team_id
    ''').fetchall()
    
    conn.close()
    return render_template('players.html', players=players)

@app.route('/player/<int:player_id>')
def player_detail(player_id):
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    player = conn.execute('''
        SELECT p.*, t.name as team_name
        FROM Players p
        LEFT JOIN Teams t ON p.team_id = t.team_id
        WHERE p.player_id = ?
    ''', (player_id,)).fetchone()
    
    stats = conn.execute('''
        SELECT s.*, g.game_date, ht.name as home_team, at.name as away_team, g.score
        FROM Statistics s
        JOIN Games g ON s.game_id = g.game_id
        JOIN Teams ht ON g.home_team_id = ht.team_id
        JOIN Teams at ON g.away_team_id = at.team_id
        WHERE s.player_id = ?
        ORDER BY g.game_date DESC
    ''', (player_id,)).fetchall()
    
    career_totals = conn.execute('''
        SELECT SUM(goals) as total_goals,
               SUM(assists) as total_assists,
               SUM(penalty_minutes) as total_pim,
               SUM(saves) as total_saves,
               SUM(shots_against) as total_shots_against
        FROM Statistics
        WHERE player_id = ?
    ''', (player_id,)).fetchone()
    
    conn.close()
    
    return render_template('player_detail.html', 
                         player=player, 
                         stats=stats,
                         totals=career_totals)

@app.route('/games')
def games():
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    # Debug: Print all tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("Database tables:", [t['name'] for t in tables])
    
    # Debug: Print teams
    teams = conn.execute("SELECT * FROM Teams").fetchall()
    print("Teams:", [dict(t) for t in teams])
    
    games = conn.execute('''
        SELECT g.*, ht.name as home_team, at.name as away_team
        FROM Games g
        JOIN Teams ht ON g.home_team_id = ht.team_id
        JOIN Teams at ON g.away_team_id = at.team_id
        ORDER BY g.game_date DESC
    ''').fetchall()
    
    print("Fetched games:", [dict(g) for g in games])  # Debug output
    
    conn.close()
    return render_template('games.html', games=games)
@app.route('/game/<int:game_id>')
def game_detail(game_id):
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    game = conn.execute('''
        SELECT g.*, ht.name as home_team, at.name as away_team
        FROM Games g
        JOIN Teams ht ON g.home_team_id = ht.team_id
        JOIN Teams at ON g.away_team_id = at.team_id
        WHERE g.game_id = ?
    ''', (game_id,)).fetchone()
    
    stats = conn.execute('''
        SELECT p.first_name, p.last_name, s.*
        FROM Statistics s
        JOIN Players p ON s.player_id = p.player_id
        WHERE s.game_id = ?
    ''', (game_id,)).fetchall()
    
    conn.close()
    return render_template('game_detail.html', game=game, stats=stats)

# CRUD Operations for Teams
@app.route('/teams/new', methods=['GET', 'POST'])
def new_team():
    if request.method == 'POST':
        conn = sqlite3.connect('hockey.db')
        conn.execute('''
            INSERT INTO Teams (name, city, league, founded_year, arena)
            VALUES (?, ?, ?, ?, ?)
        ''', [
            request.form['name'],
            request.form['city'],
            request.form['league'],
            request.form['founded_year'],
            request.form['arena']
        ])
        conn.commit()
        conn.close()
        return redirect(url_for('teams'))
    
    return render_template('new_team.html')

@app.route('/team/<int:team_id>/edit', methods=['GET', 'POST'])
def edit_team(team_id):
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE Teams SET
            name = ?, city = ?, league = ?, founded_year = ?, arena = ?
            WHERE team_id = ?
        ''', [
            request.form['name'],
            request.form['city'],
            request.form['league'],
            request.form['founded_year'],
            request.form['arena'],
            team_id
        ])
        conn.commit()
        conn.close()
        return redirect(url_for('teams'))
    
    team = conn.execute('SELECT * FROM Teams WHERE team_id = ?', [team_id]).fetchone()
    conn.close()
    return render_template('edit_team.html', team=team)

@app.route('/team/<int:team_id>/delete', methods=['POST'])
def delete_team(team_id):
    conn = sqlite3.connect('hockey.db')
    conn.execute('DELETE FROM Teams WHERE team_id = ?', [team_id])
    conn.commit()
    conn.close()
    return redirect(url_for('teams'))

@app.route('/teams')
def teams():
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    teams = conn.execute('SELECT * FROM Teams ORDER BY name').fetchall()
    
    conn.close()
    return render_template('teams.html', teams=teams)

if __name__ == '__main__':
    app.run(debug=True)