#!/usr/bin/env python3
"""
Yanmir's fall as the cinematic `yanmir_death` (devdocs/mm9_rework/MM9_CUTSCENES.md; ../mm9r_common/cutscenes.py).
convert.py builds its map Lua and installs worlds/mm9/maps/yanmirsfort.cinematics.yml from here;
cinematics_pilot.py tests the same scene without a conversion.

MM9 (YanmirBase.scr :OnTimeToDie, Yanmir_Camera.scr, YF_FallingFloor.scr): Yanmir walking into TriggerYanmirTrap once
the six supports are broken runs :OnTimeToDie. :DoCamera turns YanmirCamera on (LetterBox; its Target does not aim,
so the camera looks along its DAT rotation, down the trap hall) unless the party stands on an AIRail tagged UserData
555 (the hall and its basement, AITrk95-98 and 233-234: it sees the fall itself). CaveInDust1-3 on; :GiveEeps at
once (key 69 with key 68, else key 173; 8 000 experience); he runs to YanmirPathA4 and :FallDown at the latest 2 s
later (Wait 21 2): startDie (1.8 s, its DestroyFloor key at 1.536 s: YanDstruct0 destroyed, FallingFloor0
"Disappear", which sinks to CaveInMarker0 at 1000 LT/s and breaks Planks0 and Xbeams0 on touching them, ~0.25 s
later), then Fall looped as he drops to the end of the world, which removes him (the link breaks); the camera turns
off 3 s after that.

Timeline (s): 0 camera, experience; 0-2 run to YanmirPathA4; 2 StartDie; 3.536 the floor; 3.8 Fall, the planks;
3.8-6.3 the drop (FALL_SECONDS, the old converter's removal delay); 6.3 Yanmir removed; 9.3 the end.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import cutscenes  # noqa: E402

STEM = "yanmirsfort"
CINEMA_ID = "yanmir_death"
EVENT_BASE = 36000                 # done 36000, steps 36001-36004
WATCH_USERDATA = 1141555200        # AIRail UserData 555.0 (a float's bits in the DAT)
RUN_SECONDS = 2.0                  # :OnTimeToDie Wait 21, 2, FallDown (or the arrival at YanmirPathA4, if sooner)
FALL_SECONDS = 2.5                 # the drop from the hall's floor until the end of the world removes him
CAMERA_OFF_SECONDS = 3.0           # Yanmir_Camera.scr :OnLinkBroken Wait 0, 3, TurnOff
FALL_DEPTH = -1800                 # native z the drop ends at (CaveInMarker0's level, under the basement's beams)
STEPS = ("experience", "floor", "planks", "gone")   # MM9Cinematic.runStep indices 1-4


def watch_boxes(project, source) -> list:
    """The AIRails tagged 555 as native boxes [[low], [high]] (their brushes' extents)."""
    boxes = []
    for o in source.objects:
        if o["class"] == "AIRail" and o["properties"].get("UserData") == WATCH_USERDATA:
            native = project.native(np.array(source.models[o["name"]].points, float))
            boxes.append([native.min(0).round().astype(int).tolist(), native.max(0).round().astype(int).tolist()])
    return boxes


def _native(frame, name):
    return frame.point(cutscenes.Objects.load(STEM).named(name)["values"]["Pos"])


def scenes(yanmir: int) -> list:
    """The map's cutscenes: yanmir_death on actor `yanmir` (the map actor index of Yanmir0)."""
    objects = cutscenes.Objects.load(STEM)
    frame = cutscenes.Frame(PROJECT)
    die_seconds, die_keys = cutscenes.abc_animation("Yanmir", "startDie")
    floor_at = RUN_SECONDS + dict((event, t) for t, event in die_keys)["DestroyFloor"]
    fall_at = RUN_SECONDS + die_seconds
    gone_at = fall_at + FALL_SECONDS
    end = gone_at + CAMERA_OFF_SECONDS
    marker = _native(frame, "YanmirPathA4")
    stop = (marker[0], marker[1], 0.0)                         # A4 hangs 338 over the hall's floor (z 0)
    drop = (marker[0], marker[1], float(FALL_DEPTH))

    scene = cutscenes.Scene(CINEMA_ID, EVENT_BASE, source="YanmirBase.scr :OnTimeToDie, Yanmir_Camera.scr")
    cinema = scene.cinema
    eye, forward = frame.camera(objects, "YanmirCamera")
    cinema.fixed(end, eye, direction=forward, fov=cutscenes.MM9_CAMERA_FOV,
                 note="YanmirCamera (DAT rotation: Target does not aim), off 3 s after Yanmir's link breaks")
    scene.step(0.0, "experience", "giveEeps(EXP_TRAP)\nupdateHints()", note=":OnTimeToDie :GiveEeps (8000)")
    cinema._cue(0.0, ":OnTimeToDie RunTo YanmirPathA4", actor=yanmir, action="face", look_at=list(stop), seconds=0.3)
    cinema._cue(0.0, "", actor=yanmir, action="clip", clip="Running", loop=True)
    cinema.actor(0.0, yanmir, "move", to=stop, seconds=RUN_SECONDS)
    cinema._cue(RUN_SECONDS, ":FallDown PlayAnim startDie", actor=yanmir, action="clip", clip="StartDie", loop=False)
    scene.step(floor_at, "floor", 'openGroup("TrapFloor")', note="startDie DestroyFloor key: YanDstruct0, FallingFloor0")
    cinema.sound(floor_at, "sounds\\events\\stonecrumble.wav")
    scene.step(fall_at, "planks", 'openGroup("TrapPlanks")', note="FallingFloor0 touches Planks0: Planks0, Xbeams0")
    cinema._cue(fall_at, ":DoFall LoopAnim Fall", actor=yanmir, action="clip", clip="Fall", loop=True)
    cinema.actor(fall_at, yanmir, "move", to=drop, seconds=FALL_SECONDS, note="the drop to the end of the world")
    scene.step(gone_at, "gone", 'set("YanmirGone", 1)\nMM9.removeActor(YANMIR)',
               note="Yanmir_EndOfWorld.scr :HandleYanmir RemoveObject (the camera's link breaks)")
    return [scene]


def trap_lua(watch: list, shaft, t_fall: int, exp_trap: int) -> list[str]:
    """trapFires and the T_FALL handler of the map Lua (convert.py writes them; cinematics_pilot.py swaps them in)."""
    i = {name: k + 1 for k, name in enumerate(STEPS)}
    cid = f'"{CINEMA_ID}"'
    return [
        "-- TriggerYanmirTrap (AIOnly, turned on by YanmirTrap.scr at six supports) -> Yanmir :OnTimeToDie: the",
        f"-- cinematic {CINEMA_ID} (cutscene.py): YanmirCamera on the trap hall, the key and the experience, his run",
        "-- to YanmirPathA4, startDie (its DestroyFloor key: YanDstruct0 destroyed, FallingFloor0 drops onto Planks0,",
        "-- which breaks with Xbeams0), Fall, removed at the end of the world (Yanmir_EndOfWorld.scr). :DoCamera keeps",
        "-- the camera off for a party on an AIRail tagged 555 (it sees the hall): the same steps on the T_FALL timer.",
        f"local EXP_TRAP = {exp_trap}",
        "local WATCH = {" + ", ".join(f"{{{{{b[0][0]}, {b[0][1]}, {b[0][2]}}}, {{{b[1][0]}, {b[1][1]}, {b[1][2]}}}}}"
                                      for b in watch) + "}",
        "local function partyWatches()",
        "    local x, y, z = evt.GetPartyPosition()",
        "    for _, b in ipairs(WATCH) do",
        "        if inBox(b, x, y, z) then return true end",
        "    end",
        "    return false",
        "end",
        "local function trapFires()",
        "    if var(\"TrapFired\") == 1 then return end",
        "    set(\"TrapFired\", 1)",
        "    if not partyWatches() then",
        f"        MM9Cinematic.start({cid})",
        "        return",
        "    end",
        "    set(\"FallStage\", 1)",
        f"    MM9Cinematic.runStep({cid}, {i['experience']})",
        f"    evt.StartTimer({t_fall}, seconds({RUN_SECONDS:g}))",
        "end",
        f"handlers[{t_fall}] = function()   -- the watched fall: FallDown, the floor, the drop, removed",
        f"    evt.StopTimer({t_fall})",
        "    local stage = var(\"FallStage\")",
        "    if stage == 1 then",
        "        set(\"FallStage\", 2)",
        "        evt.PlayActorClip(YANMIR, \"StartDie\", false)",
        f"        evt.StartTimer({t_fall}, seconds(1.5))",
        "    elseif stage == 2 then",
        "        set(\"FallStage\", 3)",
        f"        MM9Cinematic.runStep({cid}, {i['floor']}); MM9Cinematic.runStep({cid}, {i['planks']})",
        "        evt.PlaySoundName(\"events/stonecrumble.wav\", 0, 0, 0)",
        "        evt.PlayActorClip(YANMIR, \"Fall\", true)",
        f"        evt.SetMapActorPosition(YANMIR, {shaft[0]}, {shaft[1]}, {shaft[2]})",
        f"        evt.StartTimer({t_fall}, seconds({FALL_SECONDS:g}))",
        "    elseif stage == 3 then",
        "        set(\"FallStage\", 4)",
        f"        MM9Cinematic.finish({cid})",
        "    end",
        "end",
    ]


def load_lua() -> str:
    """The map-load line: a fall that a map change or a save cut short (the watched timers) finishes its steps."""
    return (f"    if var(\"TrapFired\") == 1 and var(\"YanmirGone\") == 0 then MM9Cinematic.finish(\"{CINEMA_ID}\") end"
            "   -- yanmir_death's steps")
