import subprocess
import time
import os
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

processes = []

try:
    print("🚀 Menjalankan sistem pemrosesan real-time...\n")

    main_process = subprocess.Popen(
        ["python3", os.path.join(BASE_DIR, "main.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(main_process)
    print("🧠 Sistem deteksi wajah & angka aktif (background)")

    time.sleep(2)

    print("📸 Mengaktifkan kamera dan mode tethered...")
    subprocess.run(["python3", os.path.join(BASE_DIR, "camera_sync.py")])

except KeyboardInterrupt:
    print("\n🛑 Sistem dihentikan oleh pengguna...")

finally:
    print("🧹 Menutup semua proses...")
    for p in processes:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            pass
    print("✅ Semua proses berhenti dengan aman.")
