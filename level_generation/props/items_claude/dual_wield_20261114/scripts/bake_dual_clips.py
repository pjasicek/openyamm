#!/usr/bin/env python3
"""Bake the dual-wield clips into a first-person arms GLB (devdocs/solo_action/WEAPONS.md "Dual wielding").

    bake_dual_clips.py <in.glb> <in.textkeys.json> <out.glb> <out.textkeys.json>

The engine plays one clip on the whole skeleton (no per-arm layering), so every dual clip is baked here from the
one-handed set: the right arm's one-hand clips mirrored onto the left arm across the body's sagittal plane (glTF X = 0;
left and right bones swapped by name), then combined per arm. The right arm (Bip01 R Clavicle and below), the left arm
(Bip01 L Clavicle and below) and the body (everything else: spine, neck, Camera01) each take their pose from one source
clip, or the body from the mean of a clip and its mirror where both arms move alike.

A new node, OffHandWeapon, is added under Bip01 L Hand: the mirror of the right hand's Weapon node with its flat axis
(Z) turned over, so the off-hand weapon is a rotated copy of the main one, never a reflected one (no inside-out winding).

The input is never modified and must not already hold dual clips: keep the pristine GLB and bake from it again after a
change here. Every existing clip, mesh, skin and texture is copied byte for byte; only animations, accessors, buffer
views and the new node are appended. numpy only.
"""
import json
import struct
import sys

import numpy as np

FPS = 30.0
MIRROR = np.diag([-1.0, 1.0, 1.0, 1.0])
# The off-hand weapon's frame: the main hand's mirrored with the blade's flat (Z) turned over.
FLIP_FLAT = np.diag([1.0, 1.0, -1.0, 1.0])
OFF_HAND_NODE = 'OffHandWeapon'
# Nodes without a mirrored partner that keep their own local transform in a mirrored clip.
UNPAIRED = {'Torch', 'Weapon', 'BackWeapon', 'Quiver', 'SideWeapon', 'magicNode', OFF_HAND_NODE}
# The cross slash: the left blade follows the right by this much, so the forearms pass one after the other.
CROSS_DELAY = 0.1
# After its blow the cutting arm settles back into its raised guard (onehandidle, mirrored for the left) between
# SETTLE_FROM seconds past the Hit and the clip's end, instead of following through across the waiting arm.
SETTLE_FROM = 0.06
# Equip and unequip: the left hand draws (sheathes) this long after the right, so the blades never meet in front of the
# eye.
DRAW_DELAY = 0.25


def load_glb(path):
    data = open(path, 'rb').read()
    magic, _, _ = struct.unpack_from('<III', data, 0)
    assert magic == 0x46546C67, path
    json_length, json_type = struct.unpack_from('<II', data, 12)
    assert json_type == 0x4E4F534A
    j = json.loads(data[20:20 + json_length])
    offset = 20 + json_length
    bin_length, bin_type = struct.unpack_from('<II', data, offset)
    assert bin_type == 0x004E4942
    return j, bytearray(data[offset + 8:offset + 8 + bin_length])


def save_glb(path, j, blob):
    while len(blob) % 4:
        blob.append(0)
    j['buffers'][0]['byteLength'] = len(blob)
    text = json.dumps(j, separators=(',', ':')).encode()
    text += b' ' * ((4 - len(text) % 4) % 4)
    total = 12 + 8 + len(text) + 8 + len(blob)
    # 'wb' truncates the existing file in place: its hard links (the engine copy, the reference copy) stay one file.
    with open(path, 'wb') as stream:
        stream.write(struct.pack('<III', 0x46546C67, 2, total))
        stream.write(struct.pack('<II', len(text), 0x4E4F534A))
        stream.write(text)
        stream.write(struct.pack('<II', len(blob), 0x004E4942))
        stream.write(blob)


COMPONENT = {5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}


def read_accessor(j, blob, index):
    acc = j['accessors'][index]
    view = j['bufferViews'][acc['bufferView']]
    width = WIDTH[acc['type']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    values = np.frombuffer(bytes(blob[start:start + acc['count'] * width * 4]), np.float32).astype(float)
    return values.reshape(acc['count'], width) if width > 1 else values


def quat_matrix(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def matrix_quat(r):
    trace = r[0, 0] + r[1, 1] + r[2, 2]
    if trace > 0:
        s = np.sqrt(trace + 1.0) * 2
        q = [(r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s, 0.25 * s]
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = np.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2
        q = [0.25 * s, (r[0, 1] + r[1, 0]) / s, (r[0, 2] + r[2, 0]) / s, (r[2, 1] - r[1, 2]) / s]
    elif r[1, 1] > r[2, 2]:
        s = np.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2
        q = [(r[0, 1] + r[1, 0]) / s, 0.25 * s, (r[1, 2] + r[2, 1]) / s, (r[0, 2] - r[2, 0]) / s]
    else:
        s = np.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2
        q = [(r[0, 2] + r[2, 0]) / s, (r[1, 2] + r[2, 1]) / s, 0.25 * s, (r[1, 0] - r[0, 1]) / s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def compose(t, q, s):
    m = np.eye(4)
    m[:3, :3] = quat_matrix(q) * s
    m[:3, 3] = t
    return m


def decompose(m):
    scale = np.linalg.norm(m[:3, :3], axis=0)
    rotation = m[:3, :3] / scale
    assert np.linalg.det(rotation) > 0, 'a mirrored transform kept its reflection'
    return m[:3, 3].copy(), matrix_quat(rotation), scale


class Arms:
    def __init__(self, j, blob):
        self.j = j
        self.blob = blob
        self.nodes = j['nodes']
        self.index = {n.get('name'): i for i, n in enumerate(self.nodes)}
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get('children', []):
                self.parent[c] = i
        self.order = []
        roots = [i for i in range(len(self.nodes)) if i not in self.parent]
        stack = list(reversed(roots))
        while stack:
            i = stack.pop()
            self.order.append(i)
            stack.extend(reversed(self.nodes[i].get('children', [])))
        self.rest_t = np.array([n.get('translation', [0, 0, 0]) for n in self.nodes], float)
        self.rest_q = np.array([n.get('rotation', [0, 0, 0, 1]) for n in self.nodes], float)
        self.rest_s = np.array([n.get('scale', [1, 1, 1]) for n in self.nodes], float)
        self.clips = {}
        for animation in j.get('animations', []):
            channels = []
            for channel in animation['channels']:
                sampler = animation['samplers'][channel['sampler']]
                assert sampler.get('interpolation', 'LINEAR') == 'LINEAR'
                path = channel['target']['path']
                if path == 'weights':
                    continue
                channels.append((channel['target']['node'], path, read_accessor(j, blob, sampler['input']),
                                 read_accessor(j, blob, sampler['output'])))
            duration = max(c[2][-1] for c in channels)
            self.clips[animation['name']] = (channels, duration)

    def duration(self, clip):
        return self.clips[clip][1]

    def local(self, clip, t):
        trs = [self.rest_t.copy(), self.rest_q.copy(), self.rest_s.copy()]
        if clip is None:
            return trs
        for node, path, times, values in self.clips[clip][0]:
            k = int(np.searchsorted(times, t))
            k = min(max(k, 1), len(times) - 1) if len(times) > 1 else 0
            if len(times) == 1:
                value = values[0]
            else:
                f = float(np.clip((t - times[k - 1]) / max(times[k] - times[k - 1], 1e-9), 0.0, 1.0))
                a, b = values[k - 1], values[k]
                if path == 'rotation':
                    if np.dot(a, b) < 0:
                        b = -b
                    value = a + (b - a) * f
                    value = value / np.linalg.norm(value)
                else:
                    value = a + (b - a) * f
            trs[{'translation': 0, 'rotation': 1, 'scale': 2}[path]][node] = value
        return trs

    def world(self, trs):
        out = np.zeros((len(self.nodes), 4, 4))
        for i in self.order:
            m = compose(trs[0][i], trs[1][i], trs[2][i])
            out[i] = out[self.parent[i]] @ m if i in self.parent else m
        return out

    def subtree(self, name):
        out = set()
        stack = [self.index[name]]
        while stack:
            i = stack.pop()
            out.add(i)
            stack.extend(self.nodes[i].get('children', []))
        return out


def swapped(name):
    for a, b in ((' L ', ' R '), (' R ', ' L ')):
        if a in name:
            return name.replace(a, b)
    return name


class Mirror:
    """The mirrored pose of any clip: each bone takes its partner's world transform reflected across X = 0, then
    corrected by the partner's rest frame so the rest pose maps onto itself."""

    def __init__(self, arms):
        self.arms = arms
        rest = arms.world(arms.local(None, 0.0))
        self.rest = rest
        self.pair = {}
        self.correction = {}
        for i, node in enumerate(arms.nodes):
            name = node.get('name', '')
            if 'mesh' in node or name in UNPAIRED:
                continue
            partner = arms.index[swapped(name)]
            self.pair[i] = partner
            self.correction[i] = np.linalg.inv(rest[i]) @ MIRROR @ rest[partner]
        weapon, right_hand = arms.index['Weapon'], arms.index['Bip01 R Hand']
        self.weapon = weapon
        self.right_hand_correction = self.correction[right_hand]

    def symmetry_error(self):
        worst = 0.0
        for i, partner in self.pair.items():
            worst = max(worst, np.abs((MIRROR @ self.rest[i])[:3, 3] - self.rest[partner][:3, 3]).max())
        return worst

    def off_hand_local(self, weapon_local):
        return np.linalg.inv(self.right_hand_correction) @ weapon_local @ FLIP_FLAT

    def local(self, clip, t):
        arms = self.arms
        trs = arms.local(clip, t)
        world = arms.world(trs)
        mirrored = {}
        for i, partner in self.pair.items():
            mirrored[partner] = MIRROR @ world[i] @ self.correction[i]
        out = [trs[0].copy(), trs[1].copy(), trs[2].copy()]
        for i in mirrored:
            local = np.linalg.inv(mirrored[arms.parent[i]]) @ mirrored[i] if i in arms.parent else mirrored[i]
            out[0][i], out[1][i], out[2][i] = decompose(local)
        weapon_local = compose(trs[0][self.weapon], trs[1][self.weapon], trs[2][self.weapon])
        off = arms.index.get(OFF_HAND_NODE)
        if off is not None:
            out[0][off], out[1][off], out[2][off] = decompose(self.off_hand_local(weapon_local))
        return out


def add_off_hand_node(arms, mirror):
    """OffHandWeapon under Bip01 L Hand at the mirror of the Weapon node's rest place."""
    j = arms.j
    weapon = arms.nodes[arms.index['Weapon']]
    t, q, s = decompose(mirror.off_hand_local(compose(np.array(weapon['translation']), np.array(weapon['rotation']),
                                                      np.array(weapon['scale']))))
    j['nodes'].append({'name': OFF_HAND_NODE, 'translation': t.tolist(), 'rotation': q.tolist(),
                       'scale': s.tolist()})
    index = len(j['nodes']) - 1
    j['nodes'][arms.index['Bip01 L Hand']].setdefault('children', []).append(index)
    # Rebuild the views of the hierarchy with the new node.
    rebuilt = Arms(j, arms.blob)
    arms.__dict__.update(rebuilt.__dict__)
    return index


class Source:
    """One clip as a pose source: mirrored or not, delayed, looped or held at its ends. settle: (from, to) seconds over
    which this arm blends from the clip into its raised guard (SETTLE_FROM)."""

    def __init__(self, clip, mirrored=False, delay=0.0, loop=False, settle=None):
        self.clip, self.mirrored, self.delay, self.loop, self.settle = clip, mirrored, delay, loop, settle

    def sample(self, arms, mirror, t):
        duration = arms.duration(self.clip)
        time = t - self.delay
        time = time % duration if self.loop else min(max(time, 0.0), duration)
        return mirror.local(self.clip, time) if self.mirrored else arms.local(self.clip, time)

    def guard(self):
        return Source('onehandidle', mirrored=self.mirrored, loop=True)

    def settle_share(self, t):
        if self.settle is None:
            return 0.0
        x = float(np.clip((t - self.settle[0]) / max(self.settle[1] - self.settle[0], 1e-6), 0.0, 1.0))
        return x * x * (3.0 - 2.0 * x)


def mean_pose(poses):
    t = sum(p[0] for p in poses) / len(poses)
    s = sum(p[2] for p in poses) / len(poses)
    q = poses[0][1].copy()
    for p in poses[1:]:
        other = p[1] * np.where(np.sum(p[1] * poses[0][1], axis=1, keepdims=True) < 0, -1.0, 1.0)
        q = q + other
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    return [t, q, s]


def eye_relative_arm(arms, source_pose, body_world, root, camera, nodes):
    """An arm's locals from a source pose, its clavicle solved so the arm keeps its place relative to the eye on the
    baked body."""
    source_world = arms.world(source_pose)
    shift = np.eye(4)
    shift[:3, 3] = body_world[camera][:3, 3] - source_world[camera][:3, 3]
    out = [source_pose[0].copy(), source_pose[1].copy(), source_pose[2].copy()]
    local = np.linalg.inv(body_world[arms.parent[root]]) @ shift @ source_world[root]
    out[0][root], out[1][root], out[2][root] = decompose(local)
    return out


def blend_pose(a, b, share, nodes):
    out = [a[0].copy(), a[1].copy(), a[2].copy()]
    for i in nodes:
        out[0][i] = a[0][i] + (b[0][i] - a[0][i]) * share
        out[2][i] = a[2][i] + (b[2][i] - a[2][i]) * share
        q = b[1][i] if np.dot(a[1][i], b[1][i]) >= 0 else -b[1][i]
        q = a[1][i] + (q - a[1][i]) * share
        out[1][i] = q / np.linalg.norm(q)
    return out


def bake(arms, mirror, right, left, body, duration):
    """Samples per frame for every node: the right arm from `right`, the left from `left`, the body the mean of
    `body`.

    Each arm keeps the place its own source gives it relative to the eye (Camera01), not relative to the spine: the
    attack clips twist the spine far round while the engine's eye only follows Camera01's position (it always looks
    straight ahead), so an idle arm's local pose on an attacking spine swung out of view behind the eye. The clavicle's
    local is solved against the baked body; everything below it keeps its source's locals."""
    right_nodes = arms.subtree('Bip01 R Clavicle')
    left_nodes = arms.subtree('Bip01 L Clavicle')
    roots = {arms.index['Bip01 R Clavicle']: 0, arms.index['Bip01 L Clavicle']: 1}
    camera = arms.index['Camera01']
    frames = int(np.ceil(duration * FPS - 1e-6))
    times = np.array([min(k / FPS, duration) for k in range(frames + 1)])
    count = len(arms.nodes)
    out_t = np.zeros((len(times), count, 3))
    out_q = np.zeros((len(times), count, 4))
    out_s = np.zeros((len(times), count, 3))
    for f, t in enumerate(times):
        r = right.sample(arms, mirror, t)
        l = left.sample(arms, mirror, t)
        b = mean_pose([src.sample(arms, mirror, t) for src in body])
        pose = [b[0].copy(), b[1].copy(), b[2].copy()]
        for i in range(count):
            source = r if i in right_nodes else l if i in left_nodes else None
            if source is not None:
                pose[0][i], pose[1][i], pose[2][i] = source[0][i], source[1][i], source[2][i]
        body_world = arms.world(b)
        for root, side in roots.items():
            source = (right, left)[side]
            nodes = (right_nodes, left_nodes)[side]
            arm = eye_relative_arm(arms, (r, l)[side], body_world, root, camera, nodes)
            share = source.settle_share(t)
            if share > 0.0:
                guard = eye_relative_arm(arms, source.guard().sample(arms, mirror, t), body_world, root, camera, nodes)
                arm = blend_pose(arm, guard, share, nodes)
            for i in nodes:
                pose[0][i], pose[1][i], pose[2][i] = arm[0][i], arm[1][i], arm[2][i]
        out_t[f], out_q[f], out_s[f] = pose[0], pose[1], pose[2]
    # One hemisphere per channel: no flips between frames.
    for f in range(1, len(times)):
        flip = np.sum(out_q[f] * out_q[f - 1], axis=1) < 0
        out_q[f][flip] *= -1
    return times, out_t, out_q, out_s


class Writer:
    def __init__(self, j, blob):
        self.j, self.blob = j, blob

    def accessor(self, array, kind):
        array = np.ascontiguousarray(array, dtype=np.float32)
        while len(self.blob) % 4:
            self.blob.append(0)
        self.j['bufferViews'].append({'buffer': 0, 'byteOffset': len(self.blob), 'byteLength': array.nbytes})
        self.blob.extend(array.tobytes())
        acc = {'bufferView': len(self.j['bufferViews']) - 1, 'componentType': 5126, 'count': len(array),
               'type': kind}
        if kind == 'SCALAR':
            acc['min'], acc['max'] = [float(array.min())], [float(array.max())]
        self.j['accessors'].append(acc)
        return len(self.j['accessors']) - 1

    def animation(self, name, arms, times, out_t, out_q, out_s):
        animation = {'name': name, 'channels': [], 'samplers': []}
        input_index = self.accessor(times, 'SCALAR')
        for i, node in enumerate(arms.nodes):
            if 'mesh' in node:
                continue
            for path, values, kind in (('translation', out_t[:, i], 'VEC3'), ('rotation', out_q[:, i], 'VEC4'),
                                       ('scale', out_s[:, i], 'VEC3')):
                rest = {'translation': arms.rest_t, 'rotation': arms.rest_q, 'scale': arms.rest_s}[path][i]
                if path != 'rotation' and np.abs(values - rest).max() < 1e-6:
                    continue
                if path == 'rotation' and np.abs(np.abs(np.sum(values * rest, axis=1)) - 1).max() < 1e-9:
                    continue
                animation['samplers'].append({'input': input_index, 'output': self.accessor(values, kind),
                                              'interpolation': 'LINEAR'})
                animation['channels'].append({'sampler': len(animation['samplers']) - 1,
                                              'target': {'node': i, 'path': path}})
        self.j['animations'].append(animation)


def keys_of(textkeys, clip, delay=0.0, swap_chain=False, drop_chain=False, hit_from=None):
    out = []
    for time, text in textkeys[clip]['keys']:
        lowered = text.strip().lower()
        if lowered in ('start', 'end'):
            continue
        if lowered in ('a:l', 'a:r'):
            if drop_chain:
                continue
            if swap_chain:
                text = 'a:R' if lowered == 'a:l' else 'a:L'
        if lowered == 'hit' and hit_from is not None:
            continue
        out.append([time + delay, text])
    if hit_from is not None:
        out.append([hit_from, 'Hit'])
    return sorted(out, key=lambda k: k[0])


def plan(arms, textkeys):
    """(name, right, left, body sources, duration, keys) for every dual clip."""
    clips = []

    def both(name, clip, opposite=None, loop=False):
        # Both arms alike: the right arm plays the clip, the left its mirror (of the clip that moves the other way
        # for a sideways step), the body the mean of the two.
        mirrored = Source(opposite or clip, mirrored=True, loop=loop)
        clips.append((name, Source(clip, loop=loop), mirrored, [Source(clip, loop=loop), mirrored],
                      arms.duration(clip), keys_of(textkeys, clip)))

    both('dualidle', 'onehandidle', loop=True)
    for move in ('forward', 'backward', 'fastforward', 'fastbackward'):
        both('dual' + move, 'onehand' + move, loop=True)
    for move, other in (('left', 'right'), ('right', 'left'), ('fastleft', 'fastright'), ('fastright', 'fastleft')):
        both('dual' + move, 'onehand' + move, 'onehand' + other, loop=True)
    for clip in ('blockidle', 'blockhit'):
        both('dual' + clip, 'onehand' + clip, loop=clip == 'blockidle')
    for clip in ('equip', 'unequip'):
        # The right hand first, the left DRAW_DELAY later; the keys (Attach, Detach) are the right hand's.
        source = 'onehand' + clip
        late = Source(source, mirrored=True, delay=DRAW_DELAY)
        clips.append(('dual' + clip, Source(source), late, [Source(source), late],
                      arms.duration(source) + DRAW_DELAY, keys_of(textkeys, source)))

    def hit_of(clip):
        return next(t for t, k in textkeys[clip]['keys'] if k.strip().lower() == 'hit')

    def lead(name, clip, hand, swap_chain=False):
        # One hand cuts (Oblivion's clip, or its mirror for the left) and settles back into its guard after the blow;
        # the other waits raised.
        cutting = Source(clip, mirrored=hand == 'L', settle=(hit_of(clip) + SETTLE_FROM, arms.duration(clip)))
        other = Source('onehandidle', mirrored=hand == 'R', loop=True)
        right, left = (cutting, other) if hand == 'R' else (other, cutting)
        clips.append((name, right, left, [cutting], arms.duration(clip),
                      keys_of(textkeys, clip, swap_chain=swap_chain)))

    for suffix in ('', '_chop'):
        clip = 'onehandattackright' + suffix
        # The right hand cuts, the left waits raised; then the mirror: the left hand cuts, the right waits.
        lead('dualattackright' + suffix, clip, 'R')
        lead('dualattackleft' + suffix, clip, 'L', swap_chain=True)
    # Sideways power attacks: moving left the right hand sweeps (Oblivion's own), moving right the left hand sweeps
    # (its mirror). The lunge is the right hand's, the step-back cut the left's: both arms at once met in the middle.
    lead('dualattackleftpower', 'onehandattackleftpower', 'R')
    lead('dualattackrightpower', 'onehandattackleftpower', 'L')
    lead('dualattackforwardpower', 'onehandattackforwardpower', 'R')
    lead('dualattackbackpower', 'onehandattackbackpower', 'L')
    # The cross slash closing a round: both hands cut inward, the left a moment after the right; the blow lands at the
    # right blade's contact.
    clip = 'onehandattackright'
    hit = next(t for t, k in textkeys[clip]['keys'] if k.strip().lower() == 'hit')
    clips.append(('dualattackpower', Source(clip), Source(clip, mirrored=True, delay=CROSS_DELAY),
                  [Source(clip), Source(clip, mirrored=True, delay=CROSS_DELAY)],
                  arms.duration(clip) + CROSS_DELAY,
                  keys_of(textkeys, clip, drop_chain=True, hit_from=hit)))
    return clips


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    in_glb, in_keys, out_glb, out_keys = sys.argv[1:]
    j, blob = load_glb(in_glb)
    textkeys = json.load(open(in_keys))
    names = {a['name'] for a in j.get('animations', [])}
    if any(n.startswith('dual') for n in names) or any(n.get('name') == OFF_HAND_NODE for n in j['nodes']):
        print(f'{in_glb} already holds dual clips: bake from the pristine copy')
        return 1
    arms = Arms(j, blob)
    mirror = Mirror(arms)
    print(f'rest symmetry: worst mirrored joint offset {mirror.symmetry_error():.4f} units')
    add_off_hand_node(arms, mirror)
    mirror = Mirror(arms)
    writer = Writer(j, blob)
    for name, right, left, body, duration, keys in plan(arms, textkeys):
        times, out_t, out_q, out_s = bake(arms, mirror, right, left, body, duration)
        writer.animation(name, arms, times, out_t, out_q, out_s)
        textkeys[name] = {'length': float(duration),
                          'keys': [[0.0, 'start']] + keys + [[float(duration), 'end']]}
        print(f'{name}: {duration:.3f} s, {len(times)} frames, keys {keys}')
    save_glb(out_glb, j, writer.blob)
    with open(out_keys, 'w') as stream:
        json.dump(textkeys, stream, indent=1)
    print(f'wrote {out_glb} ({len(j["animations"])} clips) and {out_keys}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
