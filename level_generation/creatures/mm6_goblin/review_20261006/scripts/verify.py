"""One preservation check for the review export; no artistic acceptance inference."""
import hashlib
import json
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT = ROOT / 'review_20261006'

def load(path):
    data = path.read_bytes()
    assert data[:4] == b'glTF'
    length = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20+length])
    assert struct.unpack_from('<I', data, 24+length)[0] == 0x004E4942
    return doc, data[28+length:]

old, old_bin = load(ROOT / 'full_20261006/delivery/mm6_goblin_745.glb')
new, new_bin = load(OUT / 'goblin_review.glb')
def buffer(doc, binary, index):
    view = doc['bufferViews'][index]
    offset = view.get('byteOffset', 0)
    return binary[offset:offset+view['byteLength']]
def accessor(doc, binary, index):
    a = doc['accessors'][index]
    return {k:v for k,v in a.items() if k!='bufferView'}, buffer(doc, binary, a['bufferView'])

assert [{k:v for k,v in m.items() if k!='extras'} for m in old['materials']] == [{k:v for k,v in m.items() if k!='extras'} for m in new['materials']], 'Material factors changed'
assert old.get('textures') == new.get('textures'), 'Texture mapping changed'
assert len(old['images']) == len(new['images'])
for a,b in zip(old['images'], new['images']):
    assert a['mimeType'] == b['mimeType']
    assert buffer(old,old_bin,a['bufferView']) == buffer(new,new_bin,b['bufferView']), 'Texture pixels/encoding changed'
assert len(old['meshes']) == len(new['meshes'])
for a,b in zip(old['meshes'],new['meshes']):
    assert len(a['primitives']) == len(b['primitives'])
    for pa,pb in zip(a['primitives'],b['primitives']):
        assert pa['attributes'].keys() == pb['attributes'].keys()
        assert pa['material'] == pb['material']
        for attribute in pa['attributes']:
            assert accessor(old,old_bin,pa['attributes'][attribute]) == accessor(new,new_bin,pb['attributes'][attribute]), attribute+' changed'
        assert accessor(old,old_bin,pa['indices']) == accessor(new,new_bin,pb['indices']), 'Topology changed'
assert len(old['skins']) == len(new['skins']) == 1
assert accessor(old,old_bin,old['skins'][0]['inverseBindMatrices']) == accessor(new,new_bin,new['skins'][0]['inverseBindMatrices'])
def channels(doc,binary,animation):
    result = {}
    for channel in animation['channels']:
        target = channel['target']
        sampler = animation['samplers'][channel['sampler']]
        result[(doc['nodes'][target['node']]['name'],target['path'])] = (sampler.get('interpolation','LINEAR'),accessor(doc,binary,sampler['input']),accessor(doc,binary,sampler['output']))
    return result
new_actions = {a['name']:a for a in new['animations']}
for a in old['animations']:
    assert channels(old,old_bin,a) == channels(new,new_bin,new_actions[a['name']]), a['name']+' changed'
assert set(new_actions) == {a['name'] for a in old['animations']} | {'Meshy_Walk','Meshy_Run'}
manifest = json.loads((OUT / 'manifest.json').read_text())
for name,a in new_actions.items():
    duration = max(new['accessors'][s['input']]['max'][0] for s in a['samplers'])
    assert abs(duration-manifest['clips'][name]['duration']) < 1e-6
report = dict(status='pass', original_sha256=hashlib.sha256((ROOT/'full_20261006/delivery/mm6_goblin_745.glb').read_bytes()).hexdigest(), candidate_sha256=manifest['model_sha256'], unchanged=['body and sword positions/normals/tangents/UVs/joints/weights/topology', 'inverse bind matrices', 'four embedded PNG images', 'material factors and texture assignments', 'all seven original animation channels and sample buffers'], added_clips=['Meshy_Walk','Meshy_Run'], artistic_acceptance='not claimed; six user findings remain open', mesh_count=len(new['meshes']))
(OUT / 'preservation_check.json').write_text(json.dumps(report,indent=2)+'\n')
browser = json.loads(Path('/tmp/openyamm-goblin-viewer-check/browser_validation.json').read_text())
assert browser['status'] == 'pass'
for file in Path('/tmp/openyamm-goblin-viewer-check').iterdir():
    if file.suffix == '.png':
        shutil.copyfile(file, OUT / 'browser' / file.name)
    elif file.name == 'browser_validation.json':
        shutil.copyfile(file, OUT / file.name)
state_path = ROOT / 'stage1_20261006/creature_3d_progress.json'
p = json.loads(state_path.read_text())
p['review_workspace'] = dict(path='../review_20261006', viewer='../review_20261006/index.html', url='http://127.0.0.1:8901/level_generation/creatures/mm6_goblin/review_20261006/', model='../review_20261006/goblin_review.glb', sha256=manifest['model_sha256'], master='../review_20261006/goblin_review.blend', role='interactive comparison and Meshy locomotion candidates; original rejected regions retained', technical_check='../review_20261006/preservation_check.json', browser_check='../review_20261006/browser_validation.json', user_artistic_acceptance='not_recorded_for_new_Meshy_candidates')
p['stages']['3_animation_and_finish']['substeps']['interactive_frame_review_viewer'] = 'complete'
p['stages']['3_animation_and_finish']['substeps']['meshy_locomotion_candidates'] = 'unverified'
p['next_action'] = dict(owner='user', action='Use the interactive viewer to provide exact clip/frame/time and marked regions. Head/neck and skirt fit, attack wrist/arc, free-hand collisions and locomotion candidates still need revision/review; old export checks do not clear these findings.', input='../review_20261006/index.html', output='Copied frame feedback, marked PNG screenshots or mm6_goblin_frame_feedback.json')
p['next_codex_action'] = 'Revise head/neck and skirt fit, select/adapt Meshy locomotion after review, correct the shoulder-led attack arc and affected hand/cloth contacts. Preserve selected unrelated clips and UV/maps; verify changed surfaces/interpolation/export.'
p['correction_ledger'].append(dict(stage=3, region='interactive motion review and Meshy locomotion candidates', cause='User identified wrist flips, slicing discontinuity, skirt/hand intersections and profile errors missed by previous checks', repair='Added exact-time orbit viewer with marked feedback links and appended/adapted already downloaded Meshy Walking/Running on the retained textured rig.', evidence='review_20261006/browser_validation.json; review_20261006/preservation_check.json; review_20261006/stock_adaptation.json', status='review tools complete; reported visual findings remain open; candidate gait acceptance not inferred'))
p['updated_at'] = datetime.now(timezone.utc).isoformat()
state_path.write_text(json.dumps(p,indent=2)+'\n')
print('Preservation check passes: unchanged geometry, bind, images, materials and all seven original clips; browser checks:',len(browser['checks']))
