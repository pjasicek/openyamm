"""D7's review geometry: island outlines, road strips, masks and the measured figures (A6 sub-agent, 2026-11-21).

The outlines are the review's own (24-point clouds as X9's); L2 draws the studio's platforms from the plan's `at` and
`extent`. Imported by d7_render.py, d7_brief.py and board_d7.py.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw

import d7_design as D

RES = 64                                   # map units per mask pixel
W_PX, H_PX = D.HALF[0] * 2 // RES, D.HALF[1] * 2 // RES
SPACE = D.SPACE
QUIET_R = 2048                             # quiet: walkable cloud farther than this from any hostile group
TOWN_BUFFER = 3072
MERGE = 400                                # D-20 census: points chained within 400 are one spot
FACING = {'n': (0, 1), 's': (0, -1), 'e': (1, 0), 'w': (-1, 0), 'ne': (0.707, 0.707), 'nw': (-0.707, 0.707),
          'se': (0.707, -0.707), 'sw': (-0.707, -0.707)}
FACING_MM = {'e': 0, 'ne': 256, 'n': 512, 'nw': 768, 'w': 1024, 'sw': 1280, 's': 1536, 'se': 1792}


def to_px(p):
    return ((p[0] + D.HALF[0]) / RES, (D.HALF[1] - p[1]) / RES)


def cloud_poly(s, n=24):
    """A rounded cloud outline inside the space's extent (a superellipse with seeded wobble)."""
    rnd = random.Random(s.get('seed', 0) * 7919)
    cx, cy = s['at']
    ax, ay = s['extent'][0] / 2, s['extent'][1] / 2
    pts = []
    k = 2.6 if s['kind'] in ('town', 'lake') else 2.2
    for i in range(n):
        t = 2 * math.pi * i / n
        c, sn = math.cos(t), math.sin(t)
        r = (abs(c) ** k + abs(sn) ** k) ** (-1 / k)
        wob = 1.0 if s['kind'] == 'town' else 0.9 + 0.1 * rnd.random()
        pts.append((cx + ax * r * c * wob, cy + ay * r * sn * wob))
    return pts


def polys():
    return {s['id']: cloud_poly(s) for s in D.SPACES}


def ray_exit(poly, centre, target):
    """Where the segment centre -> target leaves the polygon."""
    best = None
    cx, cy = centre
    dx, dy = target[0] - cx, target[1] - cy
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((ax - cx) * ey - (ay - cy) * ex) / den
        u = ((ax - cx) * dy - (ay - cy) * dx) / den
        if 0 <= t <= 1 and 0 <= u <= 1 and (best is None or t < best):
            best = t
    if best is None:
        return centre
    return (cx + dx * best, cy + dy * best)


def link_ends(l, P):
    a, b = SPACE[l['a']], SPACE[l['b']]
    ta = l['gate'] if l.get('gate') and a['kind'] == 'town' else None
    tb = l['gate'] if l.get('gate') and b['kind'] == 'town' else None
    pa = ta or ray_exit(P[l['a']], a['at'], tb or b['at'])
    pb = tb or ray_exit(P[l['b']], b['at'], ta or a['at'])
    return pa, pb


def strip(p, q, width):
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * width / 2, dx / L * width / 2
    # run 256 into each island so the strip joins the cloud
    ux, uy = dx / L * 256, dy / L * 256
    p2, q2 = (p[0] - ux, p[1] - uy), (q[0] + ux, q[1] + uy)
    return [(p2[0] + nx, p2[1] + ny), (q2[0] + nx, q2[1] + ny), (q2[0] - nx, q2[1] - ny), (p2[0] - nx, p2[1] - ny)]


def masks(P):
    """Walkable mask (islands and roads) and an id image (which space or link each pixel belongs to)."""
    img = Image.new('I', (W_PX, H_PX), 0)
    draw = ImageDraw.Draw(img)
    names = ['']
    for l in D.LINKS:
        names.append(l['id'])
        p, q = link_ends(l, P)
        draw.polygon([to_px(v) for v in strip(p, q, l['width'])], fill=len(names) - 1)
    for s in D.SPACES:
        names.append(s['id'])
        draw.polygon([to_px(v) for v in P[s['id']]], fill=len(names) - 1)
    ids = np.array(img)
    return ids > 0, ids, names


def link_length(l, P):
    p, q = link_ends(l, P)
    return math.hypot(q[0] - p[0], q[1] - p[1])


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def all_points():
    """Every point of interest: the design's points and A4's house doors (Olympus)."""
    pts = [dict(p) for p in D.POINTS if p['kind'] != 'board']
    for bid, house, service, at, facing, fp, zone, note in D.BUILDINGS:
        pts.append(dict(id='poi:' + bid.split(':')[1], kind='house_door', space='zone:olympus', at=at,
                        text=f'{service} (house {house}), door facing {facing}', house=house, facing=facing))
    return pts


def census(points):
    """D-20: chain points within MERGE; return the spots (lists of point ids) and their middles."""
    n = len(points)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if dist(points[i]['at'], points[j]['at']) <= MERGE:
                parent[find(i)] = find(j)
    spots = {}
    for i in range(n):
        spots.setdefault(find(i), []).append(i)
    out = []
    for members in spots.values():
        xs = [points[i]['at'][0] for i in members]
        ys = [points[i]['at'][1] for i in members]
        out.append(dict(ids=[points[i]['id'] for i in members], at=(sum(xs) / len(xs), sum(ys) / len(ys))))
    return out


def graph(P):
    """Centre-to-centre network distances (gates for Olympus) for road lengths."""
    nodes = {s['id']: s['at'] for s in D.SPACES}
    adj = {k: [] for k in nodes}
    for l in D.LINKS:
        pa, pb = link_ends(l, P)
        w = dist(nodes[l['a']], pa) + dist(pa, pb) + dist(pb, nodes[l['b']])
        adj[l['a']].append((l['b'], w))
        adj[l['b']].append((l['a'], w))
    return adj


def shortest(adj, a, b):
    import heapq
    best = {a: 0.0}
    heap = [(0.0, a)]
    while heap:
        d, u = heapq.heappop(heap)
        if u == b:
            return d
        if d > best.get(u, 1e18):
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < best.get(v, 1e18):
                best[v] = nd
                heapq.heappush(heap, (nd, v))
    return None


def figures(P):
    walk, ids, names = masks(P)
    f = {}
    px = RES * RES
    f['room_cells'] = list(D.ROOM)
    f['room_units'] = [D.ROOM[0] * 512, D.ROOM[1] * 512]
    f['walkable_area_millions'] = round(walk.sum() * px / 1e6, 1)
    road_px = sum(int((ids == i).sum()) for i, nm in enumerate(names) if nm.startswith('link:'))
    f['road_area_millions'] = round(road_px * px / 1e6, 1)
    f['olympus_area_millions'] = round(int((ids == names.index('zone:olympus')).sum()) * px / 1e6, 1)
    # monsters
    placed = sum(g['count'] for g in D.GROUPS)
    xp = sum(g['count'] * D.ROWS[g['actor']][2] for g in D.GROUPS)
    f['placed_monsters'] = placed
    f['groups'] = len(D.GROUPS)
    f['kill_xp_party'] = xp
    f['kill_xp_per_member'] = round(xp / 4)
    f['kill_xp_per_member_with_megadragon'] = round((xp + D.ROWS[11654][2]) / 4)
    f['kill_xp_target'] = 48500
    f['by_row'] = {}
    for g in D.GROUPS:
        name, level, gxp, mode = D.ROWS[g['actor']]
        r = f['by_row'].setdefault(str(g['actor']), dict(name=name, level=level, xp=gxp, count=0, groups=0))
        r['count'] += g['count']
        r['groups'] += 1
    f['band'] = [min(D.ROWS[g['actor']][1] for g in D.GROUPS), max(D.ROWS[g['actor']][1] for g in D.GROUPS)]
    f['bandits_uncounted'] = sum(b['count'] for b in D.BANDITS)
    # quiet share
    h, w = walk.shape
    yy, xx = np.mgrid[0:h, 0:w]
    near = np.zeros_like(walk)
    for g in D.GROUPS + [D.BOSS]:
        gx, gy = to_px(g['at'])
        r = (QUIET_R + (g.get('leash', 0))) / RES
        near |= (xx - gx) ** 2 + (yy - gy) ** 2 <= r * r
    f['quiet_share'] = round(float((walk & ~near).sum() / walk.sum()), 3)
    # breath: the Megadragon's leash circle + D-54's margin against every walkable pixel but its own road
    # D-58 D-2: every walkable place but the roost and its road (the castaway's island and bridge now count)
    own = {names.index(n) for n in ('room:roost', 'link:dragon_road')}
    other = walk & ~np.isin(ids, list(own))
    bx, by = to_px(D.BOSS['at'])
    dpx = np.sqrt((xx - bx) ** 2 + (yy - by) ** 2) * RES - D.BOSS['leash']
    f['megadragon_clear'] = int(dpx[other].min())
    f['megadragon_clear_needed'] = D.BREATH_MARGIN
    sw = names.index('room:stranded_west')
    f['stranded_west_from_leash'] = int(dpx[ids == sw].min())
    f['stranded_bridge_from_leash'] = int(dpx[ids == names.index('link:stranded_bridge')].min())
    # first fight per arrival
    ff = {}
    for a in D.ARRIVALS:
        groups = D.GROUPS + ([D.BOSS] if a['space'] == 'room:roost' else [])
        d, gid = min((dist(a['at'], g['at']), g['id']) for g in groups)
        ok = (a['kind'] == 'town' and d >= TOWN_BUFFER + 2048) or (2000 <= d <= 6000) or a['id'] == 'entrance:dd17_roof'
        ff[a['id']] = dict(distance=round(d), group=gid, ok=bool(ok))
    f['first_fight'] = ff
    town = SPACE['zone:olympus']
    tp = P['zone:olympus']
    f['olympus_nearest_group'] = round(min(min(dist(v, g['at']) for v in tp) for g in D.GROUPS))
    # points
    pts = all_points()
    spots = census(pts)
    f['points'] = len(pts)
    f['points_of_interest'] = len(spots)
    nn = []
    for i, s in enumerate(spots):
        nn.append(min(dist(s['at'], t['at']) for j, t in enumerate(spots) if j != i))
    nn.sort()
    f['poi_nn_median'] = round(nn[len(nn) // 2])
    f['poi_nn_range'] = [round(nn[0]), round(nn[-1])]
    f['merged_spots'] = [s['ids'] for s in spots if len(s['ids']) > 1]
    f['poi_outside_olympus'] = sum(1 for s in spots if not all(
        next(p for p in pts if p['id'] == i)['space'] == 'zone:olympus' for i in s['ids']))
    f['chests'] = sum(1 for p in pts if p['kind'] == 'chest')
    kinds = {}
    for p in pts:
        kinds[p['kind']] = kinds.get(p['kind'], 0) + 1
    f['point_kinds'] = kinds
    # roads
    f['links'] = {l['id']: round(link_length(l, P)) for l in D.LINKS}
    adj = graph(P)
    ring = ['room:fire_corner', 'room:north_crossing', 'room:north_toll', 'room:east_rest', 'room:air_corner',
            'room:mud_wharf', 'room:east_junction', 'room:earth_corner', 'room:south_rest', 'room:steam_post',
            'room:south_toll', 'room:water_corner', 'room:west_toll', 'room:rope_head', 'room:smoke_post',
            'room:fire_corner']
    f['rest_stop_legs'] = {f'{a.split(":")[1]} -> {b.split(":")[1]}': round(shortest(adj, a, b))
                           for a, b in zip(ring, ring[1:])}
    f['ring_length'] = round(sum(f['rest_stop_legs'].values()))
    f['quiet_stop_leg_max'] = max(f['rest_stop_legs'].values())
    f['boards'] = sum(1 for p in D.POINTS if p['kind'] == 'board')
    f['from_olympus'] = {k.split(':')[1]: round(shortest(adj, 'zone:olympus', k)) for k in
                         ('room:rope_head', 'room:fire_corner', 'room:air_corner', 'room:earth_corner',
                          'room:water_corner', 'room:roost', 'room:sky_lake')}
    f['from_rope'] = {k.split(':')[1]: round(shortest(adj, 'room:rope_head', k)) for k in
                      ('zone:olympus', 'room:fire_corner', 'room:water_corner')}
    f['road_links'] = dict(min=min(f['links'].values()), max=max(f['links'].values()))
    # D-58 D-1: the two spacing figures
    st = road_stretches(P)
    f['road_stretches'] = st
    f['road_longest_empty'] = max(v['longest_empty'] for v in st.values())
    worst = poi_nn()[-1]
    f['poi_nn_max'] = round(worst[0])
    f['poi_nn_max_spot'] = worst[1]
    f['spacing_limit'] = 8192
    f['heights'] = [min(s['floor'] for s in D.SPACES), max(s['floor'] for s in D.SPACES)]
    # fall zones: walkable share over each surface map
    zone_px = {}
    for fz in D.FALLS:
        x0, x1 = fz['x']
        y0, y1 = fz['y']
        c0, c1 = (x0 + D.HALF[0]) / RES, (x1 + D.HALF[0]) / RES
        r0, r1 = (D.HALF[1] - y1) / RES, (D.HALF[1] - y0) / RES
        zone_px[fz['key']] = round(float(walk[int(r0):int(r1), int(c0):int(c1)].sum() * px / 1e6), 1)
    f['walkable_by_fall_zone_millions'] = zone_px
    return f


# ------------------------------------------------------------------------------------------------ D-1 spacing
# D-58 D-1: along the ring and the inner road no stretch longer than 8,192 may pass without a group or a POI (boards
# and quiet stops do not count). The roads are walked as polylines through the islands' middles and the links' rim
# points (Olympus through its gates); a group or a POI spot counts for a road when it lies within ROAD_NEAR of it.
ROAD_NEAR = 2048          # or anywhere on (or belonging to) an island the road passes through


def point_in(p, poly):
    x, y = p
    c = False
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            c = not c
    return c
RING_ORDER = ['room:fire_corner', 'room:griffin_watch', 'room:north_crossing', 'room:north_toll', 'room:east_rest',
              'room:air_corner', 'room:mud_wharf', 'room:east_junction', 'room:earth_corner', 'room:south_rest',
              'room:steam_post', 'room:south_toll', 'room:skywaymen_camp', 'room:water_corner', 'room:west_toll',
              'room:rope_head', 'room:smoke_post', 'room:west_lookout', 'room:fire_corner']
INNER_ORDER = ['room:rope_head', 'room:broken_launch', 'zone:olympus', 'room:pyramid_cap', 'room:sky_lake',
               'room:east_junction']
CAUSEWAY_ORDER = ['room:north_crossing', 'zone:olympus']


def _link_between(a, b):
    for l in D.LINKS:
        if (l['a'], l['b']) in ((a, b), (b, a)):
            return l
    raise KeyError((a, b))


def road_path(order, P):
    """The walking line through `order`: each island's middle (Olympus: its gates), the link's rim points."""
    pts = []
    for a, b in zip(order, order[1:]):
        l = _link_between(a, b)
        pa, pb = link_ends(l, P)
        if l['a'] != a:
            pa, pb = pb, pa
        if not pts:
            pts.append(SPACE[a]['at'] if SPACE[a]['kind'] != 'town' else pa)
        if SPACE[a]['kind'] != 'town':
            pts.append(pa)
        pts.append(pb)
        if SPACE[b]['kind'] != 'town':
            pts.append(SPACE[b]['at'])
        else:
            pts.append(SPACE[b]['at'])
    return pts


def _project(path, p):
    """(arc length along the path, distance from it) of p's nearest point."""
    best = (1e18, 0.0)
    s0 = 0.0
    for a, b in zip(path, path[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (L * L)))
        d = math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
        if d < best[0]:
            best = (d, s0 + t * L)
        s0 += L
    return best[1], best[0]


def _length(path):
    return sum(dist(a, b) for a, b in zip(path, path[1:]))


def spacing_markers():
    """Every group and every POI spot (the census' spots; boards are not points, quiet stops have none)."""
    out = [(g['id'], g['at'], g['space']) for g in D.GROUPS]
    pts = {p['id']: p for p in all_points()}
    for s in census(list(pts.values())):
        out.append(('+'.join(s['ids']), s['at'], pts[s['ids'][0]]['space']))
    return out


def road_stretches(P):
    """For each road: its length, the markers along it, and the longest stretch with none (cyclic for the ring)."""
    res = {}
    marks = spacing_markers()
    for name, order, cyclic in (('ring', RING_ORDER, True), ('inner', INNER_ORDER, False),
                                ('north_causeway', CAUSEWAY_ORDER, False)):
        path = road_path(order, P)
        L = _length(path)
        isl = [P[o] for o in order]
        on = sorted((s, mid) for mid, p, sp in marks for s, d in [_project(path, p)]
                    if d <= ROAD_NEAR or sp in order or any(point_in(p, poly) for poly in isl))
        cuts = [s for s, _ in on]
        if cyclic:
            gaps = [(b - a, ia) for ia, (a, b) in enumerate(zip(cuts, cuts[1:] + [cuts[0] + L]))]
        else:
            ext = [0.0] + cuts + [L]
            gaps = [(b - a, ia - 1) for ia, (a, b) in enumerate(zip(ext, ext[1:]))]
        g, i = max(gaps)
        nxt = (i + 1) % len(on) if cyclic else i + 1
        res[name] = dict(length=round(L), markers=len(on), longest_empty=round(g),
                         between=[on[i][1] if 0 <= i < len(on) else 'start',
                                  on[nxt][1] if 0 <= nxt < len(on) else 'end'])
    return res


def poi_nn(points=None):
    pts = all_points() if points is None else points
    spots = census(pts)
    nn = []
    for i, s in enumerate(spots):
        d, j = min((dist(s['at'], t['at']), j) for j, t in enumerate(spots) if j != i)
        nn.append((d, '+'.join(s['ids']), '+'.join(spots[j]['ids'])))
    return sorted(nn)


# ------------------------------------------------------------------------------------------------ D-58: onto the clouds
SNAP_IN = 384             # a point the build stands on its island lies at least this far inside the review outline


def _rim_dist(poly, p):
    best = 1e18
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


def snap_onto_clouds():
    """L2 (D-58): the L1 put some points on or past their island's review outline (boards, merchants, stalls); the
    build stands each on its cloud, so each such point moves straight toward its island's middle until it is SNAP_IN
    inside. Corner tips are kept (the build runs a spit out to them). Each move is recorded in D.D58_MOVES."""
    P = polys()
    for items in (D.POINTS, D.ARRIVALS):
        for it in items:
            sp = it.get('space', '')
            if it.get('kind') == 'corner' or sp not in P or SPACE[sp]['kind'] == 'town':
                continue
            poly = P[sp]
            p = tuple(it['at'])
            if point_in(p, poly) and (_rim_dist(poly, p) >= SNAP_IN or it.get('kind') == 'return' or it.get('keep')):
                continue                       # corners.yml's returns stay where the planes send the party; `keep`:
                #                                the merchants at their barges' gangplanks (A6 s24)
            c = SPACE[sp]['at']
            q = p
            for k in range(1, 101):
                t = k / 100
                q = (p[0] + (c[0] - p[0]) * t, p[1] + (c[1] - p[1]) * t)
                if point_in(q, poly) and _rim_dist(poly, q) >= SNAP_IN:
                    break
            q = (int(round(q[0] / 32) * 32), int(round(q[1] / 32) * 32))
            D.D58_MOVES.append((it['id'], p, q, 'L2: onto its cloud, 384 inside the rim'))
            it['at'] = q


snap_onto_clouds()


def snap_olympus():
    """L2 (D-58): the L1 drew Olympus' gates, Lucio's dock and its jetty partly past the town cloud's outline, and two
    gates opened onto a house's corner. The build needs them on the cloud and open to a lane: the south-west gate at
    the back lane's foot (-7936, 4352), the north gate between the temple and the Spirit guild (-3072, 10560) with a
    768-wide causeway, the east gate 384 inside the rim on its causeway's line; Lucio's Dock (1.5 x 1.5 cells) beside
    the jetty, which runs from the cloud south-east through entrance:olympus_dock (-640, 3200) to the boat (1536,
    1792). Recorded in D.D58_MOVES."""
    P = polys()
    oly = P['zone:olympus']
    c = SPACE['zone:olympus']['at']
    fixed = {'south-west gate': (-7936, 4352), 'north gate': (-3072, 10560)}
    gates = []
    for name, g, f in D.OLYMPUS_GATES:
        l = next(x for x in D.LINKS if x.get('gate') == g)
        if name in fixed:
            ng = fixed[name]
        else:
            other = SPACE[l['a'] if l['b'] == 'zone:olympus' else l['b']]['at']
            rim = ray_exit(oly, c, (c[0] + (other[0] - c[0]) * 10, c[1] + (other[1] - c[1]) * 10))
            L = dist(rim, c)
            ng = (int(round((rim[0] - (rim[0] - c[0]) / L * 384) / 32) * 32),
                  int(round((rim[1] - (rim[1] - c[1]) / L * 384) / 32) * 32))
        if name == 'north gate':
            l['width'] = 768
        D.D58_MOVES.append((f'gate:{name}', g, ng, "L2: onto the town's cloud and open to a lane"))
        l['gate'] = ng
        gates.append((name, ng, f))
    D.OLYMPUS_GATES[:] = gates
    for i, b in enumerate(D.BUILDINGS):
        if b[0] == 'building:ol_dock':
            nb = (b[0], b[1], b[2], (-1152, 4224), b[4], (1.5, 1.5), b[6], b[7])
            D.D58_MOVES.append((b[0], b[3], nb[3], "L2: Lucio's Dock beside the jetty's root, on the cloud"))
            D.BUILDINGS[i] = nb
    D.D58_MOVES.append(('jetty', (D.OLYMPUS_DOCK_START, D.OLYMPUS_DOCK_END), ((-1984, 4064), (1536, 1792)),
                        "L2: the jetty from the cloud through entrance:olympus_dock to the boat"))
    D.OLYMPUS_DOCK_START = (-1984, 4064)
    D.OLYMPUS_DOCK_END = (1536, 1792)


snap_olympus()
