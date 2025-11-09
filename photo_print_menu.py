import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
from printer_service import print_file

OUTPUT_DIR = "output"
PRINT_READY_DIR = "print_ready"

os.makedirs(PRINT_READY_DIR, exist_ok=True)

PHOTO_SIZES = {
    "2x3": (20, 30),
    "3x4": (30, 40),
    "4x6": (40, 60),
    "A4": (210, 297),
}


def list_photos():
    """Menampilkan semua foto dari folder output"""
    print("\n📸 Daftar foto siap cetak:")
    all_photos = []
    for subdir, _, files in os.walk(OUTPUT_DIR):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                full_path = os.path.join(subdir, f)
                all_photos.append(full_path)
                print(f"[{len(all_photos)}] {full_path}")
    return all_photos


def resize_photo(input_path, output_path, size_mm):
    """Ubah ukuran foto ke ukuran tertentu (mm)"""
    width_px = int(size_mm[0] / 25.4 * 300) 
    height_px = int(size_mm[1] / 25.4 * 300)
    img = Image.open(input_path)
    img_resized = img.resize((width_px, height_px))
    img_resized.save(output_path)
    return output_path


def create_pdf_for_print(image_path, copies=1):
    """Buat PDF siap cetak (A4 layout)"""
    filename = os.path.splitext(os.path.basename(image_path))[0]
    pdf_path = os.path.join(PRINT_READY_DIR, f"{filename}_print.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    img = Image.open(image_path)
    img_width, img_height = img.size
    a4_width, a4_height = A4

    for i in range(copies):
        # Posisikan di tengah halaman
        x = (a4_width - img_width * 0.24) / 2
        y = (a4_height - img_height * 0.24) / 2
        c.drawImage(image_path, x, y, img_width * 0.24, img_height * 0.24)
        c.showPage()

    c.save()
    return pdf_path


def start_photo_print_menu():
    print("🖨️=== MENU CETAK FOTO ===")

    photos = list_photos()
    if not photos:
        print("❌ Tidak ada foto ditemukan di folder output/")
        return

    try:
        pilihan = int(input("\nPilih nomor foto yang ingin dicetak: "))
        selected_photo = photos[pilihan - 1]
    except (ValueError, IndexError):
        print("⚠️ Pilihan tidak valid.")
        return

    print("\nUkuran foto tersedia:")
    for i, size in enumerate(PHOTO_SIZES.keys(), 1):
        print(f"{i}. {size}")

    try:
        size_choice = int(input("\nPilih ukuran: "))
        size_key = list(PHOTO_SIZES.keys())[size_choice - 1]
    except (ValueError, IndexError):
        print("⚠️ Pilihan tidak valid.")
        return

    copies = int(input("Masukkan jumlah cetak: ") or "1")

    # Buat versi resize
    resized_path = os.path.join(
        PRINT_READY_DIR,
        f"{os.path.basename(selected_photo).split('.')[0]}_{size_key}.jpg"
    )
    resized_path = resize_photo(selected_photo, resized_path, PHOTO_SIZES[size_key])

    print(f"\n✅ Siap mencetak {copies}x foto '{size_key}' dari {selected_photo}")
    print("1️⃣ Cetak langsung ke printer")
    print("2️⃣ Simpan sebagai PDF saja")
    option = input("Pilih opsi (1/2): ").strip()

    if option == "1":
        for _ in range(copies):
            print_file(resized_path)
    elif option == "2":
        pdf_path = create_pdf_for_print(resized_path, copies)
        print(f"📄 File PDF tersimpan: {pdf_path}")
    else:
        print("❎ Cetak dibatalkan.")


if __name__ == "__main__":
    start_photo_print_menu()
