"""Split the Meshy return into the Harvester's rigid parts and clean it (after hes_turrets_claude/scripts/parts.py).

Every connected component goes whole to one part (component indices are those of harvester_common.component_labels
on the fixed raw file meshy/harvester_st_v1; scripts/components.py and closeup.py render them):
  0      body    - hull, tracks, guards, fins, core drums, vent hoods, cables, the hinge hubs (B_Body)
  1      drill   - the conical drill's six rings (B_Drill: spins about its axis)
  2      boom    - the drill housing's rings in front of the hinge hubs (B_Boom: tilts down for the dig)
  3      sprayer - the gooseneck slag sprayer, neck and nozzle (B_Sprayer: swivels on its base)
  10..15 buckets on the machine's right (-x), front to rear; 20..25 on its left (+x) (B_Bucket_R0.. / _L0..)
Meshy mirrored the single rear sprayer into a second, lower nozzle (components 46, 68): deleted (the concept has one).
The buckets are moved along y to an even spacing (BUCKET_Y0 + i * BUCKET_STEP; Meshy spaced them irregularly), so
the conveyor clip can move each one exactly one step per cycle and loop seamlessly. Small components (bolts, knobs)
whose centre lies inside a bucket's box go with that bucket. Components of fewer than 4 vertices are deleted.
Then: merge by distance (0.1 mm) and consistent outward normals per part.
Writes work/harvester_parts_raw.blend (object `harvester` with face attribute `part`, the pivots as custom props)."""
import json
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import harvester_common as tc  # noqa: E402

DRILL = {119, 14, 54, 273, 130, 63}
BOOM = {6, 62, 139, 132}
SPRAYER = {4, 40}
DELETE = {46, 68}
BUCKETS_R = [25, 57, 123, 104, 13, 1]          # x < 0, front to rear
BUCKETS_L = [117, 39, 79, 53, 183, 160]        # x > 0
BUCKET_Y0, BUCKET_Y5 = -1.72, 2.06             # centres of the first and last bucket after spacing
BUCKET_STEP = (BUCKET_Y5 - BUCKET_Y0) / 5

obj = tc.import_raw()
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = tc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
ncomp = labels.max() + 1
lo = np.array([co[labels == c].min(0) for c in range(ncomp)])
hi = np.array([co[labels == c].max(0) for c in range(ncomp)])
mid = (lo + hi) / 2
size = np.array([(labels == c).sum() for c in range(ncomp)])

comp_part = np.zeros(ncomp, int)
comp_part[size < 4] = -1
for c in DELETE:
    comp_part[c] = -1
for c in DRILL:
    comp_part[c] = 1
for c in BOOM:
    comp_part[c] = 2
for c in SPRAYER:
    comp_part[c] = 3
buckets = [(10 + i, c) for i, c in enumerate(BUCKETS_R)] + [(20 + i, c) for i, c in enumerate(BUCKETS_L)]
for p, c in buckets:
    comp_part[c] = p
attached = {}
for c in range(ncomp):
    if comp_part[c] != 0 or size[c] >= 20:
        continue
    for p, b in buckets:
        if np.all(mid[c] > lo[b] - 0.03) and np.all(mid[c] < hi[b] + 0.03):
            comp_part[c] = p
            attached.setdefault(p, []).append(c)
            break

# even bucket spacing: shift every component of a bucket part in y
shift = {}
for p, b in buckets:
    i = p % 10
    shift[p] = BUCKET_Y0 + i * BUCKET_STEP - mid[b][1]
for v in bm.verts:
    p = comp_part[labels[v.index]]
    if p in shift:
        v.co.y += shift[p]

fpart = bm.faces.layers.int.new('part')
for f in bm.faces:
    f[fpart] = int(comp_part[labels[f.verts[0].index]])
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[fpart] < 0], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
for p in sorted({f[fpart] for f in bm.faces}):
    faces = [f for f in bm.faces if f[fpart] == p]
    bmesh.ops.remove_doubles(bm, verts=list({v for f in faces for v in f.verts}), dist=0.0001)
    faces = [f for f in bm.faces if f[fpart] == p]
    bmesh.ops.recalc_face_normals(bm, faces=faces)
bm.to_mesh(obj.data); bm.free()

counts = {}
for poly, value in zip(obj.data.polygons, obj.data.attributes['part'].data):
    counts[value.value] = counts.get(value.value, 0) + len(poly.vertices) - 2
print('PART_TRIS', json.dumps(dict(sorted(counts.items()))), 'total', sum(counts.values()))
print('BUCKET_SHIFT', json.dumps({p: round(s, 3) for p, s in shift.items()}), 'attached', json.dumps(attached))
drill = np.vstack([co[labels == c] for c in DRILL])
obj['drill_axis'] = [0.0, float(drill[:, 1].min()), float((drill[:, 2].min() + drill[:, 2].max()) / 2)]
spr = np.vstack([co[labels == c] for c in SPRAYER])
print('DRILL', obj['drill_axis'][:], 'SPRAYER lo', spr.min(0).round(3), 'hi', spr.max(0).round(3))
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'harvester_parts_raw.blend'))
print('SAVED')
