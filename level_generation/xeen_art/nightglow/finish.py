"""Height maps, checks, review sheet and install of the night-glow surface maps of xaenergy and xafield (A6, s14).

xaenergy's height is the Codex depth pass (raw/xaenergy_height_v1.png, mat.py's prompt; mat.py's alignment and
colour-tracing checks); xafield's is flat (a force field has no relief). Classes from classes.py.
usage: python3 finish.py [--install]
"""
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'level_generation/surface_materials'))
import mat  # noqa: E402
import surface_materials  # noqa: E402

CLASSES = surface_materials.load_classes()
WRAP = {'xaenergy': 'uv', 'xafield': 'uv'}
TARGET = ROOT / 'assets_source/worlds/xeen/surface_materials'


def master_of(stem):
    return np.asarray(Image.open(ROOT / f'assets_source/worlds/xeen/textures_x4/{stem}.png').convert('RGBA'))


def height_of(stem, master):
    size = (master.shape[1], master.shape[0])
    if stem == 'xafield':
        return np.full(master.shape[:2], 0.5, np.float32), []
    raw = HERE / 'raw' / f'{stem}_height_v1.png'
    height = np.asarray(Image.open(raw).convert('RGB').resize(size, Image.LANCZOS)).astype(np.float32).mean(-1) / 255
    luminance = master[..., :3].astype(np.float32) @ surface_materials.LUMA / 255.0
    problems = []
    shift = mat.phase_shift(mat.edges(luminance), mat.edges(height))
    if max(abs(shift[0]) / size[1], abs(shift[1]) / size[0]) > mat.MAX_SHIFT_FRACTION:
        problems.append(f'height misaligned by {shift} texels')
    correlation = float(np.corrcoef(luminance.ravel(), height.ravel())[0, 1])
    if correlation > mat.MAX_HEIGHT_LUMINANCE_CORRELATION:
        problems.append(f'height follows the colours ({correlation:.2f})')
    print(f'{stem}: shift {shift}, luminance correlation {correlation:.2f}')
    return mat.seamless(height, WRAP[stem]), problems


def main():
    rows = []
    out = HERE / 'candidates'
    for stem in ('xaenergy', 'xafield'):
        master = master_of(stem)
        height, problems = height_of(stem, master)
        rgb = np.asarray(Image.open(out / f'{stem}_m.png').convert('RGB'))
        indices = surface_materials.class_indices(rgb, CLASSES)
        Image.fromarray(np.clip(np.rint(height * 65535.0), 0, 65535).astype(np.uint16)).save(out / f'{stem}_h.png')
        normal, detail = surface_materials.build_maps(master, height, indices, CLASSES, {'wrap': WRAP[stem]})
        rows.append((stem, master, height, indices, normal, detail, problems))
        print(stem, 'problems:', problems or 'none')
    mat.review_sheet(rows, cell=300).save(out / 'sheet.png')
    if '--install' in sys.argv:
        TARGET.mkdir(parents=True, exist_ok=True)
        settings_path = TARGET / 'textures.yml'
        settings = (yaml.safe_load(settings_path.read_text()) or {}) if settings_path.is_file() else {}
        for stem in WRAP:
            (TARGET / f'{stem}_h.png').write_bytes((out / f'{stem}_h.png').read_bytes())
            (TARGET / f'{stem}_m.png').write_bytes((out / f'{stem}_m.png').read_bytes())
            settings.setdefault(stem, {})['wrap'] = WRAP[stem]
        settings_path.write_text(
            '# Surface material settings per texture (Xeen: level_generation/xeen_art/nightglow/finish.py writes wrap;\n'
            '# depth and painted_shading are review overrides, tools/surface_materials.py).\n'
            + yaml.safe_dump(dict(sorted(settings.items())), sort_keys=True))
        print('installed into', TARGET)


if __name__ == '__main__':
    main()
