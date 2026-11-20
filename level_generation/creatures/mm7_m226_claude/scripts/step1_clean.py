"""Step 1 cleanup of the m226 Smart Topology return (work/st_v1_parts.blend, loose parts P00..): nothing removed.
P00 body (torso, arms, legs, boots), P01 head, P03/P04 hands (right/left, separate fingers), P02 shoulder yoke, P05
hair, P06/P11/P14/P18 ponytail, P33/P36 hair strands over the face, P39/P41 eyes, P07/P10 dagger sheath and hilt (right
hip), P08 sword scabbard on the back, belt, straps, studs, spikes and buckles.
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
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN parts', len(P), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
