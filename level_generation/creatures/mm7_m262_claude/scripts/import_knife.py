"""Meshy curved knife (meshy/knife_geometry_v1, Smart Topology from references_hd/knife_single.png) into
work/props.blend as 'SwordMesh' (the export's prop name for the right-hand weapon) in prop space: +Y along the GRIP
toward the blade, origin at the grip centre, +X toward the cutting edge, +Z the blade's flat normal; overall length
KNIFE_LEN. The blade curves, so the axis is the principal axis of the HANDLE end only: the pommel end of the whole
mesh's principal axis is the end with the thicker slice; the handle = the first 38 % of the length from it; the guard
= the widest slice (across the blade flat) within 50 % of the length; the grip centre = midway between the pommel
centre and the guard. The cutting edge is the blade's concave side (the native's notched back is the convex spine):
+X points from the grip axis toward the blade's centroid. Decimated to KNIFE_TRIS with the sharp edges protected.
Meshy's maps are kept (textures/props/sword_*.png, the names compose and export expect). Args: none"""
import bpy, bmesh, os, json, shutil, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
LEN, TRIS = float(os.environ.get('KNIFE_LEN', '0.38')), int(os.environ.get('KNIFE_TRIS', '700'))
job = R('meshy', 'knife_geometry_v1')
os.makedirs(R('textures', 'props'), exist_ok=True)
for k in ('base_color', 'normal', 'metallic', 'roughness'):
    shutil.copyfile(os.path.join(job, f'texture_urls_0_{k}.png'), R('textures', 'props', f'sword_{k}.png'))
pb = R('work', 'props.blend')
if os.path.exists(pb):
    bpy.ops.wm.open_mainfile(filepath=pb)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
old = bpy.data.objects.get('SwordMesh')
if old is not None:
    bpy.data.objects.remove(old, do_unlink=True)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(job, 'model_urls_glb.glb'))
new = [o for o in bpy.data.objects if o not in before]
mesh = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
for o in new:
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices]); c = co.mean(0)
U = np.linalg.svd(co - c, full_matrices=False)[2]; u = U[0]; t = (co - c) @ u; L = np.ptp(t)


def thick(sel):
    p = co[sel] - co[sel].mean(0); p -= np.outer(p @ u, u)
    s = np.linalg.svd(p, full_matrices=False)[1] if len(p) > 3 else np.zeros(2)
    return float(s[1]) if len(s) > 1 else 0.0


lo = t < t.min() + 0.06 * L; hi = t > t.max() - 0.06 * L
if thick(hi) > thick(lo):
    u = -u; t = -t
t0 = t.min()
hsel = t < t0 + 0.38 * L
h = np.linalg.svd(co[hsel] - co[hsel].mean(0), full_matrices=False)[2][0]
if h @ u < 0:
    h = -h
th = (co - co[hsel].mean(0)) @ h; th -= th.min()
perp = co - np.outer(co @ h, h)
Lh = th.max()
bins = np.arange(0, 0.5 * Lh, 0.01 * Lh)
width = []
for a in bins:
    sl = (th >= a) & (th < a + 0.01 * Lh)
    width.append(float(np.ptp(np.linalg.norm(perp[sl] - perp[sl].mean(0), axis=1))) if sl.sum() > 3 else 0.0)
g = bins[int(np.argmax(width))] + 0.005 * Lh
pom = co[th < 0.04 * Lh].mean(0)
gc = co[np.abs(th - g) < 0.01 * Lh].mean(0)
origin = (pom + gc) / 2
blade = co[th > g + 0.05 * Lh]
bc = blade.mean(0) - origin; edge = bc - h * (bc @ h); edge /= np.linalg.norm(edge)
flat = np.cross(edge, h)
k = LEN / L
gs = (th > 0.1 * Lh) & (th < g - 0.03 * Lh)
rel = co[gs] - origin; rel -= np.outer(rel @ h, h)
grip_r = float(np.median(np.linalg.norm(rel, axis=1))) * k
M = np.array([edge, h, flat])
for v in mesh.data.vertices:
    v.co = tuple((M @ (np.array(tuple(v.co)) - origin)) * k)
mesh.data.update()
t0n = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
if t0n > TRIS:
    bm = bmesh.new(); bm.from_mesh(mesh.data)
    keep = {v.index for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(70) for v in e.verts}
    bm.free()
    vg = mesh.vertex_groups.new(name='_keep'); vg.add(sorted(keep), 1.0, 'REPLACE')
    dm = mesh.modifiers.new('dec', 'DECIMATE'); dm.decimate_type = 'COLLAPSE'; dm.ratio = TRIS / t0n
    dm.vertex_group = '_keep'; dm.invert_vertex_group = True
    bpy.ops.object.modifier_apply(modifier='dec')
    mesh.vertex_groups.remove(mesh.vertex_groups['_keep'])
mesh.name = mesh.data.name = 'SwordMesh'
for m in mesh.data.materials:
    m.name = 'Sword'
q = np.array([tuple(v.co) for v in mesh.data.vertices])
tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print('KNIFEIMPORT tris', t0n, '->', tris, 'length', round(float(np.ptp(q[:, 1])), 3), 'tip y', round(float(q[:, 1].max()), 3),
      'pommel y', round(float(q[:, 1].min()), 3), 'grip radius cm', round(grip_r * 100, 2), 'edge side x range',
      round(float(q[:, 0].min()), 3), round(float(q[:, 0].max()), 3))
json.dump({'grip_radius_m': grip_r, 'tris': tris}, open(R('textures', 'props', 'sword_meshy.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=pb)
