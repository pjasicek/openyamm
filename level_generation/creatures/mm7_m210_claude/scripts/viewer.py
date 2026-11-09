"""Review viewer for the batch-M export: review/viewer/{index.html, review.js, manifest.json, <tier>.glb}.

three.js has neither KHR_materials_variants selection nor region ramps, so each variant gets its own viewer GLB in
which every primitive takes its variant material and the region ramps are baked into the base colour with the engine
rule (t = linear luminance over the region range, colour = mix(colour, ramp(t), mask channel)); base-colour alpha is
kept. A model without variants (one palette for every tier) is shown as is. index.html and review.js are the
mm7_m390_claude viewer's, with this creature's title.
"""
import copy
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402

VIEWER = P / 'review/viewer'
TEMPLATE = P.parent / 'mm7_m390_claude/review/viewer'
LOOPS = {'Standing', 'Walking', 'Walk', 'Running', 'Fly', 'Fidget'}
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def image(doc, binary, texture):
    view = doc['bufferViews'][doc['images'][doc['textures'][texture]['source']]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[start:start + view['byteLength']])))


def ramp(colors, t):
    c = np.array(colors, np.float32)
    x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2)
    f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def bake(source, variant_index, variant):
    doc, base_binary = RV.read_glb(source)
    binary = bytearray(base_binary)
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            extension = primitive.pop('extensions', {}).get('KHR_materials_variants')
            if extension:
                primitive['material'] = next(m['material'] for m in extension['mappings']
                                             if variant_index in m['variants'])
    doc.pop('extensions', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
    used = {p['material'] for m in doc['meshes'] for p in m['primitives'] if 'material' in p}
    for index, material in enumerate(doc['materials']):
        extras = material.get('extras', {})
        if 'openyamm_region_ramps' not in extras or index not in used:
            continue
        texture = material['pbrMetallicRoughness']['baseColorTexture']['index']
        rgba = np.asarray(image(doc, binary, texture).convert('RGBA'), np.float32) / 255
        base, alpha = lin(rgba[..., :3]), rgba[..., 3:4]
        # resize each mask channel on its own: an RGBA resize premultiplies alpha
        mask4 = np.asarray(image(doc, binary, extras['openyamm_region_mask']['index']).convert('RGBA'))
        mask = np.stack([np.asarray(Image.fromarray(mask4[..., k]).resize(base.shape[1::-1], Image.BILINEAR))
                         for k in range(4)], -1).astype(np.float32) / 255
        lum = base @ RV.LUMA.astype(np.float32)
        out = base.copy()
        for channel, region in enumerate(extras['openyamm_region_ramps']):
            lo, hi = region['range']
            weight = mask[..., channel:channel + 1]
            out = out * (1 - weight) + ramp(region['colors'], (lum - lo) / (hi - lo)) * weight
        encoded = io.BytesIO()
        Image.fromarray((np.concatenate([np.clip(srgb(out), 0, 1), alpha], -1) * 255 + .5).astype(np.uint8)).save(
            encoded, 'PNG')
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(encoded.getvalue())})
        binary.extend(encoded.getvalue())
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                              'name': f'{variant}_baked'})
        sampler = doc['textures'][texture].get('sampler')
        doc['textures'].append({'source': len(doc['images']) - 1, **({'sampler': sampler} if sampler is not None else {})})
        material['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    out = VIEWER / f'{source.stem}_{variant}.glb'
    RV.write_glb(out, doc, bytes(binary))
    return out


def clips(path):
    doc, binary = RV.read_glb(path)
    result = {}
    for animation in doc.get('animations', []):
        duration = max(doc['accessors'][s['input']]['max'][0] for s in animation['samplers'])
        result[animation['name']] = {'label': animation['name'], 'duration': duration,
                                     'mode': 'loop' if animation['name'] in LOOPS else 'once',
                                     'provenance': CONFIG['viewer']['provenance'], 'anchors': []}
    return result


CONFIG = json.loads((P / 'scripts/project.json').read_text())


def patched_review_js():
    """The Roc viewer's camera focuses are fixed for the Roc's size; frame every focus from this model's posed bounds."""
    js = (TEMPLATE / 'review.js').read_text()
    old_focus = ("const focuses = {body:[0,0.13,0,1.8], head:[0,0.10,0.17,0.5], arms:[0,0.15,0,1.6], "
                 "shoulders:[0,0.13,0,1.0], skirt:[0,0.08,-0.14,0.6], feet:[0,0.04,-0.1,0.5]};")
    new_focus = ("let focuses = {body:[0,0.13,0,1.8], head:[0,0.10,0.17,0.5], arms:[0,0.15,0,1.6], "
                 "shoulders:[0,0.13,0,1.0], skirt:[0,0.08,-0.14,0.6], feet:[0,0.04,-0.1,0.5]};\n"
                 "let framed = false;\n"
                 "function frameModel(root) {\n"
                 "  root.updateMatrixWorld(true);\n"
                 "  let body = null; root.traverse(o => { if (o.isMesh && (!body || o.geometry.attributes.position.count "
                 "> body.geometry.attributes.position.count)) body = o; });\n"
                 "  const box = new THREE.Box3().setFromObject(body, true), size = box.getSize(new THREE.Vector3()), "
                 "c = box.getCenter(new THREE.Vector3());\n"
                 "  const h = Math.max(size.x, size.y, size.z), at = f => box.min.y + f * size.y;\n"
                 "  focuses = {body:[c.x,c.y,c.z,1.9*h], head:[c.x,at(.85),c.z,.6*h], arms:[c.x,at(.6),c.z,1.2*h], "
                 "shoulders:[c.x,at(.7),c.z,.9*h], skirt:[c.x,at(.4),c.z,.8*h], feet:[c.x,at(.12),c.z,.6*h]};\n"
                 "  controls.maxDistance = Math.max(12, 8*h); controls.minDistance = Math.min(0.15, 0.05*h);\n"
                 "}")
    # Frame the posed body (the default clip at time 0; a flyer's bind pose lies elsewhere), skinned vertices included.
    # Only the largest mesh counts: effect meshes (death cloud, burst) wait on bones parked far from the body.
    old_load = 'selectClip(pose?.clip||manifest.default_clip);'
    new_load = old_load + 'frameModel(model);if(!framed){framed=true;cameraView();}'
    title, stem = CONFIG['viewer']['title'], P.name
    for old, new in ((old_focus, new_focus), (old_load, new_load), ('MM7 Roc', title), ('mm6:natm', stem),
                     ('mm6_natm_claude', stem)):
        assert old in js, old
        js = js.replace(old, new)
    return js


def main():
    VIEWER.mkdir(parents=True, exist_ok=True)
    (VIEWER / 'feedback').mkdir(exist_ok=True)
    body = P / 'export' / CONFIG['build'][0]['out']
    doc, _ = RV.read_glb(body)
    variants = [v['name'] for v in doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
    labels = CONFIG['viewer']['labels']
    models = []
    if variants:
        for index, variant in enumerate(variants):
            out = bake(body, index, variant)
            models.append((variant, labels[index] if len(labels) == len(variants) else labels[0], out))
    else:
        out = VIEWER / f'{body.stem}_all.glb'
        shutil.copyfile(body, out)
        models.append(('all_tiers', labels[0], out))
    entries = []
    for model_id, label, path in models:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({'id': model_id, 'label': label, 'revision': CONFIG['viewer']['revision'],
                        'url': f'{path.name}?v={digest[:12]}', 'sha256': digest})
    clip_table = clips(body)
    for name, anchor in CONFIG['viewer'].get('anchors', {}).items():
        if name in clip_table:
            clip_table[name]['anchors'] = [{'time': 0, 'label': '0', 'phase': f'Native {anchor[0]}',
                                            'source_images': [f'../../references/{frame}.png' for frame in anchor]}]
    default_clip = CONFIG['viewer'].get('default_clip', 'Standing')
    manifest = {'revision': CONFIG['viewer']['revision'], 'default_model': entries[0]['id'],
                'default_clip': default_clip if default_clip in clip_table else next(iter(clip_table)),
                'model': entries[0]['url'].split('?')[0], 'feedback': 'feedback/user_feedback.json',
                'models': entries, 'model_sha256': entries[0]['sha256'], 'fps': 24, 'clips': clip_table}
    (VIEWER / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    feedback = VIEWER / 'feedback/user_feedback.json'
    if not feedback.exists():
        feedback.write_text('{"findings": []}\n')
    html = (TEMPLATE / 'index.html').read_text()
    html = html.replace('<title>MM7 Roc review</title>', f"<title>{CONFIG['viewer']['title']} review</title>")
    html = html.replace('<h1>MM7 Roc</h1><p>Roc, Greater Roc and Thunderbird · MM8 Thunderbird body with MM7 palette ramps.</p>',
                        f"<h1>{CONFIG['viewer']['title']}</h1><p>{CONFIG['viewer']['subtitle']}</p>")
    assert CONFIG['viewer']['title'] in html
    (VIEWER / 'index.html').write_text(html)
    (VIEWER / 'review.js').write_text(patched_review_js())
    print('viewer', [e['id'] for e in entries], list(clip_table))


if __name__ == '__main__':
    sys.exit(main())
