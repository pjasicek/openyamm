"""Runtime export: work/rig_v3.blend -> export/mm6_ttn_lod0.glb (one skinned mesh 'Titan', materials Titan_A (body
set) and TitanHead_A (head texture set)).
 - Body maps from prepare_textures.py: base colour 1024, normal 1024, ORM 1024 (R AO, G roughness, B metallic).
 - Head faces (attribute `head`, claude_shared/head_texture_split.py) keep their own 0..1 UVs and the head maps from
   compose_head_set.py.
 - Spell sockets: 'Socket_Palm_Left/Right', non-deform children of the hands on the palm surface (the engine glows
   between the bound palms; the Cast is the two-handed Mixamo push).
 - Game clips: Standing, Walking, Running, Attack (fist), Ranged (spell thrust), Cast, Hit, Death, Dead, Fidget (quaternion keys sign-continuous).
 - Walk stride from the planted-foot travel, written to export/export_info.json."""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
T = os.path.join(common.PROJECT, 'textures')
mesh, rig = bpy.data.objects['Titan'], bpy.data.objects['Titan_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


def fix_quaternion_signs(action):
    """Each bone's quaternion keys sign-continuous (opposite-sign neighbours interpolate the long way round)."""
    curves = {}
    for fc in fcurves(action):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    flipped = 0
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]
        prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] = -keys[i][j].co[1]
                    keys[i][j].handle_left[1] = -keys[i][j].handle_left[1]
                    keys[i][j].handle_right[1] = -keys[i][j].handle_right[1]
                q = [-x for x in q]
                flipped += 1
            prev = q
        for fc in comps.values():
            fc.update()
    return flipped


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(T, fname))
        img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


body = material('Titan_A', 'ttn_a_basecolor_1k.png', 'ttn_normal_1k.png', 'ttn_metal_rough_1k.png')
head = material('TitanHead_A', 'ttn_head_basecolor_graded.png', 'ttn_head_normal_1k.png', 'ttn_head_metal_rough_1k.png')
head_flags = np.zeros(len(mesh.data.polygons), np.int32)
mesh.data.attributes['head'].data.foreach_get('value', head_flags)
mesh.data.materials.clear()
mesh.data.materials.append(body)
mesh.data.materials.append(head)
mesh.data.polygons.foreach_set('material_index', head_flags)

# palm sockets: the inward-facing (palm) skin of each hand, mid-height of the hand; the engine glows between the
# bound palms (the two-handed Cast pushes both palms forward)
me = mesh.data
centres = {}
for side, sx in (('Right', -1), ('Left', 1)):
    gi = mesh.vertex_groups[side + 'Hand'].index
    hand = [v for v in me.vertices if any(g.group == gi and g.weight > 0.99 for g in v.groups)]
    zs = np.array([(mesh.matrix_world @ v.co).z for v in hand]); zmid = (zs.min() + zs.max()) / 2
    palm = [mesh.matrix_world @ v.co for v in hand
            if abs((mesh.matrix_world @ v.co).z - zmid) < 0.03 and v.normal.dot(Vector((-sx, 0, 0))) > 0.6]
    centres[side] = sum(palm, Vector()) / len(palm)
    print('SOCKET Socket_Palm_' + side, [round(x, 3) for x in centres[side]], 'from', len(palm), 'palm vertices')
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
inv = rig.matrix_world.inverted()
for side, sx in (('Right', -1), ('Left', 1)):
    name = 'Socket_Palm_' + side
    if name in eb:
        eb.remove(eb[name])
    sb = eb.new(name); c = centres[side]
    sb.head = inv @ c; sb.tail = inv @ (c + Vector((-sx * 0.04, 0, 0))); sb.parent = eb[side + 'Hand']
    sb.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
centre = centres['Right']

for a in [a.name for a in mesh.data.attributes if a.name in ('part', 'uv_region', 'hid', 'head')]:
    mesh.data.attributes.remove(mesh.data.attributes[a])
print('JOINED', mesh.name, 'materials', [m.name for m in mesh.data.materials], 'tris',
      sum(len(p.vertices) - 2 for p in mesh.data.polygons))

KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Ranged', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
print('SIGNS', {a.name: fix_quaternion_signs(a) for a in bpy.data.actions})

act = bpy.data.actions['Walking']
rig.animation_data.action = act
if act.slots:
    rig.animation_data.action_slot = act.slots[0]
ys = []
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    bpy.context.scene.frame_set(f)
    ys.append((rig.matrix_world @ rig.pose.bones['LeftFoot'].head).y)
stride = (max(ys) - min(ys)) / 0.6
rig.animation_data.action = bpy.data.actions['Standing']
if bpy.data.actions['Standing'].slots:
    rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
bpy.context.scene.frame_set(0)
out = os.path.join(common.PROJECT, 'export', 'mm6_ttn_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
lo, hi = common.world_bounds([mesh])
info = {'glb': out, 'stride_length_m': stride, 'rest_bounds_m': [list(lo), list(hi)], 'socket': list(centre),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(common.PROJECT, 'export', 'export_info.json'), 'w'), indent=2)
print('EXPORTED', json.dumps(info))
