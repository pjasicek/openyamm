#!/usr/bin/env python3
"""Material class map for the barbarian's head set, which mm6_bar1_claude/scripts/compose_bar1.py did not write.

The installed head half of the atlas (assets_source mm6_bar1.glb, x 1056-2079) carries compose_bar1's per-class
specular mask in R: skin 0.45 (115), gold circlet 1.0 (255), everything else 0.3 (77: hair, brows, eyes, lips seams).
Labels: R 115 -> skin (1), R 255 -> metal (9); R 77 -> hair (2), except the painted eyes -> eye (6): texels of the
face shell (HeadUV raster piece 0) inside a small box around each eye, found from the eye whites (low saturation,
bright), with R 77 or dark (the iris and pupil carry the skin value 115). The circlet's pale leaf has R 115 and stays
skin (its hue overlaps the skin's). The small extra pieces (mouth, 14 / 18; 15) become mouth (7) and other (11).
Outside the raster: 0.
Usage: bar1_head_classes.py <installed mm6_bar1.glb> <out.png> [preview.png]"""
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import region_variants as RV  # noqa: E402

RASTER = Path(__file__).resolve().parents[2] / 'mm6_bar1_claude' / 'work' / 'uvraster_HeadUV.npz'
HEAD_X = 1056
EYE_BOX = np.array([0.016, 0.02, 0.009])   # half extents (x, y, z) in metres around each eye's white


def image(doc, binary, name_part):
    entry = next(i for i in doc['images'] if name_part in i.get('name', ''))
    view = doc['bufferViews'][entry['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[start:start + view['byteLength']]))


def main():
    glb, out = sys.argv[1], sys.argv[2]
    doc, binary = RV.read_glb(glb)
    base = image(doc, binary, 'basecolor').convert('RGB').crop((HEAD_X, 0, HEAD_X + 1024, 1024))
    r = np.asarray(image(doc, binary, 'metal_rough').convert('RGB'))[:, HEAD_X:HEAD_X + 1024, 0]
    raster = np.load(RASTER)
    piece, pos = raster['piece'], raster['pos']
    hsv = np.asarray(base.convert('HSV'), np.float64) / 255
    labels = np.zeros((1024, 1024), np.uint8)
    inside = piece >= 0
    labels[inside & (r == 115)] = 1
    labels[inside & (r == 255)] = 9
    labels[inside & (r == 77)] = 2
    labels[np.isin(piece, [14, 18])] = 7
    labels[piece == 15] = 11
    white = (piece == 0) & (r == 77) & (hsv[..., 1] < 0.35) & (hsv[..., 2] > 0.55)
    eyes = np.zeros_like(white)
    for side in (pos[..., 0] < 0, pos[..., 0] >= 0):
        seeds = white & side
        if seeds.sum() < 10:
            continue
        centre = np.median(pos[seeds], 0)
        # the dark iris and pupil carry the skin mask (115) in compose_bar1 (brown hue): take them by value
        eyes |= (piece == 0) & ((r == 77) | (hsv[..., 2] < 0.45)) & np.all(np.abs(pos - centre) <= EYE_BOX, -1)
        print('EYE centre', np.round(centre, 3), 'white texels', int(seeds.sum()))
    labels[eyes] = 6
    Image.fromarray(labels, 'L').save(out)
    print('CLASSES', {int(k): int(v) for k, v in zip(*np.unique(labels, return_counts=True))})
    if len(sys.argv) > 3:
        preview = np.asarray(base).copy()
        preview[labels == 6] = (0, 255, 255)
        preview[labels == 9] = (255, 255, 0)
        preview[labels == 7] = (255, 0, 255)
        preview[labels == 0] //= 3
        Image.fromarray(preview).save(sys.argv[3])


if __name__ == '__main__':
    main()
