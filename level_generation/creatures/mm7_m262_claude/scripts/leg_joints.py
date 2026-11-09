"""Bird-leg joints for m262 (after compose_joints.py; overrides the leg entries of work/joints_final.json). The harpy's
legs are a bird's: feathered thighs (part of the body shell P00) down to the HOCK (the backward-bending joint, the
bird's ankle) where the bare orange leg (P01 right / P02 left) starts, a long tarsus, then four toes. Meshy's auto-rig
put a human knee at the hock and a human ankle half way down the tarsus. The humanoid chain is re-used as
Thigh = hip -> knee (inside the feathers, KNEE_T of hip -> hock, KNEE_FWD m forward), Calf = knee -> hock (the bird's
drumstick), Foot = hock -> ball (the tarsus), Toe0 = ball -> toe tips.
Hip stays Meshy's. Hock = centroid of the bare leg's top 3 cm; ball = centroid of the leg piece's slice just above
the level where it splits into the toes (first z, from the top down, with more than one loop). Args: -- <blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNEE_T, KNEE_FWD = float(os.environ.get('KNEE_T', '0.5')), float(os.environ.get('KNEE_FWD', '0.04'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']; me = ob.data
co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
E = np.array([tuple(e.vertices) for e in me.edges])
JF = os.path.join(HERE, 'work', 'joints_final.json'); J = json.load(open(JF))


def ncomp(mask):
    idx = set(np.where(mask)[0].tolist()); par = {i: i for i in idx}
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for a, b in E:
        if a in idx and b in idx:
            ra, rb = f(a), f(b)
            if ra != rb:
                par[ra] = rb
    return len({f(i) for i in idx})


for s, piece in (('R', 1), ('L', 2)):
    m = pv == piece
    z = co[m, 2]; top = z.max()
    hock = co[m & (co[:, 2] > top - 0.03)].mean(0)
    # slice profile: horizontal spread of the leg piece per 1 cm; the tarsus is narrow, the toes spread wide
    prof = []
    for zz in np.arange(0.005, top, 0.01):
        sl = co[m & (np.abs(co[:, 2] - zz) < 0.005)]
        prof.append((zz, float(np.ptp(sl[:, 0]) + np.ptp(sl[:, 1])) if len(sl) > 3 else 0.0))
    prof = np.array(prof)
    if os.environ.get('LEG_DBG'):
        print('LEGPROF', s, ' '.join(f'{a:.2f}:{b:.2f}' for a, b in prof))
    narrow = np.median(prof[(prof[:, 0] > 0.2) & (prof[:, 0] < top - 0.08), 1])
    # ball: the highest level below 0.22 m where the spread exceeds 2.2 x the tarsus (toes and the back toe)
    low = prof[(prof[:, 0] < 0.22) & (prof[:, 1] > 2.2 * narrow)]
    zb = float(low[:, 0].max()) + 0.01 if len(low) else 0.1
    ball = co[m & (np.abs(co[:, 2] - zb) < 0.008)].mean(0)
    hip = np.array(J['joints'][f'{s}_Thigh'])
    knee = hip + (hock - hip) * KNEE_T + np.array([0, -KNEE_FWD, 0])
    J['joints'][f'{s}_Calf'] = knee.tolist(); J['joints'][f'{s}_Foot'] = hock.tolist(); J['joints'][f'{s}_Toe0'] = ball.tolist()
    print('BIRDLEG', s, 'hip', np.round(hip, 3), 'knee', np.round(knee, 3), 'hock', np.round(hock, 3), 'ball', np.round(ball, 3))
json.dump(J, open(JF, 'w'), indent=1)
