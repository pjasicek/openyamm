#!/usr/bin/env python3
"""Bake the crossbow set into a first-person arms GLB (README.md, devdocs/solo_action/WEAPONS.md "Crossbow set").

    bake_crossbow_clips.py <in.glb> <in.textkeys.json> <out.glb> <out.textkeys.json>

Oblivion has no crossbow, so its clips are authored here as keyframes of the crossbow's place relative to the eye
(Camera01), and both arms are solved onto it: the right hand on the stock's wrist (the crossbow hangs on the right
hand's Weapon node, placed there by the view model weapons project's kinds.py `mount`), the left on the foregrip under
the fore-end (where the left fist closes in the Torch frame the crossbow was built in) or, while spanning, on the
cord. Each arm is a two-bone solve (upper arm and forearm, the elbow toward a pole) under the body's clavicle, the hand
turned onto its target, the forearm twist bone sharing the hand's twist as in Oblivion's clips, the fingers gripping
as in a one-handed (right) and a bow's (left) hold. The body (spine, neck, Camera01, clavicles) comes from a bow clip,
so the eye moves as the bow set's does; the chest turns the left shoulder forward as a shooter stands.

Clips (the bow set's coverage, plus the casts the set needs because the crossbow fills the right hand):
crossbowidle (breathing sway), crossbowforward ... crossbowfastright (the bow's walk and run, the crossbow carried by
the bow's motion), crossbowequip, crossbowunequip, crossbowattack (raise to the cheek, Release, a short sharp recoil,
then the reload: nose down, the left hand spans the cord from the prod back to the nut, back to the idle; a:R where
the next shot may start, at the bow shot's Release: the same cadence), crossbowblockidle, crossbowblockhit,
crossbowcastself and crossbowcasttarget (the left hand casts as in Oblivion's one-handed casts, the right holds the
crossbow low).

The input must not hold crossbow clips: bake from the dual-wield output (rebake_arms.sh runs both from the pristine
arms). Every existing clip, mesh, skin and texture is copied byte for byte. numpy only.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'dual_wield_20261114', 'scripts'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'view_model_weapons_20261114', 'scripts'))
from bake_dual_clips import Arms, Writer, compose, decompose, load_glb, matrix_quat, quat_matrix, save_glb  # noqa: E402
from kinds import KINDS, weapon_from_build  # noqa: E402

FPS = 30.0
PREFIX = 'crossbow'
# The crossbow's build frame (bolt +X, up +Y, right +Z) in the eye's axes (forward -Z, up +Y, right +X).
BASE = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
# The next shot may start when the span is done (a:R), at the bow shot's Release (bowattack 1.433 s): the engine fits
# both clips to the recovery by the same span and starts the next bow shot at its Release, so a crossbow keeps the
# bow's cadence at any recovery. The bolt leaves at RELEASE, after a quick raise to the cheek.
SHOT_SPAN = 1.433
RELEASE = 0.4


def rot_x(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def rot_y(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def rot_z(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def ease(kind, x):
    x = min(max(x, 0.0), 1.0)
    if kind == 'linear':
        return x
    if kind == 'out':
        return 1 - (1 - x) ** 3
    if kind == 'in':
        return x ** 3
    return x * x * (3 - 2 * x)


# The stock's wrist, where the right fist closes (kinds.py mount `grip`, Blender build coordinates), in glTF build
# coordinates: the pivot of every pose.
GRIP = np.array([KINDS['crossbow']['mount']['grip'][0], KINDS['crossbow']['mount']['grip'][2],
                 -KINDS['crossbow']['mount']['grip'][1]])


class Pose:
    """The crossbow relative to the eye: the stock's wrist (GRIP, in the right fist) at pos, turned by yaw
    (positive: the nose left), pitch (positive: nose up) and roll (positive: the top to the left), in degrees; the
    elbows toward their poles (directions in the eye's axes); left: 0 on the foregrip, 1 on the cord at cord_x (build
    X) with the fist above the stock; twist: the upper body turned (degrees, positive: the left shoulder forward, as
    a shooter stands), which the eye does not follow."""

    SCALARS = ('yaw', 'pitch', 'roll', 'left', 'cord_x', 'twist')

    def __init__(self, pos, yaw=0.0, pitch=0.0, roll=0.0, left=0.0, cord_x=12.0, twist=0.0, pole_r=(0.7, -1.0, 0.3),
                 pole_l=(-0.6, -1.0, 0.1)):
        self.pos = np.array(pos, float)
        self.yaw, self.pitch, self.roll = yaw, pitch, roll
        self.left, self.cord_x, self.twist = left, cord_x, twist
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
            elif key in ('left', 'cord_x'):
                setattr(out, key, value)
            else:
                setattr(out, key, getattr(out, key) + value)
        return out

    def matrix(self):
        m = np.eye(4)
        m[:3, :3] = rot_y(self.yaw) @ rot_x(self.pitch) @ rot_z(self.roll) @ BASE
        m[:3, 3] = self.pos - m[:3, :3] @ GRIP
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


# The poses, tuned against preview.py and in-game captures (README.md).
IDLE = Pose((10.0, -8.0, -19.5), yaw=-5.0, pitch=-7.0, roll=-8.0, twist=18.0)
AIM = Pose((3.5, -8.5, -13.5), yaw=3.0, pitch=3.0, roll=0.0, twist=25.0, pole_r=(1.0, -0.6, 0.2),
           pole_l=(-0.4, -1.0, 0.0))
LOWERED = IDLE.moved(dy=-15.0, dz=5.0, pitch=-40.0)
BLOCK = Pose((12.0, -8.0, -22.0), yaw=70.0, pitch=4.0, roll=-6.0, twist=10.0, pole_r=(1.0, -0.8, 0.0),
             pole_l=(-0.8, -1.0, 0.0))
SPAN = Pose((9.0, -11.5, -19.0), yaw=35.0, pitch=-15.0, roll=35.0, twist=24.0)
# One hand on the crossbow while the left casts: low on the right, the nose forward and down.
CARRY = Pose((13.0, -12.0, -15.0), yaw=12.0, pitch=-12.0, roll=-15.0)


def attack_keys():
    recoil = AIM.moved(pitch=7.0, dz=3.0, dy=0.8)
    return [
        (0.0, IDLE, 'smooth'),
        (0.25, AIM, 'smooth'),
        (RELEASE, AIM.moved(dy=-0.2), 'smooth'),
        # The recoil: a short sharp kick, the nose up and the stock back into the shoulder, then settling.
        (RELEASE + 0.06, recoil, 'out'),
        (RELEASE + 0.22, AIM.moved(dy=-0.8, pitch=-1.0), 'smooth'),
        # The span: the nose down and across, the left hand from the fore-end onto the cord at the prod, drawing it
        # back to the nut, back to the fore-end, and up into the idle by SHOT_SPAN.
        (0.8, SPAN, 'smooth'),
        (0.88, SPAN.moved(left=1.0, cord_x=5.5), 'smooth'),
        (1.08, SPAN.moved(left=1.0, cord_x=-5.0, pitch=2.0, dz=-1.0), 'smooth'),
        (1.2, SPAN.moved(left=0.0), 'smooth'),
        (SHOT_SPAN, IDLE, 'smooth'),
        (1.55, IDLE, 'smooth'),
    ]


class Rig:
    def __init__(self, arms):
        self.arms = arms
        index = arms.index
        mount = KINDS['crossbow']['mount']
        # The crossbow's build frame in the Weapon node's frame, and the Weapon and Torch nodes on their hands.
        self.weapon_from_build = weapon_from_build(mount)
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

    def rest_local(self, name):
        i = self.arms.index[name]
        return compose(self.arms.rest_t[i], self.arms.rest_q[i], self.arms.rest_s[i])

    def hand_targets(self, eye, pose):
        """World matrices of both hands for a pose: the right from the crossbow on its Weapon node, the left on the
        foregrip (the Torch frame the crossbow was built in) or on the cord."""
        build = np.eye(4)
        build[:3, 3] = eye
        build = build @ pose.matrix()
        weapon = build @ np.linalg.inv(self.weapon_from_build)
        right = weapon @ np.linalg.inv(self.weapon_local)
        fore = build @ np.linalg.inv(self.torch_local)
        # On the cord: the fist above the bolt groove, its grip axis across the stock, the knuckles forward and down.
        cord = np.eye(4)
        cord[:3, :3] = rot_z(-35.0) @ np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])
        cord[:3, 3] = (pose.cord_x, 8.2, 0.0)
        hooked = build @ cord @ np.linalg.inv(self.torch_local)
        left = blend_matrix(fore, hooked, pose.left)
        return right, left

    def solve(self, body, pose, left_from=None):
        """Locals of every node: the body's, both arms solved onto the pose (the left arm from left_from's locals
        instead, when given). Returns the locals and each wrist's miss in units."""
        arms = self.arms
        out = [body[0].copy(), body[1].copy(), body[2].copy()]
        world = arms.world(body)
        eye = world[self.camera][:3, 3]
        if abs(pose.twist) > 1e-6:
            # The chest (Spine2, carrying the neck and clavicles) turned about the vertical through it.
            spine = self.spine
            turned = world[spine].copy()
            turned[:3, :3] = rot_y(-pose.twist) @ turned[:3, :3]
            local = np.linalg.inv(world[arms.parent[spine]]) @ turned
            out[0][spine], out[1][spine], out[2][spine] = decompose(local)
            world = arms.world(out)
        right, left = self.hand_targets(eye, pose)
        misses = {}
        for s, target, pole in (('R', right, pose.pole_r), ('L', left, pose.pole_l)):
            if s == 'L' and left_from is not None:
                for i in arms.subtree('Bip01 L Clavicle'):
                    out[0][i], out[1][i], out[2][i] = left_from[0][i], left_from[1][i], left_from[2][i]
                misses[s] = 0.0
                continue
            misses[s] = self.solve_arm(out, world, s, target, pole)
        return out, misses

    def solve_arm(self, out, world, s, target, pole):
        arms = self.arms
        n = self.side[s]
        grip = self.grip[s]
        for i in n['fingers'] + [n['UpperArmTwist']]:
            out[0][i], out[1][i], out[2][i] = grip[0][i], grip[1][i], grip[2][i]
        clavicle = world[arms.parent[n['Clavicle']]] @ compose(out[0][n['Clavicle']], out[1][n['Clavicle']],
                                                               out[2][n['Clavicle']])
        clavicle_rotation = clavicle[:3, :3] / np.linalg.norm(clavicle[:3, :3], axis=0)
        shoulder = (clavicle @ np.append(out[0][n['UpperArm']], 1.0))[:3]
        wrist = target[:3, 3]
        upper, lower = n['upper'], n['lower']
        reach = wrist - shoulder
        distance = float(np.linalg.norm(reach))
        d = min(max(distance, abs(upper - lower) + 1e-3), upper + lower - 1e-3)
        bend = -math.acos(min(max((d * d - upper * upper - lower * lower) / (2 * upper * lower), -1.0), 1.0))
        forearm_local = rot_z(math.degrees(bend))
        wrist_local = np.array([upper, 0.0, 0.0]) + forearm_local @ np.array([lower, 0.0, 0.0])
        a = wrist_local / np.linalg.norm(wrist_local)
        b = np.array([1.0, 0.0, 0.0]) - a * a[0]
        b /= np.linalg.norm(b)
        a2 = reach / distance
        b2 = pole - a2 * (pole @ a2)
        b2 /= np.linalg.norm(b2)
        upper_world = np.column_stack([a2, b2, np.cross(a2, b2)]) @ np.column_stack([a, b, np.cross(a, b)]).T
        upper_local = clavicle_rotation.T @ upper_world
        out[1][n['UpperArm']] = matrix_quat(upper_local)
        out[1][n['Forearm']] = matrix_quat(forearm_local)
        forearm_world = upper_world @ forearm_local
        hand_rotation = target[:3, :3] / np.linalg.norm(target[:3, :3], axis=0)
        hand_local = forearm_world.T @ hand_rotation
        q = matrix_quat(hand_local)
        out[1][n['Hand']] = q
        # The forearm twist bone takes the hand's twist about the forearm (X), as in Oblivion's clips.
        twist = np.array([q[0], 0.0, 0.0, q[3]])
        out[1][n['ForearmTwist']] = twist / np.linalg.norm(twist)
        return max(distance - (upper + lower), 0.0) if distance > upper + lower else abs(distance - d)


def blend_matrix(a, b, f):
    if f <= 0.0:
        return a
    if f >= 1.0:
        return b
    qa, qb = matrix_quat(a[:3, :3]), matrix_quat(b[:3, :3])
    if qa @ qb < 0:
        qb = -qb
    q = qa + (qb - qa) * f
    out = np.eye(4)
    out[:3, :3] = quat_matrix(q / np.linalg.norm(q))
    out[:3, 3] = a[:3, 3] + (b[:3, 3] - a[:3, 3]) * f
    return out


def sway(t, period, amount=1.0):
    """Breathing: a slow rise and fall with a little drift, a whole number of breaths per loop."""
    w = 2 * math.pi * t / period
    return dict(dx=0.25 * amount * math.sin(w + 0.7), dy=0.45 * amount * math.sin(w), pitch=0.7 * amount *
                math.sin(w + 1.2), roll=0.4 * amount * math.sin(w + 2.0))


def relative_torch(arms, clip, t):
    w = arms.world(arms.local(clip, t))
    m = w[arms.index['Torch']].copy()
    m[:3, 3] -= w[arms.index['Camera01']][:3, 3]
    m[:3, :3] /= np.linalg.norm(m[:3, :3], axis=0)
    return m


def plan(arms, textkeys):
    """(name, duration, keys, body clip, body time offset and loop, pose at t, left arm source)."""
    clips = []

    def keys_of(clip):
        return [[t, k] for t, k in textkeys[clip]['keys'] if k.strip().lower() not in ('start', 'end')]

    # Idle: three breaths in the bow idle's three seconds.
    clips.append(('idle', 3.0, [], 'bowidle', lambda t: IDLE.moved(**sway(t, 3.0)), None))
    # Walk and run: the crossbow carried by the bow's motion relative to the eye (its Torch node).
    rest = relative_torch(arms, 'bowidle', 0.0)
    for move in ('forward', 'backward', 'left', 'right', 'fastforward', 'fastbackward', 'fastleft', 'fastright'):
        source = 'bow' + move

        def walking(t, source=source):
            delta = relative_torch(arms, source, t) @ np.linalg.inv(rest)
            out = Pose.of(IDLE.values())
            out.pos = (delta @ np.append(IDLE.pos, 1.0))[:3]
            # The bow's sway turns the crossbow by the same small angles about its own place.
            turn = delta[:3, :3]
            out.yaw += math.degrees(math.atan2(turn[0, 2], turn[2, 2]))
            out.pitch += math.degrees(math.asin(max(min(turn[2, 1], 1.0), -1.0)))
            return out
        clips.append((move, arms.duration(source), keys_of(source), source, walking, None))
    # Equip and unequip: up from below the screen into the idle, and back down.
    clips.append(('equip', 0.8, [[0.1, 'Attach']], 'bowidle',
                  lambda t: track([(0.0, LOWERED, 'smooth'), (0.7, IDLE, 'out')], t), None))
    clips.append(('unequip', 0.667, [[0.5, 'Detach']], 'bowidle',
                  lambda t: track([(0.0, IDLE, 'smooth'), (0.6, LOWERED, 'in')], t), None))
    # The shot and the reload.
    keys = attack_keys()
    clips.append(('attack', keys[-1][0], [[RELEASE, 'Release'], [SHOT_SPAN, 'a:R']], 'bowidle',
                  lambda t: track(keys, t), None))
    # Block: the crossbow raised across the face; a hit jolts it toward the eye.
    clips.append(('blockidle', arms.duration('bowblockidle'), [], 'bowidle',
                  lambda t: BLOCK.moved(**sway(t, arms.duration('bowblockidle'), 0.6)), None))
    clips.append(('blockhit', 0.3, [[0.0333, 'Blend: 0']], 'bowidle',
                  lambda t: track([(0.0, BLOCK, 'smooth'), (0.08, BLOCK.moved(dz=3.0, dy=1.5, pitch=6.0), 'out'),
                                   (0.3, BLOCK, 'smooth')], t), None))
    # Casts: the left hand casts (Oblivion's one-handed casts), the right holds the crossbow low.
    for cast in ('castself', 'casttarget'):
        source = 'onehand' + cast
        clips.append((cast, arms.duration(source), keys_of(source), source,
                      lambda t: CARRY.moved(**sway(t, 3.0, 0.5)), source))
    return clips


def bake_clip(rig, body_clip, duration, pose_at, left_from):
    arms = rig.arms
    frames = int(math.ceil(duration * FPS - 1e-6))
    times = np.array([min(k / FPS, duration) for k in range(frames + 1)])
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


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    in_glb, in_keys, out_glb, out_keys = sys.argv[1:]
    j, blob = load_glb(in_glb)
    textkeys = json.load(open(in_keys))
    if any(a['name'].startswith(PREFIX) for a in j.get('animations', [])):
        print(f'{in_glb} already holds crossbow clips: bake from the dual-wield output (rebake_arms.sh)')
        return 1
    arms = Arms(j, blob)
    rig = Rig(arms)
    writer = Writer(j, blob)
    for action, duration, keys, body, pose_at, left_from in plan(arms, textkeys):
        name = PREFIX + action
        times, out_t, out_q, out_s, worst = bake_clip(rig, body, duration, pose_at, left_from)
        writer.animation(name, arms, times, out_t, out_q, out_s)
        textkeys[name] = {'length': float(duration),
                          'keys': [[0.0, 'start']] + [[float(t), k] for t, k in keys] + [[float(duration), 'end']]}
        # The gate: how far each wrist stays from its target where the arm cannot reach (units, and when).
        print(f'{name}: {duration:.3f} s, {len(times)} frames, wrist miss R {worst["R"][0]:.2f} at {worst["R"][1]:.2f} s'
              f' L {worst["L"][0]:.2f} at {worst["L"][1]:.2f} s, keys {keys}')
    save_glb(out_glb, j, writer.blob)
    with open(out_keys, 'w') as stream:
        json.dump(textkeys, stream, indent=1)
    print(f'wrote {out_glb} ({len(j["animations"])} clips) and {out_keys}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
