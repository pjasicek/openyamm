#!/usr/bin/env python3
"""
The war council's cinematic (council.py) and Knut's rant without a map conversion: the scratch root
output/mm9_rework/cinematics_pilot_root gets thronheimcity.cinematics.yml, the installed map Lua with what the changed
converter produces (the council door starts the cinematic, :War is the reward only, the cinematic block, Yrsa's and
Knut's timers), and the installed scene with the six stage actors convert.py now places (hidden, in Kira's hall, at
the end of the actor list). Then run cinematic_council_argument_play.yml / _skip.yml there (README "Cinematics").

    python3 level_generation/projects/mm9r_thronheimcity/cinematics_pilot.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import council  # noqa: E402
import cutscenes  # noqa: E402
from dungeon import bodies  # noqa: E402
from dungeon.content import INVISIBLE_BIT  # noqa: E402
from dungeon.source import facing_degrees  # noqa: E402

SCENE = Path("worlds/mm9/maps/thronheimcity.scene.yml")
HALL_FLOOR = 3277                   # Kira's hall floor (native z; KiraCold stands at 3278: floor + 1, content.actor)
HALL_SECTOR = 59                    # KiraCold's sector
# The installed actors this map's Lua names (convert.py's self.actor in the installed build)
INSTALLED = {"KiraCold": 41, "YrsatheTroll0": 42, "CommonerHuman2MaleB0": 28, "Ake": 16}
COGS = {"SvenProp": 400, "TryygvaProp": 401, "MarkeProp": 402, "ForadProp": 403, "SigmundProp": 404,
        "BjarniProp": 405, "TreatyProp": 406, "BookProp": 407, "MarkeProp0": 408, "Shield": 409}


def stage_actors(first_index: int) -> tuple[list[dict], dict, dict]:
    """The stage actors as convert.py places them (content.actor's fields, the floor and sector of the hall)."""
    objects = cutscenes.Objects.load(council.STEM)
    by_name = {name.lower(): {"index": e["index"], "class": e["class"], "properties": e["values"]}
               for name, e in objects.by_name.items()}
    frame = cutscenes.Frame(PROJECT)
    records, actor, feet = [], {}, {}
    for k, (role, o, row, title) in enumerate(council.stage_actor_objects(by_name)):
        x, y, _ = frame.point(o["properties"]["Pos"])
        position = {"x": int(round(x)), "y": int(round(y)), "z": HALL_FLOOR + 1}
        record = {"actor_index": first_index + k, "name": title, "npc_id": 0, "attributes": INVISIBLE_BIT,
                  "hp": 20, "hostility_type": 0, "monster_info_id": 9000 + row, "monster_id": 9000 + row,
                  "radius": 31, "height": 174, "move_speed": 0, "position": position,
                  "initial_yaw_units": int(round(facing_degrees(o["properties"].get("Rotation")) % 360 / 360 * 2048))
                  % 2048, "immobile": True, "sprite_ids": [0, 0, 0, 0], "sector_id": HALL_SECTOR,
                  "current_action_animation": 0, "carried_item_id": 0, "group": 1, "ally": 118,
                  "unique_name_index": 0, "draw_scale": bodies.draw_scale(9000 + row, o["properties"]) or 1.0,
                  "mm9_source_object_index": o["index"]}
        records.append(record)
        actor[role] = record["actor_index"]
        feet[role] = [position["x"], position["y"], position["z"]]
    return records, actor, feet


def main() -> int:
    installed_scene = json.loads((cutscenes.INSTALLED / SCENE).read_text())
    actors = installed_scene["initial_state"]["actors"]
    records, actor, feet = stage_actors(len(actors))
    actor.update(kira_cold=INSTALLED["KiraCold"], yrsa=INSTALLED["YrsatheTroll0"],
                 knut=INSTALLED["CommonerHuman2MaleB0"], ake=INSTALLED["Ake"])
    actors += records
    target = cutscenes.PILOT_ROOT / SCENE
    if target.exists():
        target.unlink()
    target.write_text(json.dumps(installed_scene, indent=1))

    scenes = council.scenes(actor, feet, COGS)
    lines, timers = council.extra_lua(actor)
    extra = "\n" + "\n".join(lines) + "\n" + "\n".join(
        f'RegisterMapTimerEvent({event}, seconds(3), handlers[{event}], "{title}", "", seconds(3))'
        for event, title, *_ in timers) + "\n"
    # What the changed citylua.py writes for the council door and :War (the installed file is the older converter's)
    replacements = [
        ("    if has(90) and has(91) and not has(40) then war() end",
         f"    if has(90) and has(91) and not has(40) then MM9Cinematic.start(\"{council.CINEMA_ID}\") end"),
        ("    sprite(COG.MarkeProp, false); sprite(COG.MarkeProp0, true)\n    show(42, true)\n"
         "    evt.StatusText(\"The Jarls sign the treaty. Markel the Great lies dead at Kira's feet.\")\n", ""),
    ]
    lua = cutscenes.pilot(council.STEM, scenes, replacements, extra_lua=extra)
    # Yrsa's appearance sounds the world's audio lacks (convert.py installs them into the review root)
    sys.path.insert(0, str(cutscenes.ROOT / "tools/mm9_import_discovery"))
    import generate_mm9_events as mm9_events
    index = mm9_events.build_source_sound_index(cutscenes.SOUNDS)
    for name in council.SOUNDS_USED:
        relative = mm9_events.normalize_mm9_sound_name(name).lower()
        sound = cutscenes.PILOT_ROOT / "worlds/mm9/audio" / relative
        if not sound.exists():
            sound.parent.mkdir(parents=True, exist_ok=True)
            sound.write_bytes(mm9_events.find_source_sound_path(index, relative).read_bytes())
    cinema = scenes[0].cinema
    print(f"{lua}\n{target} (+{len(records)} stage actors {records[0]['actor_index']}..{records[-1]['actor_index']})")
    print(f"{council.CINEMA_ID}: {cinema.shots_seconds:.1f} s, {len(cinema.shots)} shots, {len(cinema.cues)} cues; "
          f"steps {[(name, event) for name, _, event in scenes[0].steps]}, done {scenes[0].done_event}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
