"""Remove the tail Meshy's Smart Topology invented behind the shorts (the masters and the native werewolf have none;
the 2026-10-09 model needed the same cut). Faces with any vertex in the tail box (behind the seat, below the waist,
near the midline) are deleted; the opening is filled (bmesh holes fill), triangulated and relaxed, then the result
replaces work/placed.npz (the original is kept as work/placed_tail.npz). Args: <ymin> <zmax> <half width>"""
import bpy, bmesh, sys, os, shutil
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; YMIN, ZMAX, HW = map(float, a[:3])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(HERE, 'work/placed_tail.npz')
if not os.path.exists(src):
    shutil.copy(os.path.join(HERE, 'work/placed.npz'), src)
D = np.load(src); P = D['co']; T = D['tri']
cx = float(np.median(P[(P[:, 2] > 0.1) & (P[:, 2] < 0.4), 0]))
bm = bmesh.new()
vs = [bm.verts.new(p) for p in P]
for t in T:
    try: bm.faces.new([vs[i] for i in t])
    except ValueError: pass
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
tail = [v for v in bm.verts if v.co.y > YMIN and v.co.z < ZMAX and abs(v.co.x - cx) < HW and v.co.z > -0.45]
faces = set(f for v in tail for f in v.link_faces)
nf = len(faces)
bmesh.ops.delete(bm, geom=list(faces), context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
before = len(bm.faces)
res = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary and e.verts[0].co.y > YMIN - 0.06 and abs(e.verts[0].co.x - cx) < HW + 0.05 and e.verts[0].co.z < ZMAX + 0.05], sides=200)
new = res['faces']
bmesh.ops.triangulate(bm, faces=new)
patch = set(v for f in bm.faces if f not in faces for v in f.verts) if False else set(v for f in new for v in f.verts if f.is_valid)
newf = [f for f in bm.faces if f.index < 0 or f in new]
vs_patch = list(set(v for f in bm.faces for v in f.verts if any(e.is_boundary for e in f.edges) is False and v.co.y > YMIN - 0.05 and abs(v.co.x - cx) < HW and v.co.z < ZMAX))
bmesh.ops.smooth_vert(bm, verts=vs_patch, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.verts.index_update()
co = np.array([v.co[:] for v in bm.verts]); tri = np.array([[v.index for v in f.verts] for f in bm.faces])
np.savez(os.path.join(HERE, 'work/placed.npz'), co=co, tri=tri, scale=D['scale'])
print('TAIL deleted faces', nf, 'filled faces', len(new), 'verts', len(co), 'tris', len(tri), 'open boundary edges', sum(1 for e in bm.edges if e.is_boundary))
