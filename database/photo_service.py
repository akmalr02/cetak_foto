import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def insert_photo(filename, photo_type, path, status="success"):
    """Simpan data foto baru ke database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO photos (filename, type, path, detected_at, status)
        VALUES (?, ?, ?, ?, ?)
    """, (filename, photo_type, path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status))

    conn.commit()
    conn.close()

def get_all_photos():
    """Ambil semua data foto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM photos ORDER BY detected_at DESC")
    data = cursor.fetchall()
    conn.close()
    return data

def get_photos_by_type(photo_type):
    """Ambil foto berdasarkan jenis"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM photos WHERE type = ? ORDER BY detected_at DESC", (photo_type,))
    data = cursor.fetchall()
    conn.close()
    return data
