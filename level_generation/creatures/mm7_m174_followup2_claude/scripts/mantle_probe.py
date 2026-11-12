#!/usr/bin/env python3
"""Arm through the sun mantle (follow-up 2, 2026-11-12): per clip sample, does an arm's bone line (clavicle end ->
elbow -> wrist -> palm) cross a mantle triangle? In Standing both arms run under the mantle and leave it below its
edge, crossing nothing; an arm that pierces the mantle's surface (the 2026-11-11 Attack: upper arm inside the cape,
forearm out of the chest) crosses it.

    mantle_probe.py <glb> [clip,...] [--side R|L|both] [--png <mask check png>]

Mantle vertices: base colour yellow-orange (texture at the UV: R > 0.55, G > 0.35, B < 0.35, R - B > 0.4) and
dominated by a trunk bone (B_Spine*, B_*_Clavicle, B_*_UpperArm*), below the neck joint. Prints per clip the share of
samples (30 Hz) where the line crosses, the frames, and the arm length inside (cm) between the first and last crossing.
"""
import argparse
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
import glb_pose  # noqa: E402

TRUNK = ('B_Spine', 'B_L_Clavicle', 'B_R_Clavicle', 'B_L_UpperArm', 'B_R_UpperArm', 'B_Neck')
# --panels: only the mantle that does not ride on the arms (dominant bone spine, pelvis, clavicle or robe chain): the
# front and back panels an arm must not pass through; the side parts are skinned to the arm and lift with it
START = 0.35
PANEL = ('B_Spine', 'B_Pelvis', 'B_L_Clavicle', 'B_R_Clavicle', 'B_Neck', 'Robe_')


def base_image(g):
    mat = g.json['materials'][0]
    tex = g.json['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
    img = g.json['images'][tex['source']]
    view = g.json['bufferViews'][img['bufferView']]
    data = bytes(g.bin[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])
    return np.asarray(Image.open(io.BytesIO(data)).convert('RGB')).astype(np.float32) / 255.0


def seg_tri(p0, p1, A, B, C):
    """Möller-Trumbore: parameter t in [0,1] of segment p0->p1 hitting each triangle, nan where it misses."""
    d = p1 - p0
    e1, e2 = B - A, C - A
    h = np.cross(d, e2)
    a = np.einsum('ij,ij->i', e1, h)
    ok = np.abs(a) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, a, 1.0), 0.0)
    s = p0 - A
    u = f * np.einsum('ij,ij->i', s, h)
    q = np.cross(s, e1)
    v = f * (q @ d)
    t = f * np.einsum('ij,ij->i', e2, q)
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)
    return np.where(hit, t, np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('glb')
    ap.add_argument('clips', nargs='?', default='Standing,Attack')
    ap.add_argument('--side', default='R')
    ap.add_argument('--png')
    ap.add_argument('--fps', type=float, default=30.0)
    ap.add_argument('--panels', action='store_true')
    ap.add_argument('--covered', action='store_true', help='print per sample: mid upper arm and elbow covered from '
                    'front / three-quarter / side (1 = behind a mantle panel)')
    a = ap.parse_args()
    g = glb_pose.Glb(a.glb)
    m = glb_pose.Model(g)
    names = [n['name'] for n in g.json['nodes']]
    prim = m.primitives[0]
    mesh = g.json['meshes'][g.json['nodes'][prim['node']]['mesh']]['primitives'][0]
    uv = g.accessor(mesh['attributes']['TEXCOORD_0'])
    img = base_image(g)
    H, W = img.shape[:2]
    px = np.clip((uv[:, 0] % 1.0) * W, 0, W - 1).astype(int)
    py = np.clip((uv[:, 1] % 1.0) * H, 0, H - 1).astype(int)
    col = img[py, px]
    yellow = (col[:, 0] > 0.55) & (col[:, 1] > 0.35) & (col[:, 2] < 0.35) & (col[:, 0] - col[:, 2] > 0.4)
    dom = [names[m.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
    trunk = np.array([d.startswith(PANEL if a.panels else TRUNK) for d in dom])
    W0 = m.world(m.sample('Standing', 0.0))
    rest = m.skinned_positions(W0)[0][0]
    neck_y = W0[names.index('B_Neck')][1, 3]
    mantle = yellow & trunk & (rest[:, 1] < neck_y)
    tri = prim['triangles']
    mtri = tri[mantle[tri].all(axis=1)]
    print(f'mantle: {mantle.sum()} vertices, {len(mtri)} triangles (of {len(tri)})')
    if a.png:
        out = (img * 255).astype(np.uint8).copy()
        for x, y in zip(px[mantle], py[mantle]):
            out[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = (0, 0, 255)
        Image.fromarray(out).resize((1024, 1024)).save(a.png)
    sides = ['L', 'R'] if a.side == 'both' else [a.side]
    for clip in a.clips.split(','):
        T = m.clip_times(clip)[-1]
        n = max(2, int(round(T * a.fps)))
        for s in sides:
            chain = [f'B_{s}_UpperArm', f'B_{s}_Forearm', f'B_{s}_Hand', f'Socket_Palm_{s}']
            hits, worst, frames, cov = 0, 0.0, [], []
            for k in range(n + 1):
                t = min(T, k * T / n)
                Wk = m.world(m.sample(clip, t))
                P = m.skinned_positions(Wk)[0][0]
                A, B, C = P[mtri[:, 0]], P[mtri[:, 1]], P[mtri[:, 2]]
                pts = [Wk[names.index(b)][:3, 3] for b in chain]
                # start a third of the way down the upper arm: the shoulder joint itself sits in the mantle's yoke
                pts[0] = pts[0] + START * (pts[1] - pts[0])
                cross = []                 # arc length along the arm of each crossing
                acc = 0.0
                for p0, p1 in zip(pts[:-1], pts[1:]):
                    L = float(np.linalg.norm(p1 - p0))
                    tt = seg_tri(p0, p1, A, B, C)
                    cross += list(acc + tt[~np.isnan(tt)] * L)
                    acc += L
                if a.covered:
                    # the elbow and mid upper arm seen from the front, three-quarter and side (rays toward the
                    # viewer): covered by a panel?
                    el = Wk[names.index(chain[1])][:3, 3]
                    mid = (Wk[names.index(chain[0])][:3, 3] + el) / 2
                    sx = 1.0 if s == 'L' else -1.0
                    row = []
                    for pnt in (mid, el):
                        for d in (np.array([0, 0, 1.0]), np.array([0.7 * sx, 0, 0.7]), np.array([sx, 0, 0])):
                            tt = seg_tri(pnt, pnt + d, A, B, C)
                            row.append(int((~np.isnan(tt)).any()))
                    cov.append((round(t, 2), row))
                if cross:
                    hits += 1
                    frames.append(round(t, 2))
                    worst = max(worst, max(cross) - min(cross) if len(cross) > 1 else 0.0)
            if cov:
                print(f'{clip} {s} covered [mid F,3Q,S | elbow F,3Q,S]: ' + '  '.join(
                    f'{t}:{"".join(map(str, r[:3]))}|{"".join(map(str, r[3:]))}' for t, r in cov))
            print(f'{clip:9} {s}: arm crosses the mantle in {100 * hits / (n + 1):4.1f}% of samples, '
                  f'inside span {100 * worst:.1f} cm, at {frames[:12]}{" ..." if len(frames) > 12 else ""}')


if __name__ == '__main__':
    main()
