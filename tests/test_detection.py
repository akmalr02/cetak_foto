import easyocr
import re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_ocr_detects_number(tmp_path):
    reader = easyocr.Reader(["en"])
    # Buat teks dummy dengan angka
    test_text = "Nomor 123"
    img_path = tmp_path / "test_image.jpg"

    # Buat gambar kecil dengan teks dummy
    import cv2
    import numpy as np
    img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, test_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.imwrite(str(img_path), img)

    result = reader.readtext(str(img_path))
    combined_text = " ".join([res[1] for res in result])
    assert re.search(r"\d+", combined_text), "OCR gagal mendeteksi angka!"
