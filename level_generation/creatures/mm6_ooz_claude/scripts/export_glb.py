"""Export the ooze master (work/anim_v1.blend) to export/mm6_ooz_lod0.glb: material Ooze_A, all clips.

The pod has no texels of its own: each pod vertex takes the UV of a point on the blob's top surface, on a disc around
the pod's base (angle around the tube -> angle on the disc, position along the tube -> radius), restricted to one UV
island so no pod face spans an atlas seam."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'anim_v1.blend'))
T = os.path.join(common.PROJECT, 'textures')
mesh, rig = bpy.data.objects['Ooze'], bpy.data.objects['Ooze_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = mesh.data
DIMS = dict(bpy.context.scene['ooz_dims'])
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
base = Vector(DIMS['pod_base'])


def surface_uv(x, y):
    loc, nrm, idx, d = tree.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)), 5.0)
    if loc is None:
        return None, None
    f = me.polygons[blob_faces[idx]]
    from mathutils.geometry import barycentric_transform
    tri = [verts[i] for i in f.vertices[:3]]
    uvs = [Vector((*uvl[li].uv, 0)) for li in list(f.loop_indices)[:3]]
    uv = barycentric_transform(loc, *tri, *uvs)
    return (uv.x, uv.y), island[blob_faces[idx]]


# the top-surface point with the largest disc whose samples all fall in one UV island (the island under the pod's base
# is small; only the sampling centre moves, the pod stays where it is)
def disc_radius(cx, cy):
    c = surface_uv(cx, cy)[1]
    if c is None:
        return 0.0, None
    best = 0.0
    for r in np.arange(0.01, 0.25, 0.01):
        if not all(surface_uv(cx + r * math.cos(a), cy + r * math.sin(a))[1] == c
                   for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)):
            break
        best = r
    return best, c


cands = [(disc_radius(x, y), x, y) for x in np.arange(-0.3, 0.31, 0.04) for y in np.arange(-0.4, 0.41, 0.04)]
(rmax, centre_island), cx, cy = max(cands, key=lambda c: c[0][0])
centre = Vector((cx, cy, 0))
centre_uv = surface_uv(cx, cy)[0]
print('POD disc radius', round(float(rmax), 3), 'island', centre_island, 'centre', round(cx, 2), round(cy, 2))
pod_len = DIMS['pod_len']
for p in me.polygons:
    if part[p.index] != 1:
        continue
    angs = [math.atan2(verts[me.loops[li].vertex_index].y - base.y, verts[me.loops[li].vertex_index].x - base.x)
            for li in p.loop_indices]
    ref = angs[0]
    for li, a in zip(p.loop_indices, angs):
        while a - ref > math.pi:                       # keep each face's angles unwrapped (no seam across the disc)
            a -= 2 * math.pi
        while a - ref < -math.pi:
            a += 2 * math.pi
        q = verts[me.loops[li].vertex_index]
        t = min(max((q.z - base.z) / pod_len, 0.0), 1.0)
        r = rmax * (0.15 + 0.85 * t)
        uv, isl = surface_uv(centre.x + r * math.cos(a), centre.y + r * math.sin(a))
        uvl[li].uv = uv if uv is not None else centre_uv

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


nt.links.new(tex('ooz_a_basecolor_graded.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tex('ooz_normal_1k.png', 'Non-Color').outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(tex('ooz_metal_rough_1k.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
me.materials.clear()
me.materials.append(mat)
for a in [a.name for a in me.attributes if a.name == 'part']:
    me.attributes.remove(me.attributes[a])
rig.animation_data.action = bpy.data.actions['Standing']
if bpy.data.actions['Standing'].slots:
    rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
bpy.context.scene.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
out = os.path.join(common.PROJECT, 'export', 'mm6_ooz_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out, {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions})
