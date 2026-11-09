#!/usr/bin/env python3
"""Texture-guard images per tier for the fix pass: the base colour of Skel_A / SkelHead_A from the installed GLB (tier skel_a is
the paint itself) and of Skel_R / SkelHead_R from the review-viewer copy with the tier ramps baked in (viewer_tiers.py on the
installed file). Writes work/fix/tex_<Skel|SkelHead>_<A|R>.png and work/fix/tex_list.json {material: [files]}."""
import io, json, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]; OUT = HERE / 'work' / 'fix'
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as glbio  # noqa: E402


def base_images(path):
    doc, binary = glbio.read(path); out = {}
    for m in doc['materials']:
        t = m.get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if t is None:
            continue
        im = doc['images'][doc['textures'][t['index']]['source']]; v = doc['bufferViews'][im['bufferView']]
        o = v.get('byteOffset', 0); out[m['name']] = Image.open(io.BytesIO(binary[o:o + v['byteLength']])).convert('RGB')
    return out


a = base_images(HERE / 'before' / 'mm9_skeleton.glb'); r = base_images(HERE / 'review' / 'viewer' / 'skel_r_inst.glb')
lst = {}
for pre in ('Skel', 'SkelHead'):
    files = []
    for tier, src in (('A', a[f'{pre}_A']), ('R', r[f'{pre}_R'])):
        f = f'tex_{pre}_{tier}.png'; src.save(OUT / f); files.append(f'fix/{f}'); print(f, src.size)
    lst[f'{pre}_A'] = files
(OUT / 'tex_list.json').write_text(json.dumps(lst, indent=1)); print(lst)
