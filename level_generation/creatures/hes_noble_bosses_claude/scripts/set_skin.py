#!/usr/bin/env python3
"""Select one of the winged body's five accepted skin variants for a boss and drop the rest: the chosen variant's
body/head materials become the primitives' own materials (renamed Noble_Body / Noble_Head), the
KHR_materials_variants mappings and unused materials are removed.

--skin RRGGBB gives the boss its own skin through the region ramps (no baked colours): the skin region's ramp (mask R)
of Noble_Body and Noble_Head keeps its luminance profile, scaled so the median skin texel lands on the colour; the
shell (<Boss>_Shell) gets a region mask of its own skin-painted texels (violet/plum hue, not the dark resin) and the
same kind of ramp, so the shell's skin patches match the body.

Usage: set_skin.py in.glb out.glb <A|B|C|KRAV|GHULKAT> [--skin RRGGBB] [--shell-mask out.png]"""
import argparse, io, json, struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('tier')
ap.add_argument('--skin'); ap.add_argument('--shell-mask')
ap.add_argument('--source', default=str(Path(__file__).resolve().parents[1] / 'source/hes_kreegan_winged.glb'))
a = ap.parse_args()


def read(path):
    raw = Path(path).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4); doc['buffers'][0]['byteLength'] = len(binary)
    js = json.dumps(doc, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binary))
                           + struct.pack('<II', len(js), 0x4E4F534A) + js
                           + struct.pack('<II', len(binary), 0x004E4942) + binary)


lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
W3 = np.array([0.2126, 0.7152, 0.0722])


def tex_image(doc, binary, tex):
    v = doc['bufferViews'][doc['images'][doc['textures'][tex]['source']]['bufferView']]
    return Image.open(io.BytesIO(bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])))


doc, binary = read(a.src); tier = a.tier
names = [m['name'] for m in doc['materials']]
want = {f'OV_Body_{tier}': 'Noble_Body', f'OV_Head_{tier}': 'Noble_Head'}
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        n = names[p['material']]
        if n.startswith('OV_Body_'):
            p['material'] = names.index(f'OV_Body_{tier}')
        elif n.startswith('OV_Head_'):
            p['material'] = names.index(f'OV_Head_{tier}')
        p.get('extensions', {}).pop('KHR_materials_variants', None)
        if 'extensions' in p and not p['extensions']:
            del p['extensions']
doc.get('extensions', {}).pop('KHR_materials_variants', None)
if 'extensions' in doc and not doc['extensions']:
    del doc['extensions']
for key in ('extensionsUsed', 'extensionsRequired'):
    if key in doc:
        doc[key] = [e for e in doc[key] if e != 'KHR_materials_variants']
        if not doc[key]:
            del doc[key]
used = sorted({p['material'] for m in doc['meshes'] for p in m['primitives']})
remap = {old: new for new, old in enumerate(used)}
doc['materials'] = [doc['materials'][i] for i in used]
for m in doc['materials']:
    m['name'] = want.get(m['name'], m['name'])
    m['doubleSided'] = True  # one culling mode: the shadow merge needs it; the wings need two sides
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        p['material'] = remap[p['material']]

# The Blender round trip drops material extras: with --skin, restore the tier's region mask, ramps and specular from
# the published winged body (the mask image copied into this file). Without it the body shows its accepted base
# colour (the Hierarch's concept plum).
sdoc, sbin = read(a.source)
smats = {m['name']: m for m in sdoc['materials']}
for m in doc['materials']:
    src_name = {'Noble_Body': f'OV_Body_{tier}', 'Noble_Head': f'OV_Head_{tier}'}.get(m['name'])
    if not src_name or not a.skin:
        continue
    ex = json.loads(json.dumps(smats[src_name]['extras']))
    v = sdoc['bufferViews'][sdoc['images'][sdoc['textures'][ex['openyamm_region_mask']['index']]['source']]['bufferView']]
    data = bytes(sbin[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary += data
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': m['name'] + '_region_mask'})
    doc['textures'].append({'source': len(doc['images']) - 1})
    ex['openyamm_region_mask'] = {'index': len(doc['textures']) - 1}
    m.setdefault('extras', {}).update(ex)

if a.skin:
    target = lin(np.array([int(a.skin[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0)

    def skin_ramp(lums, lo, hi, profile):
        """16 stops over [lo, hi]: the profile's luminance shape (stops' luminance), scaled so the median skin
        luminance maps to the target colour; clipped to 1."""
        prof = np.array(profile, float)
        pl = prof @ W3
        tm = float(np.clip((np.median(lums) - lo) / (hi - lo), 0, 1)) * (len(pl) - 1)
        i = min(int(tm), len(pl) - 2); f = tm - i
        ref = pl[i] * (1 - f) + pl[i + 1] * f
        cols = np.clip(target[None, :] * (pl[:, None] / max(ref, 1e-6)), 0, 1)
        return cols.tolist()

    report = {}
    for m in doc['materials']:
        if m['name'] not in ('Noble_Body', 'Noble_Head'):
            continue
        ex = m['extras']; reg = ex['openyamm_region_ramps'][0]
        base = lin(np.asarray(tex_image(doc, binary, m['pbrMetallicRoughness']['baseColorTexture']['index'])
                              .convert('RGB'), float) / 255)
        mask = np.asarray(tex_image(doc, binary, ex['openyamm_region_mask']['index']).convert('RGBA')
                          .resize((base.shape[1], base.shape[0])), float) / 255
        lums = (base @ W3)[mask[..., 0] > 0.5]
        lo, hi = reg['range']
        reg['colors'] = skin_ramp(lums, lo, hi, reg['colors'])
        report[m['name']] = round(float(np.median(lums)), 4)
    shell = next((m for m in doc['materials'] if m['name'].endswith('_Shell')), None)
    if shell is not None:
        img = tex_image(doc, binary, shell['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB')
        rgb = np.asarray(img, float) / 255
        mx = rgb.max(-1); mn = rgb.min(-1); d_ = np.maximum(mx - mn, 1e-6); sat = (mx - mn) / np.maximum(mx, 1e-6)
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        hue = np.where(mx == r, ((g - b) / d_) % 6, np.where(mx == g, (b - r) / d_ + 2, (r - g) / d_ + 4)) * 60
        skin = (((hue >= 285) | (hue <= 10)) & (sat > 0.22) & (mx > 0.10) & (mx < 0.9)).astype(np.uint8) * 255
        m_img = Image.fromarray(skin).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
        mask_rgba = Image.merge('RGBA', (m_img, Image.new('L', m_img.size, 0), Image.new('L', m_img.size, 0),
                                         Image.new('L', m_img.size, 0)))
        if a.shell_mask:
            mask_rgba.save(a.shell_mask)
        buf = io.BytesIO(); mask_rgba.save(buf, 'PNG'); data = buf.getvalue()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary += data
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                              'name': shell['name'] + '_region_mask'})
        doc['textures'].append({'source': len(doc['images']) - 1})
        lums = (lin(rgb) @ W3)[np.asarray(m_img) > 128]
        lo, hi = float(np.percentile(lums, 1)), float(np.percentile(lums, 99))
        body = next(m for m in doc['materials'] if m['name'] == 'Noble_Body')
        profile = body['extras']['openyamm_region_ramps'][0]['colors']
        shell.setdefault('extras', {})['openyamm_region_mask'] = {'index': len(doc['textures']) - 1}
        shell['extras']['openyamm_region_ramps'] = [{'range': [lo, hi], 'colors': skin_ramp(lums, lo, hi, profile)}]
        report['shell_skin_fraction'] = round(float((np.asarray(m_img) > 128).mean()), 4)
    print('SKIN', a.skin, report)
write(a.dst, doc, binary)
print('SKIN', tier, [m['name'] for m in doc['materials']])
