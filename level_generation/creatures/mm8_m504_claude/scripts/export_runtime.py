"""Runtime export (m504, from m470): work/rig_v7.blend (gated rig, timed clips, Meshy UVs, head split, rubble death)
-> export/mm8_m504_lod0.glb. Two skinned meshes on one rig: 'EarthElemental' (the living body) and 'Rubble' (14 rigid
capped pieces on Rubble_* bones, collapsed except after the Death break); both use EarthElemental_A (body set 1K,
UVMap) and EarthElementalHead_A (head set 1K, HeadUV as TEXCOORD_0). Fist sockets Socket_FistL/R. Clips Standing,
Walking, Attack, Hit, Death, Fidget and Dead (last Death frame held 1 s, scales included); keys at 30 fps,
quaternions sign-continuous. Args: none"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v7.blend'))   # rig_v7 = rig_v6 + rubble death
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; rub = bpy.data.objects['Rubble']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HEAD = os.path.exists(os.path.join(T, 'm504_head_basecolor_1k.png'))

# ---------------------------------------------------------------- head UVs into the single UV layer (both meshes)
HD = {}
for ob in (body, rub):
    me = ob.data
    hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd); HD[ob.name] = hd
    if HEAD:
        huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
        for p in me.polygons:
            if hd[p.index]:
                for li in p.loop_indices:
                    buv[li].uv = huv[li].uv
    me.uv_layers.active = me.uv_layers['UVMap']
    me.uv_layers.remove(me.uv_layers['HeadUV'])

props = []
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


mats = [material('EarthElemental_A', 'm504_basecolor_1k.png', 'm504_normal_1k.png', 'm504_metal_rough_1k.png')]
if HEAD:
    mats.append(material('EarthElementalHead_A', 'm504_head_basecolor_1k.png', 'm504_head_normal_1k.png', 'm504_head_metal_rough_1k.png'))
for ob, name in ((body, 'EarthElemental'), (rub, 'Rubble')):
    me = ob.data; me.materials.clear()
    for m in mats:
        me.materials.append(m)
    hd = HD[ob.name]
    me.polygons.foreach_set('material_index', (hd if HEAD else np.zeros_like(hd)).tolist())
    ob.name = me.name = name
    for at in [a.name for a in me.attributes if a.name in ('piece', 'garment', 'finger', 'head', 'orig_co', 'seg')]:
        me.attributes.remove(me.attributes[at])

# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.get('Dead') or bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 30):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location, pb.scale = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
        pb.keyframe_insert('scale', frame=f)
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
KEEP = ('Standing', 'Walking', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm8_m504_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (body, rub, rig))
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
        'rubble_tris': sum(len(p.vertices) - 2 for p in rub.data.polygons),
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
