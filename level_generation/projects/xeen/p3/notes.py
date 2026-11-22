#!/usr/bin/env python3
"""P3's L4 figures (measure.json) and NOTES.md (A6's planes sub-agent, seventeenth session, 2026-11-21; after P1's),
from gen.py's geometry, the build (build.json, the scene's actors, an `oymap export` for the triangles) and the
playtest log named by TESTS_LOG (default tests_r1.log).

    python3 level_generation/projects/xeen/p3/notes.py
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
import subprocess
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

X = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p3')
ROOT = gen.ROOT
L4 = gen.BRIEF / 'L4'
RES = 16
HALF = 6656
INSTALLED = os.environ.get('P3_INSTALLED', '')        # e.g. "2026-11-21 at 06:10"
TESTS_LOG = X / os.environ.get('TESTS_LOG', 'tests_r1.log')


def to_px(p):
    return ((p[0] + HALF) / RES, (HALF - p[1]) / RES)


def mask(polys):
    img = Image.new('L', (2 * HALF // RES, 2 * HALF // RES), 0)
    d = ImageDraw.Draw(img)
    for poly in polys:
        d.polygon([to_px(p) for p in poly], fill=255)
    return np.array(img) > 0


def triangles():
    out = X / 'build/export.json'
    subprocess.run([str(ROOT / 'openyamm-studio/build-xeen/oymap'), 'export', str(X / 'build/xeen_p3.blv'),
                    '--out', str(out)], check=True, capture_output=True)
    m = json.load(open(out))['map']
    tex = sorted({f['texture'] for f in m['faces'] if f['texture'] and not f['texture'].startswith(('ch1', 'ch3'))})
    return sum(len(f['vertices']) - 2 for f in m['faces'] if not f['is_portal']), tex


def figures():
    plats = gen.ROOMS['rooms'][0]['platforms']
    floors = [f"platform:{gen.key(s['id'])}" for s in gen.D['spaces']]
    links = [f"platform:{gen.key(l['id'])}" for l in gen.D['links']]
    walk_ids = lambda p: (p['id'] in floors or any(p['id'].startswith(x + '_') for x in links) or p['id'].startswith(('platform:arch',
                                                                                      'platform:stair'))
                          or p['id'].endswith('_scree'))
    walk = mask([gen.foot(p) for p in plats if walk_ids(p)])
    bowl = mask([gen.BOWL])
    solid = mask([gen.foot(p) for p in plats if not p.get('base') or p['id'].endswith('_talus')
                  or '_talus' in p['id'] or p['id'].startswith('platform:talus')])
    scree = bowl & ~walk & ~solid
    px = RES * RES
    outs = mask([gen.foot(p) for p in plats if p['id'].endswith('_scree')])
    dist = ndimage.distance_transform_edt(~outs) * RES
    f = {'walkable_area_m': round(walk.sum() * px / 1e6, 1), 'bowl_area_m': round(bowl.sum() * px / 1e6, 1),
         'scree_area_m': round(scree.sum() * px / 1e6, 1), 'scree_share': round(scree.sum() / bowl.sum(), 3),
         'scree_to_slope_max': int(dist[scree].max()), 'scree_to_slope_p90': int(np.percentile(dist[scree], 90)),
         'scree_slopes': sum(1 for p in plats if p['id'].endswith('_scree'))}
    tops = [q[2] - gen.SCREE for q in gen.SKYPTS[:gen.SKY_RIM]]
    n = len(gen.BOWL)
    f['walls'] = {'outline_corners': n, 'ceiling_points': len(gen.SKYPTS), 'skyline_points': gen.SKY_RIM,
                  'tops_over_scree': [min(tops), max(tops)], 'spurs': gen.BOWL_KIND.count('tooth_nose'),
                  'leans': sum(1 for p in plats if p['id'].startswith('platform:lean')),
                  'talus': sum(1 for p in plats if 'talus' in p['id']),
                  'longest_rim_wall': int(max(math.hypot(gen.BOWL[k][0] - gen.BOWL[k - 1][0],
                                                         gen.BOWL[k][1] - gen.BOWL[k - 1][1]) for k in range(n)))}
    b = json.load(open(X / 'build/build.json'))
    f['build'] = b['counts']
    f['triangles'], f['textures'] = triangles()
    scene = yaml.safe_load(open(X / 'build/xeen_p3.scene.yml'))
    acts = scene['initial_state']['actors']
    f['monsters'] = len(acts)
    f['monsters_hidden'] = sum(1 for a in acts if a.get('group') == gen.GUARD_GROUP)
    xp = sum(gen.PD.xp(next(r['level'] for r in gen.PD.ROWS.values() if r.get('id') == a['monster_info_id']))
             for a in acts)
    f['kill_xp_per_member'] = round(xp / 4)
    arr = gen.PLACE['entrance:d7_fall']['at']
    first = min(math.hypot(a['position']['x'] - arr[0], a['position']['y'] - arr[1])
                for a in acts if a.get('group') != gen.GUARD_GROUP)
    f['first_fight'] = int(first)
    f['p2'] = {'hollow_over_scree': gen.HOLLOW_FL - gen.SCREE,
               'cheeks_over_anvil': gen.CHEEK_TOP - gen.ARENA_FL,
               'cheeks_over_steps_min': gen.CHEEK_TOP - (gen.ARENA_FL - 32),
               'cheeks_over_scree': gen.CHEEK_TOP - gen.SCREE, 'slab_over_anvil': gen.SLAB_H,
               'stair_foot_over_scree': gen.HOLLOW_FL - gen.SCREE,
               'higher_floors_near_hollow': 'the Anvil (-384) 1,146 rim to rim (L1), beyond the drop reach'}
    f['p2']['lip_min'] = min(f['p2']['hollow_over_scree'], f['p2']['cheeks_over_anvil'], f['p2']['slab_over_anvil'])
    (X / 'measure.json').write_text(json.dumps(f, indent=1) + '\n')
    return f


def tests():
    out = {}
    if not TESTS_LOG.exists():
        return out
    for line in TESTS_LOG.read_text().splitlines():
        if ' run ' in line:
            name = line.split()[0]
            out.setdefault(name, [0, 0])
            out[name][0] += ' exit 0 ' in line
            out[name][1] += 1
    return out


def notes(f):
    t = tests()
    w = f['walls']
    T = []
    head = 'installed in assets_dev' if INSTALLED else 'built in the scratch root'
    T.append(f"# P3 Plane of Earth of Xeen: L4 ({head})\n")
    T.append("A6's planes sub-agent, seventeenth session, 2026-11-21. The L1 is `../L1/` with D-58 applied "
             "(`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`); L2-L4 are written by `output/studio_cal/p3/tools/gen.py` "
             "(rooms, objects, wiring, plan, project, atmosphere), the playtests by `tools/gen_playtests.py` from the "
             "build, this file and `output/studio_cal/p3/measure.json` by `tools/notes.py`. Scripts: `v.sh` "
             "(generate, validate), `b.sh` (build, playtests, install into the scratch root, audit), `run.sh` "
             "(playtests through the lane's game slots; `tools/check_scree.py`), `stage_install.sh` (install).\n")
    if INSTALLED:
        T.append(f"Installed in assets_dev on {INSTALLED} by `INSTALL=1 stage_install.sh` (stage audit 0 errors 0 "
                 "warnings, the seven playtests 14 of 14 in the stage, `output/studio_cal/a6/s20/stage_p3.log`), "
                 "then 14 of 14 again from assets_dev (session 20, S's pieces).\n")
    T.append("## What was built\n")
    T.append(f"- **room:bowl**: one open-air room (sky `xeen_plane_earth`, MOUNTAIN), its floor the scree at "
             f"{gen.SCREE} (`vlcflore` rubble), its walls raw rock to the sky: {w['outline_corners']} corners (the "
             f"studio's limit is 64), the longest wall {w['longest_rim_wall']:,}, `ceiling_points` on every corner and "
             f"up to three more on each wall ({w['skyline_points']} skyline points, {w['ceiling_points']} in all), "
             f"jagged tops {w['tops_over_scree'][0]:,}-{w['tops_over_scree'][1]:,} over the scree; three shipped rocks "
             "by stretch (`cwb1`, `gcav1wal`, `gwspotwl`), the spurs `vlcflorb` strata.")
    T.append(f"- **The walls lean in** (D-58 P3): {w['leans']} hanging slabs high on the longer walls, each a plane "
             "whose underside rises from the wall at 1.6-1.9 for each unit to a bulging ragged lip 360-560 out over "
             f"the bowl, 280 under the skyline; {w['spurs']} spurs as teeth of the outline; {w['talus']} steep talus "
             "wedges (1.15-1.85: the party slides back) at the walls' foot and round every terrace and the Anvil "
             "(none round the Hollow, the stair, the links or the slopes), so nothing stands as an extruded plate.")
    T.append("- **The terraces**: L1's outlines as rock prisms from the scree (the bowl reads deep: the scree 1,024 "
             "under the arrival, the Hollow 768); the links ridges of rock; the Giants' Arch (link:arch_e) seven "
             f"slabs, thick at its feet, thin at its crown, the scree under it walkable; {f['scree_slopes']} scree "
             "slopes (0.62 for each unit, walkable; 448 wide) from the scree up to every terrace, none to the Anvil "
             "or the Hollow (D-58 P3 Q1).")
    T.append("- **The Anvil** (-384): bedrock (`gn_mtl03`), a jagged crack of black strata at its middle where the "
             f"guardians (11722 and two 11721) wait hidden in group {gen.GUARD_GROUP}, a ring of tapering monoliths "
             "(`gwspotwl`) with the east gate and the stair's head open; the test's plate before S's pedestal.")
    T.append(f"- **The Root Stair**: twelve steps of 32 down to the Hollow between cheeks of rock 128 thick whose tops "
             f"stand level at {gen.CHEEK_TOP} (256 over the Anvil, 288 or more over every step, 896 over the scree), "
             "two monoliths flanking its head; across the head `mover:slab`, a block of bedrock 384 high that sinks "
             "388 into the rock on qbit 111766 (L1: 'a slab of stone across its head sinks on the test').")
    T.append("- **The Sleeper's Hollow** (-768, `cfb1`): under the south wall's overhang (a hanging slab whose "
             "underside rises from 880 over the floor at the wall), nine roots of stone hanging from it; the return "
             "dais a disc of grey granite (`gn_mtl01`) shown on qbit 111762; the test's chest.")
    T.append("- **The Pillar Field**: petrified trees (a flaring root foot, a trunk tapering to a broken top, some "
             "with a knot; `gcav1wal`), the Echo Stone a hollow pillar with a sapphire vein (`xdvsaph`, once). "
             "**The Geode Hall**: split boulders, their split faces amethyst (`xpegeode`), the Heart-geode the "
             "largest. **The Giants' Quarry**: cut steps, half-cut blocks, the last block with its slate, the "
             "quarrymen's hut fallen to its footings by their strongbox. **The Dust Ledge**: packed earth, the dust "
             "shaft's foot a disc of pale stone in a ring of standing stones. **The Stone Statue**: an ashlar plinth "
             "(S's statue stands on it).")
    T.append("- **Rockfall**: nine PressurePlate platforms (`xperubble`, 192 x 192) at L1's cells, none on the walk, "
             "each calling A3's `planes.rockfall` (one time in three, 50 physical, a short camera shake).\n")
    T.append("## Wiring (A3's hooks by name)\n")
    T.append(f"- `evt:test` (step, the test's plate): 'Accept the test of Earth?' Yes: `m38.test_earth`, show group "
             f"{gen.GUARD_GROUP}, map_var test_accepted. Not asked while test_accepted or qbit 111766 is set.")
    T.append(f"- `evt:test_check` (every 1 s while accepted and not passed): `Xeen.planeTestCheck(\"earth\", "
             f"{gen.GUARD_GROUP})` (runs `m38.test_earth_passed` once the three are dead: qbit 111766).")
    T.append("- `evt:gate_open` (once, with its line), `evt:gate_keep` (every 1 s once the qbit is set: the slab came "
             "back shut after a reload without it) and `evt:passed_load` (load, P-1: the slab sunk, group 60 hidden). "
             "`evt:gate`: the slab never moves by hand.")
    T.append("- `evt:dais_hide` (load: the dais hidden and passable until qbit 111762), `evt:dais` ('Step onto the dais "
             "and return to the Skyroads?', `leave: exit:d7_dais`, locked text until 111762), `evt:way_up` ('Rise with "
             "the dust to the Skyroads?', `leave: exit:d7_way_up`): both to D7's `entrance:p3_return` (C5).")
    T.append("- `evt:rockfall` (`planes.rockfall`), `evt:geode`/`evt:geode2` (`planes.geode`, both halves), "
             "`evt:echo` (`planes.echo`), `evt:last_block` (`planes.last_block`), `evt:plaque` on the plinth "
             "(`m38.plaque_earth`), the two chests (treasure 6; the quarry cache trapped, level 8).\n")
    T.append("## Figures (`output/studio_cal/p3/measure.json`)\n")
    T.append("| Figure | Target | L4 |\n| --- | --- | --- |")
    T.append(f"| Monsters | 30 (27 + the test's 3) | **{f['monsters']}** ({f['monsters_hidden']} hidden) |")
    T.append(f"| Kill XP per member | D-58 32.04k | **{f['kill_xp_per_member'] / 1000:.2f}k** |")
    T.append("| POIs (L1 census) | C8 10-12 | 10 (S's statue, sleeper and couch, pedestal and dais placed, session "
             "20, on the plinth, plate and dais disc) |")
    T.append("| Chests | 2 at treasure 6 | 2 (the test's chest in the Hollow; the trapped quarry cache) and the last "
             "block's find (2 Earth Resistance, 259); the Echo Stone's sapphire is A3's |")
    T.append(f"| P-2 lips | at least 192 | **{f['p2']['lip_min']}** (the Hollow over the scree on every side); the "
             f"stair's cheeks {f['p2']['cheeks_over_anvil']} over the Anvil, {f['p2']['cheeks_over_steps_min']}+ over "
             f"the steps, {f['p2']['cheeks_over_scree']} over the scree; the slab {f['p2']['slab_over_anvil']} over the "
             "Anvil; the stair's foot 256 over the scree; no higher floor within the drop reach (L1) |")
    T.append(f"| First fight from the arrival | 1,500-4,000 | {f['first_fight']:,} (pop:statue_west) |")
    T.append(f"| Walkable area | 44-51 M (C1) | {f['walkable_area_m']} M units on the terraces, links, stair and "
             f"slopes; the scree {f['scree_area_m']} M more ({round(100 * f['scree_share'])} % of the bowl's "
             f"{f['bowl_area_m']} M) |")
    T.append(f"| Scree to a way up | - | at most {f['scree_to_slope_max']:,} to a scree slope's foot, 90 % within "
             f"{f['scree_to_slope_p90']:,} |")
    c = f['build']
    T.append(f"| Build | 0 warnings | {c['sectors']} sectors, {c['faces']:,} faces ({f['triangles']:,} triangles), "
             f"{c['vertices']:,} vertices, {c['doors']} door record (the slab), {c['events']} events, "
             f"{c['chests']} chests, 0 lights |")
    T.append(f"| Textures | Dungeon S cap 30, 4 new | {len(f['textures'])} distinct (the chests' own pictures aside), 2 new (`xperubble`, `xpegeode`) |")
    T.append("| Audit | 0 errors | 0 errors, 0 warnings; info: `gcav1wal` and `vlcflora` squashed on the steep tops of "
             "the leans and talus (meant, `uneven`) |\n")
    T.append(f"## Playtests (headless, `run.sh`, N=2; log `{TESTS_LOG.name}`)\n")
    names = {'playtest': "the walk: arrival, the statue's terrace, the Pillar Field, the Anvil; the slab holds",
             'playtest_hostility': '27 hostiles placed and hostile, the three guardians hidden, a quiet arrival',
             'playtest_test': "the test: Yes raises the guardians, their deaths set 111766 and sink the slab, down "
                              "the Root Stair into the Hollow; after a save and reload the slab sunk, the guardians "
                              "dead",
             'playtest_bypass': "P-2: into the slab; along both cheeks from the Anvil (off the rim into the scree); "
                                "from the scree at the Hollow's west, east and north lips and at both cheeks: always "
                                "the scree, never the stair or the Hollow",
             'playtest_scree': "a drop off the statue's terrace is a real fall (140 HP each -> [21, 88, 67, 91]); "
                               "the statue's scree slope leads back up"}
    for k, v in names.items():
        ok, n = t.get(k, [0, 0])
        T.append(f"- `{k}.yml`: {v}: **{ok} of {n}**.")
    T.append("\n## Tour\n")
    T.append("`output/studio_cal/p3/pics/contact_t3.png` (shots in `pics/t3/`, `tour3.yml`, `tour.sh`; under a bridge, the Hollow from the Anvil and the south scree in `contact_t4.png`): the arrival, "
             "the Dust Ledge from above, the statue's terrace, the Pillar Field, the Anvil from its east gate, the "
             "slab, the Root Stair, the Hollow and its overhang, the Geode Hall, the quarry, the scree under the "
             "south wall, the bowl from above. Before the look fixes: `contact_t1.png`, `contact_t2.png` (before the bridges). The sky preset resolves "
             "under the open-air BLV (brown dust, no sun).\n")
    T.append("## Deviations from L1 (each one line)\n")
    T.append("- The gate is the slab L1 names (a sinking mover), not a hinged pair: the Root Stair has no wall for "
             "leaves, and L1 says 'a slab of stone across its head sinks'.")
    T.append("- The Anvil's ring is ten monoliths plus the stair's two flanking ones (the east gate open).")
    T.append("- The terraces stand ~300 off the bowl's wall (the rim keeps 300 clear of every footprint): a narrow "
             "drop to the scree behind them.")
    T.append("- The way-up disc moved in to (-4710, 4736) (L1 (-4864, 4864) is near the ledge's edge).\n")
    T += PC.notes_section('earth', [
        "- `m38.sleeper_earth` on `xeen_sleeper_earth` sets 111762 (the playtest wakes him); S's dust shaft on the "
        "way-up disc asks like it (`evt:way_up_column`)."])
    T.append("## Blocked (no stand-ins)\n")
    T.append("- None of S's pieces.")
    T.append("- **The elementals' look**: S's tier skins and bindings (D-47/C6).\n")
    T.append("## Dressing exceptions\n")
    T.append("None: no props. The monoliths, trees, boulders, quarry blocks, hut footings, talus, leans, roots and "
             "the stair's cheeks are terrain, off every walking line.\n")
    (L4 / 'NOTES.md').write_text('\n'.join(T))


if __name__ == '__main__':
    f = figures()
    notes(f)
    print(json.dumps({k: v for k, v in f.items() if k not in ('build', 'textures')}))
