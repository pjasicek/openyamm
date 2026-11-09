#!/usr/bin/env python3
"""Review viewer: installed vs reduced for each tier (Charger / Juggernaut / Demolisher), both with every part the game
draws (body, rubble, eyes, palm flash; body/rubble visibility from the collapsed-mesh scale keys). Reuses the creature's
own viewer (mm8_m608_codex/review/viewer) and its preview rule: copies that bake the runtime region ramps for Three.js
(never installed). Usage: viewer_build.py"""
import copy, hashlib, io, json, re, sys
from pathlib import Path
import numpy as np
from PIL import Image
P = Path(__file__).resolve().parents[1]; C = P.parent / 'mm8_m608_codex'; V = P / 'review/viewer'
(V / 'feedback').mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(P.parents[2] / 'tools'), str(P.parent / 'claude_shared')]
from build_actor_lods import read_glb, write_glb  # noqa: E402
from region_variants import srgb_to_linear  # noqa: E402
for name in ('index.html', 'review.js'):
    s = (C / 'review/viewer' / name).read_text()
    s = s.replace('openyamm:mm6-cle-claude:notes', 'openyamm:mm8-m608-reduce-claude:notes').replace('mm8_m608_codex_frame_feedback', 'mm8_m608_reduce_frame_feedback')
    if name == 'index.html':
        s = re.sub(r'<title>.*?</title>', '<title>MM8 Juggernaut reduction</title>', s)
        s = re.sub(r'<header>.*?</header>', '<header><h1>MM8 Juggernaut: installed vs reduced</h1><p>Same textures, tiers and clips; body 6,221 &rarr; 5,123 and rubble 2,854 &rarr; 2,282 triangles. Eyes and palm flash unchanged. The rubble replaces the body at 0.25 s of Death.</p></header>', s, flags=re.S)
    (V / name).write_text(s)
fb = V / 'feedback/user_feedback.json'
if not fb.exists():
    fb.write_text('{"findings": []}\n')
def image(d, b, index):
    im = d['images'][d['textures'][index]['source']]; v = d['bufferViews'][im['bufferView']]
    return Image.open(io.BytesIO(b[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]))
def preview(source, variant, out):
    original, raw = read_glb(source); d = copy.deepcopy(original); b = bytearray(raw); used = set()
    for mesh in d['meshes']:
        for p in mesh['primitives']:
            for mapping in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if variant in mapping['variants']:
                    p['material'] = mapping['material']
            used.add(p['material'])
    cache = {}
    for index in used:
        mat = d['materials'][index]; ex = mat.get('extras', {}); mask = ex.get('openyamm_region_mask'); ramps = ex.get('openyamm_region_ramps')
        if not mask or not ramps:
            continue
        tex = mat['pbrMetallicRoughness']['baseColorTexture']['index']; key = (tex, mask['index'], json.dumps(ramps))
        if key not in cache:
            base = image(d, b, tex).convert('RGB'); a = np.array(base, dtype=float) / 255; linear = srgb_to_linear(a)
            lum = linear @ np.array([.2126, .7152, .0722])
            weights = np.array(image(d, b, mask['index']).convert('RGBA').resize(base.size, Image.Resampling.BILINEAR), dtype=float) / 255
            for c, r in enumerate(ramps):
                t = np.clip((lum - r['range'][0]) / (r['range'][1] - r['range'][0]), 0, 1) * 15; lo = np.minimum(t.astype(int), 14); f = t - lo
                colors = np.array(r['colors']); target = colors[lo] * (1 - f[..., None]) + colors[lo + 1] * f[..., None]; w = weights[:, :, c, None]
                linear = linear * (1 - w) + target * w
            srgb = np.where(linear <= .0031308, linear * 12.92, 1.055 * np.maximum(linear, 0) ** (1 / 2.4) - .055)
            buf = io.BytesIO(); Image.fromarray(np.round(np.clip(srgb, 0, 1) * 255).astype('uint8')).save(buf, format='PNG'); payload = buf.getvalue()
            b.extend(b'\0' * (-len(b) % 4)); d['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(payload)}); b.extend(payload)
            d['images'].append({'bufferView': len(d['bufferViews']) - 1, 'mimeType': 'image/png'}); d['textures'].append({'source': len(d['images']) - 1, 'sampler': 0})
            cache[key] = len(d['textures']) - 1
        mat['pbrMetallicRoughness']['baseColorTexture']['index'] = cache[key]
    write_glb(out, d, b); return hashlib.sha256(out.read_bytes()).hexdigest()
models = []
for label, src, tris in (('installed', P / 'work/mm8_m608_source_pre_reduce.glb', '9,319'), ('reduced', P / 'export/mm8_m608.glb', '7,649')):
    for variant, (tier, name) in enumerate(zip('abc', ['Charger', 'Juggernaut', 'Demolisher'])):
        out = V / f'm608_{tier}_{label}.glb'; sha = preview(src, variant, out)
        models.append({'id': f'{tier}_{label}', 'label': f'{name} {label} ({tris} tris)', 'scale': 1, 'revision': f'mm8_m608_reduce_{label}',
                       'url': out.name + '?v=' + sha[:10], 'sha256': sha, 'runtime_source_sha256': hashlib.sha256(src.read_bytes()).hexdigest()})
base = json.loads((C / 'review/viewer/manifest.json').read_text())
manifest = {'revision': 'mm8_m608_reduce_r82', 'model': models[1]['url'], 'default_clip': 'Standing', 'default_model': 'a_reduced',
            'feedback': 'feedback/user_feedback.json', 'models': models, 'clips': base['clips']}
manifest['models'] = [m for t in 'abc' for m in models if m['id'].startswith(t)]
(V / 'manifest.json').write_text(json.dumps(manifest, indent=2)); print('VIEWER', V, len(models), 'models')
