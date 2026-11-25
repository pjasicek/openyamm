#!/usr/bin/env python3
"""F65 (the player's pins 2026-11-25, XD-25 p1 "it is a bit hard to click on them and get the crystal"): decorations
that act on a click by themselves, standing on or in front of something with an event.

MMerge's interactive decorations (the game's `InteractiveDecorationRules.cpp`) run their own event when a map gives
them none: a gem crystal (crclstr, crystl0, crys5, crys6, dec09-dec12) gives a random Gem and hides, a barrel or
cauldron gives a stat, a trash heap, cask, flour sack, bag, bucket or camp fire gives its find, MM8's dec40-dec75
fountains and pedestals their effect, a brazier or torch (brazir2f, brzier00, nwtrchnf, trchb00) toggles its light.
Since D-153 a Use looks through a decoration without an event to the thing behind it; a self-acting one is not
looked through. XD-25's crystals (crclstr, no event) stood on the crystal housing (evt:crystals): the first click took
a gem and hid them, only the second reached the housing.

For every decoration without an event whose decoration is self-acting, the clicked event faces (not pressure plates)
and the event decorations it stands on or by are found. **Error** `self_acting.on_event`: it stands on the top of a
clicked thing (a horizontal event face it overlaps, its foot within -8..32 of that top) or overlaps an event
decoration (within both radii + 16, overlapping in height): it reads as part of that thing, and its first click acts
instead (a crystal on its housing, a pot or fire on a hearth). Fix: give the decoration the event (a wiring event with
`source: deco:<id>`, the same effects) or use a decoration that does not act by itself. **Warning**
`self_acting.beside_event`: it stands within its radius + 48 in front of an upright clicked face that it overlaps along
and in height (a sack beside a bed, a barrel by a trapdoor): a thing of its own the player clicks for itself, while the
event's object stays clickable elsewhere; listed so a new one is looked at. A self-acting decoration away from events
(a stat barrel in a corner) is fine.

Usage: tools/xeen/check_self_acting_decos.py [<map.blv>...] [--assets ROOT]    no maps: every Xeen BLV in assets_dev.
Exit 1 on an error (warnings do not fail)."""
import argparse
import glob
import json
import math
import os
import subprocess
import sys
import tempfile

R = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
OYMAP = os.path.join(R, 'openyamm-studio/build-xeen/oymap')
CLICKABLE = 0x02000000

CRYSTALS = {'crystl0', 'crclstr', 'crys5', 'crys6', 'dec09', 'dec10', 'dec11', 'dec12'}
FAMILIES = [
    ('barrel', {'barrel', 'dec03', 'smlbarel', 'bigbarel', '7dec32'}),
    ('cauldron', {'cauldron', 'dec26'}),
    ('trash heap', {'trasheap', 'trash heap', 'trash pile', 'dec23'}),
    ('camp fire', {'ckfyr00', 'cmpfyr00', 'fire01', '7dec02', 'dec24', 'dec25'}),
    ('cask', {'keg', 'cask'}),
    ('flour sack', {'floursac'}),
    ('gold bag', {'bag_a'}),
    ('large bag', {'bag01'}),
    ('bucket', {'bucket'}),
    ('light toggle', {'brazir2f', 'brzier00', 'nwtrchnf', 'trchb00'}),
]


def norm(value):
    return (value or '').strip().lower()


def load_rows(assets):
    """decoration_data.txt rows by '#': (internal name, hint, radius, height), the engine's and Xeen's."""
    rows = {}
    for path in (f'{assets}/engine/data_tables/decoration_data.txt', f'{assets}/worlds/xeen/models/decoration_data.txt'):
        if not os.path.exists(path):
            continue
        for line in open(path, encoding='latin-1'):
            c = line.rstrip('\n').split('\t')
            if len(c) > 5 and c[0].strip().isdigit():
                rows[int(c[0])] = (c[1], c[2], int(c[4] or 0), int(c[5] or 0))
    return rows


def self_acting(internal, hint, instance):
    """The family name when the game binds this decoration to its own event (InteractiveDecorationRules.cpp)."""
    keys = [k for k in (norm(hint), norm(internal), norm(instance)) if k]
    crystal_keys = [norm(internal)] + ([norm(instance)] if norm(hint) == 'crystal' else [])
    if any(k in CRYSTALS for k in crystal_keys):
        return 'gem crystal'
    for name, words in FAMILIES:
        if any(k in words for k in keys):
            return name
    for k in (norm(internal), norm(instance)):
        if k.startswith('dec') and len(k) >= 4 and k[3:].isdigit() and 40 <= int(k[3:]) <= 75:
            return 'fountain/pedestal'
    return None


def check(path, assets, rows):
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OYMAP, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        m = json.load(open(t.name))['map']
    stem = os.path.basename(path)[:-4]
    V = m['vertices']
    ents = m['entities']

    def info(e):
        r = rows.get(e['decoration_list_id'] + 1)
        return r if r else ('?', '', 32, 64)

    def event(e):
        return e.get('event_id_primary') or e.get('event_id_secondary')

    evdecos = [e for e in ents if event(e)]
    # Clicked faces only (MM's face attribute 0x02000000); a pressure plate's step event is never clicked.
    faces = [(i, f) for i, f in enumerate(m['faces'])
             if f.get('cog_triggered') and f['attributes'] & CLICKABLE and not f.get('is_portal')]
    out = []
    for e in ents:
        if event(e):
            continue
        internal, hint, rad, h = info(e)
        family = self_acting(internal, hint, e.get('name'))
        if not family:
            continue
        rad = max(rad, 16)
        p = e['position']
        hits = []
        beside = []
        for g in evdecos:
            q = g['position']
            _, _, grad, gh = info(g)
            if math.hypot(p[0] - q[0], p[1] - q[1]) < rad + grad + 16 and p[2] < q[2] + gh and q[2] < p[2] + h:
                hits.append(f'event decoration {g["name"]} (event {event(g)})')
        for i, f in faces:
            n = [c / 65536 for c in f['plane_normal']]
            P = [V[v] for v in f['vertices']]
            if abs(n[2]) > 0.7:
                xs = [x[0] for x in P]
                ys = [x[1] for x in P]
                fz = max(x[2] for x in P)
                if min(xs) - rad <= p[0] <= max(xs) + rad and min(ys) - rad <= p[1] <= max(ys) + rad \
                        and -8 <= p[2] - fz <= 32:
                    hits.append(f'event face {i} on top ({f["texture"]}, event {f["cog_triggered"]})')
                continue
            dist = (p[0] - P[0][0]) * n[0] + (p[1] - P[0][1]) * n[1]
            if not -8 <= dist <= rad + 48:
                continue
            u = (-n[1], n[0])
            ts = [x[0] * u[0] + x[1] * u[1] for x in P]
            s = p[0] * u[0] + p[1] * u[1]
            zlo, zhi = min(x[2] for x in P), max(x[2] for x in P)
            if min(ts) - rad <= s <= max(ts) + rad and p[2] < zhi and zlo < p[2] + h:
                beside.append(f'event face {i} {dist:.0f} behind it ({f["texture"]}, event {f["cog_triggered"]})')
        where = f'{stem}: decoration {internal} ({family}, no event) at [{p[0]}, {p[1]}, {p[2]}]'
        if hits:
            shown = '; '.join(hits[:3]) + (f' and {len(hits) - 3} more' if len(hits) > 3 else '')
            out.append(f'error self_acting.on_event {where} stands on {shown}: its first click acts by itself; give '
                       f'it the event or use a decoration that does not act')
        elif beside:
            shown = '; '.join(beside[:3]) + (f' and {len(beside) - 3} more' if len(beside) > 3 else '')
            out.append(f'warning self_acting.beside_event {where} stands by {shown}')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('maps', nargs='*')
    ap.add_argument('--assets', default=os.path.join(R, 'assets_dev'))
    a = ap.parse_args()
    maps = a.maps or sorted(glob.glob(os.path.join(R, 'assets_dev/worlds/xeen/maps/xeen_*.blv')))
    rows = load_rows(a.assets)
    errors = warnings = 0
    for path in maps:
        for line in check(path, a.assets, rows):
            print(line)
            errors += line.startswith('error')
            warnings += line.startswith('warning')
    print(f'total {errors} self-acting decoration(s) on an event (errors), {warnings} beside one (warnings) on '
          f'{len(maps)} map(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
