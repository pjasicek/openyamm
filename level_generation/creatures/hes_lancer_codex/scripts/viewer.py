"""Review-only colour baking; runtime files retain shared maps and region-mask ramps."""
import io, json, struct, copy
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
GLOW = {'lancer_a': (1., .42, .08), 'lancer_b': (1., .36, .06), 'lancer_c': (1., .86, .55), 'forgemaster': (1., .20, .015)}


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def acc(doc, binary, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    comp = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(bytes(binary[off:off + a['count'] * comp * np.dtype(dt).itemsize]), dt).reshape(a['count'], comp)


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def image_bytes(doc, binary, idx):
    v = doc['bufferViews'][doc['images'][idx]['bufferView']]
    return bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])


import hashlib
import os
import re
import shutil
import subprocess
import yaml

R = json.loads((ROOT / 'textures/lancer_ramps.json').read_text())
viewer = ROOT / 'review/viewer'
viewer.mkdir(parents=True, exist_ok=True)
(viewer / 'feedback').mkdir(exist_ok=True)
if not (viewer / 'feedback/user_feedback.json').exists():
    (viewer / 'feedback/user_feedback.json').write_text('{"findings": []}\n')
house = ROOT.parent / 'hes_kreegan_claude/review/viewer'
html = (house / 'index.html').read_text()
html = re.sub(r'<title>.*?</title>', '<title>Hesper Lancers and Forgemaster review</title>', html)
html = re.sub(r'<header>.*?</header>', '<header><h1>Hesper Lancers and the Forgemaster</h1>'
              '<p>Concept comparison and every-clip review for Lancers A–C and the Forgemaster. '
              'Revised armour, ready carries, glowing weapons and fitted maul clips.</p>'
              '<p>Approved concepts: <a href="../../../../../design/kreegan_world/concepts/monsters/fam_lancers.png">'
              'Lancers</a> · <a href="../../../../../design/kreegan_world/concepts/monsters/boss_forgemaster.png">'
              'Forgemaster</a></p></header>', html)
html = html.replace('Tiers share geometry, rig and clips.', 'The Lancers share a body; the Forgemaster has its own maul clips.')
(viewer / 'index.html').write_text(html)
js = (house / 'review.js').read_text()
js = js.replace('openyamm:mm6-natm-claude:notes','openyamm:hes-lancer-codex:notes')
js = js.replace('MM7 Blaster Guy','Hesper Lancers and Forgemaster').replace('hesper:kreegan','hesper:lancer')
js = js.replace('hes_kreegan_claude_frame_feedback.json','hes_lancer_codex_frame_feedback.json')
js = js.replace('const [x,y,z,distance] = focuses[focus] || focuses.body;',
                "const [x,y,z,distance] = (focuses[focus] || focuses.body).map(v=>v*(selectedModel?.id==='forgemaster'?1.5:1));")
old = '  for(const [name,c] of Object.entries(manifest.clips)){'
assert old in js
js = js.replace(old, '  const clips=info.clips;\n  for(const [name,c] of Object.entries(clips)){', 1)
old = "  selectedModel=info;$('modelRevision').value=id;"
assert old in js
js = js.replace(old, "  manifest.clips=clips;$('clip').replaceChildren();\n"
                    "  for(const [name,c] of Object.entries(clips))$('clip').add(new Option(c.label,name));\n" + old)
js = js.replace('selectClip(pose?.clip||manifest.default_clip);',
                'selectClip(clips[pose?.clip]?pose.clip:manifest.default_clip);')
(viewer / 'review.js').write_text(js)
manifest = {'revision': 'hes_forgemaster_strike_20261024', 'default_model': 'lancer_a', 'default_clip': 'Standing',
            'feedback': 'feedback/user_feedback.json', 'models': []}
ready_variants={a['skin'] for a in yaml.safe_load((ROOT/'integration/actors.yml').read_text())}
for variant in R['variants']:
    if variant not in ready_variants:
        continue
    forge = variant == 'forgemaster'
    name = 'hes_forgemaster' if forge else 'hes_lancer_twin' if variant == 'lancer_b' else 'hes_lancer'
    source = ROOT / f'export/{name}_lod0.glb'
    dropped = ROOT / f'work/viewer_{variant}_dropped.glb'
    family = 'Forge' if forge else 'Carbine'
    weapon = 'hes_thunder_maul' if forge else 'hes_ion_lance_twin'
    if forge:
        subprocess.run(['python3', str(ROOT/'scripts/forge_floor.py'), str(source), str(dropped),
                        str(ROOT/'review/forge_floor_viewer.json')], check=True)
    else:
        subprocess.run(['python3', str(ROOT / 'scripts/death_carbine_floor.py'), str(source), str(dropped),
                        str(ROOT / f'export/{weapon}.glb')], check=True,
                       env={**os.environ, 'WEAPON': 'Thunder_Maul' if forge else 'Rifle',
                            'DEATH': family+'_Death', 'DEAD': family+'_Dead'})
    doc, binary = read_glb(dropped)
    for mat in doc['materials']:
        mat_name = mat['name'].split('.')[0]
        ramps = json.loads((ROOT / 'textures/forge_ramps.json').read_text()) if forge else R
        entry = next((m for m in ramps['materials'] if m['base'] == mat_name), None)
        if entry:
            ti = mat['pbrMetallicRoughness']['baseColorTexture']['index']
            img = Image.open(io.BytesIO(image_bytes(doc, binary, doc['textures'][ti]['source']))).convert('RGBA')
            base = lin(np.asarray(img, np.float32)[..., :3] / 255)
            mk = Image.open(ROOT / 'textures' / entry['mask']).convert('RGBA')
            mask = np.stack([np.asarray(ch.resize(img.size, Image.Resampling.BILINEAR), np.float32)/255
                             for ch in mk.split()], -1)
            lum, out = base @ W, base.copy()
            for c, region in enumerate(entry['ramps'][variant]):
                lo, hi = region['range']
                out = out*(1-mask[..., c:c+1])+ramp(region['colors'], (lum-lo)/(hi-lo))*mask[..., c:c+1]
            im = Image.fromarray((np.clip(srgb(out), 0, 1)*255+.5).astype(np.uint8))
            buf = io.BytesIO()
            im.save(buf, 'PNG')
            binary += b'\0'*(-len(binary)%4)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
            binary += buf.getvalue()
            doc['images'].append({'bufferView': len(doc['bufferViews'])-1, 'mimeType': 'image/png'})
            doc['textures'].append(dict(doc['textures'][ti], source=len(doc['images'])-1))
            mat['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures'])-1
        if mat_name == 'HKR_Glow':
            mat['emissiveFactor'] = list(GLOW[variant])
            mat['pbrMetallicRoughness']['baseColorFactor'] = ([0.08,0.008,0.001,1] if forge else [*GLOW[variant], 1])
        if mat_name == 'HKR_Plate' and variant == 'lancer_c':
            mat['pbrMetallicRoughness']['metallicFactor'] = .85
    if variant in ('lancer_a', 'lancer_b'):
        joint = doc['skins'][0]['joints'].index(next(i for i,n in enumerate(doc['nodes']) if n.get('name') == 'Ancient_Graft'))
        for mesh in doc['meshes']:
            for primitive in mesh['primitives']:
                js_ = acc(doc, binary, primitive['attributes']['JOINTS_0'])
                weights = acc(doc, binary, primitive['attributes']['WEIGHTS_0'])
                on = ((js_ == joint) & (weights > .999)).any(1)
                indices = acc(doc, binary, primitive['indices']).reshape(-1, 3)
                keep = ~on[indices].all(1)
                if keep.all():
                    continue
                new = indices[keep].astype(np.uint32).ravel()
                binary += b'\0'*(-len(binary)%4)
                doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': new.nbytes, 'target': 34963})
                binary += new.tobytes()
                doc['accessors'].append({'bufferView': len(doc['bufferViews'])-1, 'componentType': 5125,
                                         'count': int(new.size), 'type': 'SCALAR'})
                primitive['indices'] = len(doc['accessors'])-1
            mesh['primitives'] = [p for p in mesh['primitives'] if doc['accessors'][p['indices']]['count']]
    aliases = {family+'_'+role: role for role in ('Standing','Walking','Attack','Hit','Fidget','Death','Dead')}
    aliases['Forge_Running' if forge else 'Lancer_Running'] = 'Running'
    if forge:
        aliases['Forge_Cast'] = 'Cast'
        for root in doc['scenes'][doc.get('scene', 0)]['nodes']:
            doc['nodes'][root]['scale'] = [1.5*x for x in doc['nodes'][root].get('scale', [1,1,1])]
    doc['animations'] = [a for a in doc['animations'] if a['name'] in aliases]
    clips = {}
    for animation in doc['animations']:
        original = animation['name']
        animation['name'] = aliases[original]
        duration = max(float(acc(doc, binary, s['input']).max()) for s in animation['samplers'])
        role = animation['name']
        clips[role] = {'label': role, 'duration': duration,
                       'mode': 'loop' if role in ('Standing','Walking','Running','Dead') else 'once',
                       'provenance': 'Mixamo Standard Run, fitted demon stance and carry' if role == 'Running' else
                                     'RPG 2HandAxeAttack1 windup; fitted ground slam, 3.5 s / impact 1.75 s' if forge and role == 'Attack' else 'Fitted 2Hand Axe library / shared Demon clips' if forge else 'Shared Kreegan '+original,
                       'anchors': []}
    target = viewer / f'{variant}.glb'
    write_glb(target, doc, binary)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    label = {'lancer_a':'Lancer A — single ion lance', 'lancer_b':'Lancer B — twin ion lance',
             'lancer_c':'Lancer C — gilded shell and Ancient graft', 'forgemaster':'Forgemaster — thunder maul, hull apron, ×1.5'}[variant]
    manifest['models'].append({'id': variant, 'label': label, 'revision': manifest['revision'],
                               'url': target.name+'?v='+digest[:12], 'sha256': digest, 'clips': clips})
    print('VIEWER', variant, len(clips), 'clips', flush=True)
manifest['clips'] = manifest['models'][0]['clips'].copy()
if 'Cast' in manifest['models'][-1]['clips']:
    manifest['clips']['Cast'] = manifest['models'][-1]['clips']['Cast']
manifest['model'] = 'lancer_a.glb'
manifest['model_sha256'] = manifest['models'][0]['sha256']
(viewer / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


