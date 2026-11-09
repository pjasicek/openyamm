"""Source vertices whose posed distance to a ladder candidate exceeds REA_LOCK_MM (default 18) at REA_FRAMES
(work/ladder.blend, REA_CAND) -> work/error_verts.npy (rest-pose vertex indices of work/mesh_in.npz). Then
python3 error_lock.py <base keep .npy> <out .npy> keeps every source face within REA_LOCK_R (default 0.04 m) of them."""
import os, sys
import numpy as np
try:
    import bpy, bmesh
    from mathutils.bvhtree import BVHTree
except ImportError:
    bpy = None
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if bpy is not None:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
    sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
    cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_70')]
    def ev(o):
        b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
    bad = set()
    for spec in os.environ.get('REA_FRAMES', 'Death:36').split(','):
        clip, f = spec.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
        bs, bc = ev(src), ev(cand); t = BVHTree.FromBMesh(bc)
        bad |= {v.index for v in bs.verts if t.find_nearest(v.co)[3] > float(os.environ.get('REA_LOCK_MM', '18')) / 1000}
        bs.free(); bc.free()
    np.save(os.path.join(HERE, 'work', 'error_verts.npy'), np.array(sorted(bad), int)); print('ERRVERTS', len(bad))
    raise SystemExit
from scipy.spatial import cKDTree  # noqa: E402
base, out = sys.argv[1:3]
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); verts = np.load(os.path.join(HERE, 'work', 'error_verts.npy'))
cen = d['verts'][d['faces']].mean(1); keep = np.load(base).copy(); n0 = int(keep.sum())
for p in d['verts'][verts]:
    keep[cKDTree(cen).query_ball_point(p, float(os.environ.get('REA_LOCK_R', '0.04')))] = True
np.save(out, keep); print('LOCK', len(verts), 'vertices:', n0, '->', int(keep.sum()), 'faces kept')
