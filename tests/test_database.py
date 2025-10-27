import sqlite3
import pytest
from database.photo_service import insert_photo, get_all_photos, get_photos_by_type, DB_PATH
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def clean_db():
    """Bersihkan database sebelum test"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            type TEXT,
            path TEXT,
            detected_at TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_insert_and_fetch(clean_db):
    insert_photo("foto1.jpg", "wajah", "output/wajah")
    data = get_all_photos()
    assert len(data) == 1
    assert data[0][1] == "foto1.jpg"

def test_get_photos_by_type(clean_db):
    insert_photo("foto2.jpg", "angka", "output/angka")
    data = get_photos_by_type("angka")
    assert len(data) == 1
    assert data[0][2] == "angka"
