"""Runtime export (sorceress): work/rig_v6.blend (gated rig and timed clips synced into the UV master) ->
export/xeen_sorc_lod0.glb. One skinned mesh 'Sorc' with two materials: Sorc_A (body set: 1K colour, 1K normal, 1K ORM)
and SorcHead_A (head set: the same three 1K maps), each primitive's UVs rescaled from its half of the shared paint
square (uv_sorc.py: body u 0..0.5, head u 0.5..1, v 0..0.5) to its own 0..1 square. merge_head_material.py joins them
later (one draw). Socket bones (non-deforming, children of the hands): 'Socket_RightPalm' / 'Socket_LeftPalm', 3 cm off
each palm along its normal (cast glow and release). Clips Standing, Walking, Running, Attack, Cast, Hit, Death,
Fidget and Dead (the last Death frame held 1 s); keys at 30 fps, quaternions sign-continuous. Args: none"""
import bpy, sys, os, json, math
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
me.uv_layers.active = me.uv_layers['UVMap']
for uvl in [u.name for u in me.uv_layers if u.name != 'UVMap']:
    me.uv_layers.remove(me.uv_layers[uvl])
hs = np.zeros(len(me.polygons), np.int32); me.attributes['headset'].data.foreach_get('value', hs)
uvd = me.uv_layers['UVMap'].data
for p in me.polygons:
    du = 0.5 if hs[p.index] else 0.0
    for li in p.loop_indices:
        u, v = uvd[li].uv
        uvd[li].uv = ((u - du) * 2, v * 2)

# ---------------------------------------------------------------- palm sockets
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for s, nm in (('R', 'Socket_RightPalm'), ('L', 'Socket_LeftPalm')):
    eb = rig.data.edit_bones
    wr = eb[f'B_{s}_Hand'].head.copy(); k2 = eb[f'B_{s}_Finger2'].head.copy()
    across = eb[f'B_{s}_Finger1'].head - eb[f'B_{s}_Finger4'].head
    pn = (k2 - wr).cross(across).normalized()
    if pn.y > 0:
        pn = -pn                                                       # the A-pose palms face forward (-Y)
    sp_ = wr + (k2 - wr) * 0.45 + pn * 0.03
    sk = eb.new(nm); sk.head = sp_; sk.tail = sp_ + pn * 0.05; sk.parent = eb[f'B_{s}_Hand']; sk.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------- materials
def material(name, base, normal=None, mr=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(f, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, f)); n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    if normal:
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if mr:
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    else:
        bsdf.inputs['Roughness'].default_value = 0.55; bsdf.inputs['Metallic'].default_value = 0.0
    return m


me.materials.clear()
me.materials.append(material('Sorc_A', 'sorc_basecolor_graded.png', 'sorc_normal_1k.png', 'sorc_mr_1k.png'))
me.materials.append(material('SorcHead_A', 'sorc_head_basecolor_graded.png', 'sorc_head_normal_1k.png', 'sorc_head_mr_1k.png'))
me.polygons.foreach_set('material_index', hs.astype(np.int32))
me.update()
print('MATERIALS head faces', int(hs.sum()), 'of', len(me.polygons))
body.name = body.data.name = 'Sorc'
for at in [a.name for a in body.data.attributes if a.name in ('piece', 'garment', 'finger', 'head', 'orig_co', 'headset', 'fid')]:
    body.data.attributes.remove(body.data.attributes[at])
for ca in [a.name for a in body.data.color_attributes]:
    body.data.color_attributes.remove(body.data.color_attributes[ca])

# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if len(death.slots): rig.animation_data.action_slot = death.slots[0]
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
if len(st.slots): rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'xeen_sorc_lod0.glb')
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
info = {'glb': out, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
