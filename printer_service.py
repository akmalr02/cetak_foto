import os
import subprocess

def print_file(file_path):
    """Cetak file gambar langsung ke printer menggunakan lp (Linux)."""
    if not os.path.exists(file_path):
        print(f"❌ File tidak ditemukan: {file_path}")
        return

    print(f"🖨️ Mengirim ke printer: {file_path}")
    try:
        subprocess.run(["lp", "-o", "fit-to-page", file_path], check=True)
        print("✅ File terkirim ke printer.")
    except subprocess.CalledProcessError:
        print("⚠️ Gagal mengirim ke printer. Pastikan printer terhubung.")
