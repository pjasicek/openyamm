#!/usr/bin/env python3
"""Replace only the region-mask image of a creature GLB (the image the first material's openyamm_region_mask points
at); every other buffer view is copied byte-for-byte in order. Usage: swap_mask.py <in.glb> <mask.png> <out.glb>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
src, png, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
doc, binary = read_glb(src)
image = doc['textures'][doc['materials'][0]['extras']['openyamm_region_mask']['index']]['source']
target = doc['images'][image]['bufferView']
new = bytearray()
for i, view in enumerate(doc['bufferViews']):
    start = view.get('byteOffset', 0)
    data = png.read_bytes() if i == target else binary[start:start + view['byteLength']]
    new.extend(b'\0' * (-len(new) % 4)); view['byteOffset'] = len(new); view['byteLength'] = len(data); new.extend(data)
write_glb(out, doc, bytes(new))
print('MASK swapped image', image, 'view', target, f'{len(new) / 1e6:.2f} MB')
