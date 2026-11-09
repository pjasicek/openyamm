"""Left (bow) arm posture from the mirrored right arm: the right arm holds its palm toward the thigh within the shared
gate's roll limits (upper arm, forearm, wrist), the left arm had the opposite roll (palm out, thumb back). The left
UpperArm, UpperArmTwist, Forearm, ForearmTwist and Hand take the right arm's chest-relative rotations mirrored across
the chest's sagittal plane (bind-pose correction per bone); fingers keep their bow grip, the bow (child of the hand)
follows. Walking/Running mirror the right arm half a cycle later (opposite swing). Weight per clip as fix_bow_hand.py:
full for the lowered-bow clips, by forearm drop for Attack/Cast (the draw is untouched), fading out between 15 and
25 % of Death (before the bow is released), none for Dead. Usage: mirror_left_arm.py <in.glb> <out.glb>"""
import copy, os, struct, sys
from pathlib import Path
import numpy as np
from gltf_fk import Gltf, qmat, matq, slerp
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import write_glb, append_accessor, accessor_bytes  # noqa: E402
import bow_hand_probe as probe  # noqa: E402

src, dst = sys.argv[1], sys.argv[2]
g = Gltf(src); probe.g = g; N = g.names
BONES = ['UpperArm', 'UpperArmTwist', 'Forearm', 'ForearmTwist', 'Hand']
L = [N['B_L_' + b] for b in BONES]; R = [N['B_R_' + b] for b in BONES]
CHEST = g.parent[N['B_L_Clavicle']]; assert CHEST == g.parent[N['B_R_Clavicle']]
DEATH_FADE = [float(x) for x in os.environ.get('DEATH_FADE', '0.15,0.25').split(',')]

# bind-pose world matrices from the inverse bind matrices
d = g.doc; skin = d['skins'][0]
ibm = np.array(struct.unpack(f'<{16 * len(skin["joints"])}f', accessor_bytes(d, g.bin, skin['inverseBindMatrices']))).reshape(-1, 4, 4)
bind = {j: np.linalg.inv(m.T) for j, m in zip(skin['joints'], ibm)}
rot = lambda m: m[:3, :3] / np.linalg.norm(m[:3, :3], axis=0)
chest_bind = rot(bind[CHEST])
lat = chest_bind.T @ (bind[N['B_L_Clavicle']][:3, 3] - bind[N['B_R_Clavicle']][:3, 3]); lat /= np.linalg.norm(lat)
M = np.eye(3) - 2 * np.outer(lat, lat)    # mirror in chest-local coordinates
C = {l: np.linalg.inv(M @ (chest_bind.T @ rot(bind[r])) @ M) @ (chest_bind.T @ rot(bind[l])) for l, r in zip(L, R)}


def smooth(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


ABD = np.radians(float(os.environ.get('ABD_DEG', '8')))   # outward swing at the shoulder (bow clears the thigh)


def weight(clip, t):
    """time-based blends of ~0.4 s keep rotation steps and accelerations inside the shared gate limits"""
    if clip == 'Dead':
        return 0.0
    if clip == 'Death':   # done by 0.5 s, when the bow is released
        return 1 - float(smooth((t - 0.1) / 0.4))
    if clip in ('Attack', 'Cast'):   # out by 0.40 s (release 0.49 s), back from 0.72 s (bow lowered again)
        return float(max(1 - smooth(t / 0.40), smooth((t - 0.72) / (g.duration(clip) - 0.72))))
    return 1.0


def swing_twist_y(q):
    """q = swing * twist about local +Y; returns (swing quaternion, twist angle)"""
    tw = 2 * np.arctan2(q[1], q[3]); qt = np.array([0, np.sin(tw / 2), 0, np.cos(tw / 2)])
    from gltf_fk import qmul
    return qmul(q, qt * np.array([-1, -1, -1, 1])), tw


def blend(q_old, q_new, w):
    """bend (swing) and roll (twist about the bone axis) blended separately: the elbow stays in its hinge plane"""
    from gltf_fk import qmul
    s0, t0 = swing_twist_y(q_old); s1, t1 = swing_twist_y(q_new)
    if np.dot(s0, s1) < 0: s1 = -s1
    dt = (t1 - t0 + np.pi) % (2 * np.pi) - np.pi
    tw = t0 + dt * w
    return qmul(slerp(s0, s1, w), np.array([0, np.sin(tw / 2), 0, np.cos(tw / 2)]))


def target(clip, t):
    """new local rotations (quaternions) of the left arm bones at time t"""
    T = g.duration(clip)
    tp = (t + T / 2) % T if clip in ('Walking', 'Running') else t
    w = weight(clip, t); out = {}; ov = {}
    chest_t = rot(g.world(clip, CHEST, t)); chest_p = rot(g.world(clip, CHEST, tp))
    fwd_axis = chest_t @ np.cross(lat, chest_bind.T @ np.array([0.0, 1, 0])); fwd_axis /= np.linalg.norm(fwd_axis)
    for l, r in zip(L, R):
        rel = chest_p.T @ rot(g.world(clip, r, tp))
        world = rot_axis(fwd_axis, ABD_SIGN * ABD) @ chest_t @ (M @ rel @ M) @ C[l]
        parent = rot(g.world(clip, g.parent[l], t, ov))
        q_new = matq(parent.T @ world); q_old = g.sample(clip, l, 'rotation', t)
        if np.dot(q_new, q_old) < 0: q_new = -q_new
        out[l] = blend(q_old, q_new, w)
        ov[(l, 'rotation')] = (lambda tt, q=out[l]: q)
    return out, w


def rot_axis(axis, a):
    from gltf_fk import qaxis
    return qmat(qaxis(axis, a))


def abd_sign():
    """+1 or -1 so that the swing moves the left elbow away from the body (Standing, frame 0)"""
    sh = g.world('Standing', L[0], 0)[:3, 3]; el = g.world('Standing', L[2], 0)[:3, 3]
    chest = rot(g.world('Standing', CHEST, 0)); left = chest @ lat
    fwd = chest @ np.cross(lat, chest_bind.T @ np.array([0.0, 1, 0])); fwd /= np.linalg.norm(fwd)
    return 1 if np.dot(rot_axis(fwd, 0.2) @ (el - sh), left) > np.dot(el - sh, left) else -1


def keys(t):
    t = np.unique(np.asarray(t, np.float32)).astype(float); o = [t[0]]
    for x in t[1:]:
        if x - o[-1] > 1e-4: o.append(x)
    return np.array(o)


ABD_SIGN = abd_sign()
doc = copy.deepcopy(d); binary = bytearray(g.bin)
for a in doc['animations']:
    clip = a['name']; T = g.duration(clip)
    if weight(clip, 0.0) == 0 and clip == 'Dead':
        continue
    times = keys(np.r_[np.arange(0, T + 1e-6, 1 / 48), T])
    rows = [target(clip, t) for t in times]
    if max(w for _, w in rows) == 0:
        continue
    tin = append_accessor(doc, binary, {'componentType': 5126, 'type': 'SCALAR', 'count': len(times),
                                        'min': [float(times[0])], 'max': [float(times[-1])]}, struct.pack(f'<{len(times)}f', *times))
    for l in L:
        vals = np.array([r[0][l] / np.linalg.norm(r[0][l]) for r in rows])
        out = append_accessor(doc, binary, {'componentType': 5126, 'type': 'VEC4', 'count': len(times)},
                              struct.pack(f'<{vals.size}f', *vals.reshape(-1)))
        c = next((c for c in a['channels'] if c['target']['node'] == l and c['target']['path'] == 'rotation'), None)
        a['samplers'].append({'input': tin, 'output': out, 'interpolation': 'LINEAR'})
        if c is None:
            a['channels'].append({'sampler': len(a['samplers']) - 1, 'target': {'node': l, 'path': 'rotation'}})
        else:
            c['sampler'] = len(a['samplers']) - 1
    print('MIRRORED', clip, len(times), 'keys')
for a in doc['animations']:
    used = sorted({c['sampler'] for c in a['channels']}); remap = {o: i for i, o in enumerate(used)}
    a['samplers'] = [a['samplers'][i] for i in used]
    for c in a['channels']:
        c['sampler'] = remap[c['sampler']]
write_glb(Path(dst), doc, bytes(binary))
print('->', dst)
