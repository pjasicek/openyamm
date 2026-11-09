"""G7: clay review export of work/rig_v5.blend -> review/viewer/pilot.glb. Adds the 'Sword' bone (child of
B_R_Hand, head at the solved handle centre, along the handle axis; work/grip_pose.json) and a simple longsword mesh
weighted 100 % to it (native bar1sta2 proportions: 0.11 m grip, gold crossguard, 0.78 m blade). Clips: Standing,
Walking, Running, Attack, Hit, Death, Fidget and Dead (the last Death frame held 1 s). Quaternion keys are made
sign-continuous; actions start at frame 0. Args: none"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'pilot_grounded.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
Hm = rig.data.bones['B_R_Hand'].matrix_local
c = Hm @ Vector(G['handle_centre_hand_local']); ax = (Hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.get('Sword') or rig.data.edit_bones.new('Sword')
eb.head = c; eb.tail = c + ax * 0.15; eb.parent = rig.data.edit_bones['B_R_Hand']
eb.align_roll(Hm.to_3x3().col[2])
bpy.ops.object.mode_set(mode='OBJECT')
side = ax.orthogonal().normalized(); flat = ax.cross(side)
me = bpy.data.meshes.new('SwordMesh'); bm = bmesh.new()
def box(a0, a1, w0, w1, t):
    vs = [bm.verts.new(c + ax * a + side * (sx * w) + flat * (sy * t)) for a, w in ((a0, w0), (a1, w1)) for sx in (-1, 1) for sy in (-1, 1)]
    for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[i] for i in q])
box(-0.075, 0.045, 0.011, 0.011, 0.011)        # grip
box(-0.09, -0.075, 0.016, 0.016, 0.016)        # pommel
box(0.045, 0.06, 0.075, 0.075, 0.014)          # crossguard
box(0.06, 0.78, 0.024, 0.016, 0.004)           # blade
tip = bm.verts.new(c + ax * 0.84)
bm.to_mesh(me); bm.free()
so = bpy.data.objects.new('Sword', me); bpy.context.scene.collection.objects.link(so)
so.vertex_groups.new(name='Sword').add(list(range(len(me.vertices))), 1.0, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o in (body, so))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
mat = bpy.data.materials.new('Clay'); mat.use_nodes = True
body.data.materials.clear(); body.data.materials.append(mat)
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
out = os.path.join(HERE, 'review', 'viewer', 'pilot.glb'); os.makedirs(os.path.dirname(out), exist_ok=True)
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out, {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions})
