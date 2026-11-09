"""Step B: head-only Meshy parts on the fitted body. Old head off, torso strap ridges smoothed away (the harness is tier A's paint), the head placed. Parts: 0 body skin, 10 head shell (face, hair, ears, eyes), 14 tusks. Writes the assembled triangles for wrap_voxel.py. Args: <pose blend> <head blend> <out npz>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
S, OY, OZ = 0.518, 0.012, 0.905
C = np.array([0.0, 0.02, 0.775]); N = np.array([0.0, -0.25, 0.968]); N /= np.linalg.norm(N)
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 10, 'Hair': 10, 'Eyes': 10, 'Teeth': 14}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.verts.layers.int.new('part')
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=C, plane_no=N, clear_outer=True)
# strap ridges round the chest: smoothed, the muscles stay in the larger shape
def smooth(vs, it, k=0.55):
    for _ in range(it):
        nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / max(len(v.link_edges), 1)) for v in vs if not v.is_boundary]
        for v, c in nw: v.co = v.co * (1 - k) + c * k
bd = [e for e in bm.edges if e.is_boundary]
n0 = len(bd)
bmesh.ops.holes_fill(bm, edges=bd, sides=len(bd) + 1)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
bd = [e for e in bm.edges if e.is_boundary]
print('HOLES', n0, '->', len(bd))
band = [v for v in bm.verts if 0.245 < v.co.z < 0.45 and abs(v.co.x) < 0.37]
smooth(band, 9)
groin = [v for v in bm.verts if -0.27 < v.co.z < -0.02 and abs(v.co.x) < 0.07]
smooth(groin, 8)
print('BAND', len(band), len(groin))
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts:
        y = v.co.y * S + OY
        if nm == 'Hair' and y > 0.06: y = 0.06 + (y - 0.06) * 0.82       # the back of the hair, nearer MM9's depth
        z = v.co.z * S + OZ
        if nm == 'Hair' and z < 0.93: z = 0.93 + (z - 0.93) * 0.62       # lock tips stay off the shoulders, as MM9's
        v.co = Vector((v.co.x * S, y, z))
    tl = t.verts.layers.int.new('part')
    for v in t.verts: v[tl] = pid[nm]
    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    lay = bm.verts.layers.int['part']
    bpy.data.meshes.remove(tm)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
pa = np.array([v[lay] for v in bm.verts]); co = np.array([v.co[:] for v in bm.verts])
tri = np.array([[v.index for v in f.verts] for f in bm.faces])
print('ASSEMBLED', len(co), len(tri), {int(k): int((pa == k).sum()) for k in np.unique(pa)})
np.savez(OUT, co=co, tri=tri, part=pa)
