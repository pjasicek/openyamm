"""Repair the collapsed midline triangles at the top of the nose bridge (fourth pass): the mirrored Meshy face left
needle triangles along x = 0 (vertex pairs under 1 mm apart, unwelded) whose UVs span the face chart; any smoothing of the
bridge opened them into a dark diamond. Head-shell vertices in the bridge zone (|x| < 3 mm, rest z 0.70-0.77, front) are
welded within 1 mm, then zero-area faces there are dissolved. Positions/faces only. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
hl = bm.faces.layers.int['head']
zone = lambda p: abs(p.x) < 0.003 and 0.70 < p.z < 0.77 and p.y < -0.04
vs = list({v for f in bm.faces if f[hl] for v in f.verts if zone(v.co)})
n0, f0 = len(bm.verts), len(bm.faces)
bmesh.ops.remove_doubles(bm, verts=vs, dist=0.001)
fz = [f for f in bm.faces if f[hl] and f.calc_area() < 1e-9 and all(zone(v.co) or abs(v.co.x) < 0.006 for v in f.verts)]
ez = list({e for f in fz for e in f.edges})
if ez:
    bmesh.ops.dissolve_degenerate(bm, dist=0.0002, edges=ez)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
for v in bm.verts:
    if abs(v.co.x) < 1e-5:
        v.co.x = 0.0
print('BRIDGEWELD', {'zone_verts': len(vs), 'welded': n0 - len(bm.verts), 'faces_removed': f0 - len(bm.faces), 'zero_faces': len(fz)})
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
