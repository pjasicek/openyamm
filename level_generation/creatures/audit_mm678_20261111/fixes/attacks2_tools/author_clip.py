#!/usr/bin/env python3
"""Author a clip on a creature's own rig from a recipe, without Blender (attacks-2 stream, 2026-11-11).

    author_clip.py <in.glb> <recipe.py> <out.glb> [--fps 30]

The recipe is a Python file defining some of:

- CLIP = 'Attack'      the clip written (replaced in place when it exists, else appended);
- SOURCE = 'Attack'    the base clip sampled under the layers (None: the rest pose);
- LENGTH               new length in seconds (default: the base clip's, so the game's attack timing stays);
- TIMEWARP = [(t_new, t_source), ...]   monotone map, PCHIP (default identity scaled to the lengths);
- AMPLIFY = {'glob': factor}            local rotation/translation deviation from the base clip's first frame,
                                        scaled per joint (1 = unchanged);
- LAYERS = [{'joints': {'name or glob': weight}, 'axis': [x, y, z] or 'joint-local:x', 'keys': [(t, deg), ...]}]
                                        a rotation about a model-space axis (or the joint's own rest axis) through
                                        the joint's pivot, angle = weight x key curve (PCHIP). Layers compose in
                                        order; children inherit;
- MOVES = [{'joint': name, 'keys': [(t, [dx, dy, dz]), ...]}]
                                        a model-space offset of the joint (metres, in the GLB's own units);
- FOLLOW = {'follower': 'leader'}      keep a node's transform relative to another node as in the base clip (a prop
                                        animated under the root, e.g. the Salamander's Polearm, stays in the hands);
- PLANT = [('Thigh_L', 'Shin_L', 'HindPaw_L'), ...]   two-bone IK after the layers: each end joint keeps its
                                        base-clip world position and orientation (feet stay where the base clip put
                                        them while the body lunges), the knee bending in its current plane; an entry
                                        {'chain': (a, b, c), 'keys': [(t, [dx, dy, dz])]} moves that target (a step);
- FLOOR = {'joint': 'Root', 'min': 0.0}  after everything, lift that joint (model +Y) when the lowest visible LOD0
                                        point of the frame is below min (rough rollers turning, a lunge dipping);
- POST(t, local, ctx)                   optional hook editing local TRS {node: [T, R, S]} after everything
                                        (ctx['base_world']: world matrices of the base clip at this time).

Model space is the GLB scene's: +Y up. Key curves start and end at zero unless the recipe says otherwise, so the clip
still begins and ends on the base clip's pose. Every channel of the clip is resampled at --fps (plus the end key),
LINEAR; quaternion signs are kept continuous. Other clips, meshes and nodes stay byte for byte (new accessors are
appended; the replaced clip's old accessors stay unused in the buffer).
"""
import argparse
import fnmatch
import runpy
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def axis_angle(axis, degrees):
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    a = np.radians(degrees)
    x, y, z = axis
    c, s, k = np.cos(a), np.sin(a), 1 - np.cos(a)
    return np.array([[c + x * x * k, x * y * k - z * s, x * z * k + y * s],
                     [y * x * k + z * s, c + y * y * k, y * z * k - x * s],
                     [z * x * k - y * s, z * y * k + x * s, c + z * z * k]])


def curve(keys):
    keys = sorted(keys, key=lambda k: k[0])
    t = np.array([k[0] for k in keys], dtype=float)
    v = np.array([k[1] for k in keys], dtype=float)
    if len(t) == 1:
        return lambda x: v[0] * np.ones_like(np.asarray(x, dtype=float))[..., None] if v.ndim > 1 else v[0]
    f = PchipInterpolator(t, v, axis=0, extrapolate=False)

    def call(x):
        x = np.clip(x, t[0], t[-1])
        return f(x)
    return call


def match(names, pattern_weights):
    out = {}
    for pattern, weight in pattern_weights.items():
        for index, name in names.items():
            if name == pattern or fnmatch.fnmatchcase(name, pattern):
                out[index] = weight
    return out


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


def qpow(q, f):
    """q^f for a unit quaternion (rotation angle scaled by f)."""
    q = q / np.linalg.norm(q)
    if q[3] < 0:
        q = -q
    w = np.clip(q[3], -1, 1)
    angle = 2 * np.arccos(w)
    s = np.sqrt(max(1 - w * w, 0))
    if s < 1e-8:
        return np.array([0.0, 0.0, 0.0, 1.0])
    axis = q[:3] / s
    half = angle * f / 2
    return np.concatenate([axis * np.sin(half), [np.cos(half)]])


def qinv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]])


def rotation_between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-12:
        return np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * (1 / (1 + c))


def set_world_rotation(model, local, world, node, rot):
    """Give node the world rotation rot (3x3) by changing its local rotation; returns the new world matrices."""
    parent = model.parent[node]
    pw = world[parent][:3, :3] if parent >= 0 else np.eye(3)
    prot = pw / np.maximum(np.linalg.norm(pw, axis=0, keepdims=True), 1e-20)
    local[node] = [local[node][0], glb_pose.matrix_quaternion(prot.T @ rot), local[node][2]]
    return model.world(local)


def two_bone(model, local, base_world, chain, offset):
    a, b, c = chain
    for n in chain:
        local.setdefault(n, [p.copy() for p in model.rest[n]])
    world = model.world(local)
    pa, pb, pc = (world[n][:3, 3] for n in chain)
    target = base_world[c][:3, 3] + offset
    l1 = np.linalg.norm(base_world[b][:3, 3] - base_world[a][:3, 3])
    l2 = np.linalg.norm(base_world[c][:3, 3] - base_world[b][:3, 3])
    d = target - pa
    dist = np.clip(np.linalg.norm(d), abs(l1 - l2) + 1e-6, l1 + l2 - 1e-6)
    dn = d / np.linalg.norm(d)
    pole = pb - pa - np.dot(pb - pa, dn) * dn
    if np.linalg.norm(pole) < 1e-9:
        pole = np.cross(dn, [1.0, 0.0, 0.0])
    pole = pole / np.linalg.norm(pole)
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = np.sqrt(max(l1 * l1 - x * x, 0.0))
    knee = pa + dn * x + pole * h
    unit = lambda m: m[:3, :3] / np.maximum(np.linalg.norm(m[:3, :3], axis=0, keepdims=True), 1e-20)
    ra = rotation_between(pb - pa, knee - pa) @ unit(world[a])
    world = set_world_rotation(model, local, world, a, ra)
    pb2, pc2 = world[b][:3, 3], world[c][:3, 3]
    rb = rotation_between(pc2 - pb2, pa + dn * dist - pb2) @ unit(world[b])
    world = set_world_rotation(model, local, world, b, rb)
    set_world_rotation(model, local, world, c, unit(base_world[c]))


def build(model, recipe, fps):
    glb = model.glb
    doc = glb.json
    names = {i: n.get('name', str(i)) for i, n in enumerate(doc['nodes'])}
    by_name = {v: k for k, v in names.items()}
    source = recipe.get('SOURCE', recipe.get('CLIP', 'Attack'))
    src_times = model.clip_times(source) if source else [0.0, 1.0]
    src_len = src_times[-1] - src_times[0]
    length = float(recipe.get('LENGTH', src_len))
    warp_keys = recipe.get('TIMEWARP') or [(0.0, src_times[0]), (length, src_times[-1])]
    warp = curve(warp_keys)
    n = int(round(length * fps))
    times = np.linspace(0.0, length, n + 1)
    amplify = match(names, recipe.get('AMPLIFY', {}))
    base0 = model.sample(source, src_times[0]) if source else {}
    layers = []
    for layer in recipe.get('LAYERS', []):
        joints = match(names, layer['joints'])
        axis = layer['axis']
        layers.append((joints, axis, curve(layer['keys'])))
    moves = [(by_name[m['joint']], curve(m['keys'])) for m in recipe.get('MOVES', [])]
    post = recipe.get('POST')
    follow = [(by_name[f], by_name[l]) for f, l in recipe.get('FOLLOW', {}).items()]
    plant = []
    for chain in recipe.get('PLANT', []):
        if isinstance(chain, dict):
            plant.append((tuple(by_name[j] for j in chain['chain']), curve(chain['keys'])))
        else:
            plant.append((tuple(by_name[j] for j in chain), None))
    animated = set()
    if source:
        anim = doc['animations'][model.clips[source]]
        animated = {c['target']['node'] for c in anim['channels'] if c['target']['path'] != 'weights'}
    for joints, _, _ in layers:
        animated |= set(joints)
    for joint, _ in moves:
        animated.add(joint)
    for f, _ in follow:
        animated.add(f)
    for chain, _ in plant:
        animated |= set(chain)
    animated = sorted(animated)
    rest_world = model.world({})
    out = {node: ([], [], []) for node in animated}
    for t in times:
        st = float(warp(t))
        local = model.sample(source, st) if source else {}
        local = {k: [p.copy() for p in v] for k, v in local.items()}
        for node, factor in amplify.items():
            if node not in local or node not in base0:
                continue
            t0, r0, s0 = base0[node]
            tr, rr, sr = local[node]
            delta = qmul(rr, qinv(r0))
            local[node][1] = qmul(qpow(delta, factor), r0)
            local[node][0] = t0 + factor * (tr - t0)
        for node in animated:
            local.setdefault(node, [p.copy() for p in model.rest[node]])
        base_world_all = model.world(local) if (plant or post) else None
        base_world = None
        if follow:
            # Followers measured at unit scale: a prop hidden by a zero scale (Medusa's parked arrow) still has a frame.
            unit = dict(local)
            for f, _ in follow:
                unit[f] = [local[f][0], local[f][1], np.ones(3)]
            base_world = model.world(unit)
        ctx = {'names': names, 'by_name': by_name, 'model': model, 'time': t, 'source_time': st,
               'rest_world': rest_world, 'base_world': base_world_all}
        # Forward kinematics with layer rotations and moves.
        world = np.zeros((len(model.rest), 4, 4))
        rot_layers = {}
        for joints, axis, f in layers:
            angle = float(np.asarray(f(t)).reshape(-1)[0])
            for node, weight in joints.items():
                rot_layers.setdefault(node, []).append((axis, angle * weight))
        move_at = {node: np.asarray(f(t), dtype=float).reshape(3) for node, f in moves}
        for index in model.order:
            trs = local.get(index, model.rest[index])
            parent = model.parent[index]
            pw = world[parent] if parent >= 0 else np.eye(4)
            prot = pw[:3, :3] / np.maximum(np.linalg.norm(pw[:3, :3], axis=0, keepdims=True), 1e-20)
            pscale = np.linalg.norm(pw[:3, :3], axis=0)
            if index in rot_layers or index in move_at:
                trs = [p.copy() for p in trs]
                if index in rot_layers:
                    d = np.eye(3)
                    for axis, angle in rot_layers[index]:
                        if isinstance(axis, str) and axis.startswith('joint-local:'):
                            k = 'xyz'.index(axis.split(':')[1])
                            rw = rest_world[index][:3, :3]
                            rw = rw / np.maximum(np.linalg.norm(rw, axis=0, keepdims=True), 1e-20)
                            ax = rw[:, k]
                        else:
                            ax = axis
                        d = axis_angle(ax, angle) @ d
                    m = prot.T @ d @ prot @ glb_pose.quaternion_matrix(trs[1])
                    trs[1] = glb_pose.matrix_quaternion(m)
                if index in move_at:
                    trs[0] = trs[0] + (prot.T @ move_at[index]) / np.maximum(pscale, 1e-12)
                local[index] = trs
            world[index] = pw @ glb_pose.trs_matrix(*trs)
        for f, l in follow:
            target = world[l] @ np.linalg.inv(base_world[l]) @ base_world[f]
            parent = model.parent[f]
            rel = np.linalg.inv(world[parent]) @ target if parent >= 0 else target
            scale = np.maximum(np.linalg.norm(rel[:3, :3], axis=0), 1e-12)
            local[f] = [rel[:3, 3].copy(), glb_pose.matrix_quaternion(rel[:3, :3] / scale), local[f][2]]
        for chain, offset in plant:
            two_bone(model, local, base_world_all, chain,
                     np.asarray(offset(t), dtype=float).reshape(3) if offset else np.zeros(3))
        floor = recipe.get('FLOOR')
        if floor:
            node = by_name[floor['joint']]
            w2 = model.world(local)
            posed = model.skinned_positions(w2)
            keep = model.visible_vertices(posed)
            low = min(float(p[k][:, 1].min()) for (p, _), k in zip(posed, keep) if len(k))
            if low < floor.get('min', 0.0):
                parent = model.parent[node]
                pw = w2[parent] if parent >= 0 else np.eye(4)
                prot = pw[:3, :3] / np.maximum(np.linalg.norm(pw[:3, :3], axis=0, keepdims=True), 1e-20)
                pscale = np.linalg.norm(pw[:3, :3], axis=0)
                lift = np.array([0.0, floor.get('min', 0.0) - low, 0.0])
                local[node] = [local[node][0] + (prot.T @ lift) / np.maximum(pscale, 1e-12), local[node][1],
                               local[node][2]]
        if post:
            post(t, local, ctx)
        for node in animated:
            tr, rr, sr = local[node]
            rr = rr / np.linalg.norm(rr)
            prev = out[node][1]
            if prev and float(np.dot(prev[-1], rr)) < 0:
                rr = -rr
            out[node][0].append(np.asarray(tr, dtype=float))
            out[node][1].append(rr)
            out[node][2].append(np.asarray(sr, dtype=float))
    return times, out


def write(glb, model, recipe, times, out, path):
    doc = glb.json
    clip = recipe.get('CLIP', 'Attack')
    t_acc = glb.append_accessor(times.astype(np.float32)[:, None], 'SCALAR')
    samplers, channels = [], []
    old = doc['animations'][model.clips[clip]] if clip in model.clips else None
    paths_of = {}
    if old:
        for c in old['channels']:
            paths_of.setdefault(c['target']['node'], set()).add(c['target']['path'])
    for node, (ts, rs, ss) in out.items():
        wanted = paths_of.get(node, {'rotation'}) | ({'translation'} if node not in paths_of else set())
        for path_name, values, kind in (('translation', ts, 'VEC3'), ('rotation', rs, 'VEC4'), ('scale', ss, 'VEC3')):
            if path_name not in wanted and not (path_name == 'translation' and node in recipe.get('_moved', ())):
                continue
            acc = glb.append_accessor(np.array(values), kind)
            samplers.append({'input': t_acc, 'output': acc, 'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': node, 'path': path_name}})
    anim = {'name': clip, 'samplers': samplers, 'channels': channels}
    if old is not None:
        doc['animations'][model.clips[clip]] = anim
    else:
        doc['animations'].append(anim)
    glb.write(path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('recipe')
    p.add_argument('output')
    p.add_argument('--fps', type=float, default=30)
    a = p.parse_args()
    recipe = runpy.run_path(a.recipe)
    glb = glb_pose.Glb(a.input)
    model = glb_pose.Model(glb)
    names = {i: n.get('name', str(i)) for i, n in enumerate(glb.json['nodes'])}
    by_name = {v: k for k, v in names.items()}
    recipe['_moved'] = {by_name[m['joint']] for m in recipe.get('MOVES', [])}
    times, out = build(model, recipe, a.fps)
    write(glb, model, recipe, times, out, a.output)
    print(f"{a.output}: {recipe.get('CLIP', 'Attack')} {times[-1]:.3f} s, {len(times)} keys, {len(out)} nodes")


if __name__ == '__main__':
    main()
