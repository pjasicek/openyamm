"""Faces kept at source density in the head-detail rebuild (user 2026-10-14: the 45 % face lost its lips, an eye corner
and left a crease across the forehead): every source face whose nearest master face is head-set face skin or hair
(final_v3_head_repaired.blend: head == 1, part Body or Hair). Braid and circlet are reduced as before (the circlet is
rebuilt by circlet_r45.py). In: work/mesh_in.npz. Out: work_head/mesh_in.npz (same arrays, protect = kept faces)."""
import json, os, bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(os.path.join(HERE, '..', 'mm6_pfem_claude', 'work', 'final_v3_head_repaired.blend')))
old = bpy.data.objects['Peasant']; om = old.data
PARTS = json.loads(bpy.context.scene['pfem_parts'])
opart = np.array([a.value for a in om.attributes['part'].data]); ohead = np.array([a.value for a in om.attributes['head'].data])
keep_master = (ohead == 1) & np.isin(opart, [PARTS.index('Body'), PARTS.index('Hair')])
tree = BVHTree.FromPolygons([v.co for v in om.vertices], [list(p.vertices) for p in om.polygons])
d = dict(np.load(os.path.join(HERE, 'work', 'mesh_in.npz')))
cent = d['verts'][d['faces']].mean(1)
near = np.array([tree.find_nearest(Vector(c))[2] for c in cent])
d['protect'] = keep_master[near].astype(np.float64)
np.savez(os.path.join(HERE, 'work_head', 'mesh_in.npz'), **d)
print('PROTECT', int(d['protect'].sum()), 'of', len(cent), 'faces kept at source density; master head skin+hair faces',
      int(keep_master.sum()))
