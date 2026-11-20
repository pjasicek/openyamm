"""Runtime export: work/rig_v8.blend -> export/mm6_pmn2_lod0.glb (one skinned mesh 'Mage', one material).
 - The staff joins the body mesh (100 % on the Staff bone), so LODs/shadow LODs treat it as one actor mesh and the
   creature is a single draw; Socket_Staff_Head stays a named node (bone) for the cast glow.
 - Packed textures from prepare_textures.py (textures/): base colour 2048, normal 1024, metal/roughness 1024 (R = tint
   mask, G = rough, B = metal). Body UVs are squeezed to u * body_u and the staff's cylindrical UVs (u in
   [0, staff_u_span)) moved into the right-hand strip, per textures/atlas_pack.json.
 - Game clips: Standing (Idle_9), Walking, Running, Attack, Cast (= Attack: the engine needs a distinct cast clip for
   spellcasters; the user chose the attack for both), Hit, Death, Dead. Quaternion keys made sign-continuous.
 - Walk stride from the planted-foot travel (stance ~60 % of the cycle), written to export/export_info.json."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v8.blend'))
import staff_rig as sr
T = os.path.join(common.PROJECT, 'textures')   # maps written by prepare_textures.py

mesh = bpy.data.objects['Mage']; staff = bpy.data.objects['Staff']; rig = bpy.data.objects['Mage_Rig']
mat = bpy.data.materials.new('Mage_A'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(name, cs):
    img = bpy.data.images.load(os.path.join(T, name)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


nt.links.new(tex('pmn2_a_basecolor_1k.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex('pmn2_normal_1k.png', 'Non-Color').outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex('pmn2_metal_rough_1k.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
PACK = json.load(open(os.path.join(T, 'atlas_pack.json')))


def remap_uvs(obj, fn, keep=None):
    me = obj.data; uv = np.zeros(len(me.loops) * 2); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    moved = np.ones(len(me.loops), bool) if keep is None else ~keep
    uv[moved, 0] = fn(uv[moved, 0]); me.uv_layers.active.data.foreach_set('uv', uv.ravel())
    return uv[moved, 0].min(), uv[moved, 0].max()


# Head texture set (claude_shared/head_texture_split.py, compose_head_set.py): faces with `head` keep their own
# 0..1 UVs and use MageHead_A, one material for every tier (only the robe changes between the native palettes).
head_flags = np.zeros(len(mesh.data.polygons), np.int32); mesh.data.attributes['head'].data.foreach_get('value', head_flags)
head_loops = np.zeros(len(mesh.data.loops), bool)
for polygon in mesh.data.polygons:
    if head_flags[polygon.index]:
        head_loops[polygon.loop_start:polygon.loop_start + polygon.loop_total] = True
head = bpy.data.materials.new('MageHead_A'); head.use_nodes = True
nt = head.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
nt.links.new(tex('pmn2_head_basecolor_graded.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex('pmn2_head_normal_1k.png', 'Non-Color').outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex('pmn2_head_metal_rough_1k.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])


su = np.zeros(len(staff.data.loops) * 2); staff.data.uv_layers.active.data.foreach_get('uv', su)
assert su[0::2].min() >= 0 and su[0::2].max() < PACK['staff_u_span'], 'staff u outside the packed strip range'
print('PACKED body u', remap_uvs(mesh, lambda u: u * PACK['body_u'], head_loops), 'staff u', remap_uvs(
    staff, lambda u: PACK['strip_u0'] + u / PACK['staff_u_span'] * (PACK['strip_u1'] - PACK['strip_u0'])))
mesh.data.materials.clear(); mesh.data.materials.append(mat); mesh.data.materials.append(head)
mesh.data.polygons.foreach_set('material_index', head_flags)
staff.data.materials.clear(); staff.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o in (mesh, staff))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
print('JOINED', mesh.name, 'materials', [m.name for m in mesh.data.materials], 'tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons))

KEEP = {'Idle_9': 'Standing', 'Walking': 'Walking', 'Running': 'Running', 'Attack': 'Attack', 'Hit': 'Hit',
        'Death': 'Death', 'Dead': 'Dead'}
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
for a in list(bpy.data.actions):
    sr.fix_quaternion_signs(a); a.name = KEEP[a.name]
cast = bpy.data.actions['Attack'].copy(); cast.name = 'Cast'; cast.use_fake_user = True

act = bpy.data.actions['Walking']; rig.animation_data.action = act
if act.slots: rig.animation_data.action_slot = act.slots[0]
ys = []
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    bpy.context.scene.frame_set(f); ys.append((rig.matrix_world @ rig.pose.bones['mixamorig:LeftFoot'].head).y)
stride = (max(ys) - min(ys)) / 0.6
rig.animation_data.action = bpy.data.actions['Standing']
if bpy.data.actions['Standing'].slots: rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
bpy.context.scene.frame_set(0)
out = os.path.join(common.PROJECT, 'export', 'mm6_pmn2_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
lo, hi = common.world_bounds([mesh])
info = {'glb': out, 'stride_length_m': stride, 'rest_bounds_m': [list(lo), list(hi)]}
json.dump(info, open(os.path.join(common.PROJECT, 'export', 'export_info.json'), 'w'), indent=2)
print('EXPORTED', json.dumps(info))
