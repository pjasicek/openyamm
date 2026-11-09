"""Guard the coat repair's scope, unchanged animation and delivered motion/geometry."""
import bpy, hashlib, json, sys
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes


def animation_signature():
    result = {}
    for a in bpy.data.actions:
        curves = [fc for layer in a.layers for strip in layer.strips
                  for bag in strip.channelbags for fc in bag.fcurves]
        result[a.name] = [(c.data_path, c.array_index,
                          [(tuple(k.co), k.interpolation) for k in c.keyframe_points]) for c in curves]
    return hashlib.sha256(repr(result).encode()).hexdigest()


def snapshot():
    b = bpy.data.objects['Body']
    return np.array([v.co[:] for v in b.data.vertices]), [
        {b.vertex_groups[g.group].name: float(g.weight) for g in v.groups} for v in b.data.vertices]


base = P / 'review/coat_skin/baseline'
bpy.ops.wm.open_mainfile(filepath=str(base / 'work/master_settled.blend'))
old_co, old_weights = snapshot()
old_anim = animation_signature()
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/master_settled.blend'))
co, weights = snapshot()
assert np.array_equal(co, old_co), 'Rest geometry changed'
assert animation_signature() == old_anim, 'Animation keys changed'
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
piece = np.array([p.value for p in body.data.attributes['piece'].data])
changed = np.array([a != b for a, b in zip(weights, old_weights)])
assert (piece[changed] == 0).all()
assert (co[changed, 2] > .88).all(), 'Coat tails were reweighted'
assert sum(changed) > 100
center = rig.data.bones['B_Spine2'].head_local.x
chest = (piece == 0) & (abs(co[:, 0] - center) <= .16) & (co[:, 2] >= 1.08)
assert not any('Arm' in name or 'Clavicle' in name for i in np.flatnonzero(chest) for name in weights[i])
assert all(abs(sum(w.values()) - 1) < 1e-5 for w in weights)
report = {'changed_coat_vertices': int(sum(changed)), 'rest_geometry_unchanged': True,
          'all_animation_keys_unchanged': True, 'coat_tails_and_other_parts_unchanged': True,
          'chest_collar_arm_influences': 0, 'exports': {}}
# Compare samplers by node name, because the full export can reorder node indices.
def channels(doc, binary, animation):
    result = {}
    for c in animation['channels']:
        target = c['target']; s = animation['samplers'][c['sampler']]
        key = (doc['nodes'][target['node']]['name'], target['path'])
        result[key] = (s.get('interpolation', 'LINEAR'),
                       accessor_bytes(doc, binary, s['input']), accessor_bytes(doc, binary, s['output']))
    return result

for file in ['export/mm8_m420_prepared.glb', 'export/mm8_m420.glb',
             'review/viewer/mm8_pirate_mage_a.glb']:
    old, ob = read_glb(base / file); new, nb = read_glb(P / file)
    for a in old['animations']:
        after = next(x for x in new['animations'] if x['name'] == a['name'])
        assert channels(old, ob, a) == channels(new, nb, after), (file, a['name'])
    report['exports'][file] = {'all_nine_clip_samplers_identical': True}
    # LOD rebuilds retain topology, with only float roundoff in positions/UVs.
    max_delta = 0.0
    for om, nm in zip(old['meshes'], new['meshes']):
        for op, np_ in zip(om['primitives'], nm['primitives']):
            assert accessor_bytes(old, ob, op['indices']) == accessor_bytes(new, nb, np_['indices'])
            for attr in ['POSITION', 'TEXCOORD_0']:
                a = np.frombuffer(accessor_bytes(old, ob, op['attributes'][attr]), dtype='<f4')
                b = np.frombuffer(accessor_bytes(new, nb, np_['attributes'][attr]), dtype='<f4')
                assert a.shape == b.shape
                delta = float(np.max(abs(a - b)))
                assert delta < 2e-6, (file, om['name'], attr, delta)
                max_delta = max(max_delta, delta)
    report['exports'][file]['geometry_topology_unchanged'] = True
    report['exports'][file]['maximum_position_uv_roundoff'] = max_delta
(P / 'review/coat_skin/scope_check.json').write_text(json.dumps(report, indent=2) + '\n')
print('COAT_SCOPE', json.dumps(report))
