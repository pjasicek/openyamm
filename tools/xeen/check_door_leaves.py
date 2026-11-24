#!/usr/bin/env python3
"""Hinged door leaves of the Xeen BLVs, as the game draws them (F44, the player's pins 2026-11-24).

  leaf.back_unmirrored  error  a hinged leaf shows the same picture on both sides, laid so that the picture's hinge
                               edge is at the hinge on one side and at the free edge on the other: XD-24's oak doors
                               (cndl) show their skull knocker beside the hinge from one room. Seen from behind, a
                               real door is its front mirrored; the studio lays the back face unmirrored (REQUEST to
                               the studio: mirror the back face of a leaf whose back shows its front picture).
  leaf.swing_room       error  a leaf that opens away from whoever opens it swings through its doorway into the
                               other room, but its faces are listed only in the room it closes from, so the game
                               draws it only while that room is seen: XD-05's gate leaves vanish when the yard is
                               seen through the firing step's window. A leaf whose swing crosses its doorway is
                               listed in both rooms (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md, "Rooms").

Usage: tools/xeen/check_door_leaves.py [--assets ROOT] [--maps xeen_xd24,...] [--json FILE]   exit 1 on an error.
Reads `oymap export` of each BLV (cached under output/xeen_fb/door_leaves_cache) and its scene.yml door movers.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

import yaml

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OY = f'{R}/openyamm-studio/build-xeen/oymap'
CACHE = f'{R}/output/xeen_fb/door_leaves_cache'


def export(root, stem):
    blv = f'{root}/worlds/xeen/maps/{stem}.blv'
    os.makedirs(CACHE, exist_ok=True)
    out = f'{CACHE}/{stem}.json'
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(blv):
        subprocess.run([OY, 'export', blv, '--world', 'xeen', '--assets', root, '--out', out], check=True,
                       capture_output=True)
    return json.load(open(out))


def big_sides(m, face_ids):
    """The leaf's two upright faces wider than 64: (face, viewer's right vector, centre)."""
    V = m['vertices']
    sides = []
    for fi in face_ids:
        f = m['faces'][fi]
        n = [c / 65536 for c in f['plane_normal']]
        if abs(n[2]) > 0.1:
            continue
        P = [V[v] for v in f['vertices']]
        right = (-n[1], n[0])
        along = [p[0] * right[0] + p[1] * right[1] for p in P]
        if max(along) - min(along) < 64:
            continue
        sides.append((fi, f, P, right, along))
    return sides


def check_map(root, stem):
    d = export(root, stem)
    m = d['map']
    V = m['vertices']
    scene = yaml.safe_load(open(f'{root}/worlds/xeen/maps/{stem}.scene.yml'))
    movers = {}
    for entry in scene['initial_state'].get('doors') or []:
        rotation = (entry.get('mover') or {}).get('rotation')
        if rotation and [round(a) for a in rotation.get('axis', [])] == [0, 0, 1]:
            movers[entry['door_index']] = rotation
    portals = [(i, f) for i, f in enumerate(m['faces']) if f['is_portal']]
    findings = []
    for index, door in enumerate(d['doors']):
        rotation = movers.get(index)
        if rotation is None:
            continue
        pivot = rotation['pivot']
        sides = big_sides(m, door['faces'])
        where = f"door {door['id']} (pivot {[round(c) for c in pivot[:2]]})"
        # The picture's edge at the hinge, seen from each side.
        if len(sides) == 2 and sides[0][1]['texture'] == sides[1][1]['texture']:
            edges = []
            for fi, f, P, right, along in sides:
                lo = min(range(len(P)), key=lambda k: along[k])
                hi = max(range(len(P)), key=lambda k: along[k])
                du = f['texture_us'][hi] - f['texture_us'][lo]
                cx = sum(p[0] for p in P) / len(P)
                cy = sum(p[1] for p in P) / len(P)
                hinge_right = (pivot[0] - cx) * right[0] + (pivot[1] - cy) * right[1] > 0
                edges.append('right' if (du > 0) == hinge_right else 'left')
            if edges[0] != edges[1]:
                findings.append(('leaf.back_unmirrored', where, f"{sides[0][1]['texture']} shows its {edges[0]} edge "
                                 f"at the hinge from one side and its {edges[1]} edge from the other"))
        # A leaf that opens away swings through its doorway: listed in both rooms?
        if not rotation.get('open_away') or not sides:
            continue
        rooms = {m['faces'][fi]['room'] for fi in door['faces']}
        lo = [min(V[v][k] for fi in door['faces'] for v in m['faces'][fi]['vertices']) for k in range(3)]
        hi = [max(V[v][k] for fi in door['faces'] for v in m['faces'][fi]['vertices']) for k in range(3)]
        others = set()
        for pi, p in portals:
            P = [V[v] for v in p['vertices']]
            plo = [min(q[k] for q in P) for k in range(3)]
            phi = [max(q[k] for q in P) for k in range(3)]
            if all(plo[k] <= hi[k] + 48 and phi[k] >= lo[k] - 48 for k in range(3)):
                others |= {p['room'], p['room_behind']} - rooms
        for other in sorted(others):
            listed = set(m['sectors'][other]['faces']) if other < len(m['sectors']) else set()
            missing = [fi for fi in door['faces'] if fi not in listed]
            if missing:
                findings.append(('leaf.swing_room', where, f"swings into room {other} through its doorway but "
                                 f"{len(missing)} of its {len(door['faces'])} faces are listed only in room "
                                 f"{sorted(rooms)}"))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets', default=f'{R}/assets_dev')
    ap.add_argument('--maps')
    ap.add_argument('--json')
    a = ap.parse_args()
    stems = a.maps.split(',') if a.maps else sorted(
        os.path.basename(p)[:-4] for p in glob.glob(f'{a.assets}/worlds/xeen/maps/xeen_*.blv'))
    report = {}
    counts = {}
    for stem in stems:
        findings = check_map(a.assets, stem)
        report[stem] = findings
        for rule, where, what in findings:
            counts[rule] = counts.get(rule, 0) + 1
            print(f'{stem}: {rule}: {where}: {what}')
    print('totals:', ', '.join(f'{k} {v}' for k, v in sorted(counts.items())) or 'clean', f'({len(stems)} maps)')
    if a.json:
        json.dump(report, open(a.json, 'w'), indent=1)
    sys.exit(1 if counts else 0)


if __name__ == '__main__':
    main()
