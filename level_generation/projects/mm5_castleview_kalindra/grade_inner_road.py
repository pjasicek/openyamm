"""Bounded native grade between the authored bank and diviners' terraces."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent
# Preserve the building floor elevations; narrow the crossfall in the intervening lane.
SAMPLES = {(61, 53): 768, **{(61, c): 768 for c in range(54, 58)},
           **{(62, c): 704 for c in range(54, 58)}}


def apply(height, pads):
    for (row, column), value in SAMPLES.items():
        height[row, column] = value // 32
    for pad in pads:
        graded = {row*128+column: value for (row, column), value in SAMPLES.items()
                  if row*128+column in pad['supportVertices']}
        if not graded:
            continue
        pad['supportVertices'] = [n for n in pad['supportVertices'] if n not in graded]
        pad['gradedSupportVertices'] = [{'index': n, 'height': z} for n, z in sorted(graded.items())]
        pad['terrainTreatment'] = (
            'Retain the authored floor elevation and buried 64-unit skirt; road-side support triangles are graded. '
            'Validate the actual shell edges and the three diviners entrance steps against native terrain.')


def main():
    folder = PROJECT/'landscape'
    height = np.frombuffer((folder/'heightmap.raw').read_bytes(), dtype=np.uint8).reshape(128, 128).copy()
    terrain = json.loads((folder/'terrain.json').read_text())
    apply(height, terrain['pads'])
    (folder/'heightmap.raw').write_bytes(height.tobytes())
    Image.fromarray(height).save(folder/'heightmap_u8.png')
    Image.fromarray(height.astype(np.uint16)*32).save(folder/'heightmap_units_u16.png')
    (folder/'terrain.json').write_text(json.dumps(terrain, indent=2)+'\n')


if __name__ == '__main__':
    main()
