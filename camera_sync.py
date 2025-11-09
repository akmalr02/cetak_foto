import os
import time
import queue
import threading
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor

# Import langsung fungsi dari main.py
from main import process_photo

UPLOADS_DIR = "uploads"
MAX_WORKERS = 2  # jumlah foto yang bisa diproses bersamaan
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Queue untuk antrian file baru
photo_queue = queue.Queue()
stop_event = threading.Event()


# =====================================
# HANDLER FILE BARU
# =====================================
class UploadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        if filepath.lower().endswith((".jpg", ".jpeg", ".png")):
            print(f"[🆕] File baru terdeteksi: {os.path.basename(filepath)}")
            photo_queue.put(filepath)


# =====================================
# THREAD PEMROSESAN ANTRIAN
# =====================================
def worker_thread():
    """Worker utama untuk memproses foto dari queue"""
    while not stop_event.is_set():
        try:
            filepath = photo_queue.get(timeout=1)
            if os.path.exists(filepath):
                print(f"[⚙️] Memulai proses untuk {os.path.basename(filepath)}")
                process_photo(filepath)
                print(f"[✅] Selesai memproses {os.path.basename(filepath)}")
            else:
                print(f"[⚠️] File hilang: {filepath}")
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[❌] Error di worker: {e}")
        finally:
            photo_queue.task_done()

# =====================================
# PEMROSESAN FOTO LAMA (JIKA ADA)
# =====================================
def process_existing_photos():
    print("\n🕵️ Mengecek foto lama di folder uploads...")
    for file in os.listdir(UPLOADS_DIR):
        filepath = os.path.join(UPLOADS_DIR, file)
        if os.path.isfile(filepath) and file.lower().endswith((".jpg", ".jpeg", ".png")):
            photo_queue.put(filepath)
    print("✅ Pemeriksaan foto lama selesai.\n")


# =====================================
# MODE CAPTURE MANUAL
# =====================================
def capture_from_camera():
    """Ambil satu foto dari kamera (manual)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jpg"
    save_path = os.path.join(UPLOADS_DIR, filename)
    print(f"[📸] Mengambil foto dari kamera...")
    try:
        subprocess.run(
            ["gphoto2", "--capture-image-and-download", "--filename", save_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[✔] Foto tersimpan di {save_path}")
    except subprocess.CalledProcessError:
        print("⚠️ Kamera tidak terdeteksi atau belum siap.")


# =====================================
# MODE TETHERED OTOMATIS
# =====================================
def tethered_listener():
    """Mode tethered: kamera langsung upload ke folder uploads"""
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
        print(f"❌ Error tethered: {e}")


# =====================================
# SISTEM WATCHER (MONITOR UPLOADS)
# =====================================
def start_watcher():
    """Pantau folder uploads"""
    event_handler = UploadHandler()
    observer = Observer()
    observer.schedule(event_handler, UPLOADS_DIR, recursive=False)
    observer.start()
    print("[👁️] Sistem siap memantau folder uploads...")

    return observer


# =====================================
# FUNGSI UTAMA
# =====================================
def main():
    print("🚀 Menjalankan sistem pemrosesan real-time...\n")

    observer = start_watcher()
    process_existing_photos()

    # Jalankan pool worker
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    for _ in range(MAX_WORKERS):
        executor.submit(worker_thread)

    # Jalankan tethered mode di thread terpisah
    tether_thread = threading.Thread(target=tethered_listener, daemon=True)
    tether_thread.start()

    try:
        while True:
                        # CLI sederhana untuk ambil foto manual atau keluar
            cmd = input("\nKetik 'c' untuk capture manual, 'q' untuk keluar: ").lower().strip()
            if cmd == "c":
                capture_from_camera()
            elif cmd == "q":
                print("🛑 Perintah keluar diterima. Menunggu antrian selesai...")
                break
            else:
                print("❓ Perintah tidak dikenal. Gunakan 'c' atau 'q'.")

    except KeyboardInterrupt:
        print("\n🛑 Diterima Ctrl-C. Menghentikan...")

    finally:
        # Shutdown sequence
        stop_event.set()               # beri tanda pada worker untuk berhenti
        print("⏳ Menunggu antrian selesai...")
        try:
            photo_queue.join()         # tunggu sampai semua tugas dibereskan
        except Exception:
            pass

        print("🔒 Menutup executor dan watcher...")
        executor.shutdown(wait=True)
        observer.stop()
        observer.join()
        print("✅ Semua proses berhenti. Sampai jumpa!")

if __name__ == "__main__":
    # buat folder uploads jika belum ada
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    main()
