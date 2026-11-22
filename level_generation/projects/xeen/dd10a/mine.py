"""The Gemstone Mines (DD-10A, B, C): what the three pockets share, so they read as one mine (D-27).

Each pocket's own generator (output/studio_cal/dd10<x>/tools/gen.py) does

    import sys; sys.path.insert(0, 'level_generation/projects/xeen/dd10a')
    from mine import *

and builds its rooms, objects and events with these helpers: the 7d35 themes and surfaces, timber sets, ore carts and
rails, the veins (a wall panel and an event per vein, a map variable each), the pocket's refill on entry, the false
vein (B, C), the exit onto the outdoor map, the YAML writers. Lane A8 (agent:xeen-a8-dd10a), phase 3, 2026-11-20.

Textures (D-27, `dungeon_families.yml` mines): MM7 Nighon Tunnels 7d35 (cwb1 rock walls and roofs, cfb1 floors,
trim9_32 / trim9_32a timber, 7wtrtyl water), the world's ore cart (xncartsd, xnrustirn) and web (xnweb), A6's four vein
pictures on cwb1 (xdvruby, xdvemrld: A; xdvsaph: B; xdvdiam: C), MM6 Gharik's Forge 6d18 lava for C's seam (6voltyl,
vlcwl3a).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import yaml

R = _REPO_ROOT


class Flow(list):
    pass


def _flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.add_representer(Flow, _flow_rep)


def F(*a):
    return Flow(a)


def S(texture, w, h, scale=None, **kw):
    d = {'texture': texture, 'size': F(w, h)}
    if scale:
        d['scale'] = scale
    d.update(kw)
    return d


def dump(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=120)


def rect(x0, y0, x1, y1):
    return [F(x0, y0), F(x1, y0), F(x1, y1), F(x0, y1)]


# ---------------------------------------------------------------------------------------------------------------------
# Quest numbers (A3's q-d7, quest_hooks.yml) and items

QD7 = {'refill_a': 113141, 'refill_b': 113142, 'refill_c': 113143, 'dug': 113144}
ROCKS = {'ruby': 12357, 'emerald': 12358, 'sapphire': 12359, 'diamond': 12360}
GEM_NAMES = {'ruby': 'Ruby', 'emerald': 'Emerald', 'sapphire': 'Sapphire', 'diamond': 'Diamond'}
VEIN_TEXTURES = {'ruby': 'xdvruby', 'emerald': 'xdvemrld', 'sapphire': 'xdvsaph', 'diamond': 'xdvdiam'}
SPENT_LINE = "You've got all this vein has to offer."   # dark/aaze0039:10
MUSIC = 18

# ---------------------------------------------------------------------------------------------------------------------
# Surfaces and themes (7d35)

ROCK = S('cwb1', 128, 256)
FLOOR = S('cfb1', 128, 128)
TIMBER = S('trim9_32', 32, 64)          # upright grain: posts, door planks
TIMBER_H = S('trim9_32a', 64, 32)       # level grain: caps, lagging, cart beds
# Each texture at its own size, enlarged by scale (merge point 17: one size per texture per map).
LAGGING = S('trim9_32a', 64, 32, scale=2)
DOOR_PLANKS = S('trim9_32', 32, 64, scale=2)
# F12 (A8 session 26): the doors' leaves show a plank door picture once (MM6's rough plank door with its iron handle),
# not the timber strip DOOR_PLANKS tiled across; DOOR_PLANKS stays the themes' door default.
MINE_DOOR = S('d2smldor', 128, 256, fit=True)
WATER = S('7wtrtyl', 128, 128, liquid='water')
# The cart side (200 x 88) shows the picture once: laid at scale 1.5 (texture fit, session 7; a platform's side does
# not take `fit`, and a declared size does not change how many texels a unit spans).
CART_SIDE = S('xncartsd', 128, 64, scale=1.5)
IRON = S('xnrustirn', 64, 64)
WEB = S('xnweb', 128, 128)
LAVA = S('6voltyl', 128, 128, liquid='lava')
LAVA_ROCK = S('vlcwl3a', 128, 256)


def vein_surface(gem):
    return S(VEIN_TEXTURES[gem], 128, 256, fit=True)


THEMES = [
    {'id': 'theme:rock', 'wall': ROCK, 'floor': FLOOR, 'ceiling': ROCK, 'reveal': ROCK, 'door': DOOR_PLANKS,
     'notes': "The mine's raw rock: MM7 Nighon Tunnels (7d35) cwb1 on walls and roofs, cfb1 underfoot."},
    {'id': 'theme:timbered', 'wall': ROCK, 'floor': FLOOR, 'ceiling': LAGGING, 'reveal': TIMBER, 'door': DOOR_PLANKS,
     'notes': "Timbered drifts: 7d35's cwb1 rock under plank lagging (trim9_32a), timber jambs (trim9_32)."},
]


# ---------------------------------------------------------------------------------------------------------------------
# Timber sets, carts, rails (platforms and beams of a room)


def timber_set(axis, at, lo, hi, ceiling, floor=0, post=24, cap=24):
    """Two posts against the walls and a cap beam across a drift. axis 'x': the drift runs along x and the set stands
    across it at x = at, between the walls y = lo and y = hi; axis 'y': the drift runs along y, the set at y = at
    between x = lo and x = hi. Returns (platforms, beams)."""
    top = ceiling - 8 - cap
    rise = top - floor
    h = post // 2
    if axis == 'y':
        p = [F(lo + h, at), F(hi - h, at)]
        path = [F(lo, at), F(hi, at)]
    else:
        p = [F(at, lo + h), F(at, hi - h)]
        path = [F(at, lo), F(at, hi)]
    plats = [{'at': q, 'size': F(post, post), 'rise': rise, 'surface': TIMBER, 'top_surface': TIMBER_H,
              'notes': 'Timber set post'} for q in p]
    beams = [{'path': path, 'width': cap, 'bottom': top, 'depth': cap, 'surface': TIMBER_H,
              'notes': 'Timber set cap'}]
    return plats, beams


def rails(x0, y0, x1, y1, gauge=112):
    """Two iron rails 6 high along a straight line (as XD-02's), centred on the line."""
    import math
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    ox, oy = -dy / n * gauge / 2, dx / n * gauge / 2
    out = []
    for s in (-1, 1):
        cx, cy = s * ox, s * oy
        ex, ey = -dy / n * 5, dx / n * 5
        pts = [(x0 + cx - ex, y0 + cy - ey), (x1 + cx - ex, y1 + cy - ey), (x1 + cx + ex, y1 + cy + ey),
               (x0 + cx + ex, y0 + cy + ey)]
        out.append({'rise': 6, 'surface': IRON, 'top_surface': IRON,
                    'outline': [F(round(px), round(py)) for px, py in pts], 'notes': 'Rail'})
    return out


def cart(x, y, facing=0, notes="An old ore cart, left where it stopped.", pid=None):
    """XD-02's riveted ore cart: chassis, box, four wheels; facing in degrees (0: along x)."""
    import math
    a = math.radians(facing)
    ca, sa = math.cos(a), math.sin(a)

    def at(dx, dy):
        return F(round(x + dx * ca - dy * sa, 1), round(y + dx * sa + dy * ca, 1))

    box = {'at': F(x, y), 'size': F(180, 100), 'rise': 88, 'facing': facing, 'surface': CART_SIDE,
           'end_surface': IRON, 'top_surface': FLOOR, 'base': 24, 'top_size': F(200, 120), 'notes': notes}
    if pid:
        box = {'id': pid, **box}
    out = [{'at': F(x, y), 'size': F(160, 80), 'rise': 24, 'facing': facing, 'surface': TIMBER_H,
            'top_surface': TIMBER_H, 'notes': "The cart's chassis"}, box]
    for dx in (-60, 60):
        for dy in (-66, 66):
            out.append({'at': at(dx, dy), 'size': F(48, 10), 'rise': 48, 'facing': facing, 'surface': IRON,
                        'top_surface': IRON, 'notes': 'Cart wheel'})
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Veins: a wall panel each (clicked), a map variable each, one rock each (D-27)


def vein_panel(gem, n, offset=None, length=256, bottom=16, height=384):
    """The panel of vein n (1-5) of a gem; `offset` along its wall, else centred."""
    d = {'id': 'panel:%s_%d' % (gem, n), 'length': length, 'bottom': bottom, 'height': height,
         'surface': vein_surface(gem), 'notes': "%s vein %d: one rock (q-d7.%s_veins)." % (GEM_NAMES[gem], n, gem)}
    if offset is None:
        d['at'] = 'centre'
    else:
        d['offset'] = offset
    return d


VEIN_GLINT = {'ruby': F(255, 70, 60), 'emerald': F(70, 255, 110), 'sapphire': F(80, 120, 255),
              'diamond': F(220, 240, 255)}


def vein_light(gem, n, at, height=176, radius=360):
    """A small coloured light in front of vein n, so the vein glints from across the cave (`at` about 64 out from the
    wall)."""
    return {'id': 'light:%s_%d' % (gem, n), 'at': F(*at), 'height': height, 'radius': radius,
            'color': VEIN_GLINT[gem], 'notes': '%s vein %d glints.' % (GEM_NAMES[gem], n)}


def wall_point(outline, edge, offset=None, length=256, out=64):
    """The point `out` into the room in front of the middle of a panel on an outline's edge (0-based, from point i to
    i+1; counter-clockwise outline, so the room lies to the left): `offset` from the edge's start, else centred."""
    import math
    (x0, y0), (x1, y1) = outline[edge], outline[(edge + 1) % len(outline)]
    n = math.hypot(x1 - x0, y1 - y0)
    d = n / 2 if offset is None else offset + length / 2
    ux, uy = (x1 - x0) / n, (y1 - y0) / n
    return round(x0 + ux * d - uy * out), round(y0 + uy * d + ux * out)


def vein_var(gem, n):
    return '%s_%d' % (gem, n)


def vein_events(gem, count=5):
    """One event per vein: one rock of the gem (map_gives of the hook), the hook (sets q-d7.dug), the vein's map
    variable; once spent, the source's line (dark/aaze0039:10)."""
    out = []
    for n in range(1, count + 1):
        v = vein_var(gem, n)
        out.append({
            'id': 'evt:%s_%d' % (gem, n), 'preset': 'script', 'source': 'panel:%s_%d' % (gem, n),
            'title': '%s vein' % GEM_NAMES[gem],
            'condition': {'not': {'map_var': v}},
            'effects': [{'set': {'var': {'map_var': v}, 'value': 1}},
                        {'give_item': '%s_rock' % gem},
                        {'lua': 'XeenQuests.hook("q-d7.%s_veins")' % gem},
                        {'text': "You work %s %s rock out of the vein." % ('an' if gem[0] in 'aeiou' else 'a', gem)}],
            'else_effects': [{'text': SPENT_LINE}],
            'notes': "%s vein %d (dark/aaze0039:1-4 the hover, :10 when spent): one %s rock (%d, the hook's "
                     "map_gives), q-d7.%s_veins sets q-d7.dug (113144); map variable %s." %
                     (GEM_NAMES[gem], n, gem, ROCKS[gem], gem, v)})
    return out


def refill_event(bit, gems, count=5):
    """The pocket's entry refills its veins once the God of Minerals has been paid (D-27): when its refill bit is set,
    every vein's variable goes back to 0 and the bit is cleared."""
    effects = [{'set': {'var': {'map_var': vein_var(g, n)}, 'value': 0}} for g in gems for n in range(1, count + 1)]
    effects += [{'clear_qbit': bit}, {'text': "The veins glitter again: the God of Minerals has been at work."}]
    # On a fresh entry only (A3's bug, session 7): a load inside a visit (a saved game) finds in_visit set (saved with
    # the map) and refills nothing; leaving clears it (visit_end_event), as DD-09's prisoners.
    effects += [{'set': {'var': {'map_var': VISIT_VAR}, 'value': 1}}]
    return {'id': 'evt:refill', 'preset': 'script', 'trigger': 'load',
            'condition': {'qbit': bit, 'not': {'map_var': VISIT_VAR}}, 'effects': effects,
            'else_effects': [{'set': {'var': {'map_var': VISIT_VAR}, 'value': 1}}],
            'notes': "D-27: the God of Minerals (DD-10B, q-d7.god_of_minerals) sets the three refill bits; this "
                     "pocket's fresh entry (not a load inside a visit: in_visit) resets its veins and clears its own "
                     "bit (%s)." % bit}


VISIT_VAR = 'in_visit'


def visit_end_event():
    """Leaving ends the visit: the next load is a fresh entry (refill_event)."""
    return {'id': 'evt:visit_end', 'preset': 'script', 'trigger': 'leave',
            'effects': [{'set': {'var': {'map_var': VISIT_VAR}, 'value': 0}}],
            'notes': "Leaving ends the visit: the next load is a fresh entry (evt:refill)."}


def false_vein_event(gem, panel, amount, var='false_vein'):
    """B and C (D-27): a sixth vein of the gem that explodes once ('A gem exploded!', fire to every member); after
    that it says it is spent."""
    return {'id': 'evt:false_vein', 'preset': 'script', 'source': panel, 'title': '%s vein' % GEM_NAMES[gem],
            'condition': {'not': {'map_var': var}},
            'effects': [{'set': {'var': {'map_var': var}, 'value': 1}},
                        {'damage': {'amount': amount, 'kind': 'fire'}},
                        {'message': 'A gem exploded!'}],
            'else_effects': [{'text': SPENT_LINE}],
            'notes': "D-27's false vein (dark/aaze0039:11): %d fire to every member, once." % amount}


def exit_event(source, title='Adit'):
    return {'id': 'evt:exit', 'preset': 'exit', 'source': source, 'title': title,
            'notes': "Out to the outdoor map by the adit: the game's own leave window (D-24); 'Exit the Gemstone "
                     "Mines?' (dark/aaze0039:0) is its meaning."}


def arrival_event(text, bit_name='arrived_once'):
    return {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1,
            'condition': {'not': {'qbit': bit_name}}, 'once': True,
            'effects': [{'message': text}, {'qbit': bit_name}],
            'notes': "Why the party is here (Q-D7), on the first arrival only."}


# ---------------------------------------------------------------------------------------------------------------------
# D-89 identity (lane A8 s28, reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 DD-10A/B/C: "a timbered adit with rails, then
# rock boxes with flat vein panels"): every vein framed by clusters of MM8 d37 crystal (gcrys*) in its gem's colour,
# the rails carried on along the timbered galleries, the stopes' floors sloping.

# gcrysc1 repeats only across (trim_u, 16 x 32): enlarged 5 times so one repeat covers a shard's height; gcrysc3 at
# DD-10B's and C's size (one size per texture per map).
VEIN_CRYSTAL = {'ruby': S('gcryswal', 256, 256), 'emerald': S('gcrysc1', 16, 32, scale=5),
                'sapphire': S('gcrysc3', 64, 128), 'diamond': S('gcrysc3', 256, 512)}
_GEM_OF_TEXTURE = {t: g for g, t in VEIN_TEXTURES.items()}


def vein_crystals(rooms):
    """Adds a cluster of three tapering crystal shards at both ends of every vein panel (a panel on a numbered edge of
    an outline room whose surface is a vein picture, the false vein included), standing 56-104 out from the wall
    line (clear of `rough`'s 32), in the gem's colour. A cluster within 64 of the edge's ends is left out. The shards
    stand square to the map (a turned tapering block's faces are not flat on whole units)."""
    import math
    for r in rooms:
        pts = r.get('outline')
        if not pts:
            continue
        for w in r.get('walls', []):
            if not isinstance(w['wall'], int):
                continue
            (x0, y0), (x1, y1) = pts[w['wall']], pts[(w['wall'] + 1) % len(pts)]
            n = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / n, (y1 - y0) / n
            for p in w.get('panels', []):
                gem = _GEM_OF_TEXTURE.get(p['surface']['texture'])
                if not gem:
                    continue
                start = p['offset'] if 'offset' in p else (n - p['length']) / 2
                surf = VEIN_CRYSTAL[gem]
                for along, sign in ((start, -1), (start + p['length'], 1)):
                    if along < 64 or along > n - 64:
                        continue
                    for k, (da, out, size, rise) in enumerate(((8, 72, 44, 152), (44, 60, 32, 100), (-16, 108, 28, 72))):
                        a = along + sign * da
                        x, y = x0 + ux * a - uy * out, y0 + uy * a + ux * out
                        r.setdefault('platforms', []).append(
                            {'at': F(round(x), round(y)), 'size': F(size, size), 'top_size': F(8, 8), 'rise': rise,
                             'surface': dict(surf), 'top_surface': dict(surf),
                             'notes': "%s crystal grown beside the vein." % GEM_NAMES[gem]})


# ---------------------------------------------------------------------------------------------------------------------
# Plan helpers (L1/L2 words)


def sp(i, name, kind, size, extent, floor, clear, purpose, theme, pop=None, treasure=None, **kw):
    d = {'id': 'room:' + i, 'name': name, 'kind': kind, 'size': size, 'extent': F(*extent), 'floor': floor,
         'clear_height': clear, 'purpose': purpose, 'theme': theme}
    if pop:
        d['population'] = pop
    if treasure:
        d['treasure'] = treasure
    d.update(kw)
    return d


def placed(actor, count, level, notes=None):
    d = {'actor': actor, 'groups': 1, 'per_marker': F(count, count), 'levels': F(level, level), 'placed': True}
    if notes:
        d['notes'] = notes
    return d


def link(i, a, b, kind, **kw):
    d = {'id': 'link:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind}
    d.update(kw)
    return d


def door(i, opening, kind='hinged', **kw):
    d = {'id': 'door:' + i, 'opening': opening, 'kind': kind}
    if kind == 'hinged':
        d.update({'hinge': 'left', 'thickness': 16, 'speed': 80})
    d.update({'surface': MINE_DOOR, 'back_surface': MINE_DOOR, 'edge_surface': TIMBER, 'top_surface': TIMBER_H})
    d.update(kw)
    return d


def write_levels(out_dir, levels, project, plan_fn, diagram, rooms_doc, objects, wiring, identity=None):
    """Write L1-L4 as DD-04's generator does: L1 plan words, L2 with extents, L3 the rooms, L4 objects and wiring.
    `identity` (D-89) goes into L4's project.yml."""
    for level in levels:
        d = out_dir + '/' + level
        os.makedirs(d, exist_ok=True)
        dump(d + '/project.yml', dict(project, identity=identity) if identity and level == 'L4' else project)
        dump(d + '/plan.yml', plan_fn(level))
        open(d + '/diagram.txt', 'w').write(diagram)
        if level in ('L3', 'L4'):
            dump(d + '/rooms.yml', rooms_doc)
        if level == 'L4':
            dump(d + '/objects.yml', objects)
            dump(d + '/wiring.yml', wiring)
