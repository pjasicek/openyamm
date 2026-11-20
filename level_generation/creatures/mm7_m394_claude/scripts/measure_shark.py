"""Measure the shark's fin and mouth landmarks on work/step1.blend and write work/joints.json for rig_shark.py.
Pectoral fins: skin vertices outside the body (|x| > BODY_HALF); tip = the farthest from the midline, root = the mean
of the fin vertices in the 5 cm band outside the body. Mouth: the closed slit's fan faces ('mouth'); hinge = its rearmost
lip vertex (mouth corner) moved 3 cm back, chin = the front of the lower jaw; lip line from the corner to the front.
Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[-1]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
me = bpy.data.objects['Body'].data
co = np.array([tuple(v.co) for v in me.vertices]); pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
BODY_HALF = 0.175
skin = (pv == 0)
J = {}
fins = {}
for s, sg in (('L', 1), ('R', -1)):
    sel = skin & (sg * co[:, 0] > BODY_HALF) & (co[:, 1] < 0)
    c = co[sel]; tip = c[np.argmax(sg * c[:, 0])]
    root = c[sg * c[:, 0] < BODY_HALF + 0.05].mean(0)       # the fin's inner band (its attachment)
    root[0] = sg * (BODY_HALF - 0.04)                       # inside the body wall
    fins[s] = {'root': root.round(4).tolist(), 'tip': tip.round(4).tolist()}
J['fins'] = fins
mf = np.zeros(len(me.polygons), np.int32); me.attributes['mouth'].data.foreach_get('value', mf)
mv = sorted({v for p in me.polygons if mf[p.index] for v in p.vertices})
m = co[mv]; corner = m[np.argmax(m[:, 1])]; front = m[np.argmin(m[:, 1])]
zl = float(np.median(m[:, 2]))
J['mouth'] = {'hinge': [0.0, round(float(corner[1]) + 0.03, 4), round(zl - 0.005, 4)],
              'chin': [0.0, round(float(front[1]) - 0.005, 4), round(zl - 0.04, 4)],
              'lip_line_z': [zl, zl],
              'line': [[round(float(corner[1]), 4), zl], [round(float(front[1]), 4), zl]],
              'teeth_split_z': zl}
json.dump(J, open(os.path.join(HERE, 'work', 'joints.json'), 'w'), indent=1)
print('MEASURE', json.dumps(J))
