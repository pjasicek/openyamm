#!/usr/bin/env python3
"""Bake the pole set into a first-person arms GLB (README.md, devdocs/solo_action/WEAPONS.md "Pole set").

    bake_pole_clips.py <in.glb> <in.textkeys.json> <out.glb> <out.textkeys.json>

Oblivion has no spear or halberd, and its two-handed clips hold a pole upright with its head above the frame, so the
pole set's clips are authored here as keyframes of the pole's place relative to the eye (Camera01), and both arms are
solved onto it, as the crossbow set's are: the right fist on the Weapon node (the pole templates, w_spear, w_trident
and w_halberd, are built in that node's space: the palm at the origin, the head along +Y), the left fist further up
the shaft (its Torch frame on the shaft, the thumb toward the head). Each arm is the crossbow bake's two-bone solve.
The body (spine, neck, Camera01, clavicles) comes from the two-handed clips, the chest turned the left shoulder
forward as a spearman stands.

Clips: poleidle (low at the right hip, the head up and right of the crosshair, breathing), poleforward ...
polefastright (the two-handed walks and runs, the pole carried by their motion), poleequip, poleunequip; the combo:
poleattackright (a jab along the view), poleattackleft (a second, higher jab), poleattackright_chop (a horizontal
sweep from right to left), poleattackleft_chop (an overhead chop, the halberd's axe blade leading); the power attacks:
poleattackpower and poleattackforwardpower (a lunge thrust), poleattackbackpower (a big overhead chop),
poleattackleftpower and poleattackrightpower (big sweeps to that side); poleblockidle and poleblockhit (the shaft
raised across), polecastself and polecasttarget (the left hand casts as in Oblivion's one-handed casts, the right holds
the pole low). The attacks keep the two-handed clips' Hit and chain keys (a:L, a:R), so the engine fits them to the
recovery exactly as it fitted the two-handed swings: the same cadence, the blow at the contact frame.

The input must not hold pole clips: bake from the crossbow output (rebake_arms.sh runs dual, crossbow and pole from
the pristine arms). Every existing clip, mesh, skin and texture is copied byte for byte. numpy only.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'dual_wield_20261114', 'scripts'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'crossbow_set_20261114', 'scripts'))
from bake_dual_clips import Arms, Writer, load_glb, save_glb  # noqa: E402
from bake_crossbow_clips import Rig, ease, rot_x, rot_y, rot_z, sway  # noqa: E402

FPS = 30.0
# The swings move the head fast: baked at twice the rate, so the left fist stays on the shaft between frames too
# (the engine interpolates each bone on its own, which opens the two-handed loop a little in fast motion).
ATTACK_FPS = 60.0
PREFIX = 'pole'
# The pole's frame (the Weapon node's: edge +X, head +Y, flat +Z) in the eye's axes (forward -Z, up +Y, right +X) at
# no yaw, pitch or roll: the head forward, the edge (+X: a halberd's beak, -X its axe blade) up, the flat toward the
# left. So the right fist holds the shaft with the axe blade down, and a chop (the head pitched down from overhead)
# leads with the blade.
BASE = np.array([[0.0, 0.0, -1.0], [1.0, 0.0, 0.0], [0.0, -1.0, 0.0]])
# The pole templates (assets_source/engine/view_model/w_<kind>.glb, Weapon node space): the tip and where the head
# begins along +Y, and the butt; for the gates.
HEADS = {'spear': (60.0, 88.0, -30.0), 'trident': (48.0, 96.0, -22.0), 'halberd': (36.0, 98.0, -22.0)}


class Pose:
    """The pole relative to the eye: the right palm (the Weapon node's origin) at pos, the shaft turned by yaw
    (positive: the head left), pitch (positive: the head up) and roll (about the shaft), in degrees; the left fist
    `reach` units up the shaft from the right palm, turned `grip` degrees about it whatever the roll (the shaft turns
    in it); twist: the upper body turned
    (degrees, positive: the left shoulder forward); the elbows toward their poles (directions in the eye's axes)."""

    SCALARS = ('yaw', 'pitch', 'roll', 'reach', 'grip', 'twist')

    def __init__(self, pos, yaw=0.0, pitch=0.0, roll=0.0, reach=22.0, grip=0.0, twist=0.0, pole_r=(0.8, -1.0, 0.4),
                 pole_l=(-0.6, -1.0, 0.2)):
        self.pos = np.array(pos, float)
        self.yaw, self.pitch, self.roll = yaw, pitch, roll
        self.reach, self.grip, self.twist = reach, grip, twist
        self.pole_r, self.pole_l = np.array(pole_r, float), np.array(pole_l, float)

    def values(self):
        return np.concatenate([self.pos, [getattr(self, k) for k in Pose.SCALARS], self.pole_r, self.pole_l])

    @staticmethod
    def of(values):
        n = len(Pose.SCALARS)
        return Pose(values[0:3], *values[3:3 + n], pole_r=values[3 + n:6 + n], pole_l=values[6 + n:9 + n])

    def moved(self, **change):
        out = Pose.of(self.values())
        for key, value in change.items():
            if key in ('dx', 'dy', 'dz'):
                out.pos['xyz'.index(key[1])] += value
            elif key in ('pole_r', 'pole_l'):
                setattr(out, key, np.array(value, float))
            else:
                setattr(out, key, getattr(out, key) + value)
        return out

    def at(self, pos=None, **values):
        """A copy with absolute values (pos, yaw, pitch ...)."""
        out = Pose.of(self.values())
        if pos is not None:
            out.pos = np.array(pos, float)
        for key, value in values.items():
            setattr(out, key, np.array(value, float) if key.startswith('pole') else value)
        return out

    def matrix(self):
        m = np.eye(4)
        m[:3, :3] = rot_y(self.yaw) @ rot_x(self.pitch) @ rot_z(self.roll) @ BASE
        m[:3, 3] = self.pos
        return m


def track(keys, t):
    """keys: [(time, Pose, easing into it)]: the pose at t, eased per segment."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, p0, _), (t1, p1, kind) in zip(keys, keys[1:]):
        if t <= t1:
            f = ease(kind, (t - t0) / max(t1 - t0, 1e-9))
            return Pose.of(p0.values() + (p1.values() - p0.values()) * f)
    return keys[-1][1]


# The poses, tuned against preview.py and in-game captures (README.md). Rolls: 0 turns the edge (+X: the halberd's
# beak) up and its axe blade (-X) down, so a chop leads with the blade; 270 (-90) and 90 lead a sweep to the left and
# to the right with it; 125, the carry, turns the head's flat half toward the eye with the axe blade up and right.
ROLL_CHOP, ROLL_LEFT, ROLL_RIGHT = 0.0, 270.0, 90.0
IDLE = Pose((13.0, -23.0, 0.0), yaw=-3.0, pitch=27.0, roll=125.0, reach=22.0, grip=55.0, twist=22.0)
# Below the view, the head pitched down: the equip swings it up into the idle as the left fist closes on the shaft.
LOWERED = IDLE.moved(dx=-4.0, dy=-8.0, dz=-4.0, pitch=-70.0, reach=-12.0)
# One hand on the pole while the left casts: lower on the right, the head still up and right of the crosshair.
CARRY = IDLE.moved(dx=3.0, dy=-4.0, dz=-1.0, pitch=-16.0, yaw=-10.0)
# The shaft raised across the face, the head to the left, both fists on it.
BLOCK = Pose((13.0, -3.5, -21.0), yaw=80.0, pitch=6.0, roll=ROLL_LEFT, reach=26.0, grip=-40.0, twist=8.0,
             pole_r=(1.0, -0.8, 0.2), pole_l=(-0.8, -1.0, 0.0))


def toward(pos, depth):
    """The yaw and pitch that point the shaft from a right palm at pos to the crosshair's line at the given depth
    (the tip's: 88 units up the shaft for the spear, 96-98 for the others)."""
    d = np.array([0.0, 0.0, -depth]) - np.array(pos, float)
    d /= np.linalg.norm(d)
    return math.degrees(math.atan2(-d[0], -d[2])), math.degrees(math.asin(d[1]))


def thrust(pos, reach, twist, lift=0.0):
    """The pole from a right palm at pos with the point on the crosshair (lift: above it, in units at the tip)."""
    yaw, pitch = toward(np.array(pos) - (0.0, lift, 0.0), math.sqrt(88.0 ** 2 - pos[0] ** 2 - pos[1] ** 2) - pos[2])
    return IDLE.at(pos, yaw=yaw, pitch=pitch, reach=reach, twist=twist, pole_r=(0.8, -1.0, 0.0))


def jab_keys(hit, chain, duration, high=False):
    """A jab along the view: drawn back a little, driven forward so the point meets the crosshair at the Hit (the
    shaft sliding through the left fist toward the right), held a moment, back to the idle."""
    back = IDLE.moved(dz=4.0, dy=-1.0, pitch=2.0)
    out = thrust((8.0, -17.0, -15.0), 15.0, 8.0, lift=6.0 if high else 0.0)
    first = min(0.12, hit * 0.4)
    return [
        (0.0, IDLE, 'smooth'),
        (first, back, 'smooth'),
        (hit, out, 'out'),
        (chain, out.moved(dz=1.5), 'smooth'),
        (duration - 0.08, IDLE, 'smooth'),
        (duration, IDLE, 'smooth'),
    ]


def sweep_keys(hit, chain, duration, power=False, to_right=False):
    """A sweep across the view: the head wound out to one side, swept through the crosshair at the Hit, carried
    through to the other side, back to the idle. The edge leads (the halberd's axe blade faces the way it travels)."""
    side = -1.0 if to_right else 1.0
    wide = 1.3 if power else 1.0
    roll = ROLL_RIGHT if to_right else ROLL_LEFT
    # The fists move to the side away from the head, so the left arm reaches the shaft wherever it points.
    wound = IDLE.at((8.0 - 3.0 * side, -15.0, -8.0), yaw=-side * 42.0 * wide, pitch=12.0, roll=roll,
                    reach=11.0 if side > 0 else 16.0, twist=22.0 + side * 10.0)
    through = IDLE.at((7.0, -15.0, -14.0), yaw=4.0, pitch=8.0, roll=roll, reach=13.0, twist=10.0)
    follow = IDLE.at((1.0, -15.0, -11.0), yaw=side * 38.0 * wide, pitch=5.0, roll=roll,
                     reach=18.0 if side > 0 else 10.0, twist=10.0 - side * 10.0)
    windup = hit * (0.55 if power else 0.45)
    return [
        (0.0, IDLE, 'smooth'),
        (windup, wound, 'smooth'),
        (hit, through, 'linear'),
        (min(hit + (0.2 if power else 0.12), chain), follow, 'out'),
        (duration - 0.1, IDLE, 'smooth'),
        (duration, IDLE, 'smooth'),
    ]


def chop_keys(hit, chain, duration, power=False):
    """An overhead chop: the head raised high, brought down through the crosshair at the Hit (the halberd's axe blade
    leading), carried a little below, back to the idle."""
    # Raised up and to the right (a diagonal chop), so the left forearm stays at the bottom of the view.
    raised = IDLE.at((16.0, -17.0, -2.0), yaw=-18.0 + (4.0 if power else 0.0), pitch=52.0 + (4.0 if power else 0.0),
                     roll=ROLL_CHOP, reach=14.0, twist=24.0 + (6.0 if power else 0.0), pole_r=(0.9, -0.8, 0.3))
    struck = IDLE.at((7.0, -15.0, -15.0), yaw=4.0, pitch=8.0, roll=ROLL_CHOP, reach=13.0, twist=10.0)
    below = IDLE.at((7.0, -17.0, -13.0), yaw=4.0, pitch=-4.0 - (6.0 if power else 0.0), roll=ROLL_CHOP, reach=11.0,
                    twist=10.0)
    windup = hit * (0.6 if power else 0.5)
    return [
        (0.0, IDLE, 'smooth'),
        (windup, raised, 'smooth'),
        (hit, struck, 'in'),
        (min(hit + 0.1, chain), below, 'out'),
        (duration - 0.1, IDLE, 'smooth'),
        (duration, IDLE, 'smooth'),
    ]


def lunge_keys(hit, duration, forward=False):
    """The power thrust: drawn far back (the head close), then driven out with the whole body (the right shoulder
    forward) until the point is on the crosshair at the Hit, held, recovered."""
    drawn = IDLE.moved(dx=2.0, dy=1.0, dz=7.0, pitch=-4.0, yaw=-4.0, reach=2.0, twist=8.0)
    out = thrust((7.0, -15.0, -20.0 - (1.0 if forward else 0.0)), 8.0 if forward else 9.0, 0.0, lift=-4.0 if forward else 0.0)
    return [
        (0.0, IDLE, 'smooth'),
        (hit * 0.62, drawn, 'smooth'),
        (hit, out, 'in'),
        (hit + 0.18, out.moved(dz=1.0), 'smooth'),
        (duration - 0.15, IDLE, 'smooth'),
        (duration, IDLE, 'smooth'),
    ]


class PoleRig(Rig):
    """The crossbow bake's rig (arm solve, body twist) with the pole's hand targets."""

    def __init__(self, arms):
        self.arms = arms
        index = arms.index
        self.weapon_local = self.rest_local('Weapon')
        self.torch_local = self.rest_local('Torch')
        self.side = {}
        for s in 'RL':
            nodes = {k: index[f'Bip01 {s} {k}'] for k in ('Clavicle', 'UpperArm', 'UpperArmTwist', 'Forearm',
                                                          'ForearmTwist', 'Hand')}
            nodes['upper'] = float(np.linalg.norm(arms.rest_t[nodes['Forearm']]))
            nodes['lower'] = float(np.linalg.norm(arms.rest_t[nodes['Hand']]))
            nodes['fingers'] = [i for i in arms.subtree(f'Bip01 {s} Hand') if 'Finger' in arms.nodes[i].get('name', '')]
            self.side[s] = nodes
        self.camera = index['Camera01']
        self.spine = index['Bip01 Spine2']
        # Grips: the right fingers as they close on a one-handed hilt, the left as they close on the bow's riser.
        self.grip = {'R': arms.local('onehandidle', 0.0), 'L': arms.local('bowattack', 1.37)}

    def hand_targets(self, eye, pose):
        """World matrices of both hands: the right from the pole on its Weapon node, the left with its Torch frame on
        the shaft `reach` units up it, the frame's +Y (through the fist, the thumb's side) along the shaft."""
        weapon = np.eye(4)
        weapon[:3, 3] = eye
        weapon = weapon @ pose.matrix()
        right = weapon @ np.linalg.inv(self.weapon_local)
        on_shaft = np.eye(4)
        on_shaft[:3, :3] = rot_y(pose.grip + pose.roll) @ LEFT_GRIP
        on_shaft[:3, 3] = (0.0, pose.reach, 0.0)
        left = weapon @ on_shaft @ np.linalg.inv(self.torch_local)
        return right, left


# The left fist's Torch frame in the pole's frame at grip 0: +Y along the shaft (toward the head), +Z (the bow hold's
# palm side, toward the body) to the pole's +Z, which BASE turns to the eye's left: the palm faces in, under the shaft.
LEFT_GRIP = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])


def relative_weapon(arms, clip, t):
    w = arms.world(arms.local(clip, t))
    m = w[arms.index['Weapon']].copy()
    m[:3, 3] -= w[arms.index['Camera01']][:3, 3]
    m[:3, :3] /= np.linalg.norm(m[:3, :3], axis=0)
    return m


def plan(arms, textkeys):
    """(name, duration, keys, body clip, pose at t, left arm source)."""
    clips = []

    def keys_of(clip):
        return [[t, k] for t, k in textkeys[clip]['keys'] if k.strip().lower() not in ('start', 'end')]

    def attack_keys(clip):
        """The two-handed swing's Hit and chain keys (the cadence the engine fits to the recovery)."""
        return [[t, k] for t, k in textkeys[clip]['keys'] if k.strip().lower() in ('hit', 'a:l', 'a:r')]

    def key_time(clip, name):
        return next(t for t, k in textkeys[clip]['keys'] if k.strip().lower() == name)

    clips.append(('idle', 3.0, [], 'twohandidle', lambda t: IDLE.moved(**sway(t, 3.0)), None))
    # Walk and run: the pole carried by the two-handed walk's motion of the weapon relative to the eye.
    rest = relative_weapon(arms, 'twohandidle', 0.0)
    for move in ('forward', 'backward', 'left', 'right', 'fastforward', 'fastbackward', 'fastleft', 'fastright'):
        source = 'twohand' + move

        def walking(t, source=source):
            delta = relative_weapon(arms, source, t) @ np.linalg.inv(rest)
            out = Pose.of(IDLE.values())
            # The two-handed walk swings a sword held upright; only half its sway, so the long pole does not wag.
            out.pos = IDLE.pos + 0.6 * ((delta @ np.append(IDLE.pos, 1.0))[:3] - IDLE.pos)
            turn = delta[:3, :3]
            out.yaw += 0.5 * math.degrees(math.atan2(turn[0, 2], turn[2, 2]))
            out.pitch += 0.5 * math.degrees(math.asin(max(min(turn[2, 1], 1.0), -1.0)))
            return out
        clips.append((move, arms.duration(source), keys_of(source), source, walking, None))
    clips.append(('equip', 0.8, [[0.1, 'Attach']], 'twohandidle',
                  lambda t: track([(0.0, LOWERED, 'smooth'), (0.7, IDLE, 'out')], t), None))
    clips.append(('unequip', 0.667, [[0.5, 'Detach']], 'twohandidle',
                  lambda t: track([(0.0, IDLE, 'smooth'), (0.6, LOWERED, 'in')], t), None))

    # The combo: two jabs, the sweep, the chop, each on its two-handed swing's keys.
    def chained(action, make, duration, **extra):
        source = 'twohand' + action
        hit = key_time(source, 'hit')
        chain = next(t for t, k in textkeys[source]['keys'] if k.strip().lower() in ('a:l', 'a:r'))
        keys = make(hit, chain, duration, **extra)
        clips.append((action, duration, attack_keys(source), 'twohandidle', lambda t: track(keys, t), None))

    chained('attackright', jab_keys, 0.867)
    chained('attackleft', jab_keys, 0.833, high=True)
    chained('attackright_chop', sweep_keys, 0.9)
    chained('attackleft_chop', chop_keys, 0.933)

    # The power attacks: the lunge (standing and moving forward), the big chop (moving back), the big sweeps.
    def power(action, keys_for, duration):
        source = 'twohand' + action
        hit = key_time(source, 'hit')
        keys = keys_for(hit, duration)
        clips.append((action, duration, attack_keys(source), 'twohandidle', lambda t: track(keys, t), None))

    power('attackpower', lambda hit, d: lunge_keys(hit, d), 1.6)
    power('attackforwardpower', lambda hit, d: lunge_keys(hit, d, forward=True), 1.567)
    power('attackbackpower', lambda hit, d: chop_keys(hit, hit + 0.2, d, power=True), 1.5)
    power('attackleftpower', lambda hit, d: sweep_keys(hit, hit + 0.3, d, power=True), 1.433)
    power('attackrightpower', lambda hit, d: sweep_keys(hit, hit + 0.3, d, power=True, to_right=True), 1.7)

    # Block: the shaft raised across the face; a hit jolts it toward the eye.
    clips.append(('blockidle', 1.3, [], 'twohandidle', lambda t: BLOCK.moved(**sway(t, 1.3, 0.6)), None))
    clips.append(('blockhit', 0.3, [[0.0333, 'Blend: 0']], 'twohandidle',
                  lambda t: track([(0.0, BLOCK, 'smooth'), (0.08, BLOCK.moved(dz=3.0, dy=1.5, pitch=4.0), 'out'),
                                   (0.3, BLOCK, 'smooth')], t), None))
    # Casts: the left hand casts (Oblivion's one-handed casts), the right holds the pole low.
    for cast in ('castself', 'casttarget'):
        source = 'onehand' + cast
        clips.append((cast, arms.duration(source), keys_of(source), source,
                      lambda t: CARRY.moved(**sway(t, 3.0, 0.5)), source))
    return clips


def bake_clip(rig, body_clip, duration, pose_at, left_from, fps):
    """As the crossbow bake's bake_clip, at a given frame rate."""
    arms = rig.arms
    frames = int(math.ceil(duration * fps - 1e-6))
    times = np.array([min(k / fps, duration) for k in range(frames + 1)])
    count = len(arms.nodes)
    out_t = np.zeros((len(times), count, 3))
    out_q = np.zeros((len(times), count, 4))
    out_s = np.zeros((len(times), count, 3))
    worst = {'R': (0.0, 0.0), 'L': (0.0, 0.0)}
    body_duration = arms.duration(body_clip)
    for f, t in enumerate(times):
        body = arms.local(body_clip, t % body_duration if body_duration < duration else min(t, body_duration))
        source = arms.local(left_from, min(t, arms.duration(left_from))) if left_from else None
        pose, misses = rig.solve(body, pose_at(t), source)
        for s in 'RL':
            worst[s] = max(worst[s], (misses[s], float(t)))
        out_t[f], out_q[f], out_s[f] = pose[0], pose[1], pose[2]
    for f in range(1, len(times)):
        flip = np.sum(out_q[f] * out_q[f - 1], axis=1) < 0
        out_q[f][flip] *= -1
    return times, out_t, out_q, out_s, worst


def segment_distance(p, q, x):
    d = q - p
    s = np.clip((x - p) @ d / (d @ d), 0.0, 1.0)
    return float(np.linalg.norm(p + d * s - x))


def gates(arms, name, duration):
    """Per clip: the worst distance of the left fist (its Torch frame's origin) from the shaft's axis (the right fist holds
    the pole on its Weapon node, so it cannot leave it), the
    closest approach of the shaft (butt to tip) and of the forearms to the eye, and, for the idle, the head's place on
    screen (normalised device coordinates, 60 degree vertical field, 16:9) for each template."""
    idx = arms.index
    tan = math.tan(math.radians(30.0))
    worst = {'L': 0.0, 'eye': 1e9, 'head': [9.0, -9.0, 9.0, -9.0]}
    # Four samples per baked frame: the engine plays the clips between their frames too.
    for t in np.linspace(0.0, duration, max(int(duration * 120.0), 2)):
        w = arms.world(arms.local(name, t))
        eye = w[idx['Camera01']][:3, 3]
        weapon = w[idx['Weapon']]
        axis = weapon[:3, :3] / np.linalg.norm(weapon[:3, :3], axis=0)
        origin = weapon[:3, 3]
        p, q = origin + axis[:, 1] * -30.0, origin + axis[:, 1] * 98.0
        torch = w[idx['Torch']][:3, 3]
        worst['L'] = max(worst['L'], segment_distance(p, q, torch))
        closest = segment_distance(p, q, eye)
        for s in 'RL':
            closest = min(closest, segment_distance(w[idx[f'Bip01 {s} Forearm']][:3, 3], w[idx[f'Bip01 {s} Hand']][:3, 3],
                                                    eye))
        worst['eye'] = min(worst['eye'], closest)
        if name.endswith('idle') and not name.endswith('blockidle'):
            for start, tip, _ in HEADS.values():
                for along in (start, tip):
                    x, y, z = origin + axis[:, 1] * along - eye
                    sx, sy = x / -z / (tan * 16.0 / 9.0), y / -z / tan
                    h = worst['head']
                    h[0], h[1], h[2], h[3] = min(h[0], sx), max(h[1], sx), min(h[2], sy), max(h[3], sy)
    return worst


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    in_glb, in_keys, out_glb, out_keys = sys.argv[1:]
    j, blob = load_glb(in_glb)
    textkeys = json.load(open(in_keys))
    if any(a['name'].startswith(PREFIX) for a in j.get('animations', [])):
        print(f'{in_glb} already holds pole clips: bake from the crossbow output (rebake_arms.sh)')
        return 1
    arms = Arms(j, blob)
    rig = PoleRig(arms)
    writer = Writer(j, blob)
    baked = []
    for action, duration, keys, body, pose_at, left_from in plan(arms, textkeys):
        name = PREFIX + action
        fps = ATTACK_FPS if action.startswith('attack') else FPS
        times, out_t, out_q, out_s, worst = bake_clip(rig, body, duration, pose_at, left_from, fps)
        writer.animation(name, arms, times, out_t, out_q, out_s)
        textkeys[name] = {'length': float(duration),
                          'keys': [[0.0, 'start']] + [[float(t), k] for t, k in keys] + [[float(duration), 'end']]}
        baked.append((name, duration, len(times), worst, keys))
    save_glb(out_glb, j, writer.blob)
    with open(out_keys, 'w') as stream:
        json.dump(textkeys, stream, indent=1)
    # The gates, measured on the written clips.
    out = Arms(*load_glb(out_glb))
    for name, duration, frames, worst, keys in baked:
        g = gates(out, name, duration)
        head = (' head x %.2f..%.2f y %.2f..%.2f' % tuple(g['head'])) if g['head'][0] < 9.0 else ''
        print(f'{name}: {duration:.3f} s, {frames} frames, wrist miss R {worst["R"][0]:.2f} at {worst["R"][1]:.2f} s'
              f' L {worst["L"][0]:.2f} at {worst["L"][1]:.2f} s, left fist off the shaft {g["L"]:.2f}, eye clearance'
              f' {g["eye"]:.1f}{head}, keys {keys}')
    print(f'wrote {out_glb} ({len(j["animations"])} clips) and {out_keys}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
