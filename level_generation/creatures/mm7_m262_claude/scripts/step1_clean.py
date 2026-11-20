"""Step 1 cleanup of the m262 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P114, normalised so the
hair top is 1.70 m above the talons, facing -Y). Labels per part (work/part_labels.json, from the part report): body
(P00 torso, feathered hips and thighs, head), legs (P01/P02 bare bird legs and feet), hands with bracers (P03/P04),
bracers (P09/P10), eyes (P13/P14), gold waist band halves (P34/P74), crotch tuft (P38), hair shells and strands,
tail feather cards (behind the hips) and WING pieces (the two wing sheets P06/P07 plus 72 feather cards on the wings
and between the shoulder blades). Nothing is removed. Wing parts are joined into 'Wings' (rigged later by wings_rig.py
so Meshy's auto-rig and the body joint fits never see them); everything else into 'Body'. Both carry 'piece' and
'orig_co' point attributes. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = json.load(open(os.path.join(HERE, 'work', 'part_labels.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
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


wing = [n for n in P if LAB[str(int(n[1:]))] == 'wing']
body = join([n for n in P if n not in wing], 'Body')
wings = join(wing, 'Wings')
for ob in (body, wings):
    print('CLEAN', ob.name, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), 'verts', len(ob.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
