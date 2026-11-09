"""Runtime export: work/anim_v1.blend -> export/mm7_m298_lod0.glb (+ export/export_info.json).

One skinned mesh 'Ooze' (blob, pod with knob, globules), one material Ooze_A (2K base colour, 1K normal and ORM),
clips Standing, Walking, Running, Attack, Cast, Hit, Death, Dead, Fidget at 24 fps (quaternions made
sign-continuous), bone Socket_Spit on the knob's tip.
The pod and the globules have no texels of their own (mm6_ooz_claude route, but sampling the never-seen flat
underside, whose single large UV island Meshy painted with the same slime): each of their vertices takes the UV of a
point on the blob's underside, on a disc that lies inside one UV island (angle around the tube or sphere -> angle on
the disc, position along the tube or down the sphere -> radius), so no face spans an atlas seam. Args: none"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'anim_v1.blend'))
T = os.path.join(common.PROJECT, 'textures')
scene = bpy.context.scene
scene.render.fps = 24; scene.render.fps_base = 1
mesh, rig = bpy.data.objects['Ooze'], bpy.data.objects['Ooze_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = mesh.data
DIMS = json.loads(scene['ooze_dims'])
part = np.zeros(len(me.polygons), int)
me.attributes['part'].data.foreach_get('value', part)
uvl = me.uv_layers.active.data

# UV islands of the blob (faces connected through shared, unsplit UVs)
blob_faces = [p.index for p in me.polygons if part[p.index] == 0]
key = lambda li: (me.loops[li].vertex_index, round(uvl[li].uv[0], 5), round(uvl[li].uv[1], 5))
owner = {}
for fi in blob_faces:
    for li in me.polygons[fi].loop_indices:
        owner.setdefault(key(li), []).append(fi)
island = {}
for fi in blob_faces:
    if fi in island:
        continue
    stack, island[fi] = [fi], fi
    while stack:
        g = stack.pop()
        for li in me.polygons[g].loop_indices:
            for h in owner[key(li)]:
                if h not in island:
                    island[h] = fi
                    stack.append(h)
verts = [v.co.copy() for v in me.vertices]
tree = BVHTree.FromPolygons(verts, [tuple(me.polygons[f].vertices) for f in blob_faces])


def surface_uv(x, y):
    loc, nrm, idx, d = tree.ray_cast(Vector((x, y, -1.0)), Vector((0, 0, 1)), 5.0)    # the flat underside
    if loc is None:
        return None, None
    f = me.polygons[blob_faces[idx]]
    tri = [verts[i] for i in f.vertices[:3]]
    uvs = [Vector((*uvl[li].uv, 0)) for li in list(f.loop_indices)[:3]]
    uv = barycentric_transform(loc, *tri, *uvs)
    return (uv.x, uv.y), island[blob_faces[idx]]


def disc_radius(cx, cy):
    c = surface_uv(cx, cy)[1]
    if c is None:
        return 0.0, None
    best = 0.0
    for r in np.arange(0.01, 0.4, 0.01):
        if not all(surface_uv(cx + r * math.cos(a), cy + r * math.sin(a))[1] == c
                   for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)):
            break
        best = r
    return best, c


cands = [(disc_radius(x, y), x, y) for x in np.arange(-0.3, 0.31, 0.04) for y in np.arange(-0.3, 0.31, 0.04)]
(rmax, centre_island), cx, cy = max(cands, key=lambda c: c[0][0])
centre_uv = surface_uv(cx, cy)[0]
print('DISC radius', round(float(rmax), 3), 'island', centre_island, 'centre', round(cx, 2), round(cy, 2))


def map_faces(which, axis_of):
    """axis_of(vertex co) -> (angle about the part's axis, 0..1 from the disc centre outward)."""
    for p in me.polygons:
        if part[p.index] != which:
            continue
        vals = [axis_of(verts[me.loops[li].vertex_index]) for li in p.loop_indices]
        ref = vals[0][0]
        for li, (a, t) in zip(p.loop_indices, vals):
            while a - ref > math.pi:                   # keep each face's angles unwrapped
                a -= 2 * math.pi
            while a - ref < -math.pi:
                a += 2 * math.pi
            r = rmax * (0.12 + 0.85 * min(max(t, 0.0), 1.0))
            uv, _ = surface_uv(cx + r * math.cos(a), cy + r * math.sin(a))
            uvl[li].uv = uv if uv is not None else centre_uv


base = Vector(DIMS['pod_base'])
map_faces(1, lambda q: (math.atan2(q.y - base.y, q.x - base.x), (q.z - base.z) / DIMS['pod_len']))
gc = np.array([g[1] for g in DIMS['globs']])
gr = {i: g[2] for i, g in enumerate(DIMS['globs'])}


def glob_axis(q):
    k = int(np.argmin(((gc - np.array(tuple(q))) ** 2).sum(1)))
    c = Vector(gc[k])
    d = q - c
    zn = max(-1.0, min(1.0, d.z / (gr[k] * 0.62)))
    return math.atan2(d.y, d.x), (1 - zn) / 2


map_faces(2, glob_axis)

mat = bpy.data.materials.new('Ooze_A')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(name, cs):
    img = bpy.data.images.load(os.path.join(T, name))
    img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = img
    return n


nt.links.new(tex('ooze_basecolor_2k.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tex('ooze_normal_1k.png', 'Non-Color').outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(tex('ooze_metal_rough_1k.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
me.materials.clear()
me.materials.append(mat)
for a in [a.name for a in me.attributes if a.name == 'part']:
    me.attributes.remove(me.attributes[a])


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
        keys = [comps[i].keyframe_points for i in range(4)]
        prev = None
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
st = bpy.data.actions['Standing']
rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
scene.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.join(common.PROJECT, 'export'), exist_ok=True)
out = os.path.join(common.PROJECT, 'export', 'mm7_m298_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'export_master.blend'))
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])
info = {'glb': os.path.relpath(out, common.PROJECT), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
        'tris_by_part': {'blob': int(sum(len(me.polygons[i].vertices) - 2 for i in blob_faces)),
                         'pod': int(sum(1 for i in range(len(part)) if part[i] == 1)),
                         'globs': int(sum(1 for i in range(len(part)) if part[i] == 2))},
        'blob_rest_height_m': float(DIMS['top']), 'blob_width_m': 2 * float(DIMS['rx']),
        'blob_depth_m': 2 * float(DIMS['ry']), 'bind_pose_height_m (pod raised)': float(co[:, 2].max()),
        'fps': 24, 'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions},
        'uv_disc': {'radius_m': float(rmax), 'centre': [float(cx), float(cy)]}}
json.dump(info, open(os.path.join(common.PROJECT, 'export', 'export_info.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
