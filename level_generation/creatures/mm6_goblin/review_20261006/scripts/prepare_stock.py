"""Review candidates from existing Meshy gaits on the unchanged textured goblin."""
import bpy
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT = ROOT / 'review_20261006'
BASE = ROOT / 'full_20261006/delivery/mm6_goblin.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
arm = bpy.data.objects['Goblin_Rig']
body = bpy.data.objects['Goblin_Body']
sword = bpy.data.objects['Goblin_Sword']
scene = bpy.context.scene
native_names = ['Standing', 'Walk', 'Attack', 'Hit', 'Death', 'Corpse', 'Fidget']
native_actions = {name: bpy.data.actions[name] for name in native_names}
arm.animation_data.action = native_actions['Standing']
arm.animation_data.action_slot = native_actions['Standing'].slots[0]
scene.frame_set(1)
grip = {b.name: (b.location.copy(), b.rotation_quaternion.copy()) for b in arm.pose.bones if b.name.startswith('Digit.R.')}
with bpy.data.libraries.load(str(ROOT / 'full_20261006/work/stock_probes_v1.blend'), link=False) as (src, dst):
    dst.actions = ['Stock_Walk', 'Stock_Run']
    dst.objects = ['Goblin_Rig']
source_rig = dst.objects[0]
rest_error = max(abs(arm.data.bones[b.name].matrix_local[i][j] - b.matrix_local[i][j]) for b in source_rig.data.bones for i in range(4) for j in range(4))
assert rest_error < 1e-6, rest_error
bpy.data.objects.remove(source_rig, do_unlink=True)
def curves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves

report = []
for action, name, source in zip(dst.actions, ['Meshy_Walk', 'Meshy_Run'], ['result_basic_animations_walking_glb_url.glb', 'result_basic_animations_running_glb_url.glb']):
    action.name = name
    action.use_fake_user = True
    original_range = list(action.frame_range)
    for fc in curves(action):
        for k in fc.keyframe_points:
            k.co.x = 1 + (k.co.x - 1) * 4
            k.interpolation = 'LINEAR'
        fc.update()
    arm.animation_data.action = action
    arm.animation_data.action_slot = action.slots[0]
    for frame in range(1, round(action.frame_range[1]) + 1, 4):
        scene.frame_set(frame)
        for bone, (loc, q) in grip.items():
            pb = arm.pose.bones[bone]
            pb.location = loc
            pb.rotation_quaternion = q
            pb.keyframe_insert('location', frame=frame, group=bone)
            pb.keyframe_insert('rotation_quaternion', frame=frame, group=bone)
    for fc in curves(action):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    duration = (action.frame_range[1] - action.frame_range[0]) / 192
    action['provenance'] = str(ROOT / 'meshy/body_rig_v1' / source)
    action['review_status'] = 'candidate; user-requested Meshy gait basis; grip adapted; not production accepted'
    report.append(dict(name=name, duration_seconds=duration, source='meshy/body_rig_v1/' + source, source_sha256=hashlib.sha256((ROOT / 'meshy/body_rig_v1' / source).read_bytes()).hexdigest(), adaptation='Existing rest-space retarget on corrected 64-bone rig; retain Meshy core-bone motion, shoulder/forearm/skirt followers, close right fingers/thumb using selected ready-pose grip. Original native clips and body/UV/materials unchanged.', status='candidate_needs_visual_review'))

allowed = native_names + ['Meshy_Walk', 'Meshy_Run']
for a in list(bpy.data.actions):
    if a.name not in allowed:
        bpy.data.actions.remove(a)
for o in list(scene.objects):
    o.select_set(o in [arm, body, sword])
bpy.context.view_layer.objects.active = arm
arm.animation_data.action = native_actions['Standing']
arm.animation_data.action_slot = native_actions['Standing'].slots[0]
scene.frame_set(1)
bpy.ops.export_scene.gltf(filepath=str(OUT / 'goblin_review.glb'), export_format='GLB', use_selection=True, export_animation_mode='ACTIONS', export_anim_slide_to_zero=True, export_rest_position_armature=True, export_frame_range=False, export_force_sampling=True, export_frame_step=1, export_anim_single_armature=True, export_influence_nb=4, export_all_influences=False, export_animations=True, export_yup=True, export_apply=True, export_tangents=True, export_texcoords=True, export_normals=True, export_extras=True, export_image_format='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'goblin_review.blend'))
(OUT / 'stock_adaptation.json').write_text(json.dumps(dict(base_master=str(BASE.relative_to(ROOT)), base_master_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(), rest_matrix_max_error=rest_error, clips=report, paid_credits=0), indent=2) + '\n')
spec = json.loads((ROOT / 'stage1_20261006/motion_spec.json').read_text())
clips = {}
for c in spec['clips']:
    name = c['name']
    clips[name] = dict(label='Walk · previous reconstruction' if name == 'Walk' else name, duration=c['native_duration_ms'] / 1000, mode='hold' if name in ['Standing', 'Corpse'] else 'loop' if name in ['Walk', 'Fidget'] else 'one_shot', provenance='Previous native reconstruction · reported defects retained for review', anchors=[dict(time=a['time_ms'] / 1000, label=chr(65 + i) if len(c['anchors']) > 1 else 'Held', phase=a['phase'], source_images=['../stage1_20261006/' + image for image in a['source_images']]) for i, a in enumerate(c['anchors'])])
for r in report:
    clips[r['name']] = dict(label=r['name'].replace('_', ' ') + ' · candidate', duration=r['duration_seconds'], mode='loop', provenance='Existing Meshy stock animation · retargeted with sword grip · needs review', anchors=[])
manifest = dict(revision='review_20261006', model='goblin_review.glb', model_sha256=hashlib.sha256((OUT / 'goblin_review.glb').read_bytes()).hexdigest(), default_clip='Standing', clips=clips, feedback='feedback/user_feedback.json')
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Exported nine-clip interactive-review candidate; original delivery preserved.', flush=True)
