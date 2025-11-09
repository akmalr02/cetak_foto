import os
import shutil
import face_recognition
import easyocr
import numpy as np
from collections import defaultdict
from gtts import gTTS
from playsound import playsound
from database.photo_service import insert_photo
import cv2

# === Folder dasar ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
WAJAH_DIR = os.path.join(BASE_DIR, "output", "wajah")
ANGKA_DIR = os.path.join(BASE_DIR, "output", "angka")
MODEL_WAJAH_DIR = os.path.join(BASE_DIR, "models", "wajah")
CACHE_FILE = os.path.join(MODEL_WAJAH_DIR, "face_cache.npy")

# === Pastikan semua folder ada ===
os.makedirs(WAJAH_DIR, exist_ok=True)
os.makedirs(ANGKA_DIR, exist_ok=True)
os.makedirs(MODEL_WAJAH_DIR, exist_ok=True)

# === Inisialisasi EasyOCR (CPU friendly) ===
reader = easyocr.Reader(["id"], gpu=False)

# === Cache model wajah ===
known_faces = []
known_names = []
unknown_stats = defaultdict(int)

# ===================================================
# 🔹 Muat cache wajah jika ada
# ===================================================
if os.path.exists(CACHE_FILE):
    print("📦 Memuat cache wajah dari file...")
    data = np.load(CACHE_FILE, allow_pickle=True).item()
    known_faces = data["encodings"]
    known_names = data["names"]
else:
    print("📷 Memuat model wajah dari folder...")
    for filename in os.listdir(MODEL_WAJAH_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(MODEL_WAJAH_DIR, filename)
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                known_faces.append(encoding[0])
                known_names.append(os.path.splitext(filename)[0])
    np.save(CACHE_FILE, {"encodings": known_faces, "names": known_names})
print(f"✅ {len(known_faces)} model wajah dimuat.")

# ===================================================
# 🔊 Fungsi suara notifikasi
# ===================================================
def play_voice(message):
    try:
        tts = gTTS(text=message, lang="id")
        tts.save("notif.mp3")
        playsound("notif.mp3")
        os.remove("notif.mp3")
    except Exception:
        pass

# ===================================================
# ⚙️ Proses utama
# ===================================================
def process_photo(filepath):
    import time
    import cv2

    start_time = time.time()
    filename = os.path.basename(filepath)
    print(f"\n⚙️ Memproses: {filename}")

    # 🧩 Cegah error jika file rusak atau belum selesai diupload
    if not os.path.exists(filepath) or os.path.getsize(filepath) < 50_000:
        print(f"⚠️ File {filename} terlalu kecil atau belum siap.")
        return

    try:
        # === 1️⃣ Load & resize gambar ===
        image = face_recognition.load_image_file(filepath)
        height, width = image.shape[:2]

        # Skip foto terlalu besar (>10MB)
        if os.path.getsize(filepath) > 10_000_000:
            print(f"⚠️ {filename} terlalu besar (>10MB), dilewati.")
            insert_photo(filename, "skipped", filepath, status="failed")
            os.remove(filepath)
            return

        # Resize jika lebar > 800px
        if width > 800:
            ratio = 800 / width
            new_size = (800, int(height * ratio))
            image = cv2.resize(image, new_size)
            print(f"🪶 Resize gambar dari {width}x{height} → {new_size[0]}x{new_size[1]}")

        # === 2️⃣ Deteksi wajah ===
        face_locations = face_recognition.face_locations(image, model="hog")
        encodings = face_recognition.face_encodings(image, face_locations)
        wajah_terdeteksi = len(encodings) > 0

        angka_terdeteksi = False
        tujuan_wajah = tujuan_angka = None
        jenis_deteksi = "none"

        # ========== PROSES WAJAH ==========
        if wajah_terdeteksi:
            for enc in encodings:
                matches = face_recognition.compare_faces(known_faces, enc, tolerance=0.55)
                face_distances = face_recognition.face_distance(known_faces, enc)

                matched_name = None
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        matched_name = known_names[best_match_index]

                # === Wajah dikenal ===
                if matched_name:
                    folder_name = matched_name
                    print(f"🧠 Wajah dikenali: {matched_name}")
                else:
                    # === Wajah baru ===
                    unknown_dirs = [d for d in os.listdir(WAJAH_DIR) if d.startswith("unknown")]
                    next_num = len(unknown_dirs) + 1
                    folder_name = f"unknown{next_num}"
                    person_dir = os.path.join(WAJAH_DIR, folder_name)
                    os.makedirs(person_dir, exist_ok=True)

                    model_path = os.path.join(MODEL_WAJAH_DIR, f"{folder_name}.jpg")
                    shutil.copy(filepath, model_path)

                    # Tambahkan ke cache
                    new_img = face_recognition.load_image_file(model_path)
                    new_enc = face_recognition.face_encodings(new_img)
                    if new_enc:
                        known_faces.append(new_enc[0])
                        known_names.append(folder_name)
                        np.save(CACHE_FILE, {"encodings": known_faces, "names": known_names})

                    unknown_stats[folder_name] += 1
                    print(f"📊 Kemunculan {folder_name}: {unknown_stats[folder_name]} kali")

                    # === Promosi jadi model tetap ===
                    if unknown_stats[folder_name] >= 3:
                        new_name = f"person{len([n for n in known_names if n.startswith('person')]) + 1}"
                        new_model_path = os.path.join(MODEL_WAJAH_DIR, f"{new_name}.jpg")
                        os.rename(model_path, new_model_path)

                        idx = known_names.index(folder_name)
                        known_names[idx] = new_name
                        np.save(CACHE_FILE, {"encodings": known_faces, "names": known_names})

                        old_folder = os.path.join(WAJAH_DIR, folder_name)
                        new_folder = os.path.join(WAJAH_DIR, new_name)
                        os.rename(old_folder, new_folder)
                        del unknown_stats[folder_name]
                        play_voice("Wajah baru berhasil disimpan permanen")
                        print(f"🎓 {folder_name} dipromosikan jadi {new_name}")

                # Simpan hasil wajah
                person_dir = os.path.join(WAJAH_DIR, folder_name)
                os.makedirs(person_dir, exist_ok=True)
                tujuan_wajah = os.path.join(person_dir, filename)
                shutil.copy(filepath, tujuan_wajah)

            jenis_deteksi = "wajah"
            play_voice("Wajah terdeteksi")

        # ========== PROSES ANGKA ==========
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        result = reader.readtext(gray, detail=0, paragraph=False)
        for text in result:
            digits = "".join([c for c in text if c.isdigit()])
            if digits:
                angka_terdeteksi = True
                angka_dir = os.path.join(ANGKA_DIR, digits)
                os.makedirs(angka_dir, exist_ok=True)
                tujuan_angka = os.path.join(angka_dir, filename)
                shutil.copy(filepath, tujuan_angka)
                print(f"🔢 Angka {digits} terdeteksi")
                break

        # ========== SIMPAN HASIL ==========
        if wajah_terdeteksi and angka_terdeteksi:
            jenis_deteksi = "campuran"
            play_voice("Wajah dan angka terdeteksi")

        if not (wajah_terdeteksi or angka_terdeteksi):
            print("❌ Tidak ada wajah atau angka")
            insert_photo(filename, "none", filepath, status="failed")
        else:
            insert_photo(filename, jenis_deteksi, tujuan_wajah or tujuan_angka)
            print(f"✅ Foto {filename} selesai diproses & dihapus dari uploads.")
            os.remove(filepath)

    except Exception as e:
        print(f"❌ Error memproses {filename}: {e}")
        insert_photo(filename, "error", filepath, status="failed")

    finally:
        durasi = round(time.time() - start_time, 2)
        print(f"⏱️ Waktu proses total: {durasi} detik\n")
