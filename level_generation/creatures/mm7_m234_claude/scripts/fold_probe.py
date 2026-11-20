"""Debug: wing bone directions (angle in the rest wing plane, degrees from 'out' u toward 'down' v) at rest and after a
pose (elev, sweep, fan per bone from env POSE='e,s,f;e,s,f;...' for the 6 wing bones), both sides. Args: -- <blend>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = json.load(open(os.path.join(HERE, 'work', 'wing_chains.json')))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
SG = {'L': 1.0, 'R': -1.0}
pose = [tuple(float(x) for x in p.split(',')) for p in os.environ.get('POSE', '0,0,0;' * 6).strip(';').split(';')]
for s in 'LR':
    u, v = Vector(CH[s]['u']), Vector(CH[s]['v'])
    AX = {'elev': Vector((0, -SG[s], 0)), 'sweep': Vector((0, 0, -SG[s])), 'fan': u.cross(v).normalized()}
    names = [f'Wing_{s}_1', f'Wing_{s}_2'] + [f'Wing_{s}_F{k}' for k in (1, 2, 3, 4)]
    for name, (e, sw, f) in zip(names, pose):
        R = Matrix.Rotation(math.radians(sw), 3, AX['sweep']) @ Matrix.Rotation(math.radians(e), 3, AX['elev']) @ Matrix.Rotation(math.radians(f), 3, AX['fan'])
        Rr = rig.data.bones[name].matrix_local.to_3x3()
        pb = rig.pose.bones[name]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (Rr.inverted() @ R @ Rr).to_quaternion()
    bpy.context.view_layer.update()
    out = []
    for name in names:
        pb = rig.pose.bones[name]; d = (pb.tail - pb.head).normalized()
        out.append((name.split('_')[-1], round(math.degrees(math.atan2(d.dot(v), d.dot(u))), 0), round(pb.tail.z, 2)))
    print('FOLDPROBE', s, out)
