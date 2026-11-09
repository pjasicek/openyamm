"""H4 revised: rest-roll mismatch between our mesh and the swung source skeleton, per limb, before any clip.
- hand: our palm axes from the hand vertices (Meshy hand weight > 0.6): PCA gives the finger direction (1st) and the
  knuckle width (2nd); the thumb side is the side of the hand where the vertices stick out farthest from the finger
  axis. Source: finger direction hand -> Finger2 base, width Finger1 base -> Finger4 base (index -> pinky), carried
  by the hand's rest swing q. Mismatch = signed angle about our finger direction from the swung source width axis
  (index -> pinky) to ours.
- elbow: hinge of our mesh (compose_joints.py, line fits) vs the source elbow hinge (T-pose: forearm bone's local
  flexion axis assumed = its rest X... measured instead from the source idle clip: axis of the forearm's rotation
  relative to the upper arm), swung by the upper arm's q.
Prints the corrections; writes work/rest_roll.json. Args: -- <rig blend> <set glb>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
blend, glb = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = json.load(open(os.path.join(HERE, 'work', 'source_rest.json')))
JF = json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
OFF = json.loads(bpy.context.scene['rig_offsets'])
body = bpy.data.objects['Body']
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
out = {}


def signed(a, b, axis):
    a = a - axis * (a @ axis); b = b - axis * (b @ axis)
    a /= np.linalg.norm(a); b /= np.linalg.norm(b)
    return math.degrees(math.atan2(np.cross(a, b) @ axis, a @ b))


for s in ('R', 'L'):
    g = body.vertex_groups[f'B_{s}_Hand'].index
    w = np.array([next((e.weight for e in v.groups if e.group == g), 0.0) for v in body.data.vertices])
    hv = co[w > 0.6]
    wrist = np.array(JF['joints'][f'{s}_Hand'])
    c = hv.mean(0)
    U = np.linalg.svd(hv - c, full_matrices=False)[2]
    fdir = U[0] if U[0] @ (c - wrist) > 0 else -U[0]
    width = U[1]
    # thumb side: the thumb sticks out of the palm plane sideways; take the width-side with the larger spread
    proj = (hv - c) @ width
    if np.abs(proj.min()) > np.abs(proj.max()):
        width = -width                                          # width now points toward the thumb side
    q = Quaternion(OFF[f'B_{s}_Hand']['q'])
    h = np.array(SRC[f'B_{s}_Hand']['head'])
    f2 = np.array(SRC[f'B_{s}_Finger2']['head']); f1 = np.array(SRC[f'B_{s}_Finger1']['head']); f4 = np.array(SRC[f'B_{s}_Finger4']['head'])
    sfdir = np.array(q @ Vector(f2 - h)); sfdir /= np.linalg.norm(sfdir)
    s_thumb = np.array(q @ Vector(f1 - f4)); s_thumb /= np.linalg.norm(s_thumb)   # pinky -> index = toward the thumb
    ang = signed(s_thumb, width, fdir)
    out[f'{s}_hand'] = {'roll_deg': round(ang, 1), 'finger_dir_angle_deg': round(math.degrees(math.acos(np.clip(fdir @ sfdir, -1, 1))), 1)}
    print('ROLL', s, 'hand: swung-source thumb side -> our thumb side about the finger axis', round(ang, 1), 'deg;',
          'finger direction differs by', out[f'{s}_hand']['finger_dir_angle_deg'], 'deg')
json.dump(out, open(os.path.join(HERE, 'work', 'rest_roll.json'), 'w'), indent=1)
