"""
Thronheim City's two MM9 scenes (README "Cinematics"):

- `council_argument`: ARGUMENT.scr's war council (Argueman, started by KiraDoor2's "start" with keys 90 and 91 and
  not 40) as an in-engine cinematic (devdocs/mm9_rework/MM9_CUTSCENES.md, ../mm9r_common/cutscenes.py). MM9 films it
  on a copy of Kira's council hall under the city (the stage, y -32..260 LT: not built); the stage is the hall moved
  by STAGE_TO_HALL_LT, so its cameras, markers and actors are moved into the hall and the scene plays there. The
  stage's Kira, Bjarni, Sigmund, Forad, Tryygva and Markel are hidden actors in the hall (convert.py), shown for the
  scene in place of the posed Jarl decorations; Sven stays his decoration (his model is seated on its own chair).
  Timing: the 24 :OnDone callbacks (Camera0's MoveToPos arrival, the .abc key events of the Sc2_* animations, the
  sword sound's end, 18.wav's end) and the script's waits, from the DAT, the .abc files and the voice wavs.
- Knut Fastmouth's soapbox rant (KnutSpeech.scr, Ake.scr): ambient, not a cinematic (MM9 keeps the player in control
  for its 91 s; a cinematic locks input and saving): when Knut first finds the party, key 114, his voice at him and
  his talk clip, Ake's heckles at Ake on MM9's waits; map Lua on its own timer (knut_lua).

convert.py builds both through this module (scenes(), extra_lua(), stage_actor_objects()); cinematics_pilot.py
tests the same code against the installed map.
"""

from __future__ import annotations

import math
import sys
import wave
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import cutscenes  # noqa: E402
from cutscenes import MM9_CAMERA_FOV, Frame, Objects, Scene, abc_animation, move_to_pos  # noqa: E402

STEM = "thronheimcity"
CINEMA_ID = "council_argument"
EVENT_BASE = 36000                  # 36000 done, 36001.. steps (36000 + 50 k per scene, brief)
T_YRSA = 36040                      # ARG_Yrsa.scr :OnAppear's waits after the scene (a map timer)
T_KNUT = 36050                      # KnutSpeech.scr / Ake.scr: Knut's rant (a map timer, second scene's range)
VOICES = cutscenes.ROOT / "mm9/extracted/VOICES/VOICES"
VOICE = "voices\\cinema\\theargument\\{}.wav"

# The stage (ARGUMENT.scr's set under the city) is Kira's hall moved by this (LT x, y, z): the floors (-32 / 1280),
# table tops, candles, walls, Jarls and chairs of the two agree to 8 LT (Prop2 92,-20,56 / Prop17 -4300,1316,6520 ...).
STAGE_TO_HALL_LT = (-4400.0, 1312.0, 6464.0)
# The stage actors placed in the hall (convert.py): role, DAT name, MM9 MONSTERS row, name
STAGE_ACTORS = (("kira", "Kira", 251, "Kira the Cold"), ("bjarni", "Bjarni", 246, "Bjarni Thorvaldssen"),
                ("sigmund", "Sigmund", 247, "Sigmund the Stressed"), ("forad", "Forad", 252, "Forad Darre"),
                ("tryygva", "Tryygva", 250, "Tryggva Ravenlocks"), ("markel", "Markel", 248, "Markel the Great"))
# The seated Jarls (props.json's posed people, actors on their HD models since 2026-11-08: rude_props.py) play their
# roles themselves; only Kira has a stage actor (she stands at the fire and walks). Sven sits through it.
POSED_JARLS = {"bjarni": "BjarniProp", "sigmund": "SigmundProp", "forad": "ForadProp", "tryygva": "TryygvaProp",
               "markel": "MarkeProp"}
KIRA_SWORD = "worlds/mm9/models/mm9_item_kirasword.glb"   # ARG_Kira.scr's AttachProp kirasword.ABC
ABC = {"kira": "KIRA", "markel": "MARKEL", "bjarni": "BJARNI", "sigmund": "SIGMUND", "forad": "FORADDARRE",
       "tryygva": "TRYGGVA"}
# MM9 animation -> the GLB clip (actors.yml script_clips; level_generation/creatures/mm9_<name>_claude)
CLIPS = {"Sc2_Bjarni1a": "ArgumentShot1A", "Sc2_Bjarni1c": "ArgumentShake", "Sc2_Bjarni2": "ArgumentSpeak2",
         "Sc2_Bjarni9": "ArgumentSpeak9", "Sc2_bjarni15": "ArgumentSpeak16", "Sc2_Forad6": "ArgumentSpeak6",
         "Sc2_Forad26": "ArgumentSpeak20", "Sc2_MARKEL08": "Sc2_Markel08", "Sc2_MARKEL10": "Sc2_Markel10",
         "Sc2_MARKEL13": "Sc2_Markel13", "Sc2_MARKEL15": "Sc2_Markel15", "Sc2_Kira20-23": "Sc2_KIRA20_23",
         "Sc2_Kira22": "Sc2_KIRA22", "static_die2": "StaticDie"}
WALK_LT = 50.0                      # MONSTERS.txt WalkVelocity of Kira and Markel (rows 251, 248)
WALKTO_REACH_LT = 8.0               # ARG_Kira/ARG_Markel.scr walkto <marker> 8: arrival within 8
# Kira's walk (stage x, z): both walk to KiraMarker1 and MM9's bodies collide; she comes round the left row of chairs
# (behind Sven's and Tryggva's) and stops facing Markel from outside, where Camera9 and Camera10 ("behind Markel")
# frame her
KIRA_PATH_LT = ((-150.0, 100.0), (-150.0, -5.0))


def voice_seconds(number: str) -> float:
    path = VOICES / "CINEMA/THEARGUMENT" / f"{number.upper()}.wav"
    with wave.open(str(path)) as stream:
        return stream.getnframes() / float(stream.getframerate())


def hall_lt(lt) -> tuple[float, float, float]:
    return tuple(float(v) + d for v, d in zip(lt, STAGE_TO_HALL_LT))


def stage_actor_objects(objects_by_name: dict) -> list[tuple[str, dict, int, str]]:
    """The stage actors as hall objects for convert.py's content.actor: (role, object with its Pos moved into the
    hall, MM9 row, name). objects_by_name: the converter's source.by_name (lowercase names)."""
    out = []
    for role, name, row, title in STAGE_ACTORS:
        o = objects_by_name[name.lower()]
        properties = dict(o["properties"], Pos=list(hall_lt(o["properties"]["Pos"])), Visible=0)
        out.append((role, {"name": f"Stage{name}", "class": o["class"], "index": o["index"],
                           "properties": properties}, row, title))
    return out


# --- the cinematic --------------------------------------------------------------------------------------------------
class _Timeline:
    """ARGUMENT.scr's chain, followed in seconds: the Done callbacks and the cameras switched at each."""

    def __init__(self, scene: Scene, actor: dict, feet: dict, objects: Objects, frame: Frame):
        self.scene, self.cinema, self.actor, self.feet = scene, scene.cinema, actor, feet
        self.objects, self.frame = objects, frame
        self.cuts: list[tuple[float, str]] = []        # (seconds, camera name)
        self.clap = 0

    def native(self, name: str):
        return self.frame.point(hall_lt(self.objects.named(name)["values"]["Pos"]))

    def native_lt(self, stage_xz):
        """A stage (x, z) point in the hall's native frame (its height left to the caller)."""
        return self.frame.point(hall_lt((stage_xz[0], 0.0, stage_xz[1])))

    def camera(self, name: str, pos_from: str | None = None):
        values = self.objects.named(name)["values"]
        eye = self.native(pos_from or name)
        return eye, self.frame.direction(values.get("Rotation"))

    def cut(self, at: float, name: str) -> None:
        self.cuts.append((at, name))

    def clip(self, at: float, role: str, clip: str, loop: bool = False, note: str = "") -> None:
        self.cinema._cue(at, note, actor=self.actor[role], action="clip", clip=CLIPS.get(clip, clip), loop=loop)

    def anim(self, at: float, role: str, animation: str, then: str | None = "Sit", note: str = "") -> dict:
        """PlayAnim <animation> then (OnIdle / Init) loopanim Sit: the clip, its key events in seconds."""
        length, events = abc_animation(ABC[role], animation)
        self.clip(at, role, animation, note=note or f"{role} {animation}")
        if then:
            self.clip(at + length, role, then, loop=True)
        keys = {}
        for seconds, event in events:
            keys.setdefault(event.lower(), at + seconds)
        keys["end"] = at + length
        return keys

    def speak(self, at: float, role: str, animation: str, voice: str, then: str | None = "Sit") -> float:
        """An actor's speech: the animation, its Voice key's wav, its Done key (the director's next step)."""
        keys = self.anim(at, role, animation, then)
        voice_at = next(t for k, t in keys.items() if k.startswith("voice"))
        self.cinema.sound(voice_at, VOICE.format(voice), note=f"{role} {voice}.wav ({voice_seconds(voice):.1f} s)")
        return keys["done"] if "done" in keys else keys["done2"]

    def applause(self, at: float, roles) -> None:
        """Trigger Clap: Applause (its Clap keys play a random clap01-07.wav: here in turn), then Sit."""
        for role in roles:
            keys = self.anim(at, role, "Applause", "Sit" if role != "kira" or at < 100 else "Standing")
            _, events = abc_animation(ABC[role], "Applause")
            for seconds, event in events:
                if event.lower() == "clap":
                    self.clap = self.clap % 7 + 1
                    self.cinema.sound(at + seconds, f"sounds\\events\\clap0{self.clap}.wav")
            del keys


def council_scene(actor: dict, feet: dict, cogs: dict, posed: dict | None = None) -> Scene:
    """The war council. actor: role -> scene actor index (the six stage roles, kira_cold, yrsa); feet: role -> its
    native feet [x, y, z] (the stage roles); cogs: the decorations' SetSprite cogs (citylua.prop_cogs); posed: role ->
    the Lua lines that seat a Jarl again (rude_props.load_lines: Sit, his chair's facing)."""
    posed = posed or {}
    objects = Objects.load(STEM)
    frame = Frame(PROJECT)
    scene = Scene(CINEMA_ID, EVENT_BASE, source="ARGUMENT.scr (Argueman) :OnStart..:End2 with ARG_*.scr, ARGUECAM1")
    cinema = scene.cinema
    line = _Timeline(scene, actor, feet, objects, frame)
    stage_roles = [role for role, *_ in STAGE_ACTORS]
    show = "; ".join(f"show({actor[role]}, true)" for role in stage_roles)
    hide = "; ".join(f"show({actor[role]}, false)" for role in stage_roles if role not in POSED_JARLS)
    reseat = [line.strip() for role in stage_roles if role in POSED_JARLS and role != "markel"
              for line in posed.get(role, [])]
    markel_x, markel_y, markel_z = feet["markel"]

    # :OnStart ScreenFadeOut 1, wait 1 :FadeIn (LetterBox, Camera0 On and Play, ScreenFadeIn 1).
    cinema.party(1.0, note="OnStart: ScreenFadeOut 1 on the party's view")
    cinema.fade(0.0, "out", 1.0, note="OnStart ScreenFadeOut 1")
    scene.step(0.95, "stage", "\n".join([
        "-- the seated Jarls play their parts, Kira's stage actor at her place (Kira the Cold hidden meanwhile)",
        f"show({actor['kira_cold']}, false)", show]))
    for role in stage_roles:
        line.clip(0.95, role, "Sit", loop=True)
    treaty = cogs.get("TreatyProp")
    stage_treaty = objects.named("Prop9")["values"]["Pos"]
    treaty_marker = objects.named("treatymarker")["values"]["Pos"]
    treaty_offset = [round(a - b, 1) for a, b in zip(frame.point(stage_treaty), frame.point(treaty_marker))]
    treaty_offset[2] = 0.0
    if treaty is not None:
        # Prop9 (arguetreaty.scr "treatymarker 4"): the treaty lies before Bjarni until Sigmund's Shot1A slides it
        # to the marker before Sigmund at 4 LT/s; the hall's TreatyProp lies at the marker.
        cinema._cue(0.95, "the treaty before Bjarni", decoration=treaty, offset=treaty_offset, seconds=0)
    t = 1.0
    cinema.fade(t, "in", 1.0, note="FadeIn: ScreenFadeIn 1")
    # ARGUECAM1.scr (Camera0, "CameraMarker0 40"): MoveToPos to the marker at 40 LT/s; OnArrive: Argueman Done (1).
    eye0, forward0 = line.camera("Camera0")
    marker0 = line.native("CameraMarker0")
    _, arrival = move_to_pos(eye0, marker0, frame.speed(40.0), 0.0)
    done = t + arrival
    # Done 1 :Cam1: ScreenFadeOut .5, wait .5 :Cam2b
    cinema.moving(arrival + 0.5, [(0.0, eye0, {"direction": forward0, "fov": MM9_CAMERA_FOV}),
                                  (arrival, marker0, {"direction": forward0, "fov": MM9_CAMERA_FOV})],
                  easing="linear", note="Camera0 (ARGUECAM1 Play: to CameraMarker0 at 40)")
    cinema.fade(done, "out", 0.5, note="Cam1: ScreenFadeOut .5")
    t = done + 0.5
    # :Cam2b: Camera1 On, ScreenFadeIn .5, RemoveNPC 2 (KiraCold KillMarkel swaps the hall's Markel: at the end here),
    # Bjarni Shot1A (Sc2_Bjarni1a: Sign signs, its Cam3 key is Done 2)
    line.cut(t, "Camera1")
    cinema.fade(t, "in", 0.5, note="Cam2b: ScreenFadeIn .5")
    scene.step(t, "forad", "MM9.removeHireling(2)   -- ARGUMENT.scr :Cam2b RemoveNPC 2: Forad leaves the party")
    keys = line.anim(t, "bjarni", "Sc2_Bjarni1a", note="Cam2b: Bjarni Shot1A")
    cinema.sound(keys["sign"], "sounds\\events\\signature1.wav", note="Bjarni Sign")
    done = keys["cam3"]
    # Done 2 :Cam2: Camera11, Sigmund Shot1A (the treaty slides to him, a page turns, Sc2_Sigmund1b), wait 4 :Cam2c
    line.cut(done, "Camera11")
    line.cut(done + 4.0, "Camera2")
    if treaty is not None:
        cinema._cue(done, "Prop9 play: to treatymarker at 4 LT/s", decoration=treaty, offset=[0.0, 0.0, 0.0],
                    seconds=round(math.dist(stage_treaty, treaty_marker) / 4.0, 3))
    cinema.sound(done, "sounds\\events\\bookpgturn01.wav", note="Sigmund Shot1A")
    keys = line.anim(done, "sigmund", "Sc2_Sigmund1b", note="Sigmund Shot1A")
    cinema.sound(keys["sign"], "sounds\\events\\signature2.wav", note="Sigmund Sign")
    done = keys["done"]
    # Done 3 :Cam3: Camera3, Bjarni and Sigmund shake hands, the others clap, gosub War, wait 4 :OnMarkel
    line.cut(done, "Camera3")
    line.anim(done, "bjarni", "Sc2_Bjarni1c")
    line.anim(done, "sigmund", "Sc2_Sigmund1c")
    line.applause(done, ("kira", "markel", "forad", "tryygva"))
    scene.step(done, "war", "war()   -- ARGUMENT.scr :Cam3 gosub War")
    t = done + 4.0
    # :OnMarkel: Camera4, Markel Scene2 (Sc2_MARKEL02, Voice1; wait 1.5 Book: the book opens), Done 4
    line.cut(t, "Camera4")
    done = line.speak(t, "markel", "Sc2_MARKEL02", "01")
    cinema.sound(t + 1.5, "sounds\\events\\bookopen.wav", note="ARG_Markel.scr :Book")
    # Done 4-18: the speeches, each one's Done key the next (camera, speaker, animation, voice)
    speeches = [("Camera1", "bjarni", "Sc2_Bjarni2", "02"), ("Camera2", "sigmund", "Sc2_Sigmund3b", "03"),
                ("Camera4", "markel", "Sc2_MARKEL04", "04"), ("Camera5", "kira", "Sc2_KIRA5", "05"),
                ("Camera6", "forad", "Sc2_Forad6", "06"), ("Camera5", "kira", "Sc2_Kira7", "07"),
                ("Camera4", "markel", "Sc2_MARKEL08", "08"), ("Camera7", "bjarni", "Sc2_Bjarni9", "09"),
                (None, "kira", "Sc2_Kira9b", "10"), ("Camera4", "markel", "Sc2_MARKEL10", "11"),
                ("Camera5", "kira", "Sc2_KIRA12", "12"), ("Camera4", "markel", "Sc2_MARKEL13", "13"),
                ("Camera5", "kira", "Sc2_KIRA14", "14"), ("Camera4", "markel", "Sc2_MARKEL15", "15"),
                ("Camera7", "bjarni", "Sc2_bjarni15", "16")]
    for camera, role, animation, voice in speeches:
        if camera:
            line.cut(done, camera)
        start = done
        done = line.speak(start, role, animation, voice)
    # Bjarni16 also sends Markel Move: his chair slides back (the chair decoration has no cog: not moved), he walks to
    # KiraMarker1 and faces Kira (ARG_Markel.scr :OnMove, :Target)
    cinema.sound(start, "sounds\\events\\chairslide.wav", note="ARG_Markel.scr :OnMove")
    markel_from = feet["markel"]
    marker = line.native("KiraMarker1")
    marker = (marker[0], marker[1], markel_from[2])
    reach = frame.speed(WALKTO_REACH_LT)
    markel_to = _short_of(markel_from, marker, reach)
    markel_walk = math.dist(markel_from[:2], markel_to[:2]) / frame.speed(WALK_LT)
    cinema._cue(start, "Markel faces KiraMarker1", actor=actor["markel"], action="face", look_at=list(markel_to),
                seconds=0.2)
    line.clip(start, "markel", "Walking", loop=True)
    cinema.actor(start, actor["markel"], "move", to=markel_to, seconds=markel_walk, note="Markel walkto KiraMarker1")
    line.clip(start + markel_walk, "markel", "Standing", loop=True)
    cinema._cue(start + markel_walk, "ARG_Markel.scr :Target Kira", actor=actor["markel"], action="face",
                look_at_actor=actor["kira"], seconds=0.4)
    # Done 19 :KiraStand: Kira Stand (Sc2_KIRA16b; its Done2 is Done 20 :OnKiraStand: Camera8), then :Walk to
    # KiraMarker1 (target Markel), :DrawSword (Sc2_Kira17: the sword drawn at its attach key, DrawSword.wav's end is
    # Done 21 :KiraCam: Camera9), :Attack (Sc2_Kira20-23: KillMarkel; Witty: Sc2_Kira22 with 17.wav, its Done2 is
    # Done 22 :KiraCam2: Camera10 and Speak18: 18.wav, whose end is Done 23; wait .5 ClapTrigger)
    # ARG_Kira.scr :OnStand: AttachProp kirasword Sheath (her sword at her hip only once she stands)
    scene.step(done, "kira_sheath", f"evt.AttachActorItem({actor['kira']}, \"{KIRA_SWORD}\", \"Socket_Sheath\")")
    keys = line.anim(done, "kira", "Sc2_KIRA16b", then=None, note="KiraStand: Sc2_KIRA16b")
    line.cut(keys["done2"], "Camera8")
    walk_start = keys["end"]
    # MM9's walkto paths round the table: KIRA_PATH_LT
    path = [feet["kira"]] + [_feet(frame, line.native_lt(corner), feet["kira"]) for corner in KIRA_PATH_LT]
    t = walk_start
    line.clip(t, "kira", "Walking", loop=True)
    for start_point, end_point in zip(path, path[1:]):
        seconds = math.dist(start_point[:2], end_point[:2]) / frame.speed(WALK_LT)
        cinema._cue(t, "Kira turns along her walk", actor=actor["kira"], action="face", look_at=list(end_point),
                    seconds=0.3)
        cinema.actor(t, actor["kira"], "move", to=end_point, seconds=seconds, note="Kira walkto KiraMarker1")
        t += seconds
    cinema._cue(t, "Kira faces Markel", actor=actor["kira"], action="face", look_at_actor=actor["markel"],
                seconds=0.2)
    keys = line.anim(t, "kira", "Sc2_Kira17", then=None, note="DrawSword: Sc2_Kira17")
    cinema.sound(keys["attach"], "sounds\\events\\drawsword.wav", note="OnAttach: the sword in her hand")
    # :OnAttach (Sc2_Kira17's attach key): DetachProp the sheathed sword, AttachProp kirasword RHand1
    scene.step(keys["attach"], "kira_draw", "\n".join([
        f"evt.DetachActorItem({actor['kira']}, \"Socket_Sheath\")",
        f"evt.AttachActorItem({actor['kira']}, \"{KIRA_SWORD}\", \"Socket_RHand1\")"]))
    line.cut(keys["attach"] + cutscenes.wav_seconds("sounds\\events\\drawsword.wav"), "Camera9")
    keys = line.anim(keys["end"], "kira", "Sc2_Kira20-23", then=None, note="Attack: Sc2_Kira20-23")
    kill = keys["killmarkel"]
    die = line.anim(kill, "markel", "Sc2_markel21", then="static_die2", note="Markel Kill: Sc2_markel21")
    cinema.sound(die["die"], "sounds\\weapons\\cflesh.wav", note="ARG_Markel.scr :OnDie")
    cinema.sound(die["die"], VOICE.format("16a"), note="Markel's last words")
    witty = keys["witty"]
    keys = line.anim(witty, "kira", "Sc2_Kira22", then="Standing", note="WittyRetort: Sc2_Kira22")
    cinema.sound(keys["speak17"], VOICE.format("17"), note="Kira 17.wav")
    line.applause(witty + 0.5, ("bjarni", "sigmund", "forad", "tryygva"))
    done = keys["done2"]
    line.cut(done, "Camera10")
    cinema.sound(done, VOICE.format("18"), note="Kira Speak18: 18.wav (Done 23 at its end)")
    done += voice_seconds("18")
    # Done 23 :Agree: Camera0 (at CameraMarker0, where its Play left it), the Jarls agree (Bjarni's "Yeah"), wait 2
    # :Kira19: Camera10, Sc2_Kira19 (19.wav; Done2 is Done 24 :End)
    line.cut(done, "Camera0@CameraMarker0")
    cinema.sound(done, "sounds\\events\\mm9yeah.wav", note="ARG_Bjarni.scr :OnAgree")
    for role in ("bjarni", "sigmund", "forad", "tryygva"):
        line.anim(done, role, "Agree")
    t = done + 2.0
    line.cut(t, "Camera10")
    done = line.speak(t, "kira", "Sc2_Kira19", "19", then="Standing")
    # :End: gosub War, ScreenFadeOut 1, wait 1 :End2: Camera10 Off, Yrsa appear, LetterBox false, ScreenFadeIn 1
    cinema.fade(done, "out", 1.0, note="End: ScreenFadeOut 1")
    end2 = done + 1.0
    scene.step(end2, "end", "\n".join([
        "-- :End gosub War; the hall as the scene left it: the posed Jarls back, Markel dead (NPC239.scr",
        "-- :OnKillMarkel), Kira the Cold at her place; ARG_Yrsa.scr :OnAppear: Yrsa 5 + 2 s later",
        "war()",
        f"evt.DetachActorItem({actor['kira']})   -- her sword goes with her stage actor (MM9 drops props on a load)",
        hide,
        "-- the Jarls back in their chairs, looping Sit (the scene's presentation ends with it)",
        *reseat,
        "-- :Cam2b's KillMarkel is a message to Kira the Cold: a dead one takes none (MM9.receives): Markel stays",
        f"if MM9.receives(\"thronheimcity\", \"KiraCold\", \"KillMarkel\", {actor['kira_cold']}) then",
        f"    show({actor['markel']}, false); sprite(COG.MarkeProp0, true)",
        "else",
        f"    evt.SetMapActorPosition({actor['markel']}, {markel_x}, {markel_y}, {markel_z})",
        *["    " + line.strip() for line in posed.get("markel", [])],
        "end",
        f"show({actor['kira_cold']}, true)",
        f"set(\"YrsaAppear\", 1); evt.StartTimer({T_YRSA}, seconds(5))"]))

    # The shots from the cuts
    cuts = line.cuts
    for (at, name), (until, _) in zip(cuts, cuts[1:] + [(end2, None)]):
        if name == "Camera0@CameraMarker0":
            eye, forward = line.camera("Camera0", pos_from="CameraMarker0")
        else:
            eye, forward = line.camera(name)
        cinema.fixed(until - at, eye, direction=forward, fov=MM9_CAMERA_FOV, note=name)
    cinema.party(1.0, note="End2: Camera10 Off, LetterBox false: the party's view")
    cinema.fade(end2, "in", 1.0, note="End2: ScreenFadeIn 1")
    return scene


def _feet(frame: Frame, native, like):
    return (round(native[0], 1), round(native[1], 1), like[2])


def _short_of(start, target, distance: float):
    """The point on start -> target that stops distance before target (feet; start's height)."""
    dx, dy = target[0] - start[0], target[1] - start[1]
    length = math.hypot(dx, dy)
    share = max(0.0, (length - distance) / length) if length > 1e-6 else 0.0
    return (round(start[0] + dx * share, 1), round(start[1] + dy * share, 1), start[2])


def scenes(actor: dict, feet: dict, cogs: dict, posed: dict | None = None) -> list[Scene]:
    return [council_scene(actor, feet, cogs, posed)]


# --- Lua beside the cinematic ---------------------------------------------------------------------------------------
KNUT_VOICE = "voices\\cinema\\socialism\\knutfastmouth01.wav"
KNUT_SIGHT = 1536                   # Knut's SightDistance (scene mm9_ai sight): KnutSpeech.scr's OnFoundPlayer


def _knut_schedule() -> tuple[dict, int, int]:
    """Ake.scr's heckles: Knut's :Speak triggers Ake's blabber, Ake waits 5-10 s (7.5 here) between heckles 01-05,
    each after the last ends, until Knut's :shutup (the speech's length - 5 s). Seconds after :Speak, rounded to the
    one-second timer: {second: heckle}, shutup, the speech's end."""
    speech = None
    with wave.open(str(VOICES / "CINEMA/SOCIALISM/KNUTFASTMOUTH01.wav")) as stream:
        speech = stream.getnframes() / float(stream.getframerate())
    shutup = speech - 5.0
    heckles, t, n = {}, 7.5, 0
    while t < shutup:
        number = n % 5 + 1
        with wave.open(str(VOICES / f"CINEMA/SOCIALISM/AKE0{number}.wav")) as stream:
            length = stream.getnframes() / float(stream.getframerate())
        heckles[int(round(t))] = f"0{number}"
        t += length + 7.5
        n += 1
    return heckles, int(round(shutup)), int(math.ceil(speech))


def extra_lua(actor: dict) -> tuple[list[str], list[tuple]]:
    """The map Lua beside the scenes (map timers; their handlers use the city script's locals): Yrsa's appearance
    after the council and Knut's rant. Returns (lines, registrations for lua.Script.add)."""
    yrsa, knut, ake = actor["yrsa"], actor["knut"], actor["ake"]
    heckles, shutup, speech_end = _knut_schedule()
    lines = [
        "-- ARG_Yrsa.scr :OnAppear (the council's :End2 sends appear): wait 5 :Appear2 (the summoning glow's windup),",
        "-- wait 2 :Appear2b (Town Portal's sound, she shows, fidget1), then :DoRude: key 93 (TELP 1.3), her greeting",
        "-- and RUDE 1 (council.py).",
        "local function soundAt(actorIndex, name)   -- a sound where the actor stands",
        "    local x, y, z = evt.GetMapActorPosition(actorIndex)",
        "    if x ~= nil then evt.PlaySoundName(name, math.floor(x), math.floor(y), math.floor(z)) end",
        "end",
        f"handlers[{T_YRSA}] = function()",
        "    local stage = var(\"YrsaAppear\")",
        "    if stage == 1 then",
        f"        set(\"YrsaAppear\", 2); evt.StartTimer({T_YRSA}, seconds(2))",
        f"        soundAt({yrsa}, \"magic/windup10.wav\"); MM9.clientFx({yrsa}, \"mm9:GreaterDemon\")   "
        "-- :Appear2: DoClientFX g_hMyObject, GreaterDemon",
        "    elseif stage == 2 then",
        f"        set(\"YrsaAppear\", 3); evt.StartTimer({T_YRSA}, seconds(3))",
        f"        soundAt({yrsa}, \"spells/townportal.wav\")",
        f"        if not has(185) then show({yrsa}, true); evt.PlayActorClip({yrsa}, \"Fidget\") end",
        "    elseif stage == 3 then",
        "        set(\"YrsaAppear\", 4)",
        "        if not has(185) then",
        f"            MM9.giveKey(93); MM9.playSound(\"voices/npc/npc_001.wav\"); MM9.openRude(1, {yrsa})",
        "        end",
        "    end",
        "end",
        "",
        "-- KnutSpeech.scr (Knut Fastmouth, \"Ake\") and Ake.scr: when Knut first finds the party (OnFoundPlayer:",
        f"-- within his sight, {KNUT_SIGHT}) he rants (Conv; a second later :Speak: key 114 and his 91 s speech at",
        "-- him); Ake heckles (ake01-05.wav at Ake, facing Knut) on Ake.scr's waits until :shutup, 5 s before its end.",
        "-- Ambient as in MM9 (the party keeps control); once (key 114). MM9's four-place cycle is not carried.",
        "local KNUT_HECKLES = {" + ", ".join(f"[{s}] = \"{n}\"" for s, n in sorted(heckles.items())) + "}",
        f"handlers[{T_KNUT}] = function()",
        f"    evt.StartTimer({T_KNUT}, seconds(1))",
        "    local clock = var(\"KnutClock\")",
        f"    local kx, ky, kz = evt.GetMapActorPosition({knut})",
        "    if clock < 0 or kx == nil then return end",
        "    if clock == 0 then",
        "        if has(114) then set(\"KnutClock\", -1) return end",
        f"        if not MM9.actorAlive({knut}) then return end   -- a dead Knut's OnFoundPlayer does not fire",
        "        local x, y, z = evt.GetPartyPosition()",
        f"        if (x - kx) ^ 2 + (y - ky) ^ 2 > {KNUT_SIGHT} ^ 2 or math.abs(z - kz) > 512 then return end",
        f"        evt.PlayActorClip({knut}, \"talk\", true)   -- :OnBlabber: Conv",
        "        set(\"KnutClock\", 1) return",
        "    end",
        "    clock = clock + 1",
        "    set(\"KnutClock\", clock)",
        "    local t = clock - 2   -- seconds after :Speak",
        "    if t == 0 then",
        f"        MM9.giveKey(114); soundAt({knut}, \"{KNUT_VOICE.replace(chr(92), '/')}\")",
        "        -- :Speak sends Ake blabber; his heckles run on his own waits from there: a dead Ake takes no message",
        f"        set(\"AkeHeckles\", MM9.receives(\"thronheimcity\", \"Ake\", \"blabber\", {ake}) and 1 or 0)",
        f"    elseif KNUT_HECKLES[t] ~= nil and var(\"AkeHeckles\") == 1 then",
        f"        evt.FaceActorTo({ake}, kx, ky, 0.4); evt.PlayActorClip({ake}, \"talk\")",
        f"        soundAt({ake}, \"voices/cinema/socialism/ake\" .. KNUT_HECKLES[t] .. \".wav\")",
        f"    elseif t == {shutup} then",
        f"        evt.ClearActorPresentation({knut}); evt.ClearActorPresentation({ake})   -- :shutup",
        f"    elseif t >= {speech_end} then",
        "        set(\"KnutClock\", -1)",
        "    end",
        "end",
        "",
    ]
    return lines, [(T_YRSA, "Yrsa", None, "timer"), (T_KNUT, "Knut", None, "timer")]


SOUNDS_USED = ("magic\\windup10.wav", "spells\\townportal.wav")


def install_sounds(review_root) -> list[str]:
    """The scene's MM9 sounds the world's audio lacks (Yrsa's appearance), copied from MM9's sounds into the review
    root (as the Isle of Ashes story does)."""
    sys.path.insert(0, str(cutscenes.ROOT / "tools/mm9_import_discovery"))
    import generate_mm9_events as mm9_events
    index = mm9_events.build_source_sound_index(cutscenes.SOUNDS)
    installed = []
    for name in SOUNDS_USED:
        relative = mm9_events.normalize_mm9_sound_name(name).lower()
        target = Path("worlds/mm9/audio") / relative
        if review_root.mirror_path(target).is_file():
            continue
        source = mm9_events.find_source_sound_path(index, relative)
        if source is None:
            raise SystemExit(f"council sound {name} has no MM9 source")
        review_root.install(target, source.read_bytes())
        installed.append(relative)
    return installed
