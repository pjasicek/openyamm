"""Prepare physical component profiles and exact cylindrical UV paint templates; never installs assets."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import median_filter

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
# Fraction of source height occupied by the head, including its socket/attachment.
HEADS = dict(zip(
    '6trident5 7item031 7item032 7item033 7item034 7item035 7item036 7item037 7item038 7item039 7item040 7item041 7item225 7item227 halberd1 halberd2 halberd3 item041 item042 item043 item044 item045 item046 item047 item048 item049 item050 item051 item052 item053 item054 item055 item242 item243 item244 item331 item341 spear1 spear2 spear3 spear4 spear5 trident1 trident2 trident3 6staff4 7item061 7item062 7item063 7item233 item079 item080 item081 item082 item083 item250 item335 staff1 staff2 staff3'.split(),
    [.30,.16,.23,.37,.27,.28,.31,.30,.33,.31,.31,.32,.34,.42,.36,.38,.38,0,.37,.40,.40,.44,.29,.30,.35,.39,.43,.30,.27,.51,.36,.41,.36,.42,.42,.44,.44,.28,.24,.30,.49,.39,.42,.29,.30,.24,0,.22,.20,.36,0,.23,.30,.29,1,.44,1,.23,.20,.24]))
HYBRID = {'staff3': 'staff3', '6staff4': 'staff3', '7item063': '7item063', '7item233': '7item233',
          'item050': 'item050', 'item250': 'item250', 'item082': 'item082',
          'item083': 'item083', 'item335': 'item083', 'item242': 'item242'}
GROUPS = {'6trident5': 'trident3', '6staff4': 'staff3', 'item335': 'item083',
          'item331': 'item045', 'item341': 'item045'}


def simplify(points, epsilon):
    points = np.asarray(points, float)
    if len(points) < 3:
        return points.tolist()
    direction = points[-1] - points[0]
    norm = np.linalg.norm(direction)
    distance = (np.abs(direction[0] * (points[:, 1] - points[0, 1])
                       - direction[1] * (points[:, 0] - points[0, 0])) / norm
                if norm > 1e-9 else np.linalg.norm(points - points[0], axis=1))
    split = int(distance.argmax())
    if distance[split] <= epsilon:
        return [points[0].tolist(), points[-1].tolist()]
    return simplify(points[:split + 1], epsilon)[:-1] + simplify(points[split:], epsilon)


def contours(mask):
    """Directed pixel boundaries, simplified without altering the spaces between polearm blades."""
    edges = {}
    h, w = mask.shape
    for y, x in zip(*np.nonzero(mask)):
        for neighbour, a, b in [((y - 1, x), (x, y), (x + 1, y)),
                                 ((y, x + 1), (x + 1, y), (x + 1, y + 1)),
                                 ((y + 1, x), (x + 1, y + 1), (x, y + 1)),
                                 ((y, x - 1), (x, y + 1), (x, y))]:
            yy, xx = neighbour
            if not (0 <= yy < h and 0 <= xx < w and mask[yy, xx]):
                edges.setdefault(a, []).append(b)
    loops = []
    while edges:
        start = next(iter(edges))
        current, loop = start, [start]
        while True:
            nxt = edges[current].pop()
            if not edges[current]:
                del edges[current]
            current = nxt
            if current == start:
                break
            loop.append(current)
        if len(loop) < 6:
            continue
        split = int(np.linalg.norm(np.asarray(loop) - np.asarray(loop[0]), axis=1).argmax())
        result = simplify(loop[:split + 1], .65)[:-1] + simplify(loop[split:] + [loop[0]], .65)[:-1]
        if len(result) >= 3:
            loops.append(result)
    return loops


def main():
    owned = json.loads((HERE / 'ownership.json').read_text())
    for icon in ('item082', 'item083', 'item335', 'item242'):
        HEADS[icon] = 1
    previous = json.loads((HERE / 'designs.json').read_text())
    designs = {}
    for entry in owned:
        icon = entry['icon']
        image = Image.open(ROOT / entry['icon_reference']).convert('RGBA')
        rgba = np.asarray(image)
        mask = rgba[:, :, 3] > 127
        h, w = mask.shape
        end = round(HEADS[icon] * h)
        profiles = []
        for y in range(min(end, h - 1), h):
            xs = np.flatnonzero(mask[y])
            if len(xs):
                profiles.append([float(y), float((xs.min() + xs.max()) / 2), float((xs.max() - xs.min() + 1) / 2)])
        profile = np.asarray(profiles)
        if len(profile):
            profile[:, 1:] = median_filter(profile[:, 1:], size=(5, 1), mode='nearest')
            # Ring spacing follows physical changes in centreline/radius, not a dense pixel lattice.
            indexes = {0, len(profile) - 1}
            for axis in [1, 2]:
                reduced = simplify(profile[:, [0, axis]], .45)
                indexes.update(int(np.argmin(abs(profile[:, 0] - point[0]))) for point in reduced)
            profile = profile[sorted(indexes)]
        head_mask = mask.copy()
        head_mask[end:] = False
        loops = contours(head_mask) if end and icon not in HYBRID else []
        design = {'title': entry['items'][0]['name'], 'icons': [icon], 'master_icon': icon,
                  'route': 'hybrid' if icon in HYBRID else 'blender', 'geometry_group': GROUPS.get(icon, icon),
                  'image_size': [w, h], 'head_end': end, 'head_loops': loops, 'shaft_profile': profile.tolist(),
                  'length': entry['binding']['length'], 'tris': 12000,
                  'mesh_head': HYBRID.get(icon), 'identity': entry['items'][0]['name'] + ': preserve the source icon components and proportions.'}
        old = previous.get('pole_' + icon, {})
        design = {**old, **design, 'tris': old.get('tris', design['tris']), 'route': old.get('route', design['route'])}
        designs['pole_' + icon] = design
        folder = HERE / 'textures' / icon
        folder.mkdir(parents=True, exist_ok=True)
        # Left: cylinder albedo, right: its matching binary material mask. Both are exact 512x1024 UV rectangles.
        template = Image.new('RGB', (1024, 1024), (96, 96, 96))
        draw = ImageDraw.Draw(template)
        for row in range(1024):
            sy = min(h - 1, end + int(row / 1023 * max(h - 1 - end, 1)))
            xs = np.flatnonzero(mask[sy])
            if len(xs):
                centre = int(np.median(xs))
                samples = rgba[sy, max(0, centre - 2):centre + 3, :3]
                colour = tuple(np.median(samples, axis=0).astype(int))
            else:
                colour = (100, 80, 50)
            draw.line((0, row, 511, row), fill=colour)
            draw.line((512, row, 1023, row), fill=(0, 0, 0))
        template.save(folder / 'shaft_uv_template.png')
    (HERE / 'designs.json').write_text(json.dumps(designs, indent=2) + '\n')
    assert len(designs) == len(owned) == 60
    assert len(contours(np.ones((4, 8), bool))) == 1
    print('Prepared 60 component designs and exact shaft UV templates')


if __name__ == '__main__':
    main()
