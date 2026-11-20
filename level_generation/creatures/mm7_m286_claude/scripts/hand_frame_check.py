"""G3 hand-frame gate (numbers): the source fingers carried by our hand's rest swing vs our fitted fingers. Per finger
the angle between the carried source direction (knuckle -> distal joint) and ours, and the knuckle offset across the
hand (thumb side positive). Pass: every finger within ~25 deg, thumb on the same side. Args: -- <rig blend>"""
import bpy, sys, os, json, math
from mathutils import Vector, Quaternion
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
SRC = json.load(open(os.path.join(HERE, 'work', 'source_rest.json')))
FJ = json.load(open(os.path.join(HERE, 'work', 'finger_joints.json')))
off = json.loads(bpy.context.scene['rig_offsets'])
for sd in ('R', 'L'):
    qh = Quaternion(off[f'B_{sd}_Hand']['q']); h0 = Vector(SRC[f'B_{sd}_Hand']['head'])
    wr = rig.data.bones[f'B_{sd}_Hand'].head_local
    out = []
    for f, name in [(0, 'thumb')] + [(i, {1: 'index', 2: 'middle', 3: 'ring', 4: 'pinky'}[i]) for i in tuple(int(x) for x in __import__('os').environ.get('FINGERS', '1,2,3,4').split(','))]:
        a = f'B_{sd}_Finger{f}'; c = SRC[a]['child']; g = SRC[c]['child']
        s_dir = qh @ (Vector(SRC[g]['head']) - Vector(SRC[a]['head']))
        o_dir = Vector(FJ[sd][g]) - Vector(FJ[sd][a])
        s_kn = qh @ (Vector(SRC[a]['head']) - h0); o_kn = Vector(FJ[sd][a]) - wr
        out.append(f'{name} dir {math.degrees(s_dir.angle(o_dir)):5.1f} kn-angle {math.degrees(s_kn.angle(o_kn)):5.1f}')
    print('HANDFRAME', sd, ' | '.join(out))
