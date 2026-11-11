#!/usr/bin/env python3
"""MM9 props whose LithTech models move rigid pieces (a chest's lid, a bell and its clapper, the Lich engine's rings, a
windmill's sails) as animated decorations (DecorationModelSet: a binding's `parts`, or a binding model that moves as a
whole; evt.PlayDecorationClip, a chest's lid opening with its chest, `idle` loops). For each prop in PROPS:

  1. its finished decoration (the installed source, kept once as work/originals/<glb>, since the install below
     replaces it) is matched to its raw import (the props project's work/raw/<raw>/<raw>.glb: the ABC pieces at their
     bind pose with every clip): the axis permutation, scale and offset that map the raw import onto the finished
     model's LOD0 corners (checked within TOLERANCE), and each triangle of every LOD goes to the piece its corners lie on;
  2. the pieces are grouped by how they move over the prop's clips (a piece every clip leaves still is the body);
  3. the body keeps the still pieces (less DROP: pieces every placement hides), each moving group becomes a part on
     one node at its first piece's bone with the clips sampled at SAMPLE_RATE from the raw import (glTF convention:
     translation lerp, rotation slerp, as LithTech interpolates), carried into asset space; a prop with no still piece
     moves as a whole: its model keeps its one node and takes the clips itself;
  4. --install installs body and parts (tools/install_model.py --world mm9) and rewrites every binding of the model in
     worlds/mm9/models/indoor_decorations.yml and decorations.yml under the shared lock: `parts`, IDLE's clip, and its height times the
     body's share of the whole (so the scale stays; skipped for a binding that already lists the parts).

Clip names are lower case (MM9's Open/Closed/Down... -> open/close/down...; RENAME). Usage:
    python3 prop_parts.py [prop ...]            # build into work/, report
    python3 prop_parts.py [prop ...] --install
"""
import fcntl
import itertools
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
PROPS_DIR = REPO / 'level_generation/props'
SOURCE = REPO / 'assets_source/worlds/mm9/models'
MANIFESTS = [REPO / 'assets_dev/worlds/mm9/models/indoor_decorations.yml',
             REPO / 'assets_dev/worlds/mm9/models/decorations.yml']
LOCK = REPO / 'level_generation/projects/mm9r_common/locks/mm9_decorations.lock'
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(PROPS_DIR / 'mm9_isleofashes_claude/scripts'))
from link_static_model_lods import read_glb, write_glb  # noqa: E402
from glbio import array  # noqa: E402

TOLERANCE = 0.005           # of the model's largest extent: the worst corner off its raw vertex
SAMPLE_RATE = 30.0
STILL = 1e-4                # a motion this close to identity (matrix entries) is no motion
# prop: (model file in assets_source, raw import under level_generation/props, pieces every placement hides,
#        original (None: the installed source))
PROPS = {
    'coffinfancy': ('mm9_deco_coffinfancy.glb', 'mm9_beethoven_claude/work/raw/coffinfancy/coffinfancy.glb',
                    {'Skeleton'}, 'mm9_beethoven_claude/work/mm9_deco_coffinfancy.glb'),
    'coffinraised': ('mm9_deco_coffinraised.glb', 'mm9_beethoven_claude/work/raw/coffinraised/coffinraised.glb',
                     set(), None),
    'chest': ('mm9_deco_chest.glb', 'mm9_anskramkeep_claude/work/raw/chest1/chest1.glb', set(), None),
    'chest1': ('mm9_deco_chest1.glb', 'mm9_anskramkeep_claude/work/raw/chest1/chest1.glb', set(), None),
    'chest3': ('mm9_deco_chest3.glb', 'mm9_templeofhonk_claude/work/raw/chest3/chest3.glb', set(), None),
    'chest5': ('mm9_deco_chest5.glb', 'mm9_chasmofthedead_claude/work/raw/chest5/chest5.glb', set(), None),
    'blackchest': ('mm9_deco_blackchest.glb', 'mm9_lichlab_claude/work/raw/blackchest/blackchest.glb', set(), None),
    'chestrusty01': ('mm9_deco_chestrusty01.glb', 'mm9_yanmirsfort_claude/work/raw/chestrusty01/chestrusty01.glb',
                     set(), None),
    'bell': ('mm9_deco_bell.glb', 'mm9_lindisfarnemonastery_claude/work/raw/bell/bell.glb', set(), None),
    'lichengine': ('mm9_deco_lichengine.glb', 'mm9_lichlab_claude/work/raw/lichengine/lichengine.glb', set(), None),
    'switch02': ('mm9_deco_switch02.glb', 'mm9_lichlab_claude/work/raw/switch02/switch02.glb', set(), None),
    'switch03': ('mm9_deco_switch03.glb', 'mm9_1000terrors_claude/work/raw/switch03/switch03.glb', set(), None),
    'windmillp335': ('mm9_deco_windmillp335.glb',
                     'mm9_outdoor_regions_claude/work/raw/windmillp335/windmillp335.glb', set(), None),
    'statstone': ('mm9_deco_statstone.glb', 'mm9_outdoor_regions_claude/work/raw/statstone/statstone.glb', set(),
                  None),
    'statstonegreen': ('mm9_deco_statstonegreen.glb',
                       'mm9_outdoor_regions_claude/work/raw/statstonegreen/statstonegreen.glb', set(), None),
    'statstoneplain': ('mm9_deco_statstoneplain.glb',
                       'mm9_outdoor_regions_claude/work/raw/statstoneplain/statstoneplain.glb', set(), None),
    'statstonepurple': ('mm9_deco_statstonepurple.glb',
                        'mm9_outdoor_regions_claude/work/raw/statstonepurple/statstonepurple.glb', set(), None),
    'statstoneyellow': ('mm9_deco_statstoneyellow.glb',
                        'mm9_outdoor_regions_claude/work/raw/statstoneyellow/statstoneyellow.glb', set(), None),
}
# Props built in an animation pose (their props project's POSES): prop -> (clip, seconds), the rest the parts move from.
POSE = {'bell': ('static_model', 0.0), 'windmillp335': ('static_model', 0.0)}
# Tilted variants (the outdoor regions' TILTS, baked in by their build): prop -> the tilt's angle (radians).
TILT = {'windmillp335': 2 * np.pi - 5.85383415222168}
# Clips loop without a script (PropAnim.scr's LoopAnim): prop -> clip.
IDLE = {'windmillp335': 'slow', 'statstone': 'rotate', 'statstonegreen': 'rotate', 'statstoneplain': 'rotate',
        'statstonepurple': 'rotate', 'statstoneyellow': 'rotate'}
RENAME = {'closed': 'close'}
SKIP_CLIPS = re.compile(r'^(ns.*|static.*|.*setup)$', re.I)


def mat4s(document, binary, index):
    """A MAT4 accessor (column-major floats) as (n, 4, 4) row-major matrices."""
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    values = np.frombuffer(binary, np.float32, accessor['count'] * 16, start)
    return values.reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)


def quat_matrix(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def trs(translation, rotation, scale=(1, 1, 1)):
    m = np.identity(4)
    m[:3, :3] = quat_matrix(rotation) @ np.diag(scale)
    m[:3, 3] = translation
    return m


def matrix_quat(r):
    """A proper rotation matrix as (x, y, z, w)."""
    w = np.sqrt(max(0.0, 1 + r[0, 0] + r[1, 1] + r[2, 2])) / 2
    x = np.copysign(np.sqrt(max(0.0, 1 + r[0, 0] - r[1, 1] - r[2, 2])) / 2, r[2, 1] - r[1, 2])
    y = np.copysign(np.sqrt(max(0.0, 1 - r[0, 0] + r[1, 1] - r[2, 2])) / 2, r[0, 2] - r[2, 0])
    z = np.copysign(np.sqrt(max(0.0, 1 - r[0, 0] - r[1, 1] + r[2, 2])) / 2, r[1, 0] - r[0, 1])
    q = np.array([x, y, z, w])
    return q / np.linalg.norm(q)


def slerp(a, b, t):
    a, b = np.array(a, float), np.array(b, float)
    if np.dot(a, b) < 0:
        b = -b
    d = np.clip(np.dot(a, b), -1, 1)
    if d > 0.9995:
        q = a + t * (b - a)
    else:
        th = np.arccos(d)
        q = (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)
    return q / np.linalg.norm(q)


class Raw:
    """The raw import: each piece's world vertices at rest and its motion (4x4) at a clip's time."""

    def __init__(self, path, pose=None):
        self.doc, self.bin = read_glb(path)
        self.pose = pose or (None, 0.0)
        self.parent = {c: i for i, n in enumerate(self.doc['nodes']) for c in n.get('children', [])}
        self.tracks = {}
        for animation in self.doc.get('animations', []):
            tracks = {}
            for channel in animation['channels']:
                sampler = animation['samplers'][channel['sampler']]
                tracks[(channel['target']['node'], channel['target']['path'])] = (
                    array(self.doc, self.bin, sampler['input']).ravel(), array(self.doc, self.bin, sampler['output']))
            self.tracks[animation['name']] = tracks

    def duration(self, clip):
        return max(float(times[-1]) for times, _ in self.tracks[clip].values())

    def local(self, index, clip=None, time=0.0):
        node = self.doc['nodes'][index]
        values = {'translation': node.get('translation', [0, 0, 0]), 'rotation': node.get('rotation', [0, 0, 0, 1]),
                  'scale': node.get('scale', [1, 1, 1])}
        for path in values:
            track = self.tracks.get(clip, {}).get((index, path)) if clip else None
            if track is None:
                continue
            times, out = track
            if time <= times[0]:
                values[path] = out[0]
            elif time >= times[-1]:
                values[path] = out[-1]
            else:
                k = int(np.searchsorted(times, time)) - 1
                t = (time - times[k]) / (times[k + 1] - times[k])
                values[path] = slerp(out[k], out[k + 1], t) if path == 'rotation' else out[k] + t * (out[k + 1] - out[k])
        rotation = np.array(values['rotation'], float)       # some ABC keys are a little off unit length
        return trs(values['translation'], rotation / np.linalg.norm(rotation), values['scale'])

    def world(self, index, clip=None, time=0.0):
        m = self.local(index, clip, time)
        while index in self.parent:
            index = self.parent[index]
            m = self.local(index, clip, time) @ m
        return m

    def pieces(self):
        """{piece: (rest points (n, 3), the node whose motion moves it)}: a rigid piece's mesh node, a skinned one's
        joint (each raw piece is weighted to one bone)."""
        out = {}
        for index, node in enumerate(self.doc['nodes']):
            if 'mesh' not in node:
                continue
            mesh = self.doc['meshes'][node['mesh']]
            points, mover = [], index
            for prim in mesh['primitives']:
                p = array(self.doc, self.bin, prim['attributes']['POSITION']).astype(float)
                if 'skin' in node:
                    skin = self.doc['skins'][node['skin']]
                    joints = array(self.doc, self.bin, prim['attributes']['JOINTS_0']).astype(int)
                    weights = array(self.doc, self.bin, prim['attributes']['WEIGHTS_0'])
                    used = set(joints[weights > 0.01].ravel().tolist())
                    if len(used) != 1:
                        raise SystemExit(f'{mesh["name"]}: a skinned piece on {len(used)} bones (not rigid)')
                    slot = used.pop()
                    mover = skin['joints'][slot]
                    ibm = mat4s(self.doc, self.bin, skin['inverseBindMatrices'])[slot]
                    m = self.world(mover, *self.pose) @ ibm
                else:
                    m = self.world(index, *self.pose)
                points.append(p @ m[:3, :3].T + m[:3, 3])
            out[mesh['name']] = (np.concatenate(points), mover)
        return out

    def motion(self, node, clip, time):
        return self.world(node, clip, time) @ np.linalg.inv(self.world(node, *self.pose))


def nearest(points, cloud):
    best = np.full(len(points), np.inf)
    which = np.zeros(len(points), int)
    for start in range(0, len(cloud), 512):
        d = np.linalg.norm(points[:, None, :] - cloud[None, start:start + 512, :], axis=2)
        k = d.argmin(1)
        v = d[np.arange(len(points)), k]
        better = v < best
        best[better], which[better] = v[better], k[better] + start
    return best, which


def axis_rotation(axis, angle):
    c, n = np.cos(angle), np.sin(angle)
    i, j = [k for k in range(3) if k != axis]
    r = np.identity(3)
    r[i, i], r[i, j], r[j, i], r[j, j] = c, -n, n, c
    return r


def similarity(source, target, reflect):
    """Least-squares x -> a x + o (a = s R, R a rotation, or a reflection when reflect) from paired points."""
    ms, mt = source.mean(0), target.mean(0)
    u, sv, vt = np.linalg.svd((target - mt).T @ (source - ms))
    d = np.identity(3)
    d[2, 2] = np.sign(np.linalg.det(u @ vt)) * (-1 if reflect else 1)
    r = u @ d @ vt
    s = float(np.trace(np.diag(sv) @ d) / ((source - ms) ** 2).sum())
    return s * r, mt - s * r @ ms


def fit(raw_points, asset_points, tilt=0.0):
    """x -> a x + o mapping the raw pieces onto the finished corners: started from each signed axis permutation (the
    builds mirror and turn the raw frame), turned by a baked tilt (a tilted variant's pitch/roll: tried about each axis
    both ways), scaled and placed by the bounding boxes, then refined by nearest-corner least squares (ICP)."""
    best = None
    lo, hi = asset_points.min(0), asset_points.max(0)
    tilts = [np.identity(3)] + [axis_rotation(k, sign * tilt) for k in range(3) for sign in (1, -1) if tilt]
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            p = np.zeros((3, 3))
            for row, (col, sign) in enumerate(zip(perm, signs)):
                p[row, col] = sign
            for r in tilts:
                mapped = raw_points @ (r @ p).T
                extent = np.maximum(mapped.max(0) - mapped.min(0), 1e-9)
                s = float(np.median((hi - lo) / extent))
                a = s * r @ p
                o = (lo + hi) / 2 - s * (mapped.max(0) + mapped.min(0)) / 2
                error = float(np.median(nearest(asset_points, raw_points @ a.T + o)[0]))
                if best is None or error < best[0]:
                    best = (error, a, o)
    _, a, o = best
    reflect = np.linalg.det(a) < 0
    for _ in range(8):
        distance, which = nearest(raw_points @ a.T + o, asset_points)
        close = distance <= np.percentile(distance, 80)
        a, o = similarity(raw_points[close], asset_points[which[close]], reflect)
    return a, o


def lod_primitives(doc, binary):
    for m, mesh in enumerate(doc['meshes']):
        for p, prim in enumerate(mesh['primitives']):
            yield m, p, prim


def build(doc, binary, keep, offset=None, translation=None, clips=None):
    """A GLB of doc's meshes with only the triangles keep[(mesh, primitive)], compacted, on one node; offset is
    subtracted from the positions and translation is the node's; clips: {name: [(time, translation, rotation)]}."""
    out = json.loads(json.dumps({k: v for k, v in doc.items()
                                 if k not in ('accessors', 'bufferViews', 'meshes', 'nodes', 'animations')}))
    out['accessors'], out['bufferViews'], out['meshes'] = [], [], []
    blob = bytearray()

    def view(data, target=None):
        blob.extend(b'\0' * (-len(blob) % 4))
        entry = {'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}
        if target:
            entry['target'] = target
        out['bufferViews'].append(entry)
        blob.extend(data)
        return len(out['bufferViews']) - 1

    def accessor(values, source, target=34962, minmax=False):
        values = np.ascontiguousarray(values)
        entry = {'bufferView': view(values.tobytes(), target), 'count': int(len(values))}
        entry.update({k: source[k] for k in ('componentType', 'type', 'normalized') if k in source})
        if minmax:
            entry['min'], entry['max'] = values.min(0).tolist(), values.max(0).tolist()
        out['accessors'].append(entry)
        return len(out['accessors']) - 1

    shift = np.zeros(3) if offset is None else np.array(offset)
    for m, mesh in enumerate(doc['meshes']):
        prims = []
        for p, prim in enumerate(mesh['primitives']):
            mask = keep[(m, p)]
            if not mask.any():
                continue
            tris = array(doc, binary, prim['indices']).reshape(-1, 3)[mask]
            used, remap = np.unique(tris, return_inverse=True)
            attributes = {}
            for name, index in prim['attributes'].items():
                values = array(doc, binary, index)[used]
                if name == 'POSITION':
                    values = (values - shift).astype(np.float32)
                attributes[name] = accessor(values, doc['accessors'][index], minmax=name == 'POSITION')
            indices = accessor(remap.reshape(-1).astype(np.uint32), {'componentType': 5125, 'type': 'SCALAR'}, 34963)
            prims.append({'attributes': attributes, 'indices': indices, 'material': prim['material']})
        if not prims:
            raise SystemExit(f'{mesh["name"]}: no triangles left in a LOD')
        out['meshes'].append({'name': mesh['name'], 'primitives': prims,
                              **({'extras': mesh['extras']} if 'extras' in mesh else {})})
    for image in out.get('images', []):
        if 'bufferView' in image:
            source = doc['bufferViews'][image['bufferView']]
            start = source.get('byteOffset', 0)
            image['bufferView'] = view(bytes(binary[start:start + source['byteLength']]))
    node = {'name': doc['nodes'][0]['name'], 'mesh': 0}
    if translation is not None:
        node['translation'] = [float(v) for v in translation]
    out['nodes'] = [node]
    out['scenes'] = [{'name': 'Scene', 'nodes': [0]}]
    if clips:
        out['animations'] = []
        for name, keys in clips.items():
            times = np.array([k[0] for k in keys], np.float32)
            t_in = accessor(times[:, None], {'componentType': 5126, 'type': 'SCALAR'}, None)
            out['accessors'][t_in]['min'], out['accessors'][t_in]['max'] = [float(times[0])], [float(times[-1])]
            moves = accessor(np.array([k[1] for k in keys], np.float32), {'componentType': 5126, 'type': 'VEC3'}, None)
            turns = accessor(np.array([k[2] for k in keys], np.float32), {'componentType': 5126, 'type': 'VEC4'}, None)
            out['animations'].append({'name': name, 'samplers': [
                {'input': t_in, 'output': moves, 'interpolation': 'LINEAR'},
                {'input': t_in, 'output': turns, 'interpolation': 'LINEAR'}], 'channels': [
                {'sampler': 0, 'target': {'node': 0, 'path': 'translation'}},
                {'sampler': 1, 'target': {'node': 0, 'path': 'rotation'}}]})
    out['buffers'] = [{'byteLength': len(blob)}]
    return out, bytes(blob)


def clip_names(raw):
    out = {}
    for name in raw.tracks:
        if SKIP_CLIPS.match(name):
            continue
        ours = RENAME.get(name.lower(), name.lower())
        out.setdefault(ours, name)
    return out


def split(prop):
    """Builds work/<prop>/: body (or the whole moving model) and parts; returns the plan."""
    model, raw_path, dropped, original = PROPS[prop]
    keep_dir = HERE / 'work/originals'
    keep_dir.mkdir(parents=True, exist_ok=True)
    kept = keep_dir / model
    if not kept.exists():
        shutil.copyfile(PROPS_DIR / original if original else SOURCE / model, kept)
    doc, binary = read_glb(kept)
    raw = Raw(PROPS_DIR / raw_path, POSE.get(prop))
    pieces = raw.pieces()
    names = list(pieces)
    cloud = np.concatenate([pieces[n][0] for n in names])
    labels = np.concatenate([[n] * len(pieces[n][0]) for n in names])
    lod0 = np.concatenate([array(doc, binary, p['attributes']['POSITION']) for p in doc['meshes'][0]['primitives']])
    a, o = fit(cloud, lod0, TILT.get(prop, 0.0))
    mapped = cloud @ a.T + o
    error = nearest(lod0, mapped)[0]
    print(f'{prop}: fit scale {abs(np.linalg.det(a)) ** (1 / 3):.4f}, LOD0 corners off by median '
          f'{np.median(error):.4f}, max {error.max():.4f}')
    if error.max() > TOLERANCE * (lod0.max(0) - lod0.min(0)).max():
        raise SystemExit(f'{prop}: the raw import does not fit the finished model')
    a_inv = np.linalg.inv(a)

    def to_asset(motion):
        r = a @ motion[:3, :3] @ a_inv
        return r, a @ motion[:3, 3] + o - r @ o

    clips = clip_names(raw)
    times = {ours: sorted(set(np.round(np.arange(0.0, raw.duration(name), 1.0 / SAMPLE_RATE), 4).tolist()
                              + [round(raw.duration(name), 4)]))
             for ours, name in clips.items()}
    # Group the pieces by motion: the same matrices at every sampled time.
    signature, groups = {}, {}
    for piece in names:
        node = pieces[piece][1]
        motions = np.array([raw.motion(node, clips[c], t) for c in clips for t in times[c]])
        if np.abs(motions - np.identity(4)).max() < STILL:
            continue
        key = next((k for k, m in signature.items() if np.abs(m - motions).max() < STILL), None)
        if key is None:
            key = piece
            signature[key] = motions
        groups.setdefault(key, []).append(piece)
    still = [n for n in names if not any(n in g for g in groups.values()) and n not in dropped]

    triangle_piece = {}
    for m, p, prim in lod_primitives(doc, binary):
        points = array(doc, binary, prim['attributes']['POSITION'])
        indices = array(doc, binary, prim['indices']).ravel()
        _, which = nearest(points, mapped)
        corner = labels[which][indices.reshape(-1, 3)]
        triangle_piece[(m, p)] = np.array([max(set(row), key=list(row).count) for row in corner])

    out_dir = HERE / 'work' / prop
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = {'prop': prop, 'model': model, 'parts': [], 'whole': not still}
    counts = {n: int(sum((t == n).sum() for t in triangle_piece.values())) for n in names}
    print(f'  triangles by piece {counts}; still {still}; moving {groups}; dropped {sorted(dropped)}; '
          f'clips {sorted(clips)}')

    def keyed(group_key):
        node = pieces[group_key][1]
        rest = raw.world(node, *raw.pose)
        pivot = a @ rest[:3, 3] + o
        out = {}
        for ours, name in clips.items():
            keys = []
            for t in times[ours]:
                r, tr = to_asset(raw.motion(node, name, t))
                if abs(np.linalg.det(r) - 1) > 1e-3:
                    raise SystemExit(f'{prop}: a motion is not a rotation in asset space')
                keys.append((float(t), (r @ pivot + tr).tolist(), matrix_quat(r).tolist()))
            out[ours] = keys
        # A close that does not end at rest (CoffinRaised's Closed is a copy of its Open) is the open played back.
        if 'close' in out and 'open' in out and np.abs(raw.motion(node, clips['close'], raw.duration(clips['close']))
                                                       - np.identity(4)).max() > STILL:
            end = out['open'][-1][0]
            out['close'] = [(end - t, q, r) for t, q, r in reversed(out['open'])]
            print(f'  {group_key}: close is the open reversed')
        return pivot, out

    if not still:
        # Every piece moves: the largest motion group is the model, moving as a whole; the others are its parts.
        key = max(groups, key=lambda k: sum(counts[n] for n in groups[k]))
        members = groups.pop(key)
        pivot, keys = keyed(key)
        keep = {k: np.isin(v, members) for k, v in triangle_piece.items()}
        body_doc, body_bin = build(doc, binary, keep, pivot, pivot, keys)
    else:
        keep = {k: np.isin(v, still) for k, v in triangle_piece.items()}
        body_doc, body_bin = build(doc, binary, keep)
    write_glb(out_dir / model, body_doc, body_bin)
    plan['body'] = str(out_dir / model)
    body0 = np.concatenate([array(body_doc, body_bin, p['attributes']['POSITION'])
                            for p in body_doc['meshes'][0]['primitives']])
    plan['share'] = float((body0[:, 1].max() - body0[:, 1].min()) / (lod0[:, 1].max() - lod0[:, 1].min()))
    for key, members in groups.items():
        pivot, keys = keyed(key)
        keep = {k: np.isin(v, members) for k, v in triangle_piece.items()}
        part_doc, part_bin = build(doc, binary, keep, pivot, pivot, keys)
        suffix = re.sub(r'[^a-z0-9]+', '', key.lower())
        base = re.sub(r'[^a-z0-9]+', '', model[len('mm9_deco_'):-len('.glb')])
        for prefix in (base, base.rstrip('0123456789')):
            if suffix.startswith(prefix) and len(suffix) > len(prefix):
                suffix = suffix[len(prefix):]
                break
        name = model.replace('.glb', f'_{suffix}.glb')
        write_glb(out_dir / name, part_doc, part_bin)
        plan['parts'].append({'file': str(out_dir / name), 'name': name, 'pieces': members})
    return plan


def rewrite_bindings(plan, manifest):
    """Every binding of the plan's model in the manifest: parts, idle, height x share (once)."""
    text = manifest.read_text()
    blocks = re.split(r'(?m)^(?=  - name: )', text)
    model_path = f'worlds/mm9/models/{plan["model"]}'
    parts = [f'worlds/mm9/models/{p["name"]}' for p in plan['parts']]
    changed = []
    for i, block in enumerate(blocks):
        if f'\n    model: {model_path}\n' not in block:
            continue
        name = re.match(r'  - name: (\S+)', block).group(1)
        if parts and '\n    parts:' not in block:
            height = float(re.search(r'\n    height: ([0-9.]+)', block).group(1))
            block = re.sub(r'\n    height: [0-9.]+', f'\n    height: {round(height * plan["share"], 1)}', block, 1)
            block = block.replace(f'\n    model: {model_path}\n',
                                  f'\n    model: {model_path}\n    parts: [{", ".join(parts)}]\n', 1)
        idle = IDLE.get(plan['prop'])
        if idle and '\n    idle:' not in block:
            block = block.replace(f'\n    model: {model_path}\n', f'\n    model: {model_path}\n    idle: {idle}\n', 1)
        if block != blocks[i]:
            blocks[i] = block
            changed.append(name)
    manifest.write_text(''.join(blocks))
    return changed


def install(plan):
    check = REPO / 'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'
    files = [(plan['body'], plan['model'])] + [(p['file'], p['name']) for p in plan['parts']]
    for path, name in files:
        subprocess.run([sys.executable, str(check), path], check=True)
        subprocess.run([sys.executable, str(REPO / 'tools/install_model.py'), path, '--world', 'mm9', '--name', name],
                       check=True)
    with open(LOCK, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for manifest in MANIFESTS:
            print(f'  {manifest.name}: {rewrite_bindings(plan, manifest)}')


def main():
    props = [a for a in sys.argv[1:] if not a.startswith('--')] or list(PROPS)
    plans = []
    for prop in props:
        plan = split(prop)
        plans.append(plan)
        print(f'  -> body share {plan["share"]:.3f}, parts {[p["name"] for p in plan["parts"]]}'
              f'{", moves whole" if plan["whole"] else ""}')
    (HERE / 'work/plans.json').write_text(json.dumps(plans, indent=1) + '\n')
    if '--install' in sys.argv:
        for plan in plans:
            install(plan)


if __name__ == '__main__':
    main()
