"""Components of the great cannon source (work/emplacement/great_cannon_source.glb, LOD0 node only), positions
welded: size, bounds (Blender metres at the source scale) and the zone materials on them. For the emplacement split."""
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import machines_common as mc  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', 'emplacement', 'great_cannon_source.glb'))
obj = bpy.data.objects['IonCannon']
print('MATERIALS', [m.name for m in obj.data.materials])
bm = bmesh.new(); bm.from_mesh(obj.data); bm.transform(obj.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
labels = mc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
fl = np.array([labels[f.verts[0].index] for f in bm.faces]); fm = np.array([f.material_index for f in bm.faces])
rows = []
for c in range(labels.max() + 1):
    p = co[labels == c]
    mats = sorted(set(fm[fl == c].tolist()))
    rows.append((len(p), c, p.min(0).round(2).tolist(), p.max(0).round(2).tolist(), mats))
print('BOUNDS', co.min(0).round(2), co.max(0).round(2), 'components', len(rows))
for r in sorted(rows, reverse=True)[:45]:
    print('COMP', *r)
