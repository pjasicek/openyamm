#!/usr/bin/env python3
"""Write one engine screenshot tour per studied map from a list of (shot name, sector | face) picks.

Room shot: camera on a grid point inside the sector's floor with wall clearance, about 40 % of the sector's long
extent from the floor centroid, preferring the long axis, looking at the centroid. Face shot (mechanisms): camera
in front of the face along its normal, looking at it. Positions are feet positions; yaw 0 = +x, counter-clockwise.
"""
import math
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file  # noqa: E402

EYE = 160.0

# name -> (world, map, [(shot, 'sector', id) | (shot, 'face', id) | (shot, 'pos', [x, y, z, yaw, pitch])])
PICKS = yaml.safe_load((STUDY / 'tour_picks.yml').read_text())


def newell(P):
    n = np.zeros(3)
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
    return n


def inside(x, y, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and \
                x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1] + 1e-9) + poly[i][0]:
            c = not c
        j = i
    return c


def crosses(p, q, a, b):
    def orient(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    return orient(p, q, a) * orient(p, q, b) < 0 and orient(a, b, p) * orient(a, b, q) < 0


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
    return float(np.linalg.norm(p - (a + t * ab)))


class Map:
    def __init__(self, world, name):
        p = parse_blv_file(ROOT / 'assets_dev/worlds' / world / 'maps' / name)['payload']
        self.V = np.array([[v['x'], v['y'], v['z']] for v in p['vertices']], float)
        self.faces = p['faces']

    def sector_faces(self, sid):
        floors, walls = [], []
        for f in self.faces:
            if f['room_number'] != sid and f['room_behind_number'] != sid:
                continue
            P = self.V[f['vertex_indices']]
            n = newell(P)
            a = np.linalg.norm(n)
            if a == 0:
                continue
            if n[2] / a > 0.7 and f['room_number'] == sid and not f['is_portal']:
                floors.append((P, a / 2))
            elif abs(n[2] / a) < 0.3 and not f['is_portal']:
                walls.append(P)
        return floors, walls

    def room_shot(self, sid, pitch, min_clear=96):
        floors, walls = self.sector_faces(sid)
        allxy = np.vstack([P[:, :2] for P, _ in floors])
        weights = np.concatenate([[a / len(P)] * len(P) for P, a in floors])
        centroid = (allxy * weights[:, None]).sum(axis=0) / weights.sum()
        main_z = max(floors, key=lambda q: q[1])[0][:, 2].mean()
        lo, hi = allxy.min(axis=0), allxy.max(axis=0)
        long_axis = np.array([1.0, 0.0]) if hi[0] - lo[0] >= hi[1] - lo[1] else np.array([0.0, 1.0])
        extent = float(max(hi - lo))
        segs = []
        for P in walls:
            zlo, zhi = P[:, 2].min(), P[:, 2].max()
            for i in range(len(P)):
                segs.append((P[i, :2], P[(i + 1) % len(P), :2], zlo, zhi))
        best = None
        step = max(48.0, extent / 60)
        for x in np.arange(lo[0] + 32, hi[0] - 32, step):
            for y in np.arange(lo[1] + 32, hi[1] - 32, step):
                fz = None
                for P, _ in floors:
                    if inside(x, y, P[:, :2]):
                        z = P[:, 2].mean()
                        fz = z if fz is None else max(fz, z)
                if fz is None or abs(fz - main_z) > 200:
                    continue
                pt = np.array([x, y])
                clear = min([seg_dist(pt, a, b) for a, b, zlo, zhi in segs if zhi > fz + 40 and zlo < fz + 200]
                            or [1e9])
                if clear < min_clear:
                    continue
                eye = fz + EYE
                if any(zlo < eye < zhi and crosses(pt, centroid, a, b) for a, b, zlo, zhi in segs):
                    continue
                d = pt - centroid
                dist = np.linalg.norm(d)
                along = abs(np.dot(d, long_axis)) / max(dist, 1)
                score = -abs(dist - 0.4 * extent) + 0.25 * extent * along + min(clear, 256)
                if best is None or score > best[0]:
                    best = (score, x, y, fz)
        if best is None:
            if min_clear > 40:
                return self.room_shot(sid, pitch, min_clear / 2)
            raise ValueError(f'no camera spot in sector {sid}')
        _, x, y, fz = best
        yaw = math.atan2(centroid[1] - y, centroid[0] - x) % (2 * math.pi)
        return [round(x), round(y), round(fz + 1)], round(yaw, 3), pitch

    def all_walls(self):
        if not hasattr(self, '_walls'):
            rows = []
            for f in self.faces:
                if f['is_portal']:
                    continue
                P = self.V[f['vertex_indices']]
                n = newell(P)
                a = np.linalg.norm(n)
                if a and abs(n[2] / a) < 0.5:
                    for i in range(len(P)):
                        rows.append([*P[i, :2], *P[(i + 1) % len(P), :2], P[:, 2].min(), P[:, 2].max()])
            self._walls = np.array(rows)
        return self._walls

    def rays(self, pt, eye, count=32):
        W = self.all_walls()
        W = W[(W[:, 4] < eye) & (W[:, 5] > eye)]
        a, b = W[:, 0:2], W[:, 2:4]
        e = b - a
        out = []
        for k in range(count):
            ang = 2 * math.pi * k / count
            d = np.array([math.cos(ang), math.sin(ang)])
            den = d[0] * e[:, 1] - d[1] * e[:, 0]
            w = a - pt
            with np.errstate(divide='ignore', invalid='ignore'):
                t = (w[:, 0] * e[:, 1] - w[:, 1] * e[:, 0]) / den
                u = (w[:, 0] * d[1] - w[:, 1] * d[0]) / den
            hit = (np.abs(den) > 1e-9) & (t > 1) & (u >= 0) & (u <= 1)
            out.append(float(t[hit].min()) if hit.any() else 20000.0)
        return np.array(out)

    def open_shot(self, sid, pitch):
        floors, _ = self.sector_faces(sid)
        allxy = np.vstack([P[:, :2] for P, _ in floors])
        main_z = max(floors, key=lambda q: q[1])[0][:, 2].mean()
        lo, hi = allxy.min(axis=0), allxy.max(axis=0)
        step = max(64.0, float(max(hi - lo)) / 25)
        best = None
        for x in np.arange(lo[0] + 32, hi[0] - 32, step):
            for y in np.arange(lo[1] + 32, hi[1] - 32, step):
                fz = None
                for P, _ in floors:
                    if inside(x, y, P[:, :2]):
                        z = P[:, 2].mean()
                        fz = z if fz is None else max(fz, z)
                if fz is None or abs(fz - main_z) > 200:
                    continue
                r = self.rays(np.array([x, y]), fz + EYE)
                if r.min() < 96:
                    continue
                window = np.array([r[np.arange(k - 3, k + 4) % len(r)].min() for k in range(len(r))])
                k = int(window.argmax())
                # Stand near a wall (short ray behind) and look across the longest clear view.
                score = window[k] - 0.5 * r[(k + len(r) // 2) % len(r)]
                if best is None or score > best[0]:
                    best = (score, x, y, fz, 2 * math.pi * k / len(r))
        if best is None:
            raise ValueError(f'no open spot in sector {sid}')
        _, x, y, fz, yaw = best
        return [round(x), round(y), round(fz + 1)], round(yaw, 3), pitch

    def mech_shot(self, event, dist):
        group = [f for f in self.faces if (f['face_param'] or {}).get('cog_triggered') == event
                 and f['attributes'] & 0x02000000]
        P = np.vstack([self.V[f['vertex_indices']] for f in group])
        c = P.mean(axis=0)
        sid = group[0]['room_number']
        floors, walls = self.sector_faces(sid)
        segs = [(W[i, :2], W[(i + 1) % len(W), :2], W[:, 2].min(), W[:, 2].max()) for W in walls
                for i in range(len(W))]
        best = None
        for k in range(16):
            ang = k * math.pi / 8
            for d in (dist, dist * 0.7, dist * 0.5):
                pt = c[:2] + d * np.array([math.cos(ang), math.sin(ang)])
                fz = None
                for Q, _ in floors:
                    if inside(pt[0], pt[1], Q[:, :2]):
                        z = Q[:, 2].mean()
                        if c[2] - 400 < z < c[2] + 16 and (fz is None or z > fz):
                            fz = z
                if fz is None:
                    continue
                eye = fz + EYE
                if any(zlo < eye < zhi and crosses(pt, c[:2] + (pt - c[:2]) * 0.15, a, b) for a, b, zlo, zhi in segs):
                    continue
                if any(zlo < eye < zhi and crosses(pt, c[:2], a, b) for a, b, zlo, zhi in segs
                       if seg_dist(c[:2], a, b) > 48):
                    continue
                clear = min([seg_dist(pt, a, b) for a, b, zlo, zhi in segs if zlo < eye < zhi] or [1e9])
                score = d + min(clear, 200) - abs(c[2] - eye)
                if clear > 64 and (best is None or score > best[0]):
                    best = (score, pt, fz)
                break
        if best is None:
            raise ValueError(f'no camera spot for event {event}')
        _, pt, fz = best
        yaw = math.atan2(c[1] - pt[1], c[0] - pt[0]) % (2 * math.pi)
        pitch = math.atan2(c[2] - (fz + EYE), float(np.linalg.norm(c[:2] - pt)))
        return [round(pt[0]), round(pt[1]), round(fz + 1)], round(yaw, 3), round(pitch, 3)

    def face_shot(self, fid, dist):
        f = self.faces[fid]
        P = self.V[f['vertex_indices']]
        n = newell(P)
        n = n / np.linalg.norm(n)
        c = P.mean(axis=0)
        horiz = np.array([n[0], n[1]])
        if np.linalg.norm(horiz) < 0.2:
            horiz = np.array([1.0, 0.0])
        horiz = horiz / np.linalg.norm(horiz)
        cam = c[:2] + horiz * dist
        floor = None
        for g in self.faces:
            if g['room_number'] != f['room_number'] or g['is_portal']:
                continue
            Q = self.V[g['vertex_indices']]
            m = newell(Q)
            if np.linalg.norm(m) and m[2] / np.linalg.norm(m) > 0.7 and inside(cam[0], cam[1], Q[:, :2]):
                z = Q[:, 2].mean()
                if z < c[2] + 32 and (floor is None or z > floor):
                    floor = z
        floor = c[2] - 150 if floor is None else floor
        yaw = math.atan2(-horiz[1], -horiz[0]) % (2 * math.pi)
        pitch = math.atan2(c[2] - (floor + EYE), dist)
        return [round(cam[0]), round(cam[1]), round(floor + 1)], round(yaw, 3), round(pitch, 3)


def shot_pose(m, kind, ref, extra):
    if kind == 'sector':
        return m.room_shot(ref, extra if extra is not None else -0.12)
    if kind == 'open':
        return m.open_shot(ref, extra if extra is not None else -0.12)
    if kind == 'mech':
        return m.mech_shot(ref, extra or 300)
    if kind == 'face':
        return m.face_shot(ref, extra or 320)
    return ref[:3], ref[3], ref[4]


def main():
    only = set(sys.argv[1:])
    for name, spec in PICKS.items():
        if only and name not in only:
            continue
        m = Map(spec['world'], spec['map'])
        shots = []
        for shot in spec['shots']:
            label, kind, ref = shot[:3]
            extra = shot[3] if len(shot) > 3 else None
            try:
                pos, yaw, pitch = shot_pose(m, kind, ref, extra)
            except ValueError as exc:
                print('skip', name, label, exc)
                continue
            shots.append(dict(name=label, position=pos, yaw=yaw, pitch=pitch))
            print(name, label, pos, yaw, pitch)
        out = STUDY / 'shots' / name
        tour = dict(output_dir=str(out), settle_seconds=2.0, exit=True, shots=shots)
        (STUDY / 'tours' / (name + '.yml')).write_text(yaml.safe_dump(tour, sort_keys=False))


if __name__ == '__main__':
    main()
