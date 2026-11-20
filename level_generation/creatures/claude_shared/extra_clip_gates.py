#!/usr/bin/env python3
"""Numbers and frame strips for added script clips on any MM9 body (dropped-clip pass, run2-clips-groupC,
2026-10-31). Works on non-humanoid skeletons (no limb names needed). Per clip at FPS on the LOD0 mesh:

- floor: lowest visible point per frame, cm: min, max, first, last frame;
- jitter: skinned vertices' second difference per frame (mm/frame^2), p99 over vertices, worst frame;
- bones: every joint's posed parent offset length against its rest length, worst ratio (over 10 % = stretching;
  root joints and their children are skipped: their offset is the body's motion);
- body in body: triangle pairs that intersect between parts more than two joints apart in the skeleton (a limb,
  tail, wing or jaw through the body), per frame: worst count and the joint pair seen most;
- strip: N frames per clip, side and 3/4 views, flat shaded, floor line (painter's order, untextured).

The same numbers on the body's accepted clips (--ref-clips) give the baseline: MM9 bodies intersect a little at
rest (teeth, eyelids), so read a new clip's count against the accepted clips', not against zero.

    extra_clip_gates.py <glb> --clips A,B --ref-clips Standing,Walking [--out dir] [--fps 30] [--frames 8]
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent / 'floor'))
import glb_pose  # noqa: E402


def frames(model, clip, fps):
    times = model.clip_times(clip)
    n = max(2, int(round((times[-1] - times[0]) * fps)) + 1)
    return np.linspace(times[0], times[-1], n)


class Body:
    def __init__(self, glb_path):
        self.model = glb_pose.Model(glb_pose.Glb(glb_path))
        m = self.model
        nodes = m.glb.json['nodes']
        tris, joint_of_tri, offset = [], [], 0
        for p in m.primitives:
            tris.append(p['triangles'] + offset)
            if p['skinned']:
                w = np.zeros((len(p['positions']), len(m.joints)))
                np.add.at(w, (np.repeat(np.arange(len(w)), 4), p['joints'].reshape(-1)), p['weights'].reshape(-1))
                tri_w = w[p['triangles']].sum(axis=1)
                joint_of_tri.append(np.array(m.joints)[tri_w.argmax(axis=1)])
            else:
                joint_of_tri.append(np.full(len(p['triangles']), p['node']))
            offset += len(p['positions'])
        self.tris = np.concatenate(tris)
        self.tri_joint = np.concatenate(joint_of_tri)
        # skeleton graph distance between joints (nodes), capped at 3
        n = len(nodes)
        adj = [set() for _ in range(n)]
        for i, par in enumerate(m.parent):
            if par >= 0:
                adj[i].add(par)
                adj[par].add(i)
        self.near = np.zeros((n, n), bool)
        for j in set(self.tri_joint.tolist()):
            seen, frontier = {j}, {j}
            for _ in range(2):
                frontier = {k for f in frontier for k in adj[f]} - seen
                seen |= frontier
            self.near[j, list(seen)] = True
        self.names = [nd.get('name', str(i)) for i, nd in enumerate(nodes)]
        # bone lengths: skip the root joints and their children (their offset is the body's own motion)
        roots = set(m.root_joints)
        self.joint_nodes = [j for j in m.joints if j not in roots and m.parent[j] not in roots]

    def posed(self, clip, t):
        m = self.model
        local = m.sample(clip, float(t)) if clip else {}
        world = m.world(local)
        posed = m.skinned_positions(world)
        visible = m.visible_vertices(posed)
        low = min(float(p[v, 1].min()) for (p, _), v in zip(posed, visible) if len(v))
        return np.concatenate([p for p, _ in posed]), low, local

    def intersections(self, V):
        T = self.tris
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        cen = (a + b + c) / 3
        rad = np.max(np.stack([np.linalg.norm(x - cen, axis=1) for x in (a, b, c)]), axis=0)
        area = np.linalg.norm(np.cross(b - a, c - a), axis=1)
        tree = cKDTree(cen)
        pairs = tree.query_pairs(2 * float(np.percentile(rad, 99)), output_type='ndarray')
        if not len(pairs):
            return 0, None
        i, j = pairs[:, 0], pairs[:, 1]
        ji, jj = self.tri_joint[i], self.tri_joint[j]
        far = ~self.near[ji, jj]
        shared = (T[i][:, :, None] == T[j][:, None, :]).any(axis=(1, 2))
        ok = far & ~shared & (area[i] > 1e-10) & (area[j] > 1e-10)
        ok &= np.linalg.norm(cen[i] - cen[j], axis=1) <= rad[i] + rad[j]
        i, j = i[ok], j[ok]
        if not len(i):
            return 0, None
        hit = seg_tri(V, T[i], T[j]) | seg_tri(V, T[j], T[i])
        if not hit.any():
            return 0, None
        pj = sorted(zip(self.tri_joint[i[hit]], self.tri_joint[j[hit]]))
        pj = [tuple(sorted((self.names[x], self.names[y]))) for x, y in pj]
        top = max(set(pj), key=pj.count)
        return int(hit.sum()), top


def seg_tri(V, edges_of, tris):
    """Any edge of triangles edges_of crosses triangle tris (pairwise rows)."""
    hit = np.zeros(len(tris), bool)
    p0, p1, p2 = V[tris[:, 0]], V[tris[:, 1]], V[tris[:, 2]]
    e1, e2 = p1 - p0, p2 - p0
    for k in range(3):
        o = V[edges_of[:, k]]
        d = V[edges_of[:, (k + 1) % 3]] - o
        h = np.cross(d, e2)
        det = (e1 * h).sum(1)
        good = np.abs(det) > 1e-14
        inv = np.where(good, 1.0 / np.where(good, det, 1.0), 0.0)
        s = o - p0
        u = (s * h).sum(1) * inv
        q = np.cross(s, e1)
        v = (d * q).sum(1) * inv
        t = (e2 * q).sum(1) * inv
        hit |= good & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < 1)
    return hit


def measure(body, clip, fps, step=2):
    m = body.model
    rest_len = {j: float(np.linalg.norm(m.rest[j][0])) for j in body.joint_nodes}
    lows, verts, worst_bone, inter = [], [], (1.0, ''), []
    for k, t in enumerate(frames(m, clip, fps)):
        V, low, local = body.posed(clip, t)
        lows.append(low)
        verts.append(V)
        for j in body.joint_nodes:
            if rest_len[j] < 0.01 * 0.0256 * 10 or j not in local:
                continue
            ratio = float(np.linalg.norm(local[j][0])) / rest_len[j]
            off = max(ratio, 1 / max(ratio, 1e-6))
            if off > worst_bone[0]:
                worst_bone = (off, body.names[j])
        if k % step == 0:
            inter.append(body.intersections(V))
    A = np.stack(verts)
    acc = np.linalg.norm(A[2:] - 2 * A[1:-1] + A[:-2], axis=2) * 1000 if len(A) > 2 else np.zeros((1, 1))
    p99 = np.percentile(acc, 99, axis=1)
    lows = np.array(lows) * 100
    worst_inter = max(inter, key=lambda x: x[0])
    return {'frames': len(A), 'floor_min_cm': round(float(lows.min()), 1), 'floor_max_cm': round(float(lows.max()), 1),
            'floor_first_last_cm': [round(float(lows[0]), 1), round(float(lows[-1]), 1)],
            'jitter_p99_mm_f2': round(float(p99.max()), 2), 'jitter_frame': int(p99.argmax()) + 1,
            'bone_worst_ratio': round(worst_bone[0], 3), 'bone_worst_joint': worst_bone[1],
            'body_in_body_max_pairs': worst_inter[0], 'body_in_body_parts': worst_inter[1]}


def duplicate_of(body, clip):
    """Another clip of the GLB with the same length and the same joint rotations (an MM9 clip that carries another
    clip's keys, e.g. the Eye's Flap = Fly): its name, or None."""
    m = body.model
    ta = m.clip_times(clip)
    for other in m.clips:
        if other == clip:
            continue
        tb = m.clip_times(other)
        if abs((ta[-1] - ta[0]) - (tb[-1] - tb[0])) > 0.04:
            continue
        same = True
        for f in np.linspace(0, 1, 6):
            la = m.sample(clip, ta[0] + f * (ta[-1] - ta[0]))
            lb = m.sample(other, tb[0] + f * (tb[-1] - tb[0]))
            for j in m.joints:
                qa, qb = la.get(j, m.rest[j])[1], lb.get(j, m.rest[j])[1]
                if 2 * np.degrees(np.arccos(min(1.0, abs(float(np.dot(qa, qb)))))) > 0.05:
                    same = False
                    break
            if not same:
                break
        if same:
            return other
    return None


def view_matrix(yaw, pitch):
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return rx @ ry


def render(P, T, x0, y0, scale, size, floor_y=None, light=np.array([0.4, 0.7, 0.6])):
    """P: camera-space points (x right, y up, z depth toward the viewer)."""
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    n = np.cross(b - a, c - a)
    nl = np.linalg.norm(n, axis=1)
    keep = nl > 1e-12
    n = n[keep] / nl[keep, None]
    depth = ((a + b + c) / 3)[keep, 2]
    shade = np.clip(np.abs(n @ (light / np.linalg.norm(light))), 0, 1) * 0.75 + 0.2
    tri = np.stack([a, b, c], axis=1)[keep]
    img = Image.new('RGB', (size, size), (236, 236, 232))
    draw = ImageDraw.Draw(img)
    if floor_y is not None:
        fy = size - 8 - (floor_y - y0) * scale
        draw.line([(0, fy), (size, fy)], fill=(170, 90, 60), width=2)
    for idx in np.argsort(depth):
        pts = [(size / 2 + (x - x0) * scale, size - 8 - (y - y0) * scale) for x, y, _ in tri[idx]]
        g = int(255 * shade[idx])
        draw.polygon(pts, fill=(g, int(g * 0.95), int(g * 0.88)))
    return img


def strip(body, clips, fps, nframes, out_path, cell=180):
    """Side view (looking along x, floor drawn) and a 3/4 view from above; each clip
    framed on its own sampled frames."""
    m = body.model
    yaw = np.pi / 2   # MM9 bodies face along glTF z (actors.yml yaw_offset -90 deg): look along x for the side
    views = [(view_matrix(yaw, 0.0), True), (view_matrix(yaw + np.pi / 4, 0.4), False)]
    rows = []
    for clip in clips:
        ts = frames(m, clip, fps)
        pick = ts[np.linspace(0, len(ts) - 1, nframes).round().astype(int)]
        posed = [body.posed(clip, t)[0] for t in pick]
        for vi, (R, side) in enumerate(views):
            Ps = [V @ R.T for V in posed]
            allp = np.concatenate(Ps)
            lo, hi = allp.min(0), allp.max(0)
            if side:
                lo[1] = min(lo[1], 0.0)
            span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
            scale = (cell - 16) / max(span, 1e-6)
            x0 = (lo[0] + hi[0]) / 2
            row = Image.new('RGB', (cell * nframes + 110, cell), (255, 255, 255))
            ImageDraw.Draw(row).text((4, cell // 2), f'{clip}\n{"side" if side else "3/4 above"}', fill=(0, 0, 0))
            for k, (t, P) in enumerate(zip(pick, Ps)):
                img = render(P, body.tris, x0, lo[1], scale, cell, 0.0 if side else None)
                ImageDraw.Draw(img).text((3, 3), f'{t - ts[0]:.2f}s', fill=(60, 60, 60))
                row.paste(img, (110 + k * cell, 0))
            rows.append(row)
    sheet = Image.new('RGB', (rows[0].width, cell * len(rows)), (255, 255, 255))
    for r, row in enumerate(rows):
        sheet.paste(row, (0, r * cell))
    sheet.save(out_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--clips', required=True)
    parser.add_argument('--ref-clips', default='')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--fps', type=float, default=30.0)
    parser.add_argument('--frames', type=int, default=7)
    parser.add_argument('--no-strip', action='store_true')
    parser.add_argument('--strip-only', action='store_true')
    parser.add_argument('--dupes-only', action='store_true')
    args = parser.parse_args()
    body = Body(args.glb)
    if args.dupes_only:
        print({c: duplicate_of(body, c) for c in args.clips.split(',')})
        return
    out = {'new': {}, 'ref': {}}
    for group, names in (() if args.strip_only else (('ref', args.ref_clips), ('new', args.clips))):
        for clip in [c for c in names.split(',') if c]:
            r = measure(body, clip, args.fps)
            if group == 'new':
                r['duplicate_of'] = duplicate_of(body, clip)
            out[group][clip] = r
            print(group, clip, json.dumps(r), flush=True)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        if not args.strip_only:
            json.dump(out, open(args.out / 'extra_gates.json', 'w'), indent=1)
        if not args.no_strip:
            clips = args.clips.split(',')
            for k in range(0, len(clips), 5):
                strip(body, clips[k:k + 5], args.fps, args.frames, args.out / f'strip_new_{k // 5}.png')


if __name__ == '__main__':
    main()
