"""Stage G: split DeathFull into Death (625 ms) + Dead (settle/hold), hide the knife outside Attack, drop
temporary actions, measure walk stride. Writes work/final_v1.blend and work/clips.json."""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
KEEP = ['Standing', 'Walking', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget']


def fcurves(act):
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def trimmed(source, name, first, last):
    act = source.copy(); act.name = name; act.use_fake_user = True
    for fc in fcurves(act):
        for i in reversed(range(len(fc.keyframe_points))):
            x = fc.keyframe_points[i].co.x
            if x < first - 1e-3 or x > last + 1e-3:
                fc.keyframe_points.remove(fc.keyframe_points[i])
        for kp in fc.keyframe_points:
            kp.co.x -= first - 1; kp.handle_left.x -= first - 1; kp.handle_right.x -= first - 1
        fc.update()
    return act


full = bpy.data.actions.get('DeathFull')
if full is not None:
    for old in ('Death', 'Dead'):
        if old in bpy.data.actions: bpy.data.actions.remove(bpy.data.actions[old])
    trimmed(full, 'Death', 1, 16)
    trimmed(full, 'Dead', 16, 40)
rig = bpy.data.objects['Peasant_Rig']
knife = rig.pose.bones['Knife']
for name in KEEP:
    act = bpy.data.actions[name]
    rig.animation_data.action = act
    f0, f1 = act.frame_range
    if name != 'Attack':
        for f in (f0, f1):
            knife.scale = (0, 0, 0); knife.keyframe_insert('scale', frame=f)
        for fc in fcurves(act):
            if '"Knife"' in fc.data_path:
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for act in list(bpy.data.actions):
    if act.name not in KEEP:
        bpy.data.actions.remove(act)
# Walk stride: Meshy source hips travel over one cycle, scaled by the retarget leg ratio (0.864).
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'meshy/baseline_rig_v1/result_basic_animations_walking_glb_url.glb'))
src = next(o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE')
sa = src.animation_data.action; a0, a1 = (int(round(x)) for x in sa.frame_range)
bpy.context.scene.frame_set(a0); p0 = src.matrix_world @ src.pose.bones['Hips'].head
bpy.context.scene.frame_set(a1); p1 = src.matrix_world @ src.pose.bones['Hips'].head
travel = (p1 - p0).length
for o in [o for o in bpy.data.objects if o not in before]:
    bpy.data.objects.remove(o, do_unlink=True)
for act in list(bpy.data.actions):
    if act.name not in KEEP: bpy.data.actions.remove(act)
clips = {a.name: {'frames': [a.frame_range[0], a.frame_range[1]],
                  'seconds': round((a.frame_range[1] - a.frame_range[0]) / 24.0, 4)} for a in bpy.data.actions}
info = {'fps': 24, 'clips': clips, 'source_walk_hips_travel_m': travel, 'stride_length_m': travel * 0.864}
json.dump(info, open(os.path.join(common.WORK, 'clips.json'), 'w'), indent=2)
print('CLIPS', json.dumps(info))
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, os.environ.get('FINAL_OUT', 'final_v3.blend')))
