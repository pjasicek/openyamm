"""Turn the project's generated textures into a source tree the cook tools and the bake read.

  python3 source/make_textures.py

For every textures/codex/<stem>.png (a seamless square Codex texture) it writes, under textures/root/worlds/mm6:
textures_x4/<stem>.png (512x512 master, 128 native texels), textures_x2/<stem>.png, textures/<stem>.bmp (native),
and surface material maps: surface_materials/<stem>_m.png (stone, mortar in the dark joints) and <stem>_h.png
(16-bit height from the blurred brightness, joints recessed), plus textures.yml (wrap on both axes).
build.py cooks them into the stage only (cook_surface_textures.py and surface_materials.py with --only).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PROJECT = Path(__file__).resolve().parents[1]
CODEX = PROJECT / 'textures/codex'
ROOT = PROJECT / 'textures/root/worlds/mm6'
NATIVE = 128
STONE, MORTAR, WOOD = (190, 150, 90), (110, 110, 110), (255, 128, 0)
# Stone ashlars get mortar joints in their class map; boards are wood throughout (trim_textures.py).
TEXTURES = ['lgashlar', 'rblcut', 'tewcut', 'tavcut', 't1cut', 'thcut', 'slatecap', 'cscut', 'strcut', 'hccut', 'gbcut']
# Brightness gains measured against the concepts: dressed coping and trim read a step lighter than the rubble.
GAIN = {'rblcut': 1.25, 'tewcut': 2.0, 'dockdeck': 1.15, 'roofcap': 1.25}
BOARDS = ['rhwood', 'pxshcap', 'plrcap', 'dockdeck', 'dkwood', 'snowcap', 'pbrcap', 'thatchcap', 'roofcap']


def main():
    for folder in ('textures_x4', 'textures_x2', 'textures', 'surface_materials'):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    settings = []
    for stem in TEXTURES + BOARDS:
        source = Image.open(CODEX / f'{stem}.png').convert('RGB')
        if stem in GAIN:
            source = Image.fromarray(np.clip(np.asarray(source, float) * GAIN[stem], 0, 255).astype(np.uint8))
        master = source.resize((NATIVE * 4, NATIVE * 4), Image.LANCZOS)
        master.save(ROOT / 'textures_x4' / f'{stem}.png')
        master.resize((NATIVE * 2, NATIVE * 2), Image.LANCZOS).save(ROOT / 'textures_x2' / f'{stem}.png')
        master.resize((NATIVE, NATIVE), Image.LANCZOS).save(ROOT / 'textures' / f'{stem}.bmp')
        luma = np.asarray(master.convert('L'), float)
        smooth = np.asarray(master.convert('L').filter(ImageFilter.GaussianBlur(24)), float)
        # Dark stone has dark pits as well as joints: a stricter threshold keeps the pits on the stone.
        joints = luma < np.minimum(smooth * (0.4 if luma.mean() < 80 else 0.55), 40)
        if stem in BOARDS:
            joints &= False
        classes = np.zeros(luma.shape + (3,), np.uint8)
        classes[:] = WOOD if stem in BOARDS else STONE
        classes[joints] = MORTAR
        Image.fromarray(classes).save(ROOT / 'surface_materials' / f'{stem}_m.png')
        height = np.asarray(master.convert('L').filter(ImageFilter.GaussianBlur(2)), float)
        height[joints] *= 0.3
        height = (height - height.min()) / max(np.ptp(height), 1e-6)
        Image.fromarray((height * 65535).astype(np.uint16)).save(ROOT / 'surface_materials' / f'{stem}_h.png')
        settings.append(f'{stem}:\n  wrap: uv\n')
        print(stem, 'joints', round(float(joints.mean()) * 100, 1), '%')
    (ROOT / 'surface_materials/textures.yml').write_text(''.join(settings))


if __name__ == '__main__':
    main()
