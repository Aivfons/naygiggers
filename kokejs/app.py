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

if __name__ == '__main__':
    app.run(debug=True)