"""Convert a 16:9 flyer image into A4 print-ready files (300dpi, PNG + PDF).

The source aspect ratio (16:9) does not match A4 (√2:1), so the image is scaled
to fit the page width and the remaining area is filled with a blurred, darkened
copy of the image so the extension looks natural instead of a hard black bar.
"""
import sys
from PIL import Image, ImageFilter, ImageEnhance

DPI = 300
A4_LANDSCAPE = (3508, 2480)  # 297 x 210 mm @ 300dpi
A4_PORTRAIT = (2480, 3508)   # 210 x 297 mm @ 300dpi


def build(src: Image.Image, size: tuple[int, int]) -> Image.Image:
    W, H = size
    # Background: cover-scaled, heavily blurred and darkened copy of the source
    scale = max(W / src.width, H / src.height)
    bg = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    left = (bg.width - W) // 2
    top = (bg.height - H) // 2
    bg = bg.crop((left, top, left + W, top + H))
    bg = bg.filter(ImageFilter.GaussianBlur(60))
    bg = ImageEnhance.Brightness(bg).enhance(0.35)

    # Foreground: fit-scaled source, centered
    scale = min(W / src.width, H / src.height)
    fg = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    x = (W - fg.width) // 2
    y = (H - fg.height) // 2
    bg.paste(fg, (x, y))
    return bg


def main(src_path: str, out_dir: str) -> None:
    src = Image.open(src_path).convert("RGB")
    for name, size in (("A4_landscape", A4_LANDSCAPE), ("A4_portrait", A4_PORTRAIT)):
        img = build(src, size)
        img.save(f"{out_dir}/{name}.png", dpi=(DPI, DPI))
        img.save(f"{out_dir}/{name}.pdf", "PDF", resolution=DPI)
        print(name, img.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
