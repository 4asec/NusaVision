import os
from PIL import Image, JpegImagePlugin

def compile_pdf():
    cache_dir = r"D:\nusavision\submission_assets\slide_cache"
    output_pdf = r"D:\nusavision\submission_assets\NusaVision_Slide_Deck_Kartika2026.pdf"
    root_pdf = r"D:\nusavision\NusaVision_Slide_Deck_Kartika2026.pdf"

    images = []
    print("Membaca 12 slide PNG 1920x1080...")
    for i in range(1, 13):
        slide_img = os.path.join(cache_dir, f"slide_{i:02d}.png")
        if not os.path.exists(slide_img):
            raise FileNotFoundError(f"Missing {slide_img}")
        img = Image.open(slide_img).convert("RGB")
        images.append(img)
        print(f"  [+] Slide {i:02d} dimuat ({img.size[0]}x{img.size[1]})")

    print(f"Menyusun ke PDF 16:9...")
    images[0].save(
        output_pdf,
        save_all=True,
        append_images=images[1:],
        resolution=100.0,
        quality=95
    )
    images[0].save(
        root_pdf,
        save_all=True,
        append_images=images[1:],
        resolution=100.0,
        quality=95
    )
    print(f"BERHASIL! PDF tersimpan di:\n  1. {output_pdf} ({os.path.getsize(output_pdf)} bytes)\n  2. {root_pdf}")

if __name__ == "__main__":
    compile_pdf()
