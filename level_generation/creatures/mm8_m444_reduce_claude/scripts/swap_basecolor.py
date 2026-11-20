#!/usr/bin/env python3
"""Replace only the base-colour image (pbrMetallicRoughness baseColorTexture) of a GLB with a new PNG of the same size and
mode; every other buffer view keeps its bytes. Usage: swap_basecolor.py <in.glb> <basecolor.png> <out.glb>"""
import copy, io, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
src, png, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
doc, binary = read_glb(src)
idx = {m['pbrMetallicRoughness']['baseColorTexture']['index'] for m in doc['materials']}
assert len(idx) == 1, idx
image = doc['images'][doc['textures'][idx.pop()]['source']]
old_view = image['bufferView']; ov = doc['bufferViews'][old_view]
old = Image.open(io.BytesIO(binary[ov.get('byteOffset', 0):ov.get('byteOffset', 0) + ov['byteLength']]))
new = Image.open(png); assert new.size == old.size and new.mode == old.mode, (new.size, new.mode, old.size, old.mode)
data = png.read_bytes()
# rebuild the buffer: same views in order, the mask view's bytes replaced
views, newbin = [], bytearray()
for i, v in enumerate(doc['bufferViews']):
    start = v.get('byteOffset', 0); chunk = data if i == old_view else binary[start:start + v['byteLength']]
    newbin.extend(b'\0' * (-len(newbin) % 4)); nv = copy.deepcopy(v); nv['byteOffset'] = len(newbin)
    nv['byteLength'] = len(chunk); newbin.extend(chunk); views.append(nv)
doc['bufferViews'] = views
write_glb(out, doc, bytes(newbin))
print('BASECOLOR swapped', image.get('name'), len(data), 'bytes')
