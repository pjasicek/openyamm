#!/usr/bin/env python3
"""An attack clip retargeted from a donor body's clip (MM9 or LoMM, Bip01 skeleton) onto an installed MM6-MM8 B_*
body, without Blender (attacks stream, MM6-MM8 audit fixes, 2026-11-11).

    donor_attack.py <job.json> [--out <glb>] [--no-cloth]

Run from the repository root; paths in the job are relative to it. Job keys:
  target       installed GLB to start from (the project's work/before_attacks copy)
  out          output GLB (the target with the new clip added or replaced; everything else byte-for-byte, the old
               clip's accessors stay unreferenced in the buffer)
  clip         output clip name (default Attack); replace: true drops an existing clip of that name first
  donor        donor GLB (an installed MM9 body) or a LithTech .abc (LoMM; read directly); donor_clip (an ABC clip may
               join several animations with '+'); donor_ref: "clip0"
               (default: the donor clip's first frame) or a donor clip name whose t = 0 is the reference
  timing       {length, impact, donor_impact[, donor_start, donor_end]}: output clip length and the impact time;
               donor time is piecewise linear through (0, donor_start), (impact, donor_impact), (length, donor_end)
  facing       "axis" (default: both bodies face +Z, as MM9, LoMM and our GLBs do) or "hips" (from hips and toes)
  mirror       true: the donor's left side drives our right side (and the motion is reflected)
  gains        per group scale of the donor's world rotation change (rot power) and travel:
               {pelvis, spine, neck, head, arms, legs, travel, lift}
  map          extra or replacing {target bone: donor bone}
  blend_in / blend_out   seconds eased from and back to our Standing frame 0 (smoothstep on the deltas)
  feet         "ik" (default): ankles follow the donor's ankle travel (scaled by leg length) with two-bone IK;
               "planted": ankles stay where Standing has them
  floor        "lift" (default): the whole body is raised where a foot/toe vertex goes under the floor
  cloth        list of cloth_sim.py configs (gait rollout h11, numpy robe/cape chains); simulated on the clip padded
               with 0.7 s of Standing on both ends (the sim is periodic) and cut back
  ring_skirt   {scripts: <dir holding ring_skirt.py + gaitlib.py>, cfg: {...}}: PeasantF3's skirt cage fitted per sample
  travel_extra [[[x, y, z] metres in the body frame, t0, t1, t2, t3], ...]: authored pelvis travel (a brace, a lunge)
  passthrough  node globs that take the donor clip's own locals at the remapped time (self-donor: the model's own clip
               as donor, for its fingers, props, strings and bolt)
  keep         node globs that keep the target's Standing frame 0 locals (fingers, props: default all unmapped)
  arm_direction {bones: [...], ramp: [t0, t1, t2, t3], weight}: those bones take the donor's world bone direction
               (eased in t0..t1, out t2..t3), roll from the change; for donors whose idle limbs differ from ours
  trunk_yaw_max  degrees: soft limit (tanh) of each trunk bone's turn about the vertical; arms follow the chest
  spine_spread true: B_Spine and B_Spine1 take 1/3 and 2/3 of the turn between the pelvis and B_Spine2
  travel_node  a node above the pelvis that takes the pelvis travel instead (Efreeti: BodyRoot carries the tail)
  twist        true (default): B_*_ForearmTwist / B_*_UpperArmTwist re-derived from the new arm (0.6 of the hand's
               roll about the forearm; -0.5 of the upper arm's own roll), as mm6_natm_claude/scripts/twist_bones.py
  wrist_limit  {knee, max, twist_max} degrees (default 40, 58, 75): soft limits of the hand's swing and twist
               against its forearm, relative to Standing (playbook: swing <= 60, twist <= ~90)
  extra        {"pre": [[bone, [x, y, z] degrees about the body frame (x left, y up, z forward), t0, t1, t2, t3], ...]}
               an authored extra rotation, eased in t0..t1, held, eased out t2..t3 (applied in world after retarget);
               a 7th element "chain" turns the mapped descendants with it (a rigid turn of the whole limb)

Retarget: world-rotation change copy. For a mapped bone, our world rotation = A D(t) D(ref)^-1 A^-1 R(Standing),
where D is the donor bone's world rotation and A turns the donor's facing onto ours (both skeletons Y up; facing from
the hips and the toes). The pelvis travels by the donor's pelvis travel x (our leg length / donor leg length).
"""
import argparse
import fnmatch
import json
import math
from pathlib import Path
import sys
import types

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
import glb_pose  # noqa: E402

H11 = ROOT / 'level_generation/creatures/gait_rollout_20261031/h11/scripts'
UP = np.array([0.0, 1.0, 0.0])
SIDES = ('L', 'R')
CORE = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head']
LIMBS = ['Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot', 'Toe0']
GROUP = {'B_Pelvis': 'pelvis', 'B_Spine': 'spine', 'B_Spine1': 'spine', 'B_Spine2': 'spine', 'B_Neck': 'neck',
         'B_Head': 'head'}
for _s in SIDES:
    for _l in LIMBS:
        GROUP[f'B_{_s}_{_l}'] = 'legs' if _l in ('Thigh', 'Calf', 'Foot', 'Toe0') else 'arms'


def unit(v):
    return v / max(float(np.linalg.norm(v)), 1e-12)


def rot_of(m):
    r = np.asarray(m[:3, :3], dtype=float)
    u, _, vt = np.linalg.svd(r)
    q = u @ vt
    if np.linalg.det(q) < 0:
        u[:, -1] *= -1
        q = u @ vt
    return q


def axis_angle(axis, angle):
    a = unit(np.asarray(axis, dtype=float))
    k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(angle) * k + (1 - math.cos(angle)) * k @ k


def rot_between(u, v):
    u, v = unit(u), unit(v)
    axis = np.cross(u, v)
    s = float(np.linalg.norm(axis))
    c = float(np.clip(u @ v, -1, 1))
    if s < 1e-9:
        if c > 0:
            return np.eye(3)
        perp = unit(np.cross(u, [1.0, 0, 0] if abs(u[0]) < 0.9 else [0, 1.0, 0]))
        return axis_angle(perp, math.pi)
    return axis_angle(axis / s, math.atan2(s, c))


def rot_power(r, w):
    if abs(w - 1.0) < 1e-9:
        return r
    q = glb_pose.matrix_quaternion(r)
    if q[3] < 0:
        q = -q
    angle = 2 * math.atan2(float(np.linalg.norm(q[:3])), float(q[3]))
    if angle < 1e-9:
        return np.eye(3)
    return axis_angle(q[:3], angle * w)


def yaw_of(v):
    return math.atan2(v[0], v[2])


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


class Skeleton:
    def __init__(self, path):
        self.glb = glb_pose.Glb(path)
        self.model = glb_pose.Model(self.glb)
        self.nodes = self.glb.json['nodes']
        self.idx = {}
        for i, n in enumerate(self.nodes):
            self.idx.setdefault(n.get('name'), i)
        self.parent = self.model.parent
        self.order = self.model.order

    def world(self, clip, t):
        local = self.model.sample(clip, float(t))
        return local, self.model.world(local)

    def pos(self, W, name):
        return W[self.idx[name], :3, 3].copy()


class AbcSkeleton:
    """A LithTech ABC (LoMM, MM9) read with tools/mm9_import_discovery/convert_abc_model.read_abc, posed like Skeleton:
    node-local translation and (x, y, z, w) rotation keys, linear / slerp between keys, Y up, facing +Z as the
    converted MM9 GLBs. `clip` may join several ABC animations with '+' (played one after the other)."""

    def __init__(self, path):
        sys.path.insert(0, str(ROOT / 'tools/mm9_import_discovery'))
        import convert_abc_model  # noqa: E402
        m = convert_abc_model.read_abc(Path(path))
        self.nodes = [{'name': n.name} for n in m.nodes]
        self.idx = {n.name: i for i, n in enumerate(m.nodes)}
        self.parent = [n.parent_index if n.parent_index is not None else -1 for n in m.nodes]
        self.order = sorted(range(len(m.nodes)), key=self._depth)
        self.anims = {a.name: a for a in m.animations}
        self.model = types.SimpleNamespace(clip_times=self.clip_times)

    def _depth(self, i):
        d = 0
        while self.parent[i] >= 0:
            i = self.parent[i]
            d += 1
        return d

    def _parts(self, clip):
        parts, start = [], 0.0
        for name in clip.split('+'):
            a = self.anims[name]
            times = np.array([k.time_ms / 1000.0 for k in a.keyframes])
            parts.append((start, a, times))
            start += float(times[-1])
        return parts

    def pos(self, W, name):
        return W[self.idx[name], :3, 3].copy()

    def clip_times(self, clip):
        out = []
        for start, _, times in self._parts(clip):
            out += list(start + times)
        return sorted(set(out))

    def world(self, clip, t):
        parts = self._parts(clip)
        start, a, times = parts[-1]
        for p in parts:
            if t <= p[0] + p[2][-1] + 1e-9:
                start, a, times = p
                break
        tl = min(max(t - start, times[0]), times[-1])
        k = int(np.clip(np.searchsorted(times, tl, side='right') - 1, 0, len(times) - 1))
        k2 = min(k + 1, len(times) - 1)
        f = 0.0 if k2 == k else (tl - times[k]) / max(times[k2] - times[k], 1e-12)
        W = np.zeros((len(self.nodes), 4, 4))
        for i in self.order:
            tr = a.node_transforms[i]
            p0, p1 = np.array(tr[k].translation), np.array(tr[k2].translation)
            q0, q1 = np.array(tr[k].rotation), np.array(tr[k2].rotation)
            q = glb_pose.slerp(q0, q1, f)
            q = q / np.linalg.norm(q)
            M = glb_pose.trs_matrix(p0 + f * (p1 - p0), q, np.ones(3))
            W[i] = M if self.parent[i] < 0 else W[self.parent[i]] @ M
        return None, W


def donor_map(donor, extra):
    names = set(donor.idx)

    def pick(*cands):
        for c in cands:
            if c in names:
                return c
        return None
    m = {'B_Pelvis': pick('Bip01 Pelvis'), 'B_Spine': pick('Bip01 Spine'), 'B_Spine1': pick('Bip01 Spine1'),
         'B_Spine2': pick('Bip01 Spine3', 'Bip01 Spine2', 'Bip01 Spine1'), 'B_Neck': pick('Bip01 Neck'),
         'B_Head': pick('Bip01 Head')}
    for s in SIDES:
        for limb in LIMBS:
            m[f'B_{s}_{limb}'] = pick(f'Bip01 {s} {limb}')
    m.update(extra or {})
    return {k: v for k, v in m.items() if v}


def facing(sk, W, lname='B_L_Thigh', rname='B_R_Thigh', feet=None):
    left = sk.pos(W, lname) - sk.pos(W, rname)
    left[1] = 0
    fwd = unit(np.cross(unit(left), UP))
    toes = None
    if feet:
        toes = np.zeros(3)
        for foot, toe in feet:
            if foot in sk.idx and toe in sk.idx:
                toes += sk.pos(W, toe) - sk.pos(W, foot)
        toes[1] = 0
        toes = unit(toes) if np.linalg.norm(toes) > 1e-9 else None
    return fwd, unit(left), toes


def leg_length(sk, W, name):
    """name(side, limb) -> node name"""
    out = []
    for s in SIDES:
        t, c, f = (sk.pos(W, name(s, l)) for l in ('Thigh', 'Calf', 'Foot'))
        out.append(np.linalg.norm(c - t) + np.linalg.norm(f - c))
    return float(np.mean(out))


def twist_about(q, axis):
    """Twist angle of quaternion q (x, y, z, w) about a unit axis."""
    v = np.asarray(q[:3])
    a = 2 * math.atan2(float(v @ axis), float(q[3]))
    return (a + math.pi) % (2 * math.pi) - math.pi


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('job')
    ap.add_argument('--out')
    ap.add_argument('--no-cloth', action='store_true')
    ap.add_argument('--set', default='{}', help='JSON merged into the job (one level deep for dicts; cloth: a dict '
                    'merged into every cloth config)')
    ap.add_argument('--report')
    args = ap.parse_args()
    job = json.loads(Path(args.job).read_text())
    for key, value in json.loads(args.set).items():
        if key == 'cloth' and isinstance(value, dict):
            for cfg in job.get('cloth', []):
                for k, v in value.items():
                    if v is None:
                        cfg.pop(k, None)
                    else:
                        cfg[k] = v
        elif isinstance(value, dict) and isinstance(job.get(key), dict):
            job[key].update(value)
        else:
            job[key] = value
    T = Skeleton(ROOT / job['target'])
    D = AbcSkeleton(ROOT / job['donor']) if job['donor'].lower().endswith('.abc') else Skeleton(ROOT / job['donor'])
    clip = job.get('clip', 'Attack')
    fps = float(job.get('fps', 30))
    timing = job['timing']
    dclip = job['donor_clip']
    dtimes = D.model.clip_times(dclip)
    d0, d1 = float(timing.get('donor_start', dtimes[0])), float(timing.get('donor_end', dtimes[-1]))
    L, imp, dimp = float(timing['length']), float(timing['impact']), float(timing['donor_impact'])
    N = int(round(L * fps))
    times = np.arange(N + 1) / N * L
    dtime = np.interp(times, [0, imp, L], [d0, dimp, d1])
    report = {'donor': job['donor'], 'donor_clip': dclip, 'length': L, 'impact': imp,
              'donor_window': [d0, d1], 'donor_impact': dimp}

    mp = donor_map(D, job.get('map'))
    mirror = bool(job.get('mirror', False))
    gains = {'pelvis': 1.0, 'spine': 1.0, 'neck': 1.0, 'head': 1.0, 'arms': 1.0, 'legs': 1.0, 'travel': 1.0,
             'lift': 1.0}
    gains.update(job.get('gains', {}))
    gain_bone = job.get('gain_bone', {})

    # references
    t_local0, t_W0 = T.world('Standing', 0.0)
    ref = job.get('donor_ref', 'clip0')
    d_local0, d_W0 = D.world(dclip, d0) if ref == 'clip0' else D.world(ref, 0.0)
    feetT = [(f'B_{s}_Foot', f'B_{s}_Toe0') for s in SIDES]
    feetD = [(mp.get(f'B_{s}_Foot'), mp.get(f'B_{s}_Toe0')) for s in SIDES]
    has_legs = all(f'B_{s}_Thigh' in T.idx for s in SIDES)
    d_has_legs = mp.get('B_L_Thigh') and mp.get('B_R_Thigh')
    fT = fD = np.array([0.0, 0.0, 1.0])
    leftT = leftD = np.array([1.0, 0.0, 0.0])
    toesT = toesD = None
    if job.get('facing', 'axis') == 'hips':
        if has_legs:
            fT, leftT, toesT = facing(T, t_W0, feet=feetT)
        else:
            # legless body (Efreeti): facing from the clavicles
            fT, leftT, toesT = facing(T, t_W0, 'B_L_Clavicle', 'B_R_Clavicle')
        if d_has_legs:
            fD, leftD, toesD = facing(D, d_W0, mp['B_L_Thigh'], mp['B_R_Thigh'], feet=feetD)
        else:
            fD, leftD, toesD = facing(D, d_W0, mp['B_L_Clavicle'], mp['B_R_Clavicle'])
    # default "axis": MM9, LoMM and our B_* bodies all face +Z in their GLBs, so the model axes are aligned. The hips
    # are not the facing (the MM9 Nosferatu stands with its hips turned 30 deg, which aimed a strike 27 deg off)
    if job.get('target_forward'):
        fT = unit(np.asarray(job['target_forward'], float))
    if job.get('donor_forward'):
        fD = unit(np.asarray(job['donor_forward'], float))
    A = axis_angle(UP, yaw_of(fT) - yaw_of(fD))
    Mref = np.eye(3) - 2 * np.outer(leftD, leftD)
    report['facing'] = {'target_hips': fT.round(3).tolist(), 'target_toes': None if toesT is None else
                        toesT.round(3).tolist(), 'donor_hips': fD.round(3).tolist(),
                        'donor_toes': None if toesD is None else toesD.round(3).tolist(),
                        'turn_deg': round(math.degrees(yaw_of(fT) - yaw_of(fD)), 1)}
    if has_legs and d_has_legs:
        scale = leg_length(T, t_W0, lambda s_, l_: f'B_{s_}_{l_}') / leg_length(D, d_W0, lambda s_, l_: mp[f'B_{s_}_{l_}'])
    else:
        a = np.linalg.norm(T.pos(t_W0, 'B_Neck') - T.pos(t_W0, 'B_Pelvis'))
        b = np.linalg.norm(D.pos(d_W0, mp['B_Neck']) - D.pos(d_W0, mp['B_Pelvis']))
        scale = float(a / b)
    scale *= float(job.get('scale_mul', 1.0))
    report['travel_scale'] = round(scale, 4)

    # donor source bone per target bone (mirrored: the other side)
    def src(bone):
        if mirror:
            if '_L_' in bone:
                bone = bone.replace('_L_', '_R_')
            elif '_R_' in bone:
                bone = bone.replace('_R_', '_L_')
        return mp.get(bone)

    mapped = [b for b in T.idx if b in GROUP and src(b) and b in T.idx]
    report['map'] = {b: src(b) for b in mapped}
    keep_globs = job.get('keep', [])

    # blend weights
    bi, bo = float(job.get('blend_in', 0.06)), float(job.get('blend_out', 0.25))
    wts = np.array([min(smoothstep(t / bi) if bi > 0 else 1.0, smoothstep((L - t) / bo) if bo > 0 else 1.0)
                    for t in times])

    pel_name = 'B_Pelvis'
    tp0 = T.pos(t_W0, pel_name)
    dp0 = D.pos(d_W0, mp[pel_name])
    rotT0 = {b: rot_of(t_W0[T.idx[b]]) for b in T.idx if T.idx[b] is not None}
    scaleT0 = [np.linalg.norm(t_W0[i, :3, :3], axis=0) for i in range(len(T.nodes))]

    extra = job.get('extra', {}).get('pre', [])

    def extra_rot_one(e, t):
        R = np.eye(3)
        basis = np.stack([leftT, UP, fT], axis=1)       # body frame columns: x left, y up, z forward
        t0, t1, t2, t3 = e[2:6]
        w = smoothstep((t - t0) / max(t1 - t0, 1e-6)) if t < t1 else (
            1.0 if t <= t2 else 1.0 - smoothstep((t - t2) / max(t3 - t2, 1e-6)))
        deg = np.asarray(e[1], float) * w
        for k in range(3):
            if abs(deg[k]) > 1e-9:
                R = axis_angle(basis[:, k], math.radians(deg[k])) @ R
        return R

    def extra_rot(bone, t):
        R = np.eye(3)
        for e in extra:
            if e[0] == bone:
                R = extra_rot_one(e, t) @ R
        return R

    travel_node = job.get('travel_node')

    pass_globs = job.get('passthrough', [])
    pass_nodes = {i for i, n in enumerate(T.nodes) if any(fnmatch.fnmatch(n.get('name') or '', g) for g in pass_globs)}

    def assemble(rots, pel, dlocal=None):
        W = np.zeros((len(T.nodes), 4, 4))
        for i in T.order:
            name = T.nodes[i].get('name')
            trs = t_local0.get(i, T.model.rest[i])
            if dlocal is not None and i in pass_nodes:
                # (self-donor, same skeleton) the clip's own fingers, props and strings at the remapped time
                trs = dlocal.get(i, T.model.rest[i])
            M = glb_pose.trs_matrix(*trs)
            p = T.parent[i]
            Wp = W[p] if p >= 0 else np.eye(4)
            if travel_node and name == travel_node:
                # (Efreeti) the travel goes to a node above the pelvis that also carries the flame tail
                W[i] = t_W0[i].copy()
                W[i][:3, 3] += pel - tp0
                continue
            if name in rots and name == pel_name and travel_node:
                w_ = np.eye(4)
                w_[:3, :3] = rots[name] * scaleT0[i][None, :]
                w_[:3, 3] = (Wp @ np.append(trs[0], 1.0))[:3]
                W[i] = w_
                continue
            if name in rots:
                w_ = np.eye(4)
                w_[:3, :3] = rots[name] * scaleT0[i][None, :]
                w_[:3, 3] = pel if name == pel_name else (Wp @ np.append(trs[0], 1.0))[:3]
                W[i] = w_
            else:
                W[i] = Wp @ M
        return W

    worlds = []
    pass_locals = []       # passthrough nodes' own locals per sample (written as is: keeps visibility scale keys)
    foot_info = []
    last_tw = {}
    for k, (t, td) in enumerate(zip(times, dtime)):
        dlocal, dW = D.world(dclip, td)
        if not pass_nodes:
            dlocal = None
        rots = {}
        for b in mapped:
            db = src(b)
            delta = rot_of(dW[D.idx[db]]) @ rot_of(d_W0[D.idx[db]]).T
            if mirror:
                delta = Mref @ delta @ Mref
            delta = A @ delta @ A.T
            g = float(gain_bone.get(b, gains[GROUP[b]])) * wts[k]
            delta = rot_power(delta, g)
            rots[b] = extra_rot(b, t) @ delta @ rotT0[b]
        # extras flagged "chain" also turn every mapped descendant, as a rigid turn of the limb about its joint
        for e in extra:
            if len(e) > 6 and e[6] == 'chain' and e[0] in rots:
                R = extra_rot_one(e, t)
                for b in rots:
                    if b != e[0] and is_below(T, T.idx[b], T.idx[e[0]]):
                        rots[b] = R @ rots[b]
        ad = job.get('arm_direction')
        if ad:
            # chosen limb bones take the donor's world bone direction (not only its change), eased in and out over
            # `ramp`; roll stays from the change. For donors whose idle arms differ from ours (the Nosferatu holds
            # its claws forward, PeasantF3's arms hang: copied changes swung her raised arm out sideways)
            t0, t1, t2, t3 = ad['ramp']
            wd = smoothstep((t - t0) / max(t1 - t0, 1e-6)) if t < t1 else (
                1.0 if t <= t2 else 1.0 - smoothstep((t - t2) / max(t3 - t2, 1e-6)))
            wd *= float(ad.get('weight', 1.0))
            if wd > 1e-6:
                for b in ad['bones']:
                    child = {'UpperArm': 'Forearm', 'Forearm': 'Hand', 'Thigh': 'Calf', 'Calf': 'Foot'}[b.split('_')[-1]]
                    cb = b.rsplit('_', 1)[0] + '_' + child
                    db, dc = src(b), src(cb)
                    if not db or not dc or b not in rots:
                        continue
                    dd = dW[D.idx[dc], :3, 3] - dW[D.idx[db], :3, 3]
                    if mirror:
                        dd = Mref @ dd
                    dd = A @ dd
                    # our bone axis in its Standing frame, then where the current rotation puts it
                    u_loc = rotT0[b].T @ unit(t_W0[T.idx[cb], :3, 3] - t_W0[T.idx[b], :3, 3])
                    cur = rots[b] @ u_loc
                    rots[b] = rot_power(rot_between(cur, dd), wd) @ rots[b]
        ymax = job.get('trunk_yaw_max')
        if ymax:
            # playbook: trunk axial twist soft-limited (~45 deg); each trunk bone's yaw about the vertical is limited,
            # the arms turn with the chest's correction so they stay attached to it
            ymax = math.radians(float(ymax))
            corr = {}
            for b in ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head'):
                if b not in rots:
                    continue
                d = rots[b] @ rotT0[b].T
                f2 = d @ fT
                yaw = math.atan2(float(f2 @ leftT), float(f2 @ fT))
                new = ymax * math.tanh(yaw / ymax)
                corr[b] = axis_angle(UP, new - yaw)        # a turn about +Y by a > 0 moves fT toward leftT
                rots[b] = corr[b] @ rots[b]
            if 'B_Spine2' in corr:
                for b in rots:
                    if GROUP.get(b) == 'arms':
                        rots[b] = corr['B_Spine2'] @ rots[b]
        if job.get('spine_spread') and all(b in rots for b in ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2')):
            # the trunk's world turn spread evenly from the pelvis to the top spine joint (a donor bend concentrated
            # at one joint stretched the Ogre Mage's back 34 % at B_Spine1)
            d_p = rots['B_Pelvis'] @ rotT0['B_Pelvis'].T
            d_t = rots['B_Spine2'] @ rotT0['B_Spine2'].T
            step = d_t @ d_p.T
            for frac, b in ((1 / 3, 'B_Spine'), (2 / 3, 'B_Spine1')):
                rots[b] = rot_power(step, frac) @ d_p @ rotT0[b]
        move = dW[D.idx[mp[pel_name]], :3, 3] - dp0
        if mirror:
            move = Mref @ move
        move = A @ move * scale * wts[k]
        move[[0, 2]] *= gains['travel']
        move[1] *= gains['lift']
        for e in job.get('travel_extra', []):
            # authored pelvis travel [x left, y up, z forward] metres, eased in t0..t1, held, eased out t2..t3
            t0, t1, t2, t3 = e[1:5]
            w = smoothstep((t - t0) / max(t1 - t0, 1e-6)) if t < t1 else (
                1.0 if t <= t2 else 1.0 - smoothstep((t - t2) / max(t3 - t2, 1e-6)))
            move = move + (np.stack([leftT, UP, fT], axis=1) @ np.asarray(e[0], float)) * w
        pel = tp0 + move
        W = assemble(rots, pel, dlocal)
        # legs: two-bone IK to the donor's ankle travel
        feet_mode = job.get('feet', 'ik' if d_has_legs else 'planted')
        if has_legs and (feet_mode == 'planted' or (d_has_legs and feet_mode == 'ik')):
            info = {}
            for s in SIDES:
                th, ca, fo = (f'B_{s}_{l}' for l in ('Thigh', 'Calf', 'Foot'))
                ankle0 = T.pos(t_W0, fo)
                if feet_mode == 'ik':
                    dfo = src(fo)
                    fm = dW[D.idx[dfo], :3, 3] - d_W0[D.idx[dfo], :3, 3]
                    if mirror:
                        fm = Mref @ fm
                    fm = A @ fm * scale * wts[k]
                    fm[[0, 2]] *= gains['travel']
                    target = ankle0 + fm
                else:
                    target = ankle0
                for b in (th, ca, fo):
                    rots.setdefault(b, rot_of(W[T.idx[b]]))
                hip = W[T.idx[th], :3, 3]
                knee = W[T.idx[ca], :3, 3]
                ank = W[T.idx[fo], :3, 3]
                l1 = np.linalg.norm(knee - hip)
                l2 = np.linalg.norm(ank - knee)
                d = target - hip
                dl = float(np.clip(np.linalg.norm(d), abs(l1 - l2) + 1e-4, (l1 + l2) * 0.9995))
                dn = unit(d)
                pole = knee - hip
                pole = unit(pole - (pole @ dn) * dn)
                a = (l1 * l1 + dl * dl - l2 * l2) / (2 * dl)
                h = math.sqrt(max(l1 * l1 - a * a, 0.0))
                knee_new = hip + dn * a + pole * h
                R1 = rot_between(knee - hip, knee_new - hip)
                rots[th] = R1 @ rots[th]
                ank_after_thigh = hip + R1 @ (ank - hip)
                R2 = rot_between(ank_after_thigh - knee_new, hip + dn * dl - knee_new)
                rots[ca] = R2 @ R1 @ rots[ca]
                info[s] = round(float(np.linalg.norm(target - (hip + dn * dl))), 4)
            W = assemble(rots, pel, dlocal)
            foot_info.append(info)
        wl = job.get('wrist_limit', {'knee': 40.0, 'max': 58.0})
        if wl:
            changed = False
            for s in SIDES:
                fo, ha = f'B_{s}_Forearm', f'B_{s}_Hand'
                if fo not in rots or ha not in rots:
                    continue
                Rf = rot_of(W[T.idx[fo]])
                rel0 = rotT0[fo].T @ rotT0[ha]
                rel = Rf.T @ rots[ha]
                d = rel @ rel0.T
                axis = unit(rotT0[fo].T @ (t_W0[T.idx[ha], :3, 3] - t_W0[T.idx[fo], :3, 3]))
                tw = twist_about(glb_pose.matrix_quaternion(d), axis)
                swing = d @ axis_angle(axis, -tw)
                if s in last_tw:                             # unwrap over time: a roll through 180 deg stays smooth
                    tw = last_tw[s] + (tw - last_tw[s] + math.pi) % (2 * math.pi) - math.pi
                last_tw[s] = tw
                q = glb_pose.matrix_quaternion(swing)
                ang = math.degrees(2 * math.atan2(float(np.linalg.norm(q[:3])), abs(float(q[3]))))
                knee, top = float(wl['knee']), float(wl['max'])
                tmax = math.radians(float(wl.get('twist_max', 75.0)))
                new_tw = tmax * math.tanh(tw / tmax)
                if ang > knee or abs(new_tw - tw) > 1e-4:
                    if ang > knee:
                        new = knee + (top - knee) * math.tanh((ang - knee) / (top - knee))
                        swing = rot_power(swing, new / ang)
                    rots[ha] = Rf @ swing @ axis_angle(axis, new_tw) @ rel0
                    changed = True
                    rep = report.setdefault('wrist_limited_deg', {}).setdefault(s, [0.0, 0.0])
                    rep[0] = round(max(rep[0], ang), 1)
                    rep[1] = round(max(rep[1], abs(math.degrees(tw))), 1)
            if changed:
                W = assemble(rots, W[T.idx[pel_name], :3, 3], dlocal)
        worlds.append(W)
        pass_locals.append({i: dlocal.get(i, T.model.rest[i]) for i in pass_nodes} if dlocal is not None else {})
    worlds = np.array(worlds)
    if foot_info:
        report['ik_miss_m'] = {s: max(f[s] for f in foot_info) for s in SIDES}

    # floor: lift where a foot/toe-dominated vertex is under the floor
    if has_legs and job.get('floor', 'lift') == 'lift':
        joints = np.asarray(T.model.joints)
        foot_nodes = {T.idx[n] for n in T.idx if n and any(fnmatch.fnmatch(n, g) for g in
                                                           ('B_*_Foot', 'B_*_Toe0', 'B_*_Calf'))}
        sel = []
        for prim, (p0, _) in zip(T.model.primitives, T.model.skinned_positions(t_W0)):
            if prim['skinned']:
                dom = joints[prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
                # leg-weighted vertices near the floor at Standing (soles, and a hem weighted to the calves)
                sel.append(np.isin(dom, list(foot_nodes)) & (p0[:, 1] < 0.15))
            else:
                sel.append(np.zeros(len(prim['positions']), bool))
        if not any(s_.any() for s_ in sel):
            sel = None
            report['floor'] = 'no leg vertices near the floor (legs stripped under a robe): skipped'
    if has_legs and job.get('floor', 'lift') == 'lift' and sel is not None:
        ref_low = min(float(p[s_, 1].min()) for (p, _), s_ in zip(T.model.skinned_positions(t_W0), sel) if s_.any())
        lows = []
        for W in worlds:
            lows.append(min(float(p[s_, 1].min()) for (p, _), s_ in zip(T.model.skinned_positions(W), sel)
                            if s_.any()))
        lows = np.array(lows)
        sink = np.maximum(min(ref_low, 0.0) - lows, 0.0)
        if sink.max() > 0:
            from scipy.ndimage import gaussian_filter1d, maximum_filter1d
            shift = np.maximum(gaussian_filter1d(maximum_filter1d(sink, 5, mode='nearest'), 1.5, mode='nearest'),
                               sink)
            # the clip still starts and ends on Standing exactly (the smoothing spread a lift into frame 0)
            ends = np.array([min(smoothstep(t / 0.1), smoothstep((L - t) / 0.1)) for t in times])
            shift = np.where(sink > 0, shift, shift * ends)
            below = [i for i in range(len(T.nodes)) if is_below(T, i, T.idx[pel_name])]
            worlds[:, below, 1, 3] += shift[:, None]
            report['floor_lift_m'] = round(float(shift.max()), 4)
        report['foot_low_m'] = [round(float(lows.min() - ref_low), 4), round(float(lows.max() - ref_low), 4)]

    # twist bones
    if job.get('twist', True):
        bind = T.model.world({i: T.model.rest[i] for i in range(len(T.nodes))})
        for s in SIDES:
            for base, child, name, share, own in (('Forearm', 'Hand', 'ForearmTwist', 0.6, False),
                                                  ('UpperArm', 'Forearm', 'UpperArmTwist', -0.5, True)):
                bn, cn, tn = f'B_{s}_{base}', f'B_{s}_{child}', f'B_{s}_{name}'
                if tn not in T.idx:
                    continue
                share = float(job.get('twist_share', {}).get(name, share))
                ib, ic, it = T.idx[bn], T.idx[cn], T.idx[tn]
                ip = T.parent[ib]
                tw_local = glb_pose.trs_matrix(*T.model.rest[it])
                for W in worlds:
                    Rb = rot_of(W[ib])
                    seg = unit(W[ic, :3, 3] - W[ib, :3, 3])
                    seg_local = Rb.T @ seg
                    if own:
                        # the upper arm's own rotation relative to its rest local (pose basis), about its segment
                        rel = rot_of(W[ip]).T @ Rb
                        rest_rel = rot_of(bind[ip]).T @ rot_of(bind[ib])
                        dq = glb_pose.matrix_quaternion(rest_rel.T @ rel)
                    else:
                        rel = Rb.T @ rot_of(W[ic])
                        rest_rel = rot_of(bind[ib]).T @ rot_of(bind[ic])
                        dq = glb_pose.matrix_quaternion(rel @ rest_rel.T)
                    ang = share * twist_about(dq, seg_local)
                    base_w = W[ib] @ tw_local
                    R = axis_angle(seg, ang)
                    W[it, :3, :3] = R @ base_w[:3, :3]
                    W[it, :3, 3] = base_w[:3, 3]

    # (mfp) a ring-skirt cage fitted to the posed legs, with the h05 / anim-fix ring_skirt.py imported unchanged
    if job.get('ring_skirt'):
        rs = job['ring_skirt']
        sys.path.insert(0, str(ROOT / rs['scripts']))
        import ring_skirt  # noqa: E402
        P = types.SimpleNamespace(glb=T.glb, model=T.model, nodes=T.nodes, idx=T.idx, parent=T.parent, order=T.order)
        sim = ring_skirt.RingSkirt(P, rs['cfg'])
        before = worlds.copy()
        worlds = np.array(sim.pose(worlds))
        # eased in and out: the fit differs from the accepted Standing cage by about a centimetre, so the clip
        # starts and ends on Standing's cage (carried by the pelvis) instead of popping at the crossfade
        ein, eout = float(rs.get('ease_in', 0.15)), float(rs.get('ease_out', 0.25))
        cage = sorted(sim.nodes())
        for k, t in enumerate(times):
            w = min(smoothstep(t / ein), smoothstep((L - t) / eout))
            if w >= 1.0:
                continue
            for n in cage:
                Wc = before[k][T.parent[n]] @ glb_pose.trs_matrix(*t_local0.get(n, T.model.rest[n]))
                qa = glb_pose.matrix_quaternion(rot_of(Wc))
                qb = glb_pose.matrix_quaternion(rot_of(worlds[k][n]))
                M = np.eye(4)
                M[:3, :3] = glb_pose.quaternion_matrix(glb_pose.slerp(qa, qb, w)) * np.linalg.norm(Wc[:3, :3], axis=0)
                M[:3, 3] = Wc[:3, 3] * (1 - w) + worlds[k][n, :3, 3] * w
                worlds[k][n] = M
        report['ring_skirt'] = rs['scripts']

    # cloth chains: periodic sim on the clip padded with Standing
    if job.get('cloth') and not args.no_cloth:
        sys.path.insert(0, str(H11))
        import cloth_sim  # noqa: E402
        P = types.SimpleNamespace(glb=T.glb, model=T.model, nodes=T.nodes, idx=T.idx, parent=T.parent, order=T.order)
        pad = int(round(float(job.get('cloth_pad', 0.7)) * fps))
        loop = np.concatenate([np.repeat(t_W0[None], pad, 0), worlds[:-1], np.repeat(t_W0[None], pad, 0)])
        TL = len(loop) / fps
        caps_all = list(cloth_sim.CAPS)
        # bodies without legs (Efreeti): only the capsules whose joints exist
        cloth_sim.CAPS = [c for c in caps_all if c[0] in T.idx and c[1].split(':')[0] in T.idx]
        for cfg in job['cloth']:
            cfg = dict(cfg)
            cfg['chains'] = str(ROOT / cfg['chains'])
            cloth = cloth_sim.Cloth(P, cfg)
            if cfg.get('rest_from', 'Standing') == 'Standing':
                standing_rest(cloth, T, t_W0)
            X = cloth.simulate(loop, TL)
            if cfg.get('rest_from', 'Standing') == 'Standing':
                # keep only the dynamic part: the sim's standing equilibrium (the padding) is not the accepted
                # Standing shape (bend limit, chain floor, inflated leg capsules); subtract its offset, turned with
                # the root's yaw, so a still body gives exactly Standing
                settle = max(1, pad // 2)
                r0 = X[:settle].mean(axis=0) - np.array(cloth.REST)
                for i in range(len(X)):
                    Ry = cloth.yaw(loop[i][T.idx[cloth.root]])
                    X[i] = X[i] - r0 @ Ry.T
                report.setdefault('cloth_rest_offset_cm', []).append(
                    (np.linalg.norm(r0, axis=2).max(axis=1) * 100).round(1).tolist())
            loop = key_from_standing(cloth, T, t_local0, loop, X) if cfg.get('rest_from', 'Standing') == 'Standing' \
                else cloth.key(loop, X)
            if cfg.get('hem_floor') is not None:
                rep = {}
                loop = cloth_sim.hem_floor(P, loop, cloth, float(cfg['hem_floor']), rep)
                report.setdefault('hem_floor', []).append(rep.get('hem_floor'))
            names = [b for bones in cloth.bones for b in bones]
            ids = [T.idx[n] for n in names]
            worlds[:-1, ids] = loop[pad:pad + N, ids]
            worlds[-1, ids] = loop[pad + N, ids]
        report['cloth'] = [c['chains'] for c in job['cloth']]

    # write
    glb = T.glb
    anims = glb.json.setdefault('animations', [])
    slot = None
    if any(a.get('name') == clip for a in anims):
        if not job.get('replace'):
            raise SystemExit(f'{clip} exists; set replace')
        slot = [a.get('name') for a in anims].index(clip)     # replaced in place: clip order stays (glb_diff)
    base = glb.json['animations'][[a.get('name') for a in anims].index('Standing')]
    nodes = sorted({c['target']['node'] for c in base['channels']})
    t_acc = glb.append_accessor(times.reshape(-1, 1), 'SCALAR')
    channels, samplers = [], []
    for node in nodes:
        name = T.nodes[node].get('name')
        p = T.parent[node]
        keep = any(fnmatch.fnmatch(name or '', g) for g in keep_globs)
        tr, ro, sc = [], [], []
        for k, W in enumerate(worlds):
            base_trs = t_local0.get(node, T.model.rest[node])
            if keep:
                tr.append(base_trs[0]), ro.append(base_trs[1]), sc.append(base_trs[2])
                continue
            if node in pass_locals[k]:
                # the donor clip's own locals, scale included (2026-11-11: a hidden bolt's zero scale was dropped)
                own = pass_locals[k][node]
                tr.append(own[0]), ro.append(own[1]), sc.append(own[2])
                continue
            local = np.linalg.inv(W[p]) @ W[node] if p >= 0 else W[node]
            tr.append(local[:3, 3])
            ro.append(glb_pose.matrix_quaternion(rot_of(local)))
            sc.append(np.asarray(base_trs[2]))
        q = np.array(ro, float)
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        for i in range(1, len(q)):
            if np.dot(q[i], q[i - 1]) < 0:
                q[i] = -q[i]
        for path, values, kind in (('translation', np.array(tr), 'VEC3'), ('rotation', q, 'VEC4'),
                                   ('scale', np.array(sc), 'VEC3')):
            out = glb.append_accessor(values, kind)
            samplers.append({'input': t_acc, 'output': out, 'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': int(node), 'path': path}})
    if slot is None:
        anims.append({'name': clip, 'channels': channels, 'samplers': samplers})
    else:
        anims[slot] = {'name': clip, 'channels': channels, 'samplers': samplers}
    out = ROOT / (args.out or job['out'])
    out.parent.mkdir(parents=True, exist_ok=True)
    glb.write(out)
    report['out'] = str(out.relative_to(ROOT))
    report['keys'] = N + 1
    print(json.dumps(report, indent=1))
    rep_path = Path(args.report) if args.report else Path(args.job).with_suffix('.report.json')
    rep_path.write_text(json.dumps(report, indent=1))


def standing_rest(cloth, T, W0):
    """The chains hang toward their Standing frame 0 shape (the sim's own rest bell is the chain JSON's, which is not
    how the accepted Standing poses the robe: 15 % of the gown read stretched at t = 0 against 3 % in Standing)."""
    import cloth_sim
    bind = T.model.world({i: T.model.rest[i] for i in range(len(T.nodes))})
    rest = []
    for c, chain in enumerate(cloth.CH):
        bones = chain['bones']
        J = [W0[T.idx[b], :3, 3] for b in bones]
        last = T.idx[bones[-1]]
        tail_bind = cloth_sim.to_gltf(chain['pts'][len(bones)])
        tail_local = np.linalg.inv(bind[last]) @ np.append(tail_bind, 1.0)
        J.append((W0[last] @ tail_local)[:3])
        F = []
        for k in range(len(bones)):
            F += [J[k], (J[k] + J[k + 1]) / 2]
        F.append(J[len(bones)])
        rest.append(np.array(F))
    cloth.REST = rest
    cloth.SEG = [np.linalg.norm(np.diff(r, axis=0), axis=1) for r in rest]
    cloth.nbrest = {(a, b): np.linalg.norm(rest[a][1:] - rest[b][1:], axis=1) for a, b in cloth.nb}
    cloth.rest_root = W0[T.idx[cloth.root]].copy()
    cloth.rest_world = W0
    # capsule radii from the Standing shape (the sim sizes them on the bind pose with a 9 cm leg floor, which put the
    # Standing hem by the feet inside the foot capsules and shot those chains up to 50 cm out)
    allrest = np.vstack([r[1:] for r in rest] + [(rest[a][1:] + rest[b][1:]) / 2 for a, b in cloth.nb])
    radii = []
    for (a, b, r) in cloth.caps:
        pa, pb = cloth.joint(W0, a), cloth.joint(W0, b)
        d = np.linalg.norm(cloth_sim.seg_dist(allrest, pa, pb), axis=1).min()
        radii.append(float(np.clip(d - cloth.margin - 0.004, 0.0, r)))
    cloth.radii = radii


def key_from_standing(cloth, T, local0, worlds, X):
    """Chain bones aimed at the simulated joints: each bone's Standing local under its posed parent, turned by the
    least rotation that takes its Standing direction onto the simulated next joint. At the Standing shape this is
    exactly Standing (the sim's own key() starts from the bind orientation and rolled the hem bones 60-100 deg)."""
    for c, bones in enumerate(cloth.bones):
        for i in range(len(worlds)):
            W = worlds[i]
            for k, b in enumerate(bones):
                n = T.idx[b]
                parent = T.parent[n]
                Mu = W[parent] @ glb_pose.trs_matrix(*local0.get(n, T.model.rest[n]))
                rest_next = cloth.REST[c][2 * k + 2]
                rest_head = cloth.REST[c][2 * k]
                # the Standing direction in the bone's Standing frame: REST is the Standing shape in world
                W0b = cloth.rest_world[n]
                d_loc = rot_of(W0b).T @ unit(rest_next - rest_head)
                d_cur = rot_of(Mu) @ d_loc
                R = rot_between(d_cur, X[i, c, 2 * k + 2] - Mu[:3, 3])
                M = Mu.copy()
                M[:3, :3] = R @ Mu[:3, :3]
                W[n] = M
    return worlds


def is_below(T, node, ancestor):
    n = node
    while n >= 0:
        if n == ancestor:
            return True
        n = T.parent[n]
    return False


if __name__ == '__main__':
    main()
