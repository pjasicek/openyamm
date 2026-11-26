#!/usr/bin/env python3
"""X8 Cloudreach: writes the L3 and L4 project files (lane A6 sub-agent, 2026-11-20).

One open-air room (room:air) from the safety floor at -6000 to the sky at 6000; its walls, floor and ceiling are sky
faces. Every cloud island is a hanging platform (`base`) with an irregular outline, cloud top and cloud sides, and
flared rock-and-cloud roots under it. Bridges and causeways are hanging slabs (`top_heights` + `thickness`) turned
along their line (`facing`), rope bridges with rope rails (raking beams). Positions follow L2's plan.yml (D-6.2: the
long bridge's spans 3,500-4,000).

    python3 level_generation/projects/xeen/x8/gen.py            # writes devdocs/xeen/briefs/x8/L3 and L4 (not their NOTES)
"""
import math
import random
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
BRIEF = ROOT / 'devdocs/xeen/briefs/x8'

FLOOR = -6000          # the safety floor (a fall that the poll misses ends here, and runs the same fall)
CEIL = 6000
SLAB = 256             # island slab thickness under its top
SINK = 8               # how far a block on an island or another block is sunk into it (no bottom on the walking plane)

CLOUD_TOP = {'texture': 'xccloud', 'size': [256, 256], 'scale': 2}
CLOUD_SIDE = {'texture': 'xccloudsd', 'size': [256, 256], 'scale': 2, 'uneven': True}
MARBLE = {'texture': '7tws1f', 'size': [128, 128]}
DECK = {'texture': 't66floor', 'size': [128, 128]}
ROPE = {'texture': 'hwm2rf', 'size': [128, 128]}
ROCK = {'texture': 'gcav1flr', 'size': [128, 128]}
STRAW = {'texture': 'gkp1flr', 'size': [128, 128]}
STONE = {'texture': 'hwm2wall', 'size': [128, 128]}
SLATE = {'texture': 'xtslate', 'size': [128, 128]}
SKY = {'texture': 'xccloud', 'size': [256, 256], 'scale': 32, 'sky': True}

# id: (centre, extent, floor, name)   -- L2 plan positions (D-6.2)
ISLANDS = {
    'witch_landing': ((11520, -5632), (4608, 3584), 0, "The Witch Clouds' landing"),
    'offering_terrace': ((6656, -1024), (4096, 3584), 128, 'The offering terrace'),
    'nest_spires': ((11776, 3072), (4096, 4608), 256, 'The nest spires'),
    'queens_eyrie': ((9728, 8960), (4608, 4096), 640, "The Harpy Queen's eyrie"),
    'explorers_rock': ((14080, 12288), (2560, 2560), 896, "The explorer's rock"),
    'witch_perch': ((10240, -10240), (3072, 2560), -128, "The witch's perch"),
    'half_way': ((0, 256), (2048, 1536), -64, 'The half-way cloud'),
    'stair_landing': ((-10240, -3072), (4608, 3584), 0, "The Stairway to Heaven's head"),
    'observatory_isle': ((-6656, 3072), (5120, 4608), 256, 'The observatory isle'),
    'golem_heights': ((-11264, 9216), (5120, 4096), 768, 'The golem heights'),
    'rhyme_garden': ((-13312, 1792), (3584, 3072), 128, 'The rhyme garden'),
    'windward_rock': ((-3584, 7424), (2048, 2048), -256, 'Windward rock'),
    'lantern_cloud': ((-8704, -8192), (3072, 2560), -128, 'The lantern cloud'),
}

# id: (from, to, kind, width, notes)   kind rope = planks with rope rails, sagging when long; ramp = cloud-stone
LINKS = [
    ('witch_causeway', 'witch_landing', 'offering_terrace', 'ramp', 768, 'cloud-stone causeway'),
    ('perch_bridge', 'witch_landing', 'witch_perch', 'rope', 256, 'short rope bridge'),
    ('spires_ramp', 'offering_terrace', 'nest_spires', 'ramp', 768, 'cloud-stone ramp'),
    ('eyrie_ramp', 'nest_spires', 'queens_eyrie', 'ramp', 512, 'cloud-stone ramp up to the eyrie'),
    ('explorer_bridge', 'queens_eyrie', 'explorers_rock', 'rope', 256, 'rope bridge over the void'),
    ('long_bridge_east', 'offering_terrace', 'half_way', 'rope', 384, 'the long rope bridge, east span'),
    ('long_bridge_west', 'half_way', 'observatory_isle', 'rope', 384, 'the long rope bridge, west span'),
    ('high_causeway', 'stair_landing', 'observatory_isle', 'ramp', 768, 'cloud-stone causeway'),
    ('garden_bridge', 'stair_landing', 'rhyme_garden', 'rope', 256, 'rope bridge'),
    ('garden_obs_bridge', 'rhyme_garden', 'observatory_isle', 'rope', 256,
     'rope bridge keeping the High Magic loop (D-6.2: in place of the garden ramp)'),
    ('heights_ramp', 'observatory_isle', 'golem_heights', 'ramp', 512,
     'the long ramp up to the golem heights, a dead end'),
    ('windward_bridge', 'observatory_isle', 'windward_rock', 'rope', 256, 'rope bridge down to windward rock'),
    ('lantern_bridge', 'stair_landing', 'lantern_cloud', 'rope', 256, 'rope bridge'),
]


def outline(cx, cy, ex, ey, seed, n=16):
    """An irregular cloud outline: an ellipse with smooth radial bumps (deterministic), counter-clockwise."""
    rnd = random.Random(seed)
    phases = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]
    amps = [0.07, 0.05, 0.03]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1.0 + sum(amp * math.sin(k * a + ph) for k, (amp, ph) in zip((2, 3, 5), zip(amps, phases)))
        r = min(r, 1.0)  # stays inside the plan extent
        pts.append([int(round(cx + 0.5 * ex * r * math.cos(a))), int(round(cy + 0.5 * ey * r * math.sin(a)))])
    return pts


def rim_point(poly, inside, outside):
    """Where the segment from `inside` to `outside` leaves the polygon."""
    best = None
    px, py = inside
    dx, dy = outside[0] - px, outside[1] - py
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % len(poly)]
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((ax - px) * ey - (ay - py) * ex) / den
        u = ((ax - px) * dy - (ay - py) * dx) / den
        if 0 <= t <= 1 and 0 <= u <= 1 and (best is None or t < best):
            best = t
    return (px + dx * best, py + dy * best)


def inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            c = not c
    return c


def landing_end(poly, centre, u, width, margin=24):
    """Where a deck of `width` leaving the island at `centre` along `u` is past the island across its whole width:
    the point on the centre line `margin` beyond the furthest bit of cloud under the deck."""
    ux, uy = u
    nx, ny = -uy, ux
    far = 0
    for k in range(9):
        o = (k / 8 - 0.5) * width
        t = 0
        while t < 20000:
            if inside(poly, centre[0] + ux * t + nx * o, centre[1] + uy * t + ny * o):
                far = max(far, t)
            t += 8
            if t > far + 2000:
                break
    far += margin
    return (centre[0] + ux * far, centre[1] + uy * far)


OUTLINES = {k: outline(c[0], c[1], e[0], e[1], seed=i * 7 + 3) for i, (k, (c, e, f, n)) in enumerate(ISLANDS.items())}


def platform_slab(pid, a, b, z0, z1, width, surface, top_surface, thickness, notes=None):
    """A hanging slab from point a (top z0) to b (top z1), `width` wide."""
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    facing = math.degrees(math.atan2(by - ay, bx - ax))
    low = min(z0, z1) - thickness
    base = low - FLOOR
    entry = {
        'id': pid,
        'at': [int(round((ax + bx) / 2)), int(round((ay + by) / 2))],
        'size': [int(round(length)), width],
        'facing': round(facing, 2),
        'base': int(base),
        'rise': int(min(z0, z1) - low),
        'top_heights': [int(z0 - low), int(z1 - low), int(z1 - low), int(z0 - low)],
        'thickness': thickness,
        'surface': surface,
        'top_surface': top_surface,
        'bottom_surface': surface,
    }
    if z0 == z1:
        # a level piece (a landing on an island): a block `thickness` deep under its top
        for k in ('top_heights', 'thickness'):
            entry.pop(k)
        entry['rise'] = thickness
    if notes:
        entry['notes'] = notes
    return entry


RAIL_POST = 16         # the posts a rope bridge's rails are tied to at both ends (F70)


def rail_posts(lid, a, b, u, width, end_a, end_b):
    """F70 (the player's pins 2026-11-26, X9 p5-p10 "the side rails stop in the air"; X8's bridges the same): a rope
    bridge's two rails are tied at each end to a post standing on the island just before the deck's end, its top 16
    over the rail (tools/xeen/check_beam_ends.py)."""
    ux, uy = u
    nx, ny = -uy * (width / 2 - 8), ux * (width / 2 - 8)
    out = []
    for tag, p, back, (iid, z) in (('a', a, -1, end_a), ('b', b, 1, end_b)):
        cx, cy = p[0] + back * ux * RAIL_POST / 2, p[1] + back * uy * RAIL_POST / 2
        for k, side in enumerate((1, -1)):
            x, y = cx + side * nx, cy + side * ny
            if not inside(OUTLINES[iid], x, y):
                raise SystemExit(f'{lid}: rail post {tag}{k + 1} at ({x:.0f}, {y:.0f}) is off its island {iid}')
            out.append({'id': f'platform:{lid}_post_{tag}{k + 1}', 'at': [int(round(x)), int(round(y))],
                        'size': [RAIL_POST, RAIL_POST], 'facing': round(math.degrees(math.atan2(uy, ux)), 2),
                        'base': z - SINK - FLOOR, 'rise': SINK + 8 + 88 + 16, 'surface': ROPE, 'top_surface': ROPE})
    return out


def build_rooms():
    platforms = []
    beams = []
    # ---- islands
    for i, (iid, ((cx, cy), (ex, ey), floor, name)) in enumerate(ISLANDS.items()):
        platforms.append({
            'id': f'platform:{iid}',
            'outline': OUTLINES[iid],
            'base': floor - SLAB - FLOOR,
            'rise': SLAB,
            'surface': CLOUD_SIDE,
            'top_surface': CLOUD_TOP,
            'bottom_surface': CLOUD_SIDE,
            'notes': f'{name}: a cloud island, its top at {floor}.',
        })
        # roots: two or three flared cloud masses hanging under the island
        rnd = random.Random(100 + i)
        roots = 3 if ex * ey > 12e6 else 2
        for r in range(roots):
            ox = rnd.uniform(-0.08, 0.08) * ex
            oy = rnd.uniform(-0.08, 0.08) * ey
            top_w = int(0.5 * ex) // 16 * 16
            top_d = int(0.5 * ey) // 16 * 16
            depth = int(rnd.uniform(900, 1700)) // 16 * 16
            platforms.append({
                'id': f'platform:{iid}_root{r + 1}',
                'at': [int(cx + ox), int(cy + oy)],
                'size': [max(160, top_w // 5), max(160, top_d // 5)],
                'top_size': [top_w, top_d],
                'base': floor - SLAB + 8 * (r + 1) - depth - FLOOR,
                'rise': depth,
                'surface': CLOUD_SIDE,
                'top_surface': CLOUD_SIDE,
                'bottom_surface': CLOUD_SIDE,
            })
    # ---- links
    for lid, frm, to, kind, width, notes in LINKS:
        ca, cb = ISLANDS[frm][0], ISLANDS[to][0]
        za, zb = ISLANDS[frm][2], ISLANDS[to][2]
        ra = rim_point(OUTLINES[frm], ca, cb)
        rb = rim_point(OUTLINES[to], cb, ca)
        # run 160 into each island so the deck's end lies over the cloud (8 above it: no faces in one plane)
        d = math.hypot(rb[0] - ra[0], rb[1] - ra[1])
        ux, uy = (rb[0] - ra[0]) / d, (rb[1] - ra[1]) / d
        a = (ra[0] - ux * 160, ra[1] - uy * 160)
        b = (rb[0] + ux * 160, rb[1] + uy * 160)
        za8, zb8 = za + 8, zb + 8
        # F62 (the player's pins 2026-11-25): a deck that sloped from its end on the cloud dipped under the cloud's
        # top before the rim (a sag, a lower or a higher island beyond) and came out again over the void. The deck
        # now lies level at the island's height until it is past the island across its whole width (the rim is
        # crooked), and slopes only over the void.
        pa = landing_end(OUTLINES[frm], ca, (ux, uy), width)
        pb = landing_end(OUTLINES[to], cb, (-ux, -uy), width)
        span = [(pa, pb, za8, zb8)]
        if kind != 'ramp' and d > 2000:
            # rope bridge: two spans meeting at a sag in the middle when longer than 2,000
            sag = min(160, int(d / 25))
            m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            zm = (za8 + zb8) / 2 - sag
            span = [(pa, m, za8, zm), (m, pb, zm, zb8)]
        segs = [(a, pa, za8, za8)] + span + [(pb, b, zb8, zb8)]
        if kind == 'ramp':
            for k, (p, q, z0, z1) in enumerate(segs):
                platforms.append(platform_slab(f'platform:{lid}' if k == 0 else f'platform:{lid}_{k + 1}', p, q,
                                               int(z0), int(z1), width, MARBLE, MARBLE, 96,
                                               f'link:{lid}: {notes}, {int(d)} long' if k == 0 else None))
            continue
        for k, (p, q, z0, z1) in enumerate(segs):
            pid = f'platform:{lid}' if k == 0 else f'platform:{lid}_{k + 1}'
            platforms.append(platform_slab(pid, p, q, int(z0), int(z1), width, ROPE, DECK, 24,
                                           f'link:{lid}: {notes}, {int(d)} long' if k == 0 else None))
            # rope rails 88 over the deck at both sides
            nx, ny = -uy * (width / 2 - 8), ux * (width / 2 - 8)
            for side in (1, -1):
                beams.append({
                    'path': [[int(round(p[0] + side * nx)), int(round(p[1] + side * ny))],
                             [int(round(q[0] + side * nx)), int(round(q[1] + side * ny))]],
                    'width': 8, 'depth': 8,
                    'bottom': int(z0 + 80), 'bottom_end': int(z1 + 80),
                    'surface': ROPE,
                })
        platforms += rail_posts(lid, a, b, (ux, uy), width, (frm, za), (to, zb))
    # ---- the two stairs out of the cloud sea (arrivals): steps hanging down from the south rim
    for iid, x in (('witch_landing', 11520), ('stair_landing', -10752)):
        cx, cy = ISLANDS[iid][0]
        rim = rim_point(OUTLINES[iid], (x, cy), (x, cy - 10000))
        for k in range(8):
            top = -32 * (k + 1)
            y = rim[1] + 96 - 192 * k - 96
            platforms.append({
                'id': f'platform:{iid}_step{k + 1}',
                'at': [x, int(y)],
                'size': [512, 192],
                'base': top - 32 - FLOOR,
                'rise': 32,
                'surface': MARBLE,
                'top_surface': MARBLE,
                'bottom_surface': MARBLE,
            })
        # F62 (X8 p3/p6, "is it intended that you can't go back to the tower?"): at the stair's foot the stair of
        # cloud the party came up by (XD-04's xwcloudst picture) stands across the way; a click on it goes back down
        # to the tower's roof (gen_objects.py evt:down_*). It also stops a walk off the last step into the sky.
        foot = rim[1] - 192 * 7
        platforms.append({
            'id': f'platform:{iid}_down',
            'at': [x, int(foot - 96 - 24)],
            'size': [512, 48],
            'base': -256 - SINK - FLOOR,
            'rise': 512 + SINK,
            'surface': {'texture': 'xwcloudst', 'size': [512, 512]},
            'end_surface': CLOUD_SIDE,      # the picture once on each face, the 48-wide ends plain cloud (feature_cut)
            'top_surface': CLOUD_TOP,
            'bottom_surface': CLOUD_SIDE,
            'notes': "The stair of cloud down to the tower the party came up from (a clicked exit).",
        })
    # ---- set pieces on the islands
    platforms += set_pieces()
    room = {
        'id': 'room:air',
        'space': 'void:cloud_sea',
        'name': 'Cloudreach',
        'outline': [[-20480, -15360], [19456, -15360], [19456, 17408], [-20480, 17408]],
        'floor': FLOOR,
        'ceiling': CEIL,
        'platforms': platforms,
        'beams': beams,
        'notes': ('The open air over Cloudside: one room from the safety floor at -6000 to the sky at 6000, every '
                  'wall, floor and ceiling face a sky face. The islands, bridges and causeways hang in it.'),
    }
    return {
        'format': 0,
        'themes': [{'id': 'theme:air', 'wall': SKY, 'floor': SKY, 'ceiling': SKY}],
        'defaults': {'theme': 'theme:air', 'ambient': 30},
        'rooms': [room],
    }


def on(iid, dx, dy):
    (cx, cy), _, floor, _ = ISLANDS[iid]
    return [cx + dx, cy + dy], floor


def block(pid, iid, dx, dy, size, rise, surface, top=None, top_size=None, extra_base=0, facing=None, notes=None):
    at, floor = on(iid, dx, dy)
    # F62 (X8 p8, "you get stuck here"): every block hangs from the room's floor at -6,000, so the studio draws its
    # bottom; a bottom lying on the cloud top is a ceiling at the party's feet, which wedged it at the block's foot.
    # Each block is sunk SINK into what it stands on (tools/xeen/check_floor_cross.py floor.lid).
    e = {'id': pid, 'at': at, 'size': size, 'base': floor + extra_base - SINK - FLOOR, 'rise': rise + SINK,
         'surface': surface}
    if top:
        e['top_surface'] = top
    if top_size:
        e['top_size'] = top_size
    if facing is not None:
        e['facing'] = facing
    if notes:
        e['notes'] = notes
    return e


def set_pieces():
    out = []
    # offering terrace: stepped twice (two tiers of 32)
    out.append(block('platform:terrace_tier1', 'offering_terrace', 512, 0, [2304, 2048], 32, CLOUD_SIDE, CLOUD_TOP,
                     notes='The terrace\'s first step.'))
    out.append(block('platform:terrace_tier2', 'offering_terrace', 768, 128, [1280, 1280], 32, CLOUD_SIDE, CLOUD_TOP,
                     extra_base=32, notes='The terrace\'s second step: the offering statues stand here.'))
    out.append(block('platform:offering_1', 'offering_terrace', 512, 512, [128, 128], 48, MARBLE, MARBLE,
                     extra_base=64, notes='Plinth of the first offering statue.'))
    out.append(block('platform:offering_2', 'offering_terrace', 1024, -256, [128, 128], 48, MARBLE, MARBLE,
                     extra_base=64, notes='Plinth of the second offering statue.'))
    # nest spires: three rock-and-cloud spires, nests at the feet of two
    for k, (dx, dy, h) in enumerate(((-768, 896, 1664), (896, 512, 1280), (128, -1024, 1024))):
        out.append(block(f'platform:spire_{k + 1}', 'nest_spires', dx, dy, [512, 448], h, ROCK, ROCK,
                         top_size=[64, 64], notes='A rock-and-cloud spire.'))
    out.append(block('platform:nest_1', 'nest_spires', -768, 256, [384, 384], 32, STRAW, STRAW,
                     notes='The first harpy nest (x8-sky.nest_1), at the foot of the tallest spire.'))
    out.append(block('platform:nest_2', 'nest_spires', 896, -192, [384, 384], 32, STRAW, STRAW,
                     notes='The second harpy nest (x8-sky.nest_2).'))
    out.append(block('platform:nest_3', 'witch_perch', 384, -256, [384, 384], 32, STRAW, STRAW,
                     notes="The nest on the witch's perch (x8-sky.nest_3)."))
    # the queen's eyrie: a ring of broken rock round the great nest
    ways = []
    for lid, frm, to, kind, width, notes in LINKS:
        if 'queens_eyrie' in (frm, to):
            other = ISLANDS[to if frm == 'queens_eyrie' else frm][0]
            c = ISLANDS['queens_eyrie'][0]
            ways.append(math.atan2(other[1] - c[1], other[0] - c[0]))
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.3
        if min(abs(math.remainder(a - w, 2 * math.pi)) for w in ways) < math.radians(28):
            continue  # the gaps the ramp and the explorer's bridge come in by
        r = 1500
        out.append(block(f'platform:eyrie_rock_{k + 1}', 'queens_eyrie', int(r * math.cos(a)), int(r * math.sin(a)),
                         [384, 288], 448 + 160 * (k % 3), ROCK, ROCK, top_size=[96, 64],
                         notes='Broken rock round the eyrie.'))
    out.append(block('platform:great_nest', 'queens_eyrie', 0, 256, [896, 896], 32, STRAW, STRAW,
                     notes="The Harpy Queen's great nest; her hoard lies in it."))
    # explorer's rock: a plinth for the statue
    out.append(block('platform:explorer_plinth', 'explorers_rock', 0, 128, [192, 192], 64, MARBLE, MARBLE,
                     notes="The explorer's statue's plinth."))
    # rhyme statues' plinths
    out.append(block('platform:rhyme_1_plinth', 'witch_perch', -512, 128, [160, 160], 48, MARBLE, MARBLE))
    out.append(block('platform:rhyme_2_plinth', 'rhyme_garden', 0, 0, [160, 160], 48, MARBLE, MARBLE))
    out.append(block('platform:rhyme_3_plinth', 'observatory_isle', 1408, -640, [160, 160], 48, MARBLE, MARBLE))
    # the observatory: a round tower, a split dome, a telescope raking out of the split
    (ox, oy), floor = on('observatory_isle', -512, 1152)
    ring = [[int(ox + 560 * math.cos(2 * math.pi * k / 12)), int(oy + 560 * math.sin(2 * math.pi * k / 12))]
            for k in range(12)]
    out.append({'id': 'platform:observatory', 'outline': ring, 'base': floor - SINK - FLOOR, 'rise': 768 + SINK,
                'surface': STONE, 'top_surface': STONE, 'notes': "The sorcerer's observatory: a round stone tower."})
    out.append({'id': 'platform:dome_w', 'at': [ox - 208, oy], 'size': [400, 960], 'top_size': [160, 640],
                'base': floor + 768 - SINK - FLOOR, 'rise': 288 + SINK, 'surface': SLATE, 'top_surface': SLATE,
                'notes': 'The west half of the split dome.'})
    out.append({'id': 'platform:dome_e', 'at': [ox + 208, oy], 'size': [400, 960], 'top_size': [160, 640],
                'base': floor + 768 - SINK - FLOOR, 'rise': 288 + SINK, 'surface': SLATE, 'top_surface': SLATE,
                'notes': 'The east half of the split dome; the telescope looks out of the split between them.'})
    out.append({'id': 'platform:observatory_porch', 'at': [ox, oy - 704], 'size': [768, 256],
                'base': floor - SINK - FLOOR, 'rise': 16 + SINK, 'surface': MARBLE, 'top_surface': MARBLE,
                'notes': "The observatory's porch: the sorcerer's chest and the eyepiece of his telescope."})
    out.append({'id': 'platform:telescope', 'at': [ox + 256, oy - 704], 'size': [96, 96],
                'base': floor + 16 - SINK - FLOOR, 'rise': 96 + SINK, 'surface': {'texture': 'xngong5', 'size': [128, 32]},
                'top_surface': {'texture': 'xngong5', 'size': [128, 32]},  # a bronze tile (texture fit: not the gong)
                'notes': "The brass eyepiece of the sorcerer's telescope (a clicked block)."})
    # golem heights: lumps of cloud
    for k, (dx, dy, w, d, h) in enumerate(((-1280, 768, 896, 768, 96), (1024, 1024, 768, 640, 128),
                                          (-256, -896, 640, 640, 64))):
        out.append(block(f'platform:heights_lump_{k + 1}', 'golem_heights', dx, dy, [w, d], h, CLOUD_SIDE,
                         CLOUD_TOP, top_size=[w - 192, d - 192], notes='A lump of cloud on the heights.'))
    # rhyme garden: wind-bell posts
    for k in range(6):
        a = 2 * math.pi * k / 6
        out.append(block(f'platform:bell_post_{k + 1}', 'rhyme_garden', int(900 * math.cos(a)),
                         int(800 * math.sin(a)), [24, 24], 224, ROPE, ROPE, notes='A post hung with wind bells.'))
    return out


if __name__ == '__main__':
    rooms = build_rooms()
    for level in ('L3', 'L4'):
        (BRIEF / level).mkdir(parents=True, exist_ok=True)
        with open(BRIEF / level / 'rooms.yml', 'w') as f:
            yaml.safe_dump(rooms, f, sort_keys=False, width=120)
    # L3 is the shell: rooms and the start; L4 adds objects and wiring (gen_objects.py)
    import gen_objects
    with open(BRIEF / 'L3' / 'objects.yml', 'w') as f:
        yaml.safe_dump({'format': 1, 'start': gen_objects.objects()['start']}, f, sort_keys=False, width=120)
    print('platforms', len(rooms['rooms'][0]['platforms']), 'beams', len(rooms['rooms'][0]['beams']))
    for lid, frm, to, kind, width, notes in LINKS:
        ca, cb = ISLANDS[frm][0], ISLANDS[to][0]
        ra = rim_point(OUTLINES[frm], ca, cb)
        rb = rim_point(OUTLINES[to], cb, ca)
        print(f'{lid:20s} {kind:5s} {int(math.hypot(rb[0] - ra[0], rb[1] - ra[1])):6d} rim to rim, '
              f'rise {ISLANDS[to][2] - ISLANDS[frm][2]}')
