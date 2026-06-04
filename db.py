import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'projects.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id INTEGER NOT NULL,
            title TEXT DEFAULT 'UNTITLED NOTE',
            content TEXT NOT NULL,
            sentiment TEXT DEFAULT 'neutral',
            price_at_creation REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS spreadsheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id INTEGER NOT NULL,
            row_idx INTEGER NOT NULL,
            col_idx INTEGER NOT NULL,
            value TEXT,
            FOREIGN KEY (folder_id) REFERENCES folders (id),
            UNIQUE(folder_id, row_idx, col_idx)
        )
    ''')
    conn.commit()
    conn.close()

# Spreadsheet Methods
def get_spreadsheet_data(folder_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT row_idx, col_idx, value FROM spreadsheets WHERE folder_id = ?', (folder_id,))
    cells = [dict(row) for row in c.fetchall()]
    conn.close()
    return cells

def update_spreadsheet_cell(folder_id, row_idx, col_idx, value):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO spreadsheets (folder_id, row_idx, col_idx, value)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(folder_id, row_idx, col_idx) DO UPDATE SET value=excluded.value
    ''', (folder_id, row_idx, col_idx, value))
    conn.commit()
    conn.close()
    return True

# Folder Methods
def create_folder(name):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO folders (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        return True, "Folder created."
    except sqlite3.IntegrityError:
        return False, "Folder already exists."

def get_folders():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM folders ORDER BY created_at DESC')
    folders = [dict(row) for row in c.fetchall()]
    conn.close()
    return folders

def get_folder_by_name(name):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM folders WHERE name = ?', (name,))
    folder = c.fetchone()
    conn.close()
    return dict(folder) if folder else None

def delete_folder(name):
    folder = get_folder_by_name(name)
    if not folder:
        return False, "Folder not found."
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM notes WHERE folder_id = ?', (folder['id'],))
    c.execute('DELETE FROM folders WHERE id = ?', (folder['id'],))
    conn.commit()
    conn.close()
    return True, f"Deleted folder {name} and its notes."

# Note Methods
def create_note(folder_id, title, content, sentiment='neutral', price=None):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO notes (folder_id, title, content, sentiment, price_at_creation) 
        VALUES (?, ?, ?, ?, ?)
    ''', (folder_id, title, content, sentiment, price))
    conn.commit()
    conn.close()
    return True

def get_notes_by_folder(folder_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM notes WHERE folder_id = ? ORDER BY created_at DESC', (folder_id,))
    notes = [dict(row) for row in c.fetchall()]
    conn.close()
    return notes

def delete_note(note_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
