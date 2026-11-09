#!/usr/bin/env python3
"""
Temple of Honk, MM9 rework: MM9's TEMPLEOFHONK.dat as a native indoor map (BLV) on the shared dungeon converter
(../mm9r_common/dungeon/, ../mm9r_common/DUNGEON_PLAYBOOK.md). This file holds the map's own population and events:

    python3 level_generation/projects/mm9r_templeofhonk/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_templeofhonk/convert.py --plan     # rooms only: work/rooms*.png

MM9's scripted objects as native events (see README.md):
- DoubleDoor13, the door from the entrance hall into the temple, opens only for a party on the Golden Honk quest
  (Honk.scr: key 343 unlocks DoubleDoorL13/R13).
- The accountant's key (key0, HonkKey.scr) gives item 445 and key 7000; stolen under the accountant's eyes (within
  200 LT) it turns the Honks hostile.
- The HONK buttons (HonkSecretDoor.scr): with key 7000 the four buttons on the pool's south wall unlock; each raises its
  corner stone; H, O, N, K in that order opens the secret door to the treasury (it shuts after 10 s; a pad inside opens
  it again), any other order sinks the stones again. Everything resets after 20 s.
- The Golden Honk on the altar (Honk.scr): item 369 and key 344 (on the quest) or 345 (without), Honks hostile.
- The Honks (HonkHostility.inc) are the party's friends until the party hurts or kills one, or steals: then all are
  hostile.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[0] / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from dungeon import lua, water  # noqa: E402
from dungeon.source import SCALE  # noqa: E402

PROPS = PROJECT / "props.json"
POOL_MODEL = "BlueWater0"           # the entrance channel's water volume
POOL_TEXTURE = "water:pool"         # overrides.yml textures: MM9's Water115.spr frame 0 (worlds/mm9/textures/WATEQOBX0Z.bmp)
HONK_GROUP = 1                      # every Honk: friends of the party until HonksHostile
BUTTONS = {"H": 61, "O": 62, "N": 63, "K": 64}       # HONK order; click events of the buttons
DOOR13_EVENT = 130                  # DoubleDoor13: locked unless the party is on the Golden Honk quest
VAULT_PAD_EVENT = 70                # UnlockDoorTrig inside the treasury opens the secret door
KEY_EVENT, GOLDEN_HONK_EVENT = 75, 76
DAMAGE_HOOK, KILL_HOOK = 96, 97
TIMER_STONES, TIMER_OPEN, TIMER_SHUT, TIMER_RESET = 150, 151, 152, 153
TIMER_CEREMONY = 154                # HonkLeader.scr's ceremony, checked every 3 s
CEREMONIES = ((6 * 60 + 15, 6 * 60 + 45), (18 * 60 + 15, 18 * 60 + 45))   # @M 6:15 RingGong .. 6:45 EndCeremony
PLATFORMS = ("PlatformMarker0", "PlatformMarker1", "PlatformMarker2")       # spObjects (PlatformMarker3 is not in the DAT)
QUEST_KEY, ON_QUEST_TAKEN, OFF_QUEST_TAKEN, HONK_KEY = 343, 344, 345, 7000
GOLDEN_HONK_ITEM, HONK_KEY_ITEM = 369, 445
STOLEN_DISTANCE = 200 * SCALE       # HonkKey.scr: the accountant sees the theft within 200 LT


class TempleOfHonk(dungeon.Hooks):
    generator = "mm9r_templeofhonk"
    mover_events = {f"{letter}Button": (event, "click") for letter, event in BUTTONS.items()}
    mover_events["DoubleDoor13"] = (DOOR13_EVENT, "click")

    def populate(self, build):
        content = build.content
        if PROPS.exists():
            # the accountant's key and the Golden Honk are world items (dungeon/pickups.py); their pickups run the
            # events below
            content.props(PROPS, events={"key0": KEY_EVENT, "Honk": GOLDEN_HONK_EVENT})
        else:
            print("note: props.json is missing; no decorations, chests or quest objects placed")
        self.pool(build)
        trigger = build.source.by_name["unlockdoortrig"]
        content.pad(trigger["name"], trigger["properties"]["Pos"], trigger["properties"]["Dims"], VAULT_PAD_EVENT)
        for name in ("TriggerStartCeremony0", "TriggerStartCeremony1", "TriggerStartCeremony2"):
            content.report["omitted"].append({"anchor": name, "class": "Trigger",
                                              "reason": "removes HONK_CEREMONY, which no MM9 script listens to "
                                                        "(HonkFirstCeremony.inc is included nowhere)"})

    def pool(self, build):
        """The entrance channel's water: the top face of MM9's BlueWater0 volume (8 LT over the channel floor, 2 under
        its rim) as an untouchable face with MM9's SpriteSurfaceName Water115.spr (first frame; MM9 animates it at 0.9
        alpha, which BLV faces cannot). Untouchable, so with swimming (water.swimming: the scene's water_volumes) it is
        the non-solid surface of the volume: the party wades in 15 units of water (its eye never goes under, as in
        MM9) and the fish swim in it (`swim_fish`). The shared water rule (water.drawn_surfaces) draws this top itself
        for a skipped volume with ShowSurface: then the hook builds nothing (no second face)."""
        project, package = build.project, build.package
        if any(polygon.model == POOL_MODEL for polygon in build.polygons):
            build.content.report["water"] = {"model": POOL_MODEL, "built_by": "dungeon/water.py drawn_surfaces"}
            return
        points = np.array(build.source.models[POOL_MODEL].points, float)
        top = points[:, 1].max()
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        ring = np.array([[x0, top, z0], [x0, top, z1], [x1, top, z1], [x1, top, z0]])
        native = np.round(project.native(ring)).astype(np.int64)
        if np.cross(native[1] - native[0], native[2] - native[0])[2] < 0:
            native, ring = native[::-1], ring[::-1]
        key = package.material(POOL_TEXTURE)[0]
        node = f"TRIGGER_water_{POOL_MODEL}"     # the compiler reads ROOM_, PORTAL_, TRIGGER_, MECH_, DECOR_, LIGHT_ nodes only
        package.nodes[node].append((native, ring[:, [0, 2]] - ring[:, [0, 2]].min(0), key))
        room = build.content.owner(np.array([(x0 + x1) / 2, top - 4, (z0 + z1) / 2]))
        package.room_nodes[room].append(node)
        package.metadata["surfaces"].append({"id": POOL_MODEL, "source_node": node, "flags": ["untouchable"]})
        build.content.report["water"] = {"model": POOL_MODEL, "room": room, "z": int(native[0][2]),
                                         "corners": native.tolist()}

    def actors(self, build, sector_of_room):
        content = build.content
        # npc_rows: the geese (Goose, MM9 row 293) and the pool's fish (Fish, row 227) on their own rows and models
        bases = content.monster_bases(npc_rows=True)
        out, honks = [], []
        self.fish_report = []
        for o in build.source.objects:
            if o["name"] not in bases:
                continue
            # The fish (no script, fish.scr from its row) are harmless pool life outside the Honks' hostility; the
            # geese run DumbGoose.scr, which includes HonkHostility.inc: they stand and turn with the Honks.
            fish = o["class"] == "Fish"
            actor = content.actor(o, bases[o["name"]], sector_of_room, group=0 if fish else HONK_GROUP, friendly=True)
            if fish and water.swimming(build.project):
                self.swim_fish(build, o, actor)
            out.append(actor)
            if not fish:
                honks.append(actor)
        self.honk_monsters = sorted({a["monster_id"] for a in honks})
        self.accountant = next(a["actor_index"] for a in content.report["actors"] if a["anchor"] == "Accountant")
        return out

    def swim_fish(self, build, o: dict, actor: dict) -> None:
        """A fish as a swimmer in the pool (MM9's AISwimFly; the engine binds a swimmer whose body box centre starts in
        a water volume to it, mm9_fish_claude README "Swimming"). The pool is 15 units deep over its bed, and the engine
        sets a placed flyer whose feet are not over the floor onto it: the feet go 2 over the bed and the collision
        body is as tall as keeps its centre 1.5 under the surface (22; MM9's body at the DAT Scale 0.4-0.7 would be
        33-57, and the shared swimmer rule's 82 sets the centre over the water: a walker). The model keeps MM9's DAT
        Scale (draw_scale), so the drawn fish rides at the surface, as MM9's float 10 LT over it."""
        p = o["properties"]
        scale = float(p.get("Scale", 1.0) or 1.0)
        native = build.project.native
        top = float(native(np.array(build.source.models[POOL_MODEL].points, float))[:, 2].max())
        bed = build.content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1])
        bed = float(native(np.array([p["Pos"][0], bed, p["Pos"][2]], float))[2])
        foot = int(np.ceil(bed + 2.0))
        actor["height"] = max(8, min(int(round(actor["height"] * scale)), int(2.0 * (top - 1.5 - foot))))
        actor["radius"] = max(4, int(round(actor["radius"] * scale)))
        actor["position"]["z"] = foot
        self.fish_report.append({"anchor": o["name"], "actor_index": actor["actor_index"], "height": actor["height"],
                                 "foot": foot, "centre": round(foot + actor["height"] / 2.0, 1), "bed": round(bed, 1),
                                 "surface": round(top, 1)})

    def map_script(self, build):
        script = lua.Script(build, "Temple of Honk")
        script.doors()
        script.chests()
        key = build.project.native(build.source.properties("key0")["Pos"]).round().astype(int).tolist()
        honk_ids = ", ".join(f"[{m}] = true" for m in self.honk_monsters)
        script.add([
            "-- The Honks (HonkHostility.inc): the party's friends until it hurts or kills one or steals from them.",
            f"local HONKS = {{{honk_ids}}}",
            "local function honksHostile()",
            "    if var(\"HonksHostile\") == 1 then return end",
            "    set(\"HonksHostile\", 1)",
            f"    evt.SetMonGroupBit({HONK_GROUP}, MonsterBits.Hostile, true)",
            "end",
            f"handlers[{DAMAGE_HOOK}] = function(context)",
            "    if HONKS[context.monsterId] then honksHostile() end",
            "end",
            f"handlers[{KILL_HOOK}] = function(context)",
            "    if HONKS[context.monsterId] then honksHostile() end",
            "end",
            "",
            f"-- DoubleDoor13 (Honk.scr): unlocked for a party on the Golden Honk quest (key {QUEST_KEY}).",
            f"handlers[{DOOR13_EVENT}] = function()",
            f"    if MM9.hasKey({QUEST_KEY}) == 0 then evt.StatusText(\"The door is locked.\") return end",
            "    evt.SetDoorState(DOORS.DoubleDoorL13, DoorAction.Trigger)",
            "    evt.SetDoorState(DOORS.DoubleDoorR13, DoorAction.Trigger)",
            "end",
            ""], (DOOR13_EVENT, "Door", "Door"))
        script.add([
            f"-- The accountant's key (HonkKey.scr): a world item ({HONK_KEY_ITEM}); its pickup gives key {HONK_KEY}, which "
            "unlocks the HONK buttons. Stolen",
            "-- under the accountant's eyes (within 200 LT) it turns the Honks hostile.",
            f"handlers[{KEY_EVENT}] = function()",
            f"    if MM9.hasKey({HONK_KEY}) == 1 then return end",
            f"    MM9.giveKey({HONK_KEY})",
            f"    if not evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, {self.accountant}, 0, false) then",
            f"        local x, y, z = evt.GetMapActorPosition({self.accountant})",
            f"        if x ~= nil and math.sqrt((x - {key[0]}) ^ 2 + (y - {key[1]}) ^ 2) <= {int(round(STOLEN_DISTANCE))} "
            "then",
            "            set(\"KeyStolenSeen\", 1)",
            "            honksHostile()",
            "        end",
            "    end",
            "end",
            ""], (KEY_EVENT, "Key", None))
        order = "".join(BUTTONS)
        script.add([
            "-- The HONK buttons (HonkSecretDoor.scr): locked until the party has the accountant's key. Each raises its",
            "-- corner stone out of the pool (MM9 48 LT at 15 LT/s); the fourth stone decides: H, O, N, K opens the secret",
            "-- door (it shuts after 10 s, as MM9's CloseWaitTime), any other order sinks the stones and buttons again.",
            "-- Everything resets 20 s after the door opens.",
            f"local ORDER = \"{order}\"",
            "local function resetButtons()",
            "    for i = 1, 4 do",
            "        local letter = string.sub(ORDER, i, i)",
            "        close(letter .. \"CornerStone\"); close(letter .. \"Button\"); set(\"Pressed\" .. letter, 0)",
            "    end",
            "    set(\"HonkCount\", 0); set(\"HonkWrong\", 0)",
            "end",
            "local function press(letter, position)",
            f"    if MM9.hasKey({HONK_KEY}) == 0 then evt.StatusText(\"The button will not move.\") return end",
            "    if var(\"Pressed\" .. letter) == 1 or var(\"Pending\") ~= 0 then return end",
            "    set(\"Pressed\" .. letter, 1)",
            "    open(letter .. \"Button\"); open(letter .. \"CornerStone\")",
            "    local count = var(\"HonkCount\") + 1",
            "    set(\"HonkCount\", count)",
            "    if count ~= position then set(\"HonkWrong\", 1) end",
            "    if count == 4 then",
            "        if var(\"HonkWrong\") == 0 then set(\"Pending\", 1) else set(\"Pending\", 2) end",
            f"        evt.StartTimer({TIMER_STONES}, seconds(4))",
            "    end",
            "end",
            f"handlers[{TIMER_STONES}] = function()   -- the fourth stone has risen",
            f"    evt.StopTimer({TIMER_STONES})",
            "    local pending = var(\"Pending\")",
            "    if pending == 1 then",
            "        set(\"Pending\", 3); set(\"VaultOpened\", var(\"VaultOpened\") + 1)",
            "        open(\"SecretDoor\")",
            f"        evt.StartTimer({TIMER_SHUT}, seconds(10)); evt.StartTimer({TIMER_RESET}, seconds(20))",
            "    elseif pending == 2 then",
            "        set(\"Pending\", 0); resetButtons()",
            "    end",
            "end",
            f"handlers[{TIMER_SHUT}] = function() evt.StopTimer({TIMER_SHUT}); if var(\"Pending\") == 3 then "
            "close(\"SecretDoor\") end end",
            f"handlers[{TIMER_RESET}] = function() evt.StopTimer({TIMER_RESET}); if var(\"Pending\") == 3 then "
            "set(\"Pending\", 0); resetButtons() end end",
            "-- UnlockDoorTrig: from inside the treasury the secret door opens again (MM9 Trigger -> secretdoor open).",
            f"handlers[{VAULT_PAD_EVENT}] = function()",
            "    open(\"SecretDoor\")",
            f"    evt.StartTimer({TIMER_OPEN}, seconds(10))",
            "end",
            f"handlers[{TIMER_OPEN}] = function() evt.StopTimer({TIMER_OPEN}); if var(\"Pending\") ~= 3 then "
            "close(\"SecretDoor\") end end"]
            + [f"handlers[{event}] = function() press(\"{letter}\", {i + 1}) end   -- {letter}Button"
               for i, (letter, event) in enumerate(BUTTONS.items())]
            + [""],
            *[(event, f"{letter} button", "Button") for letter, event in BUTTONS.items()],
            (TIMER_STONES, "HONK stones risen", None, "timer"), (TIMER_SHUT, "Secret door shuts", None, "timer"),
            (TIMER_RESET, "HONK buttons reset", None, "timer"), (TIMER_OPEN, "Secret door shuts (inside)", None, "timer"),
            (VAULT_PAD_EVENT, "UnlockDoorTrig", None))
        script.add([
            f"-- The Golden Honk (Honk.scr): a world item ({GOLDEN_HONK_ITEM}); its pickup gives key {ON_QUEST_TAKEN} on the "
            f"quest (key {QUEST_KEY}), {OFF_QUEST_TAKEN} without; the Honks turn hostile.",
            f"handlers[{GOLDEN_HONK_EVENT}] = function()",
            f"    local taken = MM9.hasKey({QUEST_KEY}) == 1 and {ON_QUEST_TAKEN} or {OFF_QUEST_TAKEN}",
            "    if MM9.hasKey(taken) == 1 then return end",
            "    MM9.giveKey(taken)",
            "    honksHostile()",
            "end",
            ""], (GOLDEN_HONK_EVENT, "Golden Honk", None))
        script.add(self.ceremony_lines(build), (TIMER_CEREMONY, "Honk ceremony", None, "timer"))
        script.hooks += [f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Honk hostility", handlers[{DAMAGE_HOOK}])',
                         f'RegisterMonsterKilledHook({KILL_HOOK}, "Honk hostility", handlers[{KILL_HOOK}])']
        return script.finish()

    def ceremony_lines(self, build) -> list[str]:
        """HonkLeader.scr's ceremony, as far as it runs without the followers' walk (HonkFollower.scr, not carried):
        at 6:15 and 18:15 (RingGong) the church bell; until 6:45 and 18:45 (EndCeremony) the leader preaches
        (RandomPreach: one of thunder01-04 at him) and paces between the platform markers (Pace: WalkTo a random
        one). Not while the Honks are hostile."""
        leader = next(a["actor_index"] for a in build.content.report["actors"] if a["anchor"] == "HonkLeader")
        native = build.project.native
        marks = ", ".join("{" + ", ".join(str(int(round(v))) for v in native(build.source.properties(m)["Pos"])) + "}"
                          for m in PLATFORMS)
        spans = ", ".join(f"{{{a}, {b}}}" for a, b in CEREMONIES)
        return [
            "-- The Honk ceremony (HonkLeader.scr): the bell at 6:15 and 18:15, then until 6:45 and 18:45 the leader",
            "-- preaches (a thunder at him) and paces between the platforms; the followers' walk to the pulpit is not",
            "-- carried (HonkFollower.scr).",
            f"local CEREMONIES = {{{spans}}}",
            f"local PLATFORMS = {{{marks}}}",
            f"local LEADER = {leader}",
            "local function leaderSound(name)",
            "    local x, y, z = evt.GetMapActorPosition(LEADER)",
            "    if x ~= nil then evt.PlaySoundName(name, math.floor(x), math.floor(y), math.floor(z)) end",
            "end",
            f"handlers[{TIMER_CEREMONY}] = function()",
            "    if var(\"HonksHostile\") == 1 then return end",
            "    local now = math.floor(evt.CurrentGameMinutes())",
            "    local minute, day = now % 1440, math.floor(now / 1440)",
            "    for k, span in ipairs(CEREMONIES) do",
            "        if minute >= span[1] and minute < span[2] then",
            "            local id = day * 2 + k",
            "            if var(\"CeremonyRung\") ~= id then",
            "                set(\"CeremonyRung\", id); set(\"Ceremonies\", var(\"Ceremonies\") + 1)",
            "                leaderSound(\"events/churchbellring.wav\")   -- RingGong",
            "            elseif var(\"CeremonyStep\") % 2 == 0 then",
            "                leaderSound(\"ambient/thunder/thunder0\" .. MM9.random(1, 4) .. \".wav\")   -- RandomPreach",
            "            else",
            "                local p = PLATFORMS[MM9.random(1, #PLATFORMS)]   -- Pace",
            "                evt.MoveActorTo(LEADER, p[1], p[2], p[3])",
            "            end",
            "            set(\"CeremonyStep\", var(\"CeremonyStep\") + 1)",
            "            return",
            "        end",
            "    end",
            "end",
            "",
        ]

    def scene(self, build, scene: dict) -> None:
        """MM9's water surfaces drawn by the liquid shader."""
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)

    def report(self, build):
        return {"honk_monsters": getattr(self, "honk_monsters", []), "accountant_actor": getattr(self, "accountant", None),
                "swim_fish": getattr(self, "fish_report", [])}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, TempleOfHonk()))
