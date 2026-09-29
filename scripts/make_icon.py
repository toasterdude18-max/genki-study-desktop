"""Generate assets/genki.ico — a red rounded tile with a black "G".

Run:  python scripts\\make_icon.py   (from D:\\Genki Study)
"""
import os

from PIL import Image, ImageDraw, ImageFont

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(APP_DIR, "assets", "genki.ico")
PREVIEW = os.path.join(APP_DIR, "assets", "genki_preview.png")
SIZE = 256
RED = (217, 4, 41, 255)      # #d90429
BLACK = (0, 0, 0, 255)


def load_font(size):
    for path in (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def main():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 2, SIZE - 3, SIZE - 3], radius=48, fill=RED)

    font = load_font(int(SIZE * 0.66))
    text = "G"
    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    d.text(((SIZE - w) / 2 - bbox[0], (SIZE - h) / 2 - bbox[1]), text,
           font=font, fill=BLACK)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                         (64, 64), (128, 128), (256, 256)])
    img.save(PREVIEW)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
