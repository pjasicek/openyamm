#!/usr/bin/env python3
"""
Isle of Ashes, MM9 rework: the story's actors and the book's cinema for the BLV (../mm9r_isleofashes_blv/convert.py).

- the story actors: the DAT actors the chain needs (the DoRude NPCs, the actors whose death messages a script object,
  the actors a story trigger addresses), which convert.py places itself from the old import's records;
- the book's cinema (IsleAshesBook.scr, IA_Camera2.scr) as the cinematic book_sinking, isleofashes.cinematics.yml,
  and the MM9 sounds it plays.

The map Lua is the BLV's hand port, ../mm9r_isleofashes_blv/regionlua.py (2026-11-06). This module no longer writes
Lua: the generic story runtime (story.lua, the generated Isle.* tables) and the compiled RUDE hooks are gone, and with
them the ODM pilot in this folder, which no longer builds (README.md).
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
sys.path.insert(0, str(ROOT / "level_generation/projects/mm9r_common"))
import cinematics  # noqa: E402
import generate_mm9_events as mm9_events  # noqa: E402

RAW_OBJECTS = ROOT / "assets_editor_dev/worlds/mm9/maps/isleofashes.raw_objects.yml"
# The old ODM import's scene: its records (every placed actor with its DAT object index) are what the story places
# from. Since the BLV was promoted into assets_dev (2026-11-06) the old import's inputs live in assets_editor_dev
# (restored from the promotion backup, TABLE_CONSISTENCY_20261106.md).
OLD_SCENES = (ROOT / "assets_editor_dev/worlds/mm9/maps/isleofashes.scene.yml",)


def old_scene_path() -> Path:
    for path in OLD_SCENES:
        if path.is_file() and re.search(r'geometry_file:\s*"?isleofashes\.odm', path.read_text()):
            return path
    raise FileNotFoundError(f"no old ODM import scene of Isle of Ashes among {[str(p) for p in OLD_SCENES]}")


SOUNDS = ROOT / "mm9/extracted/SOUNDS/SOUNDS"

# The DAT triggers of the chain: the bunker's Bone Thrashers rise (Trigger2), the Lich summons on the road
# (TriggerStarters), the islet's explosions (TriggerEffects, sent by FortWall0's death). Trigger1 raises the west
# beach's BoneThrasher0 the same way (AutoResurrect.Scr, 2026-11-05). Trigger0 ("GetPlayer" to Peter, an ordinary
# Skeletoid who sees the party anyway) stays with the general population.
STORY_TRIGGERS = ("Trigger1", "Trigger2", "TriggerStarters", "TriggerEffects")
OBJECT_EVENT_BASE = 30000               # an object's Use event: 30000 + source object index (regionlua.py)
# IsleAshesBook.scr's cinema as the cinematic book_sinking (worlds/mm9/maps/isleofashes.cinematics.yml): the map
# events of its gameplay steps (regionlua.py; they also run on a skip) and the event that runs when it ends.
CINEMA_ID = "book_sinking"
CINEMA_EVENTS = {"monsters": 31010, "fortWall": 31011, "shooter": 31012, "shooter0": 31013, "sink": 31014,
                 "exit": 31015}
CINEMA_DONE_EVENT = 31019
FLYER_CLASSES = ("DragonFly", "DragonFlyMite", "FireDragonFly")
FLYER_CLEARANCE = 128                   # a flyer floats at least this far above our ground


class Objects:
    def __init__(self):
        raw = yaml.load(RAW_OBJECTS.read_text(), Loader=yaml.CSafeLoader)["objects"]
        self.by_index = {}
        self.by_name = {}
        for node in raw:
            values, _ = mm9_events.object_properties(node)
            entry = {"index": int(node["object_index"]), "class": str(node["name"]), "values": values}
            self.by_index[entry["index"]] = entry
            if values.get("Name"):
                self.by_name.setdefault(str(values["Name"]), entry)

    def named(self, name):
        return self.by_name[name]


def to_map(position, transform):
    """A LithTech position in this map's frame (convert.py TRANSFORM)."""
    scale = transform["scale"]
    return (position[0] * scale - transform["offset_x"], position[2] * scale - transform["offset_y"],
            (position[1] - transform["sea_level_lt"]) * scale)


def direction(rotation):
    """A LithTech rotation's forward vector in this frame (LithTech: pitch about x, yaw about y; x, z, y here)."""
    pitch, yaw = rotation[0], rotation[1]
    return (math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), -math.sin(pitch))


class Story:
    """The story's actors and cinema for ../mm9r_isleofashes_blv/convert.py."""

    # The story NPCs' own MM9 rows (monster data and descriptor share the id; their 3D models bind by descriptor:
    # level_generation/creatures/mm9_{yrsa,forad,annud}_claude). The old scene points them at MM6-MM8 stand-ins.
    NPC_ROWS = {46: 9254, 61: 9252, 747: 9054}      # Yrsa the Troll, Forad Darre, Annud Redeye (MONSTERS.txt 54)

    def __init__(self, transform):
        self.transform = transform
        self.objects = Objects()
        self.old_scene = yaml.load(old_scene_path().read_text(), Loader=yaml.CSafeLoader)
        self.old_actors = {a["mm9_source_object_index"]: a for a in self.old_scene["initial_state"]["actors"]}

    # --- Scene content ----------------------------------------------------------------------------------------------

    def story_actor_sources(self) -> list[int]:
        """The DAT actors of the chain: the DoRude NPCs, the actors whose death messages a script object (KillControl's
        dragonflies) and the actors the story triggers address (Trigger2's Bone Thrashers, the Lich)."""
        sources = []
        script_objects = {e["values"].get("Name") for e in self.objects.by_index.values() if e["class"] == "ScriptObject"}
        for index, entry in sorted(self.objects.by_index.items()):
            values = entry["values"]
            if index not in self.old_actors:
                continue
            if mm9_events.bool_property(values.get("DoRude"), False) or values.get("DeathTriggerTarget") in script_objects:
                sources.append(index)
        for trigger in STORY_TRIGGERS:
            for target, _ in self.trigger_messages(self.objects.named(trigger)["values"]):
                entry = self.objects.by_name.get(target)
                if entry is not None and entry["index"] in self.old_actors and entry["index"] not in sources:
                    sources.append(entry["index"])
        return sources

    @staticmethod
    def trigger_messages(values):
        pairs = []
        for number in range(1, 11):
            target, message = values.get(f"TargetName{number}"), values.get(f"MessageName{number}")
            if target and message:
                pairs.append((str(target), str(message)))
        return pairs

    # --- Cinematics -------------------------------------------------------------------------------------------------

    def cinematics(self) -> list[cinematics.Cinematic]:
        """IsleAshesBook.scr's cinema (OnUse to FadeOut2) from the DAT cameras: Camera0, Camera1 and Camera2 fixed at
        their DAT poses, Camera2's Pan (IA_Camera2.scr), then Camera3; the fades, the sounds and the gameplay steps
        as map events (regionlua.py) at the script's waits. Seconds from the use: 0 OnUse, 1 StartDestroy, 1.2 Shoot,
        2.2 Camera1, 3.2 Shoot2, 4.2 Camera2, 4.5 OnSink, 8.5 OnCrane (the pan), 12 OnCrane2 (the 3.5 s CraneShot
        wait), 16 FadeOut, 17 FadeOut2."""
        scale = self.transform["scale"]

        def camera(name):
            values = self.objects.named(name)["values"]
            fov = cinematics.vertical_fov(float(values.get("FOV") or 90.0))
            return (to_map(values["Pos"], self.transform), direction(values.get("Rotation") or [0, 0, 0]),
                    round(fov, 1))

        eye0, forward0, fov0 = camera("Camera0")
        eye1, forward1, fov1 = camera("Camera1")
        eye2, forward2, fov2 = camera("Camera2")
        eye3, forward3, fov3 = camera("Camera3")
        # IA_Camera2.scr:30-40 OnPlay: MoveToPos (Camera3's x, x, z) at 100 (the script passes Xpos as y, so MM9's
        # crane also sinks to y 184 LT), FaceObject Boat at 20 degrees a second; 3.5 s later the book's Crane.
        camera3_lt = self.objects.named("Camera3")["values"]["Pos"]
        pan_target = to_map([camera3_lt[0], camera3_lt[0], camera3_lt[2]], self.transform)
        pan_seconds = 3.5
        pan_eye, _ = cinematics.move_to_pos(eye2, pan_target, 100.0 * scale, pan_seconds)
        # FaceObject follows the boat, which sails from OnSink (4.5 s) to BoatMarker's x and z at 100 (IS_Boat.scr):
        # aim where it is at the pan's end (12 s); our boat glides the same way (regionlua.py boatMove).
        boat = to_map(self.objects.named("Boat")["values"]["Pos"], self.transform)
        marker = to_map(self.objects.named("BoatMarker")["values"]["Pos"], self.transform)
        sail = (marker[0] - boat[0], marker[1] - boat[1])
        sail_length = math.hypot(*sail)
        sailed = min(sail_length, 100.0 * scale * (12.0 - 4.5))
        boat = (boat[0] + sail[0] / sail_length * sailed, boat[1] + sail[1] / sail_length * sailed, boat[2])
        pan_forward, turn_seconds = cinematics.face_toward(forward2, pan_eye, boat, 20.0, pan_seconds)
        keys = [(0.0, eye2, {"direction": forward2, "fov": fov2})]
        if 0.0 < turn_seconds < pan_seconds:
            # The turn ends before the move: a key where it does, on the line at that time.
            turned_eye, _ = cinematics.move_to_pos(eye2, pan_target, 100.0 * scale, turn_seconds)
            keys.append((turn_seconds, turned_eye, {"direction": pan_forward, "fov": fov2}))
        keys.append((pan_seconds, pan_eye, {"direction": pan_forward, "fov": fov2}))

        events = CINEMA_EVENTS
        cinema = cinematics.Cinematic(CINEMA_ID, source="IsleAshesBook.scr :OnUse..:FadeOut2, IA_Camera2.scr")
        cinema.fixed(2.2, eye0, direction=forward0, fov=fov0, note="Camera0 (OnUse)")
        cinema.fixed(2.0, eye1, direction=forward1, fov=fov1, note="Camera1")
        cinema.fixed(4.3, eye2, direction=forward2, fov=fov2, note="Camera2")
        cinema.moving(pan_seconds, keys, easing="linear", note="Camera2 Pan (IA_Camera2.scr)")
        cinema.fixed(5.0, eye3, direction=forward3, fov=fov3, note="Camera3 (OnCrane2)")
        # OnUse: ScreenFadeout 1 and ScreenFadeIn 1 in one step: from black over a second.
        cinema.fade(0.0, "in", 1.0, note="OnUse ScreenFadeout 1, ScreenFadeIn 1")
        cinema.event(0.0, events["monsters"], note="OnUse DestroyMonsters")
        cinema.event(1.0, events["fortWall"], note="StartDestroy: FortWall destroy")
        cinema.event(1.2, events["shooter"], note="Shoot: Shooter on")
        cinema.event(3.2, events["shooter0"], note="Shoot2: Shooter0 on")
        cinema.sound(3.2, "sounds\\spells\\ebolt01.wav")
        cinema.event(4.5, events["sink"], note="OnSink: FortWall0, Terrain3, Boat, key 28, 5200 experience")
        cinema.sound(4.5, "sounds\\spells\\eblast03.wav")
        cinema.sound(4.5, "sounds\\events\\drown01.wav")
        cinema.sound(4.5, "sounds\\ambient\\fire\\forrestfireloop.wav")
        cinema.sound(12.0, "sounds\\events\\drown01.wav", note="OnCrane2")
        cinema.fade(16.0, "out", 1.0, note="FadeOut")
        cinema.event(17.0, events["exit"], note="FadeOut2: ExitTrigger1 trigger (Sturmford)")
        return [cinema]

    def cinematics_text(self) -> str:
        return cinematics.to_yaml(self.cinematics(), source="mm9r_isleofashes/story.py from ISLEOFASHES.dat")

    # --- Sounds -----------------------------------------------------------------------------------------------------

    def sound_names(self) -> list[str]:
        """The MM9 sounds the cinematic plays (its sound cues; quest.wav, which regionlua.py plays, is the engine's
        quest cue: MM9.playSound)."""
        names = [cue["sound"] for cinema in self.cinematics() for cue in cinema.cues if "sound" in cue]
        return sorted({name for name in names if not name.lower().endswith("quest.wav")})

    def install_sounds(self, review_root) -> list[str]:
        """The cinematic's sounds that the world's audio lacks at the scripts' paths (IsleAshesBook.scr names
        spells\\ebolt01.wav, which MM9 keeps under weapons\\), copied from MM9's sound files into the review root."""
        index = mm9_events.build_source_sound_index(SOUNDS)
        installed = []
        for name in self.sound_names():
            relative = mm9_events.normalize_mm9_sound_name(name.replace("\\\\", "\\")).lower()
            target = Path("worlds/mm9/audio") / relative
            if review_root.mirror_path(target).is_file():
                continue
            source = mm9_events.find_source_sound_path(index, relative)
            if source is None:
                raise SystemExit(f"story sound {name} has no MM9 source")
            review_root.install(target, source.read_bytes())
            installed.append(relative)
        return installed
