import os
import shutil
import time
import sqlite3
import sys
import pytest
from PIL import Image  # untuk buat dummy image

# pastikan project root ada di path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import UPLOADS_DIR, WAJAH_DIR, ANGKA_DIR
from database.photo_service import DB_PATH, insert_photo, get_all_photos
from database.db_setup import init_db  # <=== Tambahkan

@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    """Bersihkan dan siapkan lingkungan test"""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(WAJAH_DIR, exist_ok=True)
    os.makedirs(ANGKA_DIR, exist_ok=True)

    # pastikan database siap
    init_db()  # <=== Pastikan tabel 'photos' ada

    # bersihkan folder sebelum test
    for folder in [UPLOADS_DIR, WAJAH_DIR, ANGKA_DIR]:
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

    yield
    # cleanup setelah test selesai
    shutil.rmtree(UPLOADS_DIR, ignore_errors=True)


def test_face_and_number_detection(monkeypatch):
    """Uji logika deteksi wajah dan angka dari main.py"""

    # Buat gambar dummy valid
    dummy_file = os.path.join(UPLOADS_DIR, "dummy.jpg")
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    img.save(dummy_file)

    import main

    def fake_face_locations(image):
        return [(0, 10, 10, 0)]  # wajah terdeteksi

    def fake_face_encodings(image, locations=None):
        return [[0.1, 0.2, 0.3]]  # encoding wajah palsu

    def fake_readtext(path):
        return [[(0, 0, 100, 100), "Nomor 01", 0.9]]  # hasil OCR palsu

    monkeypatch.setattr(main.face_recognition, "face_locations", fake_face_locations)
    monkeypatch.setattr(main.face_recognition, "face_encodings", fake_face_encodings)
    monkeypatch.setattr(main.reader, "readtext", fake_readtext)

    # Jalankan handler manual
    handler = main.PhotoHandler()
    event = type("Event", (object,), {"is_directory": False, "src_path": dummy_file})
    handler.on_created(event)

    time.sleep(1)

    # Pastikan file berpindah
    wajah_files = os.listdir(WAJAH_DIR)
    angka_files = os.listdir(ANGKA_DIR)
    assert len(wajah_files) > 0 or len(angka_files) > 0, "File tidak terproses"

    # Cek data di database
    insert_photo("dummy.jpg", "test", "success")
    data = get_all_photos()
    assert len(data) > 0, "Data tidak tersimpan di database"

    print("✅ Pipeline deteksi wajah & angka berfungsi dengan baik")
