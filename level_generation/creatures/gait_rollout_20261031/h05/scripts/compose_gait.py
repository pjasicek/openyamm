#!/usr/bin/env python3
"""Author new in-place locomotion clips (a jog, a sprint) on an installed MM6 humanoid GLB and append them.

Package h05 copy of h04's composer (2026-10-31), with h01's `even_bob` and h16's `symmetric_drop` (an even pelvis
drop on both steps), h01's `swing_height` (the same as `swing_lift`), h19's `track_out` (a wider track), and
`thigh_swing` (the MM6 PeasantF4's swing-only thigh helpers, which carry her skirt, recomputed from the new thighs).
h04's header: Package h04 copy of h02's composer (2026-10-31): `raise_arms` returns after `elbow_forward_deg`, and the arm
clearance keeps that forearm bend (it may run with it; `arms_raise_deg` still needs the clearance off). h02's header:
Copied from mm6_sprint_humanoids_claude/scripts/compose_gait.py for the gait rollout package h02 (2026-10-31), with
three additions: `swing_lift` scales the ankle's height above its flat height (the swing foot's clearance; a short
body's scaled library walk shuffles) and `arms_raise_deg` turns both arms forward and up as one rigid unit about the
shoulder line (a two-handed weapon carry kept exactly; the Minotaur's knees drive into its axe haft in the sprint);
and `elbow_forward_deg` bends a forearm toward the travel direction (the Jackalman's running arm from its walk).
The pilot's header follows.

Adapted from mm8_pirates_gait_claude/scripts/compose_gait.py (2026-10-31) with four additions for runs and sprints:
`align` (the clip's left foot is forward-most at the same loop phase as a reference clip's, since the engine shares
one gait phase across walk, run and sprint), `arm_gain` (the base clip's arm swing scaled about its loop mean, per
side, for a stronger arm drive), `lean_deg` (an extra forward pitch per trunk bone, in world space) and `side_gain`
per arm side (a held weapon's arm can keep its accepted swing).

    compose_gait.py <in.glb> <out.glb> <job.json> [<job.json> ...]

Each job (JSON) names a library loop (npz from extract_source.py), the clip to write, its length and stride, and the
pirate's own clip that supplies the upper body (`base`). Why this split: the legs, pelvis and trunk rhythm of a
jog or a slow walk come from the library mocap, while the arms, hands, fingers, twist bones and props (cutlass and
hook, crossbow carry with strings and quiver, cobra staff) keep the pirate's own fitted locomotion clip, phase-aligned
on the left foot's forward-most point, so every grip, prop clearance and finger solve stays the accepted one.

- Treadmill frame: the source loop is resampled (periodic cubic, seam drift and root travel removed) and turned to
  face +Z, the pirates' forward. Positions scale by the leg-length ratio k; the forward axis additionally by c so the
  planted foot slides back at stride / length (one loop per stride: no slide in game).
- Pelvis: the source's hip-joint midpoint path (sway, surge, bob) scaled by k; its mean height chosen so the stance
  legs keep the source's extension (hip-ankle distance over leg length), lowered smoothly wherever a leg would
  overreach. Pelvis, spine, neck and head rotations: the source's world rotation change about its loop mean, applied
  to our mean posture (the base clip's mean, or blended toward Standing with `lean`); `weights` scale them.
- Legs: ankle targets from the source ankle paths (lateral about our hip width; height above each foot's flat height),
  analytic two-bone IK with the knee in the source's leg plane and the hinge axis measured on the base clip, foot
  rotation = the source foot's change about its stance mean applied to the base clip's stance foot; toes as Standing.
- Floor: posed LOD0 soles (vertices below 6 cm in Standing, each side) put on the floor in the source's stance
  (one constant per side) and lifted wherever they would go under it (smoothed), then IK again.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gaitlib  # noqa: E402
from gaitlib import ROOT, glb_pose, unit  # noqa: E402

SIDES = (('L', 'Left', 1.0), ('R', 'Right', -1.0))
CHAIN = (('B_Pelvis', 'Hips'), ('B_Spine', 'Spine'), ('B_Spine1', 'Spine1'), ('B_Spine2', 'Spine2'),
         ('B_Neck', 'Neck'), ('B_Head', 'Head'))
LEG_BONES = [f'B_{s}_{b}' for s, _, _ in SIDES for b in ('Thigh', 'Calf', 'Foot', 'Toe0')]


def qmean(mats):
    q = gaitlib.quat_from_matrices(mats)
    q = q * np.sign(q @ q[0])[:, None]
    m = q.mean(axis=0)
    return glb_pose.quaternion_matrix(m / np.linalg.norm(m))


def rot_power(r, w):
    """Rotation matrix to the power w (axis-angle scaling)."""
    q = glb_pose.matrix_quaternion(r)
    if q[3] < 0:
        q = -q
    angle = 2 * np.arctan2(np.linalg.norm(q[:3]), q[3])
    if angle < 1e-9:
        return np.eye(3)
    axis = q[:3] / np.linalg.norm(q[:3])
    a = angle * w
    return glb_pose.quaternion_matrix(np.append(axis * np.sin(a / 2), np.cos(a / 2)))


def frame_from(axis_y, hinge):
    """Orthonormal 3x3 with columns (x, y, z): y = bone axis, x = hinge made orthogonal to it."""
    y = unit(axis_y)
    x = unit(hinge - y * np.dot(hinge, y))
    z = np.cross(x, y)
    return np.stack([x, y, z], axis=1)


def periodic_smooth(values, sigma):
    return gaussian_filter1d(values, sigma, axis=0, mode='wrap') if sigma > 0 else values


class Body:
    def __init__(self, path):
        self.glb = glb_pose.Glb(path)
        self.model = glb_pose.Model(self.glb)
        self.nodes = self.glb.json['nodes']
        self.idx = {n['name']: i for i, n in enumerate(self.nodes)}
        self.parent = self.model.parent
        self.order = self.model.order

    def clip_world(self, clip, times):
        locals_, worlds = [], []
        for t in times:
            local = self.model.sample(clip, float(t))
            locals_.append(local)
            worlds.append(self.model.world(local))
        return locals_, np.array(worlds)

    def clip_length(self, clip):
        return self.model.clip_times(clip)[-1]

    def channel_nodes(self, clip):
        animation = self.glb.json['animations'][self.model.clips[clip]]
        return sorted({c['target']['node'] for c in animation['channels']})


def solve(body, job):
    P = body
    P.toe_bend = {}
    I = P.idx
    P.thigh_swing = {}
    if job.get('thigh_swing'):
        # swing-only thigh helpers (natf: B_<s>_ThighSwing, a pelvis child at the thigh's rest): rest x swing part of
        # the thigh's rotation from its rest (twist about the bone's Y removed), as her project's skirt_skin.py bakes
        P.thigh_swing = {I[f'B_{s}_ThighSwing']: I[f'B_{s}_Thigh'] for s, _, _ in SIDES}
        P.extra_authored = getattr(P, 'extra_authored', set()) | set(P.thigh_swing)
    rate = job.get('rate', 120)
    T = float(job['duration'])
    N = int(round(T * rate))
    phases = np.arange(N) / N
    src = gaitlib.Cycle(job['source'], N, job.get('source_period_frames'))
    base = job['base']
    Tb = P.clip_length(base)
    report = {'clip': job['clip'], 'source': str(src.path.name), 'source_period_s': src.period,
              'source_yaw_deg': src.yaw_degrees, 'duration': T, 'stride': job['stride'], 'base': base}

    # --- our references
    _, W_std = P.clip_world('Standing', [0.0])
    W_std = W_std[0]
    base_times = np.arange(240) / 240 * Tb
    _, W_base = P.clip_world(base, base_times)
    l1 = {s: float(np.linalg.norm(P.model.rest[I[f'B_{s}_Calf']][0])) for s, _, _ in SIDES}
    l2 = {s: float(np.linalg.norm(P.model.rest[I[f'B_{s}_Foot']][0])) for s, _, _ in SIDES}
    L_our = l1['L'] + l2['L']
    k = L_our / src.leg_length
    S = float(job['stride'])
    hip_mid_src = 0.5 * (src.pos['LeftUpLeg'] + src.pos['RightUpLeg'])
    # source ground speed: median backward speed of the low ankle (in place: the treadmill speed)
    dt_src = src.period / N
    speeds = []
    for _, side, _ in SIDES:
        a = src.pos[f'{side}Foot']                    # treadmill frame: the ground slides back under the loop
        h = src.pos[f'{side}Foot'][:, 1]
        low = h <= h.min() + 0.12 * np.ptp(h)
        v = -(np.roll(a[:, 2], -1) - a[:, 2]) / dt_src
        speeds.extend(v[low & np.roll(low, -1)])
    v_src = float(np.median(speeds))
    S_src = v_src * src.period
    c = S / (k * S_src)
    report.update({'k': k, 'source_stride_scaled': k * S_src, 'forward_scale': c})

    # phase alignment: left ankle forward-most relative to the hips
    psi_L = phases[np.argmax(src.pos['LeftFoot'][:, 2] - src.pos['Hips'][:, 2])]
    base_rel = W_base[:, I['B_L_Foot'], 2, 3] - W_base[:, I['B_Pelvis'], 2, 3]
    phi_L = np.argmax(base_rel) / len(base_times)
    base_phase = (phases - psi_L + phi_L) % 1.0
    report['phase'] = {'source_left_front': float(psi_L), 'base_left_front': float(phi_L)}
    base_local, W_bp = P.clip_world(base, base_phase * Tb)
    gain_arms(P, base_local, job, report)
    if job.get('skirt_gain'):
        gain_skirt(P, base_local, job, report)

    # --- trunk rotations: source change about its loop mean, on our mean posture
    lean = float(job.get('lean', 1.0))
    weights = job.get('weights', {})
    world_rot = {}
    for ours, theirs in CHAIN:
        mean_base = qmean(W_base[:, I[ours], :3, :3])
        R_std = W_std[I[ours], :3, :3]
        mean_ours = glb_pose.quaternion_matrix(glb_pose.slerp(glb_pose.matrix_quaternion(R_std),
                                                              glb_pose.matrix_quaternion(mean_base), lean))
        R_src = src.rot[theirs]
        mean_src = qmean(R_src)
        w = float(weights.get(ours, 1.0))
        tilt = pitch(float(job.get('lean_deg', {}).get(ours, 0.0)))
        world_rot[ours] = np.array([tilt @ rot_power(R_src[i] @ mean_src.T, w) @ mean_ours for i in range(N)])

    # --- pelvis position: hip midpoint path
    thigh_T = {s: P.model.rest[I[f'B_{s}_Thigh']][0] for s, _, _ in SIDES}
    mid_local = 0.5 * (thigh_T['L'] + thigh_T['R'])
    base_hipmid = 0.5 * (W_base[:, I['B_L_Thigh'], :3, 3] + W_base[:, I['B_R_Thigh'], :3, 3])
    origin = base_hipmid.mean(axis=0)
    src_mid_mean = hip_mid_src.mean(axis=0)
    rel = hip_mid_src - src_mid_mean
    mid = np.zeros((N, 3))
    mid[:, 0] = origin[0] + k * rel[:, 0] * job.get('sway', 1.0)
    mid[:, 2] = origin[2] + k * c * rel[:, 2]
    bob = k * rel[:, 1] * job.get('bob', 1.0)
    if job.get('even_bob', False):
        # (h01) the source's hip bob made alike on both steps: the mean of the signal and itself half a loop later
        bob = 0.5 * (bob + np.roll(bob, N // 2))

    # --- ankle targets (height above the floor added later as the flat height)
    std_ankle = {s: W_std[I[f'B_{s}_Foot'], :3, 3] for s, _, _ in SIDES}
    w_our = 0.5 * abs(W_std[I['B_L_Thigh'], 0, 3] - W_std[I['B_R_Thigh'], 0, 3])
    w_src = 0.5 * float(np.mean(np.abs(src.pos['LeftUpLeg'][:, 0] - src.pos['RightUpLeg'][:, 0])))
    target = {}
    flat_src = {}
    for s, side, sign in SIDES:
        a = src.pos[f'{side}Foot']
        flat_src[s] = a[:, 1].min()
        t = np.zeros((N, 3))
        t[:, 0] = origin[0] + sign * w_our + k * (a[:, 0] - src_mid_mean[0] - sign * w_src) * job.get('width', 1.0)
        t[:, 0] += sign * float(job.get('track_out', 0.0))          # (h19) a wider track
        t[:, 2] = origin[2] + k * c * float(job.get('side_scale', {}).get(s, 1.0)) * (a[:, 2] - src_mid_mean[2])
        t[:, 1] = std_ankle[s][1] + k * (a[:, 1] - flat_src[s]) * float(job.get('swing_lift', job.get('swing_height', 1.0)))
        target[s] = t
    contact = {s: src.contact(side) for s, side, _ in SIDES}

    # --- knee poles from the source leg plane
    pole = {}
    for s, side, _ in SIDES:
        hp, kn, an = src.pos[f'{side}UpLeg'], src.pos[f'{side}Leg'], src.pos[f'{side}Foot']
        u = unit(an - hp)
        w = (kn - hp) - u * np.sum((kn - hp) * u, axis=1, keepdims=True)
        w = w + 0.02 * np.array([0, 0, 1.0])            # straight leg: knee forward
        pole[s] = periodic_smooth(unit(w), 1.0)

    # --- hinge axes in the thigh and calf local frames, measured on the base clip's bent frames
    hinge = {}
    for s, _, _ in SIDES:
        H, K, A = (W_base[:, I[f'B_{s}_{b}'], :3, 3] for b in ('Thigh', 'Calf', 'Foot'))
        u = unit(A - H)
        w = (K - H) - u * np.sum((K - H) * u, axis=1, keepdims=True)
        bend = np.degrees(np.arccos(np.clip(np.sum(unit(K - H) * unit(A - K), axis=1), -1, 1)))
        use = bend > 15
        n = unit(np.cross(unit(w[use]), u[use]))
        ht = np.einsum('kba,kb->ka', W_base[use, I[f'B_{s}_Thigh'], :3, :3], n).mean(axis=0)
        hc = np.einsum('kba,kb->ka', W_base[use, I[f'B_{s}_Calf'], :3, :3], n).mean(axis=0)
        hinge[s] = (unit(ht), unit(hc))
        report.setdefault('hinge_local', {})[s] = [np.round(unit(ht), 3).tolist(), np.round(unit(hc), 3).tolist()]

    # --- foot rotations: source change about its stance mean, on the base clip's stance foot
    foot_rot, flat_feet = {}, {}
    for s, side, sign in SIDES:
        Rb = W_base[:, I[f'B_{s}_Foot'], :3, :3]
        hb = W_base[:, I[f'B_{s}_Foot'], 1, 3]
        stance_b = hb <= hb.min() + 0.01
        # the planted foot's rotation: the base clip's stance foot, or Standing's (flat on the floor) turned about the
        # vertical to point along travel: Standing's idle toe-out (27 deg on both MM6 models) read as duck feet in a run
        if job.get('stance_foot') == 'Standing':
            flat_ours = W_std[I[f'B_{s}_Foot'], :3, :3]
            if 'foot_toe_out_deg' in job:
                # heading of the foot's pitch axis (up x foot->toe on the ground), so a pitched foot reads right;
                # forward is +Z, the travel direction (Standing's own feet are yawed 4 deg off it; the accepted
                # Walking plants along +Z)
                d = W_std[I[f'B_{s}_Toe0'], :3, 3] - W_std[I[f'B_{s}_Foot'], :3, 3]
                yaw = np.arctan2(d[0], d[2])
                want = sign * np.radians(float(job['foot_toe_out_deg']))     # left is +X: toe-out is +yaw
                a = want - yaw
                Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
                flat_ours = Ry @ flat_ours
                report.setdefault('foot_yaw_turn_deg', {})[s] = float(np.degrees(a))
        else:
            flat_ours = qmean(Rb[stance_b])
        flat_feet[s] = flat_ours
        Rs = src.rot[f'{side}Foot']
        flat_theirs = qmean(Rs[contact[s]])
        wf = float(job.get('foot_weight', 1.0))
        foot_rot[s] = np.array([rot_power(Rs[i] @ flat_theirs.T, wf) @ flat_ours for i in range(N)])
    toe_local = {s: P.model.sample('Standing', 0.0)[I[f'B_{s}_Toe0']][1] for s, _, _ in SIDES}
    for s in job.get('rigid_foot', []):
        # a peg: the (virtual) foot keeps Standing's rotation relative to the calf
        local = glb_pose.quaternion_matrix(P.model.sample('Standing', 0.0)[I[f'B_{s}_Foot']][1])
        foot_rot[s] = ('calf', local)

    if job.get('lock_stance', False):
        lock_stance(job, target, foot_rot, flat_feet, contact, std_ankle, S / T, T / N, report)
    if job.get('foot_smooth', 0) > 0:
        # a gentler foot roll than the source's (the humanoid set's sprint snaps its feet): periodic quaternion blur
        for s in foot_rot:
            if isinstance(foot_rot[s], tuple):
                continue
            q = gaitlib.quat_from_matrices(foot_rot[s])
            foot_rot[s] = gaitlib.matrices_from_quat(periodic_smooth(q, float(job['foot_smooth'])))

    # --- mean pelvis height: match the source's stance-leg extension
    ext_src = {}
    for s, side, _ in SIDES:
        d = np.linalg.norm(src.pos[f'{side}Foot'] - src.pos[f'{side}UpLeg'], axis=1) / src.leg_length
        ext_src[s] = d
    R_pel = world_rot['B_Pelvis']

    def hips_at(height_offsets):
        """World hip joints and pelvis translation for a per-sample hip-midpoint height."""
        m = mid.copy()
        m[:, 1] = height_offsets
        pel = m - np.einsum('kab,b->ka', R_pel, mid_local)
        hips = {s: pel + np.einsum('kab,b->ka', R_pel, thigh_T[s]) for s, _, _ in SIDES}
        return pel, hips

    def extension(height):
        """High stance extension (90th percentile over both stance legs) for a mean hip height."""
        _, hips = hips_at(height + bob)
        ext = []
        for s, _, _ in SIDES:
            d = np.linalg.norm(target[s] - hips[s], axis=1) / (l1[s] + l2[s])
            ext.append(d[contact[s]])
        return float(np.percentile(np.concatenate(ext), 90))

    std_mid = 0.5 * (W_std[I['B_L_Thigh'], 1, 3] + W_std[I['B_R_Thigh'], 1, 3])
    grid = np.linspace(0.75 * std_mid, 1.05 * std_mid, 301)
    want = float(job.get('stance_extension', 0.97))
    H0 = float(grid[np.argmin([abs(extension(h) - want) for h in grid])]) + float(job.get('height_offset', 0.0))
    report['hip_height'] = {'standing': std_mid, 'chosen': H0}

    reach = float(job.get('reach', 0.985))
    soles = sole_sets(P, W_std)
    lift = {s: np.zeros(N) for s, _, _ in SIDES}
    drop = np.zeros(N)
    for iteration in range(4):
        height = H0 + bob - drop
        pel, hips = hips_at(height)
        # reach: lower the pelvis where a leg would overreach
        need = np.zeros(N)
        for s, _, _ in SIDES:
            A = target[s] + np.outer(lift[s], [0, 1, 0])
            d = A - hips[s]
            L = reach * (l1[s] + l2[s])
            horiz = np.sum(d[:, [0, 2]] ** 2, axis=1)
            vert_max = np.sqrt(np.maximum(L * L - horiz, 0))
            need = np.maximum(need, -d[:, 1] - vert_max)          # d.y is negative (ankle below hip)
        need = np.maximum(need, 0)
        if job.get('symmetric_drop', False):
            # (h16) both steps lowered alike (an asymmetric source overreaches on one side only: a limping head bob)
            need = np.maximum(need, np.roll(need, N // 2))
        if need.max() > 1e-5:
            drop = drop + periodic_smooth(maximum_filter1d(need, 5, mode='wrap'), 3) * 1.15
            height = H0 + bob - drop
            pel, hips = hips_at(height)
        legs = {}
        for s, _, _ in SIDES:
            A = target[s] + np.outer(lift[s], [0, 1, 0])
            legs[s] = ik_leg(hips[s], A, pole[s], l1[s], l2[s], hinge[s], R_pel)
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local)
        lows = sole_heights(P, worlds, soles)
        if iteration == 3:
            break
        for s, _, _ in SIDES:
            low = lows[s]
            if iteration == 0:
                # one constant per side: soles on the floor during the source's stance
                offset = -float(np.median(low[contact[s]]))
                target[s][:, 1] += offset
                report.setdefault('stance_offset_m', {})[s] = offset
            else:
                under = np.maximum(-low, 0)
                lift[s] = lift[s] + periodic_smooth(maximum_filter1d(under, 5, mode='wrap'), 2) * 1.2
    if job.get('ground_every_frame', False):
        # a walk always has a foot on the floor: shift the whole body so the lowest sole is on it in every frame
        shift = -periodic_smooth(np.minimum(lows['L'], lows['R']), float(job.get('ground_sigma', 1.0)))
        for s, _, _ in SIDES:
            target[s][:, 1] += shift
        height = H0 + bob - drop + shift
        pel, hips = hips_at(height)
        legs = {s: ik_leg(hips[s], target[s] + np.outer(lift[s], [0, 1, 0]), pole[s], l1[s], l2[s], hinge[s], R_pel)
                for s, _, _ in SIDES}
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local)
        lows = sole_heights(P, worlds, soles)
        report['ground_shift_m'] = [float(shift.min()), float(shift.max())]
    if job.get('plant', True):
        # planted soles still: the sole vertices on the floor (the stride audit's band) must slide back at exactly
        # stride / length. Our feet roll about other points than the source's, so correct each ankle's forward
        # path by the integrated speed error over every contact run, then solve the legs again.
        v = S / T
        band = float(job.get('plant_band', 0.006))          # truly planted: within 6 mm of the floor
        dt = T / N
        fix = {s: np.zeros(N) for s, _, _ in SIDES}
        clip_err = float(job.get('plant_clip', 0.5))
        min_on = int(job.get('plant_min_vertices', 3))     # a low-poly sole (the ogre's claws) lands on fewer
        for _ in range(int(job.get('plant_iterations', 4))):
            skid = {s: np.zeros(N) for s, _, _ in SIDES}
            pts = sole_points(P, worlds, soles)
            for s, _, _ in SIDES:
                a, b = pts[s], np.roll(pts[s], -1, axis=0)
                band_s = max(band, float(pts[s][:, :, 1].min()) + band)   # a support that never quite lands
                err = np.zeros(N)
                on_any = np.zeros(N, dtype=bool)
                for i in range(N):
                    on = (a[i][:, 1] < band_s) & (b[i][:, 1] < band_s)
                    if on.sum() >= min_on and job.get('lift_skids', False):
                        # a support touching down while it still swings forward: keep it just off the floor
                        speed = np.median(-(b[i][on, 2] - a[i][on, 2]) / dt)
                        if speed < 0.3 * v:
                            skid[s][i] = band_s + 0.003 - float(a[i][:, 1].min())
                            continue
                    if on.sum() >= min_on:
                        err[i] = np.clip(np.median(-(b[i][on, 2] - a[i][on, 2]) / dt) - v, -clip_err * v, clip_err * v)
                        on_any[i] = True
                # integrate within each contact run (cyclic), anchored to zero mean over the run
                corr = np.zeros(N)
                if on_any.any() and not on_any.all():
                    start = int(np.argmin(on_any))            # a sample off the floor
                    order = [(start + j) % N for j in range(N)]
                    run = []
                    for i in order + [order[0]]:
                        if on_any[i] and i not in run:
                            run.append(i)
                            continue
                        if run:
                            acc = np.cumsum([err[j] * dt for j in run])
                            acc = np.concatenate([[0.0], acc[:-1]])
                            acc -= acc.mean()
                            corr[run] = acc
                            run = []
                # off the floor the correction is carried across the swing linearly (no pop at touch-down)
                if on_any.any() and not on_any.all():
                    known = np.where(on_any)[0]
                    idx = np.arange(N)
                    corr = np.interp(idx, np.concatenate([known - N, known, known + N]),
                                     np.tile(corr[known], 3))
                fix[s] = fix[s] + 0.8 * periodic_smooth(corr, 3.0)
                if skid[s].max() > 0:
                    lift[s] = lift[s] + periodic_smooth(maximum_filter1d(skid[s], 5, mode='wrap'), 2.0)
            for s, _, _ in SIDES:
                A = target[s] + np.outer(lift[s], [0, 1, 0]) + np.outer(fix[s], [0, 0, 1])
                legs[s] = ik_leg(hips[s], A, pole[s], l1[s], l2[s], hinge[s], R_pel)
            worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local)
        for s, _, _ in SIDES:
            target[s][:, 2] += fix[s]
        report['plant_fix_m'] = {s: [float(fix[s].min()), float(fix[s].max())] for s in fix}
        lows = sole_heights(P, worlds, soles)
        # the plant moves the ankles along the floor, so a rolling toe can dip under it again: lift once more
        for _ in range(3):
            under = {s: np.maximum(-lows[s], 0) for s in lows}
            if max(u.max() for u in under.values()) < 0.002:
                break
            for s, _, _ in SIDES:
                lift[s] = lift[s] + periodic_smooth(maximum_filter1d(under[s], 5, mode='wrap'), 2) * 1.2
                legs[s] = ik_leg(hips[s], target[s] + np.outer(lift[s], [0, 1, 0]), pole[s], l1[s], l2[s], hinge[s],
                                 R_pel)
            worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local)
            lows = sole_heights(P, worlds, soles)
    if job.get('toe_bend', True):
        worlds = bend_toes(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, report)
    report['pelvis_drop_max_m'] = float(drop.max())
    report['lift_max_m'] = {s: float(lift[s].max()) for s in lift}
    report['sole_low_m'] = {s: [float(lows[s].min()), float(np.median(lows[s][contact[s]]))] for s in lows}
    report['authored_speed'] = S / T
    pre = {}
    if job.get('arms_raise_deg') or job.get('elbow_forward_deg') or job.get('arm_out_deg'):
        if job.get('arms_raise_deg') and job.get('arm_clearance', True):
            raise SystemExit('arms_raise_deg needs arm_clearance false')
        worlds, pre = raise_arms(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, job, report)
    if job.get('arm_clearance', True):
        props = {node: str(ROOT / path) for node, path in job.get('clear_props', {}).items()}
        worlds, pre = clear_arms(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, report, props, pre,
                                 tuple(job.get('clear_extra_targets', ())))
    if job.get('prop_floor'):
        worlds, pre = lift_prop(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, job, report, pre)
    if job.get('cape_lift'):
        # (h05) a cape streams further back at a faster gait: every chain root of `prefix` turned back by `deg` about
        # the body's lateral axis at its joint (world pre-rotation; the chains keep the base clip's motion below it)
        cfg = job['cape_lift']
        _, roots = skirt_chains(P, cfg.get('prefix', 'Cloak_'))
        pre = dict(pre)
        for root in roots.values():
            pre[root] = np.array([pitch(float(cfg['deg']))] * len(worlds))
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre)
        report['cape_lift_deg'] = float(cfg['deg'])
    if job.get('skirt_follow'):
        worlds, pre = follow_skirt(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, job, report, pre,
                                   W_bp)
    if job.get('skirt_clear'):
        worlds, pre = clear_skirt(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, job, report, pre)
    report['pre_rotated'] = sorted(pre)
    if job.get('ring_skirt') is not None:
        # (h05) the MM6 PeasantF3's five-ring skirt cage fitted to the new legs (ring_skirt.py, her project's fit)
        import ring_skirt
        sim = ring_skirt.RingSkirt(P, job['ring_skirt'])
        worlds = sim.pose(worlds)
        P.extra_authored = getattr(P, 'extra_authored', set()) | sim.nodes()
    if job.get('align'):
        # the loop's start: the left ankle forward-most (relative to the pelvis) at the reference clip's phase
        Tr = P.clip_length(job['align'])
        _, W_ref = P.clip_world(job['align'], np.arange(240) / 240 * Tr)
        ref = W_ref[:, I['B_L_Foot'], 2, 3] - W_ref[:, I['B_Pelvis'], 2, 3]
        phi_ref = np.argmax(ref) / 240
        ours = worlds[:, I['B_L_Foot'], 2, 3] - worlds[:, I['B_Pelvis'], 2, 3]
        psi = np.argmax(ours) / N
        shift = int(round((psi - phi_ref) * N)) % N
        worlds = np.roll(worlds, -shift, axis=0)
        base_local = base_local[shift:] + base_local[:shift]
        report['align'] = {'clip': job['align'], 'reference_left_front': float(phi_ref),
                           'solved_left_front': float(psi), 'shift_samples': shift}
    return worlds, base_local, report


def raise_arms(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, job, report):
    """World-space arm changes applied after the body is solved (both need arm_clearance false):
    - `arms_raise_deg`: both arms (and a two-handed prop) turned forward and up as one rigid unit, the same world
      rotation about the line through both shoulder joints applied to both upper arms, so a two-handed grip is kept
      exactly. Positive moves the hands forward and up. For a sprinting body whose knees drive up into a weapon carried
      across the thighs (the Minotaur's axe).
    - `elbow_forward_deg` {L, R}: the forearm bent about the elbow toward the travel direction (+Z) by that angle, in
      the plane of the upper arm and +Z, per sample: a running arm from a walk's hanging arm whose measured forearm
      hinge (gain_arms' `elbow_flex_deg`) is mostly a twist and swung the hand across the body (the Jackalman)."""
    I = P.idx
    pre = {}
    if job.get('arms_raise_deg'):
        angle = -np.radians(float(job['arms_raise_deg']))
        mats = []
        for W in worlds:
            axis = unit(W[I['B_L_UpperArm'], :3, 3] - W[I['B_R_UpperArm'], :3, 3])
            mats.append(glb_pose.quaternion_matrix(np.append(axis * np.sin(angle / 2), np.cos(angle / 2))))
        pre = {f'B_{s}_UpperArm': np.array(mats) for s in 'LR'}
        report['arms_raise_deg'] = float(job['arms_raise_deg'])
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre)
    for s, degrees in job.get('arm_out_deg', {}).items():
        # (h02's addition, same form) abduction: the upper arm turned out about the travel axis (+Z) at the shoulder
        angle = np.radians(float(degrees)) * (1.0 if s == 'L' else -1.0)
        out = glb_pose.quaternion_matrix(np.array([0.0, 0.0, np.sin(angle / 2), np.cos(angle / 2)]))
        name = f'B_{s}_UpperArm'
        pre[name] = np.array([out @ m for m in pre[name]]) if name in pre else np.array([out] * len(worlds))
        report.setdefault('arm_out_deg', {})[s] = float(degrees)
    if job.get('arm_out_deg'):
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre)
    for s, degrees in job.get('elbow_forward_deg', {}).items():
        angle = np.radians(float(degrees))
        mats = []
        for W in worlds:
            d = unit(W[I[f'B_{s}_Forearm'], :3, 3] - W[I[f'B_{s}_UpperArm'], :3, 3])
            axis = unit(np.cross(d, np.array([0.0, 0.0, 1.0])))
            mats.append(glb_pose.quaternion_matrix(np.append(axis * np.sin(angle / 2), np.cos(angle / 2))))
        pre[f'B_{s}_Forearm'] = np.array(mats)
        report.setdefault('elbow_forward_deg', {})[s] = float(degrees)
    if job.get('elbow_forward_deg'):
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre)
    return worlds, pre
    return worlds, pre


def lock_stance(job, target, foot_rot, flat_feet, contact, std_ankle, v, dt, report):
    """Planted feet by construction (a sprint's contacts are too short for the integral plant correction): over each
    source contact the ankle slides back at exactly the ground speed v through its mid-contact point, at Standing's
    ankle height, and the foot holds its flat stance rotation; `lock_blend` samples blend in and out on each side."""
    blend = int(job.get('lock_blend', 3))
    extend = int(job.get('lock_extend', 0))           # samples added to each end of the source contact
    for s in target:
        on = contact[s]
        N = len(on)
        if on.all() or not on.any():
            continue
        start = int(np.argmin(on))
        order = [(start + j) % N for j in range(N)]
        runs, run = [], []
        for i in order:
            if on[i]:
                run.append(i)
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        lengths = []
        for run in runs:
            run = [(run[0] - j - 1) % N for j in reversed(range(extend))] + run + \
                  [(run[-1] + j + 1) % N for j in range(extend)]
            lengths.append(len(run))
            mid = run[len(run) // 2]
            z_mid = target[s][mid, 2]
            R_flat = flat_feet[s]
            for d in range(-len(run) // 2 - blend, len(run) - len(run) // 2 + blend):
                i = (mid + d) % N
                inside = -(len(run) // 2) <= d < len(run) - len(run) // 2
                if inside:
                    w = 1.0
                else:
                    gap = (-(len(run) // 2) - d) if d < 0 else d - (len(run) - len(run) // 2 - 1)
                    x = 1.0 - gap / (blend + 1)
                    w = x * x * (3 - 2 * x)
                target[s][i, 2] = (1 - w) * target[s][i, 2] + w * (z_mid - v * d * dt)
                target[s][i, 1] = (1 - w) * target[s][i, 1] + w * std_ankle[s][1]
                q = glb_pose.slerp(glb_pose.matrix_quaternion(foot_rot[s][i]), glb_pose.matrix_quaternion(R_flat), w)
                foot_rot[s][i] = glb_pose.quaternion_matrix(q)
        report.setdefault('lock_samples', {})[s] = lengths


def pitch(degrees):
    """World rotation about +X (the body's left): positive tilts +Y toward +Z, a forward lean."""
    a = np.radians(degrees)
    return np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])


ARM_GAIN_BONES = ('Clavicle', 'UpperArm', 'Forearm')


def gain_arms(P, base_local, job, report):
    """Scale the base clip's arm swing about its loop mean (local rotations of clavicle, upper arm and forearm), per
    side: `arm_gain` (all) or `side_gain` {L, R}. Hands, fingers, twist bones and props keep their own locals, so grips
    are unchanged; `elbow_flex_deg` {L, R} adds a constant extra elbow bend (forearm local, about its hinge)."""
    gains = {s: float(job.get('side_gain', {}).get(s, job.get('arm_gain', 1.0))) for s in 'LR'}
    flex = {s: float(job.get('elbow_flex_deg', {}).get(s, 0.0)) for s in 'LR'}
    report['arm_gain'] = gains
    for s in 'LR':
        for bone in ARM_GAIN_BONES:
            node = P.idx.get(f'B_{s}_{bone}')
            if node is None or node not in base_local[0]:
                continue
            g = gains[s] if bone != 'Clavicle' else 1.0 + 0.5 * (gains[s] - 1.0)
            if abs(g - 1.0) < 1e-6 and not (bone == 'Forearm' and flex[s]):
                continue
            mats = np.array([glb_pose.quaternion_matrix(local[node][1]) for local in base_local])
            mean = qmean(mats)
            extra = np.eye(3)
            if bone == 'Forearm' and flex[s]:
                # hinge: the axis of the forearm's largest swing about its mean (measured, not assumed)
                rv = []
                for m in mats:
                    q = glb_pose.matrix_quaternion(m @ mean.T)
                    rv.append(q[:3] * np.sign(q[3] if q[3] else 1.0))
                rv = np.array(rv)
                axis = np.linalg.svd(rv - rv.mean(axis=0) if len(rv) > 2 else rv)[2][0]
                # bend direction: the sign that increases the mean flexion (larger rotation from rest)
                rest_q = P.model.rest[node][1]
                rest = glb_pose.quaternion_matrix(rest_q)

                def bend(r):
                    return np.degrees(np.arccos(np.clip((np.trace(r @ rest.T) - 1) / 2, -1, 1)))
                a = np.radians(flex[s])
                cand = [glb_pose.quaternion_matrix(np.append(sg * axis * np.sin(a / 2), np.cos(a / 2)))
                        for sg in (1.0, -1.0)]
                extra = max(cand, key=lambda r: bend(r @ mean))
            for local, m in zip(base_local, mats):
                r = rot_power(m @ mean.T, g) @ extra @ mean
                t, _, sc = local[node]
                local[node] = (t, glb_pose.matrix_quaternion(r), sc)


def gain_skirt(P, base_local, job, report):
    """(h04) A long skirt's swing for a longer stride: the base clip's skirt-chain rotations (nodes named
    `skirt_prefix`, default Skirt_) scaled about their loop mean by `skirt_gain`, local to each parent like gain_arms.
    The chains hang from the pelvis, so they also follow the new pelvis; the gain widens the cloth's fore-aft swing
    roughly with the stride (the base clip's skirt was fitted to its own, shorter legs)."""
    prefix = job.get('skirt_prefix', 'Skirt_')
    g = float(job['skirt_gain'])
    nodes = [i for i, n in enumerate(P.nodes) if n.get('name', '').startswith(prefix) and i in base_local[0]]
    for node in nodes:
        mats = np.array([glb_pose.quaternion_matrix(local[node][1]) for local in base_local])
        mean = qmean(mats)
        for local, m in zip(base_local, mats):
            t, _, sc = local[node]
            local[node] = (t, glb_pose.matrix_quaternion(rot_power(m @ mean.T, g) @ mean), sc)
    report['skirt_gain'] = {'gain': g, 'nodes': len(nodes)}


def lift_prop(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, job, report, pre):
    """(h04) A held prop kept off the floor: the base clip's staff carry over a lower, leaning run put the MM6 elder's
    staff foot through the floor (his accepted Running already dips it 5 cm). Where the prop's lowest point is below
    `margin_m`, the holding arm's upper arm turns about the shoulder (world pre-rotation, axis (tip - shoulder) x up,
    so the tip rises) by the least smoothed angle; the grip is unchanged. `prop_floor`: {node, path, side (R),
    margin_m (0.01)}."""
    cfg = job['prop_floor']
    I = P.idx
    node = I[cfg['node']]
    pts = np.concatenate([q['positions'] for q in glb_pose.Model(glb_pose.Glb(str(ROOT / cfg['path']))).primitives])
    side = cfg.get('side', 'R')
    margin = float(cfg.get('margin_m', 0.01))
    arm = f'B_{side}_UpperArm'
    N = len(worlds)
    rotvec = np.zeros((N, 3))
    base_pre = pre.get(arm)
    pre = dict(pre)

    def lows(worlds):
        depth, tip = np.zeros(N), np.zeros((N, 3))
        for i, W in enumerate(worlds):
            q = pts @ W[node, :3, :3].T + W[node, :3, 3]
            k = int(np.argmin(q[:, 1]))
            depth[i], tip[i] = margin - q[k, 1], q[k]
        return depth, tip

    depth, tip = lows(worlds)
    report['prop_low_m_before'] = float(margin - depth.max())
    for _ in range(6):
        if depth.max() < 0.002:
            break
        shoulder = worlds[:, I[arm], :3, 3]
        r = tip - shoulder
        axis = np.cross(r, np.array([0.0, 1.0, 0.0]))
        axis = axis / np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-9)
        horizontal = np.maximum(np.linalg.norm(r[:, [0, 2]], axis=1), 0.15)
        need = np.where(depth > 0, (depth + 0.003) / horizontal, 0.0)[:, None] * axis
        mag = np.linalg.norm(need, axis=1)
        spread = np.array([need[(i + np.arange(-3, 4)) % N][np.argmax(mag[(i + np.arange(-3, 4)) % N])]
                           for i in range(N)])
        rotvec = rotvec + periodic_smooth(spread, 2.0) * 1.15
        mats = []
        for v in rotvec:
            a = np.linalg.norm(v)
            ax = v / a if a > 1e-12 else np.array([1.0, 0, 0])
            mats.append(glb_pose.quaternion_matrix(np.append(ax * np.sin(a / 2), np.cos(a / 2))))
        pre[arm] = np.array([m @ b for m, b in zip(mats, base_pre)]) if base_pre is not None else np.array(mats)
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre)
        depth, tip = lows(worlds)
    report['prop_low_m_after'] = float(margin - depth.max())
    report['prop_lift_deg'] = float(np.degrees(np.linalg.norm(rotvec, axis=1).max()))
    return worlds, pre


def skirt_chains(P, prefix):
    """Skirt chains: name prefix<chain>_<k>; chain -> root node name (the chain node whose parent is not in it)."""
    names = [n.get('name', '') for n in P.nodes]
    chain_of = {n: n[len(prefix):].rsplit('_', 1)[0] for n in names if n.startswith(prefix)}
    roots = {}
    for n, c in chain_of.items():
        parent = P.parent[P.idx[n]]
        if parent < 0 or names[parent] not in chain_of:
            roots[c] = n
    return chain_of, roots


def follow_skirt(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, job, report, pre, W_base):
    """(h04) The base clip's skirt motion corrected for the new legs: the skirt chains swing with the base clip's
    thighs, so where a jog's thigh is further forward (or back) than the base clip's at the same phase, the chains in
    front of (behind) that thigh turn with it. Per chain root (a world pre-rotation about the body's lateral axis at the
    root joint): angle = -gain x (thigh pitch difference) x facing x side, facing = the chain's forward (backward)
    share of its hanging direction in Standing (cosine, positive part), side = 0.5 + 0.5 x its lateral share toward
    that thigh. `skirt_follow`: {gain (0.6), prefix (Skirt_)}."""
    cfg = job['skirt_follow'] if isinstance(job['skirt_follow'], dict) else {}
    prefix = cfg.get('prefix', 'Skirt_')
    gain = float(cfg.get('gain', 0.6))
    I = P.idx
    _, roots = skirt_chains(P, prefix)
    _, W_std = P.clip_world('Standing', [0.0])
    W_std = W_std[0]
    centre = W_std[I['B_Pelvis'], :3, 3]

    def pitch_of(W, s):
        d = W[:, I[f'B_{s}_Calf'], :3, 3] - W[:, I[f'B_{s}_Thigh'], :3, 3]
        return np.arctan2(d[:, 2], -d[:, 1])

    delta = {s: periodic_smooth(pitch_of(worlds, s) - pitch_of(W_base, s), 1.5) for s, _, _ in SIDES}
    pre = dict(pre)
    turns = []
    # the chain's hanging direction in Standing: root joint to its deepest descendant
    names = [n.get('name', '') for n in P.nodes]
    for c, root in roots.items():
        tips = [i for i, n in enumerate(names) if n.startswith(f'{prefix}{c}_')]
        tip = min(tips, key=lambda i: W_std[i, 1, 3])
        d = W_std[tip, :3, 3] - centre
        d[1] = 0.0
        d = d / max(np.linalg.norm(d), 1e-9)
        angle = np.zeros(len(worlds))
        for s, _, sign in SIDES:
            side = 0.5 + 0.5 * sign * d[0]
            facing = np.where(delta[s] > 0, max(d[2], 0.0), max(-d[2], 0.0))
            angle += -gain * delta[s] * facing * side
        turns.append(float(np.degrees(np.abs(angle).max())))
        pre[root] = np.array([pitch(np.degrees(a)) for a in angle])
    report['skirt_follow_max_deg'] = max(turns)
    return assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre), pre


def clear_skirt(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, job, report, pre):
    """(h04) A long skirt kept outside the new legs: the base clip's skirt chains were fitted to its own, smaller knee
    lift, so a jog's knee showed through the cloth. The legs are capsules (lower half of the thigh, knee to ankle; radii
    `thigh_radius_m` 0.065 and `calf_radius_m` 0.055: the skin's measured 75th-90th percentile distance from the bone
    axis plus about a centimetre); per sample, the deepest skirt vertex of each chain inside a capsule pushes the chain
    out: its root bone turns, as a world pre-rotation about its root joint, by the least angle that moves that vertex
    out of the capsule (+8 mm), dilated and smoothed over time like the arm clearance. Children follow (a chain stays
    one piece), and neighbouring chains round the hem take a share of the strongest nearby turn (`neighbour_share`, default
    0.75 and 0.4 for the next two), so the panel moves together. `skirt_clear`: {prefix (Skirt_), iterations (6),
    thigh_radius_m, calf_radius_m, neighbour_share}. (Nearest-vertex skin
    tests were too noisy on the sparse cloth: the accepted Walking read 50 mm deep with nothing visible.)"""
    cfg = job['skirt_clear'] if isinstance(job['skirt_clear'], dict) else {}
    prefix = cfg.get('prefix', 'Skirt_')
    prim = P.model.primitives[0]
    names = [n.get('name', '') for n in P.nodes]
    dom = [names[P.model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])),
                                                           prim['weights'].argmax(axis=1)]]
    # chains: prefix<chain>_<k>; the root is the chain node whose parent is not in the chain
    chain_of = {}
    for i, n in enumerate(names):
        if n.startswith(prefix):
            chain_of[n] = n[len(prefix):].rsplit('_', 1)[0]
    roots = {}
    for n, c in chain_of.items():
        parent = P.parent[P.idx[n]]
        if parent < 0 or names[parent] not in chain_of:
            roots[c] = n
    skirt_v = np.array([d in chain_of for d in dom])
    si = np.where(skirt_v)[0]
    chain_v = np.array([chain_of[dom[v]] for v in si])
    chains = sorted(roots)
    N = len(worlds)
    I = P.idx
    rotvec = {c: np.zeros((N, 3)) for c in chains}
    pre = dict(pre)
    follow = {roots[c]: pre[roots[c]] for c in chains if roots[c] in pre}      # follow_skirt's turn stays under

    radius = {'Thigh': float(cfg.get('thigh_radius_m', 0.065)), 'Calf': float(cfg.get('calf_radius_m', 0.055)),
              'Foot': float(cfg.get('foot_radius_m', 0.0))}      # (h05) a boot (ankle to toe), off by default

    def depths(worlds):
        """Per chain and sample: the deepest skirt vertex inside a leg capsule (lower half of the thigh, knee to
        ankle; radii measured on the skin, plus a margin), that vertex and the direction out of the capsule."""
        out = {c: (np.zeros(N), np.zeros((N, 3)), np.zeros((N, 3))) for c in chains}
        for i, W in enumerate(worlds):
            pts = P.model.skinned_positions(W)[0][0][si]
            best = np.zeros(len(si))
            away = np.zeros((len(si), 3))
            for s, _, _ in SIDES:
                H, K, A, F = (W[I[f'B_{s}_{b}'], :3, 3] for b in ('Thigh', 'Calf', 'Foot', 'Toe0'))
                for seg, (a, b) in (('Thigh', (0.5 * (H + K), K)), ('Calf', (K, A)), ('Foot', (A, F))):
                    if radius[seg] <= 0:
                        continue
                    ab = b - a
                    t = np.clip(((pts - a) @ ab) / (ab @ ab), 0.0, 1.0)
                    rel = pts - (a + t[:, None] * ab)
                    dist = np.linalg.norm(rel, axis=1)
                    pen = radius[seg] - dist
                    take = pen > best
                    best[take] = pen[take]
                    away[take] = rel[take] / np.maximum(dist[take, None], 1e-9)
            for c in chains:
                m = (best > 0.003) & (chain_v == c)
                if m.any():
                    k = int(np.argmax(np.where(m, best, 0)))
                    out[c][0][i] = best[k]
                    out[c][1][i] = pts[k]
                    out[c][2][i] = away[k]
        return out

    current = depths(worlds)
    report['skirt_inside_mm_before'] = float(1000 * max(current[c][0].max() for c in chains))
    for _ in range(int(cfg.get('iterations', 6))):
        if max(current[c][0].max() for c in chains) < 0.003:
            break
        for c in chains:
            d, p, n = current[c]
            if d.max() < 0.003:
                continue
            root = np.array([W[I[roots[c]], :3, 3] for W in worlds])
            arm = p - root
            lever = np.maximum(np.linalg.norm(arm, axis=1), 0.1)
            axis = np.cross(arm, n)
            axis = axis / np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-9)
            need = np.where(d > 0, (d + 0.008) / lever, 0.0)[:, None] * axis
            mag = np.linalg.norm(need, axis=1)
            spread = np.array([need[(i + np.arange(-3, 4)) % N][np.argmax(mag[(i + np.arange(-3, 4)) % N])]
                               for i in range(N)])
            rotvec[c] = rotvec[c] + periodic_smooth(spread, 2.0) * 1.15
        # neighbouring chains share the push (the cloth is one panel: a lone chain opened a slit beside the knee).
        # Chains are numbered round the hem; each takes the strongest of its neighbours' turns, scaled by distance.
        # (h05) chain names m88..m11, p0..p88 (the MM6 Nobleman's cape: signed angle round the shoulders) sort by angle
        def ring_key(c):
            if c.isdigit():
                return int(c)
            if c[:1] in 'mp' and c[1:].isdigit():
                return -int(c[1:]) if c[0] == 'm' else int(c[1:])
            return c
        ring = sorted(chains, key=ring_key)
        share = [float(w) for w in cfg.get('neighbour_share', (0.75, 0.4))]
        mags = {c: np.linalg.norm(rotvec[c], axis=1) for c in ring}
        shared = {}
        for n, c in enumerate(ring):
            best, best_mag = rotvec[c].copy(), mags[c].copy()
            for k, w in enumerate(share, start=1):
                for other in (ring[(n - k) % len(ring)], ring[(n + k) % len(ring)]):
                    cand = w * mags[other]
                    take = cand > best_mag
                    best[take] = w * rotvec[other][take]
                    best_mag[take] = cand[take]
            shared[c] = best
        rotvec = shared
        for c in chains:
            if not np.abs(rotvec[c]).max():
                continue
            mats = []
            for v in rotvec[c]:
                a = np.linalg.norm(v)
                ax = v / a if a > 1e-12 else np.array([1.0, 0, 0])
                mats.append(glb_pose.quaternion_matrix(np.append(ax * np.sin(a / 2), np.cos(a / 2))))
            pre[roots[c]] = np.array([m @ f for m, f in zip(mats, follow[roots[c]])]) if roots[c] in follow \
                else np.array(mats)
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre)
        current = depths(worlds)
    report['skirt_inside_mm_after'] = float(1000 * max(current[c][0].max() for c in chains))
    report['skirt_turn_deg'] = float(np.degrees(max(np.linalg.norm(rotvec[c], axis=1).max() for c in chains)))
    return worlds, pre


def bend_toes(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, report):
    """Toes that stay on the floor at toe-off: where a toe vertex (dominated by the toe bone) would go under the floor
    as the heel rises, the toe bends up (dorsiflexion, about the body's lateral axis at the toe joint) by the least
    smoothed angle that keeps it on the floor. The ogre's claws pointed into the floor without it."""
    prim = P.model.primitives[0]
    dom = np.asarray(P.model.joints)[prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
    N = len(worlds)
    P.toe_bend = {s: np.zeros(N) for s, _, _ in SIDES}
    for _ in range(5):
        worst = 0.0
        for s, _, _ in SIDES:
            node = P.idx[f'B_{s}_Toe0']
            ids = np.where(dom == node)[0]
            if not len(ids):
                continue            # a rigid sabaton: no toe-dominated skin
            need = np.zeros(N)
            for i, W in enumerate(worlds):
                pts = P.model.skinned_positions(W)[0][0][ids]
                k = int(np.argmin(pts[:, 1]))
                depth = -pts[k, 1]
                if depth > 0.001:
                    lever = max(float(np.linalg.norm((pts[k] - W[node, :3, 3])[1:])), 0.03)
                    need[i] = -np.degrees(np.arcsin(min((depth + 0.002) / lever, 1.0)))
                worst = max(worst, depth)
            P.toe_bend[s] = P.toe_bend[s] + periodic_smooth(-maximum_filter1d(-need, 5, mode='wrap'), 1.5) * 1.1
        if worst < 0.002:
            break
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local)
    report['toe_bend_deg'] = {s: float(-P.toe_bend[s].min()) for s in P.toe_bend}
    return worlds


ARM_PROBE = ('Forearm', 'Hand', 'Finger')
BODY_TARGET = ('Thigh', 'Calf', 'Foot', 'Toe', 'Pelvis', 'Spine')


def arm_depths(P, worlds, groups):
    """Per side and sample: the deepest forearm/hand vertex inside the legs/trunk skin (m, 0 if none) and the
    vertex's position."""
    from scipy.spatial import cKDTree
    prim, probe, target, props = groups
    out = {s: (np.zeros(len(worlds)), np.zeros((len(worlds), 3)), np.zeros((len(worlds), 3))) for s in 'LR'}
    for i, W in enumerate(worlds):
        points, _ = P.model.skinned_positions(W)[0]
        normals = vertex_normals(points, prim['triangles'])
        tree = cKDTree(points[target])
        tp, tn = points[target], normals[target]
        for s in 'LR':
            p = points[probe[s]]
            for side, node, pts in props:
                if side == s:
                    p = np.concatenate([p, pts @ W[node, :3, :3].T + W[node, :3, 3]])
            d, j = tree.query(p)
            depth = np.einsum('ij,ij->i', p - tp[j], tn[j])
            inside = (d < 0.04) & (depth < -0.002)
            if inside.any():
                k = np.argmin(np.where(inside, depth, 0))
                out[s][0][i] = -depth[k]
                out[s][1][i] = p[k]
                out[s][2][i] = tn[j[k]]
    return out


def vertex_normals(points, triangles):
    n = np.zeros_like(points)
    face = np.cross(points[triangles[:, 1]] - points[triangles[:, 0]], points[triangles[:, 2]] - points[triangles[:, 0]])
    for c in range(3):
        np.add.at(n, triangles[:, c], face)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def clear_arms(P, worlds, base_local, world_rot, pel, legs, foot_rot, toe_local, report, job_props=None, pre=None,
               extra_targets=()):
    """Hands kept outside the body envelope: where a forearm or hand would enter the legs or trunk (their own
    clip's arm swing over our new legs), turn the upper arm outward (abduction about the shoulder) by the least
    angle that clears it, smoothed over time. Arms, hands and props move together, so grips are unchanged."""
    prim = P.model.primitives[0]
    names = [n['name'] for n in P.nodes]
    dom = [names[P.model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])),
                                                           prim['weights'].argmax(axis=1)]]
    probe = {s: np.array([d.startswith(f'B_{s}_') and any(t in d for t in ARM_PROBE) for d in dom]) for s in 'LR'}
    # h04: `clear_extra_targets` adds bone-name parts (Skirt_: a long skirt's chains) to the legs and trunk
    target = np.array([any(t in d for t in BODY_TARGET + extra_targets)
                       and not any(t in d for t in ('Clavicle', 'Arm', 'Hand', 'Finger')) for d in dom])
    props = []
    for node, path in (job_props or {}).items():
        # a held prop (attachment GLB on a hand-child node) is cleared with the arm that holds it
        pts = np.concatenate([q['positions'] for q in glb_pose.Model(glb_pose.Glb(path)).primitives])
        index = P.idx[node]
        chain = index
        while chain >= 0 and not P.nodes[chain]['name'].startswith(('B_L_', 'B_R_')):
            chain = P.parent[chain]
        props.append((P.nodes[chain]['name'][2], index, pts[::max(1, len(pts) // 400)]))
    groups = (prim, probe, target, props)
    N = len(worlds)
    rotvec = {s: np.zeros((N, 3)) for s in 'LR'}
    pre = dict(pre or {})        # h04: earlier forearm bends (elbow_forward_deg) are kept under the clearance
    I = P.idx
    before = arm_depths(P, worlds, groups)
    report['arm_inside_mm_before'] = {s: float(1000 * before[s][0].max()) for s in 'LR'}
    depths = before
    for _ in range(5):
        if max(depths[s][0].max() for s in 'LR') < 0.003:
            break
        for s in 'LR':
            d, p, n = depths[s]
            if d.max() < 0.003:
                continue
            shoulder = np.array([W[I[f'B_{s}_UpperArm'], :3, 3] for W in worlds])
            arm = p - shoulder
            lever = np.maximum(np.linalg.norm(arm, axis=1), 0.15)
            # turn about the shoulder so the deepest point moves out along the skin normal it is under
            axis = np.cross(arm, n)
            axis = axis / np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-9)
            need = np.where(d > 0, (d + 0.008) / lever, 0.0)[:, None] * axis
            # dilate in time (the strongest need within +-3 keys), then smooth
            mag = np.linalg.norm(need, axis=1)
            spread = np.array([need[(i + np.arange(-3, 4)) % N][np.argmax(mag[(i + np.arange(-3, 4)) % N])]
                               for i in range(N)])
            rotvec[s] = rotvec[s] + periodic_smooth(spread, 2.5) * 1.15
        for s in 'LR':
            if not np.abs(rotvec[s]).max():
                continue
            mats = []
            for v in rotvec[s]:
                a = np.linalg.norm(v)
                ax = v / a if a > 1e-12 else np.array([1.0, 0, 0])
                mats.append(glb_pose.quaternion_matrix(np.append(ax * np.sin(a / 2), np.cos(a / 2))))
            pre[f'B_{s}_UpperArm'] = np.array(mats)
        worlds = assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre)
        depths = arm_depths(P, worlds, groups)
    angle = {s: np.linalg.norm(rotvec[s], axis=1) for s in 'LR'}
    report['arm_clearance_deg'] = {s: float(np.degrees(angle[s].max())) for s in 'LR'}
    report['arm_inside_mm_after'] = {s: float(1000 * depths[s][0].max()) for s in 'LR'}
    return worlds, pre


def sole_sets(P, W_std):
    """Per side: LOD0 vertex indices (per primitive) below 6 cm in Standing, split by the body's mid plane."""
    posed = P.model.skinned_positions(W_std)
    mid_x = W_std[P.idx['B_Pelvis'], 0, 3]
    sets = {'L': [], 'R': []}
    for points, _ in posed:
        low = points[:, 1] < 0.06
        sets['L'].append(np.where(low & (points[:, 0] > mid_x))[0])
        sets['R'].append(np.where(low & (points[:, 0] <= mid_x))[0])
    return sets


def sole_points(P, worlds, soles):
    out = {'L': [], 'R': []}
    for W in worlds:
        posed = P.model.skinned_positions(W)
        for s in out:
            out[s].append(np.concatenate([points[ids] for (points, _), ids in zip(posed, soles[s]) if len(ids)]))
    return {s: np.array(v) for s, v in out.items()}


def sole_heights(P, worlds, soles):
    out = {'L': [], 'R': []}
    for W in worlds:
        posed = P.model.skinned_positions(W)
        for s in out:
            vals = [points[ids, 1].min() for (points, _), ids in zip(posed, soles[s]) if len(ids)]
            out[s].append(min(vals))
    return {s: np.array(v) for s, v in out.items()}


def ik_leg(H, A, pole, l1, l2, hinge, R_pel):
    """World thigh and calf rotations and the knee position, per sample."""
    n_samples = len(H)
    thigh = np.zeros((n_samples, 3, 3))
    calf = np.zeros((n_samples, 3, 3))
    knees = np.zeros((n_samples, 3))
    ht, hc = hinge
    for i in range(n_samples):
        d_vec = A[i] - H[i]
        d = np.clip(np.linalg.norm(d_vec), abs(l1 - l2) + 1e-4, (l1 + l2) * 0.9999)
        u = d_vec / np.linalg.norm(d_vec)
        w = pole[i] - u * np.dot(pole[i], u)
        w = w / np.linalg.norm(w)
        a = (d * d + l1 * l1 - l2 * l2) / (2 * d)
        b = np.sqrt(max(l1 * l1 - a * a, 0.0))
        K = H[i] + a * u + b * w
        n = np.cross(w, u)
        n = n / np.linalg.norm(n)
        F_local_t = frame_from(np.array([0, 1.0, 0]), ht)
        F_local_c = frame_from(np.array([0, 1.0, 0]), hc)
        thigh[i] = frame_from(K - H[i], n) @ F_local_t.T
        calf[i] = frame_from(H[i] + d * u - K, n) @ F_local_c.T
        knees[i] = K
    return thigh, calf, knees


def assemble(P, base_local, world_rot, pel, legs, foot_rot, toe_local, pre=None):
    """World matrices of every node per sample: base clip locals, then the authored trunk and legs on top."""
    I = P.idx
    out = []
    for i, local in enumerate(base_local):
        W = np.zeros((len(P.nodes), 4, 4))
        for index in P.order:
            trs = local.get(index, P.model.rest[index])
            M = glb_pose.trs_matrix(*trs)
            parent = P.parent[index]
            Wp = W[parent] if parent >= 0 else np.eye(4)
            name = P.nodes[index]['name']
            R = None
            if name in world_rot:
                R = world_rot[name][i]
            else:
                for s, _, _ in SIDES:
                    if name == f'B_{s}_Thigh':
                        R = legs[s][0][i]
                    elif name == f'B_{s}_Calf':
                        R = legs[s][1][i]
                    elif name == f'B_{s}_Foot':
                        R = Wp[:3, :3] @ foot_rot[s][1] if isinstance(foot_rot[s], tuple) else foot_rot[s][i]
                    elif name == f'B_{s}_Toe0':
                        R = Wp[:3, :3] @ glb_pose.quaternion_matrix(toe_local[s])
                        bend = getattr(P, 'toe_bend', {}).get(s)
                        if bend is not None and bend[i]:
                            R = pitch(bend[i]) @ R
            if R is not None:
                world = np.eye(4)
                world[:3, :3] = R * np.asarray(trs[2])[None, :]
                world[:3, 3] = pel[i] if name == 'B_Pelvis' else (Wp @ np.append(trs[0], 1.0))[:3]
                W[index] = world
            else:
                W[index] = Wp @ M
                if pre and name in pre:
                    W[index][:3, :3] = pre[name][i] @ W[index][:3, :3]
        for helper, thigh in getattr(P, 'thigh_swing', {}).items():
            W[helper] = W[P.parent[helper]] @ glb_pose.trs_matrix(*swing_local(P, W, helper, thigh))
        out.append(W)
    return np.array(out)


def swing_local(P, W, helper, thigh):
    """Local TRS of a swing-only helper: its rest rotation times the swing part of the thigh's local rotation from
    the thigh's rest (the twist about the bone's own Y axis removed). Both are children of the pelvis."""
    local = np.linalg.inv(W[P.parent[thigh]]) @ W[thigh]
    rest_t, rest_h = P.model.rest[thigh], P.model.rest[helper]
    q_rest = glb_pose.matrix_quaternion(glb_pose.quaternion_matrix(rest_t[1]))
    b = quat_mul(quat_inv(q_rest), glb_pose.matrix_quaternion(local[:3, :3] / np.linalg.norm(local[:3, :3], axis=0)))
    twist = np.array([0.0, b[1], 0.0, b[3]])
    twist = twist / np.linalg.norm(twist)
    swing = quat_mul(b, quat_inv(twist))
    return np.asarray(rest_h[0]), quat_mul(np.asarray(rest_h[1]), swing), np.asarray(rest_h[2])


def quat_mul(a, b):
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def quat_inv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]])


def write_clip(P, name, worlds, base_local, base_clip, T, extra=()):
    """Append an animation: T/R/S of every node the base clip animates, keys at k * T / N plus the loop key."""
    g = P.glb
    animations = g.json.setdefault('animations', [])
    if any(a.get('name') == name for a in animations):
        raise SystemExit(f'{name} already exists in the input GLB')
    N = len(worlds)
    times = np.arange(N + 1) / N * T
    t_acc = g.append_accessor(times.reshape(-1, 1), 'SCALAR')
    channels, samplers = [], []
    authored = {P.idx[name] for name, _ in CHAIN} | {P.idx[name] for name in LEG_BONES} | {P.idx[n] for n in extra} \
        | getattr(P, 'extra_authored', set())
    for node in P.channel_nodes(base_clip):
        parent = P.parent[node]
        trs_t, trs_r, trs_s = [], [], []
        for i in range(N + 1):
            base_trs = base_local[i % N].get(node, P.model.rest[node])
            if node not in authored:
                trs_t.append(np.asarray(base_trs[0]))
                trs_r.append(np.asarray(base_trs[1]))
                trs_s.append(np.asarray(base_trs[2]))
                continue
            W = worlds[i % N]
            local_world = np.linalg.inv(W[parent]) @ W[node] if parent >= 0 else W[node]
            trs_t.append(local_world[:3, 3])
            trs_r.append(glb_pose.matrix_quaternion(local_world[:3, :3]))
            trs_s.append(np.asarray(base_trs[2]))
        q = np.array(trs_r)
        for i in range(1, len(q)):
            if np.dot(q[i], q[i - 1]) < 0:
                q[i] = -q[i]
        for path, values, kind in (('translation', np.array(trs_t), 'VEC3'), ('rotation', q, 'VEC4'),
                                   ('scale', np.array(trs_s), 'VEC3')):
            out = g.append_accessor(values, kind)
            samplers.append({'input': t_acc, 'output': out, 'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': int(node), 'path': path}})
    animations.append({'name': name, 'channels': channels, 'samplers': samplers})


def main():
    src_glb, out_glb, jobs = sys.argv[1], sys.argv[2], sys.argv[3:]
    body = Body(src_glb)
    reports = []
    built = []
    for path in jobs:
        job = json.loads(Path(path).read_text())
        worlds, base_local, report = solve(body, job)
        built.append((job, worlds, base_local, report['pre_rotated']))
        reports.append(report)
        print(json.dumps(report, indent=1))
    for job, worlds, base_local, extra in built:
        write_clip(body, job['clip'], worlds, base_local, job['base'], float(job['duration']), extra)
    body.glb.write(out_glb)
    Path(out_glb).with_suffix('.compose.json').write_text(json.dumps(reports, indent=1))
    print('wrote', out_glb)


if __name__ == '__main__':
    main()
