# contact sheet from views.json ([name, png] pairs): sheet.py DIR [cols] [w h]
import sys, os, json
from PIL import Image, ImageDraw
d0 = sys.argv[1]; cols = int(sys.argv[2]) if len(sys.argv) > 2 else 5
files = json.load(open(os.path.join(d0, "views.json")))
im0 = Image.open(files[0][1]); W, H = im0.size
rows = (len(files) + cols - 1) // cols
S = Image.new("RGB", (cols * W, rows * H), (40, 40, 40)); d = ImageDraw.Draw(S)
for k, (n, f) in enumerate(files):
    x, y = (k % cols) * W, (k // cols) * H
    S.paste(Image.open(f).convert("RGB"), (x, y)); d.text((x + 8, y + 6), n, fill=(255, 255, 0))
S.save(os.path.join(d0, "sheet.png")); print(S.size)
