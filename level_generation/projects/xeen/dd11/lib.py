"""DD-11A/B/C Troll Holes: helpers shared by the three generators (gen_a.py, gen_b.py, gen_c.py).

Written by agent:xeen-a7-dd11 after XD-23's gen.py (level_generation/projects/xeen/xd23/gen.py): the same texture family
(MM7's red-brown dirt cave 7dirttyl, straw, hides, bark, bones), the same room helpers. Frame: x east, y north, z up;
every pocket's pit is at the origin, its floor 0."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# One texture family (XD-23's): MM7's red-brown dirt (7dirttyl) on walls, roofs and floors; hides (xohide, XD-05's)
# for curtains and flaps; straw (MM6) for nests; bark (xdbark, D2's) for log doors and root steps; bones (xobones,
# XD-05's) for middens; water (wtrtyl) for seeps; daylight (xddaylt, D2's pass, D-34) through the sod hatch at a
# burrow's top; the pole gate (xopoles, XD-05's) for wicker gates.
DIRT = S('7dirttyl', 128, 128)
# D-89 identity (A7 s28): the burrows' floors in MM7's cave floor (cfb1, 7d08's) so walls and floors differ; Hobstadt's
# hall and its gate in MM8 Ancient Troll Home d43's cut stone (gkp2-bs1 walls, tfb11 carved slabs, gkp2flr roof).
DIRTFLR = S('cfb1', 128, 128)
CUTSTONE = S('gkp2-bs1', 128, 256)
SLABS = S('tfb11', 128, 128)
SLABROOF = S('gkp2flr', 128, 128)
HIDE = S('xohide', 128, 256)
STRAW = S('straw', 256, 256)
BARK = S('xdbark', 128, 256)
BONES = S('xobones', 128, 256)
POLES = S('xopoles', 128, 128)
# D-34 (3): the Darkside's own view (xddaylt: D2's pass under the dim amber-grey sky), not XD-05's Cloudside meadow.
DAYLIGHT = S('xddaylt', 256, 128, fit=True, uneven=True)
WATER = {'texture': 'wtrtyl'}
SKY = S('7dirttyl', 128, 128, sky=True)

THEMES = [
    {'id': 'theme:dirt', 'wall': DIRT, 'floor': DIRTFLR, 'ceiling': DIRT, 'door': HIDE, 'reveal': DIRT,
     'notes': "The pocket: MM7's red-brown dirt cave (7dirttyl) on walls and roofs, MM7's cave floor (cfb1) underfoot; hide flaps (xohide) for doors."},
    {'id': 'theme:straw', 'wall': DIRT, 'floor': STRAW, 'ceiling': DIRT, 'door': HIDE, 'reveal': DIRT,
     'notes': "Nests and sleeping hollows: the same dirt, the floor deep in old straw (MM6 straw)."},
    {'id': 'theme:hall', 'wall': CUTSTONE, 'floor': SLABS, 'ceiling': SLABROOF, 'door': HIDE, 'reveal': CUTSTONE,
     'notes': "Hobstadt's hall: an ancient troll home's cut stone (MM8 d43: gkp2-bs1 walls, tfb11 carved slabs, "
              "gkp2flr roof), the trolls' own older work under the dirt (D-89 identity)."},
]

ROUGH = {'step': 224, 'depth': 72}


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def octo(cx, cy, r, ry=None):
    ry = ry or r
    c, cy_ = int(r * 0.41), int(ry * 0.41)
    return [[cx - c, cy - ry], [cx + c, cy - ry], [cx + r, cy - cy_], [cx + r, cy + cy_], [cx + c, cy + ry],
            [cx - c, cy + ry], [cx - r, cy + cy_], [cx - r, cy - cy_]]


def blob(cx, cy, rx, ry):
    """A lumpy hexagon: a heap of bones, a straw nest scooped into the floor."""
    return [[cx - rx, cy - ry // 3], [cx - rx // 3, cy - ry], [cx + rx // 2, cy - ry], [cx + rx, cy - ry // 4],
            [cx + rx // 2, cy + ry], [cx - rx // 2, cy + ry]]


def nest(id, at, rx, ry, notes):
    return {'id': id, 'outline': blob(at[0], at[1], rx, ry), 'rise': 24, 'surface': STRAW, 'top_surface': STRAW,
            'notes': notes}


def heap(id, at, rx, ry, notes, rise=32, surface=None):
    s = surface or BONES
    d = {'outline': blob(at[0], at[1], rx, ry), 'rise': rise, 'surface': s, 'top_surface': s, 'notes': notes}
    if id:
        d = {'id': id, **d}
    return d


def dump(doc):
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)


def write(folder, docs):
    folder.mkdir(parents=True, exist_ok=True)
    for name, doc in docs:
        (folder / name).write_text(doc if isinstance(doc, str) else dump(doc))


def chest(id, room, at, facing, level, gold, notes, items=2, trap=None):
    # D-99: facing None lets the studio turn the chest (its back to the wall by it); a word overrides.
    d = {'id': id, 'room': room, 'at': at, **({'facing': facing} if facing else {}), 'treasure_level': level,
         'random_items': items, 'gold': gold, 'notes': notes}
    if trap:
        d['trap_level'] = trap
    return d


def light(id, room, at, height, radius, color, **kw):
    d = {'id': id, 'room': room, 'at': at, 'height': height, 'radius': radius, 'color': color}
    d.update(kw)
    return d


TROLL_LIGHT = [160, 125, 95]
DAY_LIGHT = [150, 140, 122]   # D-34: the Darkside's dim amber-grey day (was a noon white 205, 200, 185)

# The map card (A2 writes the row from these). Rest encounters 10 % (D-33 (2)): the warren trolls' rows follow
# relations.yml (hostile before the tribute, friendly after), so a rest spawn in a befriended pocket is friendly.
def map_stats(mid):
    return {'id': mid, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 3, 'trap_dice': 3,
            'perception_difficulty': 6, 'refill_days': 672, 'music': 8, 'environment': 'cave',
            'lock_difficulty': 6,
            'slots': [{'monster': 'Xeen Warren Troll', 'tier': 1, 'per_marker': [2, 3], 'weight': 100}]}


ATMOSPHERE = {
    'format': 0,
    'open_sky': {'mode': 'open', 'sky_texture': 'xeendark1'},
    'notes': "The pit's shaft is open to D2's sky (the darkside's xeendark1, which the world's sky.yml resolves) through its sky faces at the top; the rest of the pocket is lit by its own lights.",
}


# ------------------------------------------------------------------------------------------------ D-89 cave shape
# Every pocket's natural rooms through tools/xeen/cave_shape.py (A7 s28): corners cut where nothing needs them square,
# floors that rise and fall, vaulted roofs; the tunnels and stairs keep their slopes.
def shape_caves(l4, caves):
    import sys
    sys.path.insert(0, str(R / 'tools' / 'xeen'))
    import cave_shape
    return cave_shape.shape_l4(l4, caves, rough=ROUGH)
