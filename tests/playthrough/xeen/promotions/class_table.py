#!/usr/bin/env python3
"""
Writes the class-table segments of the Xeen promotion playthrough (README "What is checked" 5) from Xeen.Promotions
in assets_dev/worlds/xeen/events/common/xeen_common.lua. Rerun it after a change to that table or to PROMOTERS here.

    python3 tests/playthrough/xeen/promotions/class_table.py            # write the segments, print the coverage
    python3 tests/playthrough/xeen/promotions/class_table.py --coverage # print the coverage only

Every row of Xeen.Promotions (a promotion key: its "from" classes and what each becomes) is played at the promoter
that promotes later members once his quest is done (PROMOTERS: a topic, or a map hook a click calls). Two rounds per
row, each set up by a logged test setup (SetPlayerClass in a lua_event, as MM9's class table; not a cheat for a quest):

1. every "from" class of the row, the other members of classes the row must leave alone: the row's own results
   (promoted already), the other path's results for the same class (QUESTS 3.2's Light or Dark rule: a member promoted
   on one path is no longer of the class the other path's quest promotes) and the line's earlier step; the promote is
   picked, every member's class is asserted, and the promote is no longer offered (nobody left);
2. four members of such classes only: the promote is not offered at all (a hook: its line, no class changes).

The party's own classes are kept at the segment's start (class ids in global variables) and put back at its end.
Each segment is a branch: it starts from a checkpoint where the promoter's quest is done (a copy of a main chain
checkpoint, or this chain's own) and its checkpoint is used by nothing else.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COMMON = ROOT / "assets_dev/worlds/xeen/events/common/xeen_common.lua"
CLASS_EXTRA = ROOT / "assets_dev/engine/data_tables/class_extra.txt"
CP = "output/playthrough/xeen/promotions/checkpoints/"
MEMBERS = 4


def promotions() -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    """Xeen.Promotions as {key: {from: to}} in the file's order, and {key: tier} from its section comments
    ("-- tier 1", "-- tier 2, Light", "-- tier 2, Dark", "-- racial")."""
    text = COMMON.read_text()
    body = text[text.index("Xeen.Promotions = {"):]
    body = body[:body.index("\n}\n")]
    rows, tiers, tier = {}, {}, ""
    for line in body.splitlines():
        section = re.match(r"^\s*--\s*(tier 1|tier 2|racial)\b", line)
        if section:
            tier = section.group(1)
        row = re.match(r"^\s*(\w+)\s*=\s*\{([^}]*)\}", line)
        if row:
            rows[row.group(1)] = dict(re.findall(r'(\w+)\s*=\s*"(\w+)"', row.group(2)))
            tiers[row.group(1)] = tier
    return rows, tiers


def class_steps() -> dict[str, int]:
    """class_extra.txt's Step per class name, compared case- and space-blind (as Xeen.promotionTarget's classKey)."""
    steps = {}
    for line in CLASS_EXTRA.read_text().splitlines():
        cells = line.split("\t")
        if len(cells) >= 4 and cells[0].strip().isdigit():
            steps[re.sub(r"[\s_-]", "", cells[3]).lower()] = int(cells[2])
    return steps


def assert_no_crossing() -> None:
    """D-74 point 2: no "from" class of a tier-2 or racial row is a step-2 class (class_extra.txt), so a member promoted
    on one path matches no other promoter (Light/Dark: no crossing). Every "from" must be a class the table knows."""
    steps = class_steps()
    faults = []
    for key, row in ROWS.items():
        if TIERS[key] not in ("tier 2", "racial"):
            continue
        for name in row:
            step = steps.get(re.sub(r"[\s_-]", "", name).lower())
            if step is None:
                faults.append(f"{key}: {name} is not a class in class_extra.txt")
            elif step == 2:
                faults.append(f"{key}: {name} is a step-2 class (a promoted member could cross paths)")
    if faults:
        raise SystemExit("D-74 invariant broken:\n  " + "\n  ".join(faults))
    if not any(t == "tier 2" for t in TIERS.values()) or not any(t == "racial" for t in TIERS.values()):
        raise SystemExit("D-74 invariant: Xeen.Promotions' section comments (tier 2, racial) not found")


ROWS, TIERS = promotions()
assert_no_crossing()

# The talk with Valia: placed at her cottage door on X1 (segment 09's pose), the door clicked.
VALIA = ["  - set_pose: {map: xeen_x1.odm, x: 7552, y: -4332, z: 625, yaw: 1.5708, pitch: 0.0}",
         "  - advance_runtime: {seconds: 0.5}",
         "  - press_interact: {expect: {kind: event_target}}"]
# Barok's hut on X2: its house event (segment 17's way in).
BAROK = ["  - execute_event: {id: 1}"]
# Danulf at his ring of stones in X2's south woods (segment 17's pose; actor 51).
# The ring's own clear, 3,000 (D-85): session 6 cleared 9,000 because the wood's Dark Sprite spawns (3,000-9,000 away)
# Cursed and Stoned the party within seconds; X2's sprite markers were moved 5,888 clear of him (D-85, D-88), and
# A3-promo session 7 found 3,000 enough: 3 of 3 normal and 3 of 3 reload, nobody down (output/a3promo_s7/probe03.py).
DANULF = ["  - set_pose: {map: xeen_x2.odm, x: -3277, y: -8909, z: 1044, yaw: -2.16, pitch: 0.0}",
          "  - clear_hostiles: {radius: 3000}",
          "  - interact_actor: {actor_index: 51}"]
# Princess Roxanne in Castle Burlock's east tower (XD-07; segment 21's walk; her house 4204, event 42).
ROXANNE = ["  - play_lua: {source: \"click(42); wait(1)\"}"]

# Carlawna at her hut's door on X4 (segment 11's pose; house 4166).
CARLAWNA = ["  - set_pose: {map: xeen_x4.odm, x: -12210, y: 5154, z: 1376, yaw: 1.5708, pitch: 0.0}",
            "  - advance_runtime: {seconds: 0.5}",
            "  - press_interact: {expect: {kind: event_target}}"]
# The Autumn Druid in his ring on X4's savannah (A5's playtest; actor 35).
AUTUMN = ["  - set_pose: {map: xeen_x4.odm, x: -19149, y: -3584, z: 1120, yaw: 0.0, pitch: 0.0}",
          "  - clear_hostiles: {radius: 3000}",
          "  - interact_actor: {actor_index: 35}"]

# Kai Wu's Monastery on X5's crag (house 4270, event 35; segment 21's pose). Since merge point 40 (F1) a house
# whose only resident is its proprietor opens on his talk (Kai Wu, Dreyfus, Nasir, Kramer): nobody to pick.
KAIWU = ["  - set_pose: {map: xeen_x5.odm, x: 1280, y: 16660, z: 1888, yaw: 1.5708, pitch: 0.0}",
         "  - advance_runtime: {seconds: 0.5}",
         "  - press_interact: {expect: {kind: event_target}}"]
# Dimitri in the Captain's Quarters (DD-03 house 4502, event 21), beside whom the walk in ends.
DIMITRI = ["  - play_lua: {source: \"click(21); wait(0.8)\"}"]

# House talks the main chain opens the same way (its segments 49, 63, 65): placed at the door (a resident picked where
# the house has more than its proprietor).
SHARLA = ["  - set_pose: {map: xeen_d2.odm, x: -19300, y: -10839, z: 992, yaw: 2.2513, pitch: 0.0}",
          "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
          "  - press_interact: {expect: {kind: event_target}}",
          "  - select_topic: {action_id: 5101, match_label: \"Sharla\"}"]
DREYFUS = ["  - set_pose: {map: xeen_d1.odm, x: 3092, y: 2048, z: 1152, yaw: 0.0, pitch: 0.0}",
           "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
           "  - press_interact: {expect: {kind: event_target}}"]
NASIR = ["  - set_pose: {map: xeen_d3.odm, x: -13824, y: 20548, z: 1504, yaw: 1.5708, pitch: 0.0}",
         "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
         "  - press_interact: {expect: {kind: event_target}}", "  - advance_runtime: {seconds: 0.5}"]

# Astra in her house in Sandcaster (D3; house 4618, a residence of one; segment 95 ends at her door).
ASTRA = ["  - set_pose: {map: xeen_d3.odm, x: -12800, y: 20756, z: 1519, yaw: 1.5708, pitch: 0.0}",
         "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
         "  - press_interact: {expect: {kind: event_target}}", "  - advance_runtime: {seconds: 0.5}"]

# Leafpoint in his grove on D4 (segment 51's pose; actor 22).
LEAFPOINT = ["  - set_pose: {map: xeen_d4.odm, x: -11264, y: 819, z: 1504, yaw: 0.0, pitch: 0.0}",
             "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
             "  - interact_actor: {actor_index: 22}"]
# Luna in her grove on D1 (segment 85's pose; actor 47 since D1's 2026-11-25 rebuild put 15 actors before her).
LUNA = ["  - set_pose: {map: xeen_d1.odm, x: -16691, y: 717, z: 1190, yaw: 0.0, pitch: 0.0}",
        "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
        "  - interact_actor: {actor_index: 47}"]
# Kramer's Caravans on D1 (segment 47's door; it opens on Kramer's talk).
KRAMER = ["  - set_pose: {map: xeen_d1.odm, x: 3844, y: 5904, z: 1152, yaw: 0.0, pitch: 0.0}",
          "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
          "  - press_interact: {expect: {kind: event_target}}"]
# Brother Reger's cell outside Castleview's walls (segment 91: the word said, his door opens his cell; D1 event 99).
REGER = ["  - set_pose: {map: xeen_d1.odm, x: -3328, y: -15892, z: 1023, yaw: -1.5708, pitch: 0.0}",
         "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
         "  - press_interact: {expect: {kind: event_target}}"]
# Shinobu in XD-22's cellar (segment 25 ends beside her; actor 24).
SHINOBU = ["  - interact_actor: {actor_index: 24}", "  - advance_runtime: {seconds: 0.6, present_dialogs: true}"]
# Master Morbius in the Necromancers' House on D6 (segment 89; a residence of one, house 4757).
MORBIUS = ["  - set_pose: {map: xeen_d6.odm, x: 15156, y: -10496, z: 1664, yaw: 0.0, pitch: 0.0}",
           "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
           "  - press_interact: {expect: {kind: event_target}}"]
# Du Monay Manor on X3's Nightshadow square (segment 61; house of 4205).
DUMONAY = ["  - set_pose: {map: xeen_x3.odm, x: 19204, y: -1920, z: 960, yaw: 0.0, pitch: 0.0}",
           "  - advance_runtime: {seconds: 0.5}", "  - clear_hostiles: {radius: 3000}",
           "  - press_interact: {expect: {kind: event_target}}"]
# Hobstadt on his throne floor in DD-11C (segment 63; actor 12).
HOBSTADT = ["  - interact_actor: {actor_index: 12}", "  - advance_runtime: {seconds: 0.6, present_dialogs: true}"]
# Scaldrith in the Dragon Cave (XD-18; house 4852, event 18; segment 67).
SCALDRITH = ["  - play_lua: {source: \"click(18); wait(0.8)\"}"]
# The horned throne at the labyrinth's heart (DD-12 event 90; segment 65 ends on its square).
HORNED_THRONE = ["  - play_lua: {source: \"click(90); wait(0.5)\"}", "  - advance_runtime: {seconds: 0.5, present_dialogs: true}"]
# The Master Thief at his desk in DD-06's counting room (segment 55 ends there; actor 29).
MASTER_THIEF = ["  - interact_actor: {actor_index: 29}", "  - advance_runtime: {seconds: 0.6, present_dialogs: true}"]
# The Voweless Knights' plaque in DD-08's chapter hall (event 43; after the oath it runs oath_again or the oath's line).
PLAQUE = ["  - play_lua: {source: \"clear_hostiles(1800); click(43); wait(0.5)\"}",
          "  - advance_runtime: {seconds: 0.5, present_dialogs: true}"]
# The initiation cauldron in DD-20's coven hall (event 39, the map's question "Drink?"; a hook, no topic).
CAULDRON = ["  - play_lua: {source: \"click(39); wait(0.5)\"}",
            "  - assert: {dialog: {active: true, text_contains: \"Drink\"}}",
            "  - answer_input: {text: \"Yes\"}",
            "  - advance_runtime: {seconds: 1, present_dialogs: true}"]

# promoter: the Xeen.Promotions key, who, source id (None: not asserted), the talk (steps that open it), the promote's
# label (None: a map hook, the talk itself runs it), a phrase of its promote text, and for a topic whose label stays when
# nobody is eligible (its states) or a hook, a phrase of the line it says then (None: the label is offered only while
# someone is eligible)
PROMOTERS = {
    "valia": ("crusade", "Old Valia (T1-A)", 4044, VALIA, "Promotion", "Kneel, then. Knights rise as Cavaliers", None),
    "barok": ("pendant", "Barok (T1-B)", 4151, BAROK, "Promotion", "Sorcerers rise as Wizards", None),
    "danulf": ("elf", "Danulf the Faery King (Q-C17)", 4154, DANULF, "Promotion", "Rise, Patriarch.", None),
    "roxanne": ("tiara", "Princess Roxanne (T1-E)", 4404, ROXANNE, "Promotion", "Rise, Rogue.", None),
    "carlawna": ("seasons", "Carlawna (T1-C)", 4303, CARLAWNA, "Promotion", "hasn't been ordained? Kneel.", None),
    "autumn": ("seasons", "the Autumn Druid (T1-C)", 4321, AUTUMN, "Promotion", "Leaves fall so the tree can grow.",
               None),
    "kaiwu": ("pagoda", "Kai Wu (T1-D)", None, KAIWU, "Promotion", "Sit. Breathe. Stand up.", None),
    "dimitri": ("dimitri", "Dimitri (T2-A)", 5004, DIMITRI, "Quest", "Another knight in your company. Kneel.",
                "The cells are quiet. The guard can sleep"),
    "sharla": ("sprites", "Sharla (Q-D10, T2-LATER)", None, SHARLA, "Promotion", "Walk it as its lord.", None),
    "dreyfus": ("heretics", "Dreyfus (Q-D6, T2-LATER)", None, DREYFUS, "Promotion", "Crusaders rise as Heroes",
                None),
    "nasir": ("jewel", "Nasir (Q-D18, T2-LATER)", None, NASIR, "Promotion", "Wizards, take the robes.", None),
    "astra": ("quarter", "Astra (Q-D14, T2-LATER)", 5217, ASTRA, "Promotion", "Then the word is Spy.", None),
    "kramer": ("bounty", "Kramer (Q-D11, T2-LATER)", None, KRAMER, "Promotion", "Bounty Hunter. It comes with a form.",
               None),
    "leafpoint": ("leafpoint", "Leafpoint (T2-LEAFPOINT)", 5319, LEAFPOINT, "Promotion",
                  "Another druid who listens to trees.", "The wind says Thickbark has grown a new ring"),
    "thief": ("southern", "the Master Thief (Q-D19, T2-LATER)", 5109, MASTER_THIEF, "Promotion",
              "Inner circle. Don't touch the chest on your way out.", None),
    "reger": ("drawkcab", "Brother Reger (Q-D3, T2-LATER)", 4950, REGER, "Promotion", "Master you are now. Backwards, naturally.",
              None),
    "shinobu": ("clan", "Shinobu (T2-CLAN)", None, SHINOBU, "Quest", "Another one who walks quietly? Good.",
                "The old monk sweeps upstairs."),
    "morbius": ("sandro", "Master Morbius (Q-D23 released, D-74 5)", 5506, MORBIUS, "Sandro",
                "A Priest, a Wizard or a Necromancer who wants to walk where he walked: sit.",
                "Sandro is at rest. The House has his notes"),
    "dumonay": ("vampire", "Du Monay (Q-C7)", 4205, DUMONAY, "Promotion", "Rise, Nosferatu.", None),
    "hobstadt": ("troll", "Hobstadt (Q-D13's tribute, D-74 3)", 5110, HOBSTADT, "Sacrifice one",
                 "Another troll? Hobstadt take him too.", "Hobstadt has his War Troll. Go where you like."),
    "scaldrith": ("dragon", "Scaldrith (Q-C25)", 5702, SCALDRITH, "Promotion",
                  "Another dragon who reads? The office is becoming a library. Rise, Great Wyrm.",
                  "Great Wyrms are made of dragons, and you have none with you."),
    # D25-1 fixed (q-d25.yml 13:00: `throne` is a states hook without `once`, its later-Minotaur state promotes)
    "horned": ("minotaur", "the horned throne (Q-D25's later Minotaur)", None, HORNED_THRONE, None,
               "The Minotaur sits, and rises a lord of the maze.", "anyone else who sits gets a sore back"),
    "luna": ("statuettes", "Luna (Q-D20, T2-LATER)", 4952, LUNA, "Promotion", "Rise, Master Archer.", None),
    "plaque": ("knights", "the Voweless Knights' plaque (Q-D17's oath)", None, PLAQUE, None,
               "The new member says the oath without a vowel", "Th nth s swrn."),
    "cauldron": ("coven", "the coven's cauldron (Q-D22)", None, CAULDRON, None, "Another of the green ways drinks.",
                 "You have had some. It is still toad."),
}

# Castle Burlock from X4's gate (segment 21's walk: the gate, the portcullis, the hall, the east tower's stair) and back.
INTO_BURLOCK = [
    "  - assert: {map: xeen_x4.odm}",
    "  - set_pose: {map: xeen_x4.odm, x: -1024, y: 6707, z: 1760, yaw: 1.5708, pitch: 0.0}",
    "  - advance_runtime: {seconds: 0.5}",
    "  - press_interact: {expect: {kind: event_target}}",
    "  # F16: the standard entrance window.",
    "  - assert: {dialog: {active: true, action_label_present: \"OK\"}}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_xd07.blv}",
    "  - advance_runtime: {seconds: 3, present_dialogs: true}",
    "  - play_lua: {source: \"close()\"}",
    "  - walk_to: {x: 0, y: 700, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - play_lua: {source: \"click(40); wait(8); if door_state(11) ~= 'open' then error('the portcullis did not open: ' .. door_state(11)) end\"}",
    "  - walk_to: {x: 0, y: 2304, z: 0, radius: 96, timeout_seconds: 40, close_dialogs: true}",
    "  - walk_to: {x: 0, y: 3300, z: 0, radius: 96, timeout_seconds: 40, close_dialogs: true}",
    # the planner now leads east along y 3300 into a wall (2026-11-21); the hall runs north first
    "  - walk_to: {via: [[0, 5376, 0]], x: 1100, y: 5376, z: 0, radius: 64, plan: false, timeout_seconds: 40, close_dialogs: true}",
    "  - play_lua: {source: \"open_door(19, 5)\"}",
    "  - walk_to: {x: 2048, y: 5376, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 4300, y: 5376, z: 640, radius: 64, timeout_seconds: 40, close_dialogs: true}",
    "  - walk_to: {x: 4900, y: 5376, z: 640, radius: 64, timeout_seconds: 30, close_dialogs: true}",
]
OUT_OF_BURLOCK = [
    "  - walk_to: {x: 4300, y: 5376, z: 640, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 2048, y: 5376, z: 0, radius: 64, timeout_seconds: 40, close_dialogs: true}",
    "  - walk_to: {x: 1100, y: 5376, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 0, y: 3300, z: 0, radius: 96, timeout_seconds: 40, close_dialogs: true}",
    "  - walk_to: {x: 0, y: 700, z: 0, radius: 64, timeout_seconds: 60, close_dialogs: true}",
    "  - walk_to: {x: 0, y: 300, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - execute_event: {id: 8}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_x4.odm}",
]

# Castle Kalindra from D1's gate up to the Captain's Quarters (segments 59 and 31) and back out.
INTO_KALINDRA = [
    "  - set_pose: {map: xeen_d1.odm, x: -9728, y: -3072, z: 1664, yaw: 0.0, pitch: 0.0}",
    "  - clear_hostiles: {radius: 3000}",
    "  - advance_runtime: {seconds: 0.5}",
    "  - play_lua: {source: \"click(254)\"}",
    "  # F16: the standard entrance window.",
    "  - assert: {dialog: {active: true, action_label_present: \"OK\"}}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_dd03.blv}",
    "  - advance_runtime: {seconds: 4, present_dialogs: true}",
    "  - play_lua: {source: \"for _ = 1, 3 do if not close() then break end end\"}",
] + [f"  - walk_to: {{x: {x}, y: {y}, z: {z}, {extra}radius: 64, timeout_seconds: 30, clear_hostiles: 2000, close_dialogs: true}}"
     for x, y, z, extra in [(-700, 0, 0, ""), (900, 0, 0, ""), (64, 700, 0, ""), (64, 1216, 0, ""), (-1536, 1216, 0, ""),
                            (-1536, 1600, 0, ""), (-1536, 3200, 640, "z_tolerance: 60, "), (-384, 3200, 640, ""),
                            (600, 3136, 640, ""), (832, 3200, 640, "")]]
OUT_OF_KALINDRA = [
    f"  - walk_to: {{x: {x}, y: {y}, z: {z}, {extra}radius: {r}, timeout_seconds: 30, close_dialogs: true}}"
    for x, y, z, extra, r in [(600, 3136, 640, "", 64), (-384, 3200, 640, "", 64), (-1536, 3200, 640, "", 64),
                              (-1536, 1600, 0, "z_tolerance: 60, ", 64), (-1536, 1216, 0, "", 64), (64, 1216, 0, "", 64),
                              (64, 700, 0, "", 64), (-700, 0, 0, "", 64), (-1900, 0, 0, "", 48)]
] + ["  - execute_event: {id: 19}",
     "  - assert: {dialog: {active: true, action_label_present: \"OK\"}}",
     "  - select_topic: {match_label: \"OK\"}",
     "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
     "  - assert: {map: xeen_d1.odm}"]

# DD-06's getaway hatch from the counting room down the chute, and out by the front door (main 55's way out).
OUT_OF_SOUTHERN = [
    "  - walk_to: {x: 600, y: 192, z: 1920, radius: 64, clear_hostiles: 1200, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 1100, y: 192, z: 1920, radius: 48, clear_hostiles: 1200, timeout_seconds: 30, close_dialogs: true}",
    "  - play_lua: {source: \"click(22); wait(1)\"}",
    "  - assert: {party_position: {x: 1760, y: 1780, radius: 120, z_min: 0, z_max: 64}}",
    "  - play_lua: {source: \"for _ = 1, 3 do if not close() then break end end\"}",
    "  - walk_to: {x: 640, y: 1880, z: 0, radius: 48, clear_hostiles: 1200, timeout_seconds: 30, close_dialogs: true}",
    "  - play_lua: {source: \"click(17); wait(0.5)\"}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_d2.odm}",
]

# The Northern Tower from D5 (segment 35's walk: the door, L1-L4) to the oath plaque in the chapter hall, and out.
INTO_NORTHERN = [
    '  - set_pose: {map: xeen_d5.odm, x: 2560, y: 11776, z: 3008, yaw: 1.5708, pitch: 0.0}',
    '  - clear_hostiles: {radius: 3000}',
    '  - set_pose: {map: xeen_d5.odm, x: 2560, y: 11988, z: 3008, yaw: 1.5708, pitch: 0.0}',
    '  - advance_runtime: {seconds: 0.5}',
    '  - press_interact: {expect: {kind: event_target}}',
    '  - advance_runtime: {seconds: 0.5}',
    '  # F16: the standard entrance window.',
    '  - assert: {dialog: {active: true, action_label_present: "OK"}}',
    '  - select_topic: {match_label: "OK"}',
    '  - advance_runtime: {seconds: 1.5, follow_map_move: true}',
    '  - assert: {map: xeen_dd08.blv}',
    '  - advance_runtime: {seconds: 1.5, present_dialogs: true}',
    '  - play_lua: {source: "for _ = 1, 3 do if not close() then break end wait(0.3) end"}',
    '  - assert: {party_position: {x: 0, y: -1152, radius: 160}}',
    '  - walk_to: {x: 0, y: -620, z: 0, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: 0, y: -200, z: 0, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: 0, y: 60, z: 0, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: 0, y: 900, z: 448, z_tolerance: 120, radius: 64, timeout_seconds: 30, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: -400, y: 960, z: 448, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - play_lua: {source: "open_door(29, 7)"}',
    '  - walk_to: {x: -1100, y: 960, z: 448, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - clear_hostiles: {radius: 2500}',
    '  - walk_to: {x: -1300, y: 32, z: 448, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: -1984, y: 32, z: 448, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: -1984, y: 900, z: 896, z_tolerance: 120, radius: 64, timeout_seconds: 30, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: -1400, y: 960, z: 896, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: -1100, y: 128, z: 896, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: -300, y: 60, z: 896, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: 0, y: 60, z: 896, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: 0, y: 900, z: 1344, z_tolerance: 120, radius: 64, timeout_seconds: 30, clear_hostiles: 1500, close_dialogs: true}',
    '  - walk_to: {x: -400, y: 960, z: 1344, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - play_lua: {source: "open_door(26, 1)"}',
    '  - walk_to: {x: -1200, y: 960, z: 1344, radius: 64, timeout_seconds: 20, clear_hostiles: 1500, close_dialogs: true}',
    '  - clear_hostiles: {radius: 2500}',
    '  - walk_to: {x: -1500, y: 1000, z: 1344, radius: 64, timeout_seconds: 20, clear_hostiles: 1800, close_dialogs: true}',
]
OUT_OF_NORTHERN = [
    '  - walk_to: {x: -1200, y: 960, z: 1344, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: -400, y: 960, z: 1344, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: 0, y: 900, z: 1344, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: 0, y: 60, z: 896, z_tolerance: 120, radius: 64, timeout_seconds: 30, close_dialogs: true}',
    '  - walk_to: {x: -300, y: 60, z: 896, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: -1100, y: 128, z: 896, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: -1400, y: 960, z: 896, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: -1984, y: 900, z: 896, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: -1984, y: 32, z: 448, z_tolerance: 120, radius: 64, timeout_seconds: 30, close_dialogs: true}',
    '  - walk_to: {x: -1300, y: 32, z: 448, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: -1100, y: 960, z: 448, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: -400, y: 960, z: 448, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: 0, y: 900, z: 448, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: 0, y: 60, z: 0, z_tolerance: 120, radius: 64, timeout_seconds: 30, close_dialogs: true}',
    '  - walk_to: {x: 0, y: -620, z: 0, radius: 64, timeout_seconds: 20, close_dialogs: true}',
    '  - walk_to: {x: 0, y: -1300, z: 0, radius: 48, timeout_seconds: 20, close_dialogs: true}',
    '  - execute_event: {id: 37}',
    '  - advance_runtime: {seconds: 0.5, present_dialogs: true}',
    '  - play_lua: {source: "log(\'the tower gate: \' .. status())"}',
    '  - select_topic: {match_label: "OK"}',
    '  - advance_runtime: {seconds: 1.5, follow_map_move: true}',
    '  - assert: {map: xeen_d5.odm}',
    '  - play_lua: {source: "for _ = 1, 3 do if not close() then break end end"}',
]

# XD-22's cellar up the ladder, the shrine and entry halls, out by the north door (event 21) to X5 (segments 25, 21).
OUT_OF_PAGODA = [
    "  - walk_to: {x: 0, y: -1700, z: -448, radius: 40, timeout_seconds: 30, close_dialogs: true}",
    "  - climb: {ladder: cellar, timeout_seconds: 40}",
    "  - walk_to: {x: 0, y: -1350, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 0, y: -880, z: 0, radius: 48, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 0, y: -600, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 0, y: -120, z: 0, radius: 48, timeout_seconds: 40, close_dialogs: true}",
    "  - execute_event: {id: 21}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_x5.odm}",
]

# The coven hall from D4 by the Guild's back stair (segment 81: D4 event 49) to the cauldron, and back up (event 33).
INTO_COVEN = [
    "  - execute_event: {id: 49}",
    "  # F16: the standard entrance window.",
    "  - assert: {dialog: {active: true, action_label_present: \"OK\"}}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_dd20.blv}",
    "  - advance_runtime: {seconds: 1, present_dialogs: true}",
    "  - play_lua: {source: \"for _ = 1, 3 do if not close() then break end end\"}",
    "  - walk_to: {x: -128, y: -100, z: 0, radius: 48, timeout_seconds: 20, close_dialogs: true}",
]
OUT_OF_COVEN = [
    "  - walk_to: {x: -640, y: -384, z: 0, radius: 64, timeout_seconds: 20, close_dialogs: true}",
    "  - execute_event: {id: 33}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_d4.odm}",
]

# DD-11C from D2's troll hole C (segment 63's way: event 34, the log doors) to Hobstadt's floor, and out (event 12).
INTO_TROLLS = [
    "  - set_pose: {map: xeen_d2.odm, x: 1536, y: -17408, z: 928, yaw: 0.0, pitch: 0.0}",
    "  - clear_hostiles: {radius: 3000}",
    "  - advance_runtime: {seconds: 0.5}",
    "  - play_lua: {source: \"click(34)\"}",
    "  # F16: the standard entrance window.",
    "  - assert: {dialog: {active: true, action_label_present: \"OK\"}}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_dd11c.blv}",
    "  - advance_runtime: {seconds: 1, present_dialogs: true}",
    "  - play_lua: {source: \"for _ = 1, 3 do if not close() then break end wait(0.3) end; wait(2); close()\"}",
    "  - walk_to: {x: 960, y: 0, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - play_lua: {source: \"wait(1); close()\"}",
    "  - walk_to: {x: 2300, y: 0, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 3000, y: 120, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - play_lua: {source: \"for _ = 1, 3 do if not close() then break end end\"}",
]
OUT_OF_TROLLS = [
    "  - walk_to: {x: 2300, y: 0, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: 960, y: 0, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: -300, y: 0, z: 0, radius: 64, timeout_seconds: 30, close_dialogs: true}",
    "  - walk_to: {x: -1650, y: 0, z: 340, z_tolerance: 60, radius: 64, timeout_seconds: 40, close_dialogs: true}",
    "  - play_lua: {source: \"click(12); wait(0.5)\"}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_d2.odm}",
]
# The Dragon Cave from X7's mouth (segment 67: event 40, Yes) to Scaldrith's counter, and out (event 11).
INTO_DRAGON_CAVE = [
    "  - set_pose: {map: xeen_x7.odm, x: -3891, y: 16589, z: 2144, yaw: 1.5708, pitch: 0.0}",
    "  - advance_runtime: {seconds: 0.5}",
    "  - clear_hostiles: {radius: 4000}",
    "  - play_lua: {source: \"click(40); wait(0.5)\"}",
    "  - advance_runtime: {seconds: 0.3, present_dialogs: true}",
    "  # F16 (merge point 40): the standard entrance window.",
    "  - assert: {dialog: {active: true, action_label_present: \"OK\"}}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_xd18.blv}",
    "  - play_lua: {source: \"wait(2); for _ = 1, 3 do if not close() then break end end\"}",
    "  - walk_to: {x: 1984, y: -3560, z: 0, radius: 48, clear_hostiles: 1500, timeout_seconds: 40, close_dialogs: true}",
]
OUT_OF_DRAGON_CAVE = [
    "  - walk_to: {x: 140, y: -3072, z: 0, radius: 64, clear_hostiles: 1500, timeout_seconds: 40, close_dialogs: true}",
    "  - play_lua: {source: \"click(11); wait(0.5)\"}",
    "  - select_topic: {match_label: \"OK\"}",
    "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
    "  - assert: {map: xeen_x7.odm}",
]

# number, stem, what, start checkpoint, the assert of the start, promoters, steps before, steps after
SEGMENTS = [
    ("01", "valia_table", "X1: Old Valia's Crusaders (T1-A), after the main chain's segment 09", "00_main_09.oysav",
     "  - assert: {map: xeen_x1.odm, qbit_set: [110047]}", ["valia"], [], []),
    ("03", "barok_danulf_table", "X2: Barok's Promotion (T1-B) and Danulf's Patriarch (Q-C17), after segment 17",
     "00_main_17.oysav", "  - assert: {map: xeen_x2.odm, qbit_set: [110204]}", ["barok", "danulf"], [], []),
    ("05", "roxanne_table", "XD-07: Princess Roxanne's Rogues (T1-E), after segment 21; walked in and out",
     "00_main_21.oysav", "  - assert: {map: xeen_x4.odm, qbit_set: [112061]}", ["roxanne"], INTO_BURLOCK,
     OUT_OF_BURLOCK),
    ("13", "carlawna_autumn_table", "X4: Carlawna's Ordination and the Autumn Druid's The turning year (T1-C), after 11",
     "11_carlawna_scarab.oysav", "  - assert: {map: xeen_x4.odm, qbit_set: [112201]}", ["carlawna", "autumn"], [], []),
    ("23", "kaiwu_table", "X5: Kai Wu's Initiation (T1-D), after 21", "21_kaiwu_pagoda.oysav",
     "  - assert: {map: xeen_x5.odm, qbit_set: [112081]}", ["kaiwu"], [], []),
    ("33", "dimitri_table", "DD-03: Dimitri's The dungeon (T2-A), after 31; the castle walked in and out",
     "31_dimitri_test.oysav", "  - assert: {map: xeen_d1.odm, qbit_set: [114522]}", ["dimitri"], INTO_KALINDRA,
     OUT_OF_KALINDRA),
    ("41", "sharla_table", "D2: Sharla's Forest lords (Q-D10, T2-LATER), after the main chain's 49", "00_main_49.oysav",
     "  - assert: {map: xeen_d2.odm, qbit_set: [113207, 113201]}", ["sharla"], [], []),
    ("43", "dreyfus_table", "D1: Dreyfus's Mok's blessing (Q-D6, T2-LATER), after the main chain's 63", "00_main_63.oysav",
     "  - assert: {map: xeen_d1.odm, qbit_set: [113127]}", ["dreyfus"], [], []),
    ("45", "nasir_table", "D3: Nasir's Archmage's robes (Q-D18, T2-LATER), after the main chain's 65", "00_main_65.oysav",
     "  - assert: {map: xeen_d3.odm, qbit_set: [113365]}", ["nasir"], [], []),
    ("27", "shinobu_table", "XD-22: Shinobu's The clan (T2-CLAN), after 25; out of the cellar and the pagoda",
     "25_clan_return.oysav", "  - assert: {map: xeen_xd22.blv, qbit_set: [114540]}", ["shinobu"], [], OUT_OF_PAGODA),
    ("37", "plaque_table", "DD-08: the Voweless Knights' plaque (Q-D17's oath_again), after 35; the tower walked in and out",
     "35_voweless_oath.oysav", "  - assert: {map: xeen_d5.odm, qbit_set: [113344]}", ["plaque"], INTO_NORTHERN,
     OUT_OF_NORTHERN),
    ("49", "kramer_table", "D1: Kramer's Guild title (Q-D11's bounty, T2-LATER), after 47", "47_ogre_forts_burned.oysav",
     "  - assert: {map: xeen_d1.odm, qbit_set: [113228]}", ["kramer"], [], []),
    ("53", "leafpoint_table", "D4: Leafpoint's Civilized ones (T2-LEAFPOINT), after 51", "51_leafpoint.oysav",
     "  - assert: {map: xeen_d4.odm, qbit_set: [114560]}", ["leafpoint"], [], []),
    ("57", "master_thief_table", "DD-06: the Master Thief's New members (Q-D19's inner circle, T2-LATER), after 55; out",
     "55_inner_circle.oysav", "  - assert: {map: xeen_dd06.blv, qbit_set: [113385]}", ["thief"], [], OUT_OF_SOUTHERN),
    ("62", "dumonay_table", "X3: Du Monay's Nosferatu (Q-C7), after 61", "61_nightshadow_count.oysav",
     "  - assert: {map: xeen_x3.odm, qbit_set: [112143]}", ["dumonay"], [], []),
    ("64", "hobstadt_table", "DD-11C: Hobstadt's Sacrifice one (Q-D13's tribute, D-74 3), after 63; walked in and out",
     "63_hobstadt_tribute.oysav", "  - assert: {map: xeen_d2.odm, qbit_set: [113262, 113266]}", ["hobstadt"],
     INTO_TROLLS, OUT_OF_TROLLS),
    ("66", "horned_throne_table", "DD-12: the horned throne again (Q-D25's later Minotaur), after 65",
     "65_horned_throne.oysav", "  - assert: {map: xeen_dd12.blv, qbit_set: [113500]}", ["horned"], [], []),
    ("68", "scaldrith_table", "XD-18: Scaldrith's Great Wyrm (Q-C25), after 67; the cave walked in and out",
     "67_dragon_tax.oysav", "  - assert: {map: xeen_x7.odm, qbit_set: [112507]}", ["scaldrith"], INTO_DRAGON_CAVE,
     OUT_OF_DRAGON_CAVE),
    ("83", "cauldron_table", "DD-20: the coven's cauldron (Q-D22 joined), after 81; the hall walked in and out",
     "81_lakeside_coven.oysav", "  - assert: {map: xeen_d4.odm, qbit_set: [113449]}", ["cauldron"], INTO_COVEN,
     OUT_OF_COVEN),
    ("93", "reger_table", "D1: Brother Reger's Masters (Q-D3, T2-LATER), after 91", "91_drawkcab_way.oysav",
     "  - assert: {map: xeen_d1.odm, qbit_set: [113066]}", ["reger"], [], []),
    ("99", "morbius_table", "D6: Master Morbius's Sandro (Q-D23's later path, D-74 5), after 89", "89_sandros_heart.oysav",
     "  - assert: {map: xeen_d6.odm, qbit_set: [113462]}", ["morbius"], [], []),
    ("97", "astra_table", "D3: Astra's The guilds' word (Q-D14, T2-LATER), after 95", "95_wizard_quarter.oysav",
     "  - assert: {map: xeen_d3.odm, qbit_set: [113281]}", ["astra"], [], []),
    ("87", "luna_table", "D1: Luna's The altar's light (Q-D20, T2-LATER), after 85", "85_luna_statuettes.oysav",
     "  - assert: {map: xeen_d1.odm, qbit_set: [113407]}", ["luna"], [], []),
]


def ineligible(key: str) -> list[str]:
    """Classes a member may have that this row must leave alone, most telling first."""
    row = ROWS[key]
    others = [to for other, lines in ROWS.items() if other != key for f, to in lines.items() if f in row]
    own = list(row.values())
    earlier = [f for lines in ROWS.values() for f, to in lines.items() if to in row]
    pool = []
    for name in others + own + earlier + ["Peasant", "Knight", "Sorcerer", "Cleric"]:
        if name not in pool and name not in row:
            pool.append(name)
    return pool


def set_classes(names: list[str]) -> str:
    lua = " ".join(f"if not SetPlayerClass({i}, '{n}') then error('SetPlayerClass({i}, {n})') end"
                   for i, n in enumerate(names))
    return f'  - lua_event: {{source: "{lua}"}}'


def check(expected: list[str], label: str) -> str:
    want = " ".join(expected)
    return (f"  - play_lua: {{source: 'local c = classes() log(\"CLASSES {label}: \" .. c) "
            f"if c ~= \"{want}\" then error(\"expected {want}, got \" .. c) end'}}")


def rounds(promoter: str) -> list[str]:
    key, name, source, talk, label, phrase, other = PROMOTERS[promoter]
    row = ROWS[key]
    pool = ineligible(key)
    first = list(row)[:MEMBERS - 1]
    first += pool[:MEMBERS - len(first)]
    promoted = [row.get(c, c) for c in first]
    second = pool[:MEMBERS]
    who = f"source_id: {source}, " if source is not None else ""
    if label is None:
        return hook_rounds(key, name, talk, phrase, other, first, promoted, second)
    close = ["  - press_action: {action: cancel_dialog}",
             "  - play_lua: {source: \"for _ = 1, 3 do if not close() then break end end\"}"]
    lines = [f"  # {key}: {', '.join(f'{f} -> {t}' for f, t in row.items())}. {name}: \"{label}\".",
             f"  # Round 1: {' '.join(first)} -> {' '.join(promoted)}.",
             set_classes(first), check(first, f"{key} round 1 set"), *talk,
             f"  - assert: {{dialog: {{active: true, {who}action_label_present: \"{label}\"}}}}",
             f"  - select_topic: {{match_label: \"{label}\"}}",
             f"  - assert: {{dialog: {{active: true, text_contains: \"{phrase}\"}}}}",
             check(promoted, f"{key} round 1 promoted")]
    if other is None:
        lines += ["  # Nobody left: the promote is no longer offered.",
                  f"  - assert: {{dialog: {{active: true, action_label_absent: \"{label}\"}}}}"]
    else:
        lines += ["  # Nobody left: asked again, the line for a party with nobody to promote.",
                  f"  - select_topic: {{match_label: \"{label}\"}}",
                  f"  - assert: {{dialog: {{active: true, text_contains: \"{other}\"}}}}",
                  check(promoted, f"{key} round 1 again")]
    lines += [*close, f"  # Round 2: {' '.join(second)}, none of them eligible: the promote is not offered.",
              set_classes(second), check(second, f"{key} round 2 set"), *talk]
    if other is None:
        lines += [f"  - assert: {{dialog: {{active: true, {who}action_label_absent: \"{label}\"}}}}"]
    else:
        lines += [f"  - assert: {{dialog: {{active: true, {who}action_label_present: \"{label}\"}}}}",
                  f"  - select_topic: {{match_label: \"{label}\"}}",
                  f"  - assert: {{dialog: {{active: true, text_contains: \"{other}\"}}}}"]
    lines += [*close, check(second, f"{key} round 2 kept"), ""]
    return lines


# Known faults at a hook, logged as ISSUE lines where the round meets them (the asserts follow what the game shows;
# a fixed fault goes back to the right line, PLAYBOOK 2).
HOOK_ISSUES: dict[str, str] = {}
# Hooks whose lines are on the status line (D-90: q-d25.throne, `status: true`): their rounds read status(), which
# takes the lines it returns, so each line is read once.
STATUS_HOOKS = {"minotaur"}


def line_assert(key: str, text: str) -> list[str]:
    if key in STATUS_HOOKS:
        return ["  - play_lua:", "      source: |", "        local s = tostring(status())",
                f"        if not string.find(s, [[{text}]], 1, true) then error(\"status line: \" .. s) end"]
    return [f"  - assert: {{dialog: {{active: true, text_contains: \"{text}\"}}}}"]


def hook_rounds(key, name, talk, phrase, other, first, promoted, second) -> list[str]:
    """The rounds at a map hook (a click, a question): its promote line, then its line for nobody left."""
    row = ROWS[key]
    close = ["  - play_lua: {source: \"for _ = 1, 3 do if not close() then break end end\"}"]
    issue = [f"  - play_lua: {{source: \"log('{HOOK_ISSUES[key]}')\"}}"] if key in HOOK_ISSUES else []
    return [f"  # {key}: {', '.join(f'{f} -> {t}' for f, t in row.items())}. {name} (a map hook).",
            f"  # Round 1: {' '.join(first)} -> {' '.join(promoted)}.",
            set_classes(first), check(first, f"{key} round 1 set"), *talk, *issue,
            *line_assert(key, phrase),
            check(promoted, f"{key} round 1 promoted"), *close,
            "  # Nobody left: used again, the line for a party with nobody to promote.", *talk,
            *line_assert(key, other),
            check(promoted, f"{key} round 1 again"), *close,
            f"  # Round 2: {' '.join(second)}, none of them eligible: nobody is promoted.",
            set_classes(second), check(second, f"{key} round 2 set"), *talk,
            *line_assert(key, other),
            *close, check(second, f"{key} round 2 kept"), ""]


KEEP = [
    "  # The party's own classes, kept for the end (class ids in global variables; the names remembered for the check).",
    '  - lua_event: {source: "for i = 0, evt.GetPartyMemberCount() - 1 do evt.SetGlobalVar(\'Playthrough.Class\' .. i, GetPlayerClass(i)) end"}',
    "  - play_lua: {source: 'remember(\"classes_start\", classes()) log(\"CLASSES at start: \" .. classes())'}",
]
# D-82 point 5: before the rounds, no member Dead, Eradicated, Petrified, Paralyzed or Unconscious (each round reads
# every member's class); the party's conditions are logged in the report's PARTY section.
ABLE = ("local shown, down = {}, {}; for i = 0, 3 do local c = conditions(i); shown[#shown + 1] = '[' .. c .. ']'; "
        "for _, n in ipairs({'Dead', 'Eradicated', 'Petrified', 'Paralyzed', 'Unconscious'}) do "
        "if (' ' .. c .. ' '):find(' ' .. n .. ' ', 1, true) then down[#down + 1] = 'member ' .. i .. ' ' .. c; break end "
        "end end; log('PARTY NN before the class table: ' .. table.concat(shown, ' ')); "
        "if #down > 0 then error('PARTY DOWN before the class table (D-82 5): ' .. table.concat(down, ' | ')) end")
RESTORE = [
    "  # The party's own classes back.",
    '  - lua_event: {source: "for i = 0, evt.GetPartyMemberCount() - 1 do if not SetPlayerClass(i, evt.GetGlobalVar(\'Playthrough.Class\' .. i, -1)) then error(\'restore \' .. i) end evt.SetGlobalVar(\'Playthrough.Class\' .. i, 0) end"}',
    "  - play_lua: {source: 'local c = classes() log(\"CLASSES restored: \" .. c) if c ~= recall(\"classes_start\") then error(\"expected \" .. recall(\"classes_start\") .. \", got \" .. c) end'}",
]


def segment(number, stem, story, start, start_assert, keys, before, after) -> None:
    name = f"{number}_{stem}"
    lines = [
        f"# Xeen promotion playthrough {number}, the class table (README \"What is checked\" 5): {story}.",
        "# Written by class_table.py (do not edit by hand): per row of Xeen.Promotions, round 1 gives the members the",
        "# row's \"from\" classes and classes it must leave alone (a logged test setup through SetPlayerClass), picks the",
        "# promote and asserts every class; round 2 has nobody eligible and the promote is not offered. The party's own",
        "# classes are put back at the end.",
        f"#   python3 tests/playthrough/xeen/promotions/run.py {number}",
        f"id: xeen.promotions.{name}",
        f"title: \"Xeen promotions {number}: the class table, {story.split(':')[0]}\"",
        "world: xeen", "mode: faithful", "tags: [xeen, playthrough, promotions]", "steps:",
        f"  - load_game: {{path: {CP}{start}}}",
        "  - setup_shortcut: {kind: immortal}",
        start_assert,
        "  - play_lua: {source: \"for _ = 1, 3 do if not close() then break end end; for _ = 1, 3 do if held() ~= 0 then stow() end end\"}",
        *KEEP, "", *before,
        "  # D-82 point 5: no member down before the rounds (each reads every member's class).",
        f"  - play_lua: {{source: \"{ABLE.replace('NN', number)}\"}}", ""]
    for key in keys:
        lines += rounds(key)
    lines += [*RESTORE, *after, f"  - save_game: {{name: \"P{number} class table\", path: {CP}{name}.oysav}}", ""]
    (HERE / f"{name}.yml").write_text("\n".join(lines))


def coverage() -> None:
    played = {PROMOTERS[p][0]: [] for seg in SEGMENTS for p in seg[5]}
    for seg in SEGMENTS:
        for p in seg[5]:
            played[PROMOTERS[p][0]].append(f"{seg[0]} {PROMOTERS[p][1]}")
    covered = set(played)
    for key, row in ROWS.items():
        state = "; ".join(played[key]) if key in played else "no segment yet"
        print(f"  {key:10} {', '.join(f'{f}->{t}' for f, t in row.items()):40} {state}")
    print(f"{len(covered)} of {len(ROWS)} rows covered")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", action="store_true")
    args = parser.parse_args()
    if not args.coverage:
        for seg in SEGMENTS:
            segment(*seg)
    coverage()
