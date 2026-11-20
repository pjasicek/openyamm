"""Step 1 of the m410 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P100):
- the head P01 and the mask P14 each trail thin spikes down onto the chest (to z 1.29; the mask's natural tip is at
  ~1.45 and the vest collar covers the neck): their vertices below SPIKE_Z = 1.43 m are deleted;
- the pouch P06 trails a 20 cm spike up the chest: its vertices above POUCH_TOP = 1.10 m are deleted and the opening
  capped; sliver faces left anywhere (longest edge > 4 cm, height < 3 mm: two on the vest front) have their shortest
  edge collapsed;
- every shell of <= 36 triangles is deleted: ~70 vest studs, the boot-lace bits and belt rivets (the textures paint
  them; 2.4k triangles of 15k);
- kept: P00 torso + arms + hands (one shell), P01 head, P02 trousers, P03 cap, P04/P05 boots (R/L), P06 pouch (right
  hip), P07/P08 shoulder caps (R/L), P09 empty sheath (left hip), P10 belt + pouch strap, P11 belt piece, P12/P13 wrist
  band (R) / bangles (L), P14 mask, P15 buckle, P16/P17 eyes, P18 a boot-lace knot (37 tris), P19 sheath throat.
Joins the parts into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (rest positions, for the
nearest-vertex weight transfer from Meshy's rigged copy). Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
SPIKE_Z = 1.43
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
removed = []
for n in list(P):
    if sum(len(p.vertices) - 2 for p in P[n].data.polygons) <= 36:
        bpy.data.objects.remove(P.pop(n), do_unlink=True); removed.append(n)
cut = {}
for n in ('P01', 'P14'):
    me = P[n].data; bm = bmesh.new(); bm.from_mesh(me)
    kill = [v for v in bm.verts if (P[n].matrix_world @ v.co).z < SPIKE_Z]
    cut[n] = len(kill)
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(me); bm.free()
me = P['P06'].data; bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if (P['P06'].matrix_world @ v.co).z > 1.10], context='VERTS')
bnd = [e for e in bm.edges if e.is_boundary]
bmesh.ops.holes_fill(bm, edges=bnd, sides=0); bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free(); cut['P06'] = 'above 1.10 m'
slivers = 0
for n, o in P.items():
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    while True:
        bad = None
        for f in bm.faces:
            es = list(f.edges); L = max(e.calc_length() for e in es)
            if L > 0.04 and 2 * f.calc_area() / L < 0.003:
                bad = min(es, key=lambda e: e.calc_length()); break
        if bad is None:
            break
        bmesh.ops.collapse(bm, edges=[bad]); slivers += 1
    bm.to_mesh(me); bm.free()
cut['slivers collapsed'] = slivers
for o in bpy.data.objects:
    o.select_set(False)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN removed', len(removed), 'small shells; spike vertices cut', cut, '| parts', len(P), 'tris',
      sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co), 'height', round(float(co[:, 2].max() - co[:, 2].min()), 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
