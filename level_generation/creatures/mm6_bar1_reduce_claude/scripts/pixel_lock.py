"""Lock source faces under given pixels of a close_views.py render (Standing frame 0, REA_FACING=-Y): ray-cast each
pixel from that render's camera onto the posed source, take the hit faces' rest-pose centres (work/mesh_in.npz has the
same face order) and add every source face within REA_LOCK_R (default 0.03 m) to the keep mask.
Usage: blender -b -P pixel_lock.py -- <source glb> <spot_view, e.g. hand_front> <base keep .npy> <out .npy> x,y [x,y ...]"""
import os, sys, math, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, spotview, base, out, *pix = sys.argv[sys.argv.index('--') + 1:]
spot, view = spotview.rsplit('_', 1)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
pb = {b.name.lower(): b for b in rig.pose.bones}
head = rig.matrix_world @ next(b for n, b in pb.items() if n.endswith('head')).head
rhand = rig.matrix_world @ next(b for n, b in pb.items() if n.endswith('r_hand')).head
c, size = {'hand': (rhand, .4), 'tunic': (head - Vector((0, 0, .62)), .7)}[spot]
d = Vector({'front': (0, -1, .1), 'q34': (.7, -.7, .2), 'side': (1, 0, .1)}[view]).normalized()
loc = c + d * 4; rot = (c - loc).to_track_quat('-Z', 'Y').to_matrix()
right, up, fwd = rot.col[0], rot.col[1], -rot.col[2]
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Barbarian')
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg)
inv = ev.matrix_world.inverted()
src = np.load(f'{HERE}/work/mesh_in.npz'); cen = src['verts'][src['faces']].mean(1)
assert len(ev.data.polygons) == len(cen), (len(ev.data.polygons), len(cen))
keep = np.load(base).copy(); n0 = int(keep.sum()); R = float(os.environ.get('REA_LOCK_R', '0.03'))
for p in pix:
    x, y = (float(v) / 600 for v in p.split(','))
    o = loc + right * (x - .5) * size + up * (.5 - y) * size
    hit, hp, hn, fi = ev.ray_cast(inv @ o, inv.to_3x3() @ fwd)
    if not hit: print('MISS', p); continue
    r = cen[fi]; near = np.linalg.norm(cen - r, axis=1) < R; keep |= near
    print('HIT', p, 'face', fi, 'rest', np.round(r, 3), 'locked', int(near.sum()))
np.save(f'{HERE}/{out}', keep); print('LOCK', n0, '->', int(keep.sum()))
