"""Flip faces wound against their neighbours (mm9_bjarni, 2026-11-02: Meshy's Smart Topology left single inverted
triangles at the nostril, forehead, temple, crown and belt buckle; EEVEE shades them dark, the engine may cull them).
A face whose normal points against the mean of its own vertex normals (dot < LIMIT; the export's check) is flipped;
thin two-sided parts (fins, discs) average to near zero there and stay.
Geometry winding only: UVs, weights and attributes follow the face. Args: -- <in blend> <out blend> [limit -0.3]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
LIMIT = float(a[2]) if len(a) > 2 else -0.2
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
flip = []
for f in bm.faces:
    vn = sum((v.normal for v in f.verts), f.normal * 0)
    if vn.length > 1e-6 and f.normal.dot(vn.normalized()) < LIMIT:
        flip.append(f)
for f in flip:
    print('FLIP', f.index, [round(x, 3) for x in f.calc_center_median()])
bmesh.ops.reverse_faces(bm, faces=flip, flip_multires=False)
bm.to_mesh(ob.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('FIXFLIPS', len(flip))
