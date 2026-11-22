#!/usr/bin/env python3
"""Author the Dragon Pharaoh's clips on the Lizardman Warrior skeleton (no Blender): the open book rests on both palms
in front of the chest (fixed in the B_Spine2 frame), both arms solved by a two-bone IK that keeps each bone's own roll
(minimal swing from the source clip) with a fixed elbow pole; the hand's twist about its axis is shared half with the
forearm's twist bone. Fidget turns a page with the right hand and nods; Bless lifts the right hand, palm out, over the
couple. Walking and Hit keep their bodies with the book held; Death lets the hands go (the book stays in the left hand).

    author_clips.py <in.glb> <clips.json> <out.glb> <book_local.json> [--gates gates.json]

Writes the clips (replacing those names, dropping the spec's `drop` list) and the book's pose in B_L_Hand space."""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pglb import load, lod0_body, trs_matrix, matrix_quaternion, quaternion_matrix, slerp  # noqa: E402


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def swing(a, b):
    """Rotation matrix taking unit a to unit b (shortest arc)."""
    a, b = unit(a), unit(b)
    c = np.cross(a, b)
    s = np.linalg.norm(c)
    d = float(np.dot(a, b))
    if s < 1e-9:
        return np.eye(3) if d > 0 else -np.eye(3)
    k = c / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    ang = math.atan2(s, d)
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def rot_axis(axis, deg):
    return swing_axis(unit(axis), math.radians(deg))


def swing_axis(k, ang):
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def frame_from(y_dir, z_hint):
    """Orthonormal frame with Y along y_dir and Z as close as possible to z_hint."""
    y = unit(y_dir)
    z = unit(z_hint - np.dot(z_hint, y) * y)
    x = np.cross(y, z)
    return np.column_stack([x, y, z])


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def twist_about_y(R):
    """Angle (rad) of R's twist about local Y (swing-twist decomposition)."""
    q = matrix_quaternion(R)
    if q[3] < 0:
        q = -q
    return 2 * math.atan2(q[1], q[3])


class Rig:
    def __init__(self, path):
        self.g, self.m, self.n = load(path)
        self.rest = self.m.rest
        prim, dom = lod0_body(self.m)
        W = self.m.world({})
        self.palm = {}
        for side in 'LR':
            h = self.n[f'B_{side}_Hand']
            Hi = np.linalg.inv(W[h])
            pts = prim['positions'][dom == h]
            loc = (np.c_[pts, np.ones(len(pts))] @ Hi.T)[:, :3]
            c = loc.mean(0)
            _, _, vt = np.linalg.svd(loc - c)
            nrm = vt[2]
            tips = [(Hi @ W[self.n[f'B_{side}_Finger{k}2']])[:3, 3] for k in (1, 2, 4)]
            nrm = nrm * np.sign(np.dot(np.mean(tips, 0) - c, nrm))
            off = ((loc - c) @ nrm).max()
            self.palm[side] = (c + nrm * off, nrm)

    def local_pose(self, clip, t):
        loc = [list(map(np.copy, r)) for r in self.rest]
        for node, trs in self.m.sample(clip, t).items():
            loc[node] = [np.asarray(x, float) for x in trs]
        return loc

    def world(self, loc):
        return self.m.world({i: tuple(v) for i, v in enumerate(loc)})


def book_in_hand(rig, spec, side):
    """Book frame (4x4) in the hand's space. grip 'palms': book Y = palm normal (the book on the palms), X across the
    pages; grip 'edges': each palm against the cover's outer edge (palms facing each other), fingers towards the far
    edge. Origin at the spine centre on the book's underside."""
    b = spec['book']
    c, nrm = rig.palm[side]
    fingers = np.array([0, 1.0, 0])
    f = unit(fingers - np.dot(fingers, nrm) * nrm)
    yaw = b.get('finger_yaw_deg', {}).get(side, 0.0)
    f = swing_axis(nrm, math.radians(yaw)) @ f
    B = np.eye(4)
    if b.get('grip', 'palms') == 'edges':
        xb = nrm if side == 'L' else -nrm
        zb = -f
        yb = np.cross(zb, xb)
        R = np.column_stack([xb, yb, zb])
        edge = np.array([-b['width'] / 2 if side == 'L' else b['width'] / 2, b['page_thickness'] * 0.6, 0.0])
        B[:3, :3] = R
        B[:3, 3] = c + nrm * b['palm_gap'] - R @ edge
        return B
    xb = f if side == 'L' else -f
    yb = nrm
    zb = np.cross(xb, yb)
    B[:3, :3] = np.column_stack([xb, yb, zb])
    off = b['palm_offset_x']
    palm_x = -off if side == 'L' else off           # the palm centre's x in book space
    B[:3, 3] = c + nrm * b['palm_gap'] - xb * palm_x
    return B


def book_world_rest(rig, spec):
    b = spec['book']
    a = math.radians(b['tilt_deg'])
    yb = np.array([0, math.cos(a), -math.sin(a)])       # page normal: up and back to the reader
    xb = np.array([-1.0, 0, 0])                         # reader's left to right
    zb = np.cross(xb, yb)
    R = np.column_stack([xb, yb, zb])
    if b['yaw_deg']:
        R = rot_axis([0, 1, 0], b['yaw_deg']) @ R
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = b['centre']
    return M


def solve_arm(rig, loc, side, target, pole_w, twist_share=0.5):
    """Two-bone IK in place on `loc` for the wrist pose `target` (4x4 world)."""
    n = rig.n
    ua, fa, ha, ft = n[f'B_{side}_UpperArm'], n[f'B_{side}_Forearm'], n[f'B_{side}_Hand'], n[f'B_{side}_ForearmTwist']
    W = rig.world(loc)
    S = W[ua][:3, 3]
    l1 = np.linalg.norm(loc[fa][0]); l2 = np.linalg.norm(loc[ha][0])
    T = target[:3, 3]
    d = np.linalg.norm(T - S)
    reach = d
    d = min(d, (l1 + l2) * 0.999)
    nhat = unit(T - S)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0))
    p = np.asarray(pole_w, float)
    pp = unit(p - np.dot(p, nhat) * nhat)
    E = S + nhat * a + pp * h
    Tc = S + nhat * d
    parent_u = W[rig.m.parent[ua]][:3, :3]
    Ru = W[ua][:3, :3]
    Ru2 = swing(Ru[:, 1], E - S) @ Ru
    loc[ua][1] = matrix_quaternion(parent_u.T @ Ru2)
    Rf = Ru2 @ quaternion_matrix(loc[fa][1])
    Rf2 = swing(Rf[:, 1], Tc - E) @ Rf
    loc[fa][1] = matrix_quaternion(Ru2.T @ Rf2)
    Rh_local = Rf2.T @ target[:3, :3]
    loc[ha][1] = matrix_quaternion(Rh_local)
    tw = twist_about_y(Rh_local)
    loc[ft][1] = matrix_quaternion(swing_axis(np.array([0, 1.0, 0]), tw * twist_share))
    return reach - (l1 + l2), Rh_local, tw


def set_fingers(rig, loc, side, curl_share, src_loc):
    """Fingers at their rest (open claw) blended a little towards the source clip's grip."""
    for name, i in rig.n.items():
        if name.startswith(f'B_{side}_Finger'):
            q = slerp(np.asarray(rig.rest[i][1], float), np.asarray(src_loc[i][1], float), curl_share)
            loc[i][1] = q


def author(rig, spec, name, cs):
    fps = spec['fps']
    base = cs['base']
    blen = max(rig.m.clip_times(base))
    length = cs.get('length', blen)
    nf = int(round(length * fps)) + 1
    times = np.linspace(0, length, nf)
    nb = rig.n
    BL = book_in_hand(rig, spec, 'L'); BR = book_in_hand(rig, spec, 'R')
    W0 = rig.world([list(map(np.copy, r)) for r in rig.rest])
    chest0 = W0[nb['B_Spine2']]
    book_chest = np.linalg.inv(chest0) @ book_world_rest(rig, spec)
    frames = []
    gates = {'reach_over_mm': 0.0, 'wrist_deg_max': 0.0, 'twist_deg_max': 0.0}
    prev_tw = {}
    for t in times:
        ts = (t % blen) if base in ('Standing',) or name in ('Walking',) else min(t, blen)
        loc = rig.local_pose(base, ts)
        mix = cs.get('body_mix')
        if mix is not None:
            calm = rig.local_pose('Standing', 0.0)
            for i in range(len(loc)):
                loc[i][1] = slerp(np.asarray(calm[i][1]), np.asarray(loc[i][1]), mix)
                loc[i][0] = calm[i][0] + (loc[i][0] - calm[i][0]) * mix
        src = [list(map(np.copy, x)) for x in loc]
        # head nod / lift
        hn = cs.get('head_nod')
        if hn:
            w = smoothstep((t - hn[0]) / 0.5) * (1 - smoothstep((t - (hn[1] - 0.5)) / 0.5))
            loc[nb['B_Head']][1] = matrix_quaternion(quaternion_matrix(loc[nb['B_Head']][1]) @ rot_axis([1, 0, 0], hn[2] * w))
        W = rig.world(loc)
        chest = W[nb['B_Spine2']]
        book = chest @ book_chest
        targetL = book @ np.linalg.inv(BL)
        targetR = book @ np.linalg.inv(BR)
        release = cs.get('release')
        wrel = 0.0
        if release is not None and release[1] > 0:
            wrel = smoothstep((t - release[0]) / max(release[1] - release[0], 1e-6))
        elif release is not None:
            wrel = 1.0
        # right-hand free poses
        if 'page_turn' in cs:
            a, b = cs['page_turn']
            s = min(max((t - a) / (b - a), 0), 1)
            if 0 < s < 1:
                # in book space: the grip, a palm-down hover over the right page, a sweep to the left page, back
                hold = np.linalg.inv(BR)
                down = np.eye(4)
                down[:3, :3] = frame_from(np.array([-0.75, 0.0, -0.66]), np.array([0, -1.0, 0]))
                over_r = down.copy(); over_r[:3, 3] = [0.11, 0.125, 0.0]
                over_l = down.copy(); over_l[:3, 3] = [-0.05, 0.115, -0.01]
                keys = [(0.0, hold), (0.28, over_r), (0.5, over_l), (0.72, over_r), (1.0, hold)]
                for (s0, k0), (s1, k1) in zip(keys, keys[1:]):
                    if s0 <= s <= s1:
                        u = smoothstep((s - s0) / (s1 - s0))
                        q = slerp(matrix_quaternion(k0[:3, :3]), matrix_quaternion(k1[:3, :3]), u)
                        local = np.eye(4); local[:3, :3] = quaternion_matrix(q)
                        local[:3, 3] = k0[:3, 3] * (1 - u) + k1[:3, 3] * u
                        if k0 is hold or k1 is hold:
                            local[:3, 3] += np.array([0.05, 0.03, 0]) * math.sin(math.pi * u)
                        break
                targetR = book @ local
        if 'bless' in cs:
            a, b, c, d = cs['bless']
            w = smoothstep((t - a) / (b - a)) * (1 - smoothstep((t - c) / (d - c)))
            if w > 0:
                Wp = chest @ np.linalg.inv(chest0)
                free = np.eye(4)
                free[:3, :3] = frame_from(np.array(cs['fingers'], float), None if False else -np.array(cs['palm'], float)) \
                    if False else frame_from(np.array(cs['fingers'], float), np.array(cs['palm'], float))
                # palm normal is the hand's +Z (right hand): align Z with the palm direction
                free[:3, 3] = cs['wrist']
                free = Wp @ free
                q = slerp(matrix_quaternion(targetR[:3, :3]), matrix_quaternion(free[:3, :3]), w)
                arc = np.array([0, 0.06, 0.04]) * math.sin(math.pi * w)
                pos = targetR[:3, 3] * (1 - w) + free[:3, 3] * w + arc
                targetR = np.eye(4); targetR[:3, :3] = quaternion_matrix(q); targetR[:3, 3] = pos
            hl = cs.get('head_lift', 0) * w
            if hl:
                loc[nb['B_Head']][1] = matrix_quaternion(quaternion_matrix(loc[nb['B_Head']][1]) @ rot_axis([1, 0, 0], -hl))
        for side, target in (('L', targetL), ('R', targetR)):
            keep = [list(map(np.copy, x)) for x in loc] if wrel > 0 else None
            over, Rh, tw = solve_arm(rig, loc, side, target, chest[:3, :3] @ chest0[:3, :3].T @ np.asarray(spec['pole'][side], float))
            set_fingers(rig, loc, side, spec['finger_curl'], src)
            if wrel > 0:
                for bone in ('UpperArm', 'Forearm', 'Hand', 'ForearmTwist'):
                    i = nb[f'B_{side}_{bone}']
                    loc[i][1] = slerp(np.asarray(loc[i][1]), np.asarray(src[i][1]), wrel)
                for nm, i in nb.items():
                    if nm.startswith(f'B_{side}_Finger'):
                        loc[i][1] = slerp(np.asarray(loc[i][1]), np.asarray(src[i][1]), wrel)
            gates['reach_over_mm'] = max(gates['reach_over_mm'], over * 1000)
            ang = math.degrees(math.acos(min(1, max(-1, Rh[1, 1]))))
            gates['wrist_deg_max'] = max(gates['wrist_deg_max'], ang)
            gates['twist_deg_max'] = max(gates['twist_deg_max'], abs(math.degrees(tw)))
            if side in prev_tw:
                gates.setdefault('twist_jump_deg_max', 0.0)
                gates['twist_jump_deg_max'] = max(gates['twist_jump_deg_max'], abs(math.degrees(tw - prev_tw[side])))
            prev_tw[side] = tw
        frames.append(loc)
    return times, frames, gates


def write_clip(g, name, times, frames, animated, rest):
    tacc = g.append_accessor(np.asarray(times, np.float32).reshape(-1, 1), 'SCALAR')
    samplers, channels = [], []
    for node in animated:
        for path, k, kind in (('translation', 0, 'VEC3'), ('rotation', 1, 'VEC4'), ('scale', 2, 'VEC3')):
            vals = np.array([f[node][k] for f in frames], np.float64)
            if path != 'rotation' and np.abs(vals - np.asarray(rest[node][k])).max() < 1e-7:
                continue
            if path == 'rotation':
                for i in range(1, len(vals)):
                    if np.dot(vals[i], vals[i - 1]) < 0:
                        vals[i] = -vals[i]
            samplers.append({'input': tacc, 'output': g.append_accessor(vals.astype(np.float32), kind),
                             'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': node, 'path': path}})
    return {'name': name, 'channels': channels, 'samplers': samplers}


def main():
    src, spec_path, out, book_out = sys.argv[1:5]
    spec = json.load(open(spec_path))
    rig = Rig(src)
    g = rig.g
    skel = sorted(set(rig.m.joints))
    new = []
    report = {}
    for name, cs in spec['clips'].items():
        times, frames, gates = author(rig, spec, name, cs)
        anim = write_clip(g, name, times, frames, skel, rig.rest)
        new.append(anim)
        report[name] = {'length': float(times[-1]), 'frames': len(times), **{k: round(v, 2) for k, v in gates.items()}}
        print(name, report[name])
    keep = [a for a in g.json['animations'] if a['name'] not in spec['clips'] and a['name'] not in spec['drop']]
    g.json['animations'] = new + keep
    g.write(out)
    BL = book_in_hand(rig, spec, 'L')
    json.dump({'book_in_B_L_Hand': BL.tolist(), 'book_in_B_R_Hand': book_in_hand(rig, spec, 'R').tolist(),
               'book': spec['book'], 'gates': report}, open(book_out, 'w'), indent=1)
    print('WROTE', out, book_out, 'clips', [a['name'] for a in g.json['animations']])


if __name__ == '__main__':
    main()
