"""Pack painted cylinder UVs/masks and unlit metal tiles at consistent axial texel density."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes, gaussian_filter

HERE = Path(__file__).resolve().parents[1]


def prepare(icon):
    folder = HERE / 'textures' / icon
    painted = folder / 'shaft_uv_painted_v2.png'
    if not painted.exists():
        painted = folder / 'shaft_uv_painted.png'
    sheet = Image.open(painted).convert('RGB')
    assert abs(sheet.width / sheet.height - 1) < .02
    colour = sheet.crop((0, 0, sheet.width // 2, sheet.height)).resize((56, 1016), Image.Resampling.LANCZOS)
    mask = sheet.crop((sheet.width // 2, 0, sheet.width, sheet.height)).convert('L').resize((56, 1016), Image.Resampling.NEAREST)
    base = np.zeros((1024, 512, 3), np.float32)
    metal = np.ones((1024, 512), np.float32)
    base[4:1020, 4:60] = np.asarray(colour) / 255
    body_metal = binary_fill_holes(np.asarray(mask) > 127)
    rgb = base[4:1020, 4:60]
    if icon in ('staff3', '6staff4'):
        # The generated mask over-marked enamel collar rows; their red/blue pigment is dielectric.
        red, green, blue = np.moveaxis(rgb, -1, 0)
        enamel = (blue > red * 1.15) | ((red > green * 1.6) & (red > blue * 1.5))
        body_metal &= ~enamel
    metal[4:1020, 4:60] = body_metal
    base[:4, 4:60] = base[4, 4:60]
    base[1020:, 4:60] = base[1019, 4:60]
    metal[:4, 4:60] = metal[4, 4:60]
    metal[1020:, 4:60] = metal[1019, 4:60]
    for edge in range(4):
        base[:, edge] = base[:, 4]
        base[:, 60 + edge] = base[:, 59]
        metal[:, edge] = metal[:, 4]
        metal[:, 60 + edge] = metal[:, 59]
    for row, name in [(0, 'steel'), (512, 'gold')]:
        tile = Image.open(HERE / 'textures/raw' / (name + '.png')).convert('RGB').resize((448, 512))
        base[row:row + 512, 64:] = np.asarray(tile) / 255
    design = json.loads((HERE / 'designs.json').read_text())['pole_' + icon]
    if design.get('gem_head'):
        colour = np.array(design['gem_head']['colour']) / 255
        texture = base[:512, 64:]
        grain = texture.mean(axis=-1) / texture.mean()
        base[:512, 64:] = colour * np.clip(grain[..., None], .92, 1.08)
        metal[:512, 64:] = 0
    base = np.clip(base, 30 / 255, 243 / 255)
    roughness = np.where(metal > .5, .4, .72)
    if design.get('gem_head'):
        roughness[:512, 64:] = .22
    elif icon in ('7item031', '7item036', 'item046', 'item051', '7item039'):
        roughness[:512, 64:] = .62
    orm = np.stack([np.ones_like(metal), roughness, metal], -1)
    height = base @ np.array([.2126, .7152, .0722])
    detail = height - gaussian_filter(height, 2)
    dy, dx = np.gradient(detail)
    # Image rows point down, while glTF's tangent +Y follows increasing v (up).
    normal = np.stack([-dx * .8, dy * .8, np.ones_like(dx)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    for name, pixels in [('basecolor', base), ('mr', orm), ('normal', normal * .5 + .5)]:
        Image.fromarray(np.round(pixels * 255).astype(np.uint8)).save(folder / (name + '.png'))
    report = {'icon': icon, 'atlas_size': [512, 1024], 'source_paint': painted.name,
              'normal_convention': 'OpenGL +Y', 'body_metal_fraction': float(body_metal.mean()),
              'base_range': [int(np.round(base.min() * 255)), int(np.round(base.max() * 255))],
              'texel_density': 'shaft axial about 500 px/m; circumference about 500–1100 px/m; blades about 500 px/m'}
    (folder / 'atlas_report.json').write_text(json.dumps(report, indent=2) + '\n')
    assert set(np.unique(metal)).issubset({0, 1})
    assert np.isfinite(normal).all() and np.allclose(np.linalg.norm(normal, axis=-1), 1)
    print('ATLAS', icon, report['body_metal_fraction'])


if __name__ == '__main__':
    for icon in sys.argv[1:]:
        prepare(icon)
