"""Step 1 cleanup of the sorceress Smart Topology return (work/st_v1_parts.blend, loose parts P00..P58, 1.75 m to the
hair top, soles z=0):
- P56, P57, P58 are single stray triangles beside the hair at the shoulders: deleted.
- P00 (skin, halter, gloves, boots in one shell): every face longer than 10 cm with a length / height ratio above 9 is
  deleted (sliver flaps), then loose vertices.
- everything else is kept (mane, curls, circlet, earrings, choker, gems, belt studs, front/back panels, one shoulder cap).
Joins the parts into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (positions as uploaded to the
Meshy auto-rig, for the nearest-vertex weight transfer). Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for n in ('P56', 'P57', 'P58'):
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
print('CLEAN stray single-triangle parts removed 3')
# ---- P00 slivers
o = P['P00']
bm = bmesh.new(); bm.from_mesh(o.data)
bad = []
for f in bm.faces:
    vs = [v.co for v in f.verts]
    L = max((vs[i] - vs[(i + 1) % len(vs)]).length for i in range(len(vs)))
    a = f.calc_area()
    h = 2 * a / L if L > 0 else 0
    if L > 0.10 and (h == 0 or L / h > 9):
        bad.append(f)
nb = len(bad)
bmesh.ops.delete(bm, geom=bad, context='FACES_ONLY')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.to_mesh(o.data); bm.free(); o.data.update()
print('CLEAN P00 sliver faces removed', nb, 'loose verts', len(loose))
for ob in bpy.data.objects:
    ob.select_set(False)
for n, ob in P.items():
    ob.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(ob.data.vertices))
    ob.data.materials.clear()
    ob.select_set(True)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
for p in me.polygons:
    p.use_smooth = True
print('CLEAN tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co), 'height', round(float(co[:, 2].max()), 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
