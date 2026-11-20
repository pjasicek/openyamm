#!/usr/bin/env python3
"""MM9 props whose LithTech models are skinned (a banner's cloth, a statue made from a creature, a book's pages) as
the `animated` copies of their decorations (devdocs/ANIMATED_DECORATIONS.md): for each prop in PROPS a skinned GLB,
work/<prop>/mm9_deco_<prop>_anim.glb, with the finished decoration's own meshes, materials and LODs:

  1. the raw import (its props project's work/raw/<raw>/<raw>.glb, skinned, with every clip) is skinned into the pose
     the props project built the decoration in (the table's: its props_table POSES, a clip and a frame; else the best
     of rest and every clip's first frame), and fitted onto the
     finished model's corners (prop_parts.fit: axis permutation, scale, tilt, ICP; checked within prop_parts.TOLERANCE);
  2. each finished vertex (every LOD) takes the joints and weights of the raw vertex it lies on (the nearest);
  3. the skeleton is the raw import's, carried into asset space (each node's local transform conjugated by the fit,
     so a node's world motion is the raw one seen in asset space), at rest in the build pose, so the copy at rest is
     the decoration; the inverse bind matrices are that pose's;
  4. the clips (lower case; static and NS* clips left out) are sampled at prop_parts.SAMPLE_RATE on every joint.

--install installs it (tools/install_model.py --world mm9) and gives every binding of the decoration `animated:` (and
IDLE's clip, USE's clips) under the shared lock.
Usage: prop_skins.py [prop ...] [--install]"""
import fcntl
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import prop_parts as pp  # noqa: E402

# prop: (decoration model, raw import, build pose (clip, frame) or None)
PROPS = {
    'bannerc': ('mm9_deco_bannerc.glb', 'mm9_outdoor_regions_claude/work/raw/bannerc/bannerc.glb', None),
    'bannercw': ('mm9_deco_bannercw.glb', 'mm9_outdoor_regions_claude/work/raw/bannercw/bannercw.glb', None),
    'iceskeleton': ('mm9_deco_iceskeleton.glb', 'mm9_darkpassageway_claude/work/raw/iceskeleton/iceskeleton.glb',
                    ('stand', 0)),
    'icezombie': ('mm9_deco_icezombie.glb', 'mm9_darkpassageway_claude/work/raw/icezombie/icezombie.glb',
                  ('stand', 0)),
    'icelich': ('mm9_deco_icelich.glb', 'mm9_darkpassageway_claude/work/raw/icelich/icelich.glb', ('stand', 0)),
    'icebanshee': ('mm9_deco_icebanshee.glb', 'mm9_darkpassageway_claude/work/raw/icebanshee/icebanshee.glb',
                   ('standAir', 0)),
    'iceterror': ('mm9_deco_iceterror.glb', 'mm9_darkpassageway_claude/work/raw/iceterror/iceterror.glb',
                  ('stand', 0)),
    'iceskeletonwarrior': ('mm9_deco_iceskeletonwarrior.glb',
                           'mm9_darkpassageway_claude/work/raw/iceskeletonwarrior/iceskeletonwarrior.glb',
                           ('stand', 0)),
    'sorcererstatue': ('mm9_deco_sorcererstatue.glb',
                       'mm9_1000terrors_claude/work/raw/sorcererstatue/sorcererstatue.glb', ('fidget2', 57)),
    'bookflat': ('mm9_deco_bookflat.glb', 'mm9_templeofhonk_claude/work/raw/bookflat/bookflat.glb', None),
    'booktilt': ('mm9_deco_booktilt.glb', 'mm9_lichlab_claude/work/raw/booktilt/booktilt.glb', None),
}
IDLE = {'bannerc': 'banner', 'bannercw': 'banner'}
# Clips each use steps through (Book.scr: OpenBook, TurnPage, TurnBack, CloseBook on successive uses).
USE = {'bookflat': ['openbook', 'turnpage', 'turnback', 'closebook']}
# Tilted variants (their props projects' book pitch, baked in): prop -> the tilt's angle (radians).
TILT = {'booktilt': 0.471}
FRAME_RATES = (24.0, 25.0, 30.0)     # Blender's scene rate when the props project posed the build (frame -> seconds)


class SkinnedRaw(pp.Raw):
    def skin_matrices(self, skin_index, clip=None, time=0.0):
        skin = self.doc['skins'][skin_index]
        ibm = pp.mat4s(self.doc, self.bin, skin['inverseBindMatrices'])
        return np.array([self.world(j, clip, time) @ ibm[k] for k, j in enumerate(skin['joints'])])

    def skinned(self, clip=None, time=0.0):
        """Every skinned vertex posed: points (n, 3), joints (n, 4) as skin joint slots, weights (n, 4)."""
        points, joints, weights = [], [], []
        for node in self.doc['nodes']:
            if 'mesh' not in node or 'skin' not in node:
                continue
            matrices = self.skin_matrices(node['skin'], clip, time)
            for prim in self.doc['meshes'][node['mesh']]['primitives']:
                p = pp.array(self.doc, self.bin, prim['attributes']['POSITION']).astype(float)
                j = pp.array(self.doc, self.bin, prim['attributes']['JOINTS_0']).astype(int)
                w = pp.array(self.doc, self.bin, prim['attributes']['WEIGHTS_0']).astype(float)
                ph = np.c_[p, np.ones(len(p))]
                posed = np.einsum('nk,nkij,nj->ni', w, matrices[j], ph)[:, :3]
                points.append(posed)
                joints.append(j)
                weights.append(w / np.maximum(w.sum(1, keepdims=True), 1e-9))
        return np.concatenate(points), np.concatenate(joints), np.concatenate(weights)


def build(prop):
    model, raw_path, pose = PROPS[prop]
    keep_dir = pp.HERE / 'work/originals'
    keep_dir.mkdir(parents=True, exist_ok=True)
    kept = keep_dir / model
    if not kept.exists():
        shutil.copyfile(pp.SOURCE / model, kept)
    doc, binary = pp.read_glb(kept)
    raw = SkinnedRaw(pp.PROPS_DIR / raw_path)
    lod0 = np.concatenate([pp.array(doc, binary, p['attributes']['POSITION']) for p in doc['meshes'][0]['primitives']])
    best = None
    # The build pose: the table's (at each frame rate), else rest or a clip's first frame (MM9 draws a prop in its
    # first animation's pose; the builds follow).
    candidates = [(pose[0], pose[1] / rate) for rate in FRAME_RATES] if pose else \
        [(None, 0.0)] + [(name, 0.0) for name in raw.tracks]
    for clip, seconds in candidates:
        cloud, joints, weights = raw.skinned(clip, seconds)
        a, o = pp.fit(cloud, lod0, TILT.get(prop, 0.0))
        error = pp.nearest(lod0, cloud @ a.T + o)[0]
        if best is None or error.max() < best[0].max():
            best = (error, a, o, clip, seconds, cloud, joints, weights)
    error, a, o, clip, seconds, cloud, joints, weights = best
    print(f'{prop}: pose {clip} {seconds:.3f} s, LOD0 corners off by median {np.median(error):.4f}, max '
          f'{error.max():.4f} (extent {(lod0.max(0) - lod0.min(0)).max():.2f})')
    if error.max() > pp.TOLERANCE * (lod0.max(0) - lod0.min(0)).max():
        raise SystemExit(f'{prop}: the raw import does not fit the finished model')
    mapped = cloud @ a.T + o

    A = np.identity(4)
    A[:3, :3], A[:3, 3] = a, o
    A_inv = np.linalg.inv(A)

    def asset_local(node, clip_name, time):
        m = A @ raw.local(node, clip_name, time) @ A_inv
        r = m[:3, :3]
        if abs(np.linalg.det(r) - 1) > 1e-3:
            raise SystemExit(f'{prop}: node {node} is not rigid in asset space')
        return m[:3, 3], pp.matrix_quat(r)

    skin_raw = next(n['skin'] for n in raw.doc['nodes'] if 'skin' in n)
    joint_nodes = raw.doc['skins'][skin_raw]['joints']
    skeleton = [i for i, n in enumerate(raw.doc['nodes']) if 'mesh' not in n]
    new_index = {old: k for k, old in enumerate(skeleton)}

    out = json.loads(json.dumps({k: v for k, v in doc.items()
                                 if k not in ('accessors', 'bufferViews', 'meshes', 'nodes', 'animations', 'skins')}))
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

    def accessor(values, kind, component, target=34962, minmax=False, normalized=False):
        values = np.ascontiguousarray(values)
        entry = {'bufferView': view(values.tobytes(), target), 'count': int(len(values)), 'type': kind,
                 'componentType': component}
        if normalized:
            entry['normalized'] = True
        if minmax:
            entry['min'] = values.reshape(len(values), -1).min(0).tolist()
            entry['max'] = values.reshape(len(values), -1).max(0).tolist()
        out['accessors'].append(entry)
        return len(out['accessors']) - 1

    # Meshes: the finished primitives, each vertex weighted as the raw vertex it lies on.
    slot_of = {j: k for k, j in enumerate(joint_nodes)}
    for mesh in doc['meshes']:
        prims = []
        for prim in mesh['primitives']:
            attributes = {}
            for name, index in prim['attributes'].items():
                source = doc['accessors'][index]
                values = pp.array(doc, binary, index)
                attributes[name] = accessor(values, source['type'], source['componentType'],
                                            minmax=name == 'POSITION', normalized=source.get('normalized', False))
            points = pp.array(doc, binary, prim['attributes']['POSITION'])
            _, which = pp.nearest(points, mapped)
            attributes['JOINTS_0'] = accessor(joints[which].astype(np.uint16), 'VEC4', 5123)
            attributes['WEIGHTS_0'] = accessor(weights[which].astype(np.float32), 'VEC4', 5126)
            indices = pp.array(doc, binary, prim['indices']).ravel().astype(np.uint32)
            prims.append({'attributes': attributes, 'material': prim['material'],
                          'indices': accessor(indices, 'SCALAR', 5125, 34963)})
        out['meshes'].append({'name': mesh['name'], 'primitives': prims,
                              **({'extras': mesh['extras']} if 'extras' in mesh else {})})
    for image in out.get('images', []):
        if 'bufferView' in image:
            source = doc['bufferViews'][image['bufferView']]
            start = source.get('byteOffset', 0)
            image['bufferView'] = view(bytes(binary[start:start + source['byteLength']]))

    # Skeleton at rest in the build pose, then the model's node.
    nodes = []
    for old in skeleton:
        t, q = asset_local(old, clip, seconds)
        node = {'name': raw.doc['nodes'][old].get('name', f'node{old}'), 'translation': t.tolist(),
                'rotation': q.tolist()}
        children = [new_index[c] for c in raw.doc['nodes'][old].get('children', []) if c in new_index]
        if children:
            node['children'] = children
        nodes.append(node)
    roots = [new_index[i] for i in skeleton if i not in raw.parent]
    nodes.append({'name': doc['nodes'][0]['name'], 'mesh': 0, 'skin': 0})
    out['nodes'] = nodes
    out['scenes'] = [{'name': 'Scene', 'nodes': roots + [len(nodes) - 1]}]
    world = {}

    def asset_world(old):
        if old not in world:
            m = A @ raw.world(old, clip, seconds) @ A_inv
            world[old] = m
        return world[old]

    ibm = np.array([np.linalg.inv(asset_world(j)).T for j in joint_nodes], np.float32)   # column-major
    out['skins'] = [{'joints': [new_index[j] for j in joint_nodes],
                     'inverseBindMatrices': accessor(ibm.reshape(-1, 16), 'MAT4', 5126, None)}]

    # Clips sampled on every skeleton node.
    out['animations'] = []
    for ours, name in pp.clip_names(raw).items():
        duration = raw.duration(name)
        times = np.array(sorted(set(np.round(np.arange(0.0, duration, 1.0 / pp.SAMPLE_RATE), 4).tolist()
                                    + [round(duration, 4)])), np.float32)
        t_in = accessor(times[:, None], 'SCALAR', 5126, None)
        out['accessors'][t_in]['min'], out['accessors'][t_in]['max'] = [float(times[0])], [float(times[-1])]
        samplers, channels = [], []
        for old in skeleton:
            moves, turns = zip(*(asset_local(old, name, float(t)) for t in times))
            samplers.append({'input': t_in, 'output': accessor(np.array(moves, np.float32), 'VEC3', 5126, None),
                             'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': new_index[old], 'path': 'translation'}})
            turns = np.array(turns, np.float32)
            for k in range(1, len(turns)):          # one hemisphere, so linear blending never flips
                if np.dot(turns[k], turns[k - 1]) < 0:
                    turns[k] = -turns[k]
            samplers.append({'input': t_in, 'output': accessor(turns, 'VEC4', 5126, None), 'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': new_index[old], 'path': 'rotation'}})
        out['animations'].append({'name': ours, 'samplers': samplers, 'channels': channels})
    out['buffers'] = [{'byteLength': len(blob)}]
    out_dir = pp.HERE / 'work' / prop
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / model.replace('.glb', '_anim.glb')
    pp.write_glb(path, out, bytes(blob))
    print(f'  -> {path.name}: {len(joint_nodes)} joints, clips {[a["name"] for a in out["animations"]]}')
    return {'prop': prop, 'model': model, 'animated': str(path), 'name': path.name}


def rewrite_bindings(plan, manifest):
    text = manifest.read_text()
    blocks = re.split(r'(?m)^(?=  - name: )', text)
    model_path = f'worlds/mm9/models/{plan["model"]}'
    changed = []
    for i, block in enumerate(blocks):
        if f'\n    model: {model_path}\n' not in block:
            continue
        if '\n    animated:' not in block:
            block = block.replace(f'\n    model: {model_path}\n',
                                  f'\n    model: {model_path}\n    animated: worlds/mm9/models/{plan["name"]}\n', 1)
        use = USE.get(plan['prop'])
        if use and '\n    use_clips:' not in block:
            block = block.replace(f'\n    model: {model_path}\n',
                                  f'\n    model: {model_path}\n    use_clips: [{", ".join(use)}]\n', 1)
        idle = IDLE.get(plan['prop'])
        if idle and '\n    idle:' not in block:
            block = block.replace(f'\n    model: {model_path}\n', f'\n    model: {model_path}\n    idle: {idle}\n', 1)
        if block != blocks[i]:
            blocks[i] = block
            changed.append(re.match(r'  - name: (\S+)', block).group(1))
    manifest.write_text(''.join(blocks))
    return changed


def main():
    props = [a for a in sys.argv[1:] if not a.startswith('--')] or list(PROPS)
    plans = [build(prop) for prop in props]
    if '--install' not in sys.argv:
        return
    for plan in plans:
        subprocess.run([sys.executable, str(pp.REPO / 'tools/install_model.py'), plan['animated'], '--world', 'mm9',
                        '--name', plan['name']], check=True)
        with open(pp.LOCK, 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for manifest in pp.MANIFESTS:
                print(f'  {manifest.name}: {rewrite_bindings(plan, manifest)}')


if __name__ == '__main__':
    main()
