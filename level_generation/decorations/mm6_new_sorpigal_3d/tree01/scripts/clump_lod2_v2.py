"""v2 LOD2 clump cards, step 3: replaces Tree_LOD2's leaf faces in work_v2/tree.blend with clump cards (material
LeavesFar, atlas from make_clump_atlas_v2.py). Per clump: three near-vertical cards 60 degrees apart (random yaw,
+-12 degree tilt) with a side-view cell and one near-horizontal card (raised 0.25 r, +-15 degree tilt) with the
top-view cell, each FRAME x radius wide, centred on the clump; the variant alternates by clump. COLOR_0 per card = the clump's mean sky occlusion x its tint x TONE[2]; vertex normals
are the card normals (the atlas normal map carries the clump's shading)."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work_v2')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, 'tree.blend'))
data = json.load(open(os.path.join(W, 'clumps.json')))
clumps = data['clumps']; tone = float(data['tone']['2'])
FRAME = 3.0
SHRINK = 0.92                        # cards slightly inside the clump's fringe: the crossed set reads a bit larger
rng = np.random.default_rng(2203)
tree = bpy.data.objects['Tree_LOD2']; me = tree.data
leaf_index = [i for i, m in enumerate(me.materials) if m.name == 'Leaves'][0]
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == leaf_index], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
far = bpy.data.materials['Leaves'].copy(); far.name = 'LeavesFar'
nt = far.node_tree
for n in nt.nodes:
    if n.type == 'TEX_IMAGE':
        name = 'clumps_basecolor.png' if n.image.name.startswith('leaves_base') else 'clumps_normal.png'
        img = bpy.data.images.load(os.path.join(W, name))
        img.colorspace_settings.name = 'sRGB' if name.startswith('clumps_base') else 'Non-Color'
        n.image = img
for key in ('openyamm_wind', 'openyamm_translucency'):
    far[key] = bpy.data.materials['Leaves'][key]
me.materials.append(far); far_index = len(me.materials) - 1
uvl = bm.loops.layers.uv.verify()
colour_layer = bm.verts.layers.float_color.get('Color')
cards = 0
for ci, c in enumerate(clumps):
    centre = Vector(c['centre']); s = FRAME * c['radius'] * SHRINK / 2
    occ = np.array(c['tint']) * c['sky'] * tone
    variant = ci % 2
    yaw = rng.uniform(0, math.pi)
    # jittered tilts and a raised top card keep the cards' intersection lines from lining up into a visible grid
    planes = []
    for k in range(3):
        right = Vector((math.cos(yaw + k * math.pi / 3), math.sin(yaw + k * math.pi / 3), 0.0))
        up = Matrix.Rotation(rng.uniform(-0.21, 0.21), 3, right) @ Vector((0, 0, 1))
        planes.append((right, up, 0, Vector((0, 0, 0))))
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0)); up = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    tilt = Matrix.Rotation(rng.uniform(-0.26, 0.26), 3, right)
    planes.append((right, tilt @ up, 1, Vector((0, 0, 0.25 * c['radius']))))
    for right, up, row, offset in planes:
        middle = centre + offset
        corners = [middle - right * s - up * s, middle + right * s - up * s, middle + right * s + up * s,
                   middle - right * s + up * s]
        vs = [bm.verts.new(q) for q in corners]
        f = bm.faces.new(vs); f.material_index = far_index; f.smooth = True
        u0, v0 = 0.5 * variant, 0.5 * (1 - row)
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + 0.5 * du, v0 + 0.5 * dv)
        for v in vs:
            v[colour_layer] = (float(occ[0]), float(occ[1]), float(occ[2]), 1.0)
        cards += 1
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free()
# vertex normals = card normals for the clump cards (custom normals were set per vertex for the old leaves)
normals = []
for v in me.vertices:
    normals.append(None)
poly_normal = {}
for p in me.polygons:
    for vi in p.vertices:
        poly_normal[vi] = (p.normal.copy(), p.material_index)
custom = []
for v in me.vertices:
    n, mi = poly_normal[v.index]
    custom.append(n if mi == far_index else v.normal.copy())
me.normals_split_custom_set_from_vertices(custom)
print('LOD2 clump cards', cards, 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'tree.blend'))
