#!/usr/bin/env python3
"""Before/after review viewer for an anim-stream fix (MM6-MM8 audit fixes, 2026-11-11).

    anim_viewer.py --project <P> --name "<creature>" --before <installed before.glb> --after <after.glb>
                   [--world mm7 --stem mm7_m430]   # adds the binding's attachments (dagger, sword) from actors.yml

Writes <P>/review/viewer/: per colour variant one GLB per revision with the variant's materials picked and the region
ramps baked into the base colour (three.js has neither KHR_materials_variants nor region ramps; same rule as
mm8_m480_texpass_claude/scripts/viewer_variants.py), the attachments, manifest.json (every clip of the after GLB) and
copies of the texture-pass viewer's index.html and review.js, with camera focuses scaled to the creature's height and
attachments parented to their node. Then: python3 tools/run_creature_review.py --project <P> check
"""
import argparse
import copy
import hashlib
import io
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
import glb_pose  # noqa: E402

TEMPLATE = ROOT / 'level_generation/creatures/mm8_m480_texpass_claude/review/viewer'
LOOPING = re.compile(r'^(standing|walking|walk\d*|running|run\d*|jog|sprint|fly|flying|hover|swim|idle)$', re.I)
W = np.array([0.2126, 0.7152, 0.0722], np.float32)


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def image(doc, binary, tex):
    v = doc['bufferViews'][doc['images'][doc['textures'][tex]['source']]['bufferView']]
    s = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[s:s + v['byteLength']])))


def ramp(colors, t):
    c = np.array(colors, np.float32)
    x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2)
    f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def bake(base_rgb, mask_img, ramps):
    base = lin(np.asarray(base_rgb, np.float32) / 255)
    m4 = np.asarray(mask_img.convert('RGBA'))
    mask = np.stack([np.asarray(Image.fromarray(m4[..., k]).resize(base.shape[1::-1], Image.Resampling.BILINEAR))
                     for k in range(4)], -1).astype(np.float32) / 255
    lum = base @ W
    out = base.copy()
    for c, reg in enumerate(ramps):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    return (np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)


def variant_glbs(src, tag, out_dir):
    """Writes <variant>_<tag>.glb per variant (or <stem>_<tag>.glb without variants); returns [(variant, path)]."""
    base_doc, base_bin = read_glb(Path(src))
    names = [v['name'] for v in base_doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
    written = []
    for vi, variant in enumerate(names or [None]):
        doc = copy.deepcopy(base_doc)
        binary = bytearray(base_bin)
        if variant is not None:
            for m in doc['meshes']:
                for p in m['primitives']:
                    ext = p.pop('extensions', {}).get('KHR_materials_variants')
                    if ext:
                        hit = [x['material'] for x in ext['mappings'] if vi in x['variants']]
                        if hit:
                            p['material'] = hit[0]
            doc.get('extensions', {}).pop('KHR_materials_variants', None)
            if not doc.get('extensions'):
                doc.pop('extensions', None)
            doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
        for mi, mat in enumerate(doc.get('materials', [])):
            extras = mat.get('extras', {})
            used = any(p.get('material') == mi for m in doc['meshes'] for p in m['primitives'])
            if 'openyamm_region_ramps' not in extras or not used:
                continue
            tex = mat['pbrMetallicRoughness']['baseColorTexture']['index']
            out = bake(image(doc, binary, tex).convert('RGB'), image(doc, binary, extras['openyamm_region_mask']['index']),
                       extras['openyamm_region_ramps'])
            buf = io.BytesIO()
            Image.fromarray(out).save(buf, 'PNG')
            binary.extend(b'\0' * (-len(binary) % 4))
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
            binary.extend(buf.getvalue())
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                                  'name': f'{variant}_baked'})
            sampler = {'sampler': doc['textures'][tex]['sampler']} if 'sampler' in doc['textures'][tex] else {}
            doc['textures'].append({'source': len(doc['images']) - 1, **sampler})
            mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        label = variant or Path(src).stem
        path = out_dir / f'{label}_{tag}.glb'
        write_glb(path, doc, bytes(binary))
        written.append((label, path))
    return written


def standing_height(path):
    model = glb_pose.Model(glb_pose.Glb(path))
    clip = next((c for c in model.clips if c.lower() == 'standing'), None)
    if clip is None:
        return 1.8
    posed = model.skinned_positions(model.world(model.sample(clip, model.clip_times(clip)[0])))
    points = np.concatenate([p for p, _ in posed])
    return float(points[:, 1].max() - min(0.0, points[:, 1].min()))


def attachments(world, stem):
    if not world:
        return []
    data = yaml.safe_load((ROOT / f'assets_dev/worlds/{world}/models/actors.yml').read_text())
    entries = data if isinstance(data, list) else data.get('actors', [])
    for entry in entries:
        if isinstance(entry, dict) and Path(entry.get('model', '')).stem == stem:
            return [(ROOT / 'assets_source' / a['model'], a['node']) for a in entry.get('attachments', [])]
    return []


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--project', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--before', required=True)
    p.add_argument('--after', required=True)
    p.add_argument('--world')
    p.add_argument('--stem')
    args = p.parse_args()
    project = Path(args.project).resolve()
    out = project / 'review/viewer'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'feedback').mkdir(exist_ok=True)
    if not (out / 'feedback/user_feedback.json').exists():
        (out / 'feedback/user_feedback.json').write_text('{"findings": []}\n')
    models = []
    for tag, src in (('before', args.before), ('after', args.after)):
        for variant, path in variant_glbs(src, tag, out):
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            models.append({'id': f'{variant}_{tag}', 'label': f'{variant} · {"installed before" if tag == "before" else "anim fix"}',
                           'url': f'{path.name}?v={h[:12]}', 'sha256': h, 'revision': f'animfix-{tag}'})
    models.sort(key=lambda m: m['id'])
    attach = []
    for src, node in attachments(args.world, args.stem):
        if src.exists():
            shutil.copyfile(src, out / src.name)
            attach.append({'url': src.name, 'node': node})
    model = glb_pose.Model(glb_pose.Glb(args.after))
    clips = {}
    for name in model.clips:
        times = model.clip_times(name)
        clips[name] = {'label': name, 'duration': float(np.float32(times[-1])),
                       'mode': 'loop' if LOOPING.match(name) else 'once', 'provenance': '', 'anchors': []}
    default = next(m['id'] for m in models if m['id'].endswith('_after'))
    pick = next(m for m in models if m['id'] == default)
    manifest = {'revision': 'animfix-20261111', 'default_model': default,
                'default_clip': 'Standing' if 'Standing' in clips else next(iter(clips)), 'models': models,
                'clips': clips, 'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'],
                'model_sha256': pick['sha256'], 'attachments': attach}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    k = standing_height(args.after) / 2.7
    js = (TEMPLATE / 'review.js').read_text()
    focuses = {'body': [0, 1.35, 0, 5.4], 'head': [0, 1.62, 0, 1.2], 'arms': [0, 1.2, 0, 2.8],
               'shoulders': [0, 1.85, 0, 3.4], 'skirt': [0, 0.95, 0, 1.8], 'feet': [0, 0.35, 0, 1.8]}
    scaled = ', '.join(f'{key}:[{",".join(f"{v * k:.3f}" for v in val)}]' for key, val in focuses.items())
    js = re.sub(r'const focuses = \{[^\n]*\};', 'const focuses = {' + scaled + '};', js)
    js = js.replace('Troll texpass', f'{args.name} anim fix').replace("'mm8:m480-texpass'", f"'{project.name}'") \
        .replace('mm8_m480_texpass_claude_frame_feedback.json', f'{project.name}_frame_feedback.json')
    js = js.replace("model=gltf.scene;model.animations=gltf.animations;scene.add(model);",
                    "model=gltf.scene;model.animations=gltf.animations;scene.add(model);"
                    "for(const a of manifest.attachments||[]){const g=await new GLTFLoader().loadAsync(a.url);"
                    "const n=model.getObjectByName(a.node);if(n)n.add(g.scene);}")
    # revisions may differ in clip length (a re-timed clip): each loaded model sets the durations
    js = js.replace("if(!clip||Math.abs(clip.duration-c.duration)>1e-5){", "if(clip)c.duration=clip.duration;if(!clip){")
    (out / 'review.js').write_text(js)
    html = (TEMPLATE / 'index.html').read_text()
    html = html.replace('<title>Troll texture pass review</title>', f'<title>{args.name} anim fix review</title>')
    html = re.sub(r'<header>.*?</header>', f'<header><h1>{args.name}: anim fix ({project.name})</h1><p>Installed '
                  'before and the anim fix per tier; region ramps baked for three.js.</p></header>', html, flags=re.S)
    (out / 'index.html').write_text(html)
    print('VIEWER', len(models), 'models,', len(clips), 'clips,', len(attach), 'attachments, focus scale', round(k, 3))


if __name__ == '__main__':
    main()
