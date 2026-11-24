#!/usr/bin/env python3
"""F14 drop check on a built BLV (fast, geometric): floors the party can get down to from its start but not walk back
up from. Floors are the map's upward faces (door and lift faces left out); two floors touch where their outlines
share a stretch of edge seen from above, and the step between them is the height difference along it. The party walks
up a step of at most 50 (the game's MaximumRise) and down any drop; the scene's ladders join their foot and top.
A floor reached from the start but not left back to it is a trap unless something there moves the party: an exit, a
teleport, a ladder, a lift, a clicked panel that moves the party (checked by hand from the list printed beside it).
Usage: tools/xeen/check_drops.py <map.blv> [<scene.yml>] [--assets ROOT] [--json]   exit 1 on a pocket.
Blocks on a continuous floor (a stair's steps, a dais, the eggs' rock): an edge, sampled every 64, also joins the
floor it stands over (never through a ceiling: another room's floor beyond a wall); an edge under or within 68 of a
block standing on its face (a parapet round a well; not a shelf or bunk with room under it) is not walked off, and
the way back is followed on the joins as they are, one way or both (A7 s27, 2026-11-22).
F14 (the user 2026-11-21, Robbers' Den's race): a pocket needs a way back without spells (ladder, stair, lift, teleport
or an exit that leads on); a pocket left on purpose another way is recorded in the map's NOTES.md.
F43 (the player's pins 2026-11-24, XD-02's chasm): a mover never excuses a pocket. The chasm under XD-02's trestle was
kept "reached only by stepping off the moving car", and a player who fell off the car could not get out. A floor a
party can fall to from a car, a lift, a bridge or a ledge needs its own way out on foot; the lever or car that is
listed beside a pocket ("things there") is never that way unless it carries the party up from where it stands."""
import argparse, collections, json, math, os, re, subprocess, sys, tempfile
import yaml

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OY = f'{R}/openyamm-studio/build-xeen/oymap'
STEP = 50.0


def pip(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i][0], poly[i][1]
        x2, y2 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('blv'); ap.add_argument('scene', nargs='?')
    ap.add_argument('--things'); ap.add_argument('--assets', default=f'{R}/assets_dev')
    ap.add_argument('--json', action='store_true'); ap.add_argument('--min-area', type=float, default=64 * 64)
    a = ap.parse_args()
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OY, 'export', a.blv, '--world', 'xeen', '--assets', a.assets, '--out', t.name], check=True,
                       capture_output=True)
        d = json.load(open(t.name))
    m = d['map']; V = m['vertices']; F = m['faces']
    doorfaces = {fi for door in d.get('doors', []) for fi in door['faces']}
    floors = {}
    roofs = {}   # faces looking down: ceilings and the undersides of hanging blocks
    for i, f in enumerate(F):
        if f.get('is_portal') or i in doorfaces:
            continue
        if f['plane_normal'][2] <= -0.7 * 65536:
            roofs[i] = [V[v] for v in f['vertices']]
        if f['plane_normal'][2] < 0.7 * 65536:
            continue
        floors[i] = [V[v] for v in f['vertices']]
    def zat(poly, x, y):
        # the face's height at (x, y) from its plane (three corners)
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = poly[0], poly[1], poly[2]
        ax, ay, az, bx, by, bz = x1 - x0, y1 - y0, z1 - z0, x2 - x0, y2 - y0, z2 - z0
        nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
        if abs(nz) < 1e-9:
            return sum(p[2] for p in poly) / len(poly)
        return z0 - (nx * (x - x0) + ny * (y - y0)) / nz

    bbox = {fi: (min(p[0] for p in poly), min(p[1] for p in poly), max(p[0] for p in poly), max(p[1] for p in poly))
            for fi, poly in list(floors.items()) + list(roofs.items())}

    def roofs_at(x, y):
        for fi, poly in roofs.items():
            b = bbox[fi]
            if b[0] <= x <= b[2] and b[1] <= y <= b[3] and pip(x, y, poly):
                yield zat(poly, x, y)

    def floors_at(x, y):
        for fi, poly in floors.items():
            b = bbox[fi]
            if b[0] <= x <= b[2] and b[1] <= y <= b[3] and pip(x, y, poly):
                yield fi, zat(poly, x, y)

    BLOCK = 260   # a floor face this little above an edge is a block standing on it (a parapet, a step, a dais)

    def edge_sides(fi, p, q, t=0.5):
        # (points inside the face from the edge's point at t inward, 4 to 68 units off it; the point 4 outside it)
        mx, my = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        nx, ny = -(q[1] - p[1]) / L, (q[0] - p[0]) / L
        if not pip(mx + nx * 4, my + ny * 4, floors[fi]):
            nx, ny = -nx, -ny
        pin = [(mx + nx * d, my + ny * d) for d in (4, 20, 36, 52, 68)]   # on past the face (a fan's thin piece)
        return pin, (mx - nx * 4, my - ny * 4)

    def blocked(fi, z, pin):
        # the face's edge lies under a block or behind one standing on the same face within 68 of it: a floor face
        # from STEP to BLOCK above the face covers a point there with no underside between (a parapet round a well's
        # edge, a dais); a hanging thing with room under it (an upper bunk, a shelf) does not block
        for pt in pin:
            for fj, fz in floors_at(*pt):
                if fj != fi and STEP < fz - z <= BLOCK:
                    if not any(z + 96 < rz < fz for rz in roofs_at(*pt)):
                        return True
        return False

    # edges by line: key (direction, offset) rounded; store intervals with z at both ends
    lines = collections.defaultdict(list)
    landings = []   # (face, edge middle z, point outside): a floor the edge runs over (a block on a continuous floor)
    for fi, poly in floors.items():
        n = len(poly)
        for k in range(n):
            p, q = poly[k], poly[(k + 1) % n]
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy)
            if L < 8:
                continue
            # the edge is walked off where it is free of blocks: sampled every 64 along it (a long edge running
            # past a cauldron turned on the floor is free at its ends)
            nsamp = max(1, int(L // 64))
            blk = True
            for si in range(nsamp):
                t = (si + 0.5) / nsamp
                pin, pout = edge_sides(fi, p, q, t)
                zm = p[2] + (q[2] - p[2]) * t
                if not blocked(fi, zm, pin):
                    blk = False
                    landings.append((fi, zm, pout))
            ux, uy = dx / L, dy / L
            if ux < -1e-6 or (abs(ux) < 1e-6 and uy < 0):
                ux, uy = -ux, -uy
            off = -uy * p[0] + ux * p[1]
            key = (round(math.degrees(math.atan2(uy, ux)) * 2) / 2, round(off / 4))
            t0 = ux * p[0] + uy * p[1]; t1 = ux * q[0] + uy * q[1]
            z0, z1 = p[2], q[2]
            if t1 < t0:
                t0, t1, z0, z1 = t1, t0, z1, z0
            lines[key].append((t0, t1, z0, z1, fi, blk))
    adj = collections.defaultdict(dict)  # a -> {b: step from a up to b}
    for segs in lines.values():
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                a0, a1, az0, az1, fa, ablk = segs[i]; b0, b1, bz0, bz1, fb, bblk = segs[j]
                if fa == fb:
                    continue
                lo, hi = max(a0, b0), min(a1, b1)
                if hi - lo < 24:
                    continue
                mid = (lo + hi) / 2
                za = az0 + (az1 - az0) * ((mid - a0) / (a1 - a0) if a1 > a0 else 0)
                zb = bz0 + (bz1 - bz0) * ((mid - b0) / (b1 - b0) if b1 > b0 else 0)
                # an edge under a block (a parapet round a well, a dais on the floor) is not walked off
                if not ablk:
                    adj[fa][fb] = min(adj[fa].get(fb, 1e9), zb - za)
                if not bblk:
                    adj[fb][fa] = min(adj[fb].get(fa, 1e9), za - zb)
    # Off an edge onto the floor the edge stands over (a block or step standing on a continuous floor, whose outline
    # shares no edge with it): the highest floor under the point just outside, at most a step above the edge.
    for fi, zm, (x, y) in landings:
        under = [(fz, fj) for fj, fz in floors_at(x, y) if fj != fi and fz <= zm + STEP]
        if not under:
            continue
        fz, fj = max(under)
        if any(fz + 1 < rz < zm - 1 for rz in roofs_at(x, y)):
            continue   # a ceiling between: the point is beyond a wall, over another room's floor
        if fz < zm - STEP and any(zm + STEP < fa and not any(zm + 1 < rz < fa for rz in roofs_at(x, y))
                                  for fj2, fa in floors_at(x, y) if fj2 != fi):
            continue   # a drop through solid: the point is in a pit's wall (its rim floor stands over it with no room
            # under), the floor below is another room's (XD-12's smelting pit over the gate floor, 2026-11-22)
        adj[fi][fj] = min(adj[fi].get(fj, 1e9), fz - zm)
        if zm - fz <= STEP:
            adj[fj][fi] = min(adj[fj].get(fi, 1e9), zm - fz)
    scene = yaml.safe_load(open(a.scene or a.blv[:-4] + '.scene.yml'))

    def face_at(x, y, z, tol=64):
        best = None
        for fi, poly in floors.items():
            if pip(x, y, poly):
                fz = sum(p[2] for p in poly) / len(poly)
                if fz <= z + tol and (best is None or fz > best[1]):
                    best = (fi, fz)
        return best[0] if best else None

    for lad in scene.get('ladders') or []:
        b, t = lad['bottom'], lad.get('top_exit') or lad['top']
        fb, ft = face_at(*b, tol=8), face_at(*t, tol=8)  # not the ladder's own rungs
        if fb is not None and ft is not None:
            adj[fb][ft] = 0; adj[ft][fb] = 0
    sp = scene['party_start_points'][0]['position']
    s0 = face_at(*sp)
    if s0 is None:
        print(os.path.basename(a.blv), 'no floor under the start'); sys.exit(2)

    def bfs(start, ok, graph=adj):
        seen = {start}; q = [start]
        while q:
            u = q.pop()
            for v, st in graph[u].items():
                if v not in seen and ok(u, v, st):
                    seen.add(v); q.append(v)
        return seen

    reach = bfs(s0, lambda u, v, st: st <= STEP)
    # back: the floors that reach the start (the joins are one-way where an edge is under a block)
    radj = collections.defaultdict(dict)
    for u in list(adj):
        for v, st in adj[u].items():
            radj[v][u] = st
    back = bfs(s0, lambda u, v, st: st <= STEP, radj)
    trapped = [fi for fi in reach - back]

    def area(poly):
        s = 0
        for i in range(len(poly)):
            s += poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
        return abs(s) / 2

    # group trapped floors into pockets (touching with any step)
    pockets = []; left = set(trapped)
    while left:
        u = left.pop(); grp = {u}; q = [u]
        while q:
            x = q.pop()
            for v in adj[x]:
                if v in left:
                    left.discard(v); grp.add(v); q.append(v)
        pockets.append(grp)
    things = []
    if a.things and os.path.exists(a.things):
        thing_lines = open(a.things).read().splitlines()
    else:
        thing_lines = subprocess.run([OY, 'things', a.blv, '--world', 'xeen', '--assets', a.assets],
                                     capture_output=True, text=True).stdout.splitlines()
    if True:
        for line in thing_lines:
            mm = re.match(r'^event (\d+) "(.*)" (\w+) in sector .* used from \[(-?\d+), (-?\d+), (-?\d+)\]', line)
            if mm:
                things.append((int(mm.group(1)), mm.group(2), mm.group(3), int(mm.group(4)), int(mm.group(5)),
                               int(mm.group(6))))
    res = []
    for grp in pockets:
        ar = sum(area(floors[f]) for f in grp)
        if ar < a.min_area:
            continue
        zs = [p[2] for f in grp for p in floors[f]]
        texs = sorted({F[f]['texture'] for f in grp})
        cx = sum(p[0] for f in grp for p in floors[f]) / sum(len(floors[f]) for f in grp)
        cy = sum(p[1] for f in grp for p in floors[f]) / sum(len(floors[f]) for f in grp)
        # the lowest step up out of the pocket
        up = min([st for f in grp for v, st in adj[f].items() if v not in grp] or [None], key=lambda s: s or 1e9)
        esc = []
        for ev, title, kind, x, y, z in things:
            for f in grp:
                if kind in ('exit', 'teleport', 'lever', 'switch', 'button', 'door') and pip(x, y, floors[f]) \
                        and abs(z - sum(p[2] for p in floors[f]) / len(floors[f])) < 96:
                    esc.append(f'{kind} {ev} "{title}"'); break
        res.append({'at': [round(cx), round(cy)], 'z': [min(zs), max(zs)], 'area': round(ar), 'textures': texs,
                    'climb_out': up, 'faces': len(grp), 'things': esc})
    out = {'map': os.path.basename(a.blv), 'floors': len(floors), 'reached': len(reach), 'pockets': res}
    if a.json:
        print(json.dumps(out))
    else:
        print(f"{out['map']}: {len(floors)} floors, {len(reach)} reached from the start, {len(res)} pockets not left on foot")
        for p in res:
            print(f"  pocket at {p['at']} z {p['z'][0]:.0f}..{p['z'][1]:.0f}, {p['area']} sq, {p['faces']} faces "
                  f"{p['textures'][:4]}, lowest step out {p['climb_out']}; things there: {p['things'] or 'none'}")
    sys.exit(1 if res else 0)


main()
