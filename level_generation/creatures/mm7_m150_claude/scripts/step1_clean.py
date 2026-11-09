"""Step 1 cleanup of the m150 v2 Smart Topology return (work/st_v2_parts.blend, loose parts P000.., wing tips at 1.85 m,
hair top 1.71 m, facing -Y). v2 (after the user review of v1): bare head, polished steel cuirass, separate shoulder
straps, feathered wings as P01/P02 plus ~120 loose feather cards.
Parts are sorted by rules on their bounds (work/st_v2_parts.json), then recorded in work/step1_labels.json:
- DROP: pieces of <= 6 triangles (single loose triangles) and the small specks floating at the wing tips and beside
  the hips (<= 30 vertices, |x| > 1.0); P09's sliver fan across to the other leg is cut;
- HAIR: locks behind the head (bottom >= 1.35 m, |centre x| < 0.2, centre y >= -0.02; not the eyes P15/P16);
- WINGS: P01/P02 and every card behind the back (centre y > 0.04 and |centre x| > 0.3, bottom > 1.0), plus the
  inner root cards on the spine (centre y > 0.1, 1.05 < bottom, top < 1.4);
- everything else is the body.
Wings go to 'Wings' (rigged later by wings_rig.py); the rest is joined into 'Body'. Both carry 'piece' and 'orig_co'.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
parts = {int(r['name'][1:]): r for r in json.load(open(os.path.join(HERE, 'work', 'st_v2_parts.json')))}


def label(i, r):
    lo, hi = np.array(r['lo']), np.array(r['hi']); c = (lo + hi) / 2
    if r['tris'] <= 6:
        return 'drop'
    if r['verts'] <= 30 and r['tris'] >= 1.7 * r['verts'] and abs(c[0]) > 1.0:      # closed balls, not the flat feather cards
        return 'drop'
    if i in (15, 16):
        return 'body'
    if i in (1, 2):
        return 'wing'
    if lo[2] >= 1.35 and abs(c[0]) < 0.2 and c[1] >= -0.02 and hi[2] < 1.65:
        return 'hair'
    if (c[1] > 0.04 and abs(c[0]) > 0.3 or abs(c[0]) > 0.6) and lo[2] > 1.0:   # the outermost cards sit at y ~ 0
        return 'wing'
    if c[1] > 0.1 and lo[2] > 1.05 and hi[2] < 1.4:
        return 'wing'
    return 'body'


LAB = {i: label(i, r) for i, r in parts.items()}
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for n in [n for n in P if LAB[int(n[1:])] == 'drop']:
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
# P09 (left greave) carries a sliver fan across to the right leg (the 'spike between the knees'): cut its vertices
# medial of x = 0.08
import bmesh
if 'P09' in P:
    bm = bmesh.new(); bm.from_mesh(P['P09'].data)
    cut = [v for v in bm.verts if v.co.x < 0.08]
    bmesh.ops.delete(bm, geom=cut, context='VERTS'); bm.to_mesh(P['P09'].data); bm.free()
    print('CLEAN P09 sliver vertices removed', len(cut))
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.data.materials.clear()


def join(names, name):
    for o in bpy.data.objects:
        o.select_set(o.name in names)
    bpy.context.view_layer.objects.active = P[sorted(names)[0]]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = ob.data.name = name
    co = np.array([tuple(v.co) for v in ob.data.vertices])
    ob.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
    return ob


body = join([n for n in P if LAB[int(n[1:])] in ('body', 'hair')], 'Body')
wings = join([n for n in P if LAB[int(n[1:])] == 'wing'], 'Wings')
json.dump({str(k): v for k, v in LAB.items()}, open(os.path.join(HERE, 'work', 'step1_labels.json'), 'w'))
cnt = {k: sum(1 for v in LAB.values() if v == k) for k in ('body', 'hair', 'wing', 'drop')}
print('CLEAN labels', cnt, 'hair pieces', sorted(k for k, v in LAB.items() if v == 'hair'))
for ob in (body, wings):
    print('CLEAN', ob.name, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), 'verts', len(ob.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
