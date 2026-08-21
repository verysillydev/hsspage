#!/usr/bin/env python3
"""Diagonal lattice watermark. Text sits at the intersection points of a
rotated grid, light enough to read through but present on every frame."""
from PIL import Image, ImageDraw, ImageFont
import sys

# usage: make_wm.py out.png [width height]   defaults to 640x360
W = int(sys.argv[2]) if len(sys.argv) > 3 else 640
H = int(sys.argv[3]) if len(sys.argv) > 3 else 360
K = W / 640.0                        # scale the lattice with the frame
ANGLE = -30                          # lattice rotation
DX, DY = round(226 * K), round(104 * K)   # spacing between intersection points
FS = round(12 * K)                   # type size
LABELS = ("HOME SERVICE STUDIOS", "YONIVERSE PRODUCTIONS")

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
font = ImageFont.truetype(FONT, FS)

# oversized canvas so rotation never exposes empty corners
BIG = int((W ** 2 + H ** 2) ** 0.5) + 2 * max(DX, DY)
canvas = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
d = ImageDraw.Draw(canvas)

rows = BIG // DY + 2
cols = BIG // DX + 2
for r in range(rows):
    for c in range(cols):
        # offset alternate rows so the lattice reads as a grid, not columns
        x = c * DX + (DX // 2 if r % 2 else 0)
        y = r * DY
        label = LABELS[(r + c) % 2]
        w = d.textlength(label, font=font)
        px, py = x - w / 2, y - FS / 2
        # dark pass first so the mark survives on light footage too
        d.text((px + 1, py + 1), label, font=font, fill=(0, 0, 0, 58))
        d.text((px, py), label, font=font, fill=(255, 255, 255, 64))

rot = canvas.rotate(ANGLE, resample=Image.BICUBIC, expand=False)
left, top = (BIG - W) // 2, (BIG - H) // 2
out = rot.crop((left, top, left + W, top + H))
out.save(sys.argv[1] if len(sys.argv) > 1 else "wm.png")
print("wrote watermark", out.size)
