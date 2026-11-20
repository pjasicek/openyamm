#!/usr/bin/env python3
"""Review viewer of the Fire Elemental tiers, installed beside reduced: the m496 project's viewer page with its manifest
(clips, native anchors), one GLB per tier and model under a NativeTierScale root (1 / 1.346 / 1.538, as the production
viewer builds them). The manifest's sha256 and ?v= are rewritten on every build and review.js loads the manifest with
cache: 'no-store'. Usage: [VIEWER_DIR=review/viewer] viewer_tiers.py <glb> <tag> [<glb> <tag> ...]"""
import hashlib, json, os, shutil, struct, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; PROD = HERE.parent / 'mm8_m496_claude' / 'review' / 'viewer'
OUT = HERE / os.environ.get('VIEWER_DIR', 'review/viewer'); OUT.mkdir(parents=True, exist_ok=True)
REVISION = os.environ.get('VIEWER_REVISION', 'reduce-1')
TIERS = [('a', 'Lesser Fire Elemental', 1.0), ('b', 'Fire Elemental', 1.3461662723040522),
         ('c', 'Greater Fire Elemental', 1.5384757397760596)]


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw[28 + n:]


def write_glb(path, doc, binary):
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


for name in ('index.html', 'review.js'):
    shutil.copy(PROD / name, OUT / name)
js = (OUT / 'review.js').read_text()
(OUT / 'review.js').write_text(js.replace("fetch('manifest.json')", "fetch('manifest.json', {cache: 'no-store'})"))
models = []
for glb, tag in zip(sys.argv[1::2], sys.argv[2::2]):
    for tier, label, scale in TIERS:
        doc, binary = read_glb(Path(glb))
        roots = doc['scenes'][doc.get('scene', 0)]['nodes']
        doc['nodes'].append({'name': 'NativeTierScale', 'children': roots, 'scale': [scale] * 3})
        doc['scenes'][doc.get('scene', 0)]['nodes'] = [len(doc['nodes']) - 1]
        path = OUT / f'mm8_m496_{tier}_{tag}.glb'; write_glb(path, doc, binary)
        tris = sum(doc['accessors'][p['indices']]['count'] // 3 for n in doc['nodes'] if 'mesh' in n
                   for p in doc['meshes'][n['mesh']]['primitives'])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        models.append({'id': f'm496_{tier}_{tag}', 'label': f"{label} · {'installed' if tag == 'r100' else 'reduced'} · {tris:,} tris (LOD0, all meshes)",
                       'revision': REVISION, 'url': f'{path.name}?v={digest[:12]}', 'sha256': digest})
        print('VIEWER', path.name, tris)
m = json.loads((PROD / 'manifest.json').read_text().replace('"../../native/', '"../../../mm8_m496_claude/native/'))
pick = next(x for x in models if x['id'].endswith('_' + sys.argv[-1]) and x['id'].startswith('m496_a'))
m.update(revision=REVISION, models=models, model=pick['url'], model_sha256=pick['sha256'], default_model=pick['id'],
         feedback='../feedback/user_feedback.json')
(OUT / 'manifest.json').write_text(json.dumps(m, indent=1) + '\n')
