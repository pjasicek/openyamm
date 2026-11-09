#!/usr/bin/env python3
"""
Arslegard City's camera cinemas (devdocs/mm9_rework/MM9_CUTSCENES.md): the Great Gate scenes of FateMan.scr and
WritMan.scr as the cinematics `gate_fate` and `gate_writ` (worlds/mm9/maps/arslegardcity.cinematics.yml), built from
the DAT cameras and the scripts' timeline. One function, `scenes()`, serves the converter (citylua.map_script appends
the scenes' Lua, convert.py installs the yml) and the test without a conversion (cinematics_pilot.py).

Timeline (seconds from MM9's :OnStart, where the cinematic begins: the map Lua starts it at its third arrival poll,
about 2-3 s after the arrival, which stands for MM9's `wait 1 .1 OnLose`, ScreenFadeOut 1, `wait 1 2 OnStart`):

- cameras: LoseCam1.scr (Losecam4 / Losecam1: still 0.2 s, then MoveToPos CameraMarker0 at 100 LT/s; the arrival
  sends Cam2), LoseCam2.scr (Losecam2: MoveToPos CameraMarker2 at 150 at once; the arrival sends Cam3), Losecam3
  fixed (LoseCam2.scr, never played), Losecam5 (LoseCam3.scr "Losecam6 CameraMarker3": still 2 s, then MoveToPos
  Losecam6 at 100). Each camera keeps its DAT rotation (MM9's Target does not aim); fov MM9_CAMERA_FOV.
- speech: Hanndl.scr's PlayAnim ends (`Done`, `Close`, OnSpeak14) from the HANNDL.abc animation lengths, his wavs at
  the animations' SpeakN keys (OnVoiceN), the party's lines (`Playsound sVoiceN, TriggerN`) end at their wav lengths;
  Hanndl14.wav's end sends the fifth Done (OnVoice14's callback).
- MM9's bug kept: FateMan.scr :OnDone sends counter 5 to OnPC6 (and OnPC5 would replay Trigger13), so the party's
  line 05 never plays: the lines heard are 01, 02, 03, 04 and 06.
- the party's voice: MM9's getPCVoice picks one of 18 cinema voice sets (FateMan.scr :Init) by the first PC's voice.
  Our party members have MM6-MM8 voices with no MM9 cinema set, and a cinematic's timeline is fixed while the sets'
  lines differ in length (Assertive Male 2.1-3.8 s, Happy Male 1.3-2.8 s), so one fixed set: PARTY_VOICE_SET 11,
  AssertiveMale (the files and lengths from the script and the wavs).
- no subtitles: MM9 has no text of these lines (only Hanndl.scr's abridged comments; RollOverText strings and the
  cinema line texts are not in the extracted data).

Gameplay steps (map events, each once, also on a skip; the done event runs the rest): the keys (98; 9515), the
peephole Door0 opened and closed, the experience, the move to the Dark Passageway (ExitTrigger2's row); Hanndl removed
and the Great Gate (RotatingDoor0/1) unlocked and opened. Presentation cues: fades, sounds and voices, Hanndl's clips.
"""

from __future__ import annotations

import json
import re
import sys
import wave
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import cutscenes  # noqa: E402
from cutscenes import MM9_CAMERA_FOV, Frame, Objects, Scene, abc_animation, move_to_pos  # noqa: E402

ROOT = PROJECT.parents[2]
STEM = "arslegardcity"
SCRIPTS = ROOT / "mm9/extracted/SCRIPTS/SCRIPTS"
VOICES = ROOT / "mm9/extracted/VOICES/VOICES"
FATE_ID, WRIT_ID = "gate_fate", "gate_writ"
FATE_EVENTS, WRIT_EVENTS = 36000, 36050        # done event = base, steps base + 1..
PARTY_VOICE_SET = 11                           # getPCVoice 11: voices\cinema\AssertiveMale (FateMan.scr :Init)
KEY_FATE, KEY_WRIT_DONE = 98, 9515
HANNDL_MODEL = "Hanndl"                        # models\Hanndl.abc: Hanndl.scr's animations
DRAWER_OPEN = "sounds\\events\\draweropenwood.wav"
DRAWER_CLOSE = "sounds\\events\\drawerclosewood.wav"
QUEST = "sounds\\events\\quest.wav"
# Hanndl.scr: the speech of each trigger (animation, its voice), as OnSpeakN / OnVoiceN.
HANNDL_LINES = {9: ("Sc4_hanndl09", "voices\\cinema\\writoffate\\Hanndl09.wav"),
                10: ("Sc4_hanndl10", "voices\\cinema\\writoffate\\Hanndl10.wav"),
                11: ("Sc4_hanndl11", "voices\\cinema\\writoffate\\Hanndl11.wav"),
                12: ("Sc4_hanndl12", "voices\\cinema\\writoffate\\Hanndl12.wav"),
                13: ("Sc4_hanndl13", "voices\\cinema\\writoffate\\Hanndl13.wav"),
                14: ("Sc4_hanndl14", "voices\\cinema\\writoffate\\Hanndl14.wav"),
                15: ("Sc4_hanndl15", "voices\\cinema\\writoffate\\Hanndl15.wav"),
                16: ("sc5_Hanndl16", "voices\\cinema\\presenthanndlwithwrit\\Hanndl16.wav"),
                17: ("sc5_Hanndl17", "voices\\cinema\\presenthanndlwithwrit\\Hanndl17b.wav")}


# --- sources --------------------------------------------------------------------------------------------------------
def voice_path(relative: str) -> Path:
    """An MM9 voice as the scripts name it (voices\\cinema\\writoffate\\Hanndl09.wav) in VOICES, case-insensitively."""
    parts = [p for p in re.split(r"[\\/]+", relative) if p]
    if parts and parts[0].lower() == "voices":
        parts = parts[1:]
    path = VOICES
    for part in parts:
        matches = [c for c in path.iterdir() if c.name.lower() == part.lower()] if path.is_dir() else []
        if not matches:
            raise FileNotFoundError(relative)
        path = matches[0]
    return path


def voice_seconds(relative: str) -> float:
    with wave.open(str(voice_path(relative))) as stream:
        return stream.getnframes() / float(stream.getframerate())


def party_voices(script: str, voice_set: int = PARTY_VOICE_SET) -> dict[int, str]:
    """The :Init block's `set sVoiceN <wav>` lines under `if (g_ntemp==voice_set)` of a director script."""
    current, voices = None, {}
    for line in (SCRIPTS / script).read_text(encoding="latin-1").splitlines():
        m = re.match(r"\s*if\s*\(g_ntemp==(\d+)\)", line)
        if m:
            current = int(m.group(1))
            continue
        m = re.match(r"\s*set\s+sVoice(\d)\s+(\S+)", line, re.I)
        if m and current == voice_set:
            voices[int(m.group(1))] = m.group(2)
    if not voices:
        raise SystemExit(f"{script}: no voice set {voice_set}")
    return voices


def clip_name(animation: str) -> str:
    """The GLB clip of an MM9 animation: mm9_hanndl.glb names Sc4_hanndl09 Sc4Hanndl09 (actors.yml script_clips)."""
    head, _, tail = animation.partition("_")
    return head[:1].upper() + head[1:].lower() + tail[:1].upper() + tail[1:]


class Speech:
    """Hanndl's lines: an animation (clip and its length) with the voice at its SpeakN key."""

    def __init__(self, number: int):
        animation, self.voice = HANNDL_LINES[number]
        self.clip = clip_name(animation)
        self.length, keys = abc_animation(HANNDL_MODEL, animation)
        speak = [at for at, event in keys if event.lower() == f"speak{number}"]
        self.voice_at = speak[0] if speak else 0.0
        self.voice_length = voice_seconds(self.voice)


def sound_name(relative: str) -> str:
    """A cue's sound name: lowercase, as the world's audio files are imported (voices\\cinema\\<set>\\<file>)."""
    return relative.lstrip("\\").lower()


# --- shots ----------------------------------------------------------------------------------------------------------
class Cameras:
    def __init__(self):
        self.objects = Objects.load(STEM)
        self.frame = Frame(PROJECT)

    def pose(self, name: str):
        return self.frame.camera(self.objects, name)

    def point(self, name: str):
        return self.frame.point(self.objects.named(name)["values"]["Pos"])

    def move(self, camera: str, marker: str, lt_speed: float, hold: float = 0.0):
        """MoveToPos marker at lt_speed after `hold` seconds still: (keys, seconds until the arrival)."""
        eye, forward = self.pose(camera)
        target = self.point(marker)
        _, arrival = move_to_pos(eye, target, self.frame.speed(lt_speed), 0.0)
        aim = {"direction": forward, "fov": MM9_CAMERA_FOV}
        keys = [(0.0, eye, aim)]
        if hold > 0:
            keys.append((hold, eye, aim))
        keys.append((hold + arrival, target, aim))
        return keys, hold + arrival


def moving_shot(cinema, keys, seconds: float, note: str) -> None:
    """The keys up to `seconds` (a cut before the arrival ends the shot there, the last key held after it)."""
    kept = [k for k in keys if k[0] <= seconds + 1e-6]
    last = keys[-1]
    if last[0] > seconds + 1e-6:
        previous = kept[-1]
        share = (seconds - previous[0]) / (last[0] - previous[0])
        point = tuple(a + (b - a) * share for a, b in zip(previous[1], last[1]))
        kept.append((seconds, point, last[2]))
    # The format's times are kept to 3 decimals: no key may round past the shot's end, and a key at the end itself
    # sits 1 ms before it (the parser checks a key's double against the duration as a float: 8.042 > 8.042f).
    duration = round(seconds, 3)
    kept = [(min(round(at, 3), round(duration - 0.001, 3)) if at > 0 else 0.0, point, aim) for at, point, aim in kept]
    cinema.moving(duration, kept, easing="linear", note=note)


# --- the scenes -----------------------------------------------------------------------------------------------------
def scenes(movers: list[dict], hanndl_actor: int, dark_passageway: tuple, experience: dict) -> list[Scene]:
    """Both scenes. movers: the build's movers (work/doors.json); hanndl_actor: the gate's Hanndl (DAT Hanndl, the
    cinema actor behind the peephole); dark_passageway: ExitTrigger2's arrival (x, y, z, yaw, map) as
    citylua.dark_passageway_arrival; experience: {"fate": Lua, "writ": Lua} the awards' MM9.giveExperience calls."""
    gate = [m["node"][5:] for m in movers if m["group"] == "RotatingDoor0"]
    if not gate or not any(m["node"][5:] == "Door0" for m in movers):
        raise SystemExit("arslegardcity cinematics: no Great Gate (RotatingDoor0) or peephole (Door0) movers")
    cameras = Cameras()
    return [fate_scene(cameras, hanndl_actor, dark_passageway, experience["fate"]),
            writ_scene(cameras, gate, hanndl_actor, experience["writ"])]


def speak(scene: Scene, at: float, number: int, actor: int, note: str) -> Speech:
    line = Speech(number)
    scene.cinema._cue(at, f"{note}: Hanndl Speak{number} ({line.clip})", actor=actor, action="clip", clip=line.clip,
                      loop=False)
    scene.cinema.sound(at + line.voice_at, sound_name(line.voice), note=f"Hanndl.scr OnVoice{number}")
    return line


def fate_scene(cameras: Cameras, actor: int, dark_passageway: tuple, experience_lua: str) -> Scene:
    scene = Scene(FATE_ID, FATE_EVENTS, source="FateMan.scr :OnLose..:ExitIN (Fateman), LoseCam1/2.scr, Hanndl.scr")
    cinema = scene.cinema
    voices = party_voices("FATEMAN.scr")
    dx, dy, dz, dyaw, dmap = dark_passageway

    # Cameras: Losecam4 (LoseCam1.scr), Losecam2 (LoseCam2.scr), Losecam3.
    keys4, cam2 = cameras.move("Losecam4", "CameraMarker0", 100.0, hold=0.2)
    keys2, arrival2 = cameras.move("Losecam2", "CameraMarker2", 150.0)
    cam3 = cam2 + arrival2
    scene.step(0.0, "key", f"MM9.giveKey({KEY_FATE})", note="OnLose: givekey 98")
    cinema.fade(0.0, "in", 1.0, note="OnLose ScreenFadeOut 1; LoseCam1 OnPlay ScreenFadeIn 1")
    cinema.fade(cam2, "in", 1.0, note="OnCam2 ScreenFadeOut .5; LoseCam2 OnPlay ScreenFadeIn 1")
    cinema.fade(cam3, "in", 0.5, note="OnCam3 ScreenFadeOut .5, ScreenFadeIn .5")

    # Speech: Scene4 (1 s after Cam3) opens the peephole, Speak9 1.5 s later; each Done goes to the next OnPCn.
    t = cam3 + 1.0
    scene.step(t, "peephole_open", 'open("Door0")', note="Scene4: Door0 use")
    cinema.sound(t, sound_name(DRAWER_OPEN), note="Scene4")
    t += 1.5
    t += speak(scene, t, 9, actor, "Speak9").length                     # PlayAnim .. Done
    for pc, hanndl in ((1, 10), (2, 11), (3, 12), (4, 13)):
        cinema.sound(t, sound_name(voices[pc]), note=f"OnDone {pc}: OnPC{pc}, the party's line {pc:02d}")
        t += voice_seconds(voices[pc])                                  # Playsound sVoiceN, TriggerN
        t += speak(scene, t, hanndl, actor, f"Trigger{hanndl}").length  # Done (13: OnSpeak14)
    line14 = speak(scene, t, 14, actor, "OnSpeak14")
    t += line14.voice_at + line14.voice_length                          # OnVoice14 Playsound .. Done
    cinema.sound(t, sound_name(voices[6]), note="OnDone 5: OnPC6 (MM9's bug: counter 5 skips OnPC5, line 05)")
    t += voice_seconds(voices[6])
    t += speak(scene, t, 15, actor, "Trigger15").length                 # PlayAnim .. close: FadeOut
    close_at = t
    scene.step(close_at, "peephole_close", 'close("Door0")', note="Close: Door0 use")
    cinema.sound(close_at, sound_name(DRAWER_OPEN), note="Close (MM9 plays the open sound again)")
    fade_at = close_at + 1.0
    cinema.fade(fade_at, "out", 1.0, note="FadeOut: ScreenFadeOut 1, LetterBox False")
    end = fade_at + 1.0
    scene.step(end, "experience", experience_lua, note="ExitIN: GiveExp 46000")
    cinema.sound(end, sound_name(QUEST), note="ExitIN")
    # ExitTrigger2's row; MM9's `trigger` moves at once (no transition prompt: MoveToMap's picture argument 0).
    move = f'evt.MoveToMap({dx}, {dy}, {dz}, {dyaw}, 0, 0, 0, 0, "{dmap}")   -- ExitTrigger2\'s row'
    scene.step(end, "exit", f'set("FateMoved", var("FateMoved") + 1)\n{move}',
               note="ExitIN: ExitTrigger2 trigger (the Dark Passageway)")

    moving_shot(cinema, keys4, cam2, "Losecam4 (LoseCam1.scr: to CameraMarker0 at 100)")
    moving_shot(cinema, keys2, arrival2, "Losecam2 (LoseCam2.scr: to CameraMarker2 at 150)")
    eye3, forward3 = cameras.pose("Losecam3")
    cinema.fixed(end - cam3, eye3, direction=forward3, fov=MM9_CAMERA_FOV, note="Losecam3 (OnCam3), the peephole")
    return scene


def writ_scene(cameras: Cameras, gate: list[str], hanndl_actor: int, experience_lua: str) -> Scene:
    scene = Scene(WRIT_ID, WRIT_EVENTS, source="WritMan.scr :OnLose..:FadeIn (Writman), LoseCam1/2/3.scr, Hanndl.scr")
    cinema = scene.cinema
    voices = party_voices("WRITMAN.scr")

    keys1, cam2 = cameras.move("Losecam1", "CameraMarker0", 100.0, hold=0.2)
    keys2, arrival2 = cameras.move("Losecam2", "CameraMarker2", 150.0)
    cam3 = cam2 + arrival2
    cinema.letterbox_cue(0.0, True, 0.0, note="LoseCam1 OnPlay: LetterBox True")
    scene.step(0.0, "key", f"MM9.giveKey({KEY_WRIT_DONE})", note="OnLose: givekey 9515")
    cinema.fade(0.0, "in", 1.0, note="OnLose ScreenFadeOut 1; LoseCam1 OnPlay ScreenFadeIn 1")
    cinema.fade(cam2, "in", 1.0, note="OnCam2 ScreenFadeOut .5; LoseCam2 OnPlay ScreenFadeIn 1")
    cinema.fade(cam3, "in", 0.5, note="OnCam3 ScreenFadeOut .5, ScreenFadeIn .5")

    t = cam3 + 1.0
    scene.step(t, "peephole_open", 'open("Door0")', note="Scene3: Door0 use")
    cinema.sound(t, sound_name(DRAWER_OPEN), note="Scene3")
    t += 1.5
    line16 = speak(scene, t, 16, hanndl_actor, "Speak1")
    t += line16.voice_at + line16.voice_length                          # OnVoice16 Playsound .. Done
    cinema.sound(t, sound_name(voices[1]), note="OnDone: the party's line 01")
    t += voice_seconds(voices[1])                                       # Playsound sVoice1, Trigger10
    line17 = speak(scene, t, 17, hanndl_actor, "Trigger10")
    t += line17.voice_at + line17.voice_length                          # OnVoice17 Playsound .. Close: FadeOut
    close_at = t
    scene.step(close_at, "peephole_close", 'close("Door0")', note="Close: Door0 use")
    cinema.sound(close_at, sound_name(DRAWER_CLOSE), note="Close")
    cam5 = close_at + 1.0
    scene.step(cam5, "experience", experience_lua, note="FadeOut: giveexp 170000")
    cinema.sound(cam5, sound_name(QUEST), note="FadeOut")
    cinema.fade(cam5, "in", 1.0, note="FadeOut: Losecam5 on, ScreenFadein 1")
    gate_at = cam5 + 1.0
    opened = " ".join(f'open("{leaf}")' for leaf in gate)
    scene.step(gate_at, "gate", f"MM9.removeActor({hanndl_actor})   -- DeleteHanndl\n{opened}",
               note="FadeOut2: Hanndl removed, RotatingDoor0/1 unlocked, RotatingDoor0 use (the pair)")
    fade_at = gate_at + 4.0
    cinema.fade(fade_at, "out", 1.0, note="FadeOutReal: ScreenFadeOut 1")
    back = fade_at + 2.0
    cinema.letterbox_cue(back, False, 0.0, note="FadeIn: LetterBox False, Losecam5 off")
    cinema.fade(back, "in", 1.0, note="FadeIn: screenfadein 1 (the party's view)")

    moving_shot(cinema, keys1, cam2, "Losecam1 (LoseCam1.scr: to CameraMarker0 at 100)")
    moving_shot(cinema, keys2, arrival2, "Losecam2 (LoseCam2.scr: to CameraMarker2 at 150)")
    eye3, forward3 = cameras.pose("Losecam3")
    cinema.fixed(cam5 - cam3, eye3, direction=forward3, fov=MM9_CAMERA_FOV, note="Losecam3 (OnCam3), the peephole")
    # Losecam5 (LoseCam3.scr "Losecam6 CameraMarker3"): on at FadeOut, Play at FadeOut2, OnPan 2 s later: MoveToPos
    # Losecam6 at 100; off at FadeIn.
    keys5, _ = cameras.move("Losecam5", "Losecam6", 100.0, hold=(gate_at - cam5) + 2.0)
    moving_shot(cinema, keys5, back - cam5, "Losecam5 (LoseCam3.scr: to Losecam6 at 100 from FadeOut2 + 2 s)")
    cinema.party(1.0, note="FadeIn: the party's view fades in")
    return scene


# --- the test inputs without a build --------------------------------------------------------------------------------
def installed_inputs():
    """scenes() arguments from the project's work/doors.json, the installed scene (the gate's Hanndl, DAT Hanndl) and
    the review root's ExitTrigger2 row (the test without a conversion)."""
    import yaml
    import citylua
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    scene = yaml.load((ROOT / "assets_dev/worlds/mm9/maps/arslegardcity.scene.yml").read_text(),
                      Loader=yaml.CSafeLoader)
    index = Objects.load(STEM).named("Hanndl")["index"]
    hanndl = next(a["actor_index"] for a in scene["initial_state"]["actors"]
                  if a.get("mm9_source_object_index") == index)
    return movers, hanndl, citylua.dark_passageway_arrival(), experience()


def experience() -> dict:
    """The awards' Lua (quest_xp: capped by the balance profile where it lists them), as citylua wrote them before."""
    from quest_xp import experience_lua
    return {"fate": experience_lua(46000, KEY_FATE, "fateman.scr", "ExitIN"),
            "writ": experience_lua(170000, KEY_WRIT_DONE, "writman.scr", "FadeOut")}


if __name__ == "__main__":
    built = scenes(*installed_inputs())
    print(cutscenes.yaml_text(STEM, built))
