#!/usr/bin/env python3
"""Review viewer for the reduction: the batch I LOD0 (../mm7_m479_claude/export/mm7_m479_lod0.glb, 13,591) and the reduced
LOD0 (work/pick_lod0.glb, the swapped LOD0 of export/mm7_m479.glb) side by side, opening on the reduced model. Clip
durations from the GLB, native reference frames per clip (the production viewer's anchors), cache-busting hashes (the production viewer's relative native-frame paths work at the same depth).
One material and no tier ramps (palette 530 for all three descriptors), so the GLBs are copied as they are."""
import hashlib, json, shutil, struct
from pathlib import Path
P = Path(__file__).resolve().parents[1]; V = P / 'review' / 'viewer'
shutil.copyfile(P.parent / 'mm7_m479_claude' / 'export' / 'mm7_m479_lod0.glb', V / 'mm7_m479_r100.glb')
shutil.copyfile(P / 'work' / 'pick_lod0.glb', V / 'mm7_m479_r76.glb')
src = json.load(open(P.parent / 'mm7_m479_claude' / 'review' / 'viewer' / 'manifest.json'))
tris = lambda d: sum(d['accessors'][p['indices']]['count'] // 3 for p in d['meshes'][0]['primitives'])
models = []
for mid, label in (('r100', 'Treant · batch I'), ('r76', 'Treant · reduced 76 %')):
    raw = (V / f'mm7_m479_{mid}.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n]); sha = hashlib.sha256(raw).hexdigest()
    models.append({'id': mid, 'label': f'{label} · {tris(doc):,}', 'revision': 'reduce-1',
                   'url': f'mm7_m479_{mid}.glb?v={sha[:12]}', 'sha256': sha})
m = {'revision': 'reduce-1', 'default_clip': 'Standing', 'feedback': 'feedback/user_feedback.json', 'default_model': 'r76',
     'models': models, 'clips': src['clips']}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', [x['label'] for x in models])
