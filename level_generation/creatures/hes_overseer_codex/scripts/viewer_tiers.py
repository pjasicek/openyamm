#!/usr/bin/env python3
"""NOT READY: review-only baked colours and equipment selection on candidate LOD0.
Runtime candidates keep shared textures and ramps. Adapted from the shared Kreegan viewer builder.
"""
import io, json, struct, copy, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
GLOW = {v:((1,.84,.48) if v=='ov_c' else (1,.36,.045)) for v in ['ov_a','ov_b','ov_c','ov_krav','ov_ghulkat']}


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


R = json.load(open(ROOT / 'textures' / 'overseer_ramps.json'))
src = ROOT / 'work' / 'overseer_assembled_lod0.glb'
for variant in R['variants']:
    doc, binary = read_glb(src)
    names = [n.get('name') for n in doc['nodes']]
    joints = doc['skins'][0]['joints']
    dropped={'ov_a':['ArcMaul','HipSaber','CollarKey','HolsterPistol'],'ov_b':['ArcMaul','HipSaber','CollarKey','HolsterPistol'],'ov_c':['ArcMaul','HipSaber','CollarKey','HolsterPistol'],'ov_krav':['ArcMaul','CollarKey','HolsterPistol'],'ov_ghulkat':['CollarRod','HipSaber']}
    drop={joints.index(names.index(n)) for n in dropped[variant]}
    for mat in doc['materials']:
        name = mat['name'].split('.')[0]
        entry = next((m for m in R['materials'] if m['base'] == name), None)
        if entry is not None:
            ti = mat['pbrMetallicRoughness']['baseColorTexture']['index']
            img = Image.open(io.BytesIO(image_bytes(doc, binary, doc['textures'][ti]['source']))).convert('RGBA')
            rgba = np.asarray(img, np.float32) / 255; base = lin(rgba[..., :3])
            mk = Image.open(ROOT / 'textures' / entry['mask']).convert('RGBA')
            mask = np.stack([np.asarray(ch.resize(img.size, Image.BILINEAR), np.float32) / 255 for ch in mk.split()], -1)
            lum = base @ W; out = base.copy()
            for c, reg in enumerate(entry['ramps'][variant]):
                lo, hi = reg['range']
                out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
            im = Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + 0.5).astype(np.uint8))
            im.save(ROOT / 'work' / f'tier_{variant}_{name}.png')
            buf = io.BytesIO(); im.save(buf, 'PNG'); binary += b'\0' * (-len(binary) % 4)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary += buf.getvalue()
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{name}_{variant}'})
            doc['textures'].append(dict(doc['textures'][ti], source=len(doc['images']) - 1))
            mat['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures']) - 1
        if name.startswith('OV_Glow'):
            mat['emissiveFactor'] = list(GLOW[variant]); mat.setdefault('pbrMetallicRoughness', {})['baseColorFactor'] = [*GLOW[variant], 1.0]
    if True:
        for mesh in doc['meshes']:
            for p in mesh['primitives']:
                mname = doc['materials'][p['material']]['name']
                if not mname.startswith('OV_'):
                    continue
                J = acc(doc, binary, p['attributes']['JOINTS_0']); Wt = acc(doc, binary, p['attributes']['WEIGHTS_0']).astype(np.float32)
                if doc['accessors'][p['attributes']['WEIGHTS_0']].get('normalized'): Wt = Wt / 255.0
                on = np.zeros(len(J), bool)
                for c in drop: on |= ((J == c) & (Wt > 0.999)).any(1)
                idx = acc(doc, binary, p['indices']).reshape(-1, 3)
                keep = ~on[idx].all(1)
                if keep.all(): continue
                newi = idx[keep].astype(np.uint32).ravel()
                binary += b'\0' * (-len(binary) % 4)
                doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': newi.nbytes, 'target': 34963}); binary += newi.tobytes()
                doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5125, 'count': int(newi.size), 'type': 'SCALAR'})
                p['indices'] = len(doc['accessors']) - 1
    # Ghulkat carries his pistol on the existing hip socket; the Arc Maul stays in his right hand.
    if variant=='ov_ghulkat':
        from importlib.util import spec_from_file_location,module_from_spec
        spec=spec_from_file_location('glb_tools',ROOT.parents[2]/'tools/merge_head_material.py');gt=module_from_spec(spec);spec.loader.exec_module(gt)
        ib=gt.accessor_array(doc,binary,doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
        old=joints.index(names.index('PulsePistol'));new=joints.index(names.index('HolsterPistol'));M=np.linalg.inv(ib[new])@ib[old]
        for mesh in doc['meshes']:
            for prim in mesh['primitives']:
                J=acc(doc,binary,prim['attributes']['JOINTS_0']);Wt=acc(doc,binary,prim['attributes']['WEIGHTS_0']);mask=((J==old)&(Wt>.999)).any(1)
                if not mask.any():continue
                for key in ['POSITION','NORMAL','TANGENT','JOINTS_0']:
                    if key not in prim['attributes']:continue
                    ai=prim['attributes'][key];ar=gt.accessor_array(doc,binary,ai).copy()
                    if key=='POSITION':ar[mask]=ar[mask]@M[:3,:3].T+M[:3,3]
                    elif key=='JOINTS_0':ar[mask]=new
                    else:ar[mask,:3]=ar[mask,:3]@M[:3,:3].T
                    prim['attributes'][key]=gt.append_accessor(doc,binary,ar,doc['accessors'][ai],34962)
    out = ROOT / 'review' / 'viewer' / f'hes_overseer_{variant[3:]}.glb'
    for mesh in doc['meshes']:
        mesh['primitives']=[pr for pr in mesh['primitives'] if doc['accessors'][pr['indices']]['count']>0]
    assert len(doc['animations'])==7
    write_glb(out, doc, binary)
    print('VIEWER', out.name, round(out.stat().st_size / 1e6, 1), 'MB')

# Publish clip lengths and hashes with the models; stale lengths prevent the viewer from loading.
viewer = ROOT / 'review/viewer'
manifest = json.loads((viewer / 'manifest.json').read_text())
sources = json.loads((ROOT / 'work/action_sources.json').read_text())['clips']
probe = json.loads((ROOT / 'review/feedback_motion.json').read_text())
manifest['revision'] = 'overseers_tiercolours_20261024'
for model in manifest['models']:
    path = viewer / model['url'].split('?')[0]
    doc, binary = read_glb(path)
    assert set(a['name'] for a in doc['animations']) == set(manifest['clips'])
    model['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    model['url'] = path.name + '?v=' + model['sha256'][:12]
    model['revision'] = manifest['revision']
    for animation in doc['animations']:
        name = animation['name']
        duration = max(float(acc(doc, binary, s['input']).max()) for s in animation['samplers'])
        info = manifest['clips'][name]
        info['duration'] = duration
        source = sources[name]
        info['provenance'] = source['arm_source'] + '; ' + source['body_source'] + '. Shared LOD0 checks pass; visual review pending.'
manifest['model_sha256'] = manifest['models'][0]['sha256']
manifest['clips']['Overseer_Flight']['anchors'] = [
    {'time': 0, 'label': 'Pistol lowered', 'phase': 'Flight ready pose', 'source_images': ['../feedback_flight.png']}]
melee = probe['Overseer_AttackMelee']
manifest['clips']['Overseer_AttackMelee']['label'] = 'AttackMelee · overhead smash'
manifest['clips']['Overseer_AttackMelee']['anchors'] = [
    {'time': 0, 'label': 'Ready'},
    {'time': melee['windup_peak_s'], 'label': 'Overhead wind-up', 'phase': 'Peak staff height', 'source_images': ['../feedback_windup.png']},
    {'time': 41.5/48, 'label': 'Staff contact', 'phase': 'Peak target-directed strike speed', 'source_images': ['../feedback_strike.png']},
    {'time': melee['downstroke_peak_s'], 'label': 'Downstroke', 'phase': 'Peak downward head speed'},
    {'time': 1.05, 'label': 'Follow-through', 'source_images': ['../feedback_followthrough.png']},
    {'time': manifest['clips']['Overseer_AttackMelee']['duration'], 'label': 'Recover'}]
manifest['clips']['Overseer_AttackRanged']['label'] = 'AttackRanged · aim and fire'
manifest['clips']['Overseer_AttackRanged']['anchors'] = [
    {'time': 0, 'label': 'Low ready'},
    {'time': .35, 'label': 'Aim held', 'source_images': ['../feedback_ranged.png']},
    {'time': .45, 'label': 'Fire', 'source_images': ['../feedback_ranged.png']},
    {'time': .53, 'label': 'Muzzle recoil', 'source_images': ['../ranged_frames/13.png']},
    {'time': .73, 'label': 'Aim recovered', 'source_images': ['../ranged_frames/18.png']},
    {'time': manifest['clips']['Overseer_AttackRanged']['duration'], 'label': 'Low ready', 'source_images': ['../ranged_frames/30.png']}]
for info in manifest['clips'].values():
    for anchor in info['anchors']:
        anchor.setdefault('phase', 'Pose anchor; image shows concept appearance only')
        anchor.setdefault('source_images', ['../../references_hd/fam_overseers.png'])
        assert anchor['source_images'] and 0 <= anchor['time'] <= info['duration'] + 1e-5
(viewer / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

# Keep a portable playback and sampled pose strip beside the viewer evidence.
render=json.loads((ROOT/'review/ranged_render.json').read_text());assert render['assembly_sha256']==hashlib.sha256((ROOT/'work/overseer_assembly.blend').read_bytes()).hexdigest()
frames=[Image.open(p).convert('RGB') for p in sorted((ROOT/'review/ranged_frames').glob('*.png'))]
assert len(frames)==31
frames[0].save(ROOT/'review/ranged_motion.gif',save_all=True,append_images=frames[1:],duration=40,loop=0)
chosen=[0,6,11,13,18,24,30];sheet=Image.new('RGB',(7*300,300))
for i,n in enumerate(chosen):sheet.paste(frames[n].resize((300,300)),(i*300,0))
sheet.save(ROOT/'review/ranged_motion_sheet.png')
