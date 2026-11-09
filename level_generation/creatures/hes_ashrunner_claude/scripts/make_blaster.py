"""The Blaster Guy's pistol (native hgd attack/standing frames; HD prop reference references_hd/blaster.png), built
locally as a hard-surface prop (modelling guidelines: a few hundred triangles, quads triangulated by the exporter's
shorter diagonal, hard edges between the parts). Prop space: origin at the grip centre (the fist's tunnel centre),
+Z up the grip toward the barrel (the tunnel axis, thumb side), +Y along the barrel toward the muzzle, about 0.31 m
long (the grip at the rear, as the reference): receiver box with a rear knob, a 12-sided barrel with three bands and
a flared muzzle, a raked grip and a trigger guard. UVs: a planar side projection (Y -> u, Z -> v) fitted to the reference's alpha box, written by
blaster_texture.py into textures/props/blaster_uv.json (both sides share the side view). Writes work/blaster.blend
(object 'Blaster'; custom props muzzle = [x, y, z] in prop space). Args: none"""
import bpy, bmesh, os, sys, json, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new()
BARREL_Z = 0.072


def box(x0, x1, y0, y1, z0, z1, rake=0.0):
    """Axis box; rake (rad) leans its top toward +Y relative to its bottom (the grip)."""
    v = []
    for z in (z0, z1):
        dy = math.tan(rake) * (z - z0)
        for y in (y0, y1):
            for x in (x0, x1):
                v.append(bm.verts.new((x, y + dy, z)))
    q = lambda a, b, c, d: bm.faces.new((v[a], v[b], v[c], v[d]))
    q(0, 2, 3, 1); q(4, 5, 7, 6); q(0, 1, 5, 4); q(2, 6, 7, 3); q(0, 4, 6, 2); q(1, 3, 7, 5)


def tube(y0, y1, r0, r1, seg=12, caps=(True, True)):
    rings = []
    for y, r in ((y0, r0), (y1, r1)):
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / seg), y, BARREL_Z + r * math.sin(2 * math.pi * k / seg)))
                      for k in range(seg)])
    for k in range(seg):
        a, b = k, (k + 1) % seg
        bm.faces.new((rings[0][a], rings[0][b], rings[1][b], rings[1][a]))
    if caps[0]:
        bm.faces.new(list(reversed(rings[0])))
    if caps[1]:
        bm.faces.new(rings[1])


# dimensions from the reference silhouette (1448 px = 0.31 m; grip centre at column 190, row 680)
box(-0.017, 0.017, 0.000, 0.100, 0.045, 0.100)                     # receiver
box(-0.012, 0.012, -0.029, 0.002, 0.052, 0.094)                    # rear brass knob
tube(0.100, 0.255, 0.0160, 0.0160)                                 # barrel
for y0, y1 in ((0.118, 0.140), (0.168, 0.200), (0.232, 0.244)):    # copper and brass bands
    tube(y0, y1, 0.0200, 0.0200)
tube(0.255, 0.280, 0.0170, 0.0240)                                 # flared muzzle
box(-0.015, 0.015, -0.026, 0.026, -0.042, 0.047, rake=math.radians(15))   # raked wooden grip
# trigger guard: a bent strip under the receiver in front of the grip
pts = [(0.030, 0.045), (0.072, 0.040), (0.090, 0.024), (0.086, 0.010), (0.066, 0.006), (0.040, 0.012)]
prev = None
for k, (y, z) in enumerate(pts):                   # a 4-sided bar along the polyline (8 x 4 mm section)
    a, b = pts[max(k - 1, 0)], pts[min(k + 1, len(pts) - 1)]
    ty, tz = b[0] - a[0], b[1] - a[1]; L = math.hypot(ty, tz); ny, nz = -tz / L, ty / L
    cur = [bm.verts.new((x, y + ny * o, z + nz * o)) for (x, o) in ((-0.004, 0.0), (0.004, 0.0), (0.004, 0.004), (-0.004, 0.004))]
    if prev:
        for i in range(4):
            bm.faces.new((prev[i], prev[(i + 1) % 4], cur[(i + 1) % 4], cur[i]))
    prev = cur
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
me = bpy.data.meshes.new('Blaster'); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new('Blaster', me); bpy.context.scene.collection.objects.link(ob)
for p in me.polygons:
    p.use_smooth = False
uv = me.uv_layers.new(name='UVMap')
B = {'y': (-0.029, 0.281), 'z': (-0.042, 0.105)}                     # prop box mapped onto the reference's alpha box
for p in me.polygons:
    for li, vi in zip(p.loop_indices, p.vertices):
        c = me.vertices[vi].co
        uv.data[li].uv = ((c.y - B['y'][0]) / (B['y'][1] - B['y'][0]), (c.z - B['z'][0]) / (B['z'][1] - B['z'][0]))
ob['muzzle'] = [0.0, 0.280, BARREL_Z]
ob['uv_box'] = json.dumps(B)
mat = bpy.data.materials.new('Blaster_A'); mat.use_nodes = True
tex = os.path.join(HERE, 'textures', 'props', 'blaster.png')
if os.path.exists(tex):
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(tex)
    bsdf = next(x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    mat.node_tree.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.45; bsdf.inputs['Metallic'].default_value = 0.0
me.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'blaster.blend'))
print('BLASTER tris', sum(len(p.vertices) - 2 for p in me.polygons), 'textured', os.path.exists(tex))
