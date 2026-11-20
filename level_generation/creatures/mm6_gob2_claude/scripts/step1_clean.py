"""Step 1 cleanup of the goblin Smart Topology return (work/st_v1_parts.blend, loose parts P00..):
- the eye shells (P25, P26: separate balls in the sockets) are removed; eyes are painted by the head retexture;
- the side skirt strips P56/P63 are removed (G6 walk contacts).
Joins the rest into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (positions for the weight
transfer from Meshy's rigged copy). The triangle budget is reduced after weighting (reduce_rigged.py).
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
# P56/P63: the two side skirt strips hang exactly where the goblin's long arms swing (G6: the walking hand passed
# 4.8 cm through P56 at any arm abduction); thirteen strips remain and the pouch covers the right side
DROP = {'P25', 'P26', 'P56', 'P63'}
for n in DROP:
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
# P04, the belt pouch, hangs 5 cm off the right hip and the walking forearm passes 2.4 cm into it (G6, 7 deg arm
# abduction): tuck it 2.5 cm toward the body axis (it stays 2.6 cm off the skin)
pouch = P['P04']; pc = sum((v.co for v in pouch.data.vertices), pouch.data.vertices[0].co * 0) / len(pouch.data.vertices)
d = pc.copy(); d.z = 0; d.normalize()
for v in pouch.data.vertices:
    v.co -= d * 0.025
for o in bpy.data.objects:
    o.select_set(False)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.select_set(True)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
body.data.materials.clear()
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons))
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
