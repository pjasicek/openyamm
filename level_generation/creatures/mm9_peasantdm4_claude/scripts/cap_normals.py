"""Cap faces facing inward (diagnostic and fix, 2026-11-02: white triangles on the cap = flipped cap faces culled as back
faces, the grey scalp paint under the cap seen through them). Faces of the loose part whose vertices lie above ZMIN and
whose normal points toward the head's centre (dot with centroid - C < 0) are listed; with an out blend they are flipped.
Args (Blender): <in blend> [out blend] [zmin 0.46] [cx,cy,cz 0.0,0.04,0.40]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
out = a[1] if len(a) > 1 and a[1].endswith('.blend') else None
zmin = float(a[2]) if len(a) > 2 else 0.46
C = Vector([float(v) for v in (a[3] if len(a) > 3 else '0.0,0.04,0.40').split(',')])
ob = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
hl = bm.faces.layers.int.get('head')
bad = []
for f in bm.faces:
    if f[hl] != 1 or min(v.co.z for v in f.verts) < zmin: continue
    c = f.calc_center_median()
    d = (c - C).normalized()
    if f.normal.dot(d) < -0.2:
        bad.append(f)
        print('INWARD', f.index, [round(x, 3) for x in c], round(f.normal.dot(d), 2), round(f.calc_area() * 1e4, 2), 'cm2')
print('INWARD n', len(bad))
if out:
    bmesh.ops.reverse_faces(bm, faces=bad)
    bm.to_mesh(ob.data); bpy.ops.wm.save_as_mainfile(filepath=out); print('FLIPPED', len(bad))
