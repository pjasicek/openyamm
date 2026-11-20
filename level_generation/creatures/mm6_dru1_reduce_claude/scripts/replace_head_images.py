#!/usr/bin/env python3
"""Replace the head half of every atlas image in a druidess GLB with new head-set maps (1024 square each), keeping the
body half: x 1056..2080 = head, x 1040..1055 = the head's first column repeated (gutter half, merge_head_material.py
layout). Images are matched by name: basecolor / metal_rough / normal / region_mask. The buffer is rebuilt.
Usage: replace_head_images.py <in.glb> <out.glb> <head prefix, e.g. textures/head_r66_>"""
import io, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
src, out, prefix = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
doc, binary = read_glb(src)
KEYS = ('basecolor', 'metal_rough', 'normal', 'region_mask')
views = []
for i, bv in enumerate(doc['bufferViews']):
    s = bv.get('byteOffset', 0); views.append(bytes(binary[s:s + bv['byteLength']]))
done = []
for im in doc['images']:
    key = next(k for k in KEYS if k in im['name'])
    atlas = Image.open(io.BytesIO(views[im['bufferView']])); mode = atlas.mode
    head = Image.open(f'{prefix}{key}.png').convert(mode)
    assert atlas.size == (2080, 1024) and head.size == (1024, 1024), (atlas.size, head.size)
    atlas.paste(head, (1056, 0)); atlas.paste(head.crop((0, 0, 1, 1024)).resize((16, 1024)), (1040, 0))
    buf = io.BytesIO(); atlas.save(buf, 'PNG', optimize=True); views[im['bufferView']] = buf.getvalue(); done.append(im['name'])
out_bin = bytearray()
for i, bv in enumerate(doc['bufferViews']):
    while len(out_bin) % 4: out_bin.append(0)
    bv['byteOffset'] = len(out_bin); bv['byteLength'] = len(views[i]); out_bin += views[i]
doc['buffers'][0]['byteLength'] = len(out_bin)
write_glb(out, doc, bytes(out_bin))
print('REPLACED', done)
