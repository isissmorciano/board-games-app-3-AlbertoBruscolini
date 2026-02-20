import sqlite3
import click
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
app.config['DATABASE'] = str(Path(__file__).with_name('giochi.db'))


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.executescript(f.read())
    db.commit()


def ensure_db_initialized():
    db = get_db()
    table = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='giochi'"
    ).fetchone()
    if table is None:
        init_db()


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.cli.command('init-db')
def init_db_command():
    init_db()
    click.echo('Database inizializzato.')


@app.route('/')
def index():
    ensure_db_initialized()
    db = get_db()
    giochi = db.execute('SELECT * FROM giochi ORDER BY nome').fetchall()
    return render_template('giochi.html', giochi=giochi)


@app.route('/giochi/nuovo', methods=['GET', 'POST'])
def nuovo_gioco():
    if request.method == 'POST':
        db = get_db()
        db.execute(
            'INSERT INTO giochi (nome, numero_giocatori_massimo, durata_media, categoria) VALUES (?, ?, ?, ?)',
            (request.form['nome'], request.form['numero_giocatori_massimo'],
             request.form['durata_media'], request.form['categoria'])
        )
        db.commit()
        return redirect(url_for('index'))
    return render_template('nuovo_gioco.html')


@app.route('/giochi/<int:gioco_id>/partite')
def lista_partite(gioco_id):
    db = get_db()
    gioco = db.execute('SELECT * FROM giochi WHERE id = ?', (gioco_id,)).fetchone()
    partite = db.execute('SELECT * FROM partite WHERE gioco_id = ? ORDER BY data DESC', (gioco_id,)).fetchall()
    return render_template('partite.html', gioco=gioco, partite=partite)


@app.route('/giochi/<int:gioco_id>/partite/nuova', methods=['GET', 'POST'])
def nuova_partita(gioco_id):
    db = get_db()
    gioco = db.execute('SELECT * FROM giochi WHERE id = ?', (gioco_id,)).fetchone()
    if request.method == 'POST':
        db.execute(
            'INSERT INTO partite (gioco_id, data, vincitore, punteggio_vincitore) VALUES (?, ?, ?, ?)',
            (gioco_id, request.form['data'], request.form['vincitore'], request.form['punteggio_vincitore'])
        )
        db.commit()
        return redirect(url_for('lista_partite', gioco_id=gioco_id))
    return render_template('nuova_partita.html', gioco=gioco)


if __name__ == '__main__':
    app.run(debug=True)
