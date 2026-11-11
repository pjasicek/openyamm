#!/usr/bin/env python3
"""
Anskram Keep, MM9 rework: MM9's ANSKRAMKEEP.dat as a native indoor map (BLV) on the shared dungeon converter
(../mm9r_common/dungeon/, ../mm9r_common/DUNGEON_PLAYBOOK.md). This file holds the map's own population and events:

    python3 level_generation/projects/mm9r_anskramkeep/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_anskramkeep/convert.py --plan     # rooms only: work/rooms*.png
    python3 level_generation/projects/mm9r_anskramkeep/convert.py --scratch DIR    # build into DIR, install nothing

MM9's scripted objects as native events (README.md has the table): shooter plates, ceiling crushers, the treasure
panel, the pivot traps with their buttons, hatches and spike pits, the airlock gate, the cages, the Imp gates and the
Giant Imp. Every entity, pad, mover and actor keeps its DAT object name (work/content.json, work/doors.json).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[0] / "mm9r_common"))
import dungeon  # noqa: E402
import review_root  # noqa: E402
from dungeon import lua, tables  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402

PROPS = PROJECT / "props.json"
LETTERS = PROJECT.parents[2] / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
# The scrolls on the tables (BookLetter.scr, ScriptParams "488 Letter", "489 Letter 1": DoLetter <row>): event, row
EV_LETTERS = {"Prop3": (191, 488), "Prop4": (192, 488), "Prop5": (193, 488), "Prop6": (194, 488),
              "Prop7": (195, 489)}
FIRE_COG = 200                      # the Imp gate fire k is evt.SetSprite key FIRE_COG + k
IMP_MONSTER = 9079                  # MM9 "Imp" (AK_ImpGate.scr params "Imp 5 ...": five Imps per gate)
IMPS_PER_GATE = 5
GATE_KEY = 510                      # AK_ImpGate.scr: gate k gives key 510 + k (a QBit 90000 + key: MM9.giveKey)
# DungeonJukebox.scr's InitStrings: its ten sounds less lichkingTaunt and gopherwince, which MM9 does not ship (MM9
# plays nothing for them); WoodCreak1 is in it twice.
JUKEBOX_SOUNDS = ("door/doorcreak02.wav", "ambient/birds/owl02.wav", "ambient/thunder/thunder distant02.wav",
                  "events/rockscrumblingloop.wav", "events/woodcreak1.wav", "ambient/insects/cricket.wav",
                  "pickupitems/shield/metal01.wav", "events/woodcreak1.wav")
QUEST_KEY = 39                      # Anskrammainline.scr: all gates done; NPC997's quest entries read QBit 90039
GATE_GROUP = 60                     # actors summoned by Imp gate k are in group GATE_GROUP + k
GROUPS = {"GiantImp": 51, "GiantImpGuard0": 52, "GiantImpGuard1": 52,
          "BustOutNagate0": 53, "BustOutNagate1": 53, "BustOutNagate2": 53,
          "BustOutIcky0": 54, "BustOutIcky1": 54, "BustOutIcky2": 54}
HIDDEN = {"GiantImp", "GiantImpGuard0", "GiantImpGuard1"}      # MM9 scripts clear FLAG_VISIBLE until "appear"
FRIENDLY = {"GiantImpGuard0", "GiantImpGuard1"}                # AK_GiantImpGuard.scr: AddFriend Player
# The Giant Imp waits in its shaft under the four Floordoor slabs, on the lift ExitStairs (the lower disc's top).
GIANT_IMP_FLOOR_LT = -400.0
FLOORDOORS = ("Floordoor1", "Floordoor2", "Floordoor3", "Floordoor4")
# TriggerGiantImp (a 1024 x 1024 LT volume over the shaft) as four pads round it: a pad is a floor, and one over the
# shaft would hold the party up when the slabs fall. (x, z, half x, half z), LT.
GIANT_IMP_PADS = {"N": (0, 5322, 512, 178), "S": (0, 4668, 512, 188), "W": (-320, 4992, 192, 136),
                  "E": (320, 4992, 192, 136)}
# MM9's PerceptionBrushes: the red glow over a trap, seen by a party whose Perception reaches the PerceptionValue.
PERCEPTION_COG = 300                # brush k's faces: cog PERCEPTION_COG + k
PERCEPTION_SKILL = 29               # evt.CheckSkill's id: the party's best Perception value (mastery counted)
PERCEPTION_OPACITY = 0.5            # the brushes' Alpha (times the texture's own)
FRAME_FLAGS = {(True, True): "0x3\tHasMore,First", (False, True): "0x1\tHasMore", (False, False): "0x0\t"}

# Mover groups with events: (event, trigger type). Plates fire when stepped on, the rest on a click.
MOVER_EVENTS = {
    "ShooterPlate5": (60, "pressure_plate"), "ShooterPlate6": (61, "pressure_plate"),
    "ShooterPlate7": (62, "pressure_plate"), "ShooterPlate8": (63, "pressure_plate"),
    "ShooterPlate9": (64, "pressure_plate"), "ShooterPlate10": (65, "pressure_plate"),
    "CeilingCrushPlate1": (66, "pressure_plate"), "CeilingCrushPlate2": (67, "pressure_plate"),
    "CeilingCrushPlate3": (68, "pressure_plate"),
    "PivotTreasurePanel1": (70, "click"),
    "SwitchLever0": (71, "click"), "PanelLever": (72, "click"), "Switch0": (73, "click"), "Switch1": (74, "click"),
    # The gate's leaves work like its switches once both levers are pulled (MM9's leaves take no click: a party shut
    # in the airlock, the switch behind it, took the gate for broken; README "Deviations").
    "Outerdoor": (89, "click"), "Innerdoor": (89, "click"),
    # The pivot traps: stepping on the cross's floor springs it (MM9: PivotWallTrapTrigger on that half), the hatch
    # opens on a click from the ladder, the button in the niche springs the trap too.
    "PivotWallTrap1": (77, "pressure_plate"), "PivotWallTrap2": (78, "pressure_plate"),
    "PivotWallTrap3": (79, "pressure_plate"),
    "TrapExitDoor1": (80, "click"), "TrapExitDoor2": (81, "click"), "TrapExitDoor3": (82, "click"),
    "PivotButton1": (83, "click"), "PivotButton2": (84, "click"), "PivotButton3": (85, "click"),
}
# The spike pits under the traps: MM9 PropDamagers (20 per second): a pad on the pit floor.
SPIKE_PADS = {"Spikes14": 86, "Spikes16": 87, "Spikes17": 88}
SPIKE_DAMAGE = 20
SPIKE_HALF_LT = (40.0, 16.0, 40.0)
SPIKE_MARGIN = 40                   # a party this far off the pad still touches the spikes
TRAP_CYCLE_SECONDS = 8              # opens in 0.9 s, waits 5 s, closes in 1.8 s; then it is armed again
# MM9 trigger volumes (DAT Trigger objects) as pressure-plate pads: name -> event. The handler is chosen by the
# trigger's first target (TargetName1).
PAD_EVENTS = {"TriggerNagateBust": 75, "TriggerIckyBust": 76, "TriggerGiantImp": 90}
GATE_TRIGGER_EVENT = 170            # TriggerClosetGate* and TriggerBarrackGate*: 170, 171, ... in DAT order
KILL_HOOK_EVENT = 95                # runs on every monster kill (the Imp gates' next Imp)
CAGE_SWING_TIMER = 149              # KingKong.scr :BreakCage's hattack1, once CritterBreakOut0 has sunk
# Timers: 150-199 in the order the script takes them (plate resets, crusher strikes and rises, trap resets, spikes).
# Shooter plates: plate -> shooter: MM9 Door OpenTrigger0 "on" of a Shooter (FireBolt, DamageAmt).
SHOOTERS = {"ShooterPlate5": "Shooter5", "ShooterPlate6": "Shooter6", "ShooterPlate7": "Shooter7",
            "ShooterPlate8": "Shooter8", "ShooterPlate9": "CeilingShooter1", "ShooterPlate10": "CeilingShooter0"}
CRUSHERS = {"CeilingCrushPlate1": "CeilingCrush1", "CeilingCrushPlate2": "CeilingCrush2",
            "CeilingCrushPlate3": "CeilingCrush3"}
CRUSH_DAMAGE = 20                   # MM9 PropDamager Spikes18-20 under the crushers: DamagePerSecond 20


def integers(point) -> str:
    return ", ".join(str(int(round(v))) for v in point)


def letter(number: int) -> tuple[str, str]:
    """(title, text) of a row of MM9's BOOK AND SCROLL TEXT.csv."""
    import csv
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


class AnskramKeep(dungeon.Hooks):
    generator = "mm9r_anskramkeep"
    mover_events = MOVER_EVENTS

    def populate(self, build):
        content, source, project = build.content, build.source, build.project
        self.pads_report = content.report["pads"]
        content.props(PROPS, events={name: event for name, (event, _) in EV_LETTERS.items()})
        # The spike pits under the traps stand on their pit floors (MM9 PropDamager Spikes14/16/17, scale 1.3).
        for name in SPIKE_PADS:
            pos = source.properties(name)["Pos"]
            content.entity(name, "mm9_spikepit", project.native([pos[0], content.floor_at(pos[0], pos[2], pos[1]),
                                                                 pos[2]]), 0)
        self.gates = []                 # Imp gate k: {spawner, fire, count, position}
        self.gate_triggers = {}         # event -> gate index
        self.place_gate_fires(build)
        self.place_pads(build)
        self.place_perception_hints(build)

    def place_gate_fires(self, build):
        content, source, project = build.content, build.source, build.project
        spawners = {o["name"]: o for o in source.objects if o["class"] == "Fish"
                    and str(o["properties"].get("ScriptName", "")).lower().endswith("ak_impgate.scr")}
        for name in sorted(spawners, key=lambda n: int(n[len("ImpGateSpawner"):])):
            params = spawners[name]["properties"]["ScriptParams"].split()        # "Imp 5 killed ImpGateFire0"
            fire = source.by_name[params[3].lower()]
            spawn = spawners[name]["properties"]["Pos"]
            spawn_floor = content.floor_at(spawn[0], spawn[2], spawn[1] + 40)
            # MM9's fire burns in the sealed alcove behind the gate (floor 112 below the hall; not built): it stands
            # on the hall floor at the gate's mouth, the farthest point toward it that is still on that floor.
            pos = fire["properties"]["Pos"]
            for t in (0.8, 0.6, 0.4, 0.2, 0.0):
                x, z = spawn[0] + t * (pos[0] - spawn[0]), spawn[2] + t * (pos[2] - spawn[2])
                floor = content.floor_at(x, z, spawn[1] + 40)
                if floor is not None and abs(floor - spawn_floor) < 0.5:
                    break
            k = len(self.gates)
            content.entity(fire["name"], "mm9_gatefire", project.native([x, floor, z]), 0, primary=FIRE_COG + k,
                           light_radius=205)
            self.gates.append({"spawner": name, "fire": fire["name"], "count": int(params[1]),
                               "position": project.native([spawn[0], spawn_floor, spawn[2]]).round().astype(int).tolist()})
        content.report["gates"] = self.gates

    def place_pads(self, build):
        """MM9's touch triggers as pads. The plate triggers need none: the plates are pressure plates (MOVER_EVENTS)."""
        content, source = build.content, build.source
        gate_index = {g["spawner"]: k for k, g in enumerate(self.gates)}
        for o in source.objects:
            if o["class"] != "Trigger":
                continue
            p = o["properties"]
            target = str(p.get("TargetName1", ""))
            if o["name"] == "TriggerGiantImp":
                for side, (x, z, half_x, half_z) in GIANT_IMP_PADS.items():
                    content.pad(o["name"] + side, (x, p["Pos"][1], z), (half_x, p["Dims"][1], half_z),
                                PAD_EVENTS[o["name"]])
                continue
            if o["name"] in PAD_EVENTS:
                event = PAD_EVENTS[o["name"]]
            elif target.startswith("ImpGateSpawner"):
                event = GATE_TRIGGER_EVENT + len(self.gate_triggers)
                self.gate_triggers[event] = gate_index[target]
            else:
                continue
            content.pad(o["name"], p["Pos"], p["Dims"], event)
        for name, event in SPIKE_PADS.items():
            content.pad(name, source.properties(name)["Pos"], SPIKE_HALF_LT, event)

    def place_perception_hints(self, build):
        """Each PerceptionBrush's one visible polygon (MM9's Perception.spr, the rest of the brush is Invisible.dtx) as
        an untouchable translucent face with a cog: the map script shows it to a party with the Perception for it."""
        package, source = build.package, build.source
        self.hints = {}                 # brush name -> cog
        difficulties = perception_difficulties_by_model_name(source.world)
        names = sorted(difficulties, key=lambda n: int(n[len("perceptionbrush"):]))
        self.hint_difficulty = max(difficulties[n] for n in names)
        for k, lower in enumerate(names):
            name = next(model for model in source.models if model.lower() == lower)
            # The polygon lies 1 LT over the floor, facing down (MM9 draws it from above too): it is turned to face up,
            # so that it shows one-sided and the bake lights it from the room.
            polygon = next(p for p in source.polygons(name) if "perception" in p.texture.lower())
            polygon = Polygon(polygon.points[::-1], polygon.keys[::-1], polygon.texture, polygon.mapping, polygon.flags,
                              polygon.model, polygon.role, notes=dict(polygon.notes))
            node = f"TRIGGER_perception_{name}"
            package.add_polygon(node, polygon, build.stats)
            package.room_nodes[build.content.owner(polygon.points.mean(0) + [0, 8, 0])].append(node)
            package.metadata["surfaces"].append({"id": node[8:], "source_node": node, "flags": ["untouchable"],
                                                 "cog_number": PERCEPTION_COG + k})
            self.hints[name] = PERCEPTION_COG + k

    def scene(self, build, scene):
        """The hints' faces in the scene's translucent_faces (faces.yml lists STATIC_ nodes only: found by texture)."""
        sys.path.insert(0, str(dungeon.ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        alias = build.source.aliases["sprites\\perception.spr"]["alias"].lower()
        faces = [f["index"] for f in blv["faces"] if f["texture_name"].lower() == alias]
        if len(faces) != len(self.hints):
            raise SystemExit(f"{len(faces)} perception faces in the BLV, {len(self.hints)} brushes")
        scene.setdefault("translucent_faces", []).append({"faces": sorted(faces), "opacity": PERCEPTION_OPACITY,
                                                          "tint": [1.0, 1.0, 1.0], "two_sided": False})
        if build.project.install:
            self.install_hint_frames(build)

    def install_hint_frames(self, build):
        """MM9's Perception.spr (20 frames at 15 fps) as a texture frame sequence. The table is the engine's and only
        the review root's copy changes (README: a world contribution would take it at integration)."""
        entry = build.source.aliases["sprites\\perception.spr"]
        frames = [entry["alias"]] + [frame["alias"] for frame in entry["animation_frames"][1:]]
        relative = "engine/data_tables/texture_frame_data.txt"
        with tables.locked("review_tables.lock"):
            text = review_root.mirror_path(relative).read_text()
            if frames[0] in text:
                return
            rows = [f"{name}\t0\t1\t{len(frames) if i == 0 else 0}\t{FRAME_FLAGS[i == 0, i < len(frames) - 1]}"
                    for i, name in enumerate(frames)]
            review_root.install(relative, (text.rstrip("\n") + "\n" + "\n".join(rows) + "\n").encode())

    def actors(self, build, sector_of_room):
        """MM9's monster objects at their DAT positions on the floor, the scripted ones grouped, hidden or friendly."""
        content = build.content
        bases = content.monster_bases()
        out = []
        for o in build.source.objects:
            if o["name"] not in bases:
                continue
            base, changes = bases[o["name"]], {}
            # MM9's body at the DAT's own Scale, which replaces the row's (GiantImp 2, the bust-out Nagates and Ickies 0.7)
            changes = placed_body(base["monster_id"], o["properties"])
            if o["name"] == "GiantImp":          # AK_GiantImp.scr: SetStat HitPoints 100
                changes["hp"] = 100
            out.append(content.actor(o, base, sector_of_room, group=GROUPS.get(o["name"], 0), hidden=o["name"] in HIDDEN,
                                     friendly=o["name"] in FRIENDLY, **changes))
            if o["name"] == "GiantImp":          # it stands on the lift, which the floors of the DAT's world do not hold
                out[-1]["position"]["z"] = int(round(build.project.native([0, GIANT_IMP_FLOOR_LT, 0])[2])) + 1
        return out

    # --- Lua ----------------------------------------------------------------------------------------------------
    def map_script(self, build):
        script = lua.Script(build, "Anskram Keep")
        script.add([
            "-- A Shooter sits inside its wall or ceiling: the bolt starts a third of the way from it to the party's",
            "-- chest (at least 64 units out), inside the room, and strikes the party in its path (strikesParty).",
            "local function shoot(sx, sy, sz, damage)",
            "    local x, y, z = evt.GetPartyPosition()",
            "    z = z + 100",
            "    local dx, dy, dz = x - sx, y - sy, z - sz",
            "    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))",
            "    local k = math.max(64 / length, 0.33)",
            "    local fired = evt.FireMissile(\"Fire\", sx + dx * k, sy + dy * k, sz + dz * k, x, y, z, damage, \"Fire\", 0, 0, "
            "true)",
            "    if fired then MM9.launchSound(\"FireBolt\", sx, sy, sz) end",
            "    set(\"ShotsFired\", var(\"ShotsFired\") + (fired and 1 or 0))",
            "end",
            "local function partyIn(x0, y0, x1, y1)",
            "    local x, y = evt.GetPartyPosition()",
            "    return x >= x0 and x <= x1 and y >= y0 and y <= y1",
            "end",
            ""])
        script.doors(skip_groups=("Innerdoor", "Outerdoor"))
        script.chests()
        timers = iter(range(150, 200))
        self.script_plates(build, script, timers)
        self.script_traps(build, script, timers)
        self.script_gate(script)
        self.script_cages(script, build)
        self.script_imps(script, build)
        self.script_jukebox(script, timers)
        self.script_hints(script, timers)
        script.hooks.append(f'RegisterMonsterKilledHook({KILL_HOOK_EVENT}, "Imp gates", handlers[{KILL_HOOK_EVENT}])')
        return script.finish(on_load=[1])

    def script_plates(self, build, script, timers):
        source, project = build.source, build.project
        script.add(["-- Shooter plates: the plate sinks and its Shooter fires a fire bolt at the party (MM9 FireBolt, "
                    "DamageAmt); the plate rises after 3 s (CloseWaitTime)."])
        for plate, shooter in SHOOTERS.items():
            event = MOVER_EVENTS[plate][0]
            reset = next(timers)
            properties = source.properties(shooter)
            damage = int(round(float(properties.get("DamageAmt", 5))))
            script.add([f"handlers[{event}] = function()   -- {plate} -> {shooter}",
                        f"    if var(\"{plate}\") == 1 then return end",
                        f"    set(\"{plate}\", 1)",
                        f"    open(\"{plate}\")",
                        f"    shoot({integers(project.native(properties['Pos']))}, {damage})",
                        f"    evt.StartTimer({reset}, seconds(3))",
                        "end",
                        f"handlers[{reset}] = function() evt.StopTimer({reset}); close(\"{plate}\"); "
                        f"set(\"{plate}\", 0) end"],
                       (event, plate, plate), (reset, f"{plate} reset", None, "timer"))
        script.add(["", f"-- Ceiling crushers: the plate sinks, the crusher drops (MM9 Speed 300, MoveDist 176), its spikes "
                    f"hurt a party under it ({CRUSH_DAMAGE}, MM9 Spikes18-20), and it rises after 3 s."])
        for plate, crusher in CRUSHERS.items():
            event = MOVER_EVENTS[plate][0]
            hit, rise = next(timers), next(timers)
            model = np.array(source.models[crusher].points)
            low, high = project.native(model.min(0)), project.native(model.max(0))
            x0, x1 = sorted((low[0], high[0]))
            y0, y1 = sorted((low[1], high[1]))
            script.add([f"handlers[{event}] = function()   -- {plate} -> {crusher}",
                        f"    if var(\"{crusher}\") == 1 then return end",
                        f"    set(\"{crusher}\", 1)",
                        f"    open(\"{plate}\")",
                        f"    open(\"{crusher}\")",
                        f"    evt.StartTimer({hit}, seconds(0.7))",
                        "end",
                        f"handlers[{hit}] = function()",
                        f"    evt.StopTimer({hit})",
                        f"    if var(\"{crusher}\") ~= 1 then return end",
                        "    local x, y = evt.GetPartyPosition()",
                        f"    if x >= {int(x0) - 40} and x <= {int(x1) + 40} and y >= {int(y0) - 40} and y <= {int(y1) + 40} "
                        f"then evt.DamagePlayer(Players.All, const.Damage.Physical, {CRUSH_DAMAGE}); "
                        f"set(\"CrushHits\", var(\"CrushHits\") + 1) end",
                        f"    evt.StartTimer({rise}, seconds(2.3))",
                        "end",
                        f"handlers[{rise}] = function() evt.StopTimer({rise}); close(\"{crusher}\"); close(\"{plate}\"); "
                        f"set(\"{crusher}\", 0) end"],
                       (event, plate, plate), (hit, f"{crusher} strike", None, "timer"),
                       (rise, f"{crusher} rise", None, "timer"))
        script.add(["", "-- The treasure panel beside PivotWallTrap1 slides up (MM9 Sticky, PushOpen) to show TreasureChest1.",
                    "handlers[70] = function() open(\"PivotTreasurePanel1\") end", ""], (70, "Panel", "Panel"))

    def script_traps(self, build, script, timers):
        project, source = build.project, build.source
        script.add([
            "-- Pivot traps: the cross turns 90 degrees and tips the party into the pit; MM9's CloseWaitTime turns it back",
            "-- (the mover's auto-close, at half the speed), then it is armed again. A ladder climbs to the hatch beside it.",
            "-- Its four quarters swap as it turns: the V between the floor and the wall carries a body round the axle,",
            "-- which is how MM9 reaches the niche behind the wall: a party on the turned floor rides the slow swing back",
            "-- over the axle into the niche; the button in the niche springs the trap, and the fast swing carries it out",
            "-- again. So only the corridor's half of the floor springs the trap (MM9's PivotWallTrapTrigger stands there);",
            "-- a party landing on the niche's half does not."])
        for k in (1, 2, 3):
            trap, button, hatch = f"PivotWallTrap{k}", f"PivotButton{k}", f"TrapExitDoor{k}"
            event = MOVER_EVENTS[trap][0]
            reset = next(timers)
            axle = project.native(source.properties(trap)["RotationPoint"])
            side = project.native(build.plan["movers"][trap]["falls_point"]) - axle
            script.add([f"local function spring{k}()",
                        f"    if var(\"{trap}\") == 1 then return end",
                        f"    set(\"{trap}\", 1)",
                        f"    open(\"{trap}\")",
                        f"    open(\"{button}\")",
                        f"    evt.StartTimer({reset}, seconds({TRAP_CYCLE_SECONDS}))",
                        "end",
                        f"handlers[{event}] = function()   -- {trap}: its floor, the corridor's half",
                        "    local x, y = evt.GetPartyPosition()",
                        f"    if (x - {int(round(axle[0]))}) * {int(round(side[0]))} + (y - {int(round(axle[1]))}) * "
                        f"{int(round(side[1]))} > 0 then spring{k}() end",
                        "end",
                        f"handlers[{reset}] = function() evt.StopTimer({reset}); close(\"{button}\"); "
                        f"set(\"{trap}\", 0) end",
                        f"handlers[{MOVER_EVENTS[button][0]}] = function() spring{k}() end   -- {button}",
                        f"handlers[{MOVER_EVENTS[hatch][0]}] = function() open(\"{hatch}\") end   -- {hatch}"],
                       (event, trap, None), (reset, f"{trap} reset", None, "timer"),
                       (MOVER_EVENTS[button][0], button, button), (MOVER_EVENTS[hatch][0], hatch, "Hatch"))
        script.add([f"-- The spike pits (MM9 PropDamager, {SPIKE_DAMAGE} per second while touching): the pad strikes, and a "
                    "timer strikes every second",
                    "-- while the party stays on the spikes."])
        pads = {p["anchor"]: p for p in build.content.report["pads"]}
        for name, event in SPIKE_PADS.items():
            timer = next(timers)
            pad = pads[name]
            half_x, half_y = pad["size"][0] / 2 + SPIKE_MARGIN, pad["size"][1] / 2 + SPIKE_MARGIN
            box = (f"{int(pad['centre'][0] - half_x)}, {int(pad['centre'][1] - half_y)}, "
                   f"{int(pad['centre'][0] + half_x)}, {int(pad['centre'][1] + half_y)}")
            strike = (f"evt.DamagePlayer(Players.All, const.Damage.Physical, {SPIKE_DAMAGE}); "
                      "set(\"SpikeHits\", var(\"SpikeHits\") + 1)")
            script.add([f"handlers[{event}] = function()   -- {name}",
                        f"    if var(\"{name}\") == 1 then return end",
                        f"    set(\"{name}\", 1)",
                        f"    {strike}",
                        f"    evt.StartTimer({timer}, seconds(1))",
                        "end",
                        f"handlers[{timer}] = function()",
                        f"    evt.StopTimer({timer})",
                        f"    if var(\"{name}\") ~= 1 then return end",
                        f"    if partyIn({box}) then",
                        f"        {strike}",
                        f"        evt.StartTimer({timer}, seconds(1))",
                        "    else",
                        f"        set(\"{name}\", 0)",
                        "    end",
                        "end"],
                       (event, name, None), (timer, f"{name} strike", None, "timer"))

    def script_gate(self, script):
        script.add([
            "",
            "-- The gate is an airlock: the outer leaves stand apart (built shut, starting open) and the inner ones shut.",
            "-- SwitchLever0 slides LeverPanel and LeverPanel0 aside, PanelLever unlocks Switch0 and Switch1, and either",
            "-- switch shuts the outer gate and opens the inner one (MM9: one after the other), or the reverse.",
            "handlers[71] = function()",
            "    if var(\"SwitchLever0\") == 1 then return end",
            "    set(\"SwitchLever0\", 1)",
            "    open(\"SwitchLever0\"); open(\"LeverPanel\"); open(\"LeverPanel0\")",
            "end",
            "handlers[72] = function()",
            "    if var(\"PanelLever\") == 1 then return end",
            "    set(\"PanelLever\", 1)",
            "    open(\"PanelLever\")",
            "end",
            "local function gateSwitch(name)",
            "    if var(\"PanelLever\") == 0 then evt.StatusText(\"The switch is locked.\") return end",
            "    if var(\"Gate\") == 0 then",
            "        set(\"Gate\", 1)",
            "        open(\"Switch0\"); open(\"Switch1\")",
            "        close(\"Outerdoor0\"); close(\"Outerdoor1\"); open(\"Innerdoor0\"); open(\"Innerdoor1\")",
            "    else",
            "        set(\"Gate\", 0)",
            "        close(\"Switch0\"); close(\"Switch1\")",
            "        open(\"Outerdoor0\"); open(\"Outerdoor1\"); close(\"Innerdoor0\"); close(\"Innerdoor1\")",
            "    end",
            "end",
            "handlers[73] = function() gateSwitch(\"Switch0\") end",
            "handlers[74] = function() gateSwitch(\"Switch1\") end",
            "-- The leaves (not MM9): once both levers are pulled a click on the gate works it like a switch, so a party",
            "-- in the airlock does not have to go back out to Switch0 behind its slid panel.",
            "handlers[89] = function()",
            "    if var(\"SwitchLever0\") == 0 or var(\"PanelLever\") == 0 then",
            "        evt.StatusText(\"The gate is locked.\")",
            "        return",
            "    end",
            "    gateSwitch(\"Gate\")",
            "end",
            ""], (71, "Lever", "Lever"), (72, "Lever", "Lever"), (73, "Switch", "Switch"), (74, "Switch", "Switch"),
            (89, "Gate", "Gate"))

    def script_cages(self, script, build):
        actor = {a["anchor"]: a["actor_index"] for a in build.content.report["actors"]}
        movers = {m["group"]: m for m in build.movers}
        # KingKong.scr: the trigger sends ForceBreak to the cage's first monster, whose script destroys the cage
        # (CritterBreakOut0/1, its ScriptParams); a dead monster takes no message (MM9.receives), so its cage stands.
        lines = ["-- The cages: stepping near them breaks the walls (CritterBreakOut0/1 sink into the floor and wall)",
                 "-- and the caged Nagate Hatchlings and Airborne Ickies (KingKong.scr) come out. The first monster breaks",
                 "-- its cage (ForceBreak): once it is dead the cage stands. :RushCage roars where it stands",
                 "-- (dragonredrattack3.wav) and :BreakCage swings hattack1 once the cage is gone (MM9 destroys it at",
                 "-- once; here the swing waits for the wall to sink). The Nagate's hattack1 is its attack_melee;",
                 "-- FLYINGICKY.abc has no hattack1, so the Icky breaks out without a swing.",
                 "local function rushCage(actorIndex)",
                 "    local x, y, z = evt.GetMapActorPosition(actorIndex)",
                 "    if x ~= nil then",
                 "        evt.PlaySoundName(\"animsounds/dragonredrattack3.wav\", math.floor(x), math.floor(y), "
                 "math.floor(z))",
                 "    end",
                 "end"]
        registrations = [(75, "TriggerNagateBust", None), (76, "TriggerIckyBust", None)]
        for event, trigger, breaker, cage, swing in (
                (75, "TriggerNagateBust", "BustOutNagate0", "CritterBreakOut0", "attack_melee"),
                (76, "TriggerIckyBust", "BustOutIcky0", "CritterBreakOut1", None)):
            lines += [f"handlers[{event}] = function()",
                      f"    if var(\"{trigger}\") ~= 0 then return end",
                      f"    set(\"{trigger}\", 1)",
                      f"    if MM9.receives(\"anskramkeep\", \"{breaker}\", \"ForceBreak\", {actor[breaker]}) then",
                      f"        rushCage({actor[breaker]})",
                      f"        open(\"{cage}\")"]
            if swing is not None:
                timer = CAGE_SWING_TIMER
                sink = movers[cage]["move_length"] / movers[cage]["open_speed"]
                lines += [f"        evt.StartTimer({timer}, seconds({sink:.2f}))   -- {cage} has sunk",
                          "    end",
                          "end",
                          f"handlers[{timer}] = function()",
                          f"    evt.StopTimer({timer})",
                          f"    evt.PlayActorClip({actor[breaker]}, \"{swing}\")   -- PlayAnim hattack1",
                          "end"]
                registrations.append((timer, f"{breaker} hattack1", None, "timer"))
            else:
                lines += ["    end", "end"]
        script.add(lines + [""], *registrations)

    def script_imps(self, script, build):
        gates = len(self.gates)
        actor = {a["anchor"]: a["actor_index"] for a in build.content.report["actors"]}
        lines = [f"-- The Imp gates (AK_ImpGate.scr on ImpGateSpawner0-7): a touch trigger starts its gate; it sends "
                 f"{IMPS_PER_GATE} Imps one",
                 "-- after another, each when the last is dead; then its fire goes out. When all eight are out, the Giant Imp",
                 "-- (AK_GiantImp.scr) and its two guards (AK_GiantImpGuard.scr, friends of the party) appear when the party",
                 "-- crosses TriggerGiantImp in the north hall: the Floordoor slabs fall (MM9 destroys them) and the lift",
                 "-- ExitStairs raises it from its shaft. Gate states: 0 waiting, 1 sending, 2 done. Each gate gives its key",
                 f"-- ({GATE_KEY}-{GATE_KEY + 7}) and the last one the quest key {QUEST_KEY} (Anskrammainline.scr).",
                 "local GATES = {"]
        for k, gate in enumerate(self.gates):
            lines.append(f"    [{k}] = {{position = {lua.point(gate['position'])}, count = {gate['count']}}},   "
                         f"-- {gate['spawner']}, {gate['fire']}")
        lines += ["}",
                  "local function sendImp(k)",
                  "    local gate = GATES[k]",
                  f"    local sent = evt.SummonMonstersById({{monster = {IMP_MONSTER}, x = gate.position[1], "
                  f"y = gate.position[2], z = gate.position[3], radius = 64, group = {GATE_GROUP} + k, count = 1, "
                  "effect = \"mm9:fireblue\"})   -- :Spawn: DoClientFX hCreature, SPELL_BLUEFIRE",
                  "    set(\"ImpsSummoned\", var(\"ImpsSummoned\") + sent)",
                  "    set(\"ImpGateSent\" .. k, var(\"ImpGateSent\" .. k) + 1)",
                  "end",
                  "local function startGate(k)",
                  f"    if var(\"ImpGate\" .. k) ~= 0 or MM9.hasKey({GATE_KEY} + k) == 1 then return end",
                  "    set(\"ImpGate\" .. k, 1)",
                  "    sendImp(k)",
                  "end"]
        registrations = []
        for event, k in sorted(self.gate_triggers.items()):
            anchor = next(p["anchor"] for p in self.pads_report if p["event"] == event)
            lines.append(f"handlers[{event}] = function() startGate({k}) end   -- {anchor} -> "
                         f"{self.gates[k]['spawner']}")
            registrations.append((event, anchor, None))
        lines += [f"handlers[{KILL_HOOK_EVENT}] = function()   -- any monster killed",
                  f"    for k = 0, {gates - 1} do",
                  f"        if var(\"ImpGate\" .. k) == 1 and evt.CheckMonstersKilled(ActorKillCheck.Group, "
                  f"{GATE_GROUP} + k, 0, false) then",
                  "            if var(\"ImpGateSent\" .. k) < GATES[k].count then",
                  "                sendImp(k)",
                  "            else",
                  "                set(\"ImpGate\" .. k, 2)",
                  f"                evt.SetSprite({FIRE_COG} + k, false)",
                  f"                MM9.giveKey({GATE_KEY} + k)",
                  "                local done = 0",
                  f"                for gate = 0, {gates - 1} do done = done + MM9.hasKey({GATE_KEY} + gate) end",
                  f"                if done == {gates} then MM9.giveKey({QUEST_KEY}) end",
                  "            end",
                  "        end",
                  "    end",
                  "end",
                  "handlers[90] = function()   -- TriggerGiantImp",
                  f"    if var(\"GiantImp\") == 1 or MM9.hasKey({QUEST_KEY}) == 0 then return end",
                  "    set(\"GiantImp\", 1)",
                  "    " + "; ".join(f"open(\"{name}\")" for name in FLOORDOORS),
                  "    open(\"ExitStairs\")",
                  # TriggerGiantImp's appear to the Giant Imp, and the slabs' death triggers' appear (Floordoor2 ->
                  # GiantImpGuard1, Floordoor3 -> GiantImpGuard0): a dead receiver takes none (MM9.receives).
                  *[f"    if MM9.receives(\"anskramkeep\", \"{name}\", \"appear\", {actor[name]}) then "
                    f"evt.SetMonsterBit({actor[name]}, MonsterBits.Invisible, 0)"
                    # AK_GiantImp.scr :StartScene: DoClientFX g_hMyObject, SPELL_BLACKSMOKE as it shows
                    + (f"; MM9.clientFx({actor[name]}, \"mm9:blacksmoke\")" if name == "GiantImp" else "") + " end"
                    for name in ("GiantImp", "GiantImpGuard1", "GiantImpGuard0")],
                  "end",
                  ""]
        script.add(lines, *registrations, (90, "TriggerGiantImp", None))
        letters = ["-- The scrolls (BookLetter.scr :OnUse DoLetter <row>): MM9's BOOK AND SCROLL TEXT.csv."]
        for name, (event, number) in EV_LETTERS.items():
            title, text = letter(number)
            body = (title + "\n\n" + text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            letters.append(f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0); "
                           f"evt.SimpleMessage(\"{body}\") end   -- {name}")
        script.add(letters + [""], *[(event, "Letter", "Letter") for event, _ in EV_LETTERS.values()])

    def script_jukebox(self, script, timers):
        timer = next(timers)
        sounds = ", ".join(f'"{name}"' for name in JUKEBOX_SOUNDS)
        script.add([
            "-- DungeonJukebox.scr (the ScriptObject DungeonJukebox): every 2-8 minutes (GetRandomInt 2, 8 x 60 s) one of its",
            "-- sounds plays one unit behind the party (PlaySound radius 1/500, Volume 100: at full volume). Nothing sends",
            "-- its Play, On or Off triggers.",
            f"local JUKEBOX = {{{sounds}}}",
            f"local function startJukebox() evt.StartTimer({timer}, seconds(evt.RandomBetween(2, 8, 1) * 60)) end",
            f"handlers[{timer}] = function()",
            "    evt.PlaySoundName(JUKEBOX[evt.RandomBetween(1, #JUKEBOX, 1)], 0, 0, 0)",
            "    startJukebox()",
            "end",
            ""], (timer, "Dungeon jukebox", None, "timer"))

    def script_hints(self, script, timers):
        gates, timer = len(self.gates), next(timers)
        cogs = ", ".join(str(cog) for cog in self.hints.values())
        script.add([
            f"-- The PerceptionBrushes: the red glow over a trap shows to a party with Perception {self.hint_difficulty} or "
            "better (MM9's PerceptionValue;",
            "-- the BLV holds them visible so that they are lightmapped). Checked on load and every 3 s.",
            f"local HINTS = {{{cogs}}}",
            "local function updateHints()",
            f"    local want = evt.CheckSkill({PERCEPTION_SKILL}, 0, {self.hint_difficulty}) and 2 or 1",
            "    if var(\"PerceptionHints\") == want then return end",
            "    set(\"PerceptionHints\", want)",
            "    for _, cog in ipairs(HINTS) do evt.SetFacetBit(cog, FacetBits.Invisible, want == 1) end",
            "end",
            f"handlers[{timer}] = updateHints",
            "handlers[1] = function()   -- map load: fires of the finished gates stay out",
            f"    for k = 0, {gates - 1} do",
            f"        if MM9.hasKey({GATE_KEY} + k) == 1 then evt.SetSprite({FIRE_COG} + k, false) end",
            "    end",
            "    updateHints()",
            "    startJukebox()",
            "end",
            ""], (timer, "Perception hints", None, "timer"), (1, "Map load", None))


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, AnskramKeep()))
