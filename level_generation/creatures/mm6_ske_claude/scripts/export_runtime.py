"""Runtime export: work/rig_v3.blend -> export/mm6_ske_lod0.glb, one skinned mesh 'Skeleton' with materials
Skeleton_A (body set, 1K), SkeletonHead_A (head set, 1K; cranium, jaw, teeth; the eye spheres map
into a red swatch of it). The cutlass stays in the skinned mesh, 100 % on the 'Sword' bone (split into an
attachment later by tools/split_attachment.py); its faces map into the atlas swatches by sword_class. Clips: Standing,
Walking, Running, Attack, Hit, Death, Dead, Fidget (quaternion keys made sign-continuous).
Args: none (paths from the project)."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
T = os.path.join(common.PROJECT, 'textures')
mesh, rig = bpy.data.objects['Skeleton'], bpy.data.objects['Skeleton_Rig']
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


def fix_quaternion_signs(action):
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
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img
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


body = material('Skeleton_A', 'ske_basecolor_1k.png', 'ske_normal_1k.png', 'ske_metal_rough_1k.png')
head = material('SkeletonHead_A', 'ske_head_basecolor_1k.png', 'ske_head_normal_1k.png', 'ske_head_metal_rough_1k.png')
old = [m.name for m in mesh.data.materials]
slot = {'Bone': 0, 'Sword': 0, 'Head': 1, 'Eyes': 1}
idx = [slot[old[p.material_index]] for p in mesh.data.polygons]
eye_faces = {p.index for p in mesh.data.polygons if old[p.material_index] == 'Eyes'}
mesh.data.materials.clear()
for m in (body, head):
    mesh.data.materials.append(m)
mesh.data.polygons.foreach_set('material_index', idx)

# cutlass faces -> swatches
SW = json.load(open(os.path.join(T, 'ske_sword_swatches.json')))
CLS = ['blade', 'edge', 'brass', 'grip']
sc = np.zeros(len(mesh.data.polygons), np.int32)
pv = np.zeros(len(mesh.data.vertices), np.int32); mesh.data.attributes['piece'].data.foreach_get('value', pv)
if 'sword_class' in mesh.data.attributes:
    mesh.data.attributes['sword_class'].data.foreach_get('value', sc)
uvl = mesh.data.uv_layers['UVMap'].data
counts = {}
for p in mesh.data.polygons:
    if pv[p.vertices[0]] != 999:
        continue
    name = CLS[sc[p.index]]
    u, v, r = SW[name]
    for k, li in enumerate(p.loop_indices):
        ang = 2.0 * np.pi * k / len(p.loop_indices)
        uvl[li].uv = (u + r * np.cos(ang), v + r * np.sin(ang))
    counts[name] = counts.get(name, 0) + 1
eu, ev, er = SW['eyes']
for p in mesh.data.polygons:
    if p.index in eye_faces:
        for k, li in enumerate(p.loop_indices):
            ang = 2.0 * np.pi * k / len(p.loop_indices)
            uvl[li].uv = (eu + er * np.cos(ang), ev + er * np.sin(ang))
print('SWORD faces', counts, 'eye faces', len(eye_faces))
for a in [a.name for a in mesh.data.attributes if a.name in ('piece', 'sword_class')]:
    mesh.data.attributes.remove(mesh.data.attributes[a])
print('JOINED materials', [m.name for m in mesh.data.materials], 'tris',
      sum(len(p.vertices) - 2 for p in mesh.data.polygons))

KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
print('SIGNS', {a.name: fix_quaternion_signs(a) for a in bpy.data.actions})
stride = json.loads(bpy.context.scene.get('ske_stride', '{}'))
st = bpy.data.actions['Standing']
rig.animation_data.action = st
if getattr(st, 'slots', None) and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
bpy.context.scene.frame_set(0)
os.makedirs(os.path.join(common.PROJECT, 'export'), exist_ok=True)
out = os.path.join(common.PROJECT, 'export', 'mm6_ske_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
lo, hi = common.world_bounds([mesh])
info = {'glb': out, 'stride_m': stride, 'rest_bounds_m': [list(lo), list(hi)],
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(common.PROJECT, 'export', 'export_info.json'), 'w'), indent=2)
print('EXPORTED', json.dumps(info))
