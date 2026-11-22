"""X5 tools: house shapes, geometry helpers and the even tree stand, copied from X2's kit.py (itself from X1) so
that X5 imports nothing of another map. Coordinates: cells [x, y], x east, y south."""
import math
import random
# ---------------------------------------------------------------------------------------------------------------
# House shapes. Local frame: u along the front (0..F map units), v from the front wall back (0..D). Turned into the
# plot's frame by its facing (a plot's parts are named before its `turn`).
# ---------------------------------------------------------------------------------------------------------------
ALONG = {'n': 'ew', 's': 'ew', 'e': 'ns', 'w': 'ns'}
ACROSS = {'n': 'ns', 's': 'ns', 'e': 'ew', 'w': 'ew'}

def plot_extent(facing, fp):
    f, d = fp[0] * 512, fp[1] * 512
    return (f, d) if facing in ('n', 's') else (d, f)

def rect(facing, fp, u0, v0, du, dv):
    W, H = plot_extent(facing, fp)
    if facing == 's':
        return [u0, H - v0 - dv], [du, dv]
    if facing == 'n':
        return [u0, v0], [du, dv]
    if facing == 'e':
        return [W - v0 - dv, u0], [dv, du]
    return [v0, u0], [dv, du]

def centre(facing, fp, uc, vc):
    W, H = plot_extent(facing, fp)
    return {'s': [uc, H - vc], 'n': [uc, vc], 'e': [W - vc, uc], 'w': [vc, uc]}[facing]

def box(pid, facing, fp, u0, v0, du, dv, **kw):
    at, size = rect(facing, fp, u0, v0, du, dv)
    p = {'id': pid, 'at': [round(a) for a in at], 'size': [round(s) for s in size]}
    p.update(kw)
    return p

THATCH = 'hhp2rf'
ROOFS = {'plaster': 'hhm2rf', 'timber': 'hhm1rf', 'grey': 'hhm3rf', 'poor': 'hhp2rf', 'rich': '7hhr1rf',
         'stone': '7hhr1rf'}

def shape(kind, facing, fp, kit, sign=None, roof_tex=None):
    """The parts (and the door) of one house of `kind` on a plot of `fp` cells facing `facing`."""
    F, D = fp[0] * 512, fp[1] * 512
    tex = {'roof': roof_tex} if roof_tex else None
    parts = []
    door = {'part': 'body', 'wall': facing}
    def signs(wall_len):
        if not sign:
            return {}
        # texture fit (2026-11-20): the board at its picture's own size, so the picture shows once (MM8's shop signs
        # sg* 64 x 64, the world's xl* boards 128 x 64)
        size = [128, 64] if sign.startswith('xl') else [64, 64]
        return {'signs': [{'wall': facing, 'bay': 0, 'texture': sign, 'hang': True, 'size': size, 'out': 48,
                           'bottom': 120}]}
    if kind == 'cottage':
        # a small house with a hip roof (Harmondale's 1x1 cottages, Ravenshore's stone huts)
        b = box('body', facing, fp, 64, 64, F - 128, D - 128, roof='hip', roof_pitch=38)
        b.update(signs(F - 128))   # A4 2026-11-22: a cottage hangs its sign too (it was dropped)
        if tex: b['textures'] = dict(tex)
        parts.append(b)
    elif kind == 'gable_porch':
        # gable end to the street, a porch on posts over the door
        b = box('body', facing, fp, 64, 160, F - 128, D - 224, roof='gable', ridge_along=ACROSS[facing],
                roof_pitch=48, porches=[{'wall': facing, 'depth': 128, 'posts': 24, 'height': 224, 'floor': 16}])
        b.update(signs(F - 128))
        if tex: b['textures'] = dict(tex)
        parts.append(b)
    elif kind == 'L':
        # a front range along the street and a wing back from one end
        a = box('body', facing, fp, 48, 48, F - 96, int(D * 0.5), roof='gable', ridge_along=ALONG[facing],
                roof_pitch=45)
        a.update(signs(F - 96))
        w = box('wing', facing, fp, int(F * 0.5), int(D * 0.5) - 32, int(F * 0.5) - 112, int(D * 0.5) - 32,
                roof='gable', ridge_along=ACROSS[facing], roof_pitch=45)
        if tex:
            a['textures'] = dict(tex); w['textures'] = dict(tex)
        parts += [a, w]
    elif kind == 'jetty':
        # a shop of two storeys, the upper one reaching out over the lower
        a = box('body', facing, fp, 96, 112, F - 192, D - 192, roof='none')
        a.update(signs(F - 192))
        u = box('upper', facing, fp, 48, 64, F - 96, D - 112, bottom=256, wall_height=256, roof='gable',
                ridge_along=ALONG[facing], roof_pitch=50)
        if tex:
            a['textures'] = dict(tex); u['textures'] = dict(tex)
        parts += [a, u]
    elif kind == 'tower_house':
        # a round tower with a cone roof behind a small gabled entry
        r = int(min(F, D) * 0.34)
        c = centre(facing, fp, F / 2, D - r - 48)
        t = {'id': 'tower', 'shape': 'round', 'at': [round(c[0]), round(c[1])], 'radius': r, 'sides': 10,
             'wall_height': 512, 'roof': 'cone', 'roof_pitch': 62, 'windows': 'alternate'}
        b = box('body', facing, fp, int(F * 0.22), 48, int(F * 0.56), int(D * 0.42), roof='gable',
                ridge_along=ACROSS[facing], roof_pitch=48)
        b.update(signs(int(F * 0.56)))
        if tex:
            t['textures'] = dict(tex); b['textures'] = dict(tex)
        parts += [t, b]
    elif kind == 'barn':
        # a long low barn with a lean-to along one side
        b = box('body', facing, fp, 48, 48, F - 96, int(D * 0.62), roof='gable', ridge_along=ALONG[facing],
                roof_pitch=40)
        b.update(signs(F - 96))
        l = box('shed', facing, fp, 96, int(D * 0.62) + 48 - 16, F - 256, int(D * 0.38) - 64, roof='lean_to',
                wall_height=192, windows='none')
        if tex:
            b['textures'] = dict(tex); l['textures'] = dict(tex)
        parts += [b, l]
    elif kind == 'forge':
        # stone smithy: a gabled shop, a chimney through its roof, and against its side wall a low open workshop
        # (A6 fix, 2026-11-20: the old shed's lean-to rose from the front to the back over its depth and stood as a
        # tall narrow slab on two poles): one slope falling away from the house, its high side under the house's
        # eaves (176 + 64 = 240 < 256), on four posts, a workbench along the house wall and a crate in its back corner
        bw = int(F * 0.62)
        b = box('body', facing, fp, 48, 96, bw, D - 160, roof='gable', ridge_along=ACROSS[facing],
                roof_pitch=45)
        b.update(signs(bw))
        ch = box('chimney', facing, fp, 48 + bw - 112, D - 240, 96, 96, wall_height=512, roof='flat',
                 windows='none')
        u0, v0 = 48 + bw + 16, 160
        du, dv = F - 24 - u0, D - 320
        away = {'s': 'e', 'n': 'e', 'e': 's', 'w': 's'}[facing]       # +u in the map: the side away from the house
        sh = box('shed', facing, fp, u0, v0, du, dv, roof='lean_to', roof_low=away, roof_height=64,
                 wall_height=176, posts=16, windows='none')
        bench = box('bench', facing, fp, u0 + 24, v0 + 64, 96, min(256, dv - 176), wall_height=96, roof='flat',
                    windows='none', textures={'wall': 't06a10', 'roof': '7trimda'})
        crate = box('crate', facing, fp, u0 + du - 136, v0 + dv - 136, 96, 96, wall_height=96, roof='flat',
                    windows='none', textures={'wall': '7trimda', 'roof': '7trimda'})
        parts += [b, ch, sh, bench, crate]
    elif kind == 'round_hut':
        if sign:
            raise ValueError('a round hut has no flat wall for its sign %s: give the house another shape' % sign)
        r = int(min(F, D) * 0.42)
        parts.append({'id': 'body', 'shape': 'round', 'at': [F // 2, D // 2], 'radius': r, 'sides': 10,
                      'wall_height': 256, 'roof': 'cone', 'tiers': [[48, 128], [80, 96], [96, 64]],
                      'textures': {'roof': roof_tex or THATCH}})
        door = {'part': 'body'}
    else:
        raise ValueError(kind)
    return parts, door

TURN_OF = {'s': 0, 'w': 90, 'n': 180, 'e': 270}
def rot(px, py, cx, cy, deg):
    a = math.radians(deg)            # clockwise seen from above; y runs south, so this is the usual rotation
    dx, dy = px - cx, py - cy
    return (cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a))

def footprint(x, y, facing, fp, turn):
    W, H = plot_extent(facing, fp)
    w, h = W / 512.0, H / 512.0
    cx, cy = x + w / 2, y + h / 2
    return [rot(px, py, cx, cy, turn) for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]

def door_cell(x, y, facing, fp, turn, out=0.0):
    W, H = plot_extent(facing, fp)
    w, h = W / 512.0, H / 512.0
    px, py = {'s': (x + w / 2, y + h + out), 'n': (x + w / 2, y - out), 'e': (x + w + out, y + h / 2),
              'w': (x - out, y + h / 2)}[facing]
    return rot(px, py, x + w / 2, y + h / 2, turn)

def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)

def inside(p, poly):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c

def line_hits_poly(line, poly, clearance):
    """Does a polyline come within `clearance` cells of a polygon (or run through it)? Pass three: plots stand on half
    cells, so a building may stand against an axis-aligned road's cell (0.5 from its line); diagonals keep `clearance`."""
    base = clearance
    for a, b in zip(line, line[1:]):
        clearance = min(base, 0.5) if (a[0] == b[0] or a[1] == b[1]) else base
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            if min(seg_dist(p, a, b), seg_dist(q, a, b), seg_dist(a, p, q), seg_dist(b, p, q)) < clearance:
                return True
        steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) * 4))
        for k in range(steps + 1):
            t = k / float(steps)
            if inside((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), poly):
                return True
    return False

def nearest_on(lines, p):
    best = None
    for line in lines:
        for a, b in zip(line, line[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = dx * dx + dy * dy
            t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
            q = (a[0] + t * dx, a[1] + t * dy)
            d = math.hypot(p[0] - q[0], p[1] - q[1])
            if best is None or d < best[0]:
                best = (d, q)
    return best

def well(wid, at, roofed=False, title='Well'):
    w = {'id': wid, 'kind': 'well', 'at': list(at), 'title': title, 'frame': {'height': 200}}
    if roofed:
        w['frame'] = {'height': 224, 'roof': 'gable', 'roof_height': 64}
    w['effects'] = [{'text': 'Cool water.'}]
    return w

def stall(sid, at, turn, kit='timber', roof_tex=None):
    s = {'id': sid, 'kind': 'building', 'at': list(at), 'size': [1, 0.75], 'turn': turn, 'kit': kit, 'door': 'none',
         'title': 'Market stall',
         'parts': [{'id': 'stall', 'at': [64, 64], 'size': [384, 256], 'wall_height': 224, 'posts': 24, 'sill': 80,
                    'sill_walls': ['n', 'e', 'w'], 'roof': 'hip', 'roof_pitch': 30, 'windows': 'none'}]}
    # pass four (REVIEW_PASS3 4): a low hip roof on the posts; the lean-to's high back wall read as a broken building
    if roof_tex:
        s['parts'][0]['textures'] = {'roof': roof_tex}
    return s

def shed(sid, at, size_cells, turn, kit='poor', open_=False, roof='lean_to', title='Shed'):
    W, H = size_cells[0] * 512, size_cells[1] * 512
    p = {'id': 'shed', 'at': [48, 48], 'size': [W - 96, H - 96], 'wall_height': 256, 'roof': roof,
         'windows': 'none'}
    if open_:
        p['posts'] = 24
    return {'id': sid, 'kind': 'building', 'at': list(at), 'size': list(size_cells), 'turn': turn, 'kit': kit,
            'door': 'none', 'title': title, 'parts': [p]}

def fence(fid, line, closed=False):
    f = {'id': fid, 'kind': 'fence', 'line': [list(p) for p in line],
         'notes': 'A fence round a garden or pen (pass three: the fence word, posts and rails following the ground).'}
    if closed:
        f['closed'] = True
    return f
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
        if not inside(p, poly):
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
        return any(min(seg_dist(p, a, b) for a, b in zip(l, l[1:])) < d for l in lines)
    return f
# ---------------------------------------------------------------------------------------------------------------
import random

def poly_area(poly):
    return abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly)))) / 2.0

def edge_dist(p, poly):
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))

