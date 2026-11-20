"""Step 1 of the 7m452 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P15, 1.8 m): P15 is a stray
45-tri blob beside the right knee: removed. Kept: P00 torso and arms (one shell: the sleeveless tunic top and the bare
arms), P01 head (topknot and ears in it), P02 trousers, P03 tunic skirt with the belt, P04/P05 hands (L +x / R),
P06/P07 boots (L / R), P08/P09 bracers (L / R), P10 buckle, P11/P12 eyes, P13 mouth, P14 a bead at the tunic neck.
Joins the parts into 'Body' with a 'piece' point attribute and 'orig_co'. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for n in ['P15']:
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
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
print('CLEAN parts', len(P), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co),
      'height', round(float(co[:, 2].max() - co[:, 2].min()), 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
