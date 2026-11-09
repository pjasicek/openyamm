#!/usr/bin/env python3
"""Review viewer models for the Noble bosses (browser only; the runtime GLBs keep the shared textures and ramps):
each boss's runtime export with its weapon merged on Weapon_R and the skin ramps baked into the base colour (three.js
does not apply openyamm_region_ramps); the Hierarch also as the faltering variant (cable glow off). Writes
review/viewer/*.glb and manifest.json (clip lengths from the GLBs). Usage: viewer_build.py [revision]"""
import hashlib, io, json, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
V = P / 'review/viewer'; E = P / 'export'
REV = sys.argv[1] if len(sys.argv) > 1 else 'nobles_20261024'
W3 = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def read(path):
    raw = Path(path).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4); doc['buffers'][0]['byteLength'] = len(binary)
    js = json.dumps(doc, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binary))
                           + struct.pack('<II', len(js), 0x4E4F534A) + js
                           + struct.pack('<II', len(binary), 0x004E4942) + binary)


def image(doc, binary, tex):
    v = doc['bufferViews'][doc['images'][doc['textures'][tex]['source']]['bufferView']]
    return Image.open(io.BytesIO(bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])))


def add_image(doc, binary, im, name, like):
    buf = io.BytesIO(); im.save(buf, 'PNG'); data = buf.getvalue()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary += data
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    doc['textures'].append(dict(doc['textures'][like], source=len(doc['images']) - 1))
    return len(doc['textures']) - 1


def bake(doc, binary):
    for m in doc['materials']:
        ex = m.get('extras', {})
        if 'openyamm_region_ramps' not in ex:
            continue
        ti = m['pbrMetallicRoughness']['baseColorTexture']['index']
        base = lin(np.asarray(image(doc, binary, ti).convert('RGB'), np.float32) / 255)
        mk = image(doc, binary, ex['openyamm_region_mask']['index']).convert('RGBA').resize(
            (base.shape[1], base.shape[0]), Image.BILINEAR)
        mask = np.asarray(mk, np.float32) / 255
        lum = base @ W3; out = base.copy()
        for c, reg in enumerate(ex['openyamm_region_ramps']):
            lo, hi = reg['range']; cols = np.array(reg['colors'], np.float32)
            x = np.clip((lum - lo) / (hi - lo), 0, 1) * (len(cols) - 1)
            i = np.minimum(x.astype(int), len(cols) - 2); f = (x - i)[..., None]
            ramp = cols[i] * (1 - f) + cols[i + 1] * f
            out = out * (1 - mask[..., c:c + 1]) + ramp * mask[..., c:c + 1]
        im = Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + 0.5).astype(np.uint8))
        m['pbrMetallicRoughness']['baseColorTexture']['index'] = add_image(doc, binary, im, m['name'] + '_viewer', ti)


def accessor_max(doc, binary, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return float(np.frombuffer(bytes(binary[off:off + a['count'] * 4]), np.float32).max())


models = [('vhorrax', 'Lord Vhorrax (10105/10106)', 'hes_vhorrax_courtesy', 1.4, None),
          ('coil_keeper', 'The Coil Keeper (10108)', 'hes_coil_spear', 1.3, None),
          ('conductor', 'The Conductor (10109)', 'hes_conductor_baton', 1.3, None),
          ('hierarch', 'The Hierarch (10120/10145)', None, 2.2, None),
          ('hierarch_dark', 'The Hierarch, faltering (10146)', None, 2.2, 'hierarch_dark'),
          ('hierarch_enthroned', 'The Hierarch, enthroned (10145)', 'hes_hierarch_throne', 2.2, None)]
V.mkdir(parents=True, exist_ok=True)
manifest = json.loads((V / 'manifest.json').read_text()) if (V / 'manifest.json').exists() else {}
entries = []; clips = {}
for mid, label, weapon, scale, variant in models:
    src = E / f'hes_{"hierarch" if mid.startswith("hierarch") else mid}.glb'
    tmp = P / 'work' / f'viewer_{mid}.glb'
    if weapon:
        subprocess.run(['python3', str(P / 'scripts/merge_attachment.py'), str(src), str(E / f'{weapon}.glb'),
                        'Throne' if 'throne' in weapon else 'Weapon_R', str(tmp)], check=True, capture_output=True)
    else:
        tmp.write_bytes(src.read_bytes())
    doc, binary = read(tmp)
    if variant:
        names = [m['name'] for m in doc['materials']]
        for mesh in doc['meshes']:
            for p in mesh['primitives']:
                for mp in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                    if 1 in mp['variants'] and names[mp['material']].endswith('_' + variant):
                        p['material'] = mp['material']
    bake(doc, binary)
    out = V / f'hes_{mid}.glb'; write(out, doc, binary)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    entry = {'id': mid, 'label': label, 'revision': REV, 'url': f'{out.name}?v={sha[:12]}', 'sha256': sha,
             'scale': scale, 'clips': {}}
    entries.append(entry)
    if mid == 'hierarch_enthroned':
        manifest_default = None
    for an in doc['animations']:
        dur = max(accessor_max(doc, binary, s['input']) for s in an['samplers'])
        role = an['name'].split('_', 1)[1]
        clips[an['name']] = {'label': role, 'duration': dur,
                             'mode': 'loop' if role in ('Flight', 'Dead', 'Seated') else 'once',
                             'provenance': ('Accepted Overseer clip on the shared winged body (hes_overseer_codex)'
                                            if role in ('Flight', 'AttackMelee', 'AttackRanged', 'Cast', 'Hit', 'Death', 'Dead')
                                            else 'Authored over the accepted clips (scripts/extra_clips.py)'), 'anchors': []}
        if mid != 'hierarch_enthroned' or role.startswith('Seated'):
            entry['clips'][an['name']] = clips[an['name']]
    print('VIEWER', out.name, round(out.stat().st_size / 1e6, 1), 'MB')
manifest.update({'revision': REV, 'model': entries[0]['url'].split('?')[0], 'default_clip': 'Noble_Flight',
                 'default_model': entries[0]['id'], 'models': entries, 'clips': clips,
                 'model_sha256': entries[0]['sha256']})
manifest.setdefault('feedback', 'feedback/user_feedback.json')
(V / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('MANIFEST', len(entries), 'models', sorted(clips))
