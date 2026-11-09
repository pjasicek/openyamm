#!/usr/bin/env python3
"""Source-animation pops of the MM8 Dark Dwarf found by clip_scan.py / bone_velocity.py (viewer frame = time x 48),
fixed on the reduced export after smooth_walk_bob.py. Only the named channels and keys change; every other clip and
channel stays byte-identical, and the crossbow (its own channel under B_Pelvis) and both hands keep their world pose.
- Walking, frames 5, 14, 24 and 39: the left elbow swivels about 4 degrees within one key pair (B_L_UpperArm, 530 deg/s;
  neighbours 0.4-0.8 degrees per key) while the hand stays on the grip. B_L_UpperArm is smoothed locally (periodic Gaussian over the
  keys, blended in around each spike), turned back about the shoulder so the wrist keeps its exact path, and B_L_Hand is
  re-solved to keep its world rotation.
- Attack, frame 74: both knees swivel to the loop-out pose in the last two keys (thigh/calf/foot 3-5 degrees per key,
  knee 2 cm; the feet do not move). The knee plane now eases from the attack stance into the final plane over the last
  0.15 s; both legs are re-solved by two-bone IK so ankles and foot rotations are unchanged and the last key is exact.
- Hit, frame 24: the recovery stops dead at 0.5 s (4-6 mm and 1-3 degrees per key, then zero). The time after 0.35 s
  is remapped with a Hermite curve that reaches the final pose with zero velocity at 0.6 s (all animated channels,
  crossbow included, so the grip holds).
- Death, frame 36: the right foot dips 1.46 cm under the floor between keys while the body falls. B_Pelvis is lifted
  by a short Gaussian (1.5 cm, sigma 30 ms) around 0.758 s.
Usage: fix_clips.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from anim_fk import Clip, qmat, slerp  # noqa: E402
from build_actor_lods import read_glb, write_glb, append_accessor  # noqa: E402

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, raw = read_glb(src); binary = bytearray(raw)


def matq(m):
    out = np.empty(m.shape[:-2] + (4,))
    for k, r in enumerate(m.reshape(-1, 3, 3)):
        tr = np.trace(r)
        if tr > 0:
            s = np.sqrt(tr + 1) * 2; q = [(r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s, s / 4]
        else:
            i = int(np.argmax(np.diag(r))); j, kk = (i + 1) % 3, (i + 2) % 3
            s = np.sqrt(1 + r[i, i] - r[j, j] - r[kk, kk]) * 2; q = [0, 0, 0, (r[kk, j] - r[j, kk]) / s]
            q[i] = s / 4; q[j] = (r[j, i] + r[i, j]) / s; q[kk] = (r[kk, i] + r[i, kk]) / s
        out.reshape(-1, 4)[k] = q
    return out / np.linalg.norm(out, axis=-1, keepdims=True)


def between(a, b):
    a = a / np.linalg.norm(a, axis=1, keepdims=True); b = b / np.linalg.norm(b, axis=1, keepdims=True)
    v = np.cross(a, b); c = np.einsum('ij,ij->i', a, b); vx = np.zeros((len(a), 3, 3))
    vx[:, 0, 1], vx[:, 0, 2], vx[:, 1, 0], vx[:, 1, 2], vx[:, 2, 0], vx[:, 2, 1] = -v[:, 2], v[:, 1], v[:, 2], -v[:, 0], -v[:, 1], v[:, 0]
    return np.eye(3) + vx + vx @ vx / (1 + c)[:, None, None]


rot = lambda m: m[:, :3, :3] / np.linalg.norm(m[:, :3, :3], axis=1, keepdims=True)


def write(clip, name, path, values):
    i = clip.idx[name]; t, _, ch = clip.chan[i, path]; s = clip.anim['samplers'][ch['sampler']]
    assert len(t) == len(values) == len(clip.times), (name, path)
    out = np.array(values, float)
    if path == 'rotation':
        out = out / np.linalg.norm(out, axis=1, keepdims=True)
        for k in range(1, len(out)):
            if np.dot(out[k], out[k - 1]) < 0:
                out[k] = -out[k]
    acc = dict(doc['accessors'][s['output']]); acc.pop('min', None); acc.pop('max', None)
    s['output'] = append_accessor(doc, binary, acc, np.ascontiguousarray(out, '<f4').tobytes())


def smoothstep(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


report = {}
# --- Walking: left elbow swivel spike ------------------------------------------------------------------------------
c = Clip(None, 'Walking', doc, binary); T = len(c.times); n = T - 1
q = c.value(c.idx['B_L_UpperArm'], 'rotation', [0, 0, 0, 1])
step = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(q[1:] * q[:-1], 1)), 0, 1)))
# spikes: a step over 2.5 degrees and 3x the median step of the four keys on each side (0.4-0.8 degrees)
spikes = [k + 1 for k in range(len(step)) if step[k] > 2.5 and step[k] > 3 * np.median(
    np.concatenate([step[max(k - 6, 0):max(k - 1, 0)], step[k + 2:k + 7]]))]
kcs = sorted({k for k in spikes if k - 1 not in spikes}); report['walk_spike_keys'] = kcs
SIG = 3.0; kern = np.exp(-0.5 * (np.arange(-9, 10) / SIG) ** 2); kern /= kern.sum()
qs = np.empty_like(q)
for k in range(T):
    acc = np.zeros(4)
    for o, w in zip(range(-9, 10), kern):
        x = q[(k + o) % n]; acc += w * (x if np.dot(x, q[k]) >= 0 else -x)
    qs[k] = acc / np.linalg.norm(acc)
wgt = np.zeros(T)
for kc in kcs:
    d = np.minimum(np.abs(np.arange(T) - kc), n - np.abs(np.arange(T) - kc))
    wgt = np.maximum(wgt, np.where(d <= 4, 1.0, np.where(d >= 10, 0.0, 0.5 + 0.5 * np.cos(np.pi * (d - 4) / 6))))
wgt[-1] = wgt[0]
qn = np.array([slerp(a, b, w) for a, b, w in zip(q, qs, wgt)])
qn[-1] = qn[0]  # the last key repeats the first (loop)
over = {(c.idx['B_L_UpperArm'], 'rotation'): qn}
Wcl = c.world('B_L_Clavicle'); Wua0 = c.world('B_L_UpperArm'); Wh0 = c.world('B_L_Hand')
Wua1 = c.world('B_L_UpperArm', over); Wh1 = c.world('B_L_Hand', over)
sh = Wua0[:, :3, 3]; Rc = between(Wh1[:, :3, 3] - sh, Wh0[:, :3, 3] - sh)
Rua = Rc @ rot(Wua1); qua = matq(np.linalg.inv(rot(Wcl)) @ Rua)
over = {(c.idx['B_L_UpperArm'], 'rotation'): qua}
Wfa = c.world('B_L_Forearm', over)
qh = matq(np.linalg.inv(rot(Wfa)) @ rot(Wh0)); over[c.idx['B_L_Hand'], 'rotation'] = qh
Wh2 = c.world('B_L_Hand', over)
report['walk_hand_error_mm'] = round(float(np.linalg.norm(Wh2[:, :3, 3] - Wh0[:, :3, 3], axis=1).max() * 1000), 3)
report['walk_hand_rot_error'] = float(np.abs(rot(Wh2) - rot(Wh0)).max())
st2 = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(qua[1:] * qua[:-1], 1)), 0, 1)))
report['walk_upperarm_max_step_deg'] = (round(float(step.max()), 2), round(float(st2.max()), 2))
write(c, 'B_L_UpperArm', 'rotation', qua); write(c, 'B_L_Hand', 'rotation', qh)

# --- Attack: knee swivel snap in the last two keys -----------------------------------------------------------------
c = Clip(None, 'Attack', doc, binary); T = len(c.times); t = c.times
k0 = int(np.searchsorted(t, t[-1] - 0.15)); kh = T - 3  # last key before the snap
w = smoothstep((np.arange(T) - k0) / (T - 1 - k0))
P = rot(c.world('B_Pelvis'))
for s in 'LR':
    Wt, Wc, Wf = (c.world(f'B_{s}_{b}') for b in ('Thigh', 'Calf', 'Foot'))
    H, K, A = Wt[:, :3, 3], Wc[:, :3, 3], Wf[:, :3, 3]
    l1 = np.linalg.norm(K - H, axis=1).mean(); l2 = np.linalg.norm(A - K, axis=1).mean()
    dvec = A - H; dl = np.linalg.norm(dvec, axis=1); u = dvec / dl[:, None]
    bend = (K - H) - np.einsum('ij,ij->i', K - H, u)[:, None] * u; bend /= np.linalg.norm(bend, axis=1, keepdims=True)
    hold = bend.copy(); hold[kh + 1:] = bend[kh]
    nb = (1 - w)[:, None] * hold + w[:, None] * bend[-1]
    nb -= np.einsum('ij,ij->i', nb, u)[:, None] * u; nb /= np.linalg.norm(nb, axis=1, keepdims=True)
    a = (l1 * l1 - l2 * l2 + dl * dl) / (2 * dl); h = np.sqrt(np.maximum(l1 * l1 - a * a, 0))
    K2 = H + a[:, None] * u + h[:, None] * nb
    Rt = between(K - H, K2 - H) @ rot(Wt); Rc_ = between(A - K, A - K2) @ rot(Wc)
    sel = np.arange(T) >= k0
    for name, R in ((f'B_{s}_Thigh', np.linalg.inv(P) @ Rt), (f'B_{s}_Calf', np.linalg.inv(Rt) @ Rc_),
                    (f'B_{s}_Foot', np.linalg.inv(Rc_) @ rot(Wf))):
        old = c.value(c.idx[name], 'rotation', [0, 0, 0, 1]); new = old.copy(); new[sel] = matq(R[sel])
        write(c, name, 'rotation', new)
    report[f'attack_knee_{s}_end_error_mm'] = round(float(np.linalg.norm(K2[-1] - K[-1]) * 1000), 3)
c = Clip(None, 'Attack', doc, binary)
for s in 'LR':
    Wf2 = c.world(f'B_{s}_Foot'); Wk2 = c.world(f'B_{s}_Calf')
    report[f'attack_knee_{s}_max_step_mm'] = round(float(np.linalg.norm(np.diff(Wk2[k0 - 1:, :3, 3], axis=0), axis=1).max() * 1000), 2)
    report[f'attack_ankle_{s}_error_mm'] = round(float(np.linalg.norm(Wf2[:, :3, 3] - Clip(src, 'Attack').world(f'B_{s}_Foot')[:, :3, 3], axis=1).max() * 1000), 3)

# --- Hit: ease the recovery into its final pose --------------------------------------------------------------------
c = Clip(None, 'Hit', doc, binary); t = c.times; T = len(t)
moving = [any(np.abs(v[k] - v[k - 1]).max() > 1e-5 for (tt, v, _) in c.chan.values() if len(tt) == T) for k in range(1, T)]
te = t[max(k for k, m in enumerate(moving) if m) + 1]; ta = te - 0.15; tend = t[-1]
L, S = tend - ta, te - ta
def remap(x):
    if x <= ta:
        return x
    uu = (x - ta) / L
    return ta + (uu ** 3 - 2 * uu ** 2 + uu) * L + (-2 * uu ** 3 + 3 * uu ** 2) * S
st = np.array([remap(x) for x in t]); report['hit_motion_end_s'] = round(float(te), 4)
for (i, path), (tt, v, _) in c.chan.items():
    if len(tt) != T:
        continue
    new = v.copy()
    for k in np.where(t > ta)[0]:
        j = min(int(np.searchsorted(t, st[k], 'right')) - 1, T - 2); f = (st[k] - t[j]) / (t[j + 1] - t[j])
        new[k] = slerp(v[j], v[j + 1], f) if path == 'rotation' else v[j] * (1 - f) + v[j + 1] * f
    write(c, c.nodes[i]['name'], path, new)

# --- Death: lift the pelvis over the right-foot floor dip ----------------------------------------------------------
c = Clip(None, 'Death', doc, binary); t = c.times
tr = c.value(c.idx['B_Pelvis'], 'translation', [0, 0, 0]).copy()
lift = 0.015 * np.exp(-0.5 * ((t - 0.758) / 0.030) ** 2); tr[:, 1] += lift
write(c, 'B_Pelvis', 'translation', tr); report['death_lift_cm_max'] = round(float(lift.max() * 100), 2)

write_glb(dst, doc, bytes(binary))
for k, v in report.items():
    print('FIX', k, v)
print('WROTE', dst)
