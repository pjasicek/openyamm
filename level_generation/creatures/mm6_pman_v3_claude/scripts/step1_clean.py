"""Step 1 cleanup of the hvm Smart Topology return (work/st_v1_parts.blend, loose parts P00..): nothing removed.
P00 tunic (with the belt), P01 trouser legs, P02 head + neck, P03/P04 hands with forearms (right/left), P05 long hair,
P06/P07 shoes, P08 buckle, P09 hanging belt strap end, P10/P11 eyes, P12.. brass studs (neckline, cuffs, belt).
Joins the parts into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (positions as uploaded to
Meshy's auto-rig). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weld_neck                                     # pm3: the grafted head's neck rim welded to the body's
weld_neck.weld_from_graft(body, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work'))
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN parts', len(P), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
