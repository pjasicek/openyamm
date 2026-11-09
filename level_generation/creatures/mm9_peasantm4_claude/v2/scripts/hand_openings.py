"""Wrist centres for the hvm hands: the hands are separate shells (P03 left, P04 right) whose open proximal edge sits
inside the coat cuff, so the wrist is the centroid of that boundary loop (the ring fit put the right wrist 9 cm down
in the palm). Writes work/hand_openings.json {side: [x, y, z]}. Args: -- <step1 blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
body = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(body.data); bm.transform(body.matrix_world)
piece = bm.verts.layers.int['piece']
out = {}
for side, p in (('L', 3), ('R', 4)):
    loop = [v for e in bm.edges if e.is_boundary for v in e.verts if v[piece] == p]
    c = np.array([tuple(v.co) for v in set(loop)])
    out[side] = [round(float(x), 5) for x in c.mean(0)]
    print('OPENING', side, len(c), out[side], 'spread cm', round(float(np.ptp(c, 0).max()) * 100, 1))
json.dump(out, open(os.path.join(HERE, 'work', 'hand_openings.json'), 'w'), indent=1)
