"""Runtime export: work/rig_v7.blend -> export/mm6_gua_lod0.glb (one skinned mesh 'Guard', materials Guard_A (body +
halberd) and GuardHead_A (head texture set)).
 - Body maps from prepare_textures.py: base colour 1024, normal 1024, ORM 1024 (R AO, G roughness, B metallic).
 - Head faces (attribute `head`, claude_shared/head_texture_split.py) keep their own 0..1 UVs and the head maps from
   compose_head_set.py.
 - The halberd joins the mesh (100 % on the Halberd bone): its faces are projected into the swatches of
   textures/halberd_swatches.json in the Halberd bone's rest frame (Y shaft, Z blade normal, X spike side): wood
   cylindrical (u along the shaft, v around it), iron planar on the blade plane, gem at its swatch centre.
 - Game clips: Standing, Walking, Running, Attack, Hit, Death, Dead (quaternion keys sign-continuous).
 - Walk stride from the planted-foot travel, written to export/export_info.json."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v7.blend'))
import gua_rig as gr
T = os.path.join(common.PROJECT, 'textures')
mesh, hal, rig = bpy.data.objects['Guard'], bpy.data.objects['Halberd'], bpy.data.objects['Guard_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


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


body = material('Guard_A', 'gua_a_basecolor_1k.png', 'gua_normal_1k.png', 'gua_metal_rough_1k.png')
head = material('GuardHead_A', 'gua_head_basecolor_graded.png', 'gua_head_normal_1k.png', 'gua_head_metal_rough_1k.png')
head_flags = np.zeros(len(mesh.data.polygons), np.int32)
mesh.data.attributes['head'].data.foreach_get('value', head_flags)
mesh.data.materials.clear()
mesh.data.materials.append(body)
mesh.data.materials.append(head)
mesh.data.polygons.foreach_set('material_index', head_flags)

# body UVs follow the squeezed atlas (head faces keep their own 0..1 layout)
SW = json.load(open(os.path.join(T, 'halberd_swatches.json')))
uvb = mesh.data.uv_layers.active.data
for p in mesh.data.polygons:
    if not head_flags[p.index]:
        for li in p.loop_indices:
            uvb[li].uv = (uvb[li].uv[0] * SW['body_u'], uvb[li].uv[1])

# halberd UVs into the strip (prepare_textures.py), in the Halberd bone's rest frame: Y shaft (+ toward the gem),
# X = -(spike side) of the traced outline, so the traced (u down from the gem, v across) is (L - y_butt, -x) / H
hb = rig.data.bones['Halberd']
Minv = (rig.matrix_world @ hb.matrix_local).inverted()
hm = hal.data
if not hm.uv_layers:
    hm.uv_layers.new(name=mesh.data.uv_layers.active.name)
uvl = hm.uv_layers.active.data
part = np.zeros(len(hm.polygons), int)
hm.attributes['part'].data.foreach_get('value', part)
loc = {v.index: Minv @ (hal.matrix_world @ v.co) for v in hm.vertices}
L, GRIP, H = gr.L, gr.GRIP_FROM_FOOT, hal['body_height']
R_SHAFT = max(math.hypot(q.x, q.z) for q in loc.values() if 0.3 < (q.y + GRIP) / L < 0.6)


def into(name, fu, fv):
    a, b, c, d = SW[name]
    return (a + (c - a) * min(max(fu, 0.01), 0.99), b + (d - b) * min(max(fv, 0.01), 0.99))


for p in hm.polygons:
    centre = sum((loc[i] for i in p.vertices), Vector()) / len(p.vertices)
    plate = part[p.index] == 1 and math.hypot(centre.x, centre.z) > 1.6 * R_SHAFT
    for li in p.loop_indices:
        q = loc[hm.loops[li].vertex_index]
        frac = (q.y + GRIP) / L                                  # 0 butt .. 1 gem
        if part[p.index] == 2:
            uvl[li].uv = into('gem', 0.5, 0.5)
        elif plate:                                              # blade plates: axe / spike cells, traced frame
            u, v = (L - (q.y + GRIP)) / H, -q.x / H
            name = 'axe' if -centre.x / H < 0 else 'spike'
            U0, U1, V0, V1 = SW['blade_parts_h'][name]
            uvl[li].uv = into(name, (v - V0) / (V1 - V0), 1 - (u - U0) / (U1 - U0))
        elif part[p.index] == 1 and (centre.y + GRIP) / L < 0.5:  # butt cap: iron
            uvl[li].uv = into('iron', (math.atan2(q.z, q.x) / (2 * math.pi)) % 1.0, 0.5)
        elif part[p.index] == 1 and 0.725 < (centre.y + GRIP) / L < 0.76:   # the native blue band under the blade
            uvl[li].uv = into('band', (math.atan2(q.z, q.x) / (2 * math.pi)) % 1.0, 0.5)
        elif part[p.index] == 1:                                 # socket under the head: wood, as in the native
            uvl[li].uv = into('wood', (math.atan2(q.z, q.x) / (2 * math.pi)) % 1.0, frac)
        else:                                                    # wood
            uvl[li].uv = into('wood', (math.atan2(q.z, q.x) / (2 * math.pi)) % 1.0, frac)
hm.materials.clear()
hm.materials.append(body)
for o in bpy.data.objects:
    o.select_set(o in (mesh, hal))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
for a in [a.name for a in mesh.data.attributes if a.name in ('part', 'uv_region', 'hid', 'head')]:
    mesh.data.attributes.remove(mesh.data.attributes[a])
print('JOINED', mesh.name, 'materials', [m.name for m in mesh.data.materials], 'tris',
      sum(len(p.vertices) - 2 for p in mesh.data.polygons))

KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
for a in bpy.data.actions:
    gr.fix_quaternion_signs(a)

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
out = os.path.join(common.PROJECT, 'export', 'mm6_gua_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
lo, hi = common.world_bounds([mesh])
info = {'glb': out, 'stride_length_m': stride, 'rest_bounds_m': [list(lo), list(hi)],
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(common.PROJECT, 'export', 'export_info.json'), 'w'), indent=2)
print('EXPORTED', json.dumps(info))
