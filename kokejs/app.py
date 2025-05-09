import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('hockey.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS Teams (
                 team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 city TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Players (
                 player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 first_name TEXT NOT NULL,
                 last_name TEXT NOT NULL,
                 team_id INTEGER,
                 FOREIGN KEY (team_id) REFERENCES Teams(team_id))''')
    
    # Insert Latvian hockey sample data
    c.execute("INSERT OR IGNORE INTO Teams (name, city) VALUES ('Dinamo Rīga', 'Riga')")
    c.execute("INSERT OR IGNORE INTO Teams (name, city) VALUES ('HK Liepāja', 'Liepāja')")
    c.execute("INSERT OR IGNORE INTO Players (first_name, last_name, team_id) VALUES ('Elvis', 'Merzļikins', 1)")
    c.execute("INSERT OR IGNORE INTO Players (first_name, last_name, team_id) VALUES ('Rodrigo', 'Ābols', 1)")
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

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

@app.route('/teams')
def teams():
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    teams = conn.execute('SELECT * FROM Teams').fetchall()
    conn.close()
    return render_template('teams.html', teams=teams)

# Add these new routes after your existing ones
@app.route('/player/<int:player_id>')
def player_detail(player_id):
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    player = conn.execute('''
        SELECT p.*, t.name as team_name 
        FROM Players p LEFT JOIN Teams t ON p.team_id = t.team_id 
        WHERE p.player_id = ?
    ''', (player_id,)).fetchone()
    
    # Modified query to handle goalie stats
    stats = conn.execute('''
        SELECT s.*, g.game_date, g.game_type,
               ht.name as home_team, at.name as away_team, g.score
        FROM Statistics s
        JOIN Games g ON s.game_id = g.game_id
        JOIN Teams ht ON g.home_team_id = ht.team_id
        JOIN Teams at ON g.away_team_id = at.team_id
        WHERE s.player_id = ?
        ORDER BY g.game_date DESC
    ''', (player_id,)).fetchall()
    
    # Calculate career totals
    career_totals = conn.execute('''
        SELECT SUM(goals) as total_goals,
               SUM(assists) as total_assists,
               SUM(penalty_minutes) as total_penalty_minutes,
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
@app.route('/game/<int:game_id>')
def game_detail(game_id):
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    # Get game info
    game = conn.execute('''
        SELECT g.*, ht.name as home_team, at.name as away_team
        FROM Games g
        JOIN Teams ht ON g.home_team_id = ht.team_id
        JOIN Teams at ON g.away_team_id = at.team_id
        WHERE g.game_id = ?
    ''', (game_id,)).fetchone()
    
    # Get game statistics
    stats = conn.execute('''
        SELECT p.first_name, p.last_name, s.*
        FROM Statistics s
        JOIN Players p ON s.player_id = p.player_id
        WHERE s.game_id = ?
        ORDER BY s.goals DESC, s.assists DESC
    ''', (game_id,)).fetchall()
    
    conn.close()
    
    return render_template('game_detail.html', game=game, stats=stats)
# Add this route with the others
@app.route('/games')
def games():
    conn = sqlite3.connect('hockey.db')
    conn.row_factory = sqlite3.Row
    
    games = conn.execute('''
        SELECT g.*, ht.name as home_team, at.name as away_team
        FROM Games g
        JOIN Teams ht ON g.home_team_id = ht.team_id
        JOIN Teams at ON g.away_team_id = at.team_id
        ORDER BY g.game_date DESC
    ''').fetchall()
    
    conn.close()
    return render_template('games.html', games=games)
if __name__ == '__main__':
    app.run(debug=True)