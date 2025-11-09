import subprocess
import time
import os
import signal
import platform
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
processes = []


def check_camera_connected():
    """Cek apakah kamera terdeteksi di sistem"""
    try:
        result = subprocess.run(
            ["gphoto2", "--auto-detect"],
            capture_output=True,
            text=True,
            check=False,
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) > 2:
            print("📷 Kamera terdeteksi:")
            for line in lines[2:]:
                print("   →", line)
            return True
        else:
            print("⚠️ Tidak ada kamera yang terdeteksi.")
            return False
    except FileNotFoundError:
        print("❌ gphoto2 belum terinstal. Jalankan:")
        print("   sudo apt install gphoto2 -y")
        return False


def run_background(name, command):
    """Jalankan proses background"""
    try:
        print(f"▶️ Menjalankan {name} ...")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != "nt" else None,
        )
        processes.append(process)
        return process
    except Exception as e:
        print(f"❌ Gagal menjalankan {name}: {e}")
        return None


def stop_all_processes():
    """Matikan semua proses aktif"""
    print("\n🧹 Menutup semua proses...")
    for p in processes:
        try:
            if p.poll() is None:
                if os.name == "nt":
                    p.terminate()
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            pass
    print("✅ Semua proses berhenti dengan aman.")


def detect_environment():
    """Deteksi platform & GPU"""
    print("🔍 Mengecek environment...")
    device = "CPU"
    try:
        import torch
        if torch.cuda.is_available():
            device = "GPU (CUDA)"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "GPU (Apple MPS)"
    except Exception:
        pass

    print(f"🧠 Mode perangkat: {device}")
    print(f"💻 Sistem: {platform.system()} {platform.release()}")
    print("-" * 50)
    return device


def main():
    print("🚀 Menjalankan sistem pemrosesan real-time...\n")
    detect_environment()

    # Jalankan sistem utama
    main_path = os.path.join(BASE_DIR, "main.py")
    if not os.path.exists(main_path):
        print("❌ File main.py tidak ditemukan!")
        return

    main_process = run_background("main.py (deteksi wajah & angka)", ["python3", main_path])
    time.sleep(2)

    # Jalankan kamera hanya jika tersedia
    if check_camera_connected():
        cam_path = os.path.join(BASE_DIR, "camera_sync.py")
        if os.path.exists(cam_path):
            subprocess.run(["python3", cam_path])
        else:
            print("⚠️ File camera_sync.py tidak ditemukan.")
    else:
        print("⏩ Melewati mode tethered (tidak ada kamera).")

    # Loop utama untuk monitor proses
    try:
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"⚠️ Proses {p.args} berhenti mendadak, mencoba restart...")
                    processes.remove(p)
                    time.sleep(2)
                    run_background(p.args[-1], p.args)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Sistem dihentikan oleh pengguna.")
    finally:
        stop_all_processes()


if __name__ == "__main__":
    main()
