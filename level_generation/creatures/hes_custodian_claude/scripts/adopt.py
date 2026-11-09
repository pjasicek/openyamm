"""Adopt the Meshy retexture's own mesh (meshy/custodian_retexture_v1/model_urls_glb.glb): its maps are painted on ITS
UVs (the retexture may move UVs and weld seams), so the returned mesh is the geometry from here on (as
hes_turrets_claude/scripts/adopt_retexture.py). It comes back normalised (longest side 2, centred): scaled and moved
back onto work/uv.blend's frame; each face takes the `part` of the nearest face of our mesh, each vertex the weights
(vertex groups) of our nearest vertex; shading as prepare_uv.py (smooth, sharp over SHARP_DEG).
Writes work/tex.blend (object Custodian, face attribute `part`, vertex groups, custom property `joints`). Args: none."""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc  # noqa: E402
SHARP_DEG = 38.0

bpy.ops.wm.open_mainfile(filepath=cc.path('work/uv.blend'))
ours = bpy.data.objects['Custodian']
joints = ours['joints']
oco = np.array([v.co[:] for v in ours.data.vertices])
opart = np.zeros(len(ours.data.polygons), int); ours.data.attributes['part'].data.foreach_get('value', opart)
gnames = [g.name for g in ours.vertex_groups]
ow = [{gnames[g.group]: g.weight for g in v.groups} for v in ours.data.vertices]
kdf = KDTree(len(ours.data.polygons))
for p in ours.data.polygons:
    kdf.insert(p.center, p.index)
kdf.balance()
kdv = KDTree(len(oco))
for i, c in enumerate(oco):
    kdv.insert(c, i)
kdv.balance()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=cc.path('meshy/custodian_retexture_v1/model_urls_glb.glb'))
new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
assert len(new) == 1, new
mesh = new[0]
for o in bpy.data.objects:
    if o not in before and o is not mesh:
        bpy.data.objects.remove(o)
mesh.parent = None
mesh.data.transform(mesh.matrix_world); mesh.matrix_world = Matrix()
mco = np.array([v.co[:] for v in mesh.data.vertices])
olo, ohi, mlo, mhi = oco.min(0), oco.max(0), mco.min(0), mco.max(0)
ratio = (ohi - olo) / (mhi - mlo)
print('ADOPT scale per axis', ratio.round(5))
assert ratio.max() / ratio.min() < 1.01, 'axes do not match'
s = float(ratio.mean())
mesh.data.transform(Matrix.Translation(Vector(((olo + ohi) / 2).tolist())) @ Matrix.Scale(s, 4)
                    @ Matrix.Translation(Vector((-(mlo + mhi) / 2).tolist())))
bm = bmesh.new(); bm.from_mesh(mesh.data)
layer = bm.faces.layers.int.new('part')
far = 0.0
for f in bm.faces:
    _, idx, dist = kdf.find(f.calc_center_median())
    f[layer] = int(opart[idx]); far = max(far, dist)
    f.smooth = True
for e in bm.edges:
    e.smooth = not (len(e.link_faces) != 2 or e.calc_face_angle(0.0) > math.radians(SHARP_DEG))
bm.to_mesh(mesh.data); bm.free()
mesh.vertex_groups.clear()
for n in gnames:
    mesh.vertex_groups.new(name=n)
farv = 0.0
for v in mesh.data.vertices:
    _, idx, dist = kdv.find(v.co)
    farv = max(farv, dist)
    for n, w in ow[idx].items():
        mesh.vertex_groups[n].add([v.index], w, 'REPLACE')
print('ADOPT farthest face match', round(far, 4), 'm, vertex match', round(farv, 4), 'm')
bpy.data.objects.remove(ours)
mesh.name = mesh.data.name = 'Custodian'
mesh['joints'] = joints
mesh.data.materials.clear()
mesh.data.uv_layers.active.name = 'UVMap'
counts = {}
for p, value in zip(mesh.data.polygons, mesh.data.attributes['part'].data):
    counts[value.value] = counts.get(value.value, 0) + len(p.vertices) - 2
print('ADOPT part tris', dict(sorted(counts.items())), 'total', sum(counts.values()))
bpy.ops.wm.save_as_mainfile(filepath=cc.path('work/tex.blend'))
print('ADOPTED')
