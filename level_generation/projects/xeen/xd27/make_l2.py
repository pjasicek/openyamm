#!/usr/bin/env python3
"""XD-27: writes L2 (plan + project) from L1 by adding the specification fields (themes, light, palette, furniture,
levels, mechanisms, atmosphere). Run once; L2 is then the source for L3."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path
import yaml

R = Path(_REPO_ROOT)
L1 = R / 'devdocs/xeen/briefs/xd27/L1'
L2 = R / 'devdocs/xeen/briefs/xd27/L2'
plan = yaml.safe_load((L1 / 'plan.yml').read_text())
proj = yaml.safe_load((L1 / 'project.yml').read_text())
plan['level'] = 'L2'

ROCK = "den_rock: MM8 Dire Wolf Den (d08) brown cave rock gcav1wal on walls and roof, its grey-brown floor rock gcav1flr underfoot"
TIMBER = "d08's timber: t68a10a planks and posts, t68a11 beams, t68a10c iron bands, the t68a13 nine-part plank door"
spec = {
    'room:mouth': dict(
        extent=[1408, 1088],
        theme=ROCK + "; the exit panel in the south wall is daylight (xodaylt, the Xeen hills view made for XD-05)",
        light="daylight from the south: the map's lightest ambient; two skull torches by the gate",
        palette=["torskul0: skull torches on poles either side of the gate", "sklplrev: skull piles at their feet",
                 "7dec18, dec19, dec29: scattered bones", "6rock02, 6rock05: fallen boulders along the walls",
                 "Corpse04: a drowned boatman's body by the midden crack"],
        furniture=["the log gate (two leaves of the d08 plank door, iron-banded) across the inner end"],
    ),
    'room:midden': dict(
        theme=ROCK + "; refuse heaps", light="unlit but for the mouth's daylight at its foot",
        palette=["trasheap, 7dec10, 7dec01: refuse and gnawed-bone heaps", "dec29, 7dec18: bones", "7dec20: a skull"],
        population=[{'slot': 2, 'groups': 1, 'per_marker': [2, 3], 'levels': [14, 14], 'strength': 'pack', 'rank': 'b',
                     'notes': "Dogs gnawing bones at the bend."}],
    ),
    'room:bone_den': dict(
        theme=ROCK, light="dim: one campfire in the middle of the den",
        palette=["7dec01, trasheap: sleeping heaps of hides and straw", "7dec18, dec19, dec29: bones",
                 "7dec02: campfire", "dec05: a skeleton", "smlbarel: a keg"],
        furniture=["six sleeping heaps along the walls", "steps of rock down to the feast cave"],
        population=[{'slot': 1, 'groups': 2, 'per_marker': [2, 3], 'levels': [15, 15], 'strength': 'pack', 'rank': 'a',
                     'notes': "Asleep on their heaps until disturbed."}],
    ),
    'room:feast_cave': dict(
        theme=ROCK + "; the pit lined with blackened hearth stones (gcav1flr)",
        light="fire-lit: the great fire in the cooking pit, skull torches round the rim",
        palette=["dec04: log fire in the pit", "ckfyr00 + cauld00: the great cauldron over its fire",
                 "dec36, dec37, dec32: wooden plates and bowls on the benches", "7dec10, trasheap: bone heaps",
                 "7dec21, smlbarel, bigbarel: casks and kegs", "torskul0: skull torches on the rim"],
        furniture=["the cooking pit (128 deep, two steps)", "four rock benches round the rim", "spits over the fire (placeholder)"],
        population=[
            {'slot': 1, 'groups': 2, 'per_marker': [2, 3], 'levels': [15, 20], 'strength': 'heavy', 'rank': 'a',
             'notes': "Round the pit, one group each side, one of them rank b."},
            {'slot': 3, 'groups': 1, 'per_marker': [1, 2], 'levels': [20, 20], 'strength': 'light', 'rank': 'a',
             'notes': "A shaman by the cauldron."}],
    ),
    'room:gate_yard': dict(
        theme=ROCK + "; " + TIMBER, light="torchlit: the guards' campfire and two skull torches",
        palette=["7dec02: the guards' campfire", "smlbarel, 7dec21: kegs", "dec29: bones", "6rock06: a boulder"],
        furniture=["the gate's bar: a log beam across the gate in two forked posts (timber chocks)"],
        population=[{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [15, 15], 'strength': 'pack', 'rank': 'a',
                     'notes': "The gate guards round their fire."}],
    ),
    'room:kennel': dict(
        theme=ROCK + "; the hurdle of stakes in d08's posts", light="dim: the feast cave's fire through the hurdle",
        palette=["7dec01: straw bedding", "dec29, 7dec18: gnawed bones", "Bucket, foodbowl: water and food"],
        furniture=["a hurdle of stakes across the mouth with a gap", "a water trough (placeholder)"],
        population=[{'slot': 2, 'groups': 1, 'per_marker': [2, 3], 'levels': [14, 19], 'strength': 'pack', 'rank': 'b',
                     'notes': "The dogs and their pack leader."}],
    ),
    'room:chief_den': dict(
        theme=ROCK + "; the seat of boulders on a rock dais; trophies of the boats in d08's timber and canvas (t68a13a)",
        light="fire-lit: a campfire before the seat, two skull torches",
        palette=["6rock01, 6rock08, 6rock09: the boulders of the seat", "sklplrev: skull piles",
                 "7dec02: campfire", "7dec20: skulls"],
        furniture=["the Chieftain's seat of piled boulders on a dais 64 up", "oars (timber beams) and a torn sail (canvas panel) on the walls",
                   "a boat's figurehead (placeholder)", "the larder's plank door in the west wall"],
        population=[{'slot': 3, 'groups': 1, 'per_marker': [1, 2], 'levels': [20, 20], 'strength': 'light', 'rank': 'a',
                     'notes': "The Chieftain's shamans."}],
    ),
    'room:larder': dict(
        theme=ROCK + "; " + TIMBER, light="dim: one wall torch inside the door",
        palette=["bigbarel, smlbarel, 7dec21, 7dec32, dec03: the boats' casks and barrels",
                 "bag01, bag_A, floursac: sacks", "Corpse02: a carcass on the floor", "torch01: wall torch"],
        furniture=["carcasses on hooks from a beam (placeholder)", "the boats' cargo stacked against the walls"],
    ),
    'room:quarry_ramp': dict(theme=ROCK, light="unlit", palette=["dec29: bones", "6rock04: a boulder left on the way"]),
    'room:quarry': dict(
        theme=ROCK + "; rubble slopes and broken rock", light="dim: one campfire, two skull torches",
        palette=["6rock01-13, rock03, rock10: boulders in heaps and fallen", "7dec11: dirt", "7dec02: campfire"],
        furniture=["heaps of rounded boulders", "a rubble slope against the north wall", "timber levers (beams leaning on the rock)",
                   "a boulder sledge (placeholder)"],
        population=[{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [15, 15], 'strength': 'pack', 'rank': 'a',
                     'notes': "Ogres prising boulders from the wall."}],
    ),
    'room:chute': dict(theme=ROCK + "; the trough lined with d08's planks (t68a10a) between timber kerbs", light="the ledge's daylight ahead",
                       palette=["6rock03: the trap's boulder at the foot once it has fallen (geometry)"]),
    'room:river_ledge': dict(
        theme=ROCK + "; the parapet of boulders; the rack in d08's timber",
        light="daylight from the gorge (bright ambient); skull torches by the rack",
        palette=["6rock02, 6rock06, 6rock12: boulders along the parapet", "torskul0: skull torches", "dec29: bones"],
        furniture=["a parapet of boulders (96) along the open north side", "the boulder heap on a timber rack at the head of a slide in the east wall"],
        population=[
            {'actor': 'Ogre Chieftain', 'role': 'chieftain', 'groups': 1, 'levels': [20, 20], 'placed': True, 'strength': 'heavy',
             'rank': 'b', 'hostile': True, 'notes': "The Ogres family's rank b with a name; carries the larder key."},
            {'actor': 'Ogre', 'role': 'thrower', 'groups': 3, 'levels': [15, 15], 'placed': True, 'strength': 'pack', 'rank': 'a',
             'hostile': True, 'notes': "Throwers at the parapet."}],
    ),
    'room:gorge': dict(
        theme="gorge: d08's rock gcav1wal as the cliffs; MM8's flowing water (wtrtyl) far below; MM8's fair sky plansky3 (d39's indoor sky) as the roof; the hills beyond the river on the far wall's upper band (xodaylt)",
        light="bright daylight (the map's lightest ambient)",
    ),
}
for s in plan['spaces']:
    s.update(spec.get(s['id'], {}))
plan['mechanisms'] = [
    {'kind': 'log gate (two hinged leaves), barred from inside', 'count': 1},
    {'kind': 'gate bar (a beam lifted from inside)', 'count': 1},
    {'kind': 'locked plank door (the Chieftain carries the key)', 'count': 1},
    {'kind': 'boulder rack and heap (props knocked out, the heap rolls into a slide)', 'count': 1},
    {'kind': 'boulder trap in the chute (step: damage, shake, the boulder at the foot)', 'count': 1},
    {'kind': 'lair to destroy (a question)', 'count': 1},
    {'kind': 'fall into the gorge (washed out at the mouth)', 'count': 1},
]
plan['atmosphere'] = ("Dim firelit den (ambient about 18-20); the mouth and the ledge bright with daylight, the gorge brightest. "
                      "Music: cave (MM7 track 18 while the Xeen world has no music table). Sound: the river's roar on the ledge "
                      "and in the chute (a looping water sound at the gorge); the fire in the pit.")
plan['height_bands'] = [
    {'id': 'band:den', 'range': [0, 192], 'spaces': ['room:mouth', 'room:midden', 'room:bone_den', 'room:feast_cave', 'room:gate_yard',
                                                     'room:kennel', 'room:chief_den', 'room:larder']},
    {'id': 'band:works', 'range': [128, 384], 'spaces': ['room:quarry_ramp', 'room:quarry', 'room:chute', 'room:river_ledge']},
    {'id': 'band:river', 'range': [-896, -896], 'spaces': ['room:gorge']},
]
plan['notes'] = plan['notes'] + " L2: one texture family for the den and the works, MM8's Dire Wolf Den (d08, a small brown beast cave) with its own timber; the gorge outside is d08's rock with MM8's water and sky and the Xeen hills view of XD-05."
proj['notes'] = proj['notes'].replace('level L1', 'level L2')
L2.mkdir(parents=True, exist_ok=True)
for name, doc in [('plan.yml', plan), ('project.yml', proj)]:
    (L2 / name).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))
(L2 / 'diagram.txt').write_text((L1 / 'diagram.txt').read_text())
print('written')
