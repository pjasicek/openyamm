"""Runtime export (m430): work/rig_v6.blend (gated rig, timed clips, Meshy UVs, head split) -> export/mm7_m430_lod0.glb.
One skinned mesh 'Wight': materials Wight_A (body set 1K, UVMap), WightHead_A (head set 1K, HeadUV as TEXCOORD_0) and
Dagger_A (own props atlas, make_props.py). Bone added: 'Dagger' (child of B_R_Hand at the solved handle, +Y along the
grip axis toward the tip; the edge points from the handle toward the middle knuckle turned BLADE_ROLL about the blade,
the bar1 rule). The dagger is skinned 100 % to its bone and split into an attachment later (tools/split_attachment.py).
Clips Standing, Walking, Running, Attack, Hit, Death, Fidget and Dead (last Death frame held 1 s); keys at 30 fps,
quaternions sign-continuous. Args: none"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))   # rig_v6 = rig_v5 clips + Meshy UVs
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HEAD = os.path.exists(os.path.join(T, 'm430_head_basecolor_1k.png'))

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

# ---------------------------------------------------------------- prop bones
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
AXL = Vector(G['handle_axis_hand_local']).normalized(); GCL = Vector(G['handle_centre_hand_local'])
Hm = rig.data.bones['B_R_Hand'].matrix_local
c = Hm @ GCL; ax = (Hm.to_3x3() @ AXL).normalized()
kn = rig.data.bones['B_R_Finger2'].head_local
SX = (kn - c); SX = (SX - ax * SX.dot(ax)).normalized()
BLADE_ROLL = math.radians(float(os.environ.get('BLADE_ROLL', '105')))   # m430 sweep: attack 0.81, walk 0.91 edge-leading
SX = (SX * math.cos(BLADE_ROLL) + ax.cross(SX) * math.sin(BLADE_ROLL)).normalized(); SZ = SX.cross(ax)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('Dagger'); eb.head = c; eb.tail = c + ax * 0.15; eb.parent = rig.data.edit_bones['B_R_Hand']; eb.align_roll(SZ)
bpy.ops.object.mode_set(mode='OBJECT')
# ---------------------------------------------------------------- prop meshes from work/props.blend
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
    dst.objects = ['SwordMesh']
sw = dst.objects[0]
scene.collection.objects.link(sw)
M = Matrix((SX, ax, SZ)).transposed().to_4x4(); M.translation = c
sw.data.transform(M); sw.matrix_world = Matrix()
sw.vertex_groups.new(name='Dagger').add(list(range(len(sw.data.vertices))), 1.0, 'REPLACE')
props = [sw]
for o, bone in zip(props, ('Dagger',)):
    print('PROP', bone, sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris')
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


mats = [material('Wight_A', 'm430_basecolor_1k.png', 'm430_normal_1k.png', 'm430_metal_rough_1k.png')]
if HEAD:
    mats.append(material('WightHead_A', 'm430_head_basecolor_1k.png', 'm430_head_normal_1k.png', 'm430_head_metal_rough_1k.png'))
pm = [material('Dagger_A', 'm430_props_basecolor.png', 'm430_props_normal.png', 'm430_props_metal_rough.png')]
me.materials.clear()
for m in mats + pm:
    me.materials.append(m)
me.polygons.foreach_set('material_index', (hd if HEAD else np.zeros_like(hd)).tolist())
for o, m in zip(props, pm):
    o.data.materials.clear(); o.data.materials.append(m)
for o in bpy.data.objects:
    o.select_set(o in [body] + props)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = body.data.name = 'Wight'
for at in [a.name for a in body.data.attributes if a.name in ('piece', 'garment', 'finger', 'head', 'orig_co')]:
    body.data.attributes.remove(body.data.attributes[at])

# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
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
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm7_m430_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
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
