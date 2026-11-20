#!/usr/bin/env python3
"""The Beethoven coffins (CoffinFancy, CoffinRaise.scr) as a decoration and its moving lid (DecorationModelSet parts,
evt.PlayDecorationClip): splits the finished work/mm9_deco_coffinfancy.glb into
  work/mm9_deco_coffinfancy_body.glb   the coffin without its lid and without the Skeleton piece (every placement
                                       hides it: the DAT's HidePiece0 Skeleton; the mummy lies there instead), and
  work/mm9_deco_coffinfancy_lid.glb    the lid on one node at its hinge bone (the ABC's Bone01), with the ABC's
                                       clips `open` and `close` (1 s each) on that node.
Each triangle of every LOD goes to the ABC piece its corners lie on: the raw import (work/raw/coffinfancy, the pieces
under their bone nodes) is mapped into the finished model's asset space by the axis permutation, scale and offset that
fit it (checked: every LOD0 corner within 0.5 units of a raw vertex). The lid's clips are the raw import's own (glTF
convention), carried into asset space; between keys the node moves as LithTech moves the bone (translation lerp,
rotation slerp), since the node is the bone.

Usage: coffin_parts.py [--install]   (install: tools/install_model.py --world mm9, names mm9_deco_coffinfancy and
mm9_deco_coffinfancy_lid; the binding's height is the body's own, printed here)."""
import itertools
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO / 'level_generation/props/mm9_isleofashes_claude/scripts'))
from link_static_model_lods import read_glb, write_glb  # noqa: E402
from glbio import array  # noqa: E402

FINISHED = HERE / 'work/mm9_deco_coffinfancy.glb'
RAW = HERE / 'work/raw/coffinfancy/coffinfancy.glb'
BODY = HERE / 'work/mm9_deco_coffinfancy_body.glb'
LID = HERE / 'work/mm9_deco_coffinfancy_lid.glb'
OLD_HEIGHT = 124.3          # the binding's height of the whole coffin (indoor_decorations.yml)
LID_PIECE, DROPPED = 'Lid', {'Skeleton'}
CLIPS = {'open': 'Open', 'close': 'Close'}
TOLERANCE = 0.5


def quat_matrix(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def trs(translation, rotation):
    m = np.identity(4)
    m[:3, :3] = quat_matrix(rotation)
    m[:3, 3] = translation
    return m


def matrix_quat(r):
    """A proper rotation matrix as (x, y, z, w)."""
    w = np.sqrt(max(0.0, 1 + r[0, 0] + r[1, 1] + r[2, 2])) / 2
    x = np.sqrt(max(0.0, 1 + r[0, 0] - r[1, 1] - r[2, 2])) / 2
    y = np.sqrt(max(0.0, 1 - r[0, 0] + r[1, 1] - r[2, 2])) / 2
    z = np.sqrt(max(0.0, 1 - r[0, 0] - r[1, 1] + r[2, 2])) / 2
    x = np.copysign(x, r[2, 1] - r[1, 2])
    y = np.copysign(y, r[0, 2] - r[2, 0])
    z = np.copysign(z, r[1, 0] - r[0, 1])
    q = np.array([x, y, z, w])
    return q / np.linalg.norm(q)


class Raw:
    """The raw import: each piece's world vertices, and the global matrix of a node at a clip's key."""

    def __init__(self, path):
        self.doc, self.bin = read_glb(path)
        self.parent = {c: i for i, n in enumerate(self.doc['nodes']) for c in n.get('children', [])}

    def local(self, index, overrides=None):
        node = self.doc['nodes'][index]
        t, r = (overrides or {}).get(index, (node.get('translation', [0, 0, 0]), node.get('rotation', [0, 0, 0, 1])))
        return trs(t, r)

    def world(self, index, overrides=None):
        m = self.local(index, overrides)
        while index in self.parent:
            index = self.parent[index]
            m = self.local(index, overrides) @ m
        return m

    def pieces(self):
        out = {}
        for index, node in enumerate(self.doc['nodes']):
            if 'mesh' not in node:
                continue
            mesh = self.doc['meshes'][node['mesh']]
            points = np.concatenate([array(self.doc, self.bin, p['attributes']['POSITION']) for p in mesh['primitives']])
            m = self.world(index)
            out[mesh['name']] = (index, points @ m[:3, :3].T + m[:3, 3])
        return out

    def keys(self, clip, node):
        """[(time, {node: (translation, rotation)})] of the clip's keys on node."""
        animation = next(a for a in self.doc['animations'] if a['name'] == clip)
        tracks = {}
        for channel in animation['channels']:
            if channel['target']['node'] != node:
                continue
            sampler = animation['samplers'][channel['sampler']]
            tracks[channel['target']['path']] = (array(self.doc, self.bin, sampler['input']).ravel(),
                                                 array(self.doc, self.bin, sampler['output']))
        times = tracks['rotation'][0]
        assert np.allclose(times, tracks['translation'][0])
        return [(float(t), (tracks['translation'][1][k].tolist(), tracks['rotation'][1][k].tolist()))
                for k, t in enumerate(times)]


def nearest(points, cloud):
    """Distance from each point to the nearest of cloud, and its index."""
    best = np.full(len(points), np.inf)
    which = np.zeros(len(points), int)
    for start in range(0, len(cloud), 512):
        d = np.linalg.norm(points[:, None, :] - cloud[None, start:start + 512, :], axis=2)
        k = d.argmin(1)
        v = d[np.arange(len(points)), k]
        better = v < best
        best[better], which[better] = v[better], k[better] + start
    return best, which


def fit(raw_points, asset_points):
    """The map raw -> asset, x -> s P x + o (P a signed axis permutation): the one whose corners match best."""
    best = None
    lo, hi = asset_points.min(0), asset_points.max(0)
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            p = np.zeros((3, 3))
            for row, (col, sign) in enumerate(zip(perm, signs)):
                p[row, col] = sign
            mapped = raw_points @ p.T
            s = float(np.mean((hi - lo) / np.maximum(mapped.max(0) - mapped.min(0), 1e-9)))
            o = (lo + hi) / 2 - s * (mapped.max(0) + mapped.min(0)) / 2
            error = float(np.median(nearest(asset_points, mapped * s + o)[0]))
            if best is None or error < best[0]:
                best = (error, s * p, o)
    return best[1], best[2]


def piece_of_triangles(points, indices, cloud, labels):
    """The piece label of each triangle: the label most of its corners' nearest raw vertices carry."""
    _, which = nearest(points, cloud)
    corner = labels[which][indices.reshape(-1, 3)]
    out = []
    for row in corner:
        values, counts = np.unique(row, return_counts=True)
        out.append(values[counts.argmax()])
    return np.array(out)


def build(doc, binary, keep, lid_node=None, clips=None):
    """A GLB of doc's meshes with only the triangles keep[(mesh, primitive)] (a bool per triangle), compacted, on
    one node; lid_node = (translation of the node, offset subtracted from positions) for the lid; clips: glTF
    animations on it ({name: [(time, translation, rotation)]})."""
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

    def accessor(values, source=None, target=34962, minmax=False):
        values = np.ascontiguousarray(values)
        entry = {'bufferView': view(values.tobytes(), target), 'count': int(len(values))}
        if source is not None:
            entry.update({k: source[k] for k in ('componentType', 'type', 'normalized') if k in source})
        if minmax:
            entry['min'], entry['max'] = values.min(0).tolist(), values.max(0).tolist()
        out['accessors'].append(entry)
        return len(out['accessors']) - 1

    offset = np.zeros(3) if lid_node is None else np.array(lid_node[1])
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
                    values = (values - offset).astype(np.float32)
                attributes[name] = accessor(values, doc['accessors'][index], minmax=name == 'POSITION')
            indices = remap.reshape(-1).astype(np.uint32)
            index_accessor = accessor(indices, {'componentType': 5125, 'type': 'SCALAR'}, 34963)
            prims.append({'attributes': attributes, 'indices': index_accessor, 'material': prim['material']})
        out['meshes'].append({'name': mesh['name'], 'primitives': prims,
                              **({'extras': mesh['extras']} if 'extras' in mesh else {})})
    # images ride in buffer views
    for image in out.get('images', []):
        if 'bufferView' in image:
            source = doc['bufferViews'][image['bufferView']]
            start = source.get('byteOffset', 0)
            image['bufferView'] = view(bytes(binary[start:start + source['byteLength']]))
    node = {'name': doc['nodes'][0]['name'], 'mesh': 0}
    if lid_node is not None:
        node['name'] = 'Lid'
        node['translation'] = [float(v) for v in lid_node[0]]
    out['nodes'] = [node]
    out['scenes'] = [{'name': 'Scene', 'nodes': [0]}]
    if clips:
        out['animations'] = []
        for name, keys in clips.items():
            times = np.array([k[0] for k in keys], np.float32)
            t_in = accessor(times[:, None], {'componentType': 5126, 'type': 'SCALAR'}, None)
            out['accessors'][t_in]['min'], out['accessors'][t_in]['max'] = [float(times[0])], [float(times[-1])]
            translations = accessor(np.array([k[1] for k in keys], np.float32),
                                    {'componentType': 5126, 'type': 'VEC3'}, None)
            rotations = accessor(np.array([k[2] for k in keys], np.float32),
                                 {'componentType': 5126, 'type': 'VEC4'}, None)
            out['animations'].append({'name': name, 'samplers': [
                {'input': t_in, 'output': translations, 'interpolation': 'LINEAR'},
                {'input': t_in, 'output': rotations, 'interpolation': 'LINEAR'}], 'channels': [
                {'sampler': 0, 'target': {'node': 0, 'path': 'translation'}},
                {'sampler': 1, 'target': {'node': 0, 'path': 'rotation'}}]})
    out['buffers'] = [{'byteLength': len(blob)}]
    return out, bytes(blob)


def main():
    doc, binary = read_glb(FINISHED)
    raw = Raw(RAW)
    pieces = raw.pieces()
    names = list(pieces)
    cloud = np.concatenate([pieces[n][1] for n in names])
    labels = np.concatenate([[n] * len(pieces[n][1]) for n in names])
    lod0 = np.concatenate([array(doc, binary, p['attributes']['POSITION']) for p in doc['meshes'][0]['primitives']])
    a, o = fit(cloud, lod0)
    mapped = cloud @ a.T + o
    error = nearest(lod0, mapped)[0]
    print(f'fit: scale {np.abs(np.linalg.det(a)) ** (1 / 3):.4f}, LOD0 corners off by median {np.median(error):.3f}, '
          f'max {error.max():.3f}')
    if error.max() > TOLERANCE:
        raise SystemExit('the raw import does not fit the finished model')

    keep_body, keep_lid, counts = {}, {}, {}
    for m, mesh in enumerate(doc['meshes']):
        for p, prim in enumerate(mesh['primitives']):
            points = array(doc, binary, prim['attributes']['POSITION'])
            indices = array(doc, binary, prim['indices']).ravel()
            piece = piece_of_triangles(points, indices, mapped, labels)
            keep_lid[(m, p)] = piece == LID_PIECE
            keep_body[(m, p)] = ~np.isin(piece, list(DROPPED) + [LID_PIECE])
            for name in names:
                counts.setdefault(mesh['name'], {}).setdefault(name, 0)
                counts[mesh['name']][name] += int((piece == name).sum())
    print('triangles by piece:', json.dumps(counts))

    # The lid node is its bone: rest at the bone's origin, posed by the clips, all in asset space.
    lid_mesh_node = pieces[LID_PIECE][0]
    bone = raw.parent[lid_mesh_node]
    a_inv = np.linalg.inv(a)

    def to_asset(world):
        """A raw-world rigid motion (4x4) conjugated into asset space: rotation and translation."""
        r = a @ world[:3, :3] @ a_inv
        t = a @ world[:3, 3] + o - r @ o
        return r, t

    rest_world = raw.world(lid_mesh_node)
    pivot = a @ rest_world[:3, 3] + o
    clips = {}
    for name, source in CLIPS.items():
        keys = []
        for time, pose in raw.keys(source, bone):
            motion = raw.world(lid_mesh_node, {bone: pose}) @ np.linalg.inv(rest_world)
            r, t = to_asset(motion)
            if abs(np.linalg.det(r) - 1) > 1e-3:
                raise SystemExit('the lid motion is not a rotation in asset space')
            keys.append((time, (r @ pivot + t).tolist(), matrix_quat(r).tolist()))
        clips[name] = keys
        print(f'{name}: {len(keys)} keys over {keys[-1][0]:.3f} s, last {np.round(keys[-1][1], 1).tolist()} '
              f'{np.round(keys[-1][2], 3).tolist()}')

    body_doc, body_bin = build(doc, binary, keep_body)
    write_glb(BODY, body_doc, body_bin)
    lid_doc, lid_bin = build(doc, binary, keep_lid, (pivot, pivot), clips)
    write_glb(LID, lid_doc, lid_bin)

    full = lod0[:, 1].max() - lod0[:, 1].min()
    body0 = np.concatenate([array(body_doc, body_bin, p['attributes']['POSITION'])
                            for p in body_doc['meshes'][0]['primitives']])
    body_height = OLD_HEIGHT * (body0[:, 1].max() - body0[:, 1].min()) / full
    print(f'wrote {BODY.name}, {LID.name}; the binding height of the body: {body_height:.1f} '
          f'(base at {body0[:, 1].min():.3f}, the whole coffin\'s at {lod0[:, 1].min():.3f})')

    if '--install' in sys.argv:
        for path, name in ((BODY, 'mm9_deco_coffinfancy'), (LID, 'mm9_deco_coffinfancy_lid')):
            check = [sys.executable, str(REPO / 'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),
                     str(path)]
            subprocess.run(check, check=True)
            subprocess.run([sys.executable, str(REPO / 'tools/install_model.py'), str(path), '--world', 'mm9',
                            '--name', name + '.glb'], check=True)


if __name__ == '__main__':
    main()
