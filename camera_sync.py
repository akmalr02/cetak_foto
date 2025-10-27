import os
import subprocess
import threading
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

UPLOADS_DIR = "uploads"
LOCK_FILE = "processing.lock"

os.makedirs(os.path.join(UPLOADS_DIR, "wajah"), exist_ok=True)
os.makedirs(os.path.join(UPLOADS_DIR, "angka"), exist_ok=True)

# ==============================
# HANDLER UNTUK FILE BARU
# ==============================
class UploadHandler(FileSystemEventHandler):
    """Menangani event saat foto baru muncul di folder uploads"""
    def on_created(self, event):
        if event.is_directory:
            return

        if os.path.exists(LOCK_FILE):
            print("⚙️ Sistem masih memproses file sebelumnya...")
            return

        filepath = event.src_path
        print(f"[📁] File baru terdeteksi: {filepath}")

        try:
            open(LOCK_FILE, "w").close()
            subprocess.run(["python3", "main.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error saat menjalankan main.py: {e}")
        finally:
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)

# ==============================
# FUNGSI UNTUK PENGAMBILAN FOTO
# ==============================
def capture_from_camera():
    """Ambil satu foto dari kamera DSLR/mirrorless"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jpg"
    save_path = os.path.join(UPLOADS_DIR, filename)

    print(f"[📸] Mengambil foto dari kamera (manual via laptop)...")
    try:
        subprocess.run(
            ["gphoto2", "--capture-image-and-download", "--filename", save_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[✔] Foto tersimpan di {save_path}")
    except subprocess.CalledProcessError:
        print("⚠️ Kamera belum siap atau tidak terdeteksi. Coba lagi nanti.")

# ==============================
# MODE TETHERED (DARI KAMERA LANGSUNG)
# ==============================
def tethered_listener():
    """Mode tethered: otomatis simpan ke uploads/ saat kamera memotret"""
    print("[🔗] Mode tethered aktif. Tekan shutter di kamera untuk memotret...")
    try:
        subprocess.run([
            "gphoto2",
            "--capture-tethered",
            "--filename", os.path.join(UPLOADS_DIR, "%Y%m%d_%H%M%S.jpg")
        ])
    except KeyboardInterrupt:
        print("\n🛑 Mode tethered dihentikan.")
    except Exception as e:
        print(f"❌ Error tethered mode: {e}")

# ==============================
# SISTEM WATCHER (MONITOR FOLDER)
# ==============================
def start_watcher():
    """Pantau folder uploads & jalankan deteksi otomatis"""
    event_handler = UploadHandler()
    observer = Observer()
    observer.schedule(event_handler, UPLOADS_DIR, recursive=False)
    observer.start()
    print("[👁️] Sistem siap memantau folder uploads...")

    tether_thread = threading.Thread(target=tethered_listener, daemon=True)
    tether_thread.start()

    try:
        while True:
            command = input("\nKetik 'c' untuk capture manual, 'q' untuk keluar: ").lower().strip()
            if command == "c":
                capture_from_camera()
            elif command == "q":
                print("🛑 Sistem dihentikan oleh pengguna.")
                break
            else:
                print("❓ Perintah tidak dikenal. Gunakan 'c' atau 'q'.")
    finally:
        observer.stop()
        observer.join()

# ==============================
# MAIN ENTRY
# ==============================
if __name__ == "__main__":
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    start_watcher()
