import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_required_folders_exist():
    folders = ["uploads", "output/wajah", "output/angka", "models/wajah"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        assert os.path.exists(folder), f"Folder {folder} tidak ditemukan!"
