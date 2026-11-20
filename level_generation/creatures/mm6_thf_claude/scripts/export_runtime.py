"""Runtime export: work/rig_v3.blend -> export/mm6_thf_lod0.glb (one skinned mesh 'Thief', materials Thief_A (body
set) and ThiefHead_A (head texture set)), after mm6_ttn1_claude/scripts/export_runtime.py.
 - Body maps from prepare_textures.py: base colour 1024, normal 1024, ORM 1024 (R AO, G roughness, B metallic).
 - Head faces (attribute `head`, claude_shared/head_texture_split.py) keep their own 0..1 UVs and the head maps from
   compose_head_set.py (hood darkened to the body cloak by head_tiers.py).
 - Daggers stay in the skinned mesh (100 % on DaggerL/DaggerR, scaled to 0.001 outside the Attack), UVs into the
   atlas swatches. No spells, so no palm sockets.
 - Game clips: Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget (quaternion keys sign-continuous).
 - Walk stride from the planted-foot travel, written to export/export_info.json."""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
T = os.path.join(common.PROJECT, 'textures')
mesh, rig = bpy.data.objects['Thief'], bpy.data.objects['Thief_Rig']
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


body = material('Thief_A', 'thf_a_basecolor_1k.png', 'thf_normal_1k.png', 'thf_metal_rough_1k.png')
head = material('ThiefHead_A', 'thf_head_basecolor_graded.png', 'thf_head_normal_1k.png', 'thf_head_metal_rough_1k.png')
head_flags = np.zeros(len(mesh.data.polygons), np.int32)
mesh.data.attributes['head'].data.foreach_get('value', head_flags)
mesh.data.materials.clear()
mesh.data.materials.append(body)
mesh.data.materials.append(head)
mesh.data.polygons.foreach_set('material_index', head_flags)

# daggers: every face into one atlas swatch (prepare_textures.py), by its position along the dagger bone (rest):
# pommel and guard dark iron, grip leather, blade steel
SW = json.load(open(os.path.join(T, 'thf_dagger_swatches.json')))
parts = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(mesh.data.polygons), np.int32); mesh.data.attributes['part'].data.foreach_get('value', part)
GRIP_L = 0.085
uvl = mesh.data.uv_layers.active.data
counts = {}
for side in ('L', 'R'):
    b = rig.data.bones['Dagger' + side]
    h0 = rig.matrix_world @ b.head_local; ax = (rig.matrix_world @ b.tail_local - h0).normalized()
    for p in mesh.data.polygons:
        if parts[part[p.index]] != 'Dagger':
            continue
        c = mesh.matrix_world @ p.center
        if (c - h0).length > 0.3 or ((c.x > 0) != (h0.x > 0)):
            continue
        s_ = (c - h0).dot(ax)
        name = 'blade' if s_ > GRIP_L / 2 + 0.012 else ('grip' if -GRIP_L / 2 < s_ < GRIP_L / 2 else 'iron')
        u, v, r = SW[name]
        for k, li in enumerate(p.loop_indices):
            ang = 2.0 * np.pi * k / len(p.loop_indices)
            uvl[li].uv = (u + r * np.cos(ang), v + r * np.sin(ang))
        counts[name] = counts.get(name, 0) + 1
print('DAGGER faces', counts)
for a in [a.name for a in mesh.data.attributes if a.name in ('part', 'uv_region', 'hid', 'head')]:
    mesh.data.attributes.remove(mesh.data.attributes[a])
print('JOINED', mesh.name, 'materials', [m.name for m in mesh.data.materials], 'tris',
      sum(len(p.vertices) - 2 for p in mesh.data.polygons))

KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
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
out = os.path.join(common.PROJECT, 'export', 'mm6_thf_lod0.glb')
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
