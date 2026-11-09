#!/usr/bin/env python3
"""How much detached_parts_audit.py misses: damage good models in memory and count what it catches (read-only).

For every part rooted at bind, mutants of the bind pose (children stay where they are):
  pull  the part moved off its holder until nothing of it is within 1.5 % of the model's size of the holder;
  tilt  the part turned about one end of its contact until at least a third of its root is off the holder by over
        twice the threshold, with the other end still touching (one touching corner).
A mutant that opens no such gap (a root too deep, a part that slides along its holder) is skipped and counted as
invalid. The audit judges each one as damage present at bind (no bind root known) and as a clip pose (with the root
from the undamaged bind). A part another neighbour still holds stays attached, so those are counted apart.

    detached_parts_mutation.py <glb...> [--json out.json] [--jobs 8]
"""
import argparse
import json
import multiprocessing
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import detached_parts_audit as audit  # noqa: E402

THRESHOLD = 0.004


def rotate(points, pivot, axis, angle):
    axis = axis / max(np.linalg.norm(axis), 1e-12)
    d = points - pivot
    c, s = np.cos(angle), np.sin(angle)
    return pivot + d * c + np.cross(axis, d) * s + axis[None, :] * (d @ axis)[:, None] * (1 - c)


def mutate(cr, P, k, holder, root, kind):
    """The pose with part k damaged, or None when the mutant opens no real gap."""
    geo = audit.PoseGeometry(cr, P)
    verts = cr.comp_verts[k]
    X = P[verts]
    near = P[cr.weld_rep[cr.comp_wv[k]]][root]
    out = X.mean(0) - near.mean(0)
    if np.linalg.norm(out) < 1e-6:
        return None
    out /= np.linalg.norm(out)
    M = P.copy()
    if kind == 'pull':
        clear = 0.015 * cr.size
        step = clear
        for _ in range(8):
            if float(geo.signed(X + out * step, holder)[0].min()) >= clear:
                M[verts] = X + out * step
                return M
            step *= 1.6
        return None
    c = near - near.mean(0)
    across = np.linalg.svd(c, full_matrices=False)[2][0]
    t = c @ across
    width = float(np.ptp(t))
    if width < 2 * THRESHOLD:
        return None
    pivot = near[int(np.argmin(t))]
    axis = np.cross(out, across)
    for angle in np.radians((5, 10, 15, 20, 25, 30)):
        for sign in (1.0, -1.0):
            sd = geo.signed(rotate(near, pivot, axis, sign * angle), holder)[0]
            if (sd > 2 * THRESHOLD).mean() >= 1 / 3 and sd.min() <= THRESHOLD:
                M[verts] = rotate(X, pivot, axis, sign * angle)
                return M
    return None


def check(path):
    cr = audit.Creature(path)
    P = cr.rest
    audit.measure_pose_root(cr, P, THRESHOLD)
    roots = cr.last_roots
    rows = []
    for k, (holder, root) in roots.items():
        plate = audit.plate_axes(P[cr.weld_rep[cr.comp_wv[k]]], cr.comp_area[k]) is not None
        for kind in ('pull', 'tilt'):
            M = mutate(cr, P, k, holder, root, kind)
            row = {'part': int(k), 'joint': cr.comp_joint[k], 'tris': len(cr.comp_tris[k]), 'plate': plate,
                   'kind': kind, 'valid': M is not None, 'holder': int(holder)}
            if M is not None:
                for mode, r in (('bind', None), ('clip', roots)):
                    res = audit.measure_pose_root(cr, M, THRESHOLD, roots=r)
                    row[mode] = bool(not res[1][k])
                    row[mode + '_holder'] = int(res[2][k][1]) if k in res[2] else -1
            rows.append(row)
    return Path(path).stem, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('glbs', nargs='+')
    ap.add_argument('--json', default=None)
    ap.add_argument('--jobs', type=int, default=8)
    args = ap.parse_args()
    with multiprocessing.Pool(args.jobs) as pool:
        all_rows = dict(pool.map(check, args.glbs))
    total = [r for rows in all_rows.values() for r in rows]
    print('invalid (no real gap opened):', sum(not r['valid'] for r in total), 'of', len(total))
    for kind in ('pull', 'tilt'):
        for plate in (True, False):
            sel = [r for r in total if r['kind'] == kind and r['plate'] == plate and r['valid']]
            for mode in ('bind', 'clip') if sel else ():
                caught = sum(r[mode] for r in sel)
                other = sum(not r[mode] and r[mode + '_holder'] != r['holder'] for r in sel)
                print(f"{kind} {'plate' if plate else 'other'} as {mode}: caught {caught}/{len(sel)}, "
                      f"held by another part {other}, still on the same holder {len(sel) - caught - other}")
    if args.json:
        Path(args.json).write_text(json.dumps(all_rows, indent=1))


if __name__ == '__main__':
    main()
