import sqlite3
from common import *
from flask import flash


def init_db():
    conn = sqlite3.connect('essence.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS essence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banner TEXT,
            address TEXT,
            prix_regulier TEXT,
            prix_super TEXT,
            code_postal TEXT,
            gmap TEXT,
            selected BOOLEAN DEFAULT 0
        )
    ''')
    # Add selected column if it doesn't exist
    try:
        c.execute('ALTER TABLE essence ADD COLUMN selected BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

def get_all_station():
    conn = sqlite3.connect('essence.db')
    c = conn.cursor()
    c.execute('SELECT id, banner, address, prix_regulier, prix_super, code_postal, gmap, selected FROM essence')
    station = c.fetchall()
    conn.close()
    return station

def create_gmap_link(addresse):
    gmap_base = "https://www.google.com/maps/dir//"
    address = addresse.replace(' ',"+")
    gmap_link = gmap_base + address
    return gmap_link

def add_website(data):
    conn = sqlite3.connect('essence.db')
    c = conn.cursor()
    c.execute('SELECT id FROM essence WHERE address = ?', (data['address'],))
    existing = c.fetchone()
    if existing:
        flash('Station exist')
        return
    c.execute('''
        INSERT INTO essence (banner, address, prix_regulier, prix_super, code_postal, gmap, selected)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data["banner"], data["address"], data["prix_regulier"], data["prix_super"], data["code_postal"], data["gmap"], data["selected"]))
    conn.commit()
    conn.close()

def get_station_by_address(address):
    conn = sqlite3.connect('essence.db')
    c = conn.cursor()
    c.execute('SELECT id FROM essence WHERE address = ?', (address,))
    result = c.fetchone()
    conn.close()
    return result

def toggle_selected(website_id):
    conn = sqlite3.connect('essence.db')
    c = conn.cursor()
    c.execute('SELECT selected FROM essence WHERE id = ?', (website_id,))
    current = c.fetchone()
    if current:
        new_value = 1 if current[0] == 0 else 0
        c.execute('UPDATE essence SET selected = ? WHERE id = ?', (new_value, website_id))
        conn.commit()
    conn.close()

def delete_website(website_id):
    conn = sqlite3.connect('essence.db')
    c = conn.cursor()
    c.execute('DELETE FROM essence WHERE id = ?', (website_id,))
    conn.commit()
    conn.close()

def update_website_data(data, website_id):
    conn = sqlite3.connect('essence.db')
    c = conn.cursor()
    c.execute(f'''
        UPDATE essence
        SET banner = ?, address = ?, prix_regulier = ?, prix_super = ?, code_postal = ?, gmap = ?
        WHERE id = ?
    ''', (data["banner"], data["address"], data["prix_regulier"], data["prix_super"], data["code_postal"], data["gmap"], website_id))
    conn.commit()
    conn.close()
