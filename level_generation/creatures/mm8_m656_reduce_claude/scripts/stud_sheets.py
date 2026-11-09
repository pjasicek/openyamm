"""Before/after sheets for the stud relief (textures_v3): close-ups in tier A (installed, v2, v3) and full-body tiers
(installed vs v3 for A/B/C), from review/glbclose renders. Usage: stud_sheets.py -> review/studs_v3/*.png"""
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]
G = HERE / 'review/glbclose'
OUT = HERE / 'review/studs_v3'
OUT.mkdir(parents=True, exist_ok=True)


def sheet(rows, cols, name, size=300):
    W, H = 110 + size * len(cols), 22 + size * len(rows)
    s = Image.new('RGB', (W, H), (28, 29, 33))
    d = ImageDraw.Draw(s)
    for c, col in enumerate(cols):
        d.text((110 + c * size + 6, 5), col, fill=(240, 220, 120))
    for r, (label, tag) in enumerate(rows):
        d.text((6, 22 + r * size + size // 2), label, fill=(230, 230, 230))
        for c, col in enumerate(cols):
            f = G / f'{tag}_{col}_tex.png'
            if f.exists():
                s.paste(Image.open(f).convert('RGB').resize((size, size), Image.LANCZOS), (110 + c * size, 22 + r * size))
    s.save(OUT / name)
    print(OUT / name, s.size)


sheet([('installed A', 'inst_a'), ('v2 A', 'v2_a'), ('v3 studs A', 'v3_a')],
      ['torso', 'back', 'pauldron', 'bracer', 'hand_l', 'boots', 'chest_graze', 'head_front'], 'closeups_a.png')
sheet([(f'{n} {t.upper()}', f'{p}_{t}') for t in 'abc' for n, p in (('installed', 'inst'), ('v3 studs', 'v3'))],
      ['full_front', 'full_q34', 'full_back', 'torso'], 'tiers.png', 320)
