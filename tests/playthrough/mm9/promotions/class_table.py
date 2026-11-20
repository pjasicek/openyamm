#!/usr/bin/env python3
"""
Writes the class-table segments of the MM9 promotion playthrough (README "What is checked" 5): 90-95 (block G, the
promoters reached from the Chapter II chain) and 77, 84 (block E's branch: Grehgknak and the Green Man). Rerun it
after a change to MM9.Promotions (assets_dev/worlds/mm9/events/common/mm9_common.lua) and update its tables here.

    python3 tests/playthrough/mm9/promotions/class_table.py [--e-members N]

Each round gives the members a row's "from" classes (a logged test setup through SetPlayerClass, not a cheat for a
quest), picks the promoter's "Promote our eligible characters." (his quest is done) and asserts every member's class;
picked again, it has nobody left. A four-class round is played in chunks of the party's size; a chunk that promotes
nobody must answer "No one among you can take this promotion now.". The party's own classes are kept at the
segment's start (class ids in global variables, which outlive map changes) and put back at its end. --e-members is the party size at block E's
start (the main run's 60_krohn: 4 for the new game's party, 2 for the user's old save).
"""
import argparse
from pathlib import Path

OUT = Path(__file__).resolve().parent
CP = "output/playthrough/mm9/promotions/checkpoints/"
parser = argparse.ArgumentParser()
parser.add_argument("--e-members", type=int, default=4)
parser.add_argument("--g-start", default=CP + "63_johannes_no_one.oysav", help="the checkpoint segment 90 loads")
ARGS = parser.parse_args()
MEMBERS = 4
E_MEMBERS = ARGS.e_members
START = ARGS.g_start

ENTRIES = {
    "sturmfordcity.blv": ["  - travel: {map: sturmford.blv, days: 4}",
        "  - set_pose: {map: sturmford.blv, x: 8090, y: -3312, z: 252, yaw: 3.1416, pitch: 0}",
        "  - advance_runtime: {seconds: 0.5}",
        "  - walk_to: {x: 7300, y: -3312, z: 400, z_tolerance: 500, radius: 10, plan: false, timeout_seconds: 20, expect: dialog}"],
    "thronheimcity.blv": ["  - travel: {map: thronheim.blv, days: 3}",
        "  - set_pose: {map: thronheim.blv, x: 1392, y: 6100, z: 1279, yaw: 1.5708, pitch: 0}",
        "  - advance_runtime: {seconds: 0.5}",
        "  - walk_to: {x: 1392, y: 6498, z: 1279, timeout_seconds: 20, expect: dialog}"],
    "drangheimcity.blv": ["  - travel: {map: drangheim.blv, days: 3}",
        "  - set_pose: {map: drangheim.blv, x: 11458, y: -4164, z: 757, yaw: 0, pitch: 0}",
        "  - advance_runtime: {seconds: 0.5}",
        "  - walk_to: {x: 12032, y: -4164, z: 963, timeout_seconds: 30, expect: dialog, clear_hostiles: 2000}"],
    "guberlandcity.blv": ["  - travel: {map: guberland.blv, days: 3}",
        "  - set_pose: {map: guberland.blv, x: 6131, y: -9700, z: 1651, yaw: 1.5708, pitch: 0}",
        "  - advance_runtime: {seconds: 0.5}",
        "  - walk_to: {x: 6131, y: -9194, z: 1651, z_tolerance: 600, plan: false, timeout_seconds: 20, expect: dialog, clear_hostiles: 2000}"],
    "thjorgardcity.blv": ["  - travel: {map: thjorgard.blv, days: 3}",
        "  - set_pose: {map: thjorgard.blv, x: -9300, y: 4392, z: 1951, yaw: 0, pitch: 0}",
        "  - advance_runtime: {seconds: 0.5}",
        "  - walk_to: {x: -8790, y: 4392, z: 1951, z_tolerance: 600, plan: false, timeout_seconds: 20, expect: dialog, clear_hostiles: 2000}"],
    "frosgardcity.blv": ["  - travel: {map: frosgard.blv, days: 3}",
        "  - set_pose: {map: frosgard.blv, x: 1783, y: 3700, z: 1738, yaw: -1.5708, pitch: 0}",
        "  - advance_runtime: {seconds: 0.5}",
        "  - walk_to: {x: 1783, y: 3250, z: 1738, timeout_seconds: 20, expect: dialog}"],
}

# promoter: (promotion, rude, map, actor, (x, y, z), rounds [(set, promoted)])
PROMOTERS = {
    "fridleif": ("Gladiator", 61, "sturmfordcity.blv", 31, (5775, 4603, 20565), [
        ("Cavalier Initiate Minotaur Troll", "Champion Master MinotaurLord WarTroll"),
        ("Dragon Knight Rogue Champion", "GreatWyrm Knight Rogue Champion")]),
    "thorfinn": ("Mercenary", 240, "thronheimcity.blv", 6, (11851, 2244, 3124), [
        ("Knight Thief Archer Sorcerer", "Cavalier Rogue WarriorMage Sorcerer")]),
    "keith": ("Crusader", 89, "drangheimcity.blv", 7, (14909, -5947, 1486), [
        ("Paladin Ranger Monk Knight", "Crusader Hunter Initiate Knight")]),
    "atli_quick": ("Assassin", 88, "drangheimcity.blv", 33, (16220, -3154, 431), [
        ("Rogue Vampire Thief Cavalier", "Assassin Nosferatu Thief Cavalier")]),
    "tjolnir": ("Healer", 128, "guberlandcity.blv", 11, (-4751, -6717, 62), [
        ("Cleric Druid Sorcerer Priest", "Priest GreatDruid Sorcerer Priest")]),
    "slemnir": ("Priest", 129, "guberlandcity.blv", 9, (-6226, -6226, 1), [
        ("Priest Cleric GreatDruid Wizard", "PriestLight Cleric GreatDruid Wizard")]),
    "tymon": ("Scholar", 161, "thjorgardcity.blv", 13, (4915, 12780, 1), [
        ("Sorcerer Cleric Wizard Knight", "Wizard Cleric Wizard Knight")]),
    "johannes": ("Mage", 4, "thjorgardcity.blv", 0, (5079, 12452, 1), [
        ("Wizard Sorcerer Lich Priest", "ArchMage Sorcerer Lich Priest")]),
    "paladin": ("Paladin", 282, "lindisfarnemonastery.blv", 1, None, [
        ("Crusader Paladin Hunter Cavalier", "Hero Paladin Hunter Cavalier")]),
    "druid": ("Druid", 221, "frosgard.blv", 36, (-18078, 22282, 1773), [
        ("GreatDruid DarkElf Druid Priest", "ArchDruid Patriarch Druid Priest")]),
    "fenja": ("Ranger", 181, "frosgardcity.blv", 45, (4260, 4424, -5), [
        ("Hunter WarriorMage Ranger Archer", "RangerLord MasterArcher Ranger Archer")]),
}

SEGMENTS = [
    ("90", "sturmford_fridleif", "Sturmford City: Fridleif Gjukissen (Gladiator), two rounds: the five racial and Cavalier/Initiate lines", ["fridleif"]),
    ("91", "thronheim_thorfinn", "Thronheim City: Thorfinn Skullsplitter (Mercenary)", ["thorfinn"]),
    ("92", "drangheim_keith_atli", "Drangheim City: Keith Bloodaxe (Crusader) and Atli the Quick (Assassin)", ["keith", "atli_quick"]),
    ("93", "guberland_tjolnir_slemnir", "Guberland City: Tjolnir the Super-neat (Healer) and Gray Slemnir (Priest)", ["tjolnir", "slemnir"]),
    ("94", "thjorgard_tymon_johannes", "Thjorgard City: Tymon the Nord (Scholar) and Johannes Bem (Mage)", ["tymon", "johannes"]),
    ("95", "frosgard_fenja", "Frosgard City: Fenja Tree-friend (Ranger)", ["fenja"]),
]


TABLE = {key: (p[0], p[1], p[3], p[5]) for key, p in PROMOTERS.items()}

def set_classes(names):
    lua = " ".join(f"if not SetPlayerClass({i}, '{n}') then error('SetPlayerClass({i}, {n})') end"
                   for i, n in enumerate(names.split()))
    return f'  - lua_event: {{source: "{lua}"}}'


def check(expected, label):
    return (f"  - play_lua: {{source: 'local c = classes() log(\"CLASSES {label}: \" .. c) "
            f"if c ~= \"{expected}\" then error(\"expected {expected}, got \" .. c) end'}}")


KEEP = [
    "  # The party's own classes, kept for the end (class ids in global variables; the names remembered for the check).",
    '  - lua_event: {source: "for i = 0, evt.GetPartyMemberCount() - 1 do evt.SetGlobalVar(\'Playthrough.Class\' .. i, GetPlayerClass(i)) end"}',
    "  - play_lua: {source: 'remember(\"classes_start\", classes()) log(\"CLASSES at start: \" .. classes())'}",
]
RESTORE = [
    "", "  # The party's own classes back.",
    '  - lua_event: {source: "for i = 0, evt.GetPartyMemberCount() - 1 do if not SetPlayerClass(i, evt.GetGlobalVar(\'Playthrough.Class\' .. i, -1)) then error(\'restore \' .. i) end evt.SetGlobalVar(\'Playthrough.Class\' .. i, 0) end"}',
    "  - play_lua: {source: 'local c = classes() log(\"CLASSES restored: \" .. c) if c ~= recall(\"classes_start\") then error(\"expected \" .. recall(\"classes_start\") .. \", got \" .. c) end'}",
]


def rounds(key):
    promotion, rude, actor, table = TABLE[key]
    lines = []
    number = 0
    for before, after in table:
        b, a = before.split(), after.split()
        for start in range(0, len(b), MEMBERS):
            number += 1
            cb, ca = " ".join(b[start:start + MEMBERS]), " ".join(a[start:start + MEMBERS])
            promoted = cb != ca
            lines += [f"  # Round {number}: {cb} -> {ca}.", set_classes(cb), check(cb, f"{promotion} round {number} set"),
                      f"  - interact_actor: {{actor_index: {actor}}}",
                      f"  - assert: {{dialog: {{active: true, source_id: {rude}, action_label_present: \"Promote our eligible characters.\"}}}}",
                      "  - select_topic: {match_label: \"Promote our eligible characters.\"}",
                      ("  - assert: {dialog: {active: true, text_contains: \"is now a\"}}" if promoted else
                       "  - assert: {dialog: {active: true, text_contains: \"No one among you can take this promotion now.\"}}"),
                      check(ca, f"{promotion} round {number} promoted" if promoted else f"{promotion} round {number} kept")]
            if promoted:
                lines += ["  # Picked again: nobody left to promote.",
                          "  - select_topic: {match_label: \"Promote our eligible characters.\"}",
                          "  - assert: {dialog: {active: true, text_contains: \"No one among you can take this promotion now.\"}}",
                          check(ca, f"{promotion} round {number} again")]
            lines += ["  - press_action: {action: cancel_dialog}", "  - advance_runtime: {seconds: 0.3}"]
    return lines


HEADER = [
    "# Each round gives the members a row's \"from\" classes (a logged test setup through SetPlayerClass, not a cheat",
    "# for a quest), picks the promoter's \"Promote our eligible characters.\" (his quest is done) and asserts every",
    f"# member's class; picked again, it has nobody left. Written by class_table.py for a {MEMBERS}-member party",
    "# (a four-class round is played in chunks of the party's size). The party's own classes are",
    "# put back at the end.",
]


def paladin():
    stem = "77_lindisfarne_paladin_table"
    lines = [
        "# MM9 promotion playthrough 77, block E's class table (README \"What is checked\" 5): Grehgknak the Right",
        "# (Paladin, RUDE 282, actor 1) in Lindisfarne Monastery, beside whom segment 76 ended; then out of the monastery",
        "# on foot.", *HEADER,
        f"#   python3 tests/playthrough/mm9/promotions/run.py 77",
        f"id: mm9.promotions.{stem}", "title: \"MM9 promotions 77: the class table at Grehgknak the Right\"",
        "world: mm9", "mode: faithful", "tags: [mm9, playthrough, promotions]", "steps:",
        f"  - load_game: {{path: {CP}76_lindisfarne_crusades_done.oysav}}",
        "  - setup_shortcut: {kind: immortal}",
        "  - assert: {map: lindisfarnemonastery.blv, qbit_set: [90237], state_dump_named_map_var: {name: MonksHostile, value: 0}}",
        *KEEP, "", "  # Paladin: RUDE 282, actor 1.", *rounds("paladin"), *RESTORE,
        "", "  # Out the way the party came: the east wing, the crossing, the nave (along its west side: the monk Bred Gagii",
        "  # wanders its middle and east side), the narthex.",
        "  - walk_to: {x: 3000, y: 6390, z: 1, z_tolerance: 200, timeout_seconds: 60}",
        "  - walk_to: {via: [[2350, 6390, 1], [600, 6700, 1]], x: -100, y: 6700, z: 1, z_tolerance: 200, plan: false, timeout_seconds: 60}",
        "  - walk_to: {x: -100, y: 6300, z: 1, z_tolerance: 200, plan: false, timeout_seconds: 30}",
        '  - play_lua:',
        '      source: |',
        '        -- the doors close by themselves 10 s after opening: wait for them to settle and shut, then open them fresh',
        '        local function all(s) return door_state(3) == s and door_state(4) == s end',
        '        for i = 1, 60 do if all("closed") then break end wait(0.5) end',
        '        if not all("closed") then error("door 102 never shut") end',
        '        click(102)',
        '        for i = 1, 10 do if all("open") then break end wait(0.5) end',
        '        if not all("open") then error("door 102 did not open") end',
        "  - walk_to: {via: [[-100, 5600, 1], [-650, 5000, 1], [-650, 2300, 1]], x: -100, y: 1700, z: 1, z_tolerance: 200, plan: false, timeout_seconds: 60}",
        '  - play_lua:',
        '      source: |',
        '        -- the doors close by themselves 10 s after opening: wait for them to settle and shut, then open them fresh',
        '        local function all(s) return door_state(1) == s and door_state(2) == s end',
        '        for i = 1, 60 do if all("closed") then break end wait(0.5) end',
        '        if not all("closed") then error("door 101 never shut") end',
        '        click(101)',
        '        for i = 1, 10 do if all("open") then break end wait(0.5) end',
        '        if not all("open") then error("door 101 did not open") end',
        "  - walk_to: {via: [[-330, 1000, 1]], x: -328, y: -1000, z: 1, z_tolerance: 200, plan: false, timeout_seconds: 60}",
        "  - walk_to: {x: -328, y: -1393, z: 1, z_tolerance: 400, plan: false, timeout_seconds: 20, expect: dialog}",
        "  - select_topic: {match_label: \"OK\"}",
        "  - advance_runtime: {seconds: 1.0, follow_map_move: true}",
        "  - assert: {map: lindisfarne.blv, qbit_set: [90237]}",
        f"  - save_game: {{name: \"P77 Paladin class table\", path: {CP}{stem}.oysav}}", ""]
    (OUT / f"{stem}.yml").write_text("\n".join(lines))


def druid():
    stem = "84_frosgard_druid_table"
    lines = [
        "# MM9 promotion playthrough 84, block E's class table (README \"What is checked\" 5): the Green Man (Druid,",
        "# RUDE 221, actor 36) in his clearing in Frosgard, beside whom segment 82 ended. The block's last checkpoint.",
        *HEADER,
        f"#   python3 tests/playthrough/mm9/promotions/run.py 84",
        f"id: mm9.promotions.{stem}", "title: \"MM9 promotions 84: the class table at the Green Man\"",
        "world: mm9", "mode: faithful", "tags: [mm9, playthrough, promotions]", "steps:",
        f"  - load_game: {{path: {CP}82_frosgard_green_man_done.oysav}}",
        "  - setup_shortcut: {kind: immortal}",
        "  - assert: {map: frosgard.blv, qbit_set: [90280]}",
        "  - set_pose: {map: frosgard.blv, x: -18078, y: 22132, z: 1773, yaw: 1.5708, pitch: 0}",
        "  - advance_runtime: {seconds: 0.5}",
        *KEEP, "", "  # Druid: RUDE 221, actor 36.", *rounds("druid"), *RESTORE,
        f"  - save_game: {{name: \"P84 Druid class table\", path: {CP}{stem}.oysav}}", ""]
    (OUT / f"{stem}.yml").write_text("\n".join(lines))




def town_segment(number, name, story, keys, previous):
    map_ = PROMOTERS[keys[0]][2]
    stem = f"{number}_{name}"
    lines = [
        f"# MM9 promotion playthrough {number}, the class table in bulk (README \"What is checked\" 5): {story}.",
        *HEADER,
        f"#   python3 tests/playthrough/mm9/promotions/run.py {number}",
        f"id: mm9.promotions.{stem}",
        f"title: \"MM9 promotions {number}: the class table at {story.split(':')[0]}\"",
        "world: mm9", "mode: faithful", "tags: [mm9, playthrough, promotions]", "steps:",
        f"  - load_game: {{path: {previous}}}",
        "  - setup_shortcut: {kind: immortal}",
        *KEEP,
        "", f"  # To the region, then into {map_[:-4]} through its gate (outdoors the party is placed).",
        *ENTRIES[map_],
        "  - select_topic: {match_label: \"OK\"}",
        "  - advance_runtime: {seconds: 1.0, follow_map_move: true}",
        f"  - assert: {{map: {map_}}}",
    ]
    for key in keys:
        promotion, rude, _, actor, (x, y, z), _ = PROMOTERS[key]
        lines += ["", f"  # {promotion}: RUDE {rude}, actor {actor}.",
                  f"  - set_pose: {{map: {map_}, x: {x}, y: {y - 150}, z: {z}, yaw: 1.5708, pitch: 0}}",
                  "  - advance_runtime: {seconds: 0.5}", *rounds(key)]
    lines += [*RESTORE, f"  - save_game: {{name: \"P{number} class table\", path: {CP}{stem}.oysav}}", ""]
    (OUT / f"{stem}.yml").write_text("\n".join(lines))
    return f"{CP}{stem}.oysav"


previous = START
for segment in SEGMENTS:
    previous = town_segment(*segment, previous)
MEMBERS = E_MEMBERS
HEADER = [line.replace(f"for a 4-member party", f"for a {E_MEMBERS}-member party") for line in HEADER]
paladin()
druid()
