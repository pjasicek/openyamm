"""Reimport the delivered GLB and check its actual rig, weights and sampled geometry."""
from pathlib import Path
import bpy, json, hashlib, math
p = Path(__file__).resolve().parents[1]
source = p / 'export/mm8_m472.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(source))
rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE']
assert len(rigs) == 1
rig = rigs[0]
assert len(rig.data.bones) == 128
body = bpy.data.objects['Necromancer']
weights = [sum(g.weight for g in v.groups) for v in body.data.vertices]
assert all(abs(w - 1) < 1e-5 for w in weights)
assert max(len(v.groups) for v in body.data.vertices) <= 8
expected = {'Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget'}
actions = {a.name: a for a in bpy.data.actions}
assert set(actions) == expected, list(actions)
rig.animation_data_create()
for track in rig.animation_data.nla_tracks:
    track.mute = True
report = {}
held_poses = {}
for name, action in actions.items():
    rig.animation_data.action = action
    if action.slots:
        rig.animation_data.action_slot = action.slots[0]
    samples = []
    start, end = action.frame_range
    for frame in (start, (start + end) / 2, end):
        bpy.context.scene.frame_set(int(frame), subframe=frame % 1)
        bpy.context.view_layer.update()
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        coords = [body.matrix_world @ v.co for v in mesh.vertices]
        assert all(math.isfinite(c) for v in coords for c in v)
        if (name == 'Death' and frame == end) or (name == 'Dead' and frame == start):
            held_poses[name] = [v.copy() for v in coords]
        samples.append({'frame': frame, 'min': [min(v[i] for v in coords) for i in range(3)],
                        'max': [max(v[i] for v in coords) for i in range(3)]})
        evaluated.to_mesh_clear()
    report[name] = samples
held_error = max((a-b).length for a,b in zip(held_poses['Death'],held_poses['Dead']))
assert held_error < 1e-5, held_error
out = p / 'review/validation'
out.mkdir(exist_ok=True)
(out / 'reimport.json').write_text(json.dumps({'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'bones': len(rig.data.bones), 'max_influences': max(len(v.groups) for v in body.data.vertices),
    'held_death_max_error_m': held_error, 'sampled_clips': report}, indent=2) + '\n')
print('Reimport passed: 128 bones, normalized weights, nine finite sampled clips.')
