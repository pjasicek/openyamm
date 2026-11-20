"""Read-only gates on runtime glTF, including OpenYAMM's uninstantiated LOD meshes.

Run through run_gates.sh. All geometry is in metres, Z up, forward -Y. Native glTF
interpolation and NumPy skinning avoid importing textures or evaluating a depsgraph
separately for each LOD. Blender supplies the BVH; no authoring .blend is consulted.
"""
import argparse
import copy
import fnmatch
import hashlib
import json
import math
import re
import struct
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
C = np.array([[1., 0, 0, 0], [0, 0, -1., 0], [0, 1., 0, 0], [0, 0, 0, 1.]])
REJECTED = {
    'KHR_materials_pbrSpecularGlossiness', 'KHR_materials_clearcoat', 'KHR_materials_transmission',
    'KHR_materials_volume', 'KHR_materials_ior', 'KHR_materials_specular', 'KHR_materials_sheen',
    'KHR_materials_iridescence', 'KHR_materials_diffuse_transmission', 'KHR_materials_anisotropy',
    'KHR_materials_dispersion',
}
# Explicit batch numbers win; the remaining defaults are labelled in README.md.
LIMITS = {
    'weight_sum_error': 1e-4, 'elbow_hyperextension_deg': 5., 'elbow_flexion_deg': 150.,
    'elbow_plane_deg': 5., 'forearm_roll_deg': 90., 'wrist_flexion_deg': 70., 'wrist_roll_deg': 45.,
    'upper_arm_roll_deg': 60., 'roll_step_deg': 35., 'rotation_step_deg': 25.,
    'angular_acceleration_deg_s2': 20000., 'palm_thigh_deg': math.degrees(math.acos(.8)),
    'palm_grip_deg': 60., 'finger_curl_min_deg': 10.,
    'arm_stretch_p99': 2., 'arm_stretch_max': 4.5, 'hand_stretch_p99': 4.5, 'hand_stretch_max': 4.5,
    'floor_penetration_mm': 2., 'rest_sole_height_mm': 10., 'rest_sole_tilt_deg': 3.,
    'contact_height_mm': 10., 'running_contact_pct': 80., 'running_airborne_mm': 40.,
    'walking_lift_min_mm': 80., 'walking_lift_max_mm': 120.,
    'walking_knee_min_deg': 40., 'walking_knee_max_deg': 60., 'foot_yaw_deg': 10.,
    'penetration_mm': 2., 'cloth_penetration_mm': 2., 'head_penetration_mm': 10.,
    'grip_gap_mm': 3., 'grip_penetration_mm': 3., 'blow_pointing_deg': 70.,
    'blow_speed_fraction': .8, 'blow_time_error_s': 1 / 48, 'blade_edge_share': .7,
    'blade_signed_lead': 0., 'lod1_ratio': .55, 'lod2_ratio': .25, 'lod3_ratio': .10,
}


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-15)


def angle(a, b):
    return np.degrees(np.arccos(np.clip(np.sum(unit(a) * unit(b), axis=-1), -1, 1)))


def transform(matrix, points):
    return np.asarray(points) @ matrix[:3, :3].T + matrix[:3, 3]


def rotation(q):
    """glTF quaternion order is XYZW."""
    q = unit(q)
    x, y, z, w = np.moveaxis(q, -1, 0)
    return np.stack((1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w),
                     2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w),
                     2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)), axis=-1).reshape(q.shape[:-1]+(3, 3))


def quaternion(matrix):
    from mathutils import Matrix
    shape = matrix.shape[:-2]
    return np.array([tuple(Matrix(m.tolist()).to_quaternion()) for m in matrix.reshape(-1, 3, 3)]).reshape(shape+(4,))


def rotation_vector(matrix):
    q = quaternion(matrix)  # WXYZ
    q = np.where(q[..., :1] < 0, -q, q)
    length = np.linalg.norm(q[..., 1:], axis=-1)
    factor = np.divide(2*np.arctan2(length, q[..., 0]), length, out=np.full_like(length, 2.), where=length > 1e-12)
    return q[..., 1:] * factor[..., None]


def swing_twist(matrix, axis):
    q = quaternion(matrix)
    tw = 2*np.arctan2(np.sum(q[..., 1:]*unit(axis), axis=-1), q[..., 0])
    tw = (tw + np.pi) % (2*np.pi) - np.pi
    swing = angle(np.einsum('...ij,j->...i', matrix, unit(axis)), axis)
    return swing, np.degrees(tw)


def finger_curl(proximal, distal, root_delta, rest_direction, rest_palm_normal):
    # The bending plane follows the knuckle even after it curls past 90 degrees.
    hinge = unit(np.cross(rest_direction, rest_palm_normal))
    hinge = np.einsum('...ij,j->...i', root_delta, hinge)
    return np.degrees(np.arctan2(np.sum(np.cross(proximal, distal)*hinge, axis=-1),
                                np.sum(proximal*distal, axis=-1)))


def sample_grid(start, end, hz):
    start, end = float(start), float(end)
    return np.unique(np.r_[np.arange(start, end-1e-10, 1/hz, dtype=float), end])


def interpolate(keys, values, times, interpolation, is_rotation=False):
    if interpolation not in ('STEP', 'LINEAR'):
        raise ValueError(f'Runtime rejects {interpolation} interpolation')
    if len(keys) == 1:
        return np.repeat(values[0][None], len(times), axis=0)
    i = np.clip(np.searchsorted(keys, times, side='right')-1, 0, len(keys)-2)
    dt = keys[i+1]-keys[i]
    t = np.clip((times-keys[i])/dt, 0, 1)[:, None]
    if interpolation == 'STEP':
        return values[np.clip(np.searchsorted(keys, times, side='right')-1, 0, len(keys)-1)]
    a, b = values[i], values[i+1]
    if not is_rotation:
        return a*(1-t)+b*t
    a, b = unit(a), unit(b)
    dot = np.sum(a*b, axis=-1, keepdims=True)
    b = np.where(dot < 0, -b, b)
    # Match ModelAnimation::sampleChannel: shortest-path normalized lerp, not glTF's spherical lerp.
    return unit(a*(1-t)+b*t)


class Glb:
    def __init__(self, path):
        self.path = Path(path).resolve()
        raw = self.path.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if len(raw) < 20 or struct.unpack_from('<III', raw) != (0x46546c67, 2, len(raw)):
            raise ValueError(f'Invalid GLB header: {path}')
        chunks = {}
        offset = 12
        while offset < len(raw):
            size, kind = struct.unpack_from('<II', raw, offset)
            if size % 4 or offset+8+size > len(raw):
                raise ValueError('Invalid GLB chunk length')
            chunks[kind] = raw[offset+8:offset+8+size]
            offset += size+8
        self.doc = json.loads(chunks[0x4e4f534a])
        self.data = chunks.get(0x004e4942, b'')
        if len(self.doc.get('buffers', [])) != 1 or self.doc['buffers'][0].get('uri'):
            raise ValueError('Expected a self-contained runtime GLB with one embedded buffer')
        self.cache = {}
        self.nodes = self.doc.get('nodes', [])
        self.names = {n.get('name', f'node_{i}'): i for i, n in enumerate(self.nodes)}
        if len(self.names) != len(self.nodes):
            raise ValueError('Node names must be unique for unambiguous gates')
        self.parents = {}
        for i, n in enumerate(self.nodes):
            for child in n.get('children', []):
                if child in self.parents:
                    raise ValueError('Node has multiple parents')
                self.parents[child] = i
        self.rest = self.pose(None, np.array([0.]))[0]

    def accessor(self, index):
        if index in self.cache:
            return self.cache[index]
        a = self.doc['accessors'][index]
        dtype = np.dtype({5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2',
                          5125: '<u4', 5126: '<f4'}[a['componentType']])
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]

        def read(view, count, columns, dtype, offset=0):
            bv = self.doc['bufferViews'][view]
            if bv.get('buffer', 0) != 0:
                raise ValueError('External buffer')
            stride = bv.get('byteStride', columns*dtype.itemsize)
            end = offset+(count-1)*stride+columns*dtype.itemsize if count else offset
            if offset < 0 or end > bv['byteLength'] or bv.get('byteOffset', 0)+end > len(self.data):
                raise ValueError('Accessor outside buffer view')
            return np.ndarray((count, columns), dtype, self.data, bv.get('byteOffset', 0)+offset,
                              strides=(stride, dtype.itemsize)).copy()

        out = read(a['bufferView'], a['count'], width, dtype, a.get('byteOffset', 0)) if 'bufferView' in a else \
            np.zeros((a['count'], width), dtype)
        if 'sparse' in a:
            s = a['sparse']; idx = s['indices']; val = s['values']
            dt = np.dtype({5121: 'u1', 5123: '<u2', 5125: '<u4'}[idx['componentType']])
            ids = read(idx['bufferView'], s['count'], 1, dt, idx.get('byteOffset', 0)).ravel()
            if np.any(ids >= a['count']) or np.any(np.diff(ids.astype(np.int64)) <= 0):
                raise ValueError('Invalid sparse accessor indices')
            out[ids] = read(val['bufferView'], s['count'], width, dtype, val.get('byteOffset', 0))
        if a.get('normalized'):
            if dtype.kind not in 'iu':
                raise ValueError('Only integer accessors can be normalized')
            out = np.maximum(out.astype(float)/np.iinfo(dtype).max, -1)
        self.cache[index] = out
        return out

    def pose(self, animation, times):
        count = len(times)
        channels = {}
        if animation is not None:
            for channel in animation['channels']:
                target = channel['target']; path = target['path']
                if path == 'weights':
                    raise ValueError('Morph animation is not supported; cannot certify this model')
                sampler = animation['samplers'][channel['sampler']]
                keys = self.accessor(sampler['input']).ravel()
                if not len(keys) or np.any(np.diff(keys) <= 0):
                    raise ValueError('Animation times must strictly increase')
                channels[target['node'], path] = interpolate(keys, self.accessor(sampler['output']), times,
                                                            sampler.get('interpolation', 'LINEAR'), path == 'rotation')
        local = np.broadcast_to(np.eye(4), (count, len(self.nodes), 4, 4)).copy()
        for i, node in enumerate(self.nodes):
            if 'matrix' in node:
                if any(k[0] == i for k in channels):
                    raise ValueError('Animated node uses a matrix instead of TRS')
                local[:, i] = np.array(node['matrix']).reshape(4, 4).T
                continue
            q = channels.get((i, 'rotation'), np.array(node.get('rotation', [0, 0, 0, 1.])))
            s = channels.get((i, 'scale'), np.array(node.get('scale', [1., 1, 1])))
            t = channels.get((i, 'translation'), np.array(node.get('translation', [0., 0, 0])))
            local[:, i, :3, :3] = rotation(q)*s[..., None, :]
            local[:, i, :3, 3] = t
        world = np.empty_like(local); done = set(); visiting = set()

        def visit(i):
            if i in done:
                return
            if i in visiting:
                raise ValueError('Cyclic node graph')
            visiting.add(i)
            if i in self.parents:
                visit(self.parents[i])
                world[:, i] = world[:, self.parents[i]] @ local[:, i]
            else:
                world[:, i] = C @ local[:, i]
            visiting.remove(i); done.add(i)

        for i in range(len(self.nodes)):
            visit(i)
        return world

    def clips(self):
        result = []
        for a in self.doc.get('animations', []):
            arrays = [self.accessor(s['input']).ravel() for s in a['samplers']]
            result.append((a.get('name', f'clip_{len(result)}'), a,
                           min(x[0] for x in arrays), max(x[-1] for x in arrays)))
        if len(set(x[0] for x in result)) != len(result):
            raise ValueError('Duplicate animation names')
        return result


class Report:
    def __init__(self, config):
        self.config = config
        self.rows = {}; self.assets = []; self.sampling = []; self.timings = {}
        self.runner_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    def limit(self, key, clip):
        value = self.config.get('thresholds', {}).get(key, LIMITS[key])
        return self.config.get('clip_thresholds', {}).get(clip, {}).get(key, value)

    def add(self, gate, value, threshold, *, clip='static', lod='all', region='', time_s=None,
            lower=False, detail=None, status=None, unit_name='', asset='body'):
        key = (asset, clip, lod, gate, region)
        if value is not None:
            value = float(value)
            if not np.isfinite(value):
                raise ValueError(f'Non-finite measurement: {key}')
        if status is None:
            status = 'PASS' if (value >= threshold if lower else value <= threshold) else 'FAIL'
        row = {'asset': asset, 'clip': clip, 'lod': lod, 'gate': gate, 'region': region, 'status': status,
               'worst': value, 'time_s': None if time_s is None else float(time_s),
               'frame_48hz': None if time_s is None else float(time_s)*48,
               'threshold': threshold, 'comparison': '>=' if lower else '<=', 'unit': unit_name,
               'samples': 1, 'detail': detail}
        previous = self.rows.get(key)
        if previous:
            count = previous['samples']+1
            replace = previous['worst'] is None or (value is not None and
                      (value < previous['worst'] if lower else value > previous['worst']))
            if replace:
                self.rows[key] = row
            self.rows[key]['samples'] = count
        else:
            self.rows[key] = row
        if value is None or threshold is None:
            return False
        return abs(value-threshold) <= .2*max(abs(threshold), 1e-8)

    def missing(self, gate, reason, **kwargs):
        self.add(gate, None, None, status='UNVERIFIED', detail=reason, **kwargs)

    def series(self, gate, values, times, threshold, **kwargs):
        if not len(values):
            kwargs.pop('detail', None)
            return self.missing(gate, 'Too few samples', **kwargs)
        i = int(np.argmin(values) if kwargs.get('lower') else np.argmax(values))
        self.add(gate, values[i], threshold, time_s=times[i], **kwargs)
        key = (kwargs.get('asset', 'body'), kwargs.get('clip', 'static'), kwargs.get('lod', 'all'),
               gate, kwargs.get('region', ''))
        self.rows[key]['samples'] = len(values)

    def write(self, out, elapsed, error=None):
        rows = list(self.rows.values()); counts = dict(Counter(r['status'] for r in rows))
        status = 'ERROR' if error else 'FAIL' if counts.get('FAIL') else \
            'UNVERIFIED' if counts.get('UNVERIFIED') else 'PASS'
        payload = {'schema_version': 1, 'status': status, 'counts': counts, 'seconds': elapsed,
                   'runner_sha256': self.runner_sha256,
                   'assets': self.assets, 'config': self.config, 'default_thresholds': LIMITS,
                   'sampling': self.sampling, 'timings': self.timings, 'gates': rows, 'error': error}
        temporary = out/'.gates.json.tmp'
        temporary.write_text(json.dumps(payload, indent=2, allow_nan=False)+'\n')
        temporary.replace(out/'gates.json')
        lines = ['# Shared creature gates', '', f'**{status}** — {elapsed:.2f} seconds. {counts}', '',
                 'Times are seconds from the GLB animation timeline; frame = time × 48 (audit frame).',
                 'UNVERIFIED blocks completion. N/A means an explicitly inapplicable check.', '']
        summary = {}
        for row in rows:
            key = (row['asset'], row['clip'], row['lod'])
            summary.setdefault(key, Counter())[row['status']] += 1
        lines += ['| Asset | Clip | LOD | PASS | FAIL | UNVERIFIED |', '|---|---|---|---:|---:|---:|']
        for key, values in summary.items():
            lines.append('| '+' | '.join(key)+f" | {values['PASS']} | {values['FAIL']} | {values['UNVERIFIED']} |")
        lines += ['', '<details><summary>Every gate, value, time and threshold</summary>', '',
                 '| Asset | Clip | LOD | Gate / region | Result | Worst | Time / frame | Threshold |',
                 '|---|---|---|---|---|---:|---:|---:|']
        for r in rows:
            number = '—' if r['worst'] is None else f"{r['worst']:.6g} {r['unit']}"
            timing = '—' if r['time_s'] is None else f"{r['time_s']:.5f} / {r['frame_48hz']:.3f}"
            threshold = '—' if r['threshold'] is None else f"{r['comparison']} {r['threshold']:.6g}"
            lines.append(f"| {r['asset']} | {r['clip']} | {r['lod']} | {r['gate']} {r['region']} | "
                         f"{r['status']} | {number} | {timing} | {threshold} |")
        lines += ['', '</details>']
        notes = sorted(set(str(r['detail']) for r in rows if r['detail'] and r['status'] in ('UNVERIFIED', 'N/A')))
        if notes:
            lines += ['', '## Scope notes', ''] + ['- '+n for n in notes]
        if error:
            lines += ['', '## Error', '', str(error)]
        temporary = out/'.gates.md.tmp'; temporary.write_text('\n'.join(lines)+'\n'); temporary.replace(out/'gates.md')
        return status


def valid_ramps(doc, extras):
    mask, ramps = extras.get('openyamm_region_mask'), extras.get('openyamm_region_ramps')
    if mask is None and ramps is None:
        return True
    if not isinstance(mask, dict) or not isinstance(mask.get('index'), int) or \
            not 0 <= mask['index'] < len(doc.get('textures', [])) or \
            not isinstance(ramps, list) or not 1 <= len(ramps) <= 4:
        return False
    for ramp in ramps:
        if not isinstance(ramp, dict):
            return False
        rg, colors = ramp.get('range', []), ramp.get('colors', [])
        try:
            if len(rg) != 2 or not 0 <= rg[0] < rg[1] <= 1 or len(colors) != 16 or \
                    not all(len(c) == 3 and all(np.isfinite(x) and 0 <= x <= 1 for x in c) for c in colors):
                return False
        except (TypeError, ValueError):
            return False
    return True


def static_gates(glb, report, asset):
    doc = glb.doc
    report.assets.append({'asset': asset, 'path': str(glb.path), 'sha256': glb.sha256,
                          'bytes': glb.path.stat().st_size})
    for i, material in enumerate(doc.get('materials', [])):
        rejected = sorted(REJECTED.intersection(material.get('extensions', {})))
        report.add('material_extensions', len(rejected), 0, asset=asset, region=str(i), detail=rejected)
        report.add('region_ramps', int(not valid_ramps(doc, material.get('extras') or {})), 0,
                   asset=asset, region=str(i))
    counts = []
    for mi, mesh in enumerate(doc.get('meshes', [])):
        count = 0
        for pi, p in enumerate(mesh['primitives']):
            if p.get('mode', 4) != 4 or p.get('targets'):
                raise ValueError('Only triangle primitives without morph targets are supported')
            a = p['attributes']; n = len(glb.accessor(a['POSITION']))
            indices = glb.accessor(p['indices']).ravel() if 'indices' in p else np.arange(n)
            if len(indices) % 3 or np.any(indices >= n):
                raise ValueError('Invalid triangle indices')
            count += len(indices)//3
            weight_names = sorted(k for k in a if k.startswith('WEIGHTS_'))
            joint_names = sorted(k.replace('JOINTS_', 'WEIGHTS_') for k in a if k.startswith('JOINTS_'))
            if weight_names != joint_names:
                raise ValueError('JOINTS/WEIGHTS sets do not match')
            if weight_names:
                weights = np.concatenate([glb.accessor(a[k]) for k in weight_names], axis=1).astype(float)
                if len(weights) != n or not np.isfinite(weights).all() or (weights < 0).any():
                    raise ValueError('Invalid skin weights')
                report.add('weight_sum_error', abs(weights.sum(1)-1).max(), report.limit('weight_sum_error', 'static'),
                           asset=asset, lod=mesh.get('name', str(mi)), region=f'primitive {pi}')
        counts.append(count)
    for mi, mesh in enumerate(doc.get('meshes', [])):
        extras = mesh.get('extras', {})
        chains = [('colour', [mi]+extras.get('openyamm_lods', []))]
        if extras.get('openyamm_shadow_lods'):
            chains.append(('shadow', extras['openyamm_shadow_lods']))
        if not extras.get('openyamm_lods') and not extras.get('openyamm_shadow_lods') and \
                not any(n.get('mesh') == mi for n in glb.nodes):
            continue
        for kind, chain in chains:
            if len(set(chain)) != len(chain) or any(not isinstance(i, int) or not 0 <= i < len(counts) for i in chain):
                raise ValueError('Invalid LOD chain')
            for level, index in enumerate(chain):
                lod = f'{kind}{level}'
                cap = report.config.get('previous_counts', {}).get(asset, {}).get(kind, [])
                report.add('triangles', counts[index], cap[level] if level < len(cap) else None,
                           status=None if level < len(cap) else 'INFO',
                           asset=asset, lod=lod, detail='Count; optional previous-count cap')
                if level:
                    report.add('lod_strict_decrease', counts[index]-counts[chain[level-1]], -1,
                               asset=asset, lod=lod, unit_name='triangles')
                    report.add('lod_ratio', counts[index]/max(1, counts[chain[0]]),
                               report.limit(f'lod{min(level, 3)}_ratio', 'static'), asset=asset, lod=lod)
    return counts


class Mesh:
    def __init__(self, glb, mesh_index, node_index, label):
        self.glb, self.label, self.node = glb, label, node_index
        self.index = mesh_index; self.name = glb.doc['meshes'][mesh_index].get('name', str(mesh_index))
        vertices, faces, materials, joints, weights = [], [], [], [], []
        offset = 0; width = 0
        primitives = glb.doc['meshes'][mesh_index]['primitives']
        for p in primitives:
            width = max(width, 4*len([k for k in p['attributes'] if k.startswith('WEIGHTS_')]))
        for p in primitives:
            a = p['attributes']; co = glb.accessor(a['POSITION']).astype(float); n = len(co)
            ids = glb.accessor(p['indices']).ravel() if 'indices' in p else np.arange(n)
            vertices.append(co); faces.append(ids.reshape(-1, 3)+offset)
            materials.extend([p.get('material', -1)]*len(ids.reshape(-1, 3)))
            w = np.zeros((n, width)); j = np.zeros((n, width), dtype=int)
            for k in range(width//4):
                if f'WEIGHTS_{k}' in a:
                    w[:, k*4:k*4+4] = glb.accessor(a[f'WEIGHTS_{k}'])
                    j[:, k*4:k*4+4] = glb.accessor(a[f'JOINTS_{k}'])
            weights.append(w); joints.append(j); offset += n
        self.vertices = np.concatenate(vertices); self.faces = np.concatenate(faces).astype(int)
        self.materials = np.array(materials)
        self.weights, self.joints = np.concatenate(weights), np.concatenate(joints)
        if width:
            sums = self.weights.sum(1)
            if np.any(sums <= 0):
                raise ValueError('Zero skin weight sum')
            self.weights /= sums[:, None]  # The runtime normalizes after validating the raw sums.
        self.skin = glb.nodes[node_index].get('skin')
        if self.skin is not None:
            skin = glb.doc['skins'][self.skin]; self.skin_nodes = np.array(skin['joints'])
            if not width or self.joints.max() >= len(self.skin_nodes):
                raise ValueError('Skin missing weights or invalid joint index')
            self.bind = glb.accessor(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1) \
                if 'inverseBindMatrices' in skin else np.repeat(np.eye(4)[None], len(self.skin_nodes), axis=0)
            self.bone_names = [glb.nodes[i].get('name', str(i)) for i in self.skin_nodes]
        else:
            if width:
                raise ValueError('Weighted mesh has no skin node')
            self.bone_names = []
        self.rest = self.posed(glb.rest)
        if not np.isfinite(self.rest).all():
            raise ValueError('Non-finite vertices')
        e = np.sort(np.concatenate([self.faces[:, [0, 1]], self.faces[:, [1, 2]], self.faces[:, [2, 0]]]), axis=1)
        self.edges = np.unique(e, axis=0)
        self.lengths = np.linalg.norm(self.rest[self.edges[:, 0]]-self.rest[self.edges[:, 1]], axis=1)
        good = self.lengths > 1e-6
        self.edges, self.lengths = self.edges[good], self.lengths[good]
        # Only weld true UV seams: coincident vertices with different skinning can separate during animation.
        weld_key = self.vertices
        if self.skin is not None:
            joints = np.where(self.weights > 0, self.joints, 0)
            order = np.argsort(joints, axis=1, kind='stable')
            weld_key = np.concatenate([weld_key, np.take_along_axis(joints, order, axis=1),
                                       np.take_along_axis(self.weights, order, axis=1)], axis=1)
        _, self.weld_first, self.weld = np.unique(weld_key, axis=0, return_index=True, return_inverse=True)
        self.regions = {}
        self.components = None

    def posed(self, pose):
        if self.skin is None:
            return transform(pose[self.node], self.vertices)
        matrices = pose[self.skin_nodes] @ self.bind
        out = np.zeros_like(self.vertices)
        for k in range(self.weights.shape[1]):
            m = matrices[self.joints[:, k]]
            out += (np.einsum('nij,nj->ni', m[:, :3, :3], self.vertices)+m[:, :3, 3])*self.weights[:, k, None]
        return out

    def weight(self, patterns):
        if not self.bone_names:
            return np.zeros(len(self.rest))
        take = np.array([any(fnmatch.fnmatchcase(n, p) for p in patterns) for n in self.bone_names])
        return (take[self.joints]*self.weights).sum(1)

    def select(self, spec):
        if isinstance(spec, str):
            if spec not in self.regions:
                raise ValueError(f'Unknown region {spec} on {self.label}')
            return self.regions[spec].copy()
        mask = np.ones(len(self.rest), dtype=bool)
        if 'weights' in spec:
            mask &= self.weight(spec['weights']) > spec.get('weight_min', .3)
        if 'bounds' in spec:
            lo, hi = np.array(spec['bounds'], dtype=float)
            mask &= ((self.rest >= lo)&(self.rest <= hi)).all(1)
        if 'materials' in spec:
            ids = [i for i, m in enumerate(self.glb.doc.get('materials', []))
                   if any(fnmatch.fnmatchcase(m.get('name', ''), p) for p in spec['materials'])]
            allowed = np.zeros(len(mask), bool)
            allowed[self.faces[np.isin(self.materials, ids)].ravel()] = True
            mask &= allowed
        if 'vertices' in spec:
            allowed = np.zeros(len(mask), bool); allowed[spec['vertices']] = True; mask &= allowed
        if 'component_seeds' in spec:
            self.find_components()
            ids = [int(np.argmin(np.linalg.norm(self.rest-np.array(seed), axis=1))) for seed in spec['component_seeds']]
            mask &= np.isin(self.components, self.components[ids])
        if 'exclude' in spec:
            mask &= ~self.select(spec['exclude'])
        return mask

    def find_components(self):
        if self.components is not None:
            return
        parent = np.arange(len(self.weld_first))

        def root(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i

        for a, b, c in self.weld[self.faces]:
            p = root(a); parent[root(b)] = p; parent[root(c)] = p
        self.components = np.array([root(i) for i in self.weld])


def load_meshes(glb):
    result = []
    for ni, n in enumerate(glb.nodes):
        if 'mesh' not in n:
            continue
        mi = n['mesh']; extras = glb.doc['meshes'][mi].get('extras', {})
        for level, index in enumerate([mi]+extras.get('openyamm_lods', [])):
            result.append(Mesh(glb, index, ni, f'{n.get("name", ni)}/colour{level}'))
        for level, index in enumerate(extras.get('openyamm_shadow_lods', [])):
            result.append(Mesh(glb, index, ni, f'{n.get("name", ni)}/shadow{level}'))
    if not result:
        raise ValueError('No runtime mesh nodes')
    return result


def bone_name(config, name):
    return config.get('bones', {}).get(name, name)


def bone_gates(glb, pose, times, clip, config, report, props):
    """Vectorized over time; measure frames relative to the imported bind frame, never Euler angles."""
    def idx(name):
        return glb.names[bone_name(config, name)]

    def frame(name):
        return pose[:, idx(name)]

    def head(name):
        return frame(name)[:, :3, 3]

    def rest(name):
        return glb.rest[idx(name)]

    def axes(m):
        return m[..., :3, :3] / np.maximum(np.linalg.norm(m[..., :3, :3], axis=-2, keepdims=True), 1e-15)

    def emit(gate, values, region, lower=False, limit=None, selection=None, **kw):
        selected_times = times if selection is None else times[selection]
        values = values if selection is None else values[selection]
        report.series(gate, values, selected_times, report.limit(limit or gate, clip), clip=clip, lod='rig',
                      region=region, lower=lower, unit_name='deg', **kw)

    required = [f'B_{s}_{n}' for s in 'LR' for n in ('UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot')]
    missing = [n for n in required if bone_name(config, n) not in glb.names]
    if missing:
        report.missing('bone_anatomy', 'Missing joints: '+', '.join(missing), clip=clip, lod='rig')
        return
    for side in 'LR':
        un, fn, hn = (f'B_{side}_{n}' for n in ('UpperArm', 'Forearm', 'Hand'))
        u, f = unit(head(fn)-head(un)), unit(head(hn)-head(fn))
        ru = unit(rest(fn)[:3, 3]-rest(un)[:3, 3]); rf = unit(rest(hn)[:3, 3]-rest(fn)[:3, 3])
        ur, fr, hr = (axes(rest(n)) for n in (un, fn, hn))
        up, fp, hp = (axes(frame(n)) for n in (un, fn, hn))
        hand_config = config.get('hands', {}).get(side, {})
        # B_* source frames use -Z as the signed hinge; a fitted A-pose kink is not its anatomical plane.
        hinge_local = np.array(hand_config.get('elbow_hinge_axis', [0., 0, -1]))
        h = unit(np.einsum('tij,j->ti', up, hinge_local))
        flex = np.degrees(np.arctan2(np.sum(h*np.cross(u, f), axis=1), np.sum(u*f, axis=1)))
        emit('elbow_hyperextension_deg', -flex, side)
        emit('elbow_flexion_deg', flex, side)
        emit('elbow_plane_deg', abs(np.degrees(np.arcsin(np.clip(np.sum(f*h, axis=1), -1, 1)))), side)
        # Swing/twist decomposition removes bending before measuring axial strain.
        neutral_f = up @ ur.T @ fr
        rel_f = np.swapaxes(neutral_f, -1, -2) @ fp
        _, forearm_roll = swing_twist(rel_f, fr.T @ rf)
        emit('forearm_roll_deg', abs(forearm_roll), side)
        twist_name = f'B_{side}_ForearmTwist'
        if bone_name(config, twist_name) in glb.names:
            tr = axes(rest(twist_name)); tp = axes(frame(twist_name))
            neutral = up @ ur.T @ tr
            _, twist_roll = swing_twist(np.swapaxes(neutral, -1, -2) @ tp, tr.T @ rf)
            emit('forearm_roll_deg', abs(twist_roll), side+' twist')
            report.series('roll_step_deg', abs(np.diff(np.unwrap(np.radians(twist_roll))))*180/np.pi,
                          times[1:], report.limit('roll_step_deg', clip), clip=clip, lod='rig',
                          region=side+' forearm twist', unit_name='deg')
        # Wrist roll starts at the skin's distal forearm, after its distributed twist.
        neutral_h = tp @ tr.T @ hr if bone_name(config, twist_name) in glb.names else fp @ fr.T @ hr
        rel_h = np.swapaxes(neutral_h, -1, -2) @ hp
        fingers = hand_config.get('fingers', [f'B_{side}_Finger{i}' for i in range(5)])
        fingers = [bone_name(config, n) for n in fingers]
        finger_nodes = [glb.names[n] for n in fingers if n in glb.names]
        axis_h = unit(np.mean(glb.rest[finger_nodes, :3, 3], axis=0)-rest(hn)[:3, 3]) if finger_nodes else rf
        swing, wrist_roll = swing_twist(rel_h, hr.T @ axis_h)
        emit('wrist_flexion_deg', swing, side)
        emit('wrist_roll_deg', abs(wrist_roll), side)
        for label, values in [('forearm', forearm_roll), ('wrist', wrist_roll)]:
            delta = abs(np.diff(np.unwrap(np.radians(values))))*180/np.pi
            report.series('roll_step_deg', delta, times[1:], report.limit('roll_step_deg', clip),
                          clip=clip, lod='rig', region=f'{side} {label}', unit_name='deg')
        parent = glb.parents.get(idx(un))
        if parent is not None:
            neutral_u = axes(pose[:, parent]) @ axes(glb.rest[parent]).T @ ur
            _, upper_roll = swing_twist(np.swapaxes(neutral_u, -1, -2) @ up, ur.T @ ru)
            emit('upper_arm_roll_deg', abs(upper_roll), side)
        for name in (un, fn, hn):
            r = axes(frame(name)); dt = np.diff(times)
            velocities = rotation_vector(r[1:] @ np.swapaxes(r[:-1], -1, -2))/dt[:, None]
            steps = np.linalg.norm(velocities, axis=1)*dt*180/np.pi
            lim = report.limit('rotation_step_deg', clip)
            source = config.get('source_rotation_limits', {}).get(clip, {})
            group = 'hands' if name == hn else 'arms'
            if group in source:
                lim = source[group]+10.
            report.series('rotation_step_deg', steps, times[1:], lim, clip=clip, lod='rig', region=name,
                          unit_name='deg', detail='Source maximum + 10 deg' if group in source else 'Absolute limit')
            acc = np.linalg.norm(np.diff(velocities, axis=0), axis=1)/((dt[1:]+dt[:-1])/2)*180/np.pi
            report.series('angular_acceleration_deg_s2', acc, times[1:-1],
                          report.limit('angular_acceleration_deg_s2', clip), clip=clip, lod='rig', region=name,
                          unit_name='deg/s²')
        holds = []
        for prop in props:
            for hand in prop.get('hands', []):
                if hand['side'] == side:
                    mask = held_samples(prop, hand, clip, times)
                    mask &= np.linalg.norm(pose[:, idx(prop['node']), :3, :3], axis=(1, 2)) > 1e-7
                    if mask.any():
                        holds.append((prop, hand, mask))
        held = np.logical_or.reduce([mask for _, _, mask in holds]) if holds else np.zeros(len(times), bool)
        palm_axis = hand_config.get('palm_axis')
        if palm_axis is None and len(finger_nodes) == 5:
            # Calibrate the source hand axes from its knuckles; anatomical L/R fixes the palm/dorsum sign.
            wrist = rest(hn)[:3, 3]
            normal = np.cross(glb.rest[finger_nodes[1], :3, 3]-wrist, glb.rest[finger_nodes[4], :3, 3]-wrist)
            if np.linalg.norm(normal) > 1e-8:
                palm_axis = hr.T @ unit(normal)*(1 if side == 'R' else -1)
        if palm_axis is None:
            report.missing('palm_direction', f'Configure hands.{side}.palm_axis (signed hand-local normal)',
                           clip=clip, lod='rig', region=side)
        else:
            normal = unit(np.einsum('tij,j->ti', hp, np.array(palm_axis)))
            origin = head(hn)
            if finger_nodes:
                origin = .5*(origin+np.mean(pose[:, finger_nodes][:, :, :3, 3], axis=1))
            if holds:
                for prop, hand, mask in holds:
                    node = idx(prop['node'])
                    center = np.array(hand.get('grip_point', prop.get('grip_point', [0, 0, 0])))
                    goal = np.einsum('tij,j->ti', pose[:, node, :3, :3], center)+pose[:, node, :3, 3]
                    emit('palm_grip_deg', angle(normal, goal-origin), f'{side} {prop["name"]}', selection=mask)
            if clip_matches(clip, config.get('clips', {}).get('rest', ['Standing', 'Fidget'])) or \
                    clip_matches(clip, config.get('clips', {}).get('walk', ['Walking'])):
                goal = head(f'B_{side}_Thigh')-origin
                goal[:, 2] = 0
                if (~held).any():
                    emit('palm_thigh_deg', angle(normal, goal), side, selection=~held)
            elif not held.all():
                report.add('palm_direction', None, None, status='N/A', clip=clip, lod='rig', region=side,
                           detail='Free-hand action has no configured palm target')
        if holds:
            curls = []
            for fi in finger_nodes[1:]:
                children = glb.nodes[fi].get('children', [])
                if children and glb.nodes[children[0]].get('children'):
                    mid = children[0]; tip = glb.nodes[mid]['children'][0]
                    a = unit(pose[:, mid, :3, 3]-pose[:, fi, :3, 3])
                    b = unit(pose[:, tip, :3, 3]-pose[:, mid, :3, 3])
                    curl = angle(a, b)
                    if palm_axis is not None:
                        delta = axes(pose[:, fi]) @ axes(glb.rest[fi]).T
                        direction = unit(glb.rest[mid, :3, 3]-glb.rest[fi, :3, 3])
                        curl = finger_curl(a, b, delta, direction, hr @ np.array(palm_axis))
                    curls.append(curl)
            if curls:
                emit('finger_curl_min_deg', np.mean(curls, axis=0), side, lower=True, selection=held)
            else:
                report.missing('finger_curl_min_deg', 'Finger chains missing', clip=clip, lod='rig', region=side)
    # G6 also covers helper twists, fingers, and prop attachment rotations.
    handled = {idx(f'B_{s}_{n}') for s in 'LR' for n in ('UpperArm', 'Forearm', 'Hand')}
    for name, ni in glb.names.items():
        logical = next((k for k, v in config.get('bones', {}).items() if v == name), name)
        custom_fingers = [f for hand in config.get('hands', {}).values() for f in hand.get('fingers', [])]
        if ni in handled or not ('Twist' in logical or 'Finger' in logical or
                                 any(name.startswith(f) for f in custom_fingers) or name in [p['node'] for p in props]):
            continue
        r = axes(pose[:, ni]); steps = np.linalg.norm(rotation_vector(r[1:] @ np.swapaxes(r[:-1], -1, -2)), axis=1)
        visible = np.linalg.norm(pose[:, ni, :3, :3], axis=-2).min(1) > 1e-7
        valid = visible[:-1] & visible[1:]
        source = config.get('source_rotation_limits', {}).get(clip, {})
        group = 'arms' if 'Twist' in logical else 'hands'
        limit = source[group]+10 if group in source else report.limit('rotation_step_deg', clip)
        if valid.any():
            report.series('rotation_step_deg', np.degrees(steps[valid]), times[1:][valid], limit,
                          clip=clip, lod='rig', region=name, unit_name='deg')
        else:
            report.add('rotation_step_deg', None, None, status='N/A', clip=clip, lod='rig', region=name,
                       detail='No consecutive visible attachment samples')
    if all(bone_name(config, n) in glb.names for n in ('B_Pelvis', 'B_Neck')):
        pelvis = head('B_Pelvis')[:, 2]
        trunk = angle(head('B_Neck')-head('B_Pelvis'), [0, 0, 1])
        # Posture has no universal numerical acceptance threshold in the batch rules.
        for gate, values, lower in [('pelvis_min_m', pelvis, True), ('pelvis_max_m', pelvis, False),
                                    ('trunk_lean_deg', trunk, False)]:
            limit = config.get('posture', {}).get(clip, config.get('posture', {}).get('*', {})).get(gate)
            if limit is None:
                i = np.argmin(values) if lower else np.argmax(values)
                report.add(gate, values[i], None, status='UNVERIFIED', clip=clip, lod='rig',
                           time_s=times[i], lower=lower,
                           detail='Posture measured; configure per-clip acceptance limits')
            else:
                report.series(gate, values, times, limit, clip=clip, lod='rig', lower=lower)


def clip_matches(clip, patterns):
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        raise ValueError('Clip selectors must be lists of glob strings')
    return any(fnmatch.fnmatchcase(clip, p) for p in patterns)


def held_samples(prop, hand, clip, times):
    times = np.asarray(times)
    if not clip_matches(clip, prop.get('clips', ['*'])) or not clip_matches(clip, hand.get('clips', ['*'])):
        return np.zeros(times.shape, bool)
    intervals = hand.get('intervals', {}).get(clip)
    if intervals is None:
        return np.ones(times.shape, bool)
    result = np.zeros(times.shape, bool)
    for start, end in intervals:
        result |= (times >= start-1e-9)&(times <= end+1e-9)
    return result


def exact_ray_parity(triangles, point, direction):
    """Double-precision triangle intersections resolve BVH grazing/self-hit ambiguity."""
    points = np.asarray(point); scalar = points.ndim == 1
    points = np.atleast_2d(points)
    e1 = triangles[:, 1]-triangles[:, 0]; e2 = triangles[:, 2]-triangles[:, 0]
    h = np.cross(direction, e2); determinant = np.sum(e1*h, axis=1)
    good = abs(determinant) > 1e-12*np.linalg.norm(e1, axis=1)*np.linalg.norm(e2, axis=1)
    inv = np.divide(1., determinant, out=np.zeros_like(determinant), where=good)
    coefficients = [h*inv[:, None], np.cross(e1, direction)*inv[:, None],
                    np.cross(e1, e2)*inv[:, None]]
    offsets = [np.sum(triangles[:, 0]*c, axis=1) for c in coefficients]
    result = np.empty(len(points), bool)
    for start in range(0, len(points), 128):
        batch = points[start:start+128]
        u, v, t = [batch @ c.T-o for c, o in zip(coefficients, offsets)]
        valid = good & (u >= -1e-9) & (v >= -1e-9) & (u+v <= 1+1e-9) & (t > 1e-7)
        count = np.zeros(len(batch), int)
        # Deduplicate shared edges, but preserve a close exit/entry between touching parts.
        for sign in (-1, 1):
            distances = np.sort(np.where(valid & (determinant*sign > 0), t, np.inf), axis=1)
            count += np.isfinite(distances[:, 0]).astype(int)
            count += np.sum(np.isfinite(distances[:, 1:]) &
                            (distances[:, 1:] > distances[:, :-1]+1e-7), axis=1)
        result[start:start+len(batch)] = count % 2
    return bool(result[0]) if scalar else result


class Surface:
    """A welded, optionally capped surface; one posed BVH reused by all queries in a sample."""
    def __init__(self, mesh, mask, cap=False, opening=None):
        faces = mesh.weld[mesh.faces[np.all(mask[mesh.faces], axis=1)]]
        good = (faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 2] != faces[:, 0])
        self.faces = faces[good]; self.mesh = mesh; self.loops = []; self.opening = None; self.opening_sign = 1
        self.explicit_opening = opening if opening and 'node' in opening else None
        if not len(self.faces):
            raise ValueError(f'Empty surface on {mesh.label}')
        edges = np.concatenate([self.faces[:, [0, 1]], self.faces[:, [1, 2]], self.faces[:, [2, 0]]])
        keys, first, counts = np.unique(np.sort(edges, axis=1), axis=0, return_index=True, return_counts=True)
        self.closed = bool(np.all(counts == 2))
        if cap and np.any(counts > 2):
            raise ValueError(f'Non-manifold cloth surface on {mesh.label}; refine region selector')
        if cap:
            boundary = [tuple(e) for e in edges[first[counts == 1]]]
            outgoing = {}
            for a, b in boundary:
                if a in outgoing:
                    raise ValueError('Branched cloth boundary; refine selector')
                outgoing[a] = b
            while outgoing:
                start = next(iter(outgoing)); loop = [start]; here = start
                while True:
                    if here not in outgoing:
                        raise ValueError('Open cloth boundary chain')
                    here = outgoing.pop(here)
                    if here == start:
                        break
                    loop.append(here)
                self.loops.append(np.array(loop))
            if opening is not None and not self.explicit_opening and not self.loops:
                raise ValueError('Cloth opening requested but no boundary loops found')
            if opening is not None and not self.explicit_opening:
                axis = unit(opening.get('axis', [0, 0, -1]))
                centroids = [mesh.rest[mesh.weld_first[loop]].mean(0) for loop in self.loops]
                self.opening = int(np.argmin(np.linalg.norm(np.array(centroids)-opening['loop_seed'], axis=1))) \
                    if 'loop_seed' in opening else int(np.argmax(np.array(centroids) @ axis))
                p = mesh.rest[mesh.weld_first[self.loops[self.opening]]]
                normal = -np.sum(np.cross(p-p.mean(0), np.roll(p, -1, axis=0)-p.mean(0)), axis=0)
                self.opening_sign = 1 if normal @ axis >= 0 else -1
            self.closed = True
        self.ids = np.unique(self.faces)
        mesh.find_components()
        self.face_components = mesh.components[mesh.weld_first[self.faces[:, 0]]]

    def build(self, points, pose=None):
        from mathutils.bvhtree import BVHTree
        self.points = points[self.mesh.weld_first]
        faces = self.faces.tolist(); coords = self.points.tolist(); self.caps = set(); self.plane = None
        for i, loop in enumerate(self.loops):
            p = self.points[loop]; center = p.mean(0); ci = len(coords); coords.append(center.tolist())
            normal = -unit(np.sum(np.cross(p-center, np.roll(p, -1, axis=0)-center), axis=0))
            if i == self.opening:
                self.plane = (center, normal*self.opening_sign)
            for a, b in zip(loop, np.roll(loop, -1)):
                self.caps.add(len(faces)); faces.append([int(b), int(a), ci])
        if self.explicit_opening:
            spec = self.explicit_opening
            if pose is None or spec['node'] not in self.mesh.glb.names:
                raise ValueError('Explicit cloth opening needs a valid animated node')
            matrix = pose[self.mesh.glb.names[spec['node']]]
            self.plane = (transform(matrix, np.array(spec['point'])),
                          unit(np.linalg.inv(matrix[:3, :3]).T @ spec['axis']))
        self.tree = BVHTree.FromPolygons(coords, faces, all_triangles=True)
        self.component_trees = {}
        self.lo = self.points[self.ids].min(0); self.hi = self.points[self.ids].max(0)
        return self

    def signed(self, points, containment=False):
        """Exact nearest triangle distance, parity for closed volumes; open sheets use oriented normals.

        Blender exposes scalar BVH traversal only. Array culling, transforms, normal
        tests, and reduction are vectorized; never build a BVH per queried vertex.
        """
        from mathutils import Vector
        points = np.asarray(points)
        distance = np.full(len(points), np.inf); face = np.full(len(points), -1, int)
        if not len(points):
            return distance, face
        candidates = np.arange(len(points)) if containment else \
            np.flatnonzero(((points >= self.lo-1e-7)&(points <= self.hi+1e-7)).all(1))
        if not len(candidates):
            return distance, face
        hits = [self.tree.find_nearest(Vector(p)) for p in points[candidates]]
        closest = np.array([tuple(h[0]) for h in hits]); normals = np.array([tuple(h[1]) for h in hits])
        ds = np.array([h[3] for h in hits]); faces = np.array([h[2] for h in hits])
        normal_dot = np.sum((points[candidates]-closest)*normals, axis=1)
        inside = normal_dot < -.7*ds
        if self.closed:
            # Float32 BVH traversal can miss a thin exit face without repeating a hit.
            inside = self.exact_inside(points[candidates], (.811107, .357913, .463187))
            distance[candidates] = np.where(inside, -ds, ds); face[candidates] = faces
            return distance, face
        directions = [(.932, .217, .291), (-.313, .901, .299), (.243, -.372, .896)]
        for k in (range(len(candidates)) if self.closed else np.flatnonzero(inside)):
            point = points[candidates[k]]
            votes = 0
            tree = self.tree
            if not self.closed:
                component = self.face_components[faces[k]]
                if component not in self.component_trees:
                    from mathutils.bvhtree import BVHTree
                    selected = self.faces[self.face_components == component]
                    self.component_trees[component] = BVHTree.FromPolygons(self.points.tolist(), selected.tolist(),
                                                                         all_triangles=True)
                tree = self.component_trees[component]
            for vector in directions:
                pair_inside = True
                # An open patch can intercept every forward ray from empty space; require its opposite too.
                for sign in ([1] if self.closed else [1, -1]):
                    direction = Vector(vector).normalized()*sign
                    origin = Vector(point); n = 0; seen = set()
                    for _ in range(128):
                        hit = tree.ray_cast(origin, direction)
                        if hit[0] is None:
                            break
                        if hit[2] in seen:
                            n = self.exact_inside(point, direction, None if self.closed else component)
                            break
                        seen.add(hit[2])
                        n += 1
                        # Grazing float32 hits can lie behind the origin; traversal must advance monotonically.
                        origin += direction*(max(0., hit[3])+1e-6)
                    else:
                        n = self.exact_inside(point, direction, None if self.closed else component)
                    if not n % 2:
                        pair_inside = False
                        break
                votes += pair_inside
            inside[k] = votes > len(directions)//2
        distance[candidates] = np.where(inside, -ds, ds); face[candidates] = faces
        return distance, face

    def exact_inside(self, point, direction, component=None):
        faces = self.faces if component is None else self.faces[self.face_components == component]
        triangles = [self.points[faces]]
        if component is None:
            for loop in self.loops:
                p = self.points[loop]; centers = np.repeat(p.mean(0)[None], len(p), axis=0)
                triangles.append(np.stack([np.roll(p, -1, axis=0), p, centers], axis=1))
        return exact_ray_parity(np.concatenate(triangles), point, direction)

    def gap(self, points):
        from mathutils import Vector
        if not len(points):
            raise ValueError('Cannot measure contact on an empty region')
        bounds = np.linalg.norm(np.maximum(np.maximum(self.lo-points, points-self.hi), 0), axis=1)
        seed = int(np.argmin(bounds)); best = self.tree.find_nearest(Vector(points[seed]))[3]
        candidates = np.flatnonzero(bounds < best)
        for i in candidates:
            if bounds[i] < best:
                distance = self.tree.find_nearest(Vector(points[i]), best)[3]
                if distance is not None:
                    best = min(best, distance)
        return best


def penetration(surface, points, containment=False):
    ids = np.arange(len(points))
    if surface.plane is not None:
        center, normal = surface.plane
        ids = np.flatnonzero((points-center) @ normal < 0)
    distances, faces = surface.signed(points[ids], containment)
    depth = np.maximum(distances if containment else -distances, 0)
    if not len(depth):
        return 0., None
    i = int(np.argmax(depth))
    return float(depth[i]*1000), int(ids[i])


def configure_mesh(mesh, config, report):
    aliases = config.get('bones', {})
    defaults = {}
    for s in 'LR':
        for part, terms in [('arm', ['UpperArm', 'UpperArmTwist', 'Forearm', 'ForearmTwist', 'Hand']),
                            ('hand', ['Hand', 'Finger']),
                            ('limb', ['Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger']),
                            ('leg', ['Thigh', 'Calf', 'Foot', 'Toe0']), ('foot', ['Foot', 'Toe0'])]:
            patterns = [aliases.get(f'B_{s}_{t}', f'B_{s}_{t}')+'*' for t in terms]
            if part in ('hand', 'limb'):
                patterns += [bone_name(config, n)+'*' for n in config.get('hands', {}).get(s, {}).get('fingers', [])]
            defaults[f'{part}_{s}'] = {'weights': patterns, 'weight_min': .2 if part == 'limb' else .3}
    defaults['head'] = {'weights': [aliases.get('B_Head', 'B_Head')], 'weight_min': .7}
    definitions = {**defaults, **config.get('regions', {}),
                   **config.get('lod_regions', {}).get(mesh.label.split('/')[-1], {})}
    def dependencies(spec):
        return [spec] if isinstance(spec, str) else dependencies(spec['exclude']) if 'exclude' in spec else []

    pending = dict(definitions)
    while pending:
        ready = [name for name, spec in pending.items() if all(d in mesh.regions for d in dependencies(spec))]
        if not ready:
            raise ValueError(f'Unknown or cyclic region references: {sorted(pending)}')
        for name in ready:
            mesh.regions[name] = mesh.select(pending.pop(name))
    mesh.cloth = []; cloth_mask = np.zeros(len(mesh.rest), bool)
    for cloth in config.get('cloth', []):
        target = mesh.select(cloth['surface']); cloth_mask |= target
        samples = mesh.select(cloth['samples']) & ~target
        try:
            surface = Surface(mesh, target, cap=True, opening=cloth.get('opening'))
            if not samples.any():
                raise ValueError('Empty cloth sample region')
            mesh.cloth.append((cloth['name'], surface, samples, cloth.get('containment', True)))
        except ValueError as e:
            report.missing('cloth_setup', str(e), lod=mesh.label, region=cloth['name'])
    mesh.solid = ~cloth_mask
    mesh.surfaces = {}; mesh.contact_samples = {}
    for s in 'LR':
        mask = mesh.solid & ~mesh.regions[f'limb_{s}']
        forearm = bone_name(config, f'B_{s}_Forearm')+'*'
        samples = (mesh.regions[f'hand_{s}'] | (mesh.weight([forearm]) > .5)) & ~cloth_mask
        if samples.any():
            try:
                mesh.surfaces[s] = Surface(mesh, mask)
                mesh.contact_samples[s] = samples
            except ValueError as e:
                report.missing('arm_body_setup', str(e), lod=mesh.label, region=s)
    head = mesh.regions['head'] & ~cloth_mask
    # Exclude the connected neck joint; a configured head region can retain an exact exposed collar boundary.
    neck = bone_name(config, 'B_Neck')
    if 'head' not in config.get('regions', {}) and neck in mesh.glb.names:
        head &= mesh.rest[:, 2] > mesh.glb.rest[mesh.glb.names[neck], 2, 3]+.015
    try:
        target = mesh.select('head_obstacles') if 'head_obstacles' in mesh.regions else \
            mesh.solid & (mesh.weight([bone_name(config, 'B_Head'), bone_name(config, 'B_Neck')]) < .2)
        mesh.head_surface = Surface(mesh, target)
        mesh.head_samples = head
    except ValueError:
        mesh.head_surface = None
    if mesh.head_surface is None or not head.any():
        report.missing('head_setup', 'Empty head samples or obstacle surface; refine regions', lod=mesh.label)
    mesh.edge_regions = {}
    for name in ['arm_L', 'arm_R', 'hand_L', 'hand_R']:
        mask = mesh.regions[name]
        mesh.edge_regions[name] = mask[mesh.edges].all(1)
    for name in ('arm', 'hand'):
        mesh.edge_regions[name] = mesh.edge_regions[name+'_L'] | mesh.edge_regions[name+'_R']
    mesh.feet = {}
    for side in 'LR':
        mask = mesh.regions[f'foot_{side}'] & mesh.solid
        ids = np.flatnonzero(mask)
        if not len(ids):
            report.missing('sole_setup', 'No foot-weighted vertices', lod=mesh.label, region=side)
            continue
        low = mesh.rest[ids, 2].min()
        ids = ids[mesh.rest[ids, 2] <= low+config.get('sole_band_m', .005)]
        # UV and normal seams must not bias the sole plane or heel/toe centroids.
        ids = mesh.weld_first[np.unique(mesh.weld[ids])]
        along = mesh.rest[ids] @ unit(config.get('forward', [0, -1, 0]))
        mesh.feet[side] = (ids, ids[along <= np.quantile(along, .3)], ids[along >= np.quantile(along, .7)])
    mesh.prop_surfaces = {}


def grip_points(mesh, side, config):
    """Surface samples include triangle interiors, preventing coarse fingers from missing a narrow grip."""
    hand = mesh.regions['hand_'+side]
    tris = mesh.faces[hand[mesh.faces].all(1)]
    bary = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, .5, 0], [0, .5, .5], [.5, 0, .5], [1/3]*3])
    if not len(tris):
        return None
    labels = []
    fingers = config.get('hands', {}).get(side, {}).get('fingers', [f'B_{side}_Finger{i}' for i in range(5)])
    for part in [bone_name(config, f'B_{side}_Hand')]+[bone_name(config, n)+'*' for n in fingers]:
        w = mesh.weight([part])
        labels.append(np.einsum('sk,tk->ts', bary, w[tris]).ravel() > .3)
    digest = hashlib.sha256()
    for data in (mesh.vertices[tris], mesh.joints[tris], mesh.weights[tris], mesh.skin_nodes, mesh.bind, *labels):
        digest.update(data.tobytes())
    return tris, bary, labels, digest.hexdigest()


def mesh_sample(mesh, points, pose, t, clip, config, report, prop_data, feet_trace, grip_cache, travel_direction=None):
    near = False

    def emit(gate, value, region='', limit=None, detail=None, lower=False, threshold=None):
        nonlocal near
        lim = report.limit(limit or gate, clip) if threshold is None else threshold
        near |= report.add(gate, value, lim, clip=clip, lod=mesh.label, region=region, time_s=t,
                           lower=lower, detail=detail)

    ratio = np.linalg.norm(points[mesh.edges[:, 0]]-points[mesh.edges[:, 1]], axis=1)/mesh.lengths
    for region, take in mesh.edge_regions.items():
        kind = region.split('_')[0]
        if take.any():
            values = ratio[take]; edge = mesh.edges[np.flatnonzero(take)[int(np.argmax(values))]]
            emit(kind+'_stretch_p99', np.percentile(values, 99), region)
            emit(kind+'_stretch_max', values.max(), region, detail={'edge': edge.tolist()})
        else:
            report.missing(kind+'_stretch', 'Empty arm/hand edge region', clip=clip, lod=mesh.label, region=region)
    rest_clip = clip_matches(clip, config.get('clips', {}).get('rest', ['Standing', 'Fidget']))
    walk_clip = clip_matches(clip, config.get('clips', {}).get('walk', ['Walking']))
    run_clip = clip_matches(clip, config.get('clips', {}).get('run', ['Running']))
    foot_row = {'time': t}
    floor = config.get('floor_m', 0.)
    for side, (ids, heel, toe) in mesh.feet.items():
        sole = points[ids]; low = sole[:, 2].min()-floor
        h, tip = points[heel].mean(0), points[toe].mean(0)
        _, singular, v = np.linalg.svd(sole-sole.mean(0), full_matrices=False)
        tilt = float(angle(v[-1] if v[-1, 2] >= 0 else -v[-1], [0, 0, 1])) \
            if len(singular) >= 3 and singular[1] > 1e-6 else None
        yaw_dir = tip-h; yaw_dir[2] = 0
        forward = np.array(travel_direction if travel_direction is not None else config.get('forward', [0., -1, 0]))
        forward[2] = 0
        yaw = float(angle(yaw_dir, forward))
        joint_names = [bone_name(config, f'B_{side}_{n}') for n in ('Thigh', 'Calf', 'Foot')]
        if all(n in mesh.glb.names for n in joint_names):
            th, knee, ankle = [pose[mesh.glb.names[n], :3, 3] for n in joint_names]
            knee_deg = float(angle(knee-th, ankle-knee))
        else:
            knee_deg = None
        foot_row[side] = {'low': float(low), 'heel': float(h[2]-floor), 'toe': float(tip[2]-floor),
                          'knee': knee_deg, 'tilt': tilt}
        emit('floor_penetration_mm', max(0, -low)*1000, side)
        report.add('lowest_sole_m', low, None, status='INFO', clip=clip, lod=mesh.label, region=side,
                   time_s=t, lower=True)
        if rest_clip:
            emit('rest_sole_height_mm', max(abs(h[2]-floor), abs(tip[2]-floor))*1000, side,
                 detail={'heel_mm': float(h[2]-floor)*1000, 'toe_mm': float(tip[2]-floor)*1000})
            if tilt is None:
                report.missing('rest_sole_tilt_deg', 'Sole patch lacks three non-collinear vertices',
                               clip=clip, lod=mesh.label, region=side)
            else:
                emit('rest_sole_tilt_deg', tilt, side)
        if walk_clip or run_clip or rest_clip:
            if np.linalg.norm(yaw_dir) < 1e-6:
                report.missing('foot_yaw_deg', 'Heel/toe patches have no horizontal separation',
                               clip=clip, lod=mesh.label, region=side)
            else:
                emit('foot_yaw_deg', yaw, side)
        if walk_clip:
            for key in ('walking_lift_min_mm', 'walking_lift_max_mm'):
                limit = report.limit(key, clip)*config.get('gait_scale', 1.)
                near |= abs(low*1000-limit) <= .2*abs(limit)
    if run_clip and all(s in foot_row for s in 'LR'):
        low = min(foot_row[s]['low'] for s in 'LR')*1000
        for key in ('running_airborne_mm', 'contact_height_mm'):
            limit = report.limit(key, clip)
            near |= abs(low-limit) <= .2*abs(limit)
    feet_trace.append(foot_row)
    for side, surface in mesh.surfaces.items():
        depth, vertex = penetration(surface.build(points), points[mesh.contact_samples[side]])
        emit('arm_body_penetration_mm', depth, side, limit='penetration_mm',
             detail={'sample_vertex': vertex, 'sign': 'ray parity' if surface.closed else 'oriented open surface'})
    if mesh.head_surface and mesh.head_samples.any():
        depth, vertex = penetration(mesh.head_surface.build(points), points[mesh.head_samples])
        emit('head_penetration_mm', depth, detail={'sample_vertex': vertex})
    for name, surface, samples, containment in mesh.cloth:
        depth, vertex = penetration(surface.build(points, pose), points[samples], containment=containment)
        emit('cloth_penetration_mm', depth, name,
             detail={'sample_vertex': vertex, 'mode': 'containment' if containment else 'collision'})
    for prop in prop_data:
        name = prop['name']
        if not clip_matches(clip, prop.get('clips', ['*'])):
            continue
        node = mesh.glb.names[bone_name(config, prop['node'])]; matrix = pose[node]
        if np.linalg.norm(matrix[:3, :3], axis=0).max() < 1e-7:
            continue  # Runtime zero-scale attachment hiding (e.g. an arrow after release).
        level = int(mesh.label[-1])
        pm = prop['meshes'][min(level, len(prop['meshes'])-1)]
        prop_points = transform(matrix @ np.linalg.inv(C), pm.rest)
        held = tuple(sorted({h['side'] for h in prop.get('hands', []) if held_samples(prop, h, clip, t)}))
        surface_key = (name, held)
        if surface_key not in mesh.prop_surfaces:
            mask = mesh.solid.copy()
            for side in held:
                mask &= ~mesh.regions['hand_'+side]
            try:
                mesh.prop_surfaces[surface_key] = Surface(mesh, mask)
            except ValueError as e:
                mesh.prop_surfaces[surface_key] = None
                report.missing('prop_body_setup', str(e), clip=clip, lod=mesh.label, region=name)
        if mesh.prop_surfaces[surface_key] is not None:
            depth, vertex = penetration(mesh.prop_surfaces[surface_key].build(points), prop_points)
            emit('prop_body_penetration_mm', depth, name, limit='penetration_mm', detail={'prop_vertex': vertex})
        for hand in prop.get('hands', []):
            if not held_samples(prop, hand, clip, t):
                continue
            side = hand['side']; key = (name, level, side)
            if key not in mesh.grip_samples:
                mesh.grip_samples[key] = grip_points(mesh, side, config)
            spec = mesh.grip_samples[key]
            surfaces = prop.get('grip_surfaces', {}).get(side, [])
            if spec is None or not surfaces:
                report.missing('grip_contact', 'Configure a nonempty grip surface and hand region',
                               clip=clip, lod=mesh.label, region=f'{name} {side}')
                continue
            tris, bary, groups, signature = spec
            surface_index = min(level, len(surfaces)-1)
            cache_key = (name, side, signature, prop['grip_signatures'][side][surface_index])
            if cache_key not in grip_cache:
                world = np.einsum('sk,tkj->tsj', bary, points[tris]).reshape(-1, 3)
                local = transform(C @ np.linalg.inv(matrix), world)
                local, inverse = np.unique(local, axis=0, return_inverse=True)
                groups = [np.bincount(inverse, weights=mask, minlength=len(local)) > 0 for mask in groups]
                surface = surfaces[surface_index]
                gaps = [surface.gap(local[mask])*1000 if mask.any() else None for mask in groups]
                solid = prop['solid_surfaces'][min(level, len(prop['solid_surfaces'])-1)]
                distances, _ = solid.signed(local)
                grip_cache[cache_key] = (gaps, max(0., -distances.min())*1000)
            gaps, depth = grip_cache[cache_key]
            roots = config.get('hands', {}).get(side, {}).get('fingers',
                                                              [f'B_{side}_Finger{i}' for i in range(5)])
            for label, gap in zip(['palm'] + roots, gaps):
                if gap is None:
                    report.missing('grip_gap_mm', 'No weighted surface samples', clip=clip, lod=mesh.label,
                                   region=f'{name} {side} {label}')
                    continue
                emit('grip_gap_mm', gap, f'{name} {side} {label}')
            emit('grip_penetration_mm', depth, f'{name} {side}')
    return near


def finish_feet(trace, mesh, clip, config, report):
    trace.sort(key=lambda r: r['time']); times = np.array([r['time'] for r in trace])
    walk = clip_matches(clip, config.get('clips', {}).get('walk', ['Walking']))
    run = clip_matches(clip, config.get('clips', {}).get('run', ['Running']))
    if not walk and not run:
        return
    if not all('L' in r and 'R' in r for r in trace):
        report.missing('locomotion', 'Both soles required', clip=clip, lod=mesh.label)
        return
    low = np.array([min(r['L']['low'], r['R']['low']) for r in trace])
    if run:
        contact = (low*1000 <= report.limit('contact_height_mm', clip)).astype(float)
        fraction = np.trapezoid(contact, times)/(times[-1]-times[0]) if times[-1] > times[0] else contact[0]
        report.add('running_contact_pct', fraction*100, report.limit('running_contact_pct', clip),
                   clip=clip, lod=mesh.label, lower=True,
                   detail='Time-weighted contact; adaptive samples are not votes')
        report.series('running_airborne_mm', low*1000, times, report.limit('running_airborne_mm', clip),
                      clip=clip, lod=mesh.label)
    if walk:
        for s in 'LR':
            peak = max(trace, key=lambda r: r[s]['low']); row = peak[s]
            scale = config.get('gait_scale', 1.)
            for gate, value, lower in [('walking_lift_min_mm', row['low']*1000, True),
                                       ('walking_lift_max_mm', row['low']*1000, False),
                                       ('walking_knee_min_deg', row['knee'], True),
                                       ('walking_knee_max_deg', row['knee'], False)]:
                if value is None:
                    report.missing(gate, 'Missing leg joints', clip=clip, lod=mesh.label, region=s)
                else:
                    limit = report.limit(gate, clip)*(scale if 'lift' in gate else 1.)
                    report.add(gate, value, limit, clip=clip, lod=mesh.label, region=s, time_s=peak['time'],
                               lower=lower, detail={'heel_peak_mm': max(r[s]['heel'] for r in trace)*1000,
                                                   'toe_peak_mm': max(r[s]['toe'] for r in trace)*1000})


def prop_timing(prop, pose, times, glb, clip, config, report):
    if prop.get('kind') != 'melee' or not clip_matches(clip, prop.get('clips', ['*'])) or \
            not clip_matches(clip, config.get('clips', {}).get('attack', ['Attack*', 'Cast'])):
        return
    node = glb.names[bone_name(config, prop['node'])]
    for level, mesh in enumerate(prop['meshes']):
        vertices = transform(np.linalg.inv(C), mesh.rest)
        grip = np.array(prop.get('grip_point', [0., 0, 0]))
        tip = np.array(prop.get('tip', vertices[np.argmax(np.linalg.norm(vertices-grip, axis=1))]))
        m = pose[:, node]; pos = np.einsum('tij,j->ti', m[:, :3, :3], tip)+m[:, :3, 3]
        direction = unit(np.einsum('tij,j->ti', m[:, :3, :3], tip-grip))
        velocity = np.diff(pos, axis=0)/np.diff(times)[:, None]; speed = np.linalg.norm(velocity, axis=1)
        mid = (times[:-1]+times[1:])/2; pointing = angle(unit(direction[:-1]+direction[1:]),
                                                                     config.get('forward', [0, -1, 0]))
        good = pointing <= report.limit('blow_pointing_deg', clip)
        lod = 'colour'+str(level)
        if not good.any() or not len(speed) or speed.max() < 1e-6:
            report.add('blow_target_motion', 0, 1, lower=True, asset=prop['name'], clip=clip, lod=lod,
                       detail='No tip motion while pointing at target')
            continue
        i = int(np.argmax(np.where(good, speed, -1)))
        report.add('blow_speed_fraction', speed[i]/speed.max(), report.limit('blow_speed_fraction', clip),
                   lower=True, asset=prop['name'], clip=clip, lod=lod, time_s=mid[i],
                   detail={'tip_speed_m_s': float(speed[i]), 'pointing_deg': float(pointing[i])})
        impact = prop.get('impacts', {}).get(clip)
        report.add('blow_time_error_s', None if impact is None else abs(mid[i]-impact),
                   report.limit('blow_time_error_s', clip), asset=prop['name'], clip=clip, lod=lod, time_s=mid[i],
                   status='UNVERIFIED' if impact is None else None,
                   detail='Configure prop.impacts to compare binding timing' if impact is None else None)
        edge = prop.get('edge_axis')
        if edge is None:
            report.missing('blade_edge_share', 'Configure signed edge_axis in attachment-node coordinates',
                           asset=prop['name'], clip=clip, lod=lod)
        else:
            e = unit(np.einsum('tij,j->ti', m[:, :3, :3], unit(edge)))
            flat = unit(np.cross(direction, e)); vel = velocity[i]; edge_speed = vel @ unit(e[i]+e[i+1])
            flat_speed = vel @ unit(flat[i]+flat[i+1])
            share = abs(edge_speed)/max(math.hypot(edge_speed, flat_speed), 1e-12)
            axial = np.linalg.norm(np.cross(unit(tip-grip), unit(edge))) < 1e-8
            report.add('blade_edge_share', None if axial else share, report.limit('blade_edge_share', clip),
                       lower=True, asset=prop['name'], clip=clip, lod=lod, time_s=mid[i],
                       status='N/A' if axial else None,
                       detail='Axial thrust has no distinct flat direction; signed tip lead is checked separately'
                       if axial else None)
            report.add('blade_signed_lead', edge_speed/max(speed[i], 1e-12), report.limit('blade_signed_lead', clip),
                       lower=True, asset=prop['name'], clip=clip, lod=lod, time_s=mid[i])


def load_props(config, base, body, report):
    props = []
    for spec in config.get('props', []):
        prop = copy.deepcopy(spec)
        if bone_name(config, prop['node']) not in body.names:
            raise ValueError(f'Unknown attachment node {prop["node"]}')
        glb = Glb(base/prop['file']); static_gates(glb, report, prop['name'])
        meshes = [m for m in load_meshes(glb) if '/colour' in m.label]
        if any(m.skin is not None for m in meshes):
            raise ValueError('Separate skinned prop needs its own run; attachment props must be rigid')
        prop['meshes'] = meshes; prop['grip_surfaces'] = {}; prop['grip_signatures'] = {}
        prop['solid_surfaces'] = [Surface(m, np.ones(len(m.rest), bool)).build(m.rest) for m in meshes]
        for hand in prop.get('hands', []):
            spec = hand.get('surface', prop.get('grip_surface'))
            if spec is None:
                continue
            surfaces = []
            for mesh in meshes:
                try:
                    surface = Surface(mesh, mesh.select(spec))
                    surfaces.append(surface.build(mesh.rest))
                except ValueError as e:
                    report.missing('grip_surface_setup', str(e), asset=prop['name'], lod=mesh.label,
                                   region=hand['side'])
                    surfaces = []; break
            prop['grip_surfaces'][hand['side']] = surfaces
            prop['grip_signatures'][hand['side']] = [
                hashlib.sha256(m.rest.tobytes()+m.faces.tobytes()+s.faces.tobytes()).hexdigest()
                for m, s in zip(meshes, surfaces)]
        props.append(prop)
    return props


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError('Config must be a JSON object')
    allowed = {'version', 'thresholds', 'clip_thresholds', 'source_rotation_limits', 'posture', 'bones', 'hands',
               'clips', 'forward', 'floor_m', 'sole_band_m', 'gait_scale', 'regions', 'lod_regions', 'cloth',
               'props', 'previous_counts', 'refine_hz'}
    unknown = set(config)-allowed
    if unknown:
        raise ValueError(f'Unknown config fields: {sorted(unknown)}')
    if config.get('version', 1) != 1:
        raise ValueError('Config version must be 1')
    for overrides in [config.get('thresholds', {}), *config.get('clip_thresholds', {}).values()]:
        if set(overrides)-set(LIMITS):
            raise ValueError(f'Unknown thresholds: {set(overrides)-set(LIMITS)}')
        if not all(isinstance(v, (int, float)) and np.isfinite(v) for v in overrides.values()):
            raise ValueError('Thresholds must be finite numbers')
    if config.get('refine_hz', 48) not in [48, 96, 192]:
        raise ValueError('refine_hz must be 48, 96 or 192')
    forward = np.array(config.get('forward', [0, -1, 0]), float)
    if forward.shape != (3,) or not np.isfinite(forward).all() or np.linalg.norm(forward[:2]) < 1e-6:
        raise ValueError('forward must be a finite horizontal direction')
    names = [p['name'] for p in config.get('props', [])]
    if len(set(names)) != len(names):
        raise ValueError('Prop names must be unique')
    if any(h['side'] not in ('L', 'R') for p in config.get('props', []) for h in p.get('hands', [])):
        raise ValueError('Grip side must be L or R')
    def keys(value, allowed, label):
        if not isinstance(value, dict) or set(value)-set(allowed):
            raise ValueError(f'Invalid {label} fields; allowed: {sorted(allowed)}')

    def selector(value):
        if isinstance(value, str):
            return
        keys(value, ['weights', 'weight_min', 'bounds', 'materials', 'vertices', 'exclude', 'component_seeds'],
             'selector')
        if 'exclude' in value:
            selector(value['exclude'])

    for regions in [config.get('regions', {}), *config.get('lod_regions', {}).values()]:
        for spec in regions.values():
            selector(spec)
    for cloth in config.get('cloth', []):
        keys(cloth, ['name', 'surface', 'samples', 'opening', 'containment'], 'cloth')
        if not isinstance(cloth.get('containment', True), bool):
            raise ValueError('Cloth containment must be a boolean')
        selector(cloth['surface']); selector(cloth['samples'])
        if 'opening' in cloth:
            opening = cloth['opening']
            keys(opening, ['axis', 'loop_seed', 'node', 'point'], 'cloth opening')
            if ('node' in opening) != ('point' in opening) or ('node' in opening and 'loop_seed' in opening):
                raise ValueError('Opening uses either loop_seed or both node and point')
            for name in ('axis', 'point', 'loop_seed'):
                if name in opening:
                    v = np.asarray(opening[name], float)
                    if v.shape != (3,) or not np.isfinite(v).all() or (name == 'axis' and np.linalg.norm(v) < 1e-8):
                        raise ValueError('Cloth opening vectors must be finite, and axis nonzero')
            if 'node' in opening and 'axis' not in opening:
                raise ValueError('An explicit opening needs its local outward axis')
    for hand in config.get('hands', {}).values():
        keys(hand, ['palm_axis', 'elbow_hinge_axis', 'fingers'], 'hand')
        if 'fingers' in hand and (len(hand['fingers']) < 2 or
                                 len(set(hand['fingers'])) != len(hand['fingers'])):
            raise ValueError('hands.fingers must list distinct roots, thumb first, followed by the fingers')
    for prop in config.get('props', []):
        keys(prop, ['name', 'file', 'node', 'kind', 'clips', 'hands', 'grip_surface', 'grip_point',
                    'tip', 'edge_axis', 'impacts'], 'prop')
        if prop.get('kind') not in ('melee', 'bow', 'shield', 'projectile', 'other'):
            raise ValueError('Specify prop kind: melee, bow, shield, projectile, other')
        sides = [h['side'] for h in prop.get('hands', [])]
        if len(set(sides)) != len(sides):
            raise ValueError('Declare each hand at most once per prop')
        if 'grip_surface' in prop:
            selector(prop['grip_surface'])
        for hand in prop.get('hands', []):
            keys(hand, ['side', 'clips', 'intervals', 'surface', 'grip_point'], 'prop hand')
            for intervals in hand.get('intervals', {}).values():
                for interval in intervals:
                    if len(interval) != 2 or not np.isfinite(interval).all() or not 0 <= interval[0] <= interval[1]:
                        raise ValueError('Held intervals must be [start_s, end_s] with 0 <= start <= end')
            if 'surface' in hand:
                selector(hand['surface'])


def run(path, config, base, out, report):
    started = time.perf_counter(); glb = Glb(path)
    static_gates(glb, report, 'body'); meshes = load_meshes(glb)
    all_labels = [m.label for m in meshes]
    unique = []; aliases = {}; signatures = {}
    for mesh in meshes:
        digest = hashlib.sha256()
        for array in (mesh.vertices, mesh.faces, mesh.joints, mesh.weights, mesh.materials):
            digest.update(array.tobytes())
        signature = (mesh.node, mesh.skin, mesh.label[-1], digest.hexdigest())
        if signature in signatures and not config.get('lod_regions'):
            aliases[mesh.label] = signatures[signature]
        else:
            signatures[signature] = mesh.label; unique.append(mesh)
    meshes = unique
    props = load_props(config, base, glb, report)
    for mesh in meshes:
        configure_mesh(mesh, config, report); mesh.grip_samples = {}
    report.timings['load_and_setup_s'] = time.perf_counter()-started
    if 'props' not in config:
        report.missing('prop_inventory', 'Declare props (or [] for unarmed) to certify attachment coverage')
    if 'cloth' not in config:
        report.missing('cloth_inventory', 'Declare cloth pieces/openings (or [] for no separate cloth)')
    clips = glb.clips()
    if not clips:
        report.missing('animations', 'No animation clips in runtime GLB')
    for clip, animation, start, end in clips:
        tic = time.perf_counter(); times = sample_grid(start, end, 48)
        poses = glb.pose(animation, times)
        travel = None
        pelvis = glb.names.get(bone_name(config, 'B_Pelvis'))
        if pelvis is not None and len(times) > 1:
            path = poses[:, pelvis, :3, 3].copy(); path[:, 2] = 0
            if np.linalg.norm(path[-1]-path[0]) > .02:
                travel = np.gradient(path, times, axis=0)
                slow = np.linalg.norm(travel, axis=1) < .02
                travel[slow] = config.get('forward', [0., -1, 0])
        bone_gates(glb, poses, times, clip, config, report, props)
        for prop in props:
            prop_timing(prop, poses, times, glb, clip, config, report)
        coarse = sample_grid(start, end, 24)
        traces = {m.label: [] for m in meshes}; near = set(); seen = set()

        def sample(t):
            i = int(np.argmin(abs(times-t)))
            pose = poses[i] if abs(times[i]-t) < 1e-9 else glb.pose(animation, np.array([t]))[0]
            needed = False; grip_cache = {}
            for mesh in meshes:
                needed |= mesh_sample(mesh, mesh.posed(pose), pose, t, clip, config, report, props,
                                      traces[mesh.label], grip_cache,
                                      None if travel is None else travel[i])
            seen.add(round(float(t), 12))
            return needed

        for i, t in enumerate(coarse):
            if sample(t):
                near.update(j for j in (i-1, i) if 0 <= j < len(coarse)-1)
        for trace in traces.values():
            if all('L' in r and 'R' in r for r in trace):
                contact = [min(r[s]['low'] for s in 'LR')*1000-report.limit('contact_height_mm', clip) for r in trace]
                near.update(i for i in range(len(contact)-1) if contact[i]*contact[i+1] < 0)
        refine_hz = config.get('refine_hz', 48)
        for j in sorted(near):
            interval = sample_grid(coarse[j], coarse[j+1], refine_hz)
            for t in interval:
                if round(float(t), 12) not in seen:
                    sample(t)
        for mesh in meshes:
            finish_feet(traces[mesh.label], mesh, clip, config, report)
        report.sampling.append({'clip': clip, 'start_s': float(start), 'end_s': float(end),
                                'bone_hz': 48, 'bone_samples': len(times), 'mesh_base_hz': 24,
                                'refine_hz': refine_hz, 'mesh_samples': len(seen),
                                'refined_intervals': len(near), 'mesh_times_s': sorted(seen)})
        report.timings[clip] = time.perf_counter()-tic
        print(f'GATES {clip}: {len(times)} bone / {len(seen)} mesh samples, '
              f'{report.timings[clip]:.2f}s', flush=True)
    # Byte-identical colour/shadow geometry shares numeric evaluation, with explicit report provenance.
    for alias, original in aliases.items():
        for key, row in list(report.rows.items()):
            if row['lod'] == original and row['asset'] == 'body':
                item = dict(row, lod=alias, shared_evidence=original+' (identical geometry and weights)')
                report.rows[(item['asset'], item['clip'], alias, item['gate'], item['region'])] = item
    # Rig evidence is shared, but the report explicitly accounts for every shipped LOD.
    for key, row in list(report.rows.items()):
        if row['lod'] != 'rig':
            continue
        del report.rows[key]
        for label in all_labels:
            item = dict(row, lod=label, shared_evidence='same runtime skeleton')
            report.rows[(item['asset'], item['clip'], item['lod'], item['gate'], item['region'])] = item
    # Detect a concurrent export; the input bytes used above remain identified by SHA-256.
    for asset in report.assets:
        if hashlib.sha256(Path(asset['path']).read_bytes()).hexdigest() != asset['sha256']:
            report.missing('input_changed', 'Input changed during audit; rerun on a stable export',
                           asset=asset['asset'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path, help='Exported runtime body GLB (includes its LOD extras)')
    parser.add_argument('--config', type=Path, help='JSON creature intent; paths relative to this file')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    report = Report({}); started = time.perf_counter(); error = None
    (out/'gates.json').write_text('{"schema_version": 1, "status": "RUNNING"}\n')
    (out/'gates.md').write_text('# Shared creature gates\n\nRUNNING — results are not complete.\n')
    try:
        config = json.loads(args.config.read_text()) if args.config else {}
        report.config = config
        validate_config(config)
        run(args.glb, config, args.config.resolve().parent if args.config else args.glb.resolve().parent, out, report)
    except Exception as e:
        import traceback
        traceback.print_exc(); error = f'{type(e).__name__}: {e}'
    status = report.write(out, time.perf_counter()-started, error)
    print(f'GATES {status}: {out}/gates.md ({time.perf_counter()-started:.2f}s)', flush=True)
    if status != 'PASS':
        # Blender treats an ordinary sys.exit specially; an exception honours --python-exit-code.
        raise RuntimeError(f'Gate run {status}; see {out}/gates.json')


if __name__ == '__main__':
    main()
