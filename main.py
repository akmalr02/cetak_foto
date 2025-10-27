import os
import time
import shutil
import face_recognition
import easyocr
import numpy as np
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from gtts import gTTS
from playsound import playsound
from database.photo_service import insert_photo

# === Konfigurasi folder ===
UPLOADS_DIR = "uploads"
WAJAH_DIR = "output/wajah"
ANGKA_DIR = "output/angka"
MODEL_WAJAH_DIR = "models/wajah"

os.makedirs(WAJAH_DIR, exist_ok=True)
os.makedirs(ANGKA_DIR, exist_ok=True)
os.makedirs(MODEL_WAJAH_DIR, exist_ok=True)

reader = easyocr.Reader(["id"])

# === Fungsi Suara ===
def play_voice(message: str):
    filename = "notif.mp3"
    try:
        tts = gTTS(text=message, lang='id')
        tts.save(filename)
        playsound(filename)
    except Exception as e:
        print(f"Gagal memutar suara: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# === Load Model Wajah Dikenal ===
def load_known_faces():
    known_faces = []
    known_names = []

    for filename in os.listdir(MODEL_WAJAH_DIR):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            image_path = os.path.join(MODEL_WAJAH_DIR, filename)
            image = face_recognition.load_image_file(image_path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                known_faces.append(encoding[0])
                known_names.append(os.path.splitext(filename)[0])
                print(f"Model wajah '{filename}' dimuat")

    return known_faces, known_names


known_faces, known_names = load_known_faces()


# === Handler ===
class PhotoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)
        time.sleep(1)

        print(f"File baru terdeteksi: {filename}")

        try:
            wajah_terdeteksi = False
            angka_terdeteksi = False
            tujuan_wajah = None
            tujuan_angka = None
            jenis_deteksi = "none"

            # === Deteksi dan identifikasi wajah ===
            image = face_recognition.load_image_file(filepath)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            if face_encodings:
                wajah_terdeteksi = True
                matched_name = None
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.45)
                    face_distances = face_recognition.face_distance(known_faces, face_encoding)

                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            matched_name = known_names[best_match_index]
                            break

                if matched_name:
                    person_dir = os.path.join(WAJAH_DIR, matched_name)
                else:
                    person_dir = os.path.join(WAJAH_DIR, "unknown")

                os.makedirs(person_dir, exist_ok=True)
                tujuan_wajah = os.path.join(person_dir, filename)
                jenis_deteksi = "wajah"
                print(f"Wajah {'dikenali ' + matched_name if matched_name else 'baru'} → {person_dir}")

            # === Deteksi angka dengan OCR ===
            result = reader.readtext(filepath)
            for res in result:
                text = res[1]
                digits = ''.join([c for c in text if c.isdigit()])
                if digits:
                    angka_terdeteksi = True
                    angka_folder = os.path.join(ANGKA_DIR, digits)
                    os.makedirs(angka_folder, exist_ok=True)
                    tujuan_angka = os.path.join(angka_folder, filename)
                    print(f"🔢 Angka {digits} terdeteksi → {angka_folder}")
                    break

            # === Simpan hasil ===
            if wajah_terdeteksi and angka_terdeteksi:
                shutil.copy(filepath, tujuan_wajah)
                shutil.copy(filepath, tujuan_angka)
                os.remove(filepath)
                jenis_deteksi = "campuran"
                play_voice("Wajah dan angka terdeteksi")
                insert_photo(filename, jenis_deteksi, f"{tujuan_wajah} & {tujuan_angka}")
                print(f"📸 Disalin ke: {tujuan_wajah} dan {tujuan_angka}")

            elif wajah_terdeteksi:
                shutil.move(filepath, tujuan_wajah)
                play_voice("Wajah terdeteksi")
                insert_photo(filename, jenis_deteksi, tujuan_wajah)

            elif angka_terdeteksi:
                shutil.move(filepath, tujuan_angka)
                play_voice("Angka terdeteksi")
                insert_photo(filename, jenis_deteksi, tujuan_angka)

            else:
                print("Tidak ada wajah atau angka terdeteksi")
                insert_photo(filename, "none", UPLOADS_DIR, status="failed")

        except Exception as e:
            print(f"❌ Error memproses {filename}: {e}")
            insert_photo(filename, "error", UPLOADS_DIR, status="failed")


# === Fungsi utama ===
def main():
    print("🚀 Sistem pendeteksi wajah & angka dimulai...")
    print(f"📂 Memantau folder: {UPLOADS_DIR}")
    event_handler = PhotoHandler()
    observer = Observer()
    observer.schedule(event_handler, UPLOADS_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Sistem dihentikan.")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
