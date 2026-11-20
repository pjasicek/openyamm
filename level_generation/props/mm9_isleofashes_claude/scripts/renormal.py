#!/usr/bin/env python3
"""Normals of the installed MM9 decorations from their geometry: smooth within 40 degrees, hard beyond, as the props
builds intended (blib.smooth). Until 2026-11-06 blib.import_raw kept the glTF import's custom normals through its
bmesh round trip, where the mirror, face reversal, weld and triangulation scrambled them: the exports carried
unrelated per-corner normals, so the two triangles of a flat panel shaded differently (a hard diagonal across cabinet
doors in light). blib now drops them; this repairs the models already installed without rebuilding them (their x4
skins were swapped in after the build), touching nothing but NORMAL (and the vertex splits it needs).

Per mesh (all its triangle primitives together, as one Blender mesh): corners at one position (welded at 1e-5 m)
share a normal when their faces are joined round that position by edges with two faces, consistent winding and face
normals within the angle; the shared normal is the corner-angle weighted sum of the face normals (Blender's).

    python3 renormal.py check GLB...                 # seam share before -> after, nothing written
    python3 renormal.py install GLB... [--angle 40]  # copies to work/renormal/, then tools/install_model.py (mm9_deco_*: --world mm9)
"""
import argparse
import json
import math
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGING = HERE.parent / 'work' / 'renormal'
COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
WELD = 1e-5


def read_glb(path):
    data = Path(path).read_bytes()
    json_length = struct.unpack_from('<I', data, 12)[0]
    document = json.loads(data[20:20 + json_length])
    offset = 20 + json_length
    binary = data[offset + 8:offset + 8 + struct.unpack_from('<I', data, offset)[0]]
    return document, binary


def write_glb(path, document, blob):
    body = json.dumps(document, separators=(',', ':')).encode()
    body += b' ' * (-len(body) % 4)
    blob += b'\0' * (-len(blob) % 4)
    total = 12 + 8 + len(body) + 8 + len(blob)
    Path(path).write_bytes(struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(body), 0x4E4F534A)
                           + body + struct.pack('<II', len(blob), 0x004E4942) + blob)


def accessor_array(document, binary, index):
    accessor = document['accessors'][index]
    if 'sparse' in accessor:
        raise ValueError('sparse accessor')
    view = document['bufferViews'][accessor['bufferView']]
    dtype = np.dtype(COMPONENT[accessor['componentType']])
    width = WIDTH[accessor['type']]
    stride = view.get('byteStride', dtype.itemsize * width)
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    rows = np.frombuffer(binary, np.uint8, count=stride * (accessor['count'] - 1) + dtype.itemsize * width,
                         offset=start) if accessor['count'] else np.zeros(0, np.uint8)
    out = np.lib.stride_tricks.as_strided(rows, (accessor['count'], dtype.itemsize * width), (stride, 1))
    return np.frombuffer(np.ascontiguousarray(out).tobytes(), dtype).reshape(accessor['count'], width)


def mesh_normals(positions, triangles, angle):
    """Per-corner normals (len(triangles) x 3 x 3) of one mesh; None where a corner's group has no area."""
    span = max(float(np.ptp(positions, 0).max()), 1e-9) if len(positions) else 1.0
    key = np.round(positions / WELD).astype(np.int64)
    _, pid = np.unique(key, axis=0, return_inverse=True)
    pid = pid.ravel()
    corners = pid[triangles]                                       # T x 3 position ids
    v = positions[triangles]
    cross = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    length = np.linalg.norm(cross, axis=1)
    face = np.where(length[:, None] > 1e-12 * span * span, cross / np.maximum(length[:, None], 1e-30), 0.0)
    weight = np.zeros((len(triangles), 3))
    for k in range(3):
        a = v[:, (k + 1) % 3] - v[:, k]
        b = v[:, (k + 2) % 3] - v[:, k]
        cos = np.einsum('ij,ij->i', a, b) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-30)
        weight[:, k] = np.arccos(np.clip(cos, -1.0, 1.0))
    parent = np.arange(len(triangles) * 3)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edges = {}
    for t in range(len(triangles)):
        for k in range(3):
            a, b = corners[t, k], corners[t, (k + 1) % 3]
            if a != b:
                edges.setdefault((min(a, b), max(a, b)), []).append((t, k, a < b))
    limit = math.cos(math.radians(angle))
    for (a, b), users in edges.items():
        if len(users) != 2:
            continue
        (t0, k0, d0), (t1, k1, d1) = users
        if d0 == d1 or face[t0] @ face[t1] < limit:
            continue                                       # inconsistent winding or a crease: sharp
        for p in (a, b):
            c0 = t0 * 3 + int(np.nonzero(corners[t0] == p)[0][0])
            c1 = t1 * 3 + int(np.nonzero(corners[t1] == p)[0][0])
            r0, r1 = find(c0), find(c1)
            if r0 != r1:
                parent[r0] = r1
    roots = np.array([find(c) for c in range(len(parent))])
    contribution = (face[:, None, :] * weight[:, :, None]).reshape(-1, 3)
    total = np.zeros((len(parent), 3))
    np.add.at(total, roots, contribution)
    normal = total[roots]
    size = np.linalg.norm(normal, axis=1)
    normal = normal / np.maximum(size[:, None], 1e-30)
    return normal.reshape(-1, 3, 3), (size > 1e-20).reshape(-1, 3)


def renormal(path, angle):
    """(document, blob) with the normals rebuilt, and per mesh (vertices before, after)."""
    document, binary = read_glb(path)
    for extension in document.get('extensionsRequired', []):
        raise ValueError(f'required extension {extension}')
    new_accessors = list(document['accessors'])
    payload = {}                                           # accessor index -> new array (new accessors only)
    report = []
    for mesh in document['meshes']:
        primitives = [p for p in mesh['primitives'] if p.get('mode', 4) == 4 and 'indices' in p
                      and 'NORMAL' in p['attributes']]
        if not primitives:
            continue
        if any('targets' in p for p in primitives):
            raise ValueError('morph targets')
        positions, triangles, bases, base = [], [], [], 0
        for p in primitives:
            position = accessor_array(document, binary, p['attributes']['POSITION']).astype(float)
            index = accessor_array(document, binary, p['indices']).ravel().astype(np.int64)
            positions.append(position)
            triangles.append(index.reshape(-1, 3) + base)
            bases.append(base)
            base += len(position)
        normals, valid = mesh_normals(np.concatenate(positions), np.concatenate(triangles), angle)
        row = 0
        before = after = 0
        for p, position, tris, offset in zip(primitives, positions, triangles, bases):
            count = len(tris)
            corner_normal = normals[row:row + count].reshape(-1, 3)
            corner_valid = valid[row:row + count].ravel()
            row += count
            local = tris.ravel() - offset
            original = accessor_array(document, binary, p['attributes']['NORMAL']).astype(float)
            corner_normal = np.where(corner_valid[:, None], corner_normal, original[local])
            quantised = np.round(corner_normal * 1e4).astype(np.int64)
            keys = np.concatenate([local[:, None], quantised], axis=1)
            unique, inverse = np.unique(keys, axis=0, return_inverse=True)
            inverse = inverse.ravel()
            source = unique[:, 0]
            normal = np.zeros((len(unique), 3))
            normal[inverse] = corner_normal
            before += len(position)
            after += len(unique)
            attributes = {}
            for name, accessor in p['attributes'].items():
                data = normal.astype(np.float32) if name == 'NORMAL' else \
                    accessor_array(document, binary, accessor)[source]
                attributes[name] = len(new_accessors)
                new = {k: v for k, v in document['accessors'][accessor].items() if k not in ('byteOffset', 'min', 'max')}
                new['count'] = len(data)
                if name == 'POSITION' or 'min' in document['accessors'][accessor]:
                    new['min'] = data.min(0).tolist()
                    new['max'] = data.max(0).tolist()
                new_accessors.append(new)
                payload[attributes[name]] = data
            p['attributes'] = attributes
            index_type = 5123 if len(unique) < 65536 else 5125
            index_data = inverse.astype(COMPONENT[index_type]).reshape(-1, 1)
            p['indices'] = len(new_accessors)
            new_accessors.append({'componentType': index_type, 'count': len(index_data), 'type': 'SCALAR'})
            payload[p['indices']] = index_data
        report.append((mesh.get('name'), before, after))
    document['accessors'] = new_accessors
    return compact(document, binary, payload), report


def compact(document, binary, payload):
    """Drops unreferenced accessors and views and repacks the buffer (images and other views byte-exact)."""
    used = set()
    for mesh in document['meshes']:
        for p in mesh['primitives']:
            used.update(p['attributes'].values())
            if 'indices' in p:
                used.add(p['indices'])
            for target in p.get('targets', []):
                used.update(target.values())
    for skin in document.get('skins', []):
        if 'inverseBindMatrices' in skin:
            used.add(skin['inverseBindMatrices'])
    for animation in document.get('animations', []):
        for sampler in animation['samplers']:
            used.update((sampler['input'], sampler['output']))
    remap = {old: new for new, old in enumerate(sorted(used))}
    index_accessors = {p['indices'] for mesh in document['meshes'] for p in mesh['primitives'] if 'indices' in p}
    views, chunks, position = [], [], 0
    view_remap = {}

    def add_view(data, template=None):
        nonlocal position
        view = {'buffer': 0, 'byteOffset': position, 'byteLength': len(data)}
        if template:
            view.update({k: v for k, v in template.items() if k in ('target', 'byteStride', 'name')})
        chunks.append(data + b'\0' * (-len(data) % 4))
        position += len(chunks[-1])
        views.append(view)
        return len(views) - 1

    accessors = []
    for old in sorted(used):
        accessor = dict(document['accessors'][old])
        if old in payload:
            accessor['bufferView'] = add_view(np.ascontiguousarray(payload[old]).tobytes(),
                                              {'target': 34963 if old in index_accessors else 34962})
            accessor.pop('byteOffset', None)
        else:
            view_index = accessor['bufferView']
            if view_index not in view_remap:
                view = document['bufferViews'][view_index]
                start = view.get('byteOffset', 0)
                view_remap[view_index] = add_view(bytes(binary[start:start + view['byteLength']]), view)
            accessor['bufferView'] = view_remap[view_index]
        accessors.append(accessor)
    for image in document.get('images', []):
        if 'bufferView' in image:
            view_index = image['bufferView']
            if view_index not in view_remap:
                view = document['bufferViews'][view_index]
                start = view.get('byteOffset', 0)
                view_remap[view_index] = add_view(bytes(binary[start:start + view['byteLength']]), view)
            image['bufferView'] = view_remap[view_index]
    for mesh in document['meshes']:
        for p in mesh['primitives']:
            p['attributes'] = {k: remap[v] for k, v in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] = remap[p['indices']]
    for skin in document.get('skins', []):
        if 'inverseBindMatrices' in skin:
            skin['inverseBindMatrices'] = remap[skin['inverseBindMatrices']]
    for animation in document.get('animations', []):
        for sampler in animation['samplers']:
            sampler['input'], sampler['output'] = remap[sampler['input']], remap[sampler['output']]
    document['accessors'] = accessors
    document['bufferViews'] = views
    document['buffers'] = [{'byteLength': position}]
    return document, b''.join(chunks)


def seam_share(document, binary):
    """Share of triangle area on a shading seam: an edge between near-coplanar faces (within 10 degrees) whose
    corner normals there differ by more than 20 degrees."""
    total = seam = 0.0
    for mesh in document['meshes']:
        for p in mesh['primitives']:
            if p.get('mode', 4) != 4 or 'indices' not in p or 'NORMAL' not in p['attributes']:
                continue
            position = accessor_array(document, binary, p['attributes']['POSITION']).astype(float)
            normal = accessor_array(document, binary, p['attributes']['NORMAL']).astype(float)
            normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-30)
            tris = accessor_array(document, binary, p['indices']).ravel().astype(np.int64).reshape(-1, 3)
            _, pid = np.unique(np.round(position / WELD).astype(np.int64), axis=0, return_inverse=True)
            pid = pid.ravel()
            v = position[tris]
            cross = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
            area = np.linalg.norm(cross, axis=1) / 2
            face = cross / np.maximum(area[:, None] * 2, 1e-30)
            edges = {}
            for t, tri in enumerate(tris):
                for k in range(3):
                    i0, i1 = tri[k], tri[(k + 1) % 3]
                    edges.setdefault((min(pid[i0], pid[i1]), max(pid[i0], pid[i1])), []).append(
                        (t, {pid[i0]: i0, pid[i1]: i1}))
            flagged = np.zeros(len(tris), bool)
            for edge, users in edges.items():
                if len(users) != 2:
                    continue
                (t0, m0), (t1, m1) = users
                if face[t0] @ face[t1] < math.cos(math.radians(10)):
                    continue
                if min(normal[m0[q]] @ normal[m1[q]] for q in edge) < math.cos(math.radians(20)):
                    flagged[t0] = flagged[t1] = True
            total += area.sum()
            seam += area[flagged].sum()
    return seam / max(total, 1e-30)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('check', 'install'))
    parser.add_argument('models', nargs='+', type=Path)
    parser.add_argument('--angle', type=float, default=40.0)
    parser.add_argument('--min-seam', type=float, default=0.0,
                        help='install: skip a model whose seam share is at or below this')
    args = parser.parse_args()
    STAGING.mkdir(parents=True, exist_ok=True)
    failures = 0
    for path in args.models:
        try:
            before = seam_share(*read_glb(path))
            if args.command == 'install' and before <= args.min_seam:
                print(f'{path.name}: seams {before:.3f}, kept', flush=True)
                continue
            (document, blob), report = renormal(path, args.angle)
            after = seam_share(document, blob)
        except ValueError as error:
            print(f'{path.name}: SKIPPED ({error})', flush=True)
            failures += 1
            continue
        vertices = ', '.join(f'{b}->{a}' for _, b, a in report)
        line = f'{path.name}: seams {before:.3f} -> {after:.3f}, vertices {vertices}'
        if args.command == 'check':
            print(line, flush=True)
            continue
        out = STAGING / path.name
        write_glb(out, document, blob)
        scope = ['--world', 'mm9'] if out.name.lower().startswith('mm9_deco_') else ['--engine']
        result = subprocess.run([sys.executable, str(ROOT / 'tools/install_model.py'), str(out), *scope],
                                cwd=ROOT, capture_output=True, text=True)
        print(f"{line}, install {'ok' if result.returncode == 0 else 'FAILED'}", flush=True)
        if result.returncode != 0:
            failures += 1
            print(result.stdout[-800:], result.stderr[-800:])
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
