"""Runtime export (druidess): work/rig_v6.blend (gated rig, timed clips with the baked cloak, Meshy UVs, head split) ->
export/mm6_dru1_lod0.glb. One skinned mesh 'Druidess': material Druidess_A (body set 1K, UVMap) and DruidessHead_A
(head set 1K: face, neck and choker, hair, hood; head faces get their HeadUV as TEXCOORD_0). No held prop.
Palm sockets on both hands (Socket_Palm_Left/Right, 3 cm off the palm centre along the palm normal): the cast's glow
forms between the palms (Cast claps them together forward), the missile leaves the raised right palm (Attack).
Clips Standing, Walking, Attack, Cast, Hit, Death, Fidget and Dead (last Death frame held 1 s; the death's cloak bake
settles into that frame); keys at 30 fps, quaternions sign-continuous. Args: none"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HEAD = os.path.exists(os.path.join(T, 'dru1_head_basecolor_1k.png'))

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


mats = [material('Druidess_A', 'dru1_basecolor_1k.png', 'dru1_normal_1k.png', 'dru1_metal_rough_1k.png')]
if HEAD:
    mats.append(material('DruidessHead_A', 'dru1_head_basecolor_1k.png', 'dru1_head_normal_1k.png', 'dru1_head_metal_rough_1k.png'))
me.materials.clear()
for m in mats:
    me.materials.append(m)
me.polygons.foreach_set('material_index', (hd if HEAD else np.zeros_like(hd)).tolist())
body.name = body.data.name = 'Druidess'
for at in [a.name for a in body.data.attributes if a.name in ('piece', 'finger', 'head', 'orig_co')]:
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
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm6_dru1_lod0.glb')
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
