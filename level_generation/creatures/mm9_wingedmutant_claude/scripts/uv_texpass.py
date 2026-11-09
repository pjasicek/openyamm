"""Texture quality pass UVs (claude_shared/TEXTURE_QUALITY_PASS.md, 2026-10-30) for the symmetric Winged Mutant.

The rework's body UVMap is the v1 Smart UV layout of the whole asymmetric body: after symmetrize.py the mirrored half
reuses the kept half's islands and the grafted head has its own HeadUV, so only 8 % of the 2K body atlas was still
used. This lays new UVs on the kept (+x) half of the body and wing membranes (head faces excluded) with
claude_shared/uv_atlas.py and gives every -x face the UVs of its mirror twin, so both halves keep sharing texels.

1. Non-head polygons that are not triangles (bisect quads) are triangulated mirror-consistently: +x faces with the
   fixed 0-2 diagonal, each -x face along the mirror image of its twin's diagonal. Export triangulates anyway.
2. uv_atlas.unwrap on a copy holding only the +x non-head faces (one density, 2 px margin, 2048).
3. UVs back: +x faces by their original index (loops matched by position), -x faces from the twin face found by the
   mirrored centre (loops by mirrored position). Head faces' UVMap goes to one point (they use HeadUV at export).
4. Upload (neutral static GLB, UVMap only): the whole body incl. head; the -x half and the head collapse to one point
   in UV space (zero area: Meshy paints only the +x half, at the full atlas resolution).

Args: -- <in blend (head_v3: sym_v2 + HeadUV, no back faces)> <out blend> <upload glb> <report json>
      [key=value uv_atlas.unwrap options]
"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texpass_mesh import mirror_triangulate

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REPORT = argv[:4]
options = {k: (float(v) if v.replace('.', '', 1).isdigit() and '.' in v else int(v) if v.isdigit() else v)
           for k, v in (a.split('=', 1) for a in argv[4:])}
DUMP = (0.25 / 2048, 0.25 / 2048)

bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data


report = {'triangulated': mirror_triangulate(me)}
hd = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', hd)
centre = np.array([p.center[:] for p in me.polygons])
plus = (hd == 0) & (centre[:, 0] >= 0)       # faces lying in the plane are their own twin
minus = (hd == 0) & (centre[:, 0] < 0)
assert all(len(me.polygons[i].vertices) == 3 for i in np.nonzero(hd == 0)[0])
report.update(head_faces=int(hd.sum()), plus_faces=int(plus.sum()), minus_faces=int(minus.sum()))

# ---- 2. the +x half alone, unwrapped and packed
orig = me.attributes.new('orig_face', 'INT', 'FACE') if 'orig_face' not in me.attributes else me.attributes['orig_face']
orig.data.foreach_set('value', np.arange(len(me.polygons), dtype=np.int32))
half = body.copy()
half.data = me.copy()
half.modifiers.clear()
half.parent = None
half.matrix_world = body.matrix_world
half.name = 'TexpassHalf'
bpy.context.scene.collection.objects.link(half)
bm = bmesh.new()
bm.from_mesh(half.data)
of = bm.faces.layers.int['orig_face']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not plus[f[of]]], context='FACES')
bm.to_mesh(half.data)
bm.free()
uv_report = uv_atlas.unwrap(half, **options)
report['uv_atlas'] = uv_report
print('UV_ATLAS', json.dumps(uv_report))

# ---- 3. UVs back onto the body
hme = half.data
huv = hme.uv_layers['UVMap'].data
src = {}
for p in hme.polygons:
    src[hme.attributes['orig_face'].data[p.index].value] = {
        tuple(np.round(hme.vertices[v].co, 6)): tuple(huv[li].uv) for v, li in zip(p.vertices, p.loop_indices)}
uv = me.uv_layers['UVMap'].data
tree = KDTree(int(plus.sum()))
for i in np.nonzero(plus)[0]:
    c = centre[i]
    tree.insert((-c[0], c[1], c[2]), int(i))
tree.balance()
worst = 0.0
for p in me.polygons:
    if hd[p.index]:
        for li in p.loop_indices:
            uv[li].uv = DUMP
        continue
    if plus[p.index]:
        table = src[p.index]
        for v, li in zip(p.vertices, p.loop_indices):
            uv[li].uv = table[tuple(np.round(me.vertices[v].co, 6))]
        continue
    _, twin, d = tree.find(p.center)
    worst = max(worst, d)
    table = src[twin]
    keys = np.array(list(table))
    for v, li in zip(p.vertices, p.loop_indices):
        co = np.array(me.vertices[v].co) * [-1, 1, 1]
        j = int(np.argmin(np.linalg.norm(keys - co, axis=1)))
        worst = max(worst, float(np.linalg.norm(keys[j] - co)))
        uv[li].uv = table[tuple(keys[j])]
report['mirror_worst_match_m'] = worst
assert worst < 1e-4, worst
bpy.data.objects.remove(half)
me.attributes.remove(me.attributes['orig_face'])
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)

# ---- 4. upload: the whole body, -x half and head collapsed to one UV point
dup = body.copy()
dup.data = me.copy()
dup.modifiers.clear()
dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
dme = dup.data
dme.uv_layers.remove(dme.uv_layers['HeadUV'])
duv = dme.uv_layers['UVMap'].data
for p in dme.polygons:
    if not plus[p.index]:
        for li in p.loop_indices:
            duv[li].uv = DUMP
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
json.dump(report, open(REPORT, 'w'), indent=1)
print('TEXPASS_UV', json.dumps({k: v for k, v in report.items() if k != 'uv_atlas'}))
