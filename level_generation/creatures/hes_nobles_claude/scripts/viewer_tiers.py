#!/usr/bin/env python3
"""Review-viewer GLBs (three.js has no region ramps or per-descriptor attachments), one per row, baked from
export/hes_noble_lod0.glb (body, carapace and every weapon in one mesh, before the split):
- the row's ramps (textures/nb_ramps.json) baked into NB_Body / NB_Head / NB_Plate base colour with the engine rule
  (per region: t = linear luminance over the range, colour = mix(colour, ramp(t), mask channel));
- the carapace glow's emissive colour per row (glow_variants.py's colours), the weapons' glow orange;
- only the row's own weapons and gear (the triangles of every other NB_Weapon*/NB_WeaponGlow* material dropped);
- every clip kept (the viewer lists one clip set for all models; each row uses its prefix).
Writes review/viewer/<row>.glb and review/viewer/manifest.json. Args: none"""
import io, json, struct, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
ROWS = [  # id, label, variant, prefix, weapon material stems
    ('noble_a', 'Noble A (10040): jade skin, antique gold, the fang and sidearm', 'nb_a', 'Noble', ['noble_fang', 'noble_sidearm']),
    ('noble_b', 'Noble Duellist B (10041, x1.05): garnet, bronze gold', 'nb_b', 'Noble', ['noble_fang', 'noble_sidearm']),
    ('noble_c', 'Court Noble C (10042, x1.1): midnight sapphire, pale gold', 'nb_c', 'Noble', ['noble_fang', 'noble_sidearm']),
    ('ssekh', 'Lady Ssekh (10113, x1.15): rose tourmaline, twin crescent fangs', 'nb_ssekh', 'Ssekh', ['ssekh_fang']),
    ('mraal', 'Lord Mraal (10114, x1.15, grounded): obsidian iron, phase cleaver', 'nb_mraal', 'Mraal', ['phase_cleaver']),
    ('xith', 'Lord Xith (10115, x1.15): amethyst, storm caster', 'nb_xith', 'Xith', ['storm_rifle']),
    ('gatekeeper', 'The Gatekeeper (10112, x1.2): steel turquoise, carbine, emitter, gorget', 'nb_gatekeeper', 'Gate',
     ['lancer_carbine', 'bastion_emitter', 'gorget_seal']),
]
GLOW = {'nb_a': (1.0, 0.50, 0.12), 'nb_b': (1.0, 0.36, 0.06)}


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def image_bytes(doc, binary, idx):
    v = doc['bufferViews'][doc['images'][idx]['bufferView']]
    return bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])


R = json.load(open(ROOT / 'textures' / 'nb_ramps.json'))
src = ROOT / 'export' / 'hes_noble_lod0.glb'
out_dir = ROOT / 'review' / 'viewer'; out_dir.mkdir(parents=True, exist_ok=True)
models = []
for rid, label, variant, prefix, stems in ROWS:
    doc, binary = read_glb(src)
    for mat in doc['materials']:
        name = mat['name'].split('.')[0]
        entry = next((m for m in R['materials'] if m['base'] == name), None)
        if entry is not None:
            ti = mat['pbrMetallicRoughness']['baseColorTexture']['index']
            img = Image.open(io.BytesIO(image_bytes(doc, binary, doc['textures'][ti]['source']))).convert('RGBA')
            base = lin(np.asarray(img, np.float32)[..., :3] / 255)
            mk = Image.open(ROOT / 'textures' / entry['mask']).convert('RGBA')
            mask = np.stack([np.asarray(ch.resize(img.size, Image.BILINEAR), np.float32) / 255 for ch in mk.split()], -1)
            lum = base @ W; out = base.copy()
            for c, reg in enumerate(entry['ramps'][variant]):
                lo, hi = reg['range']
                out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
            im = Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + 0.5).astype(np.uint8))
            buf = io.BytesIO(); im.save(buf, 'PNG'); binary += b'\0' * (-len(binary) % 4)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary += buf.getvalue()
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{name}_{variant}'})
            doc['textures'].append(dict(doc['textures'][ti], source=len(doc['images']) - 1))
            mat['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures']) - 1
        if name == 'NB_Glow':
            g = GLOW.get(variant, (1.0, 0.86, 0.55))
            mat['emissiveFactor'] = list(g); mat.setdefault('pbrMetallicRoughness', {})['baseColorFactor'] = [*g, 1.0]
        if name.startswith('NB_WeaponGlow'):
            mat['emissiveFactor'] = [1.0, 0.45, 0.1]
    keep_mat = lambda n: not n.startswith(('NB_Weapon_', 'NB_WeaponGlow_')) or any(s in n for s in stems)
    for mesh in doc['meshes']:
        mesh['primitives'] = [p for p in mesh['primitives'] if keep_mat(doc['materials'][p['material']]['name'])]
    path = out_dir / f'{rid}.glb'; write_glb(path, doc, binary)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    models.append({'id': rid, 'label': label, 'revision': 'hes_nobles_claude_v1', 'url': f'{rid}.glb?v={sha[:12]}', 'sha256': sha})
    print('VIEWER', path.name, round(path.stat().st_size / 1e6, 1), 'MB')
doc, _ = read_glb(src)
info = json.load(open(ROOT / 'work' / 'clips_noble.json'))
clips = {}
for s in ('noble', 'ssekh', 'mraal', 'xith', 'gate'):
    for name, c in json.load(open(ROOT / 'work' / f'clips_{s}.json')).items():
        loop = name.endswith(('_Flight', '_Standing', '_Walking', '_Running'))
        clips[name] = {'label': name, 'duration': c['seconds'], 'mode': 'loop' if loop else 'once',
                       'provenance': ', '.join(c['sources']) + ' over ' + c['base'],
                       'anchors': [{'time': 0.0, 'label': name, 'phase': ', '.join(c['sources']),
                                    'source_images': ['../../references_hd/weapons/fam_nobles.png']}]}
manifest = {'revision': 'hes_nobles_claude_v1', 'model': models[0]['url'].split('?')[0], 'default_clip': 'Noble_Flight',
            'feedback': 'feedback/user_feedback.json', 'default_model': 'noble_a', 'model_sha256': models[0]['sha256'],
            'models': models, 'clips': clips}
(out_dir / 'manifest.json').write_text(json.dumps(manifest, indent=1))
fb = out_dir / 'feedback'; fb.mkdir(exist_ok=True)
if not (fb / 'user_feedback.json').exists(): (fb / 'user_feedback.json').write_text('{"findings": []}\n')
print('MANIFEST', len(models), 'models', len(clips), 'clips')
