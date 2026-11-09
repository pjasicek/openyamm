"""Replace only the seven edited Attack channels in every selected v5 handoff."""
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor

W = P / 'work/attack_v6'
src, sb = read_glb(W / 'momentum.glb')
source = next(a for a in src['animations'] if a['name'] == 'Attack')
changed = {tuple(x) for x in json.loads((W / 'authoring.json').read_text())['changed_channels']}
def channels(d, a):
    return {(d['nodes'][c['target']['node']]['name'], c['target']['path']): c for c in a['channels']}
sc = channels(src, source)
targets = [P / 'export' / name for name in ['mm6_gar_lod0.glb', 'mm6_gar_prepared.glb',
           'mm6_gar_lods.glb', 'mm6_gar.glb']]
targets += [P / f'review/viewer/mm6_gar_{tier}.glb' for tier in 'abc']
report = []
for target in targets:
    snapshot = W / 'before' / target.relative_to(P)
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        shutil.copy2(target, snapshot)
    old, ob = read_glb(snapshot)
    d, b = copy.deepcopy(old), bytearray(ob)
    action = next(a for a in d['animations'] if a['name'] == 'Attack')
    dc = channels(d, action)
    assert changed <= dc.keys() and changed <= sc.keys()
    for key in sorted(changed):
        sampler = copy.deepcopy(source['samplers'][sc[key]['sampler']])
        for field in ['input', 'output']:
            i = sampler[field]
            sampler[field] = append_accessor(d, b, src['accessors'][i], accessor_bytes(src, sb, i))
        dc[key]['sampler'] = len(action['samplers'])
        action['samplers'].append(sampler)
    assert bytes(b[:len(ob)]) == ob
    assert {k: v for k, v in d.items() if k not in ['animations', 'accessors', 'bufferViews']} == {
        k: v for k, v in old.items() if k not in ['animations', 'accessors', 'bufferViews']}
    for a in old['animations']:
        new = next(x for x in d['animations'] if x['name'] == a['name'])
        if a['name'] != 'Attack':
            assert a == new
        else:
            for key, ch in channels(old, a).items():
                if key not in changed:
                    assert ch == dc[key]
                    assert a['samplers'][ch['sampler']] == new['samplers'][ch['sampler']]
    write_glb(target, d, b)
    report.append({'path': str(target.relative_to(P)), 'before_sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                   'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'changed_channels': len(changed)})
installed = P.parents[2] / 'assets_dev/worlds/mm6/models/mm6_gar.glb'
previous = W / 'installed_before.glb'
if not previous.exists():
    assert installed.read_bytes() == (W / 'before/export/mm6_gar.glb').read_bytes()
    shutil.copy2(installed, previous)
shutil.copy2(P / 'export/mm6_gar.glb', installed)
(W / 'animation_only_audit.json').write_text(json.dumps({'files': report,
    'unchanged': ['All geometry, UVs, materials, images, skins, node hierarchy, LODs and back-face processing',
                  'Flight, Hit, Death, Dead: complete animation records and sample bytes',
                  'All Attack channels except six torso/head rotations and pelvis translation'],
    'runtime_matches_export': installed.read_bytes() == (P / 'export/mm6_gar.glb').read_bytes()}, indent=2) + '\n')
manifest_path = P / 'review/viewer/manifest.json'
manifest = json.loads(manifest_path.read_text())
manifest['revision'] = 'mm6_gar_codex_v6_attack_momentum'
manifest['default_clip'] = 'Attack'
manifest['model_sha256'] = hashlib.sha256((manifest_path.parent / manifest['model']).read_bytes()).hexdigest()
for model in manifest['models']:
    model['revision'] = manifest['revision']
    model['sha256'] = hashlib.sha256((manifest_path.parent / model['url']).read_bytes()).hexdigest()
manifest['clips']['Attack']['provenance'] = 'Right claw swipe with backward anticipation, forward torso delivery and left-arm balance; impact at 0.75 s.'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(report, indent=2))
