#!/usr/bin/env python3
"""Big monsters against the openings on their way (F75 of reviews/PLAYER_FEEDBACK_20261126.md, XD-18 p1 "dragon gets
stuck", p2 "they get stuck"): every placed hostile monster and spawn marker of a Xeen indoor map against the openings
(portals) it can walk or fly to from its post.

  tools/xeen/check_monster_fit.py [--maps xeen_xd18 ...] [--assets ROOT] [--mount STAGE] [--cache DIR] [--json]
      [--verbose] [--squeeze] [--suggest] [--self-test]
      (default: every xeen_*.blv with a scene; run whole-world checks through tools/heavy.sh 4)

How a monster's body meets the level indoors (game/indoor/IndoorWorldRuntime.cpp, GameplayActorService.h): its
collision radius is its own (the scene actor's `radius`, else the descriptor's Radius) capped at the world's
`actorMovement.levelRadiusLimit` (60 in Xeen's world.yml, D-32, as MM6-MM8), and its collision height is its own
(`height`, else the descriptor's Height), not capped. So a monster passes any opening at least 2 x 60 wide that is at
least its height high, whatever its body's width; an opening lower than its height stops it (D-32 keeps the dragons
out of the party's 288-high passages that way). A monster that chases the party to such an opening stops with its
centre about 60 from the opening's plane and its body (radius 238 for a dragon) sunk into the frame: the player sees a
dragon stuck in a doorway (XD-18 p1, p2; XD-07 p1 before D-154's leash).

What is measured (on the built BLV, `oymap export`; the scene's actors and spawns, the BLV's spawn markers):
- bodies: every hostile placed actor at its post, hidden (staged) actors too (a staged monster chases like any other
  once it appears, D-185; one that never chases goes in KEPT with its reason), and every spawn marker by the widest and
  tallest row its slot can roll. A body is the actor's own `radius`/`height`, else the descriptor's; its capped
  radius is c = min(radius, levelRadiusLimit) (60 in Xeen);
- openings: the BLV's portal faces, merged per pair of sectors and plane; a wall opening's width (along the wall) and
  height (its z extent), a floor or roof opening's narrowest width; an opening has a door leaf when a door's bounds
  lie in it (the export's `doors`);
- the monster's way: from its post's sector through every opening it passes, as far as its leash allows
  (`leash_radius` of a placed actor, 2D about its post as keepStepOnLeash; spawn markers and actors without a leash
  roam the whole graph; `immobile` actors have leash 0). Walkers use only wall openings whose foot is within a step
  (56) of a floor beside them; flyers also use floor and roof holes;
- an opening the monster comes up to: its nearest point within leash + body radius + MARGIN (64) of the post (2D).

The fit rule (D-185, reviews/D185_D188_DECISION.md; exit 1 on an error; KEPT below lists kept sites with reasons):
- An opening **passes** the body when its width is at least 2c and its height at least the body's height (no extra
  margin: the engine's test). An opening narrower than 2c is a wall to the planner and is not counted. When a lane
  raises an opening for a monster, it uses the next multiple of 32 at or above the height.
- `fit.stuck` (error): an opening at least 2c wide but lower than the body that the monster comes up to, unless the
  body has a way round: another opening between the same two sectors, with no door leaf, that it passes and that lies
  within its reach too (XD-09's tumbler slots beside their doorways; `--self-test`). The monster presses into the
  frame when it chases the party through it (XD-18 p1, p2). Fix it, in this order: a `leash` that keeps its leash
  circle radius + MARGIN clear of the opening (D-154, at most 1,536; `--suggest`), a post deeper in its room, an
  opening it fits, a KEPT line with a reason.
- `fit.squeeze` (warning): a passing opening narrower than 2 x radius - SQUEEZE (64): its body runs through the
  frame's sides as it goes through.
- At the leash a pursuing actor stands facing its target (tacticMoveLeavesLeash -> AI_TacticStandFacingTarget).
Known limit: narrows inside one sector (a pillar pair, a corridor built as part of a room) are not openings here.
"""
import argparse
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_arrivals as arrivals  # noqa: E402

MARGIN = 64.0        # the body's clearance from an opening it cannot pass, beyond its radius
SQUEEZE = 64.0       # an opening this much narrower than the body's diameter is a squeeze
STEP = 56.0          # the engine's step (MaximumRise 50) with rounding
DEFAULT_LIMIT = 60.0
DOOR_SLACK = 64.0    # a door leaf within this of an opening's box (its wall's depth) is that opening's leaf
# (map stem, monster id or 'slot N', rounded opening centre x, y) -> reason
KEPT = {
    ('xeen_xd01', 'slot 8', 128, 896): "Joe's counter window (open:office_counter, sill 96, 128 high): a window, not "
                                       "a way; the slot's flyers start 4,654 away in the loading bay (F75, 2026-11-26)",
}


def load_limit(assets):
    world = arrivals.load_yaml(os.path.join(assets, 'worlds', 'xeen', 'world.yml'))
    return float((world.get('actorMovement') or {}).get('levelRadiusLimit') or DEFAULT_LIMIT)


def descriptors(assets):
    """InternalName -> (height, radius) from the engine's and Xeen's monster_descriptors.txt."""
    out = {}
    for path in (os.path.join(assets, 'engine', 'data_tables', 'monster_descriptors.txt'),
                 os.path.join(assets, 'worlds', 'xeen', 'data_tables', 'monster_descriptors.txt')):
        for f in arrivals.tsv(path):
            if len(f) > 3 and f[0].strip().isdigit():
                try:
                    out[f[1].strip()] = (float(f[2]), float(f[3]))
                except ValueError:
                    pass
    return out


def body_of_row(world, desc, mid):
    """(height, radius, flies) of a monster row."""
    h, r = desc.get(world.cell(mid, 2), (128.0, 32.0))
    return h, r, world.cell(mid, 9).upper().startswith('Y')


class Openings:
    """The BLV's portal faces merged into openings per sector pair and plane."""

    def __init__(self, data):
        m = data['map']
        verts = np.array(m['vertices'], float)
        faces = [(i, f) for i, f in enumerate(m['faces']) if f.get('is_portal') or f['attributes'] & 1]
        groups = {}
        for i, f in faces:
            p = verts[f['vertices']]
            n = np.array(f.get('plane_normal') or [0, 0, 1], float)
            n /= max(np.linalg.norm(n), 1e-9)
            if n[2] < 0 or (n[2] == 0 and (n[1] < 0 or (n[1] == 0 and n[0] < 0))):
                n = -n
            pair = tuple(sorted((f['room'], f['room_behind'])))
            key = (pair, tuple(np.round(n, 2)), round(float(n @ p.mean(0)) / 16))
            groups.setdefault(key, []).append((i, p))
        self.list = []
        for (pair, n, _), members in groups.items():
            # split a group into pieces joined by shared corners
            pieces = []
            for i, p in members:
                pts = {tuple(np.round(v)) for v in p}
                hit = [k for k, pc in enumerate(pieces) if pts & pc['pts']]
                merged = {'faces': [i], 'pts': pts, 'poly': [p]}
                for k in sorted(hit, reverse=True):
                    pc = pieces.pop(k)
                    merged['faces'] += pc['faces']
                    merged['pts'] |= pc['pts']
                    merged['poly'] += pc['poly']
                pieces.append(merged)
            for pc in pieces:
                self.list.append(self._measure(pair, np.array(n), pc))
        boxes = [(np.array(d['bounds_min'], float), np.array(d['bounds_max'], float)) for d in data.get('doors') or []]
        for o in self.list:
            lo, hi = o['pts'].min(0) - DOOR_SLACK, o['pts'].max(0) + DOOR_SLACK
            o['door'] = any((dlo <= hi).all() and (dhi >= lo).all() and (dhi[2] - dlo[2]) >= 0.5 * (o['zmax'] - o['zmin'])
                            for dlo, dhi in boxes)

    @staticmethod
    def _measure(pair, n, pc):
        pts = np.array(sorted(pc['pts']), float)
        o = {'rooms': pair, 'faces': sorted(pc['faces']), 'pts': pts, 'centre': pts.mean(0),
             'zmin': float(pts[:, 2].min()), 'zmax': float(pts[:, 2].max())}
        if abs(n[2]) < 0.5:   # a wall opening
            u = np.array([-n[1], n[0], 0.0])
            u /= max(np.linalg.norm(u), 1e-9)
            s = pts @ u
            o.update(kind='wall', normal=n, width=float(s.max() - s.min()), height=o['zmax'] - o['zmin'],
                     seg=(pts[int(np.argmin(s))][:2], pts[int(np.argmax(s))][:2]))
        else:                 # a floor or roof opening: its narrowest width in plan
            xy = pts[:, :2]
            best = float('inf')
            for k in range(len(xy)):
                for j in range(k + 1, len(xy)):
                    d = xy[j] - xy[k]
                    ln = np.linalg.norm(d)
                    if ln < 1:
                        continue
                    perp = np.array([-d[1], d[0]]) / ln
                    s = xy @ perp
                    if s.max() - s.min() > 1:   # only directions of the hull's edges give the narrowest width
                        if (s >= -1e-6 + s[k]).all() or (s <= s[k] + 1e-6).all():
                            best = min(best, float(s.max() - s.min()))
            o.update(kind='hole', normal=n, width=best if best < float('inf') else 0.0, height=float('inf'))
        return o

    @staticmethod
    def distance2d(o, p):
        p = np.asarray(p[:2], float)
        if o['kind'] == 'wall':
            a, b = o['seg']
            ab = b - a
            t = 0.0 if not ab.any() else max(0.0, min(1.0, float((p - a) @ ab / (ab @ ab))))
            return float(np.linalg.norm(p - (a + ab * t)))
        xy = o['pts'][:, :2]
        lo, hi = xy.min(0), xy.max(0)
        return float(np.linalg.norm(np.maximum(0, np.maximum(lo - p, p - hi))))


def floor_room(geo, faces, p, up=64.0, down=4096.0):
    """(z, room) of the highest floor face under p."""
    x, y, z = p
    best = None
    for fi, (poly, n) in enumerate(zip(geo.polys, geo.normals)):
        if n[2] < 0.5 or not (geo.lo[fi][0] <= x <= geo.hi[fi][0] and geo.lo[fi][1] <= y <= geo.hi[fi][1]):
            continue
        inside = False
        for e in range(len(poly)):
            x1, y1, x2, y2 = poly[e][0], poly[e][1], poly[(e + 1) % len(poly)][0], poly[(e + 1) % len(poly)][1]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        if not inside:
            continue
        fz = (geo.ds[fi] - n[0] * x - n[1] * y) / n[2]
        if z - down <= fz <= z + up and (best is None or fz > best[0]):
            best = (fz, faces[geo.ids[fi]]['room'])
    return best


def walk_foot(geo, faces, o, room):
    """True when a walker in `room` can reach the wall opening's foot: a floor of that room within a step of it, just
    in front of the opening on either side."""
    c = o['centre'].copy()
    for side in (1, -1):
        q = c + o['normal'] * 64 * side
        hit = floor_room(geo, faces, [q[0], q[1], o['zmin'] + 32], up=0, down=STEP + 32)
        if hit and hit[1] == room and abs(hit[0] - o['zmin']) <= STEP:
            return True
    return False


def bodies(world, desc, scene, data, stem):
    """The hostile bodies of a map: placed actors (with their leash) and spawn markers (by every row they can roll)."""
    actors = {a['actor_index']: a for a in scene['initial_state'].get('actors') or []}
    out = []
    for h in arrivals.hostiles(world, scene, stem + '.blv', data['map'].get('spawns') or [], hidden=True):
        if h['id'].startswith('actor '):
            a = actors[int(h['id'].split()[1])]
            mid = h['monster']
            rh, rr, fly = body_of_row(world, desc, mid)
            out.append(dict(h, radius=float(a.get('radius') or rr), body_height=float(a.get('height') or rh),
                            flies=fly, leash=float(a.get('leash_radius') or 0) or None,
                            immobile=bool(a.get('immobile')), sector=a.get('sector_id')))
        else:
            if not h['rows']:
                continue
            got = [body_of_row(world, desc, m) for m in h['rows']]
            out.append(dict(h, radius=max(g[1] for g in got), body_height=max(g[0] for g in got),
                            flies=any(g[2] for g in got), leash=None, immobile=False, sector=None))
    return out


def export(stem, assets, mount, cache):
    """oymap export of the map in `mount` (a staged root) when it has one, else in `assets`."""
    if not mount or not os.path.exists(os.path.join(mount, 'worlds', 'xeen', 'maps', stem + '.blv')):
        return arrivals.export(stem, assets, cache)
    path = os.path.join(mount, 'worlds', 'xeen', 'maps', stem + '.blv')
    out = os.path.join(cache or mount, stem + '.mount.json')
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(path):
        arrivals.subprocess.run([arrivals.OYMAP, 'export', path, '--world', 'xeen', '--assets', assets, '--out', out],
                                check=True, capture_output=True)
    return json.load(open(out))


def check_map(world, desc, limit, stem, cache, ignore_leash=False, mount=None, drop=()):
    """The flags of one map. `drop`: opening centres (rounded x, y) to take away (the self-test)."""
    maps = os.path.join(mount, 'worlds', 'xeen', 'maps') if mount else os.path.join(world.xeen, 'maps')
    if not os.path.exists(os.path.join(maps, stem + '.scene.yml')):
        maps = os.path.join(world.xeen, 'maps')
    scene = arrivals.load_yaml(os.path.join(maps, stem + '.scene.yml'))
    data = export(stem, world.assets, mount, cache)
    faces = data['map']['faces']
    geo = arrivals.Geometry(data)
    ops = Openings(data)
    ops.list = [o for o in ops.list if (round(o['centre'][0]), round(o['centre'][1])) not in set(drop)]
    by_room = {}
    for k, o in enumerate(ops.list):
        for r in o['rooms']:
            by_room.setdefault(r, []).append(k)
    results = []
    feet = {}
    for b in bodies(world, desc, scene, data, stem):
        post = b['at']
        start = b['sector']
        if not start:
            hit = floor_room(geo, faces, [post[0], post[1], post[2] + 32])
            start = hit[1] if hit else None
        if not start:
            continue
        leash = 0.0 if b['immobile'] else (None if ignore_leash else b['leash'])
        reach = (leash if leash is not None else float('inf'))
        cap = min(b['radius'], limit)
        seen, queue, flags = {start}, [start], []
        done = set()

        def usable(k, room):
            """The body can use opening k from `room` at all (kind and foot), and comes up to it (2D distance)."""
            o = ops.list[k]
            if o['kind'] == 'hole' and not b['flies']:
                return None
            if o['kind'] == 'wall' and not b['flies']:
                if (k, room) not in feet:
                    feet[(k, room)] = walk_foot(geo, faces, o, room)
                if not feet[(k, room)]:
                    return None
            d = Openings.distance2d(o, post)
            return None if d > reach + b['radius'] + MARGIN else d

        def way_round(k, room):
            """Another doorless opening between the same two sectors that the body passes and comes up to."""
            o = ops.list[k]
            for j in by_room.get(room, []):
                q = ops.list[j]
                if j == k or q['rooms'] != o['rooms'] or q['door']:
                    continue
                if q['width'] >= 2 * cap and q['height'] >= b['body_height'] and usable(j, room) is not None:
                    return True
            return False

        while queue:
            room = queue.pop()
            for k in by_room.get(room, []):
                if k in done:
                    continue
                o = ops.list[k]
                d = usable(k, room)
                if d is None:
                    continue
                done.add(k)
                if o['width'] < 2 * cap:   # a slit: the route planner (capped radius) never leads through it
                    continue
                passes = o['height'] >= b['body_height']
                if not passes:
                    if way_round(k, room):
                        continue
                    clear = d - (reach if leash is not None else 0)
                    flags.append({'rule': 'fit.stuck', 'opening': k, 'distance': round(d),
                                  'clear': round(clear) if leash is not None else None})
                    continue
                if o['width'] < 2 * b['radius'] - SQUEEZE:
                    flags.append({'rule': 'fit.squeeze', 'opening': k, 'distance': round(d), 'clear': None})
                if d <= reach:
                    other = o['rooms'][1] if o['rooms'][0] == room else o['rooms'][0]
                    if other not in seen and other:
                        seen.add(other)
                        queue.append(other)
        for fl in flags:
            o = ops.list[fl['opening']]
            key = (stem, b['monster'] if b['id'].startswith('actor') else 'slot %s' % b['monster'],
                   round(o['centre'][0]), round(o['centre'][1]))
            results.append({'map': stem, 'rule': fl['rule'], 'who': b['id'], 'actor_id': b.get('actor_id'), 'monster': b['monster'],
                            'name': b['name'], 'group': b['group'], 'post': [round(v) for v in post],
                            'radius': b['radius'], 'height': b['body_height'], 'flies': b['flies'],
                            'leash': b['leash'], 'opening': {'rooms': list(o['rooms']), 'kind': o['kind'],
                                                             'centre': [round(v) for v in o['centre']],
                                                             'width': round(o['width']),
                                                             'height': None if o['kind'] == 'hole' else round(o['height'])},
                            'distance': fl['distance'], 'kept': KEPT.get(key)})
    return results


SELF_TEST = {}
XD09_SLOTS = [(4224, 1280), (5312, 376)]       # open:tn_slot, open:te_slot (256 x 112)
XD09_DOORWAYS = [(3776, 1280), (5312, 704)]    # open:tn_lock 256 x 448, open:lock_te 192 x 448, beside them


def slot_flags(drop=()):
    """The XD-09 tumbler slots that carry a fit.stuck flag (installed map), with the openings `drop` taken away."""
    t = SELF_TEST
    flags = check_map(t['world'], t['desc'], t['limit'], 'xeen_xd09', t['cache'], drop=drop)
    return sorted({tuple(r['opening']['centre'][:2]) for r in flags if r['rule'] == 'fit.stuck'} & set(XD09_SLOTS))


def self_test():
    """D-185's way round, on XD-09: each tumbler slot joins the lock hall and a tumbler room beside a doorless doorway
    in the same wall, which every golem passes, so the slot is not counted; take the doorway away and it is again.

    >>> slot_flags()
    []
    >>> slot_flags(drop=XD09_DOORWAYS)
    [(4224, 1280), (5312, 376)]
    """


def describe(r):
    o = r['opening']
    size = '%d wide' % o['width'] + ('' if o['height'] is None else ' x %d high' % o['height'])
    leash = 'leash %d' % r['leash'] if r['leash'] else 'no leash'
    text = '%s %s: %s %s (%s, r %d h %d%s, %s, group %s, post %s) -> %s opening sectors %s at %s, %s, %d from post' % (
        r['map'], r['rule'], r['who'], r['name'], r['monster'], r['radius'], r['height'], ' fly' if r['flies'] else '',
        leash, r['group'], r['post'], o['kind'], o['rooms'], o['centre'], size, r['distance'])
    if r['kept']:
        text += ' [kept: %s]' % r['kept']
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--maps', nargs='+')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--verbose', action='store_true', help='one line per monster and opening')
    ap.add_argument('--assets', default=os.path.join(arrivals.ROOT, 'assets_dev'))
    ap.add_argument('--cache', help='directory to keep the oymap exports in (reused while newer than the BLV)')
    ap.add_argument('--mount', help='a staged root (oymap install --mount) whose maps replace the installed ones')
    ap.add_argument('--squeeze', action='store_true', help='also print the fit.squeeze warnings one by one')
    ap.add_argument('--self-test', action='store_true', help="run the doctests (D-185's way round on XD-09) and exit")
    ap.add_argument('--suggest', action='store_true',
                    help="per flagged placed actor, the largest leash that keeps its body MARGIN clear of every opening "
                         "it cannot pass (measured as if it had no leash)")
    args = ap.parse_args()
    assets = os.path.abspath(args.assets)
    world = arrivals.World(assets)
    desc = descriptors(assets)
    limit = load_limit(assets)
    if args.self_test:
        import doctest
        SELF_TEST.update(world=world, desc=desc, limit=limit, cache=args.cache)
        failed, tried = doctest.testmod(verbose=args.verbose)
        print('self-test: %d of %d passed' % (tried - failed, tried))
        return 1 if failed or not tried else 0
    if args.maps:
        stems = [m if m.startswith('xeen_') else 'xeen_' + m for m in args.maps]
    else:
        stems = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(world.xeen, 'maps', 'xeen_*.blv'))
                       if os.path.exists(p[:-4] + '.scene.yml'))
    results = []
    for stem in stems:
        results += check_map(world, desc, limit, stem, args.cache, mount=args.mount)
    if args.suggest:
        for stem in sorted({r['map'] for r in results if r['rule'] == 'fit.stuck'}):
            best = {}
            for r in check_map(world, desc, limit, stem, args.cache, ignore_leash=True, mount=args.mount):
                if r['rule'] != 'fit.stuck' or not r['who'].startswith('actor'):
                    continue
                room = r['distance'] - r['radius'] - MARGIN
                if r['who'] not in best or room < best[r['who']][0]:
                    best[r['who']] = (room, r)
            for who, (room, r) in sorted(best.items(), key=lambda kv: int(kv[0].split()[1])):
                print('suggest %s %s %s at %s: leash <= %d (now %s; nearest opening %s at %s)' % (
                    stem, who, r['name'], r['post'], room, r['leash'], r['opening']['rooms'], r['opening']['centre']))
    errors = [r for r in results if r['rule'] == 'fit.stuck' and not r['kept']]
    if args.json:
        print(json.dumps(results, indent=1, default=float))
        return 1 if errors else 0
    per_map = {}
    sites = {}
    for r in results:
        c = per_map.setdefault(r['map'], {'fit.stuck': 0, 'fit.squeeze': 0, 'kept': 0})
        c['kept' if r['kept'] else r['rule']] += 1
        if args.verbose and (r['rule'] == 'fit.stuck' or r['kept'] or args.squeeze):
            print(describe(r))
        if r['rule'] == 'fit.stuck' or args.squeeze:
            sites.setdefault((r['map'], r['rule'], tuple(r['opening']['centre'])), []).append(r)
    for (stem, rule, centre), rs in sorted(sites.items()):
        o = rs[0]['opening']
        size = '%d wide' % o['width'] + ('' if o['height'] is None else ' x %d high' % o['height'])
        near = min(rs, key=lambda r: r['distance'])
        names = sorted({'%s %s' % (r['who'], r['name']) for r in rs})
        print('%s %s: %s opening sectors %s at %s, %s; %d bodies (%s), nearest %s %d from its post%s' % (
            stem, rule, o['kind'], o['rooms'], list(centre), size, len(names), ', '.join(names[:6]) +
            (' ...' if len(names) > 6 else ''), near['who'], near['distance'],
            ' [kept: %s]' % near['kept'] if all(r['kept'] for r in rs) else ''))
    for stem, c in sorted(per_map.items()):
        print('%s: stuck %d, squeeze %d, kept %d' % (stem, c['fit.stuck'], c['fit.squeeze'], c['kept']))
    print('%d maps, %d stuck (errors), %d squeeze (warnings), %d kept' % (
        len(stems), len(errors), sum(r['rule'] == 'fit.squeeze' and not r['kept'] for r in results),
        sum(bool(r['kept']) for r in results)))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
