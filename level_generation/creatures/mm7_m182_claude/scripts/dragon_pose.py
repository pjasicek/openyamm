"""Pose parameters of the v2 MM7 Dragon, shared by the native-frame fitter (system Python, numpy skinning) and the clip
author (Blender). A pose is a dict of named parameters; `ops()` turns it into world-axis bone rotations (rest frame,
applied in order about each bone's head, as `rot()` in the clip script) plus the Root translation.

Sign conventions (model faces -Y, +X is the dragon's left): +root_pitch lowers the front; +root_roll lowers the left
side; +root_yaw turns the head toward +X; +w_elev raises the wing; +w_sweep moves it back; +w_twist raises the
trailing edge... about X; +w_hand / +w_tip droop the outer wing; +w_fold closes the trailing fingers toward the arm;
neck/head/tail pitch about +X (a +X turn lowers a forward-pointing bone and lifts a backward-pointing one).
Right-side wing parameters default to the left ones (mirrored); `r_` prefixed keys override them for asymmetric
poses (hit, death)."""
import numpy as np

PARAMS = [
    # name, default, lower, upper
    ('root_pitch', 0., -1.8, 1.8), ('root_roll', 0., -1.6, 1.6), ('root_yaw', 0., -1.2, 1.2),
    ('root_x', 0., -.2, .2), ('root_y', 0., -.2, .2), ('root_z', 0., -.3, .3),
    ('spine_pitch', 0., -.4, .4), ('spine_yaw', 0., -.4, .4),
    ('neck_pitch1', 0., -1.2, 1.2), ('neck_pitch2', 0., -1.2, 1.2), ('neck_yaw', 0., -1.2, 1.2), ('neck_roll', 0., -.8, .8),
    ('head_pitch', 0., -1., 1.), ('head_yaw', 0., -1., 1.), ('jaw', .04, 0., .7),
    ('tail_pitch1', 0., -.3, .3), ('tail_pitch2', 0., -.12, .12), ('tail_yaw1', 0., -.3, .3), ('tail_yaw2', 0., -.12, .12),
    ('fore_upper', 0., -1.5, 1.5), ('fore_lower', 0., -1.5, 1.5), ('hind_upper', 0., -1.5, 1.5), ('hind_lower', 0., -1.5, 1.5),
    ('w_elev', 0., -1.7, 1.7), ('w_sweep', 0., -.6, .6), ('w_twist', 0., -.6, .6), ('w_elbow', 0., -.6, .6),
    ('w_hand', 0., -1.4, 1.4), ('w_tip', 0., -1.2, 1.2), ('w_fold', 0., -.3, 1.),
]
NAMES = [p[0] for p in PARAMS]
DEFAULT = {p[0]: p[1] for p in PARAMS}
BOUNDS = {p[0]: (p[2], p[3]) for p in PARAMS}
WING_KEYS = [n for n in NAMES if n.startswith('w_')]
X, Y, Z = (1., 0., 0.), (0., 1., 0.), (0., 0., 1.)


def full(p):
    q = dict(DEFAULT); q.update(p or {}); return q


def ops(p):
    """List of (bone, world_axis, angle) and the Root shift for pose dict p (missing keys take defaults)."""
    p = full(p); out = []
    out += [('Root', X, p['root_pitch']), ('Root', Y, p['root_roll']), ('Root', Z, p['root_yaw'])]
    for b in ('Spine1', 'Spine2'):
        out += [(b, X, p['spine_pitch']), (b, Z, p['spine_yaw'])]
    out += [('Neck1', X, p['neck_pitch1']), ('Neck2', X, p['neck_pitch2'] / 2), ('Neck3', X, p['neck_pitch2'] / 2)]
    for b in ('Neck1', 'Neck2', 'Neck3'):
        out += [(b, Z, p['neck_yaw'] / 3), (b, Y, p['neck_roll'] / 3)]
    out += [('Head', X, p['head_pitch']), ('Head', Z, p['head_yaw']), ('Jaw', X, p['jaw'])]
    for i in range(1, 11):
        out += [(f'Tail{i}', X, p['tail_pitch1'] if i <= 3 else p['tail_pitch2']),
                (f'Tail{i}', Z, p['tail_yaw1'] if i <= 3 else p['tail_yaw2'])]
    for s, sg in (('L', 1.), ('R', -1.)):
        w = {k: p.get('r_' + k, p[k]) if s == 'R' else p[k] for k in WING_KEYS}
        out += [(s + 'ForeUpper', X, p['fore_upper']), (s + 'ForeLower', X, p['fore_lower']),
                (s + 'HindUpper', X, p['hind_upper']), (s + 'HindLower', X, p['hind_lower'])]
        out += [(s + 'Wing0', Z, sg * w['w_sweep']), (s + 'Wing0', Y, -sg * w['w_elev']), (s + 'Wing0', X, w['w_twist'])]
        out += [(s + 'Wing1', Z, sg * w['w_elbow'])]
        out += [(s + 'Wing2', Y, sg * w['w_hand']), (s + 'Wing2', Z, -sg * .3 * w['w_fold'])]
        out += [(s + 'Wing3', Y, sg * w['w_tip'])]
        out += [(s + 'WingF2', Y, sg * (w['w_hand'] + .5 * w['w_tip'])), (s + 'WingF2', Z, -sg * w['w_fold'])]
        out += [(s + 'WingF3', Y, sg * .45 * w['w_hand']), (s + 'WingF3', Z, -sg * .8 * w['w_fold'])]
    shift = np.array([p['root_x'], p['root_y'], p['root_z']])
    return out, shift


def axis_angle(axis, angle):
    a = np.asarray(axis, float); a = a / np.linalg.norm(a); c, s = np.cos(angle), np.sin(angle); x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


class Skinner:
    """Linear blend skinning of the rig dump (scripts/dump_mesh.py), matching Blender's pose evaluation for poses
    built from world-axis rotations about bone heads (Skin_b = Skin_parent @ T(h) R T(-h))."""

    def __init__(self, npz):
        d = np.load(npz, allow_pickle=True)
        self.co = d['co']; self.tris = d['tris']; self.bones = [str(b) for b in d['bone_names']]
        self.parent = d['bone_parent']; self.head = d['bone_head']
        groups = [str(g) for g in d['group_names']]; W = d['weights']
        self.W = np.zeros((len(self.co), len(self.bones)), np.float32)
        for gi, g in enumerate(groups):
            self.W[:, self.bones.index(g)] = W[:, gi]
        s = self.W.sum(1, keepdims=True); self.W /= np.maximum(s, 1e-9)
        self.order = []; seen = set()
        while len(self.order) < len(self.bones):
            for i, pa in enumerate(self.parent):
                if i not in seen and (pa < 0 or pa in seen): self.order.append(i); seen.add(i)
        self.index = {b: i for i, b in enumerate(self.bones)}

    def matrices(self, p):
        rot = {b: np.eye(3) for b in self.bones}
        o, shift = ops(p)
        for b, axis, ang in o:
            if b in rot and ang != 0: rot[b] = rot[b] @ axis_angle(axis, ang)
        skin = [None] * len(self.bones)
        for i in self.order:
            M = np.eye(4); h = self.head[i]
            M[:3, :3] = rot[self.bones[i]]; M[:3, 3] = h - rot[self.bones[i]] @ h
            if self.bones[i] == 'Root': M[:3, 3] += shift
            skin[i] = M if self.parent[i] < 0 else skin[self.parent[i]] @ M
        return np.array(skin)

    def pose(self, p, idx=None):
        S = self.matrices(p); co = self.co if idx is None else self.co[idx]; W = self.W if idx is None else self.W[idx]
        used = np.nonzero(W.sum(0) > 0)[0]
        out = np.zeros_like(co)
        for b in used:
            w = W[:, b]; m = w > 0
            out[m] += w[m, None] * (co[m] @ S[b, :3, :3].T + S[b, :3, 3])
        return out
