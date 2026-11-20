#!/usr/bin/env python3
"""
Hall of the Gods' MM9 cutscene as an in-engine cinematic (devdocs/mm9_rework/MM9_CUTSCENES.md, mm9r_common/cutscenes.py):
gods_epilogue, WinMan.scr ScriptParams Part2 (:Init on load with key 109 and without the Writ of Fate, 394) with
WG_Scene7Cam1.scr and the actors' WG_NPC334.scr (Hanndl), WG_NPC335.scr (Krohn), WG_NPC336.scr (Skraelos0). Built here
for convert.py (map_script: the Lua block and the installed hallofthegods.cinematics.yml) and cinematics_pilot.py.

Timeline (seconds from :OnKrohn, MM9's letterbox): :StartPart2 at 1 (the gods shown, WG_Scene7Cam1 on, Hanndl walks to
HanndlMarker at MONSTERS.txt row 260's 50 LT/s); Scene7Cam1's Wait 1 and MoveToPos Scene7MK1 at 150 end in :OnKrohnCut
(Cam2, Wait 3.5, Cam3); Hanndl's arrival + Krohn's Wait 1 start the talk, whose cuts follow the actors' waits and
animation ends (Hanndl05's callback) and whose voices start on the .abc Voice keys (all at 0); :End (fade, item 394)
and, 3 s later, :Release. Events 36000 (done) and 36001.. (steps).
"""

from __future__ import annotations

import math
import sys
import wave
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import cutscenes  # noqa: E402
from cutscenes import MM9_CAMERA_FOV as FOV, Frame, Objects, Scene, move_to_pos  # noqa: E402

STEM = "hallofthegods"
EPILOGUE_ID, EPILOGUE_BASE = "gods_epilogue", 36000
WALK = 50.0                                  # MONSTERS.txt row 260 (Hanndl) WalkVelocity, LT/s
# MM9's WalkTo stops short of its marker: WG_Scene7Cam5, Cam8 and Cam9 (all west-facing, Cam8 and Cam9 only 53 and 20 LT
# west of HanndlMarker) frame Hanndl where Cam9's axis crosses his walk, 75 LT before the marker (Njam's RunTo on the
# Thousand Terrors stops 60 LT short, where its lightning strikes).
WALK_STOP_SHORT_LT = 75.0
VOICES = cutscenes.ROOT / "mm9/extracted/VOICES/VOICES/CINEMA/WINGAME"


def voice(name: str) -> str:
    return f"voices\\cinema\\wingame\\{name.lower()}.wav"


def voice_seconds(name: str) -> float:
    with wave.open(str(VOICES / f"{name.upper()}.wav")) as stream:
        return stream.getnframes() / float(stream.getframerate())


def gods_epilogue(actor: dict, hanndl_mark, hanndl_start) -> Scene:
    """actor: DAT name -> map actor index (convert.py's self.actor); hanndl_mark: HanndlMarker on the floor (native);
    hanndl_start: Hanndl's placed feet (native)."""
    frame, objects = Frame(PROJECT), Objects.load(STEM)
    hanndl, krohn = actor["Hanndl"], actor["Krohn"]
    scene = Scene(EPILOGUE_ID, EPILOGUE_BASE, source="WinMan.scr Part2 :OnKrohn..:Release, WG_Scene7Cam1.scr, "
                                                       "WG_NPC334/335/336.scr")
    cinema = scene.cinema
    cam = lambda n: frame.camera(objects, f"WG_Scene7Cam{n}")   # noqa: E731

    def length(model: str, animation: str) -> float:
        return cutscenes.abc_animation(model, animation)[0]

    t_part2 = 1.0                                               # :OnKrohn Letterbox, Wait 1 1 StartPart2
    eye1, fwd1 = cam(1)
    mk1 = frame.point(objects.named("Scene7MK1")["values"]["Pos"])
    _, pan = move_to_pos(eye1, mk1, frame.speed(150), 0)
    t_cut = t_part2 + 1.0 + pan                                 # Cam1 Wait 1 OnPan, MoveToPos at 150 -> CutToKrohn
    t_cam3 = t_cut + 3.5                                        # Wait 1 3.5 KrohnCut
    hanndl_lt = objects.named("Hanndl")["values"]["Pos"]
    mark_lt = objects.named("HanndlMarker")["values"]["Pos"]
    walk_lt = math.hypot(mark_lt[0] - hanndl_lt[0], mark_lt[2] - hanndl_lt[2])
    walk = (walk_lt - WALK_STOP_SHORT_LT) / WALK
    t_arrive = t_part2 + walk                                   # :OnAction WalkTo HanndlMarker -> Krohn Arrive
    t = t_arrive + 1.0                                          # Krohn :OnArrive Wait 1 StartTalk -> WinMan Hanndl1
    if not t_cam3 < t:
        raise ValueError("gods_epilogue: the talk starts before Scene7Cam3")
    # The talk: (start, camera, speaker, clip, voice), each start from the previous one's wait (scripts' line numbers).
    talk = []
    talk.append((t, 4, hanndl, "Hanndl01", "Hanndl01"))         # :OnHanndl1; WG_NPC334 Wait 1 5 Krohn1
    t += 5.0
    talk.append((t, 3, krohn, "Krohn01", "Krohn01"))            # :OnKrohn1; WG_NPC335 Wait 1 4 Hanndl2
    t += 4.0
    t_h2 = t
    talk.append((t + 1.0, None, hanndl, "Hanndl02", "Hanndl02"))   # :OnHanndl2 (Cam5), Wait 1 Speak02, Wait 2.5
    t += 1.0 + 2.5
    t_k2 = t
    talk.append((t + 1.0, None, krohn, "Krohn02", "Krohn02"))   # :OnKrohn2 (Cam6), Wait 1 Speak02, Wait 2
    t += 1.0 + 2.0
    talk.append((t, 5, hanndl, "Hanndl03", "Hanndl03"))         # :OnHanndl3 (Cam5), Wait 6
    t += 6.0
    t_k3 = t
    talk.append((t + 1.0, None, krohn, "Krohn03", "Krohn03"))   # :OnKrohn3 (Cam7), Wait 1 Speak03, Wait 3
    t += 1.0 + 3.0
    t_h4 = t
    talk.append((t, 5, hanndl, "Hanndl04", "Hanndl04"))         # :OnHanndl4 (Cam5; Wait 6 Cam9), Wait 19
    t += 19.0
    t_k4 = t
    talk.append((t + 3.0, None, krohn, "Krohn04", "Krohn04"))   # :OnKrohn4 (Cam6), Wait 3 Speak04, Wait 3
    t += 3.0 + 3.0
    t_close = t                                                 # Speak04b: HanndlClose (Cam8), Wait 2.5
    t += 2.5
    t_k5 = t                                                    # Speak04c: KrohnClose (Cam7), Krohn05, Wait 21 / 18.5
    talk.append((t, None, krohn, "Krohn05", "Krohn05"))
    t_ever = t + 18.5
    t += 21.0
    t_h5 = t
    talk.append((t, 5, hanndl, "Hanndl05", "Hanndl05"))         # :OnHanndl5 (Cam5): PlayAnim Hanndl05 Krohn5
    t += length("HANNDL", "Hanndl05")
    t_k6 = t                                                    # Krohn5: WinMan Krohn5 (Cam6), SC7_22_Krohn (Voice6)
    t_h6 = t + 4.0                                              # Wait 1 4 Hanndl6 (Cam10): Hanndl06.wav, Wait 2
    t_k7 = t_h6 + 2.0                                           # Krohn6 (Cam11): Krohn07.wav, Wait 5
    t_end = t_k7 + 5.0                                          # :End: ScreenFadeOut 1, giveitem 394, Wait 3
    t_release = t_end + 3.0                                     # :Release: letterbox off, fade in, DoHighScore

    # The cameras in WinMan.scr's order of Trigger On (one exception: :OnKrohn3 turns Cam4 off, not Cam5, so MM9 has
    # Cam5 and Cam7 on together; Cam7, the shot of the speaking Krohn, is taken).
    cuts = [(t_cut, 2), (t_cam3, 3), (talk[0][0], 4), (talk[1][0], 3), (t_h2, 5), (t_k2, 6), (talk[4][0], 5),
            (t_k3, 7), (t_h4, 5), (t_h4 + 6.0, 9), (t_k4, 6), (t_close, 8), (t_k5, 7), (t_ever, 11), (t_h5, 5),
            (t_k6, 6), (t_h6, 10), (t_k7, 11), (t_release, None)]
    cinema.party(t_part2, note=":OnKrohn: Letterbox True, Wait 1")
    cinema.moving(1.0 + pan, [(0.0, eye1, {"direction": fwd1, "fov": FOV}),
                                    (1.0, eye1, {"direction": fwd1, "fov": FOV}),
                                    (1.0 + pan, mk1, {"direction": fwd1, "fov": FOV})],
                  easing="linear", note="WG_Scene7Cam1 (:StartPart2; Wait 1, MoveToPos Scene7MK1 at 150)")
    for (start, number), (end, _) in zip(cuts, cuts[1:]):
        eye, fwd = cam(number)
        cinema.fixed(end - start, eye, direction=fwd, fov=FOV, note=f"WG_Scene7Cam{number}")
    cinema.party(1.0, note=":Release: the party's view, ScreenFadeIn 1")

    cinema.fade(t_part2, "in", 1.0, note=":StartPart2 screenfadein 1")
    cinema.fade(t_cut, "in", 1.0, note=":OnKrohnCut Screenfadeout .5, screenfadein 1")
    cinema.fade(t_end, "out", 1.0, note=":End Screenfadeout 1")
    cinema.fade(t_release, "in", 1.0, note=":Release screenfadein 1")
    # Hanndl's walk, then both face each other (Krohn :OnArrive targets Hanndl).
    marker = tuple(float(c) for c in hanndl_mark)
    start = tuple(float(c) for c in hanndl_start)
    share = 1.0 - WALK_STOP_SHORT_LT / walk_lt
    mark = (start[0] + (marker[0] - start[0]) * share, start[1] + (marker[1] - start[1]) * share, marker[2])
    cinema._cue(t_part2, "faces HanndlMarker", actor=hanndl, action="face", look_at=[round(c, 1) for c in marker],
                seconds=0)
    cinema._cue(t_part2, "WalkTo HanndlMarker", actor=hanndl, action="clip", clip="Walking", loop=True)
    cinema.actor(t_part2, hanndl, "place", to=hanndl_start, note="WG_NPC334.scr :OnStart where he stands")
    cinema.actor(t_part2, hanndl, "move", to=mark, seconds=walk, note="WG_NPC334.scr :OnAction WalkTo, 50 LT/s, stops 75 LT short")
    cinema._cue(t_arrive, ":OnKrohn: arrived", actor=hanndl, action="clip", clip="Standing", loop=True)
    cinema._cue(t_arrive, "faces Krohn", actor=hanndl, action="face", look_at_actor=krohn, seconds=0.5)
    cinema._cue(t_arrive, "Krohn :OnArrive: target Hanndl", actor=krohn, action="face", look_at_actor=hanndl,
                seconds=0.5)
    for start, _, who, clip, line in talk:
        cinema._cue(start, f"PlayAnim {clip}", actor=who, action="clip", clip=clip, loop=False)
        cinema.sound(start, voice(line), note=f"{clip} Voice key: {line}.wav ({voice_seconds(line):.2f} s)")
    cinema._cue(t_k6, "Krohn5 ReachOut: Playanim Hanndl06", actor=hanndl, action="clip", clip="Hanndl06", loop=False)
    cinema._cue(t_k6, ":OnKrohn5 PlayAnim SC7_22_Krohn", actor=krohn, action="clip", clip="SC7_22_Krohn", loop=False)
    cinema.sound(t_k6, voice("Krohn06"), note="SC7_22_Krohn Voice6: Krohn06.wav")
    cinema.sound(t_h6, voice("Hanndl06"), note=":OnHanndl6 Playsound Hanndl06.wav")
    cinema.sound(t_k7, voice("Krohn07"), note=":OnKrohn6 Playsound Krohn07.wav")

    scene.step(t_part2, "gather", "cinemaShown(true)",
               note=":StartPart2: Skraelos0, Krohn, Hanndl (and the Wyrdes) start, Krohn0 stops")
    scene.step(t_end, "writ", 'give(394, "WinMan.scr:End")', note=":End giveitem 394 (the Writ of Fate)")
    scene.step(t_release, "release", 'set("CinemaDone", 1)\ncinemaShown(false)',
               note=":Release: the cinema's gods stop, Krohn0 starts (DoHighScore: the world's completion, key 109)")
    float_safe(cinema)
    return scene



def float_safe(cinema) -> None:
    """A moving shot's last key 1 ms before its end: the engine's parser compares a key's time (double) with the shot's
    duration (float), so a key at exactly 7.37 of a 7.37 s shot is out of range."""
    for shot in cinema.shots:
        for key in shot.get("keys", []):
            if key["at"] >= shot["duration"]:
                key["at"] = round(shot["duration"] - 0.001, 3)

def epilogue_seconds() -> float:
    """The epilogue's length (its timing comes from the scripts, the wavs and the DAT, not from the map's indices)."""
    return gods_epilogue({"Hanndl": 0, "Krohn": 1}, (0, 0, 0), (1, 0, 0)).cinema.shots_seconds


def scenes(actor: dict, hanndl_mark, hanndl_start) -> list[Scene]:
    return [gods_epilogue(actor, hanndl_mark, hanndl_start)]


LOAD_LUA = [
    "-- Map load (WinMan.scr :Init, WG_NPC334/335/336.scr :Loop): with key 109 (Njam beaten), without the Writ of Fate",
    "-- (394) and before the epilogue ended here, the cinematic gods_epilogue (cinematics_hall.py) plays.",
    "handlers[1] = function()",
    "    cinemaShown(false)",
    "    if MM9.hasKey(109) == 1 and MM9.hasItem(394) == 0 and var(\"CinemaDone\") == 0 then",
    f"        MM9Cinematic.start(\"{EPILOGUE_ID}\")",
    "    end",
    "end",
]


def install(scene_list: list[Scene]) -> None:
    cutscenes.install(STEM, scene_list)
