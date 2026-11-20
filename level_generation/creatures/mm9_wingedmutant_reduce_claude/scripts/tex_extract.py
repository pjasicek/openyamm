#!/usr/bin/env python3
"""Texture guard images for mpqem.py: each LOD0 material's base colour in the three tiers, taken from the creature's approved
review-viewer GLBs (../mm9_wingedmutant_claude/review/viewer/wmut_<t>.glb, images '<prefix>_wmut_<t>': the region ramps
baked with the engine rule), 1024 px. -> work/tex_<material>_<t>.png, work/tex_list.json {material: [files]}"""
import io, json, struct
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]; CV = HERE.parent / 'mm9_wingedmutant_claude' / 'review' / 'viewer'
out = {}
for t in 'abc':
    raw = (CV / f'wmut_{t}.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]
    for im in doc['images']:
        name = im.get('name', '')
        if not name.endswith(f'_wmut_{t}'):
            continue
        prefix = name[:-len(f'_wmut_{t}')]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
        img = Image.open(io.BytesIO(binary[o:o + v['byteLength']])).convert('RGB').resize((1024, 1024), Image.LANCZOS)
        f = f'tex_{prefix}_A_{t}.png'; img.save(HERE / 'work' / f); out.setdefault(f'{prefix}_A', []).append(f)
(HERE / 'work' / 'tex_list.json').write_text(json.dumps(out, indent=1)); print('TEX', {k: len(v) for k, v in out.items()})
