#!/usr/bin/env python3
"""P1's L4 figures (measure.json) and NOTES.md (A6's planes sub-agent, 2026-11-21), from gen.py's geometry, the build
(build.json, the scene's actors) and the playtest log of the last N=2 run (tests_n2.log).

    python3 level_generation/projects/xeen/p1/notes.py
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
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402
sys.path.insert(0, str(pathlib.Path(_REPO_ROOT, 'level_generation/projects/xeen/common/planes')))
import pieces as PC  # noqa: E402

X = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p1')
L4 = gen.BRIEF / 'L4'
RES = 16
HALF = 6656


def to_px(p):
    return ((p[0] + HALF) / RES, (HALF - p[1]) / RES)


def mask(polys):
    img = Image.new('L', (2 * HALF // RES, 2 * HALF // RES), 0)
    d = ImageDraw.Draw(img)
    for poly in polys:
        d.polygon([to_px(p) for p in poly], fill=255)
    return np.array(img) > 0


def rect(e):
    """A block's or slab's footprint from its at, size and facing."""
    cx, cy = e['at']
    L, W = e['size']
    f = math.radians(e.get('facing', 0))
    ux, uy, vx, vy = math.cos(f), math.sin(f), -math.sin(f), math.cos(f)
    return [(cx + sx * L / 2 * ux + sy * W / 2 * vx, cy + sx * L / 2 * uy + sy * W / 2 * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def figures():
    rooms = gen.build_rooms()
    plats = rooms['rooms'][0]['platforms']
    walk_ids = lambda p: (p['id'].split(':')[1].startswith(('causeway', 'bridge')) or '_ramp' in p['id']
                          or p['id'] in [f"platform:{gen.key(s['id'])}" for s in gen.SHELVES]
                          or p['id'] in ('platform:arena_east', 'platform:arena_west'))
    polys = [p['outline'] if 'outline' in p else rect(p) for p in plats if walk_ids(p)]
    crater = mask([gen.CRATER])
    walk = mask(polys) & crater
    pit = mask([gen.ring(gen.PIT_AT[0], gen.PIT_AT[1], gen.PIT_R, 24)])
    walk &= ~pit
    hall = mask([gen.hall_outline()])
    px = RES * RES
    rock_ids = ('_crust', 'scree', 'spur', '_rock', 'gate_', 'way_up', 'column', 'spire_seam', 'batter', 'rib')
    rock = mask([p['outline'] if 'outline' in p else rect(p) for p in plats if any(r in p['id'] for r in rock_ids)])
    rock &= crater & ~walk
    lava = crater & ~walk & ~rock
    # ways out of the lava: the floor-0 shelves (a 40 step) and every ramp's foot
    outs = mask([p['outline'] for p in plats if p['id'] in ('platform:landing', 'platform:vents')]
                + [rect(p) for p in plats if '_ramp' in p['id']])
    dist = ndimage.distance_transform_edt(~outs) * RES
    f = {
        'walkable_area_m': round((walk.sum() + hall.sum()) * px / 1e6, 1),
        'crater_area_m': round(crater.sum() * px / 1e6, 1),
        'lava_area_m': round(lava.sum() * px / 1e6, 1),
        'lava_share': round(lava.sum() / crater.sum(), 3),
        'lava_to_way_out_max': int(dist[lava].max()), 'lava_to_way_out_p90': int(np.percentile(dist[lava], 90)),
        'ramps': sum(1 for p in plats if '_ramp' in p['id']),
        'rock_area_m': round(rock.sum() * px / 1e6, 1),
    }
    kinds = gen.RIM_KIND
    f['cliffs'] = {
        'outline_corners': len(gen.CRATER), 'ceiling_points': len(gen.SKYPTS), 'skyline_points': gen.SKY_RIM,
        'tops_over_lava': [min(q[2] for q in gen.SKYPTS[:gen.SKY_RIM]) - gen.LAVA,
                           max(q[2] for q in gen.SKYPTS[:gen.SKY_RIM]) - gen.LAVA],
        'spurs': kinds.count('tooth_nose'), 'falls': len(gen.recess('fall_back')),
        'ledges': sum(1 for p in plats if p['id'].startswith('platform:spur') and p['id'][-1].isdigit()),
        'needles': sum(1 for p in plats if p['id'].endswith('_needle')),
        'scree': sum(1 for p in plats if 'scree' in p['id']),
        'batter': sum(1 for p in plats if p['id'].startswith('platform:batter') and p['id'][-1].isdigit()),
        'batter_ledges': sum(1 for p in plats if p['id'].startswith('platform:batter') and p['id'].endswith('_ledge')),
        'batter_steps': sum(1 for p in plats if p['id'].startswith('platform:batter') and p['id'].endswith('_step')),
        'ribs': sum(1 for p in plats if p['id'].startswith('platform:rib')),
        'skirts': sum(1 for p in plats if '_crust' in p['id']),
        'longest_rim_wall': int(max(math.hypot(gen.CRATER[k][0] - gen.CRATER[k - 1][0],
                                               gen.CRATER[k][1] - gen.CRATER[k - 1][1])
                                    for k in range(len(gen.CRATER)) if kinds[k] != 'notch' and kinds[k - 1] != 'notch')),
    }
    b = json.load(open(X / 'build/build.json'))
    f['build'] = b['counts']
    scene = yaml.safe_load(open(X / 'build/xeen_p1.scene.yml'))
    acts = scene['initial_state']['actors']
    f['monsters'] = len(acts)
    f['monsters_hidden'] = sum(1 for a in acts if a.get('group') == gen.GUARD_GROUP)
    xp = sum(gen.PD.xp(next(r['level'] for r in gen.PD.ROWS.values() if r.get('id') == a['monster_info_id']))
             for a in acts)
    f['kill_xp_per_member'] = round(xp / 4)
    arr = gen.PLACE['entrance:d7_fall']['at']
    first = min((math.hypot(a['position']['x'] - arr[0], a['position']['y'] - arr[1]), a['monster_info_id'])
                for a in acts if a.get('group') != gen.GUARD_GROUP)
    f['first_fight'] = int(first[0])
    f['triangles_estimate'] = None
    f['p2'] = {'hall_walls_over_lava': gen.HALL_CEIL - gen.LAVA,
               'hall_walls_over_its_floor': gen.HALL_CEIL - gen.HALL_FLOOR,
               'gate_sill_over_lava': gen.HALL_FLOOR - gen.LAVA, 'highest_crater_floor': 260,
               'the_only_way_in': 'open:gate (door:sleeper, a hinged pair)'}
    (X / 'measure.json').write_text(json.dumps(f, indent=1) + '\n')
    return f


def tests():
    log = X / 'tests_look.log'
    out = {}
    for line in log.read_text().splitlines():
        if ' run ' in line:
            name = line.split()[0]
            ok = ' exit 0 ' in line
            out.setdefault(name, [0, 0])
            out[name][0] += ok
            out[name][1] += 1
    return out


def notes(f):
    t = tests()
    T = []
    T.append("# P1 Plane of Fire of Xeen: L4 (installed in assets_dev; the look pass of 2026-11-21)\n")
    T.append("A6's planes sub-agent, sixteenth session, 2026-11-21. The L1 is `../L1/` with D-58 applied "
             "(`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`); L2-L4 are written by `output/studio_cal/p1/tools/gen.py` "
             "(rooms, objects, wiring, plan, project, atmosphere), the playtests by `tools/gen_playtests.py` from the "
             "build, this file and `output/studio_cal/p1/measure.json` by `tools/notes.py`. Scripts: `v.sh` "
             "(generate, validate), `b.sh` (build, playtests, install into the scratch root, audit), `run.sh` "
             "(playtests through the lane's game slots), `stage_install.sh` (the lead's install).\n")
    T.append("Installed in assets_dev on 2026-11-21 at 04:44 (the look pass), 06:02 (the way up asks) and "
             f"{os.environ.get('S20_INSTALLED', '(session 20: not yet)')} (S's pieces, session 20: stage audit 0/0, "
             "the eight playtests 16 of 16 in the stage, `output/studio_cal/a6/s20/stage_p1.log`, then 16 of 16 "
             "from assets_dev). Session 25: S's Ember Font, burnt camp and the font's light installed "
             f"{os.environ.get('S25_INSTALLED', '(not yet)')} (`output/studio_cal/a6/s25/`).\n")
    T.append("## What was built\n")
    c = f['cliffs']
    T.append(f"- **room:crater**: one open-air room (sky `plane_fire`), its floor the lava lake at {gen.LAVA} "
             "(`lavtyl`, the floor's `lava` kind: it burns), its walls ragged cliffs to the sky (the look pass below). "
             "The shelves are L1's outlines standing in the lava, skirted with crust; the floor-0 ground (the Cinder "
             "Shelf, the Vent Field) is a bank, 40 over the lava (D-58 Q1: within 64); every raised shelf has ramps "
             f"({f['ramps']} in all) whose feet stand 32 over the lava; the causeways are crust wedges.")
    T.append("- **The Crucible** on its rise (256): a ring of black glass (`xpfglass`) round the pit, a pool of lava 24 "
             "under the glass (burning); the test's plate at its south gate (before S's pedestal); the guardians "
             f"(11623 and two 11622) the hidden group {gen.GUARD_GROUP} in the pit.")
    T.append(f"- **room:hall**, the Sleeper's Hall (floor {gen.HALL_FLOOR}): its own open-air room behind the crater's "
             "wall, walls to the sky on every side; the only way in is `open:gate`, a hinged pair of black-glass leaves "
             "(`door:sleeper`, two leaves, the right mirrored) at the end of the obsidian bridge from the Crucible.")
    T.append("- **Vents**: nine PressurePlate platforms (`xpfvent`, 192 x 192) at L1's cells, none on the walk, each "
             "calling A3's `planes.vent` (one time in three, 50 fire).")
    T.append("- **The Basalt Spires**: basalt columns; the tallest's red seam (`xdvruby`) calls `planes.spire`.\n")
    T.append("## The look pass (2026-11-21, the lead's review of contact_t1: D-58 P-4)\n")
    T.append(f"- **Cliffs**: the rim is {c['outline_corners']} corners (the studio's limit on an outline is 64), each "
             "with its own inset (no long straight runs: the longest rim wall "
             f"{c['longest_rim_wall']:,}); the sky is `ceiling_points` on every corner and up to three more on each wall "
             f"between ({c['skyline_points']} skyline points, {c['ceiling_points']} in all with a near ring and a ring "
             "at 2,960 over the middle), and the walls end on that line: jagged tops "
             f"{c['tops_over_lava'][0]:,}-{c['tops_over_lava'][1]:,} over the lava, the hall's notch the tallest "
             "(2,800). The generator emulates the studio's ceiling triangulation (shortest lines first) and drops the "
             "points that would make a sliver steeper than a ceiling may be. Three shipped rock faces by stretch of the "
             "rim: `vlcwl1` (lava seams), `gcav2wal` (MM8 Plane of Fire's black strata), `vlcwl3a`; the spurs "
             "`vlcwl2` (basalt columns).")
    T.append(f"- **Spurs and ledges**: {c['spurs']} spurs as teeth of the outline reaching 400-960 into the lava, their "
             f"noses 400-700 lower than their flanks (ridges running down); {c['ledges']} stepped ledges (a block "
             "tapering back, a jagged-topped ledge on it jutting past its front: leaning in and out; the tapered "
             "blocks are turned to Pythagorean directions so their leaning faces keep whole-unit corners), "
             f"{c['needles']} rock needles before them; the cliffs' batter at their foot (below, session 28-29), so no "
             "wall rises from the lava as a flat slab.")
    T.append(f"- **Lava falls**: {c['falls']} gullies cut 448 into the cliff, the back wall molten `orfyrlga` "
             "flowing down from a lip 600-700 under the gully's flanks, a glowing pool (`orfyrlga` drawn as a picture, "
             "burning by its `floors` entry) filling the gully's mouth, ringed with crust boulders. Lane S's "
             "`xeen_lavafall` is bound for outdoor maps only (no indoor binding), so the falls are geometry.")
    T.append("- **The Sleeper's Gate**: framed on the crater's side: black-glass jambs (176 x 160) from the lava to "
             "1,056, a basalt lintel over the doorway (its underside glass), a rough gable of glass over it (two "
             "wedges to 1,472) and two tapering obsidian shards beside it (to 1,560); the hinged pair, qbit 111764 and "
             "the P-2 walls unchanged.")
    T.append(f"- **Shelves and causeways**: {c['skirts']} crust skirts on their sides (steep, 1.15-1.75, "
             "`steep_floor`: the party slides back into the lava; the floor-0 banks' skirts walkable), each edge its "
             "own run, so the outlines are broken and no side reads as an extruded plate. Steep skirts' crust is "
             "drawn out down the slope (`uneven`).")
    T.append(f"- Rock over the lava: {f['rock_area_m']} M units; the hall's sky raised to 2,760 (the notch's corners).\n")
    T.append("## Wiring (A3's hooks by name)\n")
    T.append(f"- `evt:test` (step, the test's plate): 'Accept the test of Fire?' Yes: `m38.test_fire`, show group "
             f"{gen.GUARD_GROUP}, map_var test_accepted. Not asked while test_accepted or qbit 111764 is set.")
    T.append(f"- `evt:test_check` (every 1 s while accepted and not passed): `Xeen.planeTestCheck(\"fire\", "
             f"{gen.GUARD_GROUP})` (A3; runs `m38.test_fire_passed` once the three are dead: qbit 111764 and its line).")
    T.append("- `evt:gate_open` (every 1 s once the qbit is set) and `evt:passed_load` (load, P-1): open the gate; the "
             "load event also hides group 60 (the pit quiet). `evt:gate`: the leaves never move by hand.")
    T.append("- `evt:vents`, `evt:spire`, the two chests (treasure 6; the ember cache trapped, level 8).")
    T.append("- `evt:way_up` (the heat column's fissure in the cliff at the Cinder Shelf): **sealed** with a line until "
             "xeen_d7.blv is installed and lists entrance:p1_return (`P1_D7_LIVE`, D4's pattern); then the `exit` "
             "preset (D-24) with A3's `m38.way_up_fire` as its meaning.\n")
    T.append("## Figures (`output/studio_cal/p1/measure.json`)\n")
    T.append("| Figure | Target | L4 |\n| --- | --- | --- |")
    T.append(f"| Monsters | 30 (27 + the test's 3) | **{f['monsters']}** ({f['monsters_hidden']} hidden) |")
    T.append(f"| Kill XP per member | D-58 31.54k | **{f['kill_xp_per_member'] / 1000:.2f}k** |")
    T.append("| POIs (L1 census) | C8 10-12 | 10 (S's statue, sleeper, pedestal and dais placed, session 20; "
             "the Ember Font and the burnt camp, session 25) |")
    T.append("| Chests | 2 at treasure 6 | 2 (the test's chest in the hall; the trapped ember cache) and the camp's find "
             "(2 Fire Resistance, 256) |")
    T.append(f"| P-2 lips | at least 192 | the hall's walls {f['p2']['hall_walls_over_lava']:,} over the lava and "
             f"{f['p2']['hall_walls_over_its_floor']:,} over its floor (to the sky); the gate's sill "
             f"{f['p2']['gate_sill_over_lava']} over the lava; no floor higher than the hall's (the Crucible 258) |")
    T.append(f"| First fight from the arrival | 1,500-4,000 | {f['first_fight']:,} (pop:statue_lesser) |")
    T.append(f"| Walkable area | 44-51 M (C1) | {f['walkable_area_m']} M units (crater {f['crater_area_m']} M) |")
    T.append(f"| Lava | the element's ground | {f['lava_area_m']} M, {round(100 * f['lava_share'])} % of the crater; "
             f"to the nearest way out (a floor-0 bank or a ramp's foot) at most {f['lava_to_way_out_max']:,}, 90 % "
             f"within {f['lava_to_way_out_p90']:,} |")
    c = f['build']
    T.append(f"| Build | - | {c['sectors']} sectors, {c['faces']} faces, {c['vertices']} vertices, {c['portals']} "
             f"portal, {c['doors']} door records, {c['events']} events (no triangle count from the build; faces "
             "are convex polygons) |")
    T.append("| Audit | 0 errors | 0 errors, 0 warnings; info: `gcav2flr` squashed on the steep skirts (meant, "
             "`uneven`), `vlcwl3a` on 2 faces (the seam's ends), `p1_spire` set by A3's hook Lua and read there |\n")
    T.append("## Playtests (headless, the scratch root, `run.sh`, N=2)\n")
    names = {'playtest': 'the walk: arrival, the statue\'s spot, the islet, the Crucible, the bridge; the gate shut',
             'playtest_hostility': '27 hostiles placed and hostile, the three guardians hidden, a quiet arrival',
             'playtest_lava': 'standing on lavtyl the HP drops, on the crust it does not; out of the lava onto a '
                              'floor-0 shelf',
             'playtest_test': "the test: Yes raises the guardians, their deaths set 111764 and open the gate, into the "
                              "hall; after a save and reload the gate open, the guardians dead",
             'playtest_bypass': "P-2: a party in the lava pushed west into the hall's east wall (north of the gate's "
                                'frame) and north into its south wall stays in the lava'}
    for k, v in names.items():
        ok, n = t.get(k, [0, 0])
        T.append(f"- `{k}.yml`: {v}: **{ok} of {n}**.")
    T.append("\nLogs: `output/studio_cal/p1/xrun/` (the N=2 run named in `tests_look.log`; before the look pass "
             "`tests_n2.log`).\n")
    T.append("## Tour\n")
    T.append("`output/studio_cal/p1/pics/contact_t2.png` (shots in `pics/t2/`, `tour2.yml`, `tour.sh`): the arrival, "
             "the Crucible, the gate's frame, the crater from above, the Glass Shelf's fall in its gully, the Vent "
             "Field, the north-east fall, the south cliffs. Before the look pass: `contact_t1.png`.\n")
    T.append("## Deviations from L1 (each one line)\n")
    T.append("- Lava at -40, not -64: the floor-0 shelves are then a step (the engine's step is 50) out of the lava.")
    T.append("- The gate stands in the Sleeper's Hall's wall at the bridge's far end, not at the Crucible's west rim: a "
             "door needs a wall, and the hall as its own room makes P-2 hold by construction.")
    T.append("- The Glass Shelf's top is `xpfglass` (L1: black glass); the vents' plates stand 4 over their shelf.")
    T.append("- The spire's gem device keeps its one-time gem (A3's planes.spire); C8's 'one find' is the camp.\n")
    T += PC.notes_section('fire', [
        "- P1 had no dais: `platform:dais` (black glass, 224, 8 high) added in the Sleeper's Hall at L1's exit:dais "
        "(-4864, 3904), as on P2-P4, its exit to D7's `entrance:p1_return` (A3's `m38.dais_fire`).",
        "- S's heat column at the foot of the molten sheet's middle (on the lava, 4 off the wall, facing out); it "
        "asks like the sheet (`evt:way_up_column`). The walk now stops before the statue (solid) and reads Step One.",
        "- The studio's `liquid and flow` warning now counts the three decorations in the lava room (224 wanted, 3 "
        "not found: the map's 221 liquid faces all found, as before): A1."])
    T.append("## The Ember Font and the burnt camp (session 25)\n")
    T.append("- S's `xeen_emberfont` (row 4056, radius 90, solid) on the islet at (-1152, -448), z 96, facing 0; "
             "clicked, `evt:font`: A3's `planes.font` (once a day for the party, +20 Fire resistance until rest; "
             "`playtest_daily.yml`, written by `output/studio_cal/a6/s25/gen_daily.py`).")
    T.append("- S's `xeen_firecamp` (row 4057, radius 0: walked over) at (-3968, -4736), z 0, facing 90; clicked, "
             "`evt:camp`: A3's `planes.camp` (the note). The find (2 Fire Resistance) lies by the bedroll; the ember "
             "cache 870 north-west.")
    T.append("- `light:font`: a warm pulsing light 200 over the islet at the font (radius 720-800, [255, 120, 40]); "
             "S's pieces carry no light. A scene light: the build counts 0 light records.\n")
    T.append("## The batter and the way up's vent (sessions 28-29, G3 review rows 57 and 34)\n")
    c = f['cliffs']
    T.append(f"- **Batter** (`gen.py` `batter()`, replacing the scree wedges): along every plain rim wall, pieces "
             f"420-760 long, each a stack of rock tiers rising toward the wall: {c['batter']} scree feet (480-900 up the "
             f"wall, at most half the wall there, slopes 1.15-1.5, crust tops), {c['batter_ledges']} ledges with an "
             f"upright face and a top leaning back, {c['batter_steps']} steps higher and narrower again; every piece "
             f"its own depth, heights and front line. {c['ribs']} ribs of basalt columns (`vlcwl2`) stand at joints "
             "and climb most of the way up. Each tier's back stands its own distance off the wall (ledge 2, rib 9, "
             "feet 16 and 23 in turn, step 30) and the ledges and steps stand from the lava, so no faces share a "
             "plane and nothing rests on nothing (session 29).")
    T.append("- **The way up's vent** (`way_up_vent()`, row 34: the heat shimmer was lost against the lava): a disc "
             "of molten rock (`orfyrlga`, burning by `floors`) at the heat column's foot in a low lip of black glass "
             "(16-32 over the disc), two obsidian shards either side of the fissure's mouth, seen across the crater, "
             "and `light:way_up` (pulsing, radius 960-1,100).")
    T.append("- Installed 17:23 (stage 18 of 18 runs, N=2); from assets_dev 9 of 9; audit (`--dressing`) 0 errors, 0 "
             "warnings, faces in one plane 0. Before/after "
             "`output/studio_cal/a6/s29/p1/sheet_p1_before_after.jpg`.\n")
    T.append("## Blocked (no stand-ins)\n")
    T.append("- None. The elementals' look (checked in game, session 30, `output/studio_cal/a6/s30/p1/sheet.jpg`): "
             "the fire elementals (11620-11623) draw on S's `xeen_fie1` flame body (MM6's fie1, skins fie1_a/b/c, the "
             "Guardian's xfie_d), the Lava Golems (11593) on their golem model; every actor textured, none a "
             "placeholder (the session-21 line read the gold-cored flames as placeholders).\n")
    T.append("## Dressing exceptions\n")
    T.append("None: no props. The basalt columns, spurs, ledges, needles, scree, skirts, the falls' boulders and the "
             "gate's frame are terrain, off every walking line (the skirts lie beside the causeways and ramps, never "
             "on them).\n")
    (L4 / 'NOTES.md').write_text('\n'.join(T))


if __name__ == '__main__':
    f = figures()
    notes(f)
    print(json.dumps({k: v for k, v in f.items() if k not in ('build', 'p2')}))
