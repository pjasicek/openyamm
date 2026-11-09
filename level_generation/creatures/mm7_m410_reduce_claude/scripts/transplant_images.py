#!/usr/bin/env python3
"""Replace a GLB's images with those of a re-exported source of the same model, matched by image name (review
2026-10-20: the source project's body textures were recomposed after this reduction to remove patches on the arms and
trousers; the reduced geometry, LODs, clips, materials and variants stay as they are). Every image of the target must
exist in the source under the same name; the binary is rebuilt with the new image bytes. The materials' extras
(the region ramps measured with the new texture) are copied by material name too.
Usage: transplant_images.py <source.glb> <target.glb> <out.glb>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

src, dst, out = (Path(a) for a in sys.argv[1:4])
sdoc, sbin = read_glb(src)
doc, binary = read_glb(dst)
simg = {im['name']: im for im in sdoc['images']}
repl = {}
for im in doc['images']:
    s = simg[im['name']]; v = sdoc['bufferViews'][s['bufferView']]; o = v.get('byteOffset', 0)
    repl[im['bufferView']] = sbin[o:o + v['byteLength']]
newbin, views = bytearray(), []
for i, v in enumerate(doc['bufferViews']):
    v = copy.deepcopy(v); o = v.get('byteOffset', 0)
    data = repl.get(i, binary[o:o + v['byteLength']])
    newbin.extend(b'\0' * (-len(newbin) % 4)); v['byteOffset'] = len(newbin); v['byteLength'] = len(data)
    newbin.extend(data); views.append(v)
doc['bufferViews'] = views
smat = {m['name']: m for m in sdoc['materials']}
for m in doc['materials']:
    if 'extras' in smat[m['name']]:
        m['extras'] = copy.deepcopy(smat[m['name']]['extras'])
write_glb(out, doc, bytes(newbin))
print('IMAGES', len(repl), 'replaced', src.name, '->', out.name, f'{len(newbin) / 1e6:.2f} MB')
