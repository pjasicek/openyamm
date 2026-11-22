"""X1 second pass: what makes the town lived in (REVIEW.md points 1, 4, 5, 7) and the hard check that no road or path
runs under a building (the user's walk: a road under a house at -2905.9, 4519.1). Imported by gen.py."""
import math
import town as T

COBBLE = [T.MAIN, T.NORTH_ST, T.SOUTH_ST, T.GUILD_LANE, T.WEST_ROAD, T.ORCHARD_ROAD, T.SOUTH_ROAD, T.TOAD_LANE,
          T.NORTH_ROAD, T.SMITH_LANE, T.BANK_LANE, T.INN_LANE]
DIRT = [[[80, 74.5], [86, 79], [88, 81.5]], [[62, 73], [52, 78], [42, 84], [34, 92], [34.5, 97.5], [31, 97.5]]]
TOWN_POLY = [[31, 33], [71, 33], [71, 66], [31, 66]]   # with the fringe homes outside the gates

def wall_polys():
    """The town wall's runs, towers and gatehouses as polygons in cells, for the checks."""
    out = []
    for s in T.wall_structures():
        if s['kind'] == 'wall':
            (ax, ay), (bx, by) = s['line']
            L = math.hypot(bx - ax, by - ay)
            hx, hy = -(by - ay) / L * s['thickness'] / 1024.0, (bx - ax) / L * s['thickness'] / 1024.0
            out.append([(ax + hx, ay + hy), (bx + hx, by + hy), (bx - hx, by - hy), (ax - hx, ay - hy)])
            continue
        x, y = s['at']
        w, h = s['size']
        cx, cy = x + w / 2, y + h / 2
        out.append([T.rot(px, py, cx, cy, s.get('turn', 0)) for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))])
    return out

def dress(footprints, doors_out, extra_polys):
    """footprints: (building, index, polygon); doors_out: (building, index, door cell, cell 0.9 out).
    extra_polys: polygons of other structures (stalls, sheds, wells) that paths must also miss.
    Returns ground zones, scatter entries and a report."""
    report = []
    ground, scatter = [], []
    polys = [p for _, _, p in footprints]
    # --- the hard check: no cobbled road within 0.55 of a building (the tiles are a cell wide on the line)
    bad = []
    for b, ix, poly in footprints:
        for line in COBBLE + DIRT:
            if T.line_hits_poly(line, poly, 0.55):
                bad.append('road under or against a building: %s#%s by %s' % (b, ix, line[:3]))
    for line in T.LANES:
        for b, ix, poly in footprints:
            if T.line_hits_poly(line, poly, 0.3):
                bad.append('lane under a building: %s#%s by %s' % (b, ix, line))
    if bad:
        raise SystemExit('\n'.join(bad))
    # --- a path from every door to a road: an apron of dirt at the door and a strip to the nearest road or lane
    ways = COBBLE + T.LANES
    for (b, ix, dc, out) in doors_out:
        inside_town = T.inside(dc, TOWN_POLY) or b in ('building:myra_hut', 'building:valia_cottage',
                                                         'building:hamlet_houses', 'building:oslo_hut',
                                                         'building:celia_hut')
        if not inside_town:
            continue
        ax, ay = (dc[0] + out[0]) / 2, (dc[1] + out[1]) / 2
        if T.nearest_on(COBBLE, out)[0] < 1.0:
            continue      # the street's own dirt band is the door's apron
        # pass four (REVIEW_PASS3 7): no square of soil at each door (half the town floor was brown rectangles);
        # Harmondale's dirt is the trodden path only, so a door keeps just its path to the road.
        d, q = T.nearest_on(ways + DIRT, out)
        if d > 0.6:
            h = lambda v: round(v * 2) / 2.0
            spur = [[h(out[0]), h(out[1])], [h(q[0]), h(q[1])]]
            if spur[0] == spur[1]:
                continue
            for b2, ix2, poly in footprints:
                if (b2, ix2) != (b, ix) and T.line_hits_poly(spur, poly, 0.15):
                    raise SystemExit('path from %s#%s to its road crosses %s#%s' % (b, ix, b2, ix2))
            for poly in extra_polys:
                if T.line_hits_poly(spur, poly, 0.1):
                    raise SystemExit('path from %s#%s to its road crosses a structure' % (b, ix))
            ground.append({'material': 'soil', 'line': spur, 'width': 2,
                           'notes': 'path to the door of %s%s' % (b, '#%d' % ix if ix else '')})
            report.append((b, ix, round(d, 2)))
    for line in T.LANES:
        ground.append({'material': 'soil', 'line': line, 'width': 2, 'notes': 'a lane behind the shops'})
    # --- one tree per house, in its yard: the first place round it clear of buildings, roads and walls
    walls = wall_polys()
    taken = []
    kinds = ['7tree16', '7tree13', 'tree37', '7tree16', '7tree13']
    k = 0
    for b, ix, poly in footprints:
        cx = sum(p[0] for p in poly) / 4
        cy = sum(p[1] for p in poly) / 4
        if not T.inside((cx, cy), TOWN_POLY):
            continue
        r = max(math.hypot(p[0] - cx, p[1] - cy) for p in poly) + 0.55
        for a in range(0, 360, 30):
            ang = math.radians(a + 200)
            p = (cx + r * math.cos(ang), cy + r * math.sin(ang))
            ok = all(not T.inside(p, q) and min(T.seg_dist(p, q[i], q[(i + 1) % len(q)]) for i in range(len(q))) > 0.45
                     for q in polys + walls + extra_polys)
            ok = ok and all(min(T.seg_dist(p, a1, b1) for a1, b1 in zip(l, l[1:])) > 0.8 for l in COBBLE + T.LANES)
            ok = ok and all(math.hypot(p[0] - t[0], p[1] - t[1]) > 1.2 for t in taken)
            ok = ok and all(T.seg_dist(p, d[2], d[3]) > 0.7 for d in doors_out)
            if ok:
                taken.append(p)
                scatter.append({'id': 'scatter:town_trees', 'decoration': kinds[k % len(kinds)], 'count': 1,
                                'circle': {'at': [round(p[0], 2), round(p[1], 2)], 'r': 0.25}})
                k += 1
                break
    # --- flower strips under a side wall of each house in town (rebase 2026-11-20: 2 a strip, were 4; X1-8)
    flowers = ['flower01', 'flower06', 'flower02', 'flower01', 'flower06', 'flower02']
    for i, (b, ix, poly) in enumerate(footprints):
        cx = sum(p[0] for p in poly) / 4
        cy = sum(p[1] for p in poly) / 4
        if not T.inside((cx, cy), TOWN_POLY):
            continue
        # the wall from corner 1 to 2 or 3 to 0 (a side wall when the front is n or s): offset outward
        for (p, q) in ((poly[1], poly[2]), (poly[3], poly[0]))[(i % 2):(i % 2) + 1]:
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            ox, oy = mx - cx, my - cy
            L = math.hypot(ox, oy)
            ox, oy = ox / L * 0.42, oy / L * 0.42
            line = [[round(p[0] + ox, 2), round(p[1] + oy, 2)], [round(q[0] + ox, 2), round(q[1] + oy, 2)]]
            # shorten by a fifth at each end
            line = [[round(line[0][0] + (line[1][0] - line[0][0]) * 0.2, 2), round(line[0][1] + (line[1][1] - line[0][1]) * 0.2, 2)],
                    [round(line[0][0] + (line[1][0] - line[0][0]) * 0.8, 2), round(line[0][1] + (line[1][1] - line[0][1]) * 0.8, 2)]]
            clear = all(min(T.seg_dist(e, a1, b1) for a1, b1 in zip(l, l[1:])) > 0.7 for l in COBBLE + T.LANES
                        for e in line)
            clear = clear and all(not T.inside(e, q2) for e in line for q2 in polys + walls + extra_polys)
            if clear:
                scatter.append({'id': 'scatter:town_flowers', 'decoration': flowers[i % len(flowers)], 'count': 2,
                                'line': line})
    return ground, scatter, report

# ---------------------------------------------------------------------------------------------------------------
# Tree spacing (measured against shipped maps: Deyja, Tularean Forest, Harmondale, Shadowspire, Murmurwoods, Mire of
# the Damned). The studio's `clusters` packs a clump's trees at its `spacing` (half a cell) and leaves bare ground
# between clumps; its `spacing` holds only inside one entry, so two kinds overlap. Here every tree of a stand is
# placed by one dart throw over all its kinds: a least distance between any two trees, a small share of close pairs,
# kinds drawn at random per tree (mixed, not in kind patches) and fewer trees toward the stand's rim.
# ---------------------------------------------------------------------------------------------------------------
import random

def poly_area(poly):
    return abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly)))) / 2.0

def edge_dist(p, poly):
    return min(T.seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))

def even_stand(sid, poly, kinds, per_cell, d_min, d_pair=None, pair_share=0.0, edge=3.0, edge_keep=0.35,
               avoid=None, taken=None, seed=1, count=None):
    """Trees of `kinds` ({decoration: weight}) over `poly` at `per_cell` trees a cell (or `count`), each at least
    `d_min` cells from every other (a `pair_share` of them may stand `d_pair` from one), thinning over the last `edge`
    cells to `edge_keep` of the density at the rim. `avoid(p)` refuses a place; `taken` holds trees already placed
    (other stands), which this stand keeps clear of too. Returns scatter entries, one tree each."""
    rnd = random.Random(seed)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    want = count if count is not None else int(round(per_cell * poly_area(poly)))
    names = list(kinds)
    weights = [kinds[k] for k in names]
    pts = []
    taken = taken if taken is not None else []
    tries = 0
    while len(pts) < want and tries < want * 400:
        tries += 1
        p = (rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys)))
        if not T.inside(p, poly):
            continue
        e = edge_dist(p, poly)
        if e < edge and rnd.random() > edge_keep + (1 - edge_keep) * e / edge:
            continue
        if avoid and avoid(p):
            continue
        dmin = d_pair if (d_pair and rnd.random() < pair_share) else d_min
        if any(math.hypot(p[0] - q[0], p[1] - q[1]) < dmin for q in pts + taken):
            continue
        pts.append(p)
    taken.extend(pts)
    out = []
    for p in pts:
        k = rnd.choices(names, weights)[0]
        out.append({'id': sid, 'decoration': k, 'count': 1,
                    'circle': {'at': [round(p[0], 3), round(p[1], 3)], 'r': 0.1}})
    return out

def near_lines(lines, d):
    def f(p):
        return any(min(T.seg_dist(p, a, b) for a, b in zip(l, l[1:])) < d for l in lines)
    return f
