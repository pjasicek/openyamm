#!/usr/bin/env python3
"""P2's L4 figures (measure.json) and NOTES.md (A6, seventeenth session, 2026-11-21), from gen.py's geometry, the
build (build.json, the scene's actors) and a playtest log (argument; default tests_n2.log).

    python3 level_generation/projects/xeen/p2/notes.py [tests log]
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402
sys.path.insert(0, str(pathlib.Path(_REPO_ROOT, 'level_generation/projects/xeen/common/planes')))
import pieces as PC  # noqa: E402

X = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p2')
L4 = gen.BRIEF / 'L4'
LOG = Path(sys.argv[1]) if len(sys.argv) > 1 else X / 'tests_n2.log'


def area(poly):
    return abs(gen.area2([tuple(p) for p in poly])) / 2


def lips():
    """P-2: the stair's cheeks over each step (the minimum over the step's run), over the Eye at the foot; the curtain
    and the gate stones over the Eye."""
    y0 = gen.GATE_Y + 16
    run = (gen.HEAD_Y - y0) / gen.STEPS
    ya, yb = gen.GATE_Y - 16, gen.HEAD_Y - gen.INTO
    za, zb = gen.EYE_FL + 32 + gen.CHEEK_OVER + 32, gen.AERIE_FL + gen.CHEEK_OVER

    def cheek(y):
        t = max(0.0, min(1.0, (y - ya) / (yb - ya)))
        return za + (zb - za) * t

    per = []
    for k in range(gen.STEPS):
        top = gen.EYE_FL + 32 * (k + 1)
        per.append(int(min(cheek(y0 + run * k), cheek(y0 + run * (k + 1))) - top))
    return {'cheek_over_steps_min': min(per), 'cheek_over_steps_max': max(per), 'per_step': per,
            'cheek_over_eye_at_foot': int(za - gen.EYE_FL), 'curtain_over_eye': gen.CURTAIN_H,
            'gate_stones_over_eye': gen.GATE_STONE_H, 'aerie_floor': gen.AERIE_FL,
            'highest_other_floor': max(s['floor'] for s in gen.D['spaces'] if s['id'] != 'room:chamber')}


def figures():
    plats = gen.ROOMS['rooms'][0]['platforms']
    tops = sum(area(gen.TOPS[s]) for s in gen.ISLANDS)
    bridges = sum(p['size'][0] * p['size'][1] for p in plats
                  if p['id'].startswith('platform:bridge') and 'wisp' not in p['id'])
    stair = sum(p['size'][0] * p['size'][1] for p in plats if p['id'].startswith('platform:stair') and
                'cheek' not in p['id'])
    f = {'walkable_area_m': round((tops + bridges + stair) / 1e6, 1), 'island_tops_m': round(tops / 1e6, 1),
         'bridges_m': round(bridges / 1e6, 2), 'stair_m': round(stair / 1e6, 2), 'platforms': len(plats),
         'cloud_skirts': sum(1 for p in plats if '_cloud' in p['id'] or '_wisp' in p['id']),
         'crags': sum(1 for p in plats if '_crag' in p['id']), 'roots': sum(1 for p in plats if '_root' in p['id'])}
    b = json.load(open(X / 'build/build.json'))
    f['build'] = b.get('counts', {})
    scene = yaml.safe_load(open(X / 'build/xeen_p2.scene.yml'))
    acts = scene['initial_state']['actors']
    f['monsters'] = len(acts)
    f['monsters_hidden'] = sum(1 for a in acts if a.get('group') == gen.GUARD_GROUP)
    xp = sum(gen.PD.xp(next(r['level'] for r in gen.PD.ROWS.values() if r.get('id') == a['monster_info_id']))
             for a in acts)
    f['kill_xp_per_member'] = round(xp / 4)
    arr = gen.PLACE['entrance:d7_fall']['at']
    f['first_fight'] = int(min(math.hypot(a['position']['x'] - arr[0], a['position']['y'] - arr[1])
                               for a in acts if a.get('group') != gen.GUARD_GROUP))
    f['p2'] = lips()
    f['curtain'] = {'opacity': gen.CURTAIN_OPACITY, 'tint': gen.CURTAIN_TINT, 'flow': 'up'}
    (X / 'measure.json').write_text(json.dumps(f, indent=1) + '\n')
    return f


def tests():
    out = {}
    falls = ''
    if LOG.exists():
        for line in LOG.read_text().splitlines():
            if ' run ' in line:
                name = line.split()[0]
                out.setdefault(name, [0, 0])
                out[name][0] += ' exit 0 ' in line
                out[name][1] += 1
            if line.startswith('falls:'):
                falls = line
    return out, falls


def notes(f):
    t, falls = tests()
    p = f['p2']
    T = ["# P2 Plane of Air of Xeen: L4\n",
         "A6, sixteenth and seventeenth sessions, 2026-11-21. The L1 is `../L1/` with D-58 applied "
         "(`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`); the gate per D-64 (`devdocs/xeen/reviews/D64_DECISION.md`). "
         "L2-L4 are written by `output/studio_cal/p2/tools/gen.py`, the playtests by `tools/gen_playtests.py` from the "
         "build, this file and `output/studio_cal/p2/measure.json` by `tools/notes.py`. Scripts: `v.sh` (generate, "
         "fmt, validate), `b.sh` (build, playtests, scratch install, audit), `run.sh` (playtests through the lane's "
         "game slots; `tools/check_falls.py` on the fall logs), `tour.sh`, `stage_install.sh` (stage, tests, "
         "`INSTALL=1` into assets_dev).\n",
         "## What was built\n",
         "- One open-air room (`plane_air`, every face a sky face) from the safety floor -6,000 to 4,096; six islands "
         "as rough floating rock: a ragged 24-corner top slab, two shrinking tiers with their own outlines, tapered "
         "roots on Pythagorean facings to a jagged underside, crags on the rims off every walking line, untouchable "
         "cloud skirts under the rims; the Wind Statue's island packed cloud.",
         "- Five cloud-stone bridges (`7tws1f`) with untouchable wisps under them; the Stair of Wind, sixteen steps of "
         "32 from the Eye (256) to the Sleeper's Aerie (768, the highest island), with pale-brick cheeks (`t09a01`).",
         "- The Eye of the Winds: ten standing stones and the gate's two (`gn_mtl01`); between the gate's stones the "
         "curtain of wind, a translucent `xcwisp` platform with `flow: up`, opacity "
         f"{f['curtain']['opacity']}, tint {f['curtain']['tint']} (D-64), solid until qbit 111765, then hidden and "
         "passable (`evt:gate_open` on a 1 s timer, `evt:passed_load` on load: P-1).",
         "- The test's floor before S's pedestal: 'Accept the test of Air?' Yes runs A3's `m38.test_air` and shows "
         f"group {gen.GUARD_GROUP} (Sleeper's Guardian of Air 11702, two Whirlwinds 11701); `Xeen.planeTestCheck("
         "\"air\", 60)` each second sets 111765 when all three are dead.",
         "- Nine storm plates (`xpascorch`, A3's `planes.storm`), none on a bridge or in the Eye; the Singing Stones "
         "(seven hollow stones, MM8's `gwspout` once per long face, `planes.singing_stones`); the storm cairn "
         "(`planes.cairn`); the statue's plinth (`m38.plaque_air`) in the middle of its island.",
         "- Ways out (D-58 C5): the updraft in a ring of white stones by the arrival ('Ride the wind back to the "
         "Skyroads?', `leave: exit:d7_way_up`) and the return dais in the aerie, shown on `m38_air` (`leave: "
         "exit:d7_dais`); both to D7's `entrance:p2_return`.",
         "- Falls (D-58 P2 Q1): a 1 s timer sends a party under -1,500 through A3's `Xeen.skyFallTo(\"p2\")` onto the "
         "Gale Landing (`entrance:d7_fall`, -4096, -4096) from 850 above, with falling damage; the safety floor's step "
         "event does the same.\n",
         "## Figures (`output/studio_cal/p2/measure.json`)\n",
         f"- Monsters {f['monsters']} ({f['monsters'] - f['monsters_hidden']} placed hostile, {f['monsters_hidden']} "
         f"hidden); kill XP {f['kill_xp_per_member']:,} a member (D-58: 32.04k); first fight "
         f"{f['first_fight']:,} from the arrival.",
         f"- Walkable {f['walkable_area_m']} M (island tops {f['island_tops_m']} M, bridges {f['bridges_m']} M, stair "
         f"{f['stair_m']} M); {f['platforms']} platforms ({f['crags']} crags, {f['roots']} roots, "
         f"{f['cloud_skirts']} cloud skirts and wisps); build {f['build']}.",
         f"- **P-2 (measured):** the stair's cheeks stand {p['cheek_over_steps_min']} to {p['cheek_over_steps_max']} "
         f"over its steps (minimum at the last step) and {p['cheek_over_eye_at_foot']} over the Eye at the foot; the "
         f"curtain {p['curtain_over_eye']} and the gate's stones {p['gate_stones_over_eye']} over the Eye; the aerie "
         f"({p['aerie_floor']}) is the highest floor (next {p['highest_other_floor']}), so no drop reaches it. "
         "`playtest_bypass` pushes into the curtain (stays on the Eye) and round both gate stones (the party walks "
         "off the rim and is thrown back onto the Gale Landing; never on the stair).",
         "- POIs 10 (arrival and updraft, statue, Singing Stones, storm cairn, basket and cache, the Eye and the "
         "test, the gate, the aerie and sleeper, the dais); chests 2 at treasure 6 (the test's in the aerie, the "
         "trapped basket cache); the find: Air Resistance x2 by the basket.\n",
         "## Playtests (headless, `run.sh`, N=2 from assets_dev after the install of 2026-11-21 "
         f"{os.environ.get('S20_INSTALLED', '05:15')} (session 20, S's pieces); 18 of 18 in the stage before it)\n"]
    for name, (ok, n) in sorted(t.items()):
        T.append(f"- `{name}`: {ok} of {n}")
    if falls:
        T.append(f"- {falls} (`tools/check_falls.py`: HP 0.5 s after the landing equal HP 20 s later; everyone "
                 "alive).")
    T += ["\nThe falls (D-54's shape): a new party's HP is random, so each member is set to 200, 140, 140, 140 "
          "before the fall; every fall of 850 costs the level-60 party 112, 49, 69, 46 (Knight, Cleric, Archer, "
          "Sorcerer), asserted exact 0.5 s after the landing and again 20 s later. A sorcerer at under 47 HP dies "
          "of a misstep (falling damage, D-6.2).\n",
          "## Tour\n",
          "`output/studio_cal/p2/pics/contact_t1.png` (`tour1.yml`): arrival, islands from high, the statue's isle, "
          "the north bridge, the Singing Stones, the Kite Isle, the Eye from high, the gate from the test's floor and "
          "close, before and after the test (the after shots set qbit 111765 and run `event 9`, evt:gate_open), the "
          "stair, the aerie.\n",
          "## Deviations from L1 (each one line)\n",
          "- The gate is a curtain platform, not a door (D-64).",
          "- `xpastone` not made: MM8's shipped `gwspout` (pierced rock) is the Singing Stones' face.",
          "- The way-up disc moved in to (-4931, -4723) (L1's point lay 50 from the rim); the storm cairn moved in "
          "onto its island.",
          "- Island rims have 24 corners (the studio's platform limit), not 48; crags break the skyline.\n",
          *PC.notes_section('air', [
              "- The couch stands under the dome's middle (4736, 3712), not L1's (4864, 3840): there its radius met a "
              "dome column; the updraft's column over the way-up disc asks like it (`evt:way_up_column`).",
              "- The studio's `liquid and flow` warning counts the five decorations (17 wanted, 5 not found; the 12 "
              "liquid faces all found): A1."]),
          "## The wrecked basket (session 25)\n",
          "- S's `xeen_balloonbasket` (row 4058, radius 64, solid) on Kite Isle at (-3712, 4224), z 320, facing 0 "
          "(the raised side on its rocks to the north); clicked, `evt:basket`: A3's `planes.basket` (the logbook). "
          "The find lies 115 and 160 east of its middle.",
          "- The balloonist's cache moved from (-5056, 3840), 1,400 away, to (-3824, 4400), 209 north-west of the "
          "basket among its rocks, facing south-west, off the way from the bridge (the L1 design "
          "`level_generation/xeen_art/phase6/planes_design.py` and L1 rewritten): 'wedged in the basket' holds. "
          "The freed west rim took two more crags (six on Kite Isle; the kite_west fall still passes). Installed "
          f"{os.environ.get('S25_INSTALLED', '(not yet)')} (`output/studio_cal/a6/s25/`).\n",
          "## Blocked (no stand-ins)\n",
          "- None.\n",
          "## Dressing exceptions\n",
          "- None (no props; the standing stones, crags and Singing Stones are set pieces off the walking lines).\n"]
    (L4 / 'NOTES.md').write_text('\n'.join(T))


if __name__ == '__main__':
    f = figures()
    notes(f)
    print(json.dumps({k: v for k, v in f.items() if k != 'build'}, indent=None)[:900])
