#!/usr/bin/env python3
"""Rig and animation audit of creature GLBs, without Blender (MM6-MM8 audit, 2026-11-11).

    motion_audit.py <glb> [<glb> ...] --out <dir> [--fps 30]

Writes <dir>/<stem>.json per GLB. Everything is measured on LOD0 (no LOD1..3, no shadow meshes), posed by linear-blend
skinning with floor/glb_pose.py, every clip sampled at --fps. H is the largest extent of the first Standing frame (else
the bind pose); distances and speeds are in H and H per second.

Deformation (per triangle, against the bind-pose triangle; triangles of hidden parts - skin scale under 0.2 - and
degenerate rest triangles are skipped):
- stretch s1 and squash s2: singular values of the in-plane map from the rest to the posed triangle;
- fold: the posed normal points away (over 90 degrees) from the rest normal carried rigidly by the triangle's dominant
  joint: the surface turned inside out, the candy-wrapper and crumpled-hand case;
- bad = fold, s1 > 1.6 or s2 < 0.55. Per clip and body region (hand, arm, head, spine, leg, tail, wing, cloth, other,
  from joint names; triangles on parts whose skin scale differs from 1 by over 15 % are skipped): the largest share of the region's surface that is bad in one frame, the frame, and the joint with the
  largest bad share of its own surface (hotspot). Compare a clip with the same model's Standing clip: a rest pose
  away from the bind pose already squashes shoulders.

Motion (per clip, displacement from the clip's first frame):
- amp_p50 / amp_p90 / amp_max: area-weighted percentiles of each vertex's largest displacement, in H;
- body_share: share of the surface that moves more than 0.05 H at some time (a whole-body move vs an arm wave);
- region_amp: largest displacement per region; torso_turn_deg: largest rotation of a spine-region joint from frame 0;
- peak_speed: largest area-weighted p95 vertex speed of any frame (H/s); accel_p99: p99 of the per-frame vertex
  acceleration (H/s^2), a jitter indicator to compare with accepted clips;
- loop_pop: largest vertex distance between the first and last frame (H), reported for looping clips only.
Clip pairs whose trajectories (16 normalised times, 600 vertices) differ by under 0.02 H RMS are listed as
near-duplicates.

Mesh: triangle counts per LOD and shadow LOD, LOD0 sliver share (smallest angle under 3 degrees, by count), welded
boundary and non-manifold edge counts, connected components; LOD1..3 rest-pose deviation: p95 of the distance from
each LOD vertex to the nearest LOD0 vertex, in H.
"""
import argparse
import json
from pathlib import Path
import re
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent / 'floor'))
import glb_pose  # noqa: E402

REGIONS = ['hand', 'arm', 'head', 'spine', 'leg', 'tail', 'wing', 'cloth', 'other']
REGION_PATTERNS = [
    ('hand', r'hand|finger|thumb|index|middle|ring|pinky|palm|wrist|digit|claw'),
    ('cloth', r'skirt|robe|cloth|cape|cloak|dress|coat|tabard|sleeve|flap|hem|loincloth|apron'),
    ('wing', r'(?<!s)wing'),
    ('tail', r'tail'),
    ('arm', r'arm|elbow|shoulder|clavicle|collar'),
    ('head', r'head|neck|jaw|eye|ear|mouth|tongue|brow|lip|beard|hair|skull|horn|nose|teeth|mandible'),
    ('leg', r'leg|thigh|knee|calf|shin|foot|toe|ankle|paw|heel|hoof'),
    ('spine', r'spine|chest|torso|hips|pelvis|root|body|belly|abdomen|waist|thorax|ribs'),
]
LOOPING = re.compile(r'^(standing|walking|walk\d*|running|run\d*|jog|sprint|fly|flying|hover|swim|fidget_loop|idle)$',
                     re.I)
STRETCH, SQUASH = 1.6, 0.55


def region_of(name):
    lower = (name or '').lower()
    for region, pattern in REGION_PATTERNS:
        if re.search(pattern, lower):
            return region
    return 'other'


class Audit:
    def __init__(self, path):
        self.path = Path(path)
        self.glb = glb_pose.Glb(path)
        self.model = glb_pose.Model(self.glb)
        doc = self.glb.json
        nodes = doc['nodes']
        keep = []
        for primitive in self.model.primitives:
            node = nodes[primitive['node']]
            name = (doc['meshes'][node['mesh']].get('name') or '') + ' ' + (node.get('name') or '')
            if 'shadow' not in name.lower():
                keep.append(primitive)
        self.model.primitives = keep
        self.joint_names = [nodes[j].get('name', str(j)) for j in self.model.joints]
        self.joint_region = np.array([REGIONS.index(region_of(n)) for n in self.joint_names] or [0])
        # Concatenate LOD0 primitives.
        positions, triangles, vjoint, offset = [], [], [], 0
        self.parts = []
        for primitive in keep:
            p = primitive['positions']
            positions.append(p)
            triangles.append(primitive['triangles'] + offset)
            if primitive['skinned']:
                top = primitive['joints'][np.arange(len(p)), np.argmax(primitive['weights'], axis=1)]
            else:
                top = np.full(len(p), -1)
            vjoint.append(top)
            self.parts.append((offset, len(p), primitive))
            offset += len(p)
        self.rest = np.concatenate(positions)
        self.tris = np.concatenate(triangles)
        self.vjoint = np.concatenate(vjoint)
        # Triangle dominant joint: summed weights over its corners.
        tri_joint = np.full(len(self.tris), -1)
        if self.model.joints:
            nj = len(self.model.joints)
            acc = np.zeros((len(self.tris), nj))
            for offset, count, primitive in self.parts:
                if not primitive['skinned']:
                    continue
                lo, hi = offset, offset + count
                mask = (self.tris[:, 0] >= lo) & (self.tris[:, 0] < hi)
                index = np.nonzero(mask)[0]
                for corner in range(3):
                    v = self.tris[index, corner] - lo
                    for k in range(primitive['joints'].shape[1]):
                        np.add.at(acc, (index, primitive['joints'][v, k]), primitive['weights'][v, k])
            skinned = acc.sum(axis=1) > 0
            tri_joint[skinned] = np.argmax(acc[skinned], axis=1)
        self.tri_joint = tri_joint
        self.tri_region = np.where(tri_joint >= 0, self.joint_region[np.maximum(tri_joint, 0)], REGIONS.index('other'))
        a, b, c = (self.rest[self.tris[:, k]] for k in range(3))
        cross = np.cross(b - a, c - a)
        self.rest_area = 0.5 * np.linalg.norm(cross, axis=1)
        self.rest_normal = cross / np.maximum(2 * self.rest_area[:, None], 1e-20)
        self.rest_2d = self._frame(a, b, c)
        valid_area = self.rest_area > max(1e-12, 1e-7 * np.median(self.rest_area))
        self.valid = valid_area & (np.abs(np.linalg.det(self.rest_2d)) > 1e-20)
        vertex_area = np.zeros(len(self.rest))
        for k in range(3):
            np.add.at(vertex_area, self.tris[:, k], self.rest_area / 3)
        self.vertex_area = vertex_area
        self.vertex_region = np.where(self.vjoint >= 0, self.joint_region[np.maximum(self.vjoint, 0)],
                                      REGIONS.index('other'))
        # Penetration: hand vertices against the core (spine, head and leg regions) surface.
        core = {REGIONS.index(r) for r in ('spine', 'head', 'leg')}
        self.hand_vertices = np.nonzero(self.vertex_region == REGIONS.index('hand'))[0]
        self.core_tris = np.nonzero(np.isin(self.tri_region, list(core)) & self.valid)[0]
        standing = next((c for c in self.model.clips if c.lower() == 'standing'), None)
        ref = self.pose(standing, self.model.clip_times(standing)[0])[0] if standing else self.rest
        self.height = float(np.max(ref.max(axis=0) - ref.min(axis=0)))

    @staticmethod
    def _frame(a, b, c):
        e1, e2 = b - a, c - a
        u = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-20)
        n = np.cross(e1, e2)
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
        v = np.cross(n, u)
        m = np.empty((len(a), 2, 2))
        m[:, 0, 0] = np.einsum('ij,ij->i', e1, u)
        m[:, 0, 1] = np.einsum('ij,ij->i', e2, u)
        m[:, 1, 0] = np.einsum('ij,ij->i', e1, v)
        m[:, 1, 1] = np.einsum('ij,ij->i', e2, v)
        return m

    def pose(self, clip, time):
        """Posed LOD0 vertices, per-vertex skin scale and the joint palette (None for a rigid model)."""
        world = self.model.world(self.model.sample(clip, time) if clip else {})
        palette = None
        if self.model.joints:
            palette = world[self.model.joints] @ self.model.inverse_binds if self.model.inverse_binds is not None \
                else world[self.model.joints]
        out = np.empty_like(self.rest)
        scale = np.ones(len(self.rest))
        for offset, count, primitive in self.parts:
            p = self.rest[offset:offset + count]
            h = np.concatenate([p, np.ones((count, 1))], axis=1)
            if primitive['skinned']:
                m = np.einsum('vk,vkij->vij', primitive['weights'], palette[primitive['joints']])
                out[offset:offset + count] = np.einsum('vij,vj->vi', m, h)[:, :3]
                scale[offset:offset + count] = np.abs(np.linalg.det(m[:, :3, :3])) ** (1 / 3)
            else:
                m = world[primitive['node']]
                out[offset:offset + count] = (h @ m.T)[:, :3]
                scale[offset:offset + count] = abs(np.linalg.det(m[:3, :3])) ** (1 / 3)
        return out, scale, palette, world

    def deformation(self, posed, scale, palette):
        a, b, c = (posed[self.tris[:, k]] for k in range(3))
        p2 = self._frame(a, b, c)
        f = p2 @ np.linalg.inv(np.where(self.valid[:, None, None], self.rest_2d, np.eye(2)))
        s = np.linalg.svd(f, compute_uv=False)
        normal = np.cross(b - a, c - a)
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-20)
        if palette is not None:
            rot = palette[np.maximum(self.tri_joint, 0), :3, :3]
            predicted = np.einsum('tij,tj->ti', rot, self.rest_normal)
            predicted /= np.maximum(np.linalg.norm(predicted, axis=1, keepdims=True), 1e-20)
            fold = (np.einsum('ij,ij->i', normal, predicted) < 0) & (self.tri_joint >= 0)
        else:
            fold = np.zeros(len(self.tris), bool)
        # Hidden (under 0.2) and scale-animated parts (a reactor's unfolding arms) are not skin deformation.
        hidden = (np.abs(scale[self.tris] - 1) > 0.15).any(axis=1)
        live = self.valid & ~hidden
        return s[:, 0], s[:, 1], fold, live

    def penetration(self, posed, scale):
        """Share of the visible hand vertices more than 0.02 H inside the core surface, and the deepest (H): the nearest
        core triangle centroid's plane decides inside (its normal points out), checked against the 6 nearest."""
        tris = self.core_tris[(scale[self.tris[self.core_tris]] >= 0.2).all(axis=1)]
        hands = self.hand_vertices[scale[self.hand_vertices] >= 0.2]
        if not len(tris) or not len(hands):
            return 0.0, 0.0
        a, b, c = (posed[self.tris[tris, k]] for k in range(3))
        centre = (a + b + c) / 3
        normal = np.cross(b - a, c - a)
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-20)
        tree = cKDTree(centre)
        p = posed[hands]
        dist, index = tree.query(p, k=6)
        signed = np.einsum('vkj,vkj->vk', p[:, None, :] - centre[index], normal[index])
        # Inside when every one of the nearest planes has the point behind it, and the nearest is within 0.1 H.
        depth = -signed.max(axis=1)
        inside = (depth > 0.02 * self.height) & (dist[:, 0] < 0.1 * self.height)
        return float(inside.mean()), float(depth[inside].max() / self.height) if inside.any() else 0.0

    def clip(self, name, fps):
        times = self.model.clip_times(name)
        n = max(2, int(round((times[-1] - times[0]) * fps)) + 1)
        samples = np.linspace(times[0], times[-1], n)
        frames, worst_s1, worst_s2 = [], np.ones(len(self.tris)), np.ones(len(self.tris))
        region_bad = np.zeros((n, len(REGIONS)))
        nj = max(1, len(self.model.joints))
        joint_bad = np.zeros((n, nj))
        fold_area = np.zeros(n)
        spine_joints = [i for i, r in enumerate(self.joint_region) if REGIONS[r] == 'spine'] if self.model.joints else []
        torso_turn = 0.0
        base_rot = None
        hand_inside = np.zeros(n)
        hand_depth = np.zeros(n)
        for i, t in enumerate(samples):
            posed, scale, palette, world = self.pose(name, t)
            frames.append(posed)
            s1, s2, fold, live = self.deformation(posed, scale, palette)
            if self.hand_vertices.size and self.core_tris.size:
                hand_inside[i], hand_depth[i] = self.penetration(posed, scale)
            bad = live & ((s1 > STRETCH) | (s2 < SQUASH) | fold)
            worst_s1 = np.where(live, np.maximum(worst_s1, s1), worst_s1)
            worst_s2 = np.where(live, np.minimum(worst_s2, s2), worst_s2)
            region_bad[i] = np.bincount(self.tri_region[bad], self.rest_area[bad], len(REGIONS))
            fold_area[i] = self.rest_area[live & fold].sum()
            if self.model.joints:
                j = self.tri_joint[bad]
                keep = j >= 0
                joint_bad[i] = np.bincount(j[keep], self.rest_area[bad][keep], nj)
            if spine_joints:
                rot = world[[self.model.joints[k] for k in spine_joints], :3, :3]
                rot = rot / np.maximum(np.linalg.norm(rot, axis=1, keepdims=True), 1e-20)
                if base_rot is None:
                    base_rot = rot
                rel = np.einsum('kji,kjl->kil', base_rot, rot)
                cos = np.clip((np.trace(rel, axis1=1, axis2=2) - 1) / 2, -1, 1)
                torso_turn = max(torso_turn, float(np.degrees(np.arccos(cos)).max()))
        frames = np.array(frames)
        h = self.height
        region_total = np.bincount(self.tri_region[self.valid], self.rest_area[self.valid], len(REGIONS))
        joint_total = np.bincount(self.tri_joint[self.valid & (self.tri_joint >= 0)],
                                  self.rest_area[self.valid & (self.tri_joint >= 0)], nj) if self.model.joints \
            else np.ones(1)
        share = region_bad / np.maximum(region_total, 1e-20)
        deform = {}
        for r, region in enumerate(REGIONS):
            if region_total[r] <= 0.002 * region_total.sum():
                continue
            k = int(np.argmax(share[:, r]))
            deform[region] = {'bad_pct': round(100 * float(share[k, r]), 1), 'time': round(float(samples[k]), 3)}
        hotspot = None
        if self.model.joints:
            jshare = joint_bad / np.maximum(joint_total, 1e-20)
            jshare[:, joint_total < 0.001 * joint_total.sum()] = 0
            k, j = np.unravel_index(int(np.argmax(jshare)), jshare.shape)
            hotspot = {'joint': self.joint_names[j], 'region': REGIONS[self.joint_region[j]],
                       'bad_pct': round(100 * float(jshare[k, j]), 1), 'time': round(float(samples[k]), 3)}
        total = self.rest_area[self.valid].sum()
        # Motion.
        w = self.vertex_area / self.vertex_area.sum()
        disp = np.linalg.norm(frames - frames[0], axis=2).max(axis=0) / h
        amp = {q: round(float(weighted_quantile(disp, w, q)), 4) for q in (0.5, 0.9)}
        region_amp = {}
        for r, region in enumerate(REGIONS):
            sel = self.vertex_region == r
            if w[sel].sum() > 0.002:
                region_amp[region] = round(float(disp[sel].max()), 3)
        dt = (samples[-1] - samples[0]) / (n - 1) if n > 1 else 1.0
        speed = np.linalg.norm(np.diff(frames, axis=0), axis=2) / h / dt if n > 1 else np.zeros((1, len(w)))
        peak_speed = max(float(weighted_quantile(row, w, 0.95)) for row in speed)
        accel = np.linalg.norm(frames[2:] - 2 * frames[1:-1] + frames[:-2], axis=2) / h / dt ** 2 if n > 2 \
            else np.zeros((1, len(w)))
        result = {
            'length_s': round(float(samples[-1] - samples[0]), 3),
            'frames': n,
            'deform': deform,
            'deform_total_pct': round(100 * float(region_bad.sum(axis=1).max() / total), 2),
            'fold_pct': round(100 * float(fold_area.max() / total), 2),
            'stretch_p999': round(float(np.quantile(worst_s1[self.valid], 0.999)), 2),
            'squash_p001': round(float(np.quantile(worst_s2[self.valid], 0.001)), 2),
            'hotspot': hotspot,
            'amp_p50': amp[0.5], 'amp_p90': amp[0.9], 'amp_max': round(float(disp.max()), 3),
            'body_share': round(float(w[disp > 0.05].sum()), 3),
            'region_amp': region_amp,
            'torso_turn_deg': round(torso_turn, 1),
            'peak_speed': round(peak_speed, 2),
            'hand_inside_pct': round(100 * float(hand_inside.max()), 1),
            'hand_inside_time': round(float(samples[int(np.argmax(hand_inside))]), 3),
            'hand_depth': round(float(hand_depth.max()), 3),
            'accel_p99': round(float(np.quantile(accel, 0.99)), 1),
        }
        if LOOPING.match(name):
            result['loop_pop'] = round(float(np.linalg.norm(frames[-1] - frames[0], axis=1).max() / h), 4)
        return result, frames

    def mesh(self):
        doc = self.glb.json
        lods = {}
        lod_points = {}
        for mesh in doc['meshes']:
            name = mesh.get('name') or ''
            found = re.search(r'LOD(\d)', name, re.I)
            level = int(found.group(1)) if found else 0
            key = f"{'shadow' if 'shadow' in name.lower() else 'lod'}{level}"
            count = 0
            for primitive in mesh['primitives']:
                if primitive.get('mode', 4) != 4:
                    continue
                if 'indices' in primitive:
                    count += doc['accessors'][primitive['indices']]['count'] // 3
                else:
                    count += doc['accessors'][primitive['attributes']['POSITION']]['count'] // 3
                if key.startswith('lod') and level > 0:
                    lod_points.setdefault(level, []).append(
                        self.glb.accessor(primitive['attributes']['POSITION']).astype(np.float64))
            lods[key] = lods.get(key, 0) + count
        tree = cKDTree(self.rest)
        deviation = {}
        for level, chunks in sorted(lod_points.items()):
            d, _ = tree.query(np.concatenate(chunks))
            deviation[f'lod{level}'] = round(float(np.quantile(d, 0.95) / self.height), 4)
        # LOD0 topology on welded positions.
        key = np.round(self.rest / max(self.height, 1e-9) * 1e5).astype(np.int64)
        _, weld = np.unique(key, axis=0, return_inverse=True)
        weld = weld.ravel()
        t = weld[self.tris]
        edges = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
        edges = edges[edges[:, 0] != edges[:, 1]]
        _, counts = np.unique(edges, axis=0, return_counts=True)
        a, b, c = (self.rest[self.tris[:, k]] for k in range(3))
        angles = []
        for p, q, r in ((a, b, c), (b, c, a), (c, a, b)):
            u, v = q - p, r - p
            cos = np.einsum('ij,ij->i', u, v) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-20)
            angles.append(np.degrees(np.arccos(np.clip(cos, -1, 1))))
        min_angle = np.min(angles, axis=0)
        parent = np.arange(weld.max() + 1)

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for x, y in edges:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry
        used = np.unique(t)
        components = len({find(i) for i in used})
        return {
            'triangles': lods,
            'lod_deviation_p95': deviation,
            'sliver_pct': round(100 * float((min_angle < 3).mean()), 2),
            'boundary_edges': int((counts == 1).sum()),
            'nonmanifold_edges': int((counts > 2).sum()),
            'components': components,
            'joints': len(self.model.joints),
            'hand_joints': int(sum(1 for r in self.joint_region if REGIONS[r] == 'hand')) if self.model.joints else 0,
            'height': round(self.height, 4),
        }


def weighted_quantile(values, weights, q):
    order = np.argsort(values)
    cumulative = np.cumsum(weights[order])
    return values[order][min(int(np.searchsorted(cumulative, q * cumulative[-1])), len(values) - 1)]


def trajectories(frames, picks):
    index = np.linspace(0, len(frames) - 1, 16).round().astype(int)
    sel = frames[index][:, picks]
    return sel - sel[0]


def audit(path, fps):
    a = Audit(path)
    out = {'glb': str(path), 'mesh': a.mesh(), 'clips': {}}
    rng = np.random.default_rng(0)
    picks = rng.choice(len(a.rest), size=min(600, len(a.rest)), replace=False)
    tracks = {}
    for name in a.model.clips:
        try:
            result, frames = a.clip(name, fps)
        except Exception as error:  # noqa: BLE001 - report and continue with the other clips
            out['clips'][name] = {'error': str(error)}
            continue
        out['clips'][name] = result
        if result['length_s'] > 0:
            tracks[name] = trajectories(frames, picks)
    names = sorted(tracks)
    duplicates = []
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            rms = float(np.sqrt(np.mean(np.sum((tracks[x] - tracks[y]) ** 2, axis=2))) / a.height)
            motion = max(float(np.abs(tracks[x]).max()), float(np.abs(tracks[y]).max())) / a.height
            if rms < 0.02 and motion > 0.02:
                duplicates.append([x, y, round(rms, 4)])
    out['near_duplicates'] = duplicates
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('glbs', nargs='+')
    parser.add_argument('--out', required=True)
    parser.add_argument('--fps', type=float, default=30)
    args = parser.parse_args()
    Path(args.out).mkdir(parents=True, exist_ok=True)
    for path in args.glbs:
        result = audit(path, args.fps)
        (Path(args.out) / (Path(path).stem + '.json')).write_text(json.dumps(result, indent=1))
        print(path)


if __name__ == '__main__':
    main()
