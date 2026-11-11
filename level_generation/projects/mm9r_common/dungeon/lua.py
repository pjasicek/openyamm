"""
The map Lua scaffolding of a converted dungeon (worlds/mm9/events/maps/<stem>.lua): the door table and helpers, the
door groups' click events, the chests, map metadata and the event registrations. The map project adds its MM9
scripted objects as handlers between `begin()` and `finish()`.

    script = lua.Script(build, "Temple of Honk")
    script.doors()                      # click events of the door groups (movers.DOOR_EVENT_BASE + k)
    script.chests()                     # events CHEST_EVENT + k: evt.OpenChest(k)
    script.add(["handlers[70] = function() ... end"], (70, "Panel", "Panel"))
    text = script.finish(on_load=[1])
"""

from __future__ import annotations

import math
from collections import defaultdict

GAME_SECONDS_PER_SECOND = 30        # map timers run on game time: 30 game seconds per real second
TOUCH_POLL_EVENT = 900              # the TouchToOpen doors' poll (no map uses 900)
TOUCH_REACH = 37                    # the party's collision radius (IndoorWorldRuntime PartyCollisionRadius)
APPROACH_POLL_EVENT = 906           # the approach talks' 4 Hz poll (dungeon/objects.py has 902-905)
APPROACH_GAP_LT = 16                # FORAD.scr OnTargetWithinDist 16 Talk, NPC378.scr RunTo <player> 16 Talk
LT = 2.56                           # MM9 units -> engine units
INIT_POSE_EVENT = 907               # the :Init loopanim poses' load handler (init_poses)


def init_loop_clip(script_name: str) -> str | None:
    """The clip an MM9 script loops from its :Init (`loopanim <clip> ...`), lower case, or None."""
    import re
    from pathlib import Path
    name = script_name.replace("\\", "/").split("/")[-1].lower()
    if not name:
        return None
    if not hasattr(init_loop_clip, "folder"):
        folder = Path(__file__).resolve().parents[4] / "mm9/extracted/SCRIPTS/SCRIPTS"
        init_loop_clip.folder = {p.name.lower(): p for p in folder.glob("*.scr")}
    path = init_loop_clip.folder.get(name)
    if path is None:
        return None
    inside = False
    for line in path.read_text(errors="replace").splitlines():
        text = line.split(";")[0].strip()
        if text.lower().startswith(":init"):
            inside = True
            continue
        if inside and text.startswith(":"):
            return None
        match = re.match(r"loopanim\s+([A-Za-z][A-Za-z0-9_]*)\b", text, re.I) if inside else None
        if match:
            return match[1].lower()
    return None


def model_script_clips(monster_id: int) -> set:
    """The script clips (lower case) of the HD model drawing an MM9 monster row (worlds/mm9 actors.yml by its
    descriptor in monster_descriptors.txt)."""
    if not hasattr(model_script_clips, "table"):
        import yaml
        from .source import ROOT
        descriptors = {}
        for line in (ROOT / "assets_dev/worlds/mm9/data_tables/monster_descriptors.txt").read_text(
                encoding="utf-8", errors="replace").splitlines():
            cells = line.split("\t")
            if len(cells) > 1 and cells[0].strip().isdigit():
                descriptors[int(cells[0])] = cells[1].strip()
        entries = yaml.safe_load((ROOT / "assets_dev/worlds/mm9/models/actors.yml").read_text())
        clips = {}
        for entry in entries.get("actors", []) if isinstance(entries, dict) else entries:
            clips[str(entry.get("descriptor"))] = {str(k).lower() for k in (entry.get("script_clips") or {})}
        model_script_clips.table = {row: clips.get(name, set()) for row, name in descriptors.items()}
    return model_script_clips.table.get(int(monster_id), set())


def model_clip_seconds(monster_id: int) -> dict:
    """The clip lengths (seconds) of the HD model drawing an MM9 monster row, by role (lower case): its `clips` roles
    (standing, walking, fidget...) and its `script_clips` (an mm9_ai routine step's `seconds`: one plays it once)."""
    import json
    import struct
    import numpy as np
    import yaml
    from .source import ROOT
    if not hasattr(model_clip_seconds, "table"):
        descriptors = {}
        for line in (ROOT / "assets_dev/worlds/mm9/data_tables/monster_descriptors.txt").read_text(
                encoding="utf-8", errors="replace").splitlines():
            cells = line.split("\t")
            if len(cells) > 1 and cells[0].strip().isdigit():
                descriptors[int(cells[0])] = cells[1].strip()
        entries = yaml.safe_load((ROOT / "assets_dev/worlds/mm9/models/actors.yml").read_text())
        model_clip_seconds.entries = {str(entry.get("descriptor")): entry for entry in entries["actors"]}
        model_clip_seconds.descriptors = descriptors
        model_clip_seconds.table = {}
        model_clip_seconds.models = {}
    table = model_clip_seconds.table
    if monster_id not in table:
        entry = model_clip_seconds.entries.get(model_clip_seconds.descriptors.get(int(monster_id), ""), {})
        model = entry.get("model")
        if model not in model_clip_seconds.models:
            lengths = {}
            if model:
                raw = (ROOT / "assets_dev" / model).read_bytes()
                size = struct.unpack_from("<I", raw, 12)[0]
                document = json.loads(raw[20:20 + size])
                for animation in document.get("animations", []):
                    longest = 0.0
                    for sampler in animation["samplers"]:
                        accessor = document["accessors"][sampler["input"]]
                        longest = max(longest, float(np.max(accessor.get("max", [0.0]))))
                    lengths[animation.get("name", "")] = longest
            model_clip_seconds.models[model] = lengths
        lengths = model_clip_seconds.models[model]
        roles = {**(entry.get("clips") or {}), **(entry.get("script_clips") or {})}
        table[monster_id] = {str(role).lower(): lengths[clip] for role, clip in roles.items() if clip in lengths}
    return table[monster_id]


def lua_key(name: str) -> str:
    """A table key: the bare name when it is a Lua identifier, else ["name"] (Drangheim's "cottage door")."""
    return name if name.isidentifier() else '["' + name.replace('\\', '\\\\').replace('"', '\\"') + '"]'


def point(p) -> str:
    return "{" + ", ".join(str(int(round(v))) for v in p) + "}"


def thorolf_approaches(script, actors: dict, names=("Thorolf0", "Thorolf1")) -> None:
    """NPC378.scr (Thorolf Ratatoskssen, the messenger, in six cities): :Init / :OnAppear arm OnFoundPlayer :OnFound,
    which (unless key 107, or 84 without 106) runs to the player (RunTo 16) and :Talk: DoRude 378, his voice, and the
    other copy removed (Thorolf0 removes Thorolf1, any other removes Thorolf0). `actors`: DAT name -> actor index."""
    for name in names:
        twin = actors.get("Thorolf1" if name == "Thorolf0" else "Thorolf0")
        remove = f"MM9.removeActor({twin}); " if twin is not None else ""
        talk = f"{remove}MM9.openRude(378, {actors[name]}); MM9.playSound(\"voices/npc/npc_378.wav\")"
        script.approach_talk(actors[name], talk,
                             armed="not has(107) and (not has(84) or has(106))", run=True,
                             note=f"{name}: NPC378.scr :OnFound RunTo 16 :Talk")


class Script:
    def __init__(self, build, title: str, writer: str = "convert.py"):
        self.build = build
        self.door = {m["node"][5:]: m["door_id"] for m in build.movers}
        self.groups = defaultdict(list)
        for m in build.movers:
            self.groups[m["group"]].append(m["door_id"])
        self.lines = [
            f"-- {title}, MM9 rework (level_generation/projects/mm9r_{build.project.stem}/{writer} writes this file).",
            "-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by",
            "-- its DAT object (see work/content.json and the project README).",
            "local handlers = {}",
            "local DOORS = {" + ", ".join(f"{lua_key(k)} = {v}" for k, v in sorted(self.door.items())) + "}",
            "local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end",
            "local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end",
            "local function var(name) return evt.GetMapVar(name, 0) end",
            "local function set(name, value) evt.SetMapVar(name, value) end",
            "local function seconds(n) return n * " + str(GAME_SECONDS_PER_SECOND) + " end",
            "",
        ]
        self.registrations = []         # (event, title, hint or None, kind)
        self.hooks = []                 # lines registering hooks
        self.approaches = []            # approach_talk rows

    def add(self, lines: list[str], *registrations) -> None:
        self.lines += list(lines)
        for registration in registrations:
            event, title, hint = registration[:3]
            kind = registration[3] if len(registration) > 3 else "event"
            self.registrations.append((event, title, hint, kind))

    def doors(self, skip_groups=()) -> None:
        """Each door group's click event toggles all its movers (groups with their own events are skipped)."""
        own = set(self.build.hooks.mover_events) | set(skip_groups)
        self.lines.append("-- Doors: each MM9 door group opens and closes on a click.")
        events = sorted({(m["event"], m["group"]) for m in self.build.movers if m["event"] and m["group"] not in own})
        drives = {m["group"]: m.get("drives") or [] for m in self.build.movers}
        for event, group in events:
            # the group's own movers, then those of the groups it drives (a rule's `drives`: a lever and its gate)
            doors = self.groups[group] + [d for driven in drives.get(group, []) for d in self.groups[driven]]
            calls = " ".join(f"evt.SetDoorState({d}, DoorAction.Trigger)" for d in doors)
            self.lines.append(f"handlers[{event}] = function() {calls} end   -- {group}")
            self.registrations.append((event, "Door", "Door", "event"))
        self.lines.append("")

    def chests(self) -> None:
        self.lines.append("-- Chests (MM9 TreasureChest objects; loot records in the scene).")
        for c in self.build.content.report["chests"]:
            self.lines.append(f"handlers[{c['event']}] = function() evt.OpenChest({c['container_id']}) end"
                              f"   -- {c['anchor']}")
            self.registrations.append((c["event"], "Chest", "Chest", "event"))
        self.lines.append("")

    def touch_doors(self) -> list:
        """MM9's TouchToOpen doors (Door class, TouchToOpen 1): the party walking into one opens it. A 4 Hz poll tests
        the party's feet against each door's box grown by the party's radius (MM9 fires on the body's touch); a door
        MM9 closes again (CloseWaitTime) has its movers.linear_mover auto-close. Returns the load event to start it."""
        touch = [m for m in self.build.movers if m.get("touch")]
        if not touch:
            return []
        rows = []
        for m in touch:
            low, high = m["box"]
            low = [low[0] - TOUCH_REACH, low[1] - TOUCH_REACH, low[2] - TOUCH_REACH]
            high = [high[0] + TOUCH_REACH, high[1] + TOUCH_REACH, high[2]]
            rows.append(f"    {{door = {m['door_id']}, box = {{{point(low)}, {point(high)}}}}},   -- {m['node'][5:]}")
        self.lines += [
            "-- MM9's TouchToOpen doors: walking into one opens it (a 4 Hz poll of the party's position).",
            "local TOUCH_DOORS = {", *rows, "}",
            f"handlers[{TOUCH_POLL_EVENT}] = function()",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for _, t in ipairs(TOUCH_DOORS) do",
            "        local b = t.box",
            "        if x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2]",
            "                and z >= b[1][3] and z <= b[2][3] then",
            "            evt.SetDoorState(t.door, DoorAction.Open)   -- an open door ignores it; a closing one reopens",
            "        end",
            "    end",
            f"    evt.StartTimer({TOUCH_POLL_EVENT}, seconds(0.25))",
            "end",
            "",
        ]
        # a map timer: evt.StartTimer re-arms only an event registered as a timer (a plain event ran once, at load)
        self.registrations.append((TOUCH_POLL_EVENT, "Touch doors", None, "timer"))
        return [TOUCH_POLL_EVENT]

    def approach_talk(self, actor: int, talk: str, armed: str = "true", run: bool = False, note: str = "") -> None:
        """An MM9 NPC who starts his own talk when the party comes near: FORAD.scr's OnFoundPlayer -> target ->
        OnTargetWithinDist 16 Talk, NPC378.scr's OnFoundPlayer -> RunTo <player> 16 Talk. MM9's distance is the gap
        between the bodies (16 LT is inside any body from centre to centre), so the talk fires once the party's feet
        are within the actor's radius + the party's + 16 LT of his. `run`: he runs to the party once he sees it within
        his SightDistance (the placement's mm9_ai sight). `armed` (a Lua expression) is the script's own gate; the
        actor must be alive, shown and in sight (evt.ActorSeesParty). Once per visit, as the scripts' bTalking; a script
        whose flag stays set for good (FORAD.scr) gates `armed` with its own map variable.
        `talk`: the Lua statements of the script's :Talk (its DoRude and voice); MM9.openRude takes the actor as its
        second argument, so that the dialogue's close runs his OnRudeExit event."""
        record = next(r for r in self.build.scene_actors if r["actor_index"] == actor)
        reach = int(round(record["radius"] + TOUCH_REACH + APPROACH_GAP_LT * LT))
        sight = int((record.get("mm9_ai") or {}).get("sight") or 0) if run else 0
        self.approaches.append((actor, reach, sight, armed, talk, note))

    def approach_talks(self) -> list:
        """The approach talks' Lua (approach_talk), a 4 Hz poll; returns the load event that starts it."""
        if not self.approaches:
            return []
        rows = [f"    {{actor = {actor}, reach = {reach}, sight = {sight}, armed = function() return {armed} end,"
                f"\n        talk = function() {talk} end}},   -- {note}"
                for actor, reach, sight, armed, talk, note in self.approaches]
        self.lines += [
            "-- MM9's approach talks (dungeon/lua.py approach_talk): an NPC whose script talks when the party comes",
            "-- within 16 LT of his body (OnTargetWithinDist / RunTo 16 -> DoRude). reach: the feet's distance at which",
            "-- he talks; sight > 0: he runs to the party once he sees it within that range. Once per visit.",
            "local APPROACH_TALKS = {", *rows, "}",
            "local approachDone = {}",
            f"handlers[{APPROACH_POLL_EVENT}] = function()",
            "    for k, t in ipairs(APPROACH_TALKS) do",
            "        if not approachDone[k] and t.armed() then",
            "            if evt.ActorSeesParty(t.actor, t.reach) then",
            "                approachDone[k] = true",
            "                if t.sight > 0 then evt.StopActorMove(t.actor) end",
            "                t.talk()",
            "            elseif t.sight > 0 and evt.ActorSeesParty(t.actor, t.sight) then",
            "                local x, y, z = evt.GetPartyPosition()",
            "                evt.MoveActorTo(t.actor, x, y, z, 0, true)",
            "            end",
            "        end",
            "    end",
            f"    evt.StartTimer({APPROACH_POLL_EVENT}, seconds(0.25))",
            "end",
            "",
        ]
        self.registrations.append((APPROACH_POLL_EVENT, "Approach talks", None, "timer"))
        return [APPROACH_POLL_EVENT]

    def shared_objects(self) -> list:
        """The Lua of the MM9 objects every map shares (objects.shared_lines: bone piles, broken urns and explosions,
        perception hints, ambient triggers), after the map's own; returns its load events. A shared event the map
        already registers stops the build (pick the map's event elsewhere)."""
        import re
        from .objects import shared_lines
        taken = {event for event, *_ in self.registrations}
        written = taken | {int(m) for line in self.lines for m in re.findall(r"handlers\[(\d+)\]\s*=", line)}
        lines, registrations, load = shared_lines(self.build, written, "\n".join(self.lines))
        clash = sorted(event for event, *_ in registrations if event in taken)
        if clash:
            raise SystemExit(f"map events {clash} are the shared objects' (dungeon/objects.py): move the map's")
        self.lines += lines
        self.registrations += registrations
        return load

    def init_poses(self) -> list:
        """MM9's people whose script loops one animation from its :Init (NPC127.scr's Markel: "loopanim Sit 0
        DoNothing" on his throne in Guberland City; Tryggva in Frosgard City; a seated shopkeeper in Thjorgard City)
        loop it here: every load plays the clip on the placed actor and keeps its placed facing, as the posed people
        do (../rude_props.py load_lines). Only immobile actors whose HD model has that clip, and none the map's own
        Lua already plays a clip on (a 2026-11-08 player's report: Markel stood by his throne). Returns the load
        event."""
        actors = getattr(self.build, "scene_actors", None) or []
        written = "\n".join(self.lines)
        rows = []
        for index, actor in enumerate(actors):
            source = actor.get("mm9_source_object_index")
            if not actor.get("immobile") or source is None or f"PlayActorClip({index}," in written:
                continue
            properties = self.build.source.objects[source]["properties"]
            clip = init_loop_clip(str(properties.get("ScriptName") or ""))
            if clip is None or clip not in model_script_clips(actor["monster_id"]):
                continue
            yaw = actor["initial_yaw_units"] / 2048 * 2 * math.pi
            x, y = actor["position"]["x"], actor["position"]["y"]
            fx, fy = round(x + 256 * math.cos(yaw)), round(y + 256 * math.sin(yaw))
            rows.append(f"    evt.PlayActorClip({index}, \"{clip}\", true); evt.FaceActorTo({index}, {fx}, {fy}, 0)"
                        f"   -- {actor['name']}: {properties.get('ScriptName')} :Init loopanim")
        if not rows:
            return []
        self.build.stats["init_poses"] = len(rows)
        self.lines += ["-- MM9's people posed by their scripts' :Init loopanim (dungeon/lua.py init_poses): every load.",
                       f"handlers[{INIT_POSE_EVENT}] = function()", *rows, "end", ""]
        self.registrations.append((INIT_POSE_EVENT, "Script poses", None, "event"))
        return [INIT_POSE_EVENT]

    def finish(self, on_load=(), on_leave=()) -> str:
        on_load = (list(on_load) + self.touch_doors() + self.approach_talks() + self.shared_objects()
                   + self.init_poses())
        chests = self.build.content.report["chests"]
        opened = ", ".join(f"[{c['event']}] = {{{c['container_id']}}}" for c in chests)
        meta = (f"SetMapMetadata({{onLoad = {{{', '.join(map(str, on_load))}}}, onLeave = "
                f"{{{', '.join(map(str, on_leave))}}}, timers = {{}}, openedChestIds = {{{opened}}}}})")
        lines = self.lines[:11] + [meta, ""] + self.lines[11:]
        for event, title, hint, kind in self.registrations:
            if kind == "timer":
                lines.append(f'RegisterMapTimerEvent({event}, seconds(3), handlers[{event}], "{title}", "", seconds(3))')
            elif hint:
                lines.append(f'RegisterEvent({event}, "{title}", handlers[{event}], "{hint}")')
            else:
                lines.append(f'RegisterEvent({event}, "{title}", handlers[{event}])')
        lines += self.hooks
        return "\n".join(lines) + "\n"
