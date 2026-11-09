"""Step B: head-only Meshy parts on the fitted body. The body stays closed: its old head is shrunk inside the new one. Parts: 0 body skin, 10 head shell, 13 eyes, 15 mouth and eye plugs. Writes the assembled triangles for wrap_bf.py. Args: <pose blend> <head blend> <out npz>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector, Matrix
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
S, OY, OZ = 0.5, -0.30, 0.895
C = np.array([0.0, -0.28, 0.90]); SHR = 0.5
def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 10, 'Eyes': 13}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.verts.layers.int.new('part')
n = 0
for v in bm.verts:
    p = np.array(v.co[:])
    t = sstep(p[2], 0.64, 0.74) * (1 - sstep(abs(p[0]), 0.13, 0.20))
    if t > 0:
        v.co = Vector(p + t * (SHR - 1) * (p - C)); n += 1
print('SHRUNK', n)
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts: v.co = Vector((v.co.x * S, v.co.y * S + OY, v.co.z * S + OZ))
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
