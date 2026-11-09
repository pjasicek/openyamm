"""
Thronheim (the region) map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/
SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests and ForadWorld.scr
(devdocs/mm9_rework/REGIONS_FINISH.md step 2; the behaviour spec of every script is work/scr_spec.md). RUDE exits are
event 50000 + the DAT object index (game/mm9/Mm9RudeDialogue.h).

- Bikki Yrsadotir (NPC244.scr, RUDE 244): Yrsa's daughter. Once the party gave her the prize from the Thing (her
  dialogue gives key 95), leaving the dialogue pays 53 000 experience and takes the prize (item 395), key 186.

Not here: the voice lines on a click (NPC244.scr and NPCShopkeeper.scr OnUse; the dialogues and the shop work) and
StatStone0 (not placed).
"""

from __future__ import annotations

from quest_xp import balanced_experience, experience_note


def rude_exit(build, name: str) -> int:
    return 50000 + build.source.by_name[name.lower()]["index"]


def extend(hooks, build, script) -> None:
    bikki = "CommonerHumanFemaleA0"
    lines = [
        "-- NPC244.scr :OnRude -> :Prize (Bikki Yrsadotir, RUDE 244): the prize delivered (key 95): 53 000 experience,",
        "-- the prize (item 395) taken, key 186.",
        f"handlers[{rude_exit(build, bikki)}] = function()",
        f"    if has(95) and not has(186) then reward(186, {balanced_experience(53000, 186)}, 0); "
        f"MM9.takeItem(395, \"thronheim:Bikki\") end{experience_note(53000, 186)}",
        "end",
        "",
    ]
    script.add(lines, (rude_exit(build, bikki), "Bikki Yrsadotir", None))
