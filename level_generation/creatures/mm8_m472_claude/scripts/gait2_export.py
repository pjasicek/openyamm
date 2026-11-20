"""gait2 (2026-10-21): export the new clips for grafting. The new actions of work/gait2_gated.blend are appended to the
exported master (work/necromancer_master.blend: the 128-joint rig with sockets, as export_runtime.py left it) and the
armature alone is exported with export_runtime.py's glTF settings (sampled, 30 fps, slid to zero, quaternion signs
continuous) to work/gait2_anim.glb, together with the installed Walking as the pipeline check for gait2_graft.py.
The master file itself is not saved."""
from pathlib import Path
import bpy
p = Path(__file__).resolve().parents[1]; W = p / 'work'
NEW = ['Walk2', 'Run2']
bpy.ops.wm.open_mainfile(filepath=str(W / 'necromancer_master.blend'))
with bpy.data.libraries.load(str(W / 'gait2_gated.blend'), link=False) as (src, dst):
    dst.actions = [f'{n}' for n in NEW]
for a in dst.actions:
    a.use_fake_user = True
rig = bpy.data.objects['Rig']; scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()


def fcurves(action):
    return [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


for act in dst.actions:
    curves = {}
    for fc in fcurves(act):
        if fc.data_path.endswith('rotation_quaternion'): curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    for comps in curves.values():
        if len(comps) != 4: continue
        keys = [comps[i].keyframe_points for i in range(4)]; prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] *= -1; keys[i][j].handle_left[1] *= -1; keys[i][j].handle_right[1] *= -1
                q = [-x for x in q]
            prev = q
        for fc in comps.values(): fc.update()
for a in list(bpy.data.actions):
    if a.name not in NEW + ['Walking']: bpy.data.actions.remove(a)
print('GAIT2_EXPORT actions', [(a.name, tuple(a.frame_range)) for a in bpy.data.actions])
for o in bpy.data.objects: o.select_set(o == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(W / 'gait2_anim.glb'), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=True, export_attributes=False,
                          export_morph=False, export_reset_pose_bones=True, export_anim_slide_to_zero=True)
