"""Shared pieces of the gait rollout package h19 (copied from ../../mm6_sprint_humanoids_claude, itself adapted from
mm8_pirates_gait_claude): library clip sources (npz from extract_source.py), our GLB bodies, and Meshy joint aliases.

Axes are the GLB's: +Y up, the bodies face +Z, their left is +X.
"""
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
import glb_pose  # noqa: E402

UP = np.array([0.0, 1.0, 0.0])
MODELS = {m: ROOT / f'assets_source/worlds/mm8/models/mm8_{m}.glb' for m in ('m440', 'm540', 'm520', 'm436')}


# Meshy 24-bone humanoid rigs (the MM8 Lizardman Peasant) under the humanoid set's B_* names, so the composer and the
# probes read them like the B_* rigs. Applied in memory only; compose_gait.py restores the names before writing.
MESHY = {'Hips': 'B_Pelvis', 'Spine02': 'B_Spine', 'Spine01': 'B_Spine1', 'Spine': 'B_Spine2', 'neck': 'B_Neck',
         'Head': 'B_Head'}
for _s, _side in (('L', 'Left'), ('R', 'Right')):
    MESHY.update({f'{_side}UpLeg': f'B_{_s}_Thigh', f'{_side}Leg': f'B_{_s}_Calf', f'{_side}Foot': f'B_{_s}_Foot',
                  f'{_side}ToeBase': f'B_{_s}_Toe0', f'{_side}Shoulder': f'B_{_s}_Clavicle',
                  f'{_side}Arm': f'B_{_s}_UpperArm', f'{_side}ForeArm': f'B_{_s}_Forearm',
                  f'{_side}Hand': f'B_{_s}_Hand', f'{_side}Thumb': f'B_{_s}_Finger0',
                  f'{_side}Thumb_Tip': f'B_{_s}_Finger0Tip'})
    for _d in (1, 2, 3):
        MESHY.update({f'{_side}Digit{_d}': f'B_{_s}_Finger{_d}', f'{_side}Digit{_d}_Tip': f'B_{_s}_Finger{_d}Tip'})


def alias_nodes(glb):
    """Rename a Meshy rig's joints to B_* names in memory (no-op on B_* rigs); returns {alias: original}."""
    names = {n.get('name') for n in glb.json['nodes']}
    if 'B_Pelvis' in names or 'Hips' not in names:
        return {}
    back = {}
    for n in glb.json['nodes']:
        if n.get('name') in MESHY:
            back[MESHY[n['name']]] = n['name']
            n['name'] = MESHY[n['name']]
    return back


def restore_nodes(glb, back):
    for n in glb.json['nodes']:
        if n.get('name') in back:
            n['name'] = back[n['name']]


def open_glb(path):
    """glb_pose.Glb with Meshy joint names aliased to B_* (for probes: never written)."""
    glb = glb_pose.Glb(path)
    alias_nodes(glb)
    return glb


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


class Source:
    """A library clip: joint world matrices per frame (glTF axes), one loop cut out, facing and floor measured."""

    def __init__(self, path):
        data = np.load(path, allow_pickle=False)
        self.path = Path(path)
        self.names = [str(n) for n in data['names']]
        self.index = {n: i for i, n in enumerate(self.names)}
        self.fps = float(data['fps'])
        mats = data['mats']
        tails = data['toe_tails']
        self.rest = data['rest']
        # one loop: the clips loop (last frame = first); a multi-cycle clip is cut to its first cycle
        frames = len(mats) - 1
        self.cycles = self._cycles(mats, frames)
        n = frames // self.cycles
        self.mats = mats[:n + 1]
        self.tails = tails[:n + 1]
        self.n = n                       # keys 0..n, key n = key 0 of the next loop
        self.period = n / self.fps
        # facing: mean horizontal foot direction (ankle -> toe end), both feet, all frames
        d = np.concatenate([self.tails[:, k] - self.pos(f'{s}Foot') for k, s in enumerate(('Left', 'Right'))])
        d[:, 1] = 0.0
        self.forward = unit(d.mean(axis=0))
        self.left = np.cross(UP, self.forward)
        hip, knee, ankle = (self.rest[self.index[f'LeftUpLeg']][:3, 3], self.rest[self.index['LeftLeg']][:3, 3],
                            self.rest[self.index['LeftFoot']][:3, 3])
        self.leg_length = float(np.linalg.norm(knee - hip) + np.linalg.norm(ankle - knee))
        self.floor = float(min(self.tails[:, :, 1].min(), self.pos('LeftToeBase')[:, 1].min(),
                               self.pos('RightToeBase')[:, 1].min()))

    def _cycles(self, mats, frames):
        h = mats[:frames, self.index['LeftFoot'], 1, 3]
        span = max(np.ptp(h), 1e-6)
        for c in (4, 3, 2):
            if frames % c:
                continue
            lag = frames // c
            if np.abs(h[:frames - lag] - h[lag:]).mean() < 0.06 * span:
                return c
        return 1

    def pos(self, name):
        return self.mats[:, self.index[name], :3, 3]

    def rot(self, name):
        return self.mats[:, self.index[name], :3, :3]

    def foot_contact(self, side, threshold=0.03):
        """Per key: is the foot on the floor (ankle or toe within threshold of its own lowest height)."""
        ankle = self.pos(f'{side}Foot')[:, 1]
        toe = self.pos(f'{side}ToeBase')[:, 1]
        return np.minimum(ankle - ankle.min(), toe - toe.min()) < threshold

    def stats(self):
        hips = self.pos('Hips')
        dt = 1.0 / self.fps
        speeds = []
        for side in ('Left', 'Right'):
            a = self.pos(f'{side}Foot') - hips
            fwd = a @ self.forward
            h = self.pos(f'{side}Foot')[:, 1]
            low = h <= h.min() + 0.12 * np.ptp(h)
            v = -np.diff(fwd) / dt
            mask = low[:-1] & low[1:]
            speeds.extend(v[mask])
        v = float(np.median(speeds))
        contact = np.array([self.foot_contact(s) for s in ('Left', 'Right')])
        flight = float((~contact[0] & ~contact[1])[:-1].mean())
        knee = 0.0
        for side in ('Left', 'Right'):
            t = self.pos(f'{side}Leg') - self.pos(f'{side}UpLeg')
            knee = max(knee, float(np.degrees(np.arctan2(t @ self.forward, -t[:, 1])).max()))
        return {'v': v, 'S': v * self.period, 'flight': flight, 'knee': knee,
                'hip_height': float(hips[:, 1].mean() - self.floor)}


def quat_from_matrices(m):
    """(K, 3, 3) -> (K, 4) xyzw, sign-continuous."""
    q = np.array([glb_pose.matrix_quaternion(r) for r in m])
    for i in range(1, len(q)):
        if np.dot(q[i], q[i - 1]) < 0:
            q[i] = -q[i]
    return q


def matrices_from_quat(q):
    q = q / np.linalg.norm(q, axis=-1, keepdims=True)
    return np.array([glb_pose.quaternion_matrix(v) for v in q])


def best_period(signal, frames):
    """Fractional loop period (in frames) of a signal by the minimum mean difference over lags, with a parabola."""
    span = max(np.ptp(signal), 1e-6)
    errors = {}
    for lag in range(max(4, frames // 5), frames + 1):
        if lag == frames:
            errors[lag] = 0.0
            continue
        errors[lag] = float(np.abs(signal[:frames + 1 - lag] - signal[lag:frames + 1]).mean() / span)
    lags = sorted(errors)
    # the first good minimum (a clip of several loops: its first loop)
    for lag in lags[1:-1]:
        if errors[lag] < 0.1 and errors[lag] <= errors[lag - 1] and errors[lag] <= errors[lag + 1]:
            a, b, c = errors[lag - 1], errors[lag], errors[lag + 1]
            shift = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) > 1e-9 else 0.0
            return lag + shift
    return float(frames)


class Cycle:
    """One loop of a library clip resampled at K phases (periodic cubic), seam-corrected (a loop's drift and any root
    travel removed), turned to face +Z. pos[name] (K, 3), rot[name] (K, 3, 3), phases k / K."""

    def __init__(self, path, samples, period_frames=None):
        from scipy.interpolate import CubicSpline
        data = np.load(path, allow_pickle=False)
        self.path = Path(path)
        names = [str(n) for n in data['names']]
        mats = data['mats']
        tails = data['toe_tails']
        fps = float(data['fps'])
        frames = len(mats) - 1
        if period_frames is None:
            period_frames = best_period(mats[:, names.index('LeftFoot'), 1, 3], frames)
        self.period = period_frames / fps
        P = period_frames
        m = int(np.floor(P - 1e-6))
        f_knots = np.append(np.arange(m + 1, dtype=float), P)
        phases = np.arange(samples) / samples
        # facing: the root travel of a root-motion clip, else against the planted feet's slide (in place)
        hips = mats[:m + 1, names.index('Hips'), :3, 3]
        travel = hips[-1] - hips[0]
        travel[1] = 0.0
        if np.linalg.norm(travel) > 0.2:
            f = unit(travel)
        else:
            slide = np.zeros(3)
            for side in ('Left', 'Right'):
                a = mats[:m + 1, names.index(f'{side}Foot'), :3, 3]
                low = a[:, 1] <= a[:, 1].min() + 0.12 * np.ptp(a[:, 1])
                step = a[1:] - a[:-1]
                slide += step[low[:-1] & low[1:]].sum(axis=0)
            slide[1] = 0.0
            f = unit(-slide)
        theta = np.arctan2(f[0], f[2])
        c, s_ = np.cos(-theta), np.sin(-theta)
        Y = np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])
        self.yaw_degrees = float(np.degrees(theta))

        def at(values, frame):
            i = int(np.floor(frame))
            t = frame - i
            if i >= frames:
                return values[frames]
            return values[i] * (1 - t) + values[i + 1] * t

        def periodic(values):
            """values (frames+1, ...) at integer frames -> (samples, ...) over [0, P) with the seam corrected."""
            knots = np.array([values[i] for i in range(m + 1)] + [at(values, P)])
            drift = knots[-1] - knots[0]
            knots = knots - drift[None] * (f_knots / P).reshape(-1, *([1] * (knots.ndim - 1)))
            knots[-1] = knots[0]
            spline = CubicSpline(f_knots, knots, axis=0, bc_type='periodic')
            return spline(phases * P)

        self.pos, self.rot = {}, {}
        for j, name in enumerate(names):
            p = mats[:, j, :3, 3] @ Y.T
            r = np.einsum('ab,kbc,dc->kad', Y, mats[:, j, :3, :3] / np.linalg.norm(mats[:, j, :3, :3], axis=1,
                                                                                    keepdims=True), Y)
            self.pos[name] = periodic(p)
            q = quat_from_matrices(r)
            self.rot[name] = matrices_from_quat(periodic(q))
        for k, side in enumerate(('Left', 'Right')):
            self.pos[f'{side}ToeEnd'] = periodic(tails[:, k] @ Y.T)
        rest = data['rest']
        self.rest_pos = {n: Y @ rest[j][:3, 3] for j, n in enumerate(names)}
        self.floor = float(min(self.pos[f'{s}{p}'][:, 1].min() for s in ('Left', 'Right')
                               for p in ('ToeBase', 'ToeEnd', 'Foot')))
        hip, knee, ankle = (self.rest_pos['LeftUpLeg'], self.rest_pos['LeftLeg'], self.rest_pos['LeftFoot'])
        self.leg_length = float(np.linalg.norm(knee - hip) + np.linalg.norm(ankle - knee))
        self.samples = samples

    def contact(self, side, threshold=0.03):
        ankle = self.pos[f'{side}Foot'][:, 1]
        toe = self.pos[f'{side}ToeBase'][:, 1]
        return np.minimum(ankle - ankle.min(), toe - toe.min()) < threshold


class Body:
    """One installed GLB: joints, rest, Standing posture."""

    def __init__(self, name, path=None):
        self.name = name
        self.glb = glb_pose.Glb(path or MODELS[name])
        self.model = glb_pose.Model(self.glb)
        self.nodes = self.glb.json['nodes']
        self.index = {n['name']: i for i, n in enumerate(self.nodes)}
        world = self.model.world(self.model.sample('Standing', 0.0))
        p = lambda n: world[self.index[n], :3, 3]
        self.leg_length = float(np.linalg.norm(p('B_L_Calf') - p('B_L_Thigh'))
                                + np.linalg.norm(p('B_L_Foot') - p('B_L_Calf')))
        self.standing_hip_height = float(p('B_Pelvis')[1])
