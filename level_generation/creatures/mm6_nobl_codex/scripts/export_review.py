"""G7: clay review export of work/rig_v8.blend -> review/viewer/mm6_nobl_clay.glb. Adds the 'Sword' bone (child of
B_R_Hand, head at the solved handle centre, along the handle axis; work/grip_pose.json) and a simple longsword mesh
weighted 100 % to it (native bar1sta2 proportions: 0.11 m grip, gold crossguard, 0.78 m blade). Clips: Standing,
Walking, Running, Attack, Hit, Death, Fidget and Dead (the last Death frame held 1 s). Quaternion keys are made
sign-continuous; actions start at frame 0. Args: none"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v8.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
so=bpy.data.objects['SwordMesh']
for o in bpy.data.objects:o.select_set(o in (body,so))
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
# Dead: the last Death frame held one second
death = bpy.data.actions['Death']
rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
bpy.context.scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.get('Dead') or bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 30):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 30
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


for act in bpy.data.actions:
    curves = {}
    for fc in fcurves(act):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]; prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] *= -1; keys[i][j].handle_left[1] *= -1; keys[i][j].handle_right[1] *= -1
                q = [-x for x in q]
            prev = q
        for fc in comps.values():
            fc.update()
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
bpy.context.scene.render.fps = 30; bpy.context.scene.render.fps_base = 1
out = os.path.join(HERE, 'review', 'viewer', 'mm6_nobl_clay.glb'); os.makedirs(os.path.dirname(out), exist_ok=True)
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out, {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions})
