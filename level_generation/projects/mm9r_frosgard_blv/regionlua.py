"""
Frosgard (the region) map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/
SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors and chests (Frosgard's DAT
has no ForadWorld.scr object) (devdocs/mm9_rework/REGIONS_FINISH.md step 2; the behaviour spec of every script is
work/scr_spec.md). RUDE exits are event 50000 + the DAT object index (game/mm9/Mm9RudeDialogue.h).

- The Green Man (NPC221.scr, RUDE 221): the Druid promotion. His tasks done (his dialogue gives key 279), leaving the
  dialogue pays 63 000 experience, 5 000 gold and item 213 (key 280) and promotes every character who chose to be
  promoted (keys 445-448, one per character) to Druid.

Not here: the jumping Yetis (Jumper.Scr on Yeti6-9: they leap off the cliffs at the party; they are placed as
ordinary Yetis, the jump is monster AI), the Green Man's voice line on a click and wandering (NPC221.scr OnUse,
BaseWander) and StatStone0 (not placed).
"""

from __future__ import annotations

from quest_xp import balanced_experience, experience_note


def rude_exit(build, name: str) -> int:
    return 50000 + build.source.by_name[name.lower()]["index"]


def extend(hooks, build, script) -> None:
    green_man = "GreenMan0"
    lines = [
        "-- NPC221.scr :OnRude -> :Promo, :PromoteDruid (the Green Man, RUDE 221): his tasks done (key 279): key 280,",
        "-- 63 000 experience, 5 000 gold, item 213; each character holding key 445-448 becomes a Druid (key taken).",
        f"handlers[{rude_exit(build, green_man)}] = function()",
        "    if has(280) or not has(279) then return end",
        f"    reward(280, {balanced_experience(63000, 280)}, 5000); MM9.giveItem(213, \"frosgard:GreenMan\")"
        f"{experience_note(63000, 280)}",
        "    MM9.promoteParty(\"Druid\")   -- every eligible member (not MM9's per-character keys 445-448)",
        "end",
        "",
    ]
    script.add(lines, (rude_exit(build, green_man), "The Green Man", None))
