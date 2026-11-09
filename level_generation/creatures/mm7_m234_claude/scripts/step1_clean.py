"""Step 1 cleanup of the m150 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P58, normalised so the
helmet crest is 1.80 m above the soles, facing -Y). Removed: P58 (a 4-triangle feather flap floating 2 cm off the left
wing). Wings: P01 (both wings' upper coverts joined across the shoulder blades), P06/P07 (inner feather sheets) and
P11/P12 (outer feather sheets) are joined into 'Wings' (rigged later by wings.py with their own bone chains, so
Meshy's auto-rig and the body joint fits never see them). Every other part is joined into 'Body'. Both carry 'piece'
and 'orig_co' point attributes. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
WINGS = {1, 6, 7, 11, 12}
DROP = {58}
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for n in [n for n in P if int(n[1:]) in DROP]:
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
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


body = join([n for n in P if int(n[1:]) not in WINGS], 'Body')
wings = join([n for n in P if int(n[1:]) in WINGS], 'Wings')
for ob in (body, wings):
    print('CLEAN', ob.name, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), 'verts', len(ob.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
