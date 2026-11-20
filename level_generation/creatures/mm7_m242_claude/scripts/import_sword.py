"""Meshy flamberge (meshy/sword_geometry_v1, Smart Topology from references_hd/sword_single.png) into work/props.blend
as 'SwordMesh' in prop space (as make_sword.py's): +Y along the grip toward the tip, origin at the grip centre, +X toward
the edge, +Z the flat normal; overall length SWORD_LEN. Axis = principal axis of the vertices; the tip is the end
farther from the guard (the widest 1 cm slice across the flat); flat normal = the least-variance axis of the blade
half; the grip centre = the middle of the narrow span between the guard and the pommel swell. Meshy's base colour,
normal and metal/roughness are kept (copied to textures/props/sword_*.png). Replaces the row-swept make_props_m150.py
sword (user, 2026-10-20: the curled quillons and the wavy blade are better from Meshy). Prints the grip radius for the
fist solve (R_HANDLE). Args: none"""
import bpy, os, json, shutil
import numpy as np
from mathutils import Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
SWORD_LEN = float(os.environ.get('SWORD_LEN', '1.15'))
job = R('meshy', 'sword_geometry_v1')
for k in ('base_color', 'normal', 'metallic', 'roughness'):
    shutil.copyfile(os.path.join(job, f'texture_urls_0_{k}.png'), R('textures', 'props', f'sword_{k}.png'))
bpy.ops.wm.open_mainfile(filepath=R('work', 'props.blend'))
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
U = np.linalg.svd(co - c, full_matrices=False)[2]
ax = U[0]; t = (co - c) @ ax
# width across the flat per 1 cm slice; the guard is the widest slice
side = U[1]; s = (co - c) @ side
L = t.max() - t.min(); bins = np.arange(t.min(), t.max() + 0.01 * L, 0.01 * L)
width = np.array([np.ptp(s[(t >= a) & (t < a + 0.01 * L)]) if ((t >= a) & (t < a + 0.01 * L)).sum() > 2 else 0 for a in bins])
g = bins[int(np.argmax(width))] + 0.005 * L
if g - t.min() < t.max() - g:                                  # guard near the low end -> the tip is the high end
    pass
else:
    ax = -ax; t = -t; g = -g
    bins = np.arange(t.min(), t.max() + 0.01 * L, 0.01 * L)
    width = np.array([np.ptp(s[(t >= a) & (t < a + 0.01 * L)]) if ((t >= a) & (t < a + 0.01 * L)).sum() > 2 else 0 for a in bins])
# grip: from the guard toward the pommel end (t.min()); its middle at 45 % of that span
grip_c_t = g - 0.45 * (g - t.min())
blade = co[t > g + 0.05 * L]
Vb = np.linalg.svd(blade - blade.mean(0), full_matrices=False)[2]
flat = Vb[2] - ax * (Vb[2] @ ax); flat /= np.linalg.norm(flat)
edge = np.cross(ax, flat)
origin = c + ax * grip_c_t
gs = (t > grip_c_t - 0.08 * L) & (t < grip_c_t + 0.08 * L)
rel = co[gs] - origin; rel -= np.outer(rel @ ax, ax)
k = SWORD_LEN / L
grip_r = float(np.median(np.linalg.norm(rel, axis=1))) * k
M = np.array([edge, ax, flat])                                  # rows: prop X, Y, Z
for v in mesh.data.vertices:
    p = np.array(tuple(v.co)) - origin
    v.co = tuple((M @ p) * k)
mesh.data.update()
SWORD_TRIS = int(os.environ.get('SWORD_TRIS', '700'))         # LOD0 budget (Smart Topology returned ~1.7k)
t0 = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
if t0 > SWORD_TRIS:
    # protect the blade's cutting edges (vertices on edges with a dihedral angle > 70 deg): plain collapse moved them
    # inward and notched the wavy silhouette
    import bmesh, math
    bm = bmesh.new(); bm.from_mesh(mesh.data)
    keep = {v.index for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(70) for v in e.verts}
    bm.free()
    vg = mesh.vertex_groups.new(name='_keep'); vg.add(sorted(keep), 1.0, 'REPLACE')
    dm = mesh.modifiers.new('dec', 'DECIMATE'); dm.decimate_type = 'COLLAPSE'; dm.ratio = SWORD_TRIS / t0
    dm.vertex_group = '_keep'; dm.invert_vertex_group = True
    bpy.ops.object.modifier_apply(modifier='dec')
    mesh.vertex_groups.remove(mesh.vertex_groups['_keep'])
mesh.name = mesh.data.name = 'SwordMesh'
for m in mesh.data.materials:
    m.name = 'Sword'
q = np.array([tuple(v.co) for v in mesh.data.vertices])
tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
print('SWORDIMPORT tris', tris, 'length', round(float(np.ptp(q[:, 1])), 3), 'tip y', round(float(q[:, 1].max()), 3),
      'guard width', round(float(np.ptp(q[np.abs(q[:, 1] - (g - grip_c_t) * k) < 0.02][:, 0])), 3),
      'grip radius cm', round(grip_r * 100, 2), 'flat thickness cm', round(float(np.ptp(q[q[:, 1] > 0.3][:, 2])) * 100, 2))
json.dump({'grip_radius_m': grip_r, 'tris': tris}, open(R('textures', 'props', 'sword_meshy.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
