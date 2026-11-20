"""Fit the Meshy throne to the enthroned Hierarch and write its attachment GLB in the `Throne` joint's frame.

Seated body (Noble_Seated frame 0, work/hierarch/assembled.blend): the buttocks' lowest point under the pelvis and
the back surface at the chest. The throne (meshy/throne_v1) is oriented front to -Y, scaled to `--height` (body units),
its seat top (a ray down at the seat's middle) put under the buttocks, its backrest's front (a ray from the front at
chest height) just behind the back. Decimated to `--tris`. The attachment's coordinates are expressed in the Throne
node's glTF frame read from export/hierarch_lod0.glb (export_yup off, so they are written as they are).

Usage (Blender): fit_throne.py [--height 1.75] [--tris 4000] [--yaw 0]
Writes export/hes_hierarch_throne.glb, work/hierarch/throne_fit.blend, work/hierarch/throne_fit.json."""
import bpy, bmesh, sys, json, math, argparse, struct
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--height', type=float, default=1.75)
ap.add_argument('--tris', type=int, default=4000)
ap.add_argument('--yaw', type=float, default=0.0)
ap.add_argument('--gap', type=float, default=0.015)
a = ap.parse_args(argv)
P = Path(__file__).resolve().parents[1]
W = P / 'work/hierarch'
bpy.ops.wm.open_mainfile(filepath=str(W / 'assembled.blend'))
sc = bpy.context.scene
rig = bpy.data.objects['Rig']; noble = bpy.data.objects['Noble']
act = bpy.data.actions['Noble_Seated']
rig.animation_data.action = act
if act.slots:
    rig.animation_data.action_slot = act.slots[0]
sc.frame_set(0); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = noble.evaluated_get(dg).data
V = np.array([tuple(noble.matrix_world @ v.co) for v in ev.vertices])
pel = rig.matrix_world @ rig.pose.bones['B_Pelvis'].head
under = V[(np.abs(V[:, 0] - pel.x) < 0.14) & (np.abs(V[:, 1] - pel.y) < 0.14) & (V[:, 2] > pel.z - 0.2)]
seat_z = float(under[:, 2].min())
chest = V[(np.abs(V[:, 0]) < 0.1) & (V[:, 2] > pel.z + 0.25) & (V[:, 2] < pel.z + 0.45)]
back_y = float(chest[:, 1].max())
print('SEATED seat_z', round(seat_z, 3), 'back_y', round(back_y, 3), 'pelvis', [round(x, 3) for x in pel])

before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P / 'meshy/throne_v1/model_urls_glb.glb'))
new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in new:
    o.select_set(True)
bpy.context.view_layer.objects.active = new[0]
if len(new) > 1:
    bpy.ops.object.join()
th = bpy.context.view_layer.objects.active; th.name = 'Throne'; th.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.data.objects if o not in before and o != th]:
    bpy.data.objects.remove(o, do_unlink=True)
wb = bmesh.new(); wb.from_mesh(th.data); bmesh.ops.remove_doubles(wb, verts=wb.verts, dist=1e-5); wb.to_mesh(th.data); wb.free()
me = th.data
T = np.array([tuple(v.co) for v in me.vertices])
if a.yaw:
    c, s = math.cos(math.radians(a.yaw)), math.sin(math.radians(a.yaw))
    T = T @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T
lo, hi = T.min(0), T.max(0)
T = (T - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * (a.height / (hi[2] - lo[2]))
me.vertices.foreach_set('co', T.ravel()); me.update()
lo, hi = T.min(0), T.max(0)
bm = bmesh.new(); bm.from_mesh(me); bvh = BVHTree.FromBMesh(bm)
# seat: rays down over the front half, the highest hits below 45 % of the height are the seat
hits = []
for y in np.linspace(lo[1] + 0.15 * (hi[1] - lo[1]), lo[1] + 0.55 * (hi[1] - lo[1]), 9):
    for x in (-0.06, 0.0, 0.06):
        h = bvh.ray_cast(Vector((x, y, hi[2] + 0.1)), Vector((0, 0, -1)), 10)
        while h[0] is not None and h[0].z > 0.5 * a.height:
            h = bvh.ray_cast(h[0] - Vector((0, 0, 0.002)), Vector((0, 0, -1)), 10)
        if h[0] is not None:
            hits.append((y, h[0].z))
seat = max(z for _, z in hits)
back_hits = []
for z in np.linspace(seat + 0.2, seat + 0.4, 5):
    h = bvh.ray_cast(Vector((0, lo[1] - 0.2, z)), Vector((0, 1, 0)), 10)
    if h[0] is not None:
        back_hits.append(h[0].y)
backrest = min(back_hits)
print('THRONE seat', round(seat, 3), 'backrest front y', round(backrest, 3), 'box', lo.round(3), hi.round(3))
dz = seat_z - seat - 0.005
dy = (back_y + a.gap) - backrest
T[:, 2] += dz; T[:, 1] += dy
me.vertices.foreach_set('co', T.ravel()); me.update()
n0 = len(me.polygons)
bpy.context.view_layer.objects.active = th
for o in sc.objects:
    o.select_set(o == th)
if n0 > a.tris:
    m = th.modifiers.new('dec', 'DECIMATE'); m.ratio = a.tris / n0; m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
for mat in me.materials:
    b = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b:
        for l in list(b.inputs['Metallic'].links):
            mat.node_tree.links.remove(l)
        b.inputs['Metallic'].default_value = 0.0
    mat.name = 'Hierarch_Throne'
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'throne_fit.blend'))

# ---------------------------------------------------------------- the Throne node's glTF frame
raw = (P / 'export/hierarch_lod0.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
parent = {c: i for i, nd in enumerate(doc['nodes']) for c in nd.get('children', [])}


def local(nd):
    t = Vector(nd.get('translation', (0, 0, 0))); r = nd.get('rotation', (0, 0, 0, 1))
    s = Vector(nd.get('scale', (1, 1, 1)))
    return Matrix.LocRotScale(t, Quaternion((r[3], r[0], r[1], r[2])), s)


idx = next(i for i, nd in enumerate(doc['nodes']) if nd.get('name') == 'Throne')
M = Matrix.Identity(4); i = idx
while i is not None:
    M = local(doc['nodes'][i]) @ M; i = parent.get(i)
Minv = M.inverted()
TV = np.array([tuple(v.co) for v in me.vertices])
G = np.stack([TV[:, 0], TV[:, 2], -TV[:, 1]], 1)                  # Blender world -> glTF world
L = np.array([tuple(Minv @ Vector(p)) for p in G])
me.vertices.foreach_set('co', L.ravel()); me.update()
me.flip_normals() if np.linalg.det(np.array(Minv.to_3x3())) < 0 else None
for img in bpy.data.images:          # the cook takes PNG only (Meshy textures can be JPEG)
    if img.file_format != 'PNG' and img.size[0] > 0:
        img.file_format = 'PNG'
bpy.ops.export_scene.gltf(filepath=str(P / 'export/hes_hierarch_throne.glb'), export_format='GLB', use_selection=True,
                          export_yup=False, export_animations=False, export_image_format='AUTO')
stats = {'seat_z': seat_z, 'back_y': back_y, 'throne_tris': len(me.polygons), 'throne_height': a.height,
         'throne_node_world': [list(r) for r in M]}
(W / 'throne_fit.json').write_text(json.dumps(stats, indent=1))
print('THRONE', stats['throne_tris'], 'tris')
