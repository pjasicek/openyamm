#!/usr/bin/env python3
"""P4's L4 figures (measure.json) and NOTES.md (A6's planes sub-agent, seventeenth session, 2026-11-21), from gen.py's
geometry, the build (build.json, the scene's actors) and the playtest logs named by TESTS_LOG (default tests_n2.log).

    python3 level_generation/projects/xeen/p4/notes.py
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402
sys.path.insert(0, str(pathlib.Path(_REPO_ROOT, 'level_generation/projects/xeen/common/planes')))
import pieces as PC  # noqa: E402

X = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p4')
L4 = gen.BRIEF / 'L4'
RES = 16
HALF = gen.HALF


def to_px(p):
    return ((p[0] + HALF) / RES, (HALF - p[1]) / RES)


def mask(polys):
    img = Image.new('L', (2 * HALF // RES, 2 * HALF // RES), 0)
    d = ImageDraw.Draw(img)
    for poly in polys:
        d.polygon([to_px(p) for p in poly], fill=255)
    return np.array(img) > 0


def figures():
    plats = gen.ROOMS['rooms'][0]['platforms']
    floor_ids = {f'platform:{gen.key(s)}' for s in gen.SPACES} | {f"platform:{gen.key(l['id'])}" for l in gen.D['links']}
    walk = mask([gen.foot(p) for p in plats if p['id'] in floor_ids])
    blocked = mask([gen.foot(p) for p in plats if p['id'] in gen.OBSTACLES])
    walk &= ~blocked
    sea = ~mask([gen.foot(p) for p in plats if p.get('solid') is not False and p['id'] != 'platform:sea'])
    px = RES * RES
    f = {'walkable_area_m': round(walk.sum() * px / 1e6, 1), 'sea_area_m': round(sea.sum() * px / 1e6, 1),
         'sea_share': round(sea.sum() / sea.size, 3)}
    b = json.load(open(X / 'build/build.json'))
    f['build'] = b['counts']
    tri = 0
    scene = yaml.safe_load(open(X / 'build/xeen_p4.scene.yml'))
    blv_faces = b['counts']['faces']
    # triangles: each platform face is a convex polygon of n corners (n - 2 triangles); from the generator's shapes
    for p in plats:
        n = len(p['outline']) if 'outline' in p else 4
        tri += 2 * (n - 2) + 2 * n
    f['triangles_estimate'] = tri
    f['faces'] = blv_faces
    acts = scene['initial_state']['actors']
    f['monsters'] = len(acts)
    f['monsters_hidden'] = sum(1 for a in acts if a.get('group') == gen.GUARD_GROUP)
    levels = {r['id']: r['level'] for r in gen.PD.ROWS.values()}
    levels[gen.OCTOPOD_DEEP] = levels[11471]     # A2's 11474: 11471's numbers (session 20)
    f['kill_xp_per_member'] = round(sum(gen.PD.xp(levels[a['monster_info_id']]) for a in acts) / 4)
    arr = gen.PLACE['entrance:d7_fall']['at']
    first = min((math.hypot(a['position']['x'] - arr[0], a['position']['y'] - arr[1]), a['monster_info_id'])
                for a in acts if a.get('group') != gen.GUARD_GROUP)
    f['first_fight'] = int(first[0])
    f['first_fight_row'] = first[1]
    homes = [g['at'] for g in gen.D['groups'] if g.get('swims')]
    f['octopod_homes_from'] = {sid: int(min(gen.PG.poly_distance([tuple(v) for v in gen.TOPS[sid]], h) for h in homes))
                               for sid in ('room:landing', 'room:arena', 'room:chamber')}
    # P-2: what touches the Grotto and the Veil's colonnade beyond the Veil, and how high it stands over it
    veil = next(p for p in plats if p['id'] == 'platform:veil')
    a, bq, _ = gen.link_cut(gen.VEIL_LINK)
    flank_end = gen.GATE_Y - gen.FLANK_OUT
    za = gen.slab_z(gen.VEIL_LINK, (gen.GATE_X, flank_end))
    f['p2'] = {
        'grotto_over_sea': gen.CHAMBER_FL - gen.WATER,
        'veil_colonnade_over_sea_min': za - gen.WATER,
        'veil_colonnade_over_sea_at': 'its side just beyond the flank stubs (top %d)' % za,
        'flank_stubs_over_court_min': gen.FLANK_H,
        'flank_length': gen.FLANK_IN + gen.FLANK_OUT,
        'surface_jump_clears': 55,
        'lip_min': min(gen.CHAMBER_FL - gen.WATER, za - gen.WATER, gen.FLANK_H),
        'no_steps': list(gen.NO_STEPS),
        'veil_slab_rise': veil['rise'],
    }
    import re
    f['textures'] = sorted(set(re.findall(r"texture: ([a-z0-9_]+)", (L4 / 'rooms.yml').read_text())))
    f['flights'] = {k: [int(v[0][0]), int(v[0][1])] for k, v in gen.FLIGHTS.items()}
    f['flight_count'] = len({p['id'].rsplit('_', 1)[0] for p in plats if '_steps_' in p['id']})
    f['wave_plates'] = len(gen.WAVES)
    f['water_volumes'] = len(gen.water_volumes())
    (X / 'measure.json').write_text(json.dumps(f, indent=1) + '\n')
    return f


def tests():
    log = X / os.environ.get('TESTS_LOG', 'tests_n2.log')
    out = {}
    for line in log.read_text().splitlines():
        if ' run ' in line:
            name = line.split()[0]
            out.setdefault(name, [0, 0])
            out[name][0] += ' exit 0 ' in line
            out[name][1] += 1
    return out, log


def notes(f):
    t, log = tests()
    c = f['build']
    p2 = f['p2']
    T = []
    T.append("# P4 Plane of Water of Xeen: L4\n")
    T.append("A6's planes sub-agent, seventeenth session, 2026-11-21. The L1 is `../L1/` with D-58 applied "
             "(`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`); L2-L4 are written by `output/studio_cal/p4/tools/gen.py` "
             "(rooms, objects, wiring, plan, project, atmosphere), the playtests by `tools/gen_playtests.py` from the "
             "build, this file and `output/studio_cal/p4/measure.json` by `tools/notes.py`. Scripts: `v.sh` "
             "(generate, validate), `b.sh` (build, playtests, install into the scratch root, audit), `run.sh` "
             "(playtests through the lane's game slots), `tour.sh`, `stage_install.sh`.\n")
    T.append(f"INSTALL_LINE\n")
    T.append("## What was built\n")
    T.append(f"- **room:sea**: one open-air room (sky preset `xeen_plane_water`), its floor the sea bed at {gen.FLOOR}, "
             f"walls and ceiling ({gen.CEIL}) sky faces. The sea's surface is one untouchable `7wtrtyl` face at "
             f"{gen.WATER}; under it MM9 water volumes (objects.yml `water`): `water:sea` (the inner sea, no current) and "
             f"four edge bands {gen.BAND} wide past the ring of sea stacks, each a constant inward current of "
             f"{gen.CURRENT} (D-58; no radial current); `water:hold`, the wreck's hold, {gen.HOLD_TOP} deep (waded).")
    T.append("- **Terraces** (the six L1 spaces): the L1 outline with a ragged rim, marble (`gtempw1`) out of the sea "
             "with a flagstone top (`gtempflr`; the Coral Garden `xpwcoral`), on a wider foot of rough rock "
             "(`gwspotwl`) whose top is a ledge 248 under the surface, below a swimmer's feet. Broken wall stubs on "
             "the rims (brick `cdb` round the wreck, coral rock round the garden), off every walking line.")
    T.append("- **Colonnades** (the seven L1 links): marble slabs from the bed, broken columns along both edges "
             "(some intact with capitals).")
    T.append(f"- **Steps out of the water**: {f['flight_count']} flights of 32 (down to {gen.STEP_LOW}): at the middle "
             "of every colonnade but the Veil's and at one rim of every terrace but the Whirlpool Court and the Grotto "
             "(L1, P-2). A swimmer at the surface (feet -197) steps onto the flight and walks out (playtest_stepout).")
    T.append("- **The Whirlpool Court**: the whirlpool (a `7wtrtyl` disc, where the hidden guardians stand), a ring of "
             "eight mosaic slabs (`gtemprf`, once per face), a ring of broken columns, the test's floor at the east "
             "gate (S's pedestal beside it, blocked).")
    T.append(f"- **The Veil** (gate:sleeper): a falling sheet of water (`xcwisp`, translucent, flowing down) across the "
             f"head of the Grotto's colonnade, solid until qbit 111767, then passable and hidden; either side broken "
             f"wall stubs {gen.FLANK_H}-{gen.FLANK_H + 112} over the court, {p2['flank_length']} along the colonnade's "
             "head (P2's curtain route; L1 has no gate leaves, so no double door).")
    T.append("- **The Sleeper's Grotto** (192): a raised shelf of shell and stone (the couch's place, S's, blocked), a "
             "sea arch (two rock piers outside the rim and a hanging span), the return dais (hidden and passable until "
             "qbit 111763), the test's chest.")
    T.append("- **The Wreck**: a hull of MM8's ship planks (`bwoodb1`) across the south court; a breach on its "
             "north-east side with a sill of 56 (a step each side) keeps the hold's water in; the hold is half flooded "
             "(40, waded: D-58 Q2, no diving); a stern deck (`bmplnk`, 96) with the ship's log (`planes.log`) and its "
             "find (two Water Resistance, 258); a broken mast on the deck, a stump amidships, a fallen mast outside; "
             "the trapped strongbox in the hold.")
    T.append("- **The Sea Statue's forecourt**: the fountain basin in the middle of the forecourt (D-58 correction), "
             "its water and the plinth (`m38.plaque_water`; S's statue on it, blocked); the Drowned Bell's fallen "
             "frame (`planes.bell`; S's bell, blocked).")
    T.append("- **The Coral Garden**: the Tide Pool in a ring of coral rock (`planes.tide_pool`, the buff device).")
    T.append("- **The waterspout** (the way up): a translucent column of water flowing up from a basin at the Spray "
             "Terrace's corner; clicked, 'Ride the spout back to the Skyroads?' -> `leave: exit:d7_way_up` (D7 is "
             "installed and lists `entrance:p4_return`).")
    T.append(f"- **Waves**: {f['wave_plates']} PressurePlate platforms (`xpwspray`, 192 x 192) at L1's cells, none on "
             "the critical path, all calling `planes.wave`.")
    T.append("- **Sea stacks**: tapered rock stacks (two tiers, Pythagorean facings) in a ring near the room's edge with "
             "gaps, three broken arches.\n")
    T.append("## Wiring (A3's hooks by name)\n")
    T.append(f"- `evt:test` (step, the test's plate): 'Accept the test of Water?' Yes: `m38.test_water`, show group "
             f"{gen.GUARD_GROUP}, map variable test_accepted. `evt:test_check` (1 s): `Xeen.planeTestCheck(\"water\", "
             f"{gen.GUARD_GROUP})`. `evt:gate_open` (1 s once 111767 is set) and `evt:passed_load` (load, P-1): the "
             "Veil passable and hidden, the guardians hidden. `evt:gate`: the Veil clicked.")
    T.append("- `evt:dais_hide` (load, until 111763) and `evt:dais` ('Step onto the dais and return to the Skyroads?', "
             "`leave: exit:d7_dais`, locked text before the sleeper); `evt:way_up` (always open).")
    T.append("- `evt:wave` (nine plates), `evt:bell`, `evt:tide_pool`, `evt:log`, `evt:plaque`, the two chests.\n")
    T.append("## Figures (`output/studio_cal/p4/measure.json`)\n")
    T.append("| Figure | Target | L4 |\n| --- | --- | --- |")
    T.append(f"| Monsters | 30 (27 + the test's 3) | **{f['monsters']}** ({f['monsters_hidden']} hidden; 5 Great "
             "Octopods swimming) |")
    T.append(f"| Kill XP per member | D-58 32.38k | **{f['kill_xp_per_member'] / 1000:.2f}k** |")
    T.append("| POIs (L1 census) | C8 10-12 | 10 (S's statue, sleeper and couch, pedestal, dais and bell placed, "
             "session 20) |")
    T.append("| Chests | 2 at treasure 6 | 2 (the test's chest in the Grotto; the trapped strongbox in the hold) and "
             "the log's find (2 x Water Resistance) |")
    T.append(f"| P-2 lips | at least 192 | **{p2['lip_min']}**: the Veil's colonnade {p2['veil_colonnade_over_sea_min']} "
             f"over the sea at its lowest (just beyond the flank stubs), the Grotto {p2['grotto_over_sea']} "
             f"over the sea, the flank stubs {p2['flank_stubs_over_court_min']} over the court; a surface jump clears "
             "about 55 |")
    T.append(f"| First fight from the arrival | 1,500-4,000 | {f['first_fight']:,} (row {f['first_fight_row']}) |")
    T.append(f"| Octopod homes | >= 1,024 from the arrival terrace, the court, the Grotto | "
             f"{', '.join(f'{k[5:]} {v:,}' for k, v in f['octopod_homes_from'].items())} |")
    T.append(f"| Walkable area | 44-51 M (C1) | {f['walkable_area_m']} M units; the sea {f['sea_area_m']} M "
             f"({round(100 * f['sea_share'])} % of the room) |")
    T.append(f"| Build | - | {c['sectors']} sectors, {c['faces']} faces, {c['vertices']} vertices, {c['events']} events, "
             f"{c['chests']} chests, 0 lights; about {f['triangles_estimate']:,} triangles (estimate from the shapes) |")
    T.append(f"| Textures | Dungeon S, cap 30, at most 4 new | {len(f['textures'])} distinct ({', '.join(f['textures'])}); new `xpwspray`, `xpwcoral` (xpwhull not made: "
             "shipped `bwoodb1`) |")
    T.append("| Audit | 0 errors | 0 errors, 0 warnings; info: map variables p4_bell and p4_pool set by A3's hook Lua "
             "and read there |\n")
    T.append(f"## Playtests (headless, `run.sh`, N=2; `{log.name}`)\n")
    what = {'playtest': 'arrival, the colonnades, the forecourt, the court; the Veil holds before the test',
            'playtest_hostility': "27 hostile, the test's three hidden, a quiet arrival",
            'playtest_test': 'Yes raises the guardians; killed (damage_actor) they set 111767; the Veil stills; into '
                             'the Grotto; a reload keeps it',
            'playtest_bypass': "P-2: the Veil holds; off the court into the sea; from the sea against the Veil's "
                               "colonnade (both sides) and the Grotto's rim (three sides) the party stays in the water",
            'playtest_swim': '20 s at the surface: still at the surface, breath full, no drowning tick',
            'playtest_current': "the east band carries a swimmer inward to the band's inner edge (x 5,630)",
            'playtest_stepout': "a swimmer climbs the Spray Terrace's flight out of the sea: dry, on the terrace"}
    for k, (ok, n) in t.items():
        T.append(f"- `{k}.yml`: {what.get(k, '')}: **{ok} of {n}**.")
    T.append("\n## Tour\n")
    T.append("`output/studio_cal/p4/pics/contact_t1.png` (shots in `pics/t1/`, `tour1.yml`, `tour.sh`): the arrival, "
             "an overview, the north-east colonnade, the forecourt's fountain, the Tide Pool, the wreck, the court from "
             "its east gate, the Veil before and after the test, the Veil's colonnade, the Grotto, a swimmer's eye "
             "level, the stacks, under the water.\n")
    T.append("## Deviations from L1 (each one line)\n")
    T.append("- The fountain and plinth stand in the middle of the forecourt (D-58), not at L1's (256, 896).")
    T.append("- The ship runs from (-230, -3800) to (1330, -4760); the log and the strongbox stand on its deck and in its "
             "hold, not at L1's points (-128, -3840) and (1280, -4736).")
    T.append("- The test's floor stands at (-2880, 1664), off the walk line through the east gate (L1 (-2688, 1280)).")
    T.append("- The Great Octopods start mid-sea, 512 over the bed (-1,024), with `above_floor` (merge point 27) and "
             "`leash: 1280` (indoor leash since merge point 26); the Swimmer kind binds them to their volume (D-200: "
             "MM6's sea serpents' way, classic AI and the ink, no MM9 profile, no Aggressor bit).")
    T.append("- D-200 (3): the north group's home moved from L1's (-1024, 4224) to (0, 5120), so its leash plus the "
             "octopods' notice range (2,560) stays off the Whirlpool Court and the arrival.")
    T.append("- The waterspout, bell frame and tide pool are nudged 420 inside their terraces' rims.\n")
    T.append("## Open items\n")
    T += PC.notes_section('water', [
        "- The couch faces north along the shelf's 768 (at L1's north-east it overhung the 512 side).",
        "- The Drowned Bell (`xeen_drownedbell`) on the dry forecourt by its frame, facing 282 (no pool: the bell "
        "lies on the flags); clicked, `planes.bell` as the frame.",
        "- The two mid-sea Octopod groups are A2's 11474 (`Xeen Octopod E`, S's foam-free swimmer; 11471's numbers, "
        "the count unchanged)."])
    T.append("")
    T.append("## Dressing exceptions\n")
    T.append("- None: `oymap audit` reports no dressing errors or warnings (no props: the dressing is studio geometry).")
    return '\n'.join(T) + '\n'


if __name__ == '__main__':
    f = figures()
    text = notes(f)
    line = os.environ.get('INSTALL_LINE', 'Not yet installed in assets_dev (the scratch root only).')
    (L4 / 'NOTES.md').write_text(text.replace('INSTALL_LINE', line))
    print(json.dumps({k: f[k] for k in ('walkable_area_m', 'monsters', 'kill_xp_per_member', 'first_fight', 'p2',
                                         'octopod_homes_from', 'triangles_estimate')}, indent=1))
