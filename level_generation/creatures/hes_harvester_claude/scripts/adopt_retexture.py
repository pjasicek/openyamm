"""Step 3 (after hes_turrets_claude/scripts/adopt_retexture.py): adopt the Meshy retexture's own mesh
(meshy/harvester_retexture_v1/model_urls_glb.glb).

The retexture keeps our UV islands only roughly (on the turrets it moved UVs by up to 8-25 texels at 2K and welded
some seam vertices), and its maps are painted on ITS UVs, so the returned mesh is
the geometry from here on. It comes back normalised (longest side 2, centred); it is scaled and moved back onto
work/<name>_uv.blend's frame (same axes), each face takes the `part` of the nearest face of our split mesh (the
parts are separate components, so nearest is exact), and the shading is redone as in prepare_uv.py (smooth, sharp
over SHARP_DEG). Writes work/harvester_tex.blend (object `harvester`, face attribute `part`, `drill_axis` custom property)."""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = 'harvester'
SHARP_DEG = 38.0

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_uv.blend'))
ours = bpy.data.objects[NAME]
drill_axis = list(ours['drill_axis'])
oco = np.array([v.co[:] for v in ours.data.vertices])
opart = np.zeros(len(ours.data.polygons), int); ours.data.attributes['part'].data.foreach_get('value', opart)
kd = KDTree(len(ours.data.polygons))
for p in ours.data.polygons:
    kd.insert(p.center, p.index)
kd.balance()

before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', f'{NAME}_retexture_v1', 'model_urls_glb.glb'))
new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
assert len(new) == 1, new
mesh = new[0]
bpy.ops.object.select_all(action='DESELECT')
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
    c = f.calc_center_median()
    _, idx, dist = kd.find(c)
    f[layer] = int(opart[idx]); far = max(far, dist)
    f.smooth = True
for e in bm.edges:
    e.smooth = not (len(e.link_faces) != 2 or e.calc_face_angle(0.0) > math.radians(SHARP_DEG))
bm.to_mesh(mesh.data); bm.free()
print('ADOPT farthest face match', round(far, 4), 'm')
bpy.data.objects.remove(ours)
mesh.name = mesh.data.name = NAME
mesh['drill_axis'] = drill_axis
mesh.data.materials.clear()
mesh.data.uv_layers.active.name = 'UVMap'
counts = {}
for p, value in zip(mesh.data.polygons, mesh.data.attributes['part'].data):
    counts[value.value] = counts.get(value.value, 0) + len(p.vertices) - 2
print('ADOPT part tris', dict(sorted(counts.items())))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'{NAME}_tex.blend'))
print('ADOPTED')
