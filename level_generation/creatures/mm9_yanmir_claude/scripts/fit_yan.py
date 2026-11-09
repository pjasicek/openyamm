"""Step A: Meshy body -> symmetric (left half mirrored), scaled to MM9 Yanmir in true handedness, Blender axes, creature facing -Y.
The mesh keeps Meshy's A-pose: MM9's bind is a stride (right leg forward with the heel up, right arm bent round the staff), so the
rig takes MM9's frames turned onto our limbs (rig_yan.py, as mm9_highwayman_claude's fit_hw.py), not the mesh onto MM9's pose.
Scale: x and y by SC (MM9's shoulder and hip widths); z by a monotone map through MM9's LEFT joint heights (sole, ankle, knee, hip),
then SC above the hip: MM9's legs are about 1.35 x longer against the torso than Meshy's. Writes the shells for the wrap too.
Writes <out> (object Body, vertex attribute part 0) and <out>.zmap.json. Args: <meshy glb> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
MESHY, OUT = sys.argv[sys.argv.index('--') + 1:]
SC, OY = 2.55, 0.0
NECK_Z = 0.80      # MM9 z of the neck base: Meshy's head pieces start above it
# Meshy normalised z (sole -0.5) -> MM9 z (Blender, our 0.3 scale): sole, ankle, knee, hip; above the hip the slope is SC
ZK = [(-0.500, -1.449), (-0.445, -1.227), (-0.290, -0.695), (-0.100, -0.080)]


def pchip_map(z):
    """monotone cubic through the knots, linear with slope SC above the last knot (C1 at the hip)"""
    x = np.array([k[0] for k in ZK] + [0.0]); y = np.array([k[1] for k in ZK] + [ZK[-1][1] + 0.1 * SC])
    h = np.diff(x); d = np.diff(y) / h
    m = np.zeros_like(y); m[0] = d[0]; m[-1] = SC
    for k in range(1, len(x) - 1):
        m[k] = 0.0 if d[k - 1] * d[k] <= 0 else (2 * h[k] + h[k - 1] + h[k] + 2 * h[k - 1]) / (
            (2 * h[k] + h[k - 1]) / d[k - 1] + (h[k] + 2 * h[k - 1]) / d[k])
    out = np.empty_like(z)
    hi = z >= x[-1]
    out[hi] = y[-1] + (z[hi] - x[-1]) * SC
    lo = z <= x[0]
    out[lo] = y[0] + (z[lo] - x[0]) * d[0]
    mid = ~hi & ~lo
    k = np.clip(np.searchsorted(x, z[mid]) - 1, 0, len(x) - 2)
    t = (z[mid] - x[k]) / h[k]
    h00 = 2 * t ** 3 - 3 * t ** 2 + 1; h10 = t ** 3 - 2 * t ** 2 + t; h01 = -2 * t ** 3 + 3 * t ** 2; h11 = t ** 3 - t ** 2
    out[mid] = h00 * y[k] + h10 * h[k] * m[k] + h01 * y[k + 1] + h11 * h[k] * m[k + 1]
    return out


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MESHY)
body = next(o for o in bpy.data.objects if o.type == 'MESH')
Mw = body.matrix_world.copy(); body.parent = None; body.matrix_world = Mw; body.name = 'Body'
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o, do_unlink=True)
me = body.data
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
P = np.array([v.co[:] for v in bm.verts])
z0 = P[:, 2].min(); P[:, 2] += -0.5 - z0          # sole at -0.5 exactly
Z = pchip_map(P[:, 2])
for v, p, z in zip(bm.verts, P, Z): v.co = Vector((p[0] * SC, p[1] * SC + OY, z))
seen = set(); comps = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cc = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y); cc.append(y)
    comps.append(cc)
comps.sort(key=len, reverse=True); print('COMPS', [len(c) for c in comps][:12])
# Meshy returned the figure as 28 layered shells (torso + arms, hips + legs, mantle, belt, bracers, knee plates, sleeves, head pieces).
# Keep the main piece and every piece below the neck; the head is replaced by the head-only model (union_yan.py). Then one closed
# skin by the voxel wrap (wrap_bf.py + body_close.py), so no layer floats or clips through another under skinning.
drop = [v for c in comps[1:] for v in c if np.mean([w.co.z for w in c]) > NECK_Z or len(c) < 10]
bmesh.ops.delete(bm, geom=drop, context='VERTS')
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-4)
bmesh.ops.reverse_faces(bm, faces=[f for f in bm.faces if f.calc_center_median().x < 0])
bd = [e for e in bm.edges if e.is_boundary]; print('BOUNDARY', len(bd))
if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=60)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
pa = me.attributes.new('part', 'INT', 'POINT')
Q = np.array([v.co[:] for v in me.vertices])
for p in me.polygons: p.use_smooth = True
print('floor', Q[:, 2].min().round(4), 'bbox', Q.min(0).round(3), Q.max(0).round(3), 'verts', len(Q))
json.dump({'SC': SC, 'OY': OY, 'knots': ZK}, open(OUT + '.zmap.json', 'w'))
tri = np.array([p.vertices[:] for p in me.polygons if len(p.vertices) == 3])
np.savez(OUT + '.shells.npz', co=Q, tri=tri, part=np.zeros(len(Q), int))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FITTED', len(Q))
