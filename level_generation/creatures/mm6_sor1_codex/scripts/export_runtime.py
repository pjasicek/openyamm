"""Export the fitted eight-clip Sorcerer and detailed staff at 120 Hz; retain an editable packed master."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_final_textured.blend'))
sys.path.insert(0,os.path.join(HERE,'scripts'))
from add_trousers import add_trousers
scene = bpy.context.scene; scene.render.fps = 120; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
me.validate(verbose=True, clean_customdata=False)
add_trousers(body,rig)
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HEAD = os.path.exists(os.path.join(T, 'sor1_head_basecolor_1k.png'))

# ---------------------------------------------------------------- head UVs into the single UV layer
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
if HEAD:
    huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
    for p in me.polygons:
        if hd[p.index]:
            for li in p.loop_indices:
                buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])
for _l in [l.name for l in me.uv_layers if l.name != 'UVMap']:     # e.g. HeadUV_prev (face_bake.py's bake source)
    me.uv_layers.remove(me.uv_layers[_l])

# ---------------------------------------------------------------- palm sockets
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
SOCK = {}
for s_, name in (('L', 'Socket_Palm_Left'), ('R', 'Socket_Palm_Right')):
    wl = rig.data.bones[f'B_{s_}_Hand'].head_local; k2 = rig.data.bones[f'B_{s_}_Finger2'].head_local
    across = rig.data.bones[f'B_{s_}_Finger1'].head_local - rig.data.bones[f'B_{s_}_Finger4'].head_local
    pn = (k2 - wl).cross(across).normalized()
    if pn.x * wl.x > 0:                                  # the rest palms face the thighs: the normal points inward
        pn = -pn
    sp = wl + (k2 - wl) * 0.45 + pn * 0.03
    sk = rig.data.edit_bones.new(name); sk.head = sp; sk.tail = sp + pn * 0.05
    sk.parent = rig.data.edit_bones[f'B_{s_}_Hand']; sk.use_deform = False
    SOCK[name] = [round(x, 4) for x in sp]
bpy.ops.object.mode_set(mode='OBJECT')
print('SOCKETS', SOCK)

# ---------------------------------------------------------------- materials


def material(name, base, normal, mr):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(f, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, f)); n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m


mats = [material('Sorcerer_A', 'sor1_basecolor_1k.png', 'sor1_normal_1k.png', 'sor1_metal_rough_1k.png')]
if HEAD:
    mats.append(material('SorcererHead_A', 'sor1_head_basecolor_1k.png', 'sor1_head_normal_1k.png', 'sor1_head_metal_rough_1k.png'))
me.materials.clear()
for m in mats:
    me.materials.append(m)
me.polygons.foreach_set('material_index', (hd if HEAD else np.zeros_like(hd)).tolist())
staff=bpy.data.objects['Staff']; sm=staff.data
from staff_detail import rebuild_staff
rebuild_staff(staff,scene);sm=staff.data
sm.materials.clear();sm.materials.append(material('SorcererStaff','sor1_staff_basecolor.png','sor1_staff_normal.png','sor1_staff_metal_rough.png'))
for face in sm.polygons:face.material_index=0
# The native staff gem supplies the secondary cast focus.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
data=json.loads(scene['staff']);sk=rig.data.edit_bones.new('Socket_Staff_Head')
sk.head=Vector(data['centre'])+Vector(data['axis'])*(1.705-data['grip_from_foot']);sk.tail=sk.head+Vector(data['axis'])*.04
sk.parent=rig.data.edit_bones['B_Staff'];sk.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
assert len(rig.data.bones)<=128
# Cast's existing forward release peaks at frame 13. A nine-frame ready hold aligns it to Attack's frame 22.
act=bpy.data.actions['Cast']
curves=[fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
end=act.frame_range[1]
for fc in curves:
 first=fc.keyframe_points[0].co[1]
 for key in fc.keyframe_points:
  key.co.x+=36;key.handle_left.x+=36;key.handle_right.x+=36
 fc.keyframe_points.insert(0,first);fc.update()
act.use_frame_range=True;act.frame_start=0;act.frame_end=end+36
# Ease the first half of the recoil; retain the native 0.75-second hit window.
a=bpy.data.actions['Hit']
for layer in a.layers:
 for strip in layer.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:
    for key in fc.keyframe_points:
     for pt in (key.co,key.handle_left,key.handle_right):pt.x=pt.x*48/42 if pt.x<=42 else pt.x+6
    fc.update()
a.use_frame_range=True;a.frame_start=0;a.frame_end=90
body.name = body.data.name = 'Body'  


# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.get('Dead') or bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 120):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 120
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
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm6_sor1_lod0.glb')
for act in bpy.data.actions:
 for fc in fcurves(act):
  for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.frame_set(0)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'work','production_master.blend'))
# Join only for the shared offline LOD/split-attachment pipeline. Master keeps the two editable objects.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);staff.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
body.name=body.data.name='Sorcerer'
body.data.validate(verbose=True, clean_customdata=False)
for at in [a.name for a in body.data.attributes if a.name in ('piece','finger','head','orig_co')]:
 body.data.attributes.remove(body.data.attributes[at])
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=True, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
info = {'glb': out, 'head_set': HEAD, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
