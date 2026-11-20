#!/usr/bin/env python3
"""
Thousand Terrors' MM9 cutscenes as in-engine cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md, mm9r_common/cutscenes.py):
the one place that builds them, used by convert.py (map_script: the Lua block and the installed
1000terrors.cinematics.yml) and by cinematics_pilot.py (the scratch-root test without a conversion).

- njam_freeze_win (WinMan.scr :OnUse with key 108): NjamCam (WG_NjamCam.scr: to NjamCamMk1 at 100, FaceDir and
  MoveToPos NjamCamMk2 at 130), WG_Shot2Cam (the lever), Shot3Cam (NjamFreeze.scr :OnPanic), Shot4Cam and Shot5Cam on
  njam_wingame's CameraSwitch / CameraSwitch2 keys, Shot5Cam's back-up to Shot5Mk (WG_Shot5Cam.scr), Shot6Cam 0.6 s,
  Shot5Cam 3 s, Shot5CamB until :OnFrozen's fade, Shot7Cam's path over Shot7Mk0-3 at 75 (WG_Shot7Cam.scr), then
  :OnCutTo's fade and ExitTrigger1 (Hall of the Gods). Events 36000 (done) and 36001.. (steps).
- njam_taunt (TauntMan.scr :OnStart, Trigger19 with key 108 and without 497): TauntCam, TauntCamB on Njam's arrival,
  TauntCam for his vanishing (NjamTaunt.scr). Events 36050...
- chess_capture_<k> (ChessCamera.scr :ViewChessPiece, from ChessBase.inc :StartCamera): one per square a piece attacks,
  the camera at the square at ChessCam's height looking at the piece for the 2 s slide. Done events 36100 + i.

Seconds are MM9's: Wait channels, MoveToPos arrivals (distance / speed), RunTo / WalkTo at MONSTERS.txt row 261's run
and walk velocities, and njam_wingame's .abc keys (abc_animation).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import cutscenes  # noqa: E402
from cutscenes import MM9_CAMERA_FOV as FOV, Frame, Objects, Scene, face_toward, move_to_pos  # noqa: E402
from script_text import rollover_text  # noqa: E402

STEM = "1000terrors"
WIN_ID, TAUNT_ID, CHESS_PREFIX = "njam_freeze_win", "njam_taunt", "chess_capture_"
WIN_BASE, TAUNT_BASE, CHESS_BASE = 36000, 36050, 36100

NJAM_RUN, NJAM_WALK = 200.0, 75.0        # MONSTERS.txt row 261 (Njam the Meddler): RunVelocity, WalkVelocity (LT/s)
DESTROY_RADIUS_LT, DESTROY_MAX = 1024, 10   # WinMan.scr :DestroyMonsters (GetObjects AIBase, 1024, 10)
RAMP_TOP_X, RAMP_TOP_Z = 6935, 2740     # the top of the ramp between Njam's place and his hall (compiled BLV floor)
NJAM_TAUNT_GROUP = 1                     # convert.py GROUP_NJAM_TAUNT: NjamtheMeddler0's monster group
SWITCH_MIN_Z_LT = -3680                  # WinMan.scr :OnUse: nothing below LT z -3680 (TELP: through the wall)
LIGHTNING_SECONDS = 7.0                  # NjamFreeze.scr / WinMan.scr: Wait 1 7 OnLightningOff
COG_WINMAN = 1370                        # the switch's SetSprite key (mm9_switch03: the wheel's clips down, up)
CHESS_SLIDE_SECONDS = 2.0                # ChessBase.inc :AttackSquare: half the distance a second
# EarthQuake (ShakeAmount 1, DecayRate 2), the rule of MM9_CUTSCENES.md section 5: intensity min(amount, 12) / 12
QUAKE_INTENSITY, QUAKE_DECAY_SECONDS = 1.0 / 12.0, 1.0 / 2.0

SOUNDS = {
    "switch": "sounds\\door\\cell_door_close.wav",
    "windup": "sounds\\magic\\windup10.wav",
    "portal": "sounds\\spells\\townportal.wav",
    "arms": "sounds\\spells\\armsofearth01.wav",
    "column": "sounds\\spells\\column01.wav",
    "purify": "sounds\\spells\\purify.wav",
    "thunder": "sounds\\ambient\\thunder\\thunder01.wav",
    "teleport": "sounds\\magic\\teleport.wav",
}


def _dist(a, b) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _lt_vector(v) -> tuple:
    """An LT vector (x, y up, z) in the native axes (x, y, z up)."""
    return (float(v[0]), float(v[2]), float(v[1]))


def _lt(objects, name):
    return objects.named(name)["values"]["Pos"]


def lightning_lua(frame: Frame, objects: Objects, seconds: float) -> str:
    """Lightning1/2 (Lightning objects: Pos to EndPos, white-blue) as arc beams for `seconds`."""
    lines = []
    for name in ("Lightning1", "Lightning2"):
        values = objects.named(name)["values"]
        a, b = frame.point(values["Pos"]), frame.point(values["EndPos"])
        coords = ", ".join(str(int(round(c))) for c in (*a, *b))
        lines.append(f'evt.Beam("{name}", "openyamm:fx/arc_beam", {coords}, {seconds:g})')
    return "\n".join(lines)



def float_safe(cinema) -> None:
    """A moving shot's last key 1 ms before its end: the engine's parser compares a key's time (double) with the shot's
    duration (float), so a key at exactly 7.37 of a 7.37 s shot is out of range."""
    for shot in cinema.shots:
        for key in shot.get("keys", []):
            if key["at"] >= shot["duration"]:
                key["at"] = round(shot["duration"] - 0.001, 3)

# --- njam_freeze_win ------------------------------------------------------------------------------------------------
def njam_freeze_win(frame: Frame, objects: Objects, actor: dict, points: dict, arrival: tuple) -> Scene:
    njam = actor["Njam"]
    scene = Scene(WIN_ID, WIN_BASE, source="WinMan.scr :OnUse..:ChangeLevel, WG_NjamCam/Shot2/Shot5/Shot7Cam.scr, "
                                         "NjamFreeze.scr, WG_hand.scr")
    cinema = scene.cinema
    cam = lambda name: frame.camera(objects, name)   # noqa: E731

    # 0 :OnUse: the switch, experience, the quest sound, DestroyMonsters, ScreenFadeOut 1, Windup10; 2 s later :OnStart.
    t_start = 2.0
    # :OnStart: NjamCam Play (StartFilm: letterbox, fade in), Njam Chase (visible, TownPortal, RunTo NJamMarker).
    eye0, fwd0 = cam("NjamCam")
    mk1, mk2 = frame.point(_lt(objects, "NjamCamMk1")), frame.point(_lt(objects, "NjamCamMk2"))
    _, arrive1 = move_to_pos(eye0, mk1, frame.speed(100), 0)
    # :OnArrive1: FaceDir with Mk2's position as the direction (the script passes the point: kept, the picture is
    # MM9's; Mk2's own rotation agrees) at 70 degrees a second, MoveToPos Mk2 at 130.
    turned, turn_seconds = face_toward(fwd0, (0, 0, 0), _lt_vector(_lt(objects, "NjamCamMk2")), 70.0, 1e9)
    _, arrive2 = move_to_pos(mk1, mk2, frame.speed(130), 0)
    keys = [(0.0, eye0, {"direction": fwd0, "fov": FOV}), (arrive1, mk1, {"direction": fwd0, "fov": FOV})]
    if turn_seconds < arrive2:
        mid, _ = move_to_pos(mk1, mk2, frame.speed(130), turn_seconds)
        keys.append((arrive1 + turn_seconds, mid, {"direction": turned, "fov": FOV}))
        end_dir = turned
    else:
        end_dir, _ = face_toward(fwd0, (0, 0, 0), _lt_vector(_lt(objects, "NjamCamMk2")), 70.0, arrive2)
    keys.append((arrive1 + arrive2, mk2, {"direction": end_dir, "fov": FOV}))
    t_cam_done = t_start + arrive1 + arrive2                     # :OnArrive2 -> WinMan :OnNjamCamDone

    # Njam runs from his DAT place to where Lightning1/2 strike (their EndPos: MM9's RunTo stops short of NJamMarker,
    # and Shot3Cam's close-up, 37 LT in front of him, frames him there); LeverHand plays, :OnDone 1 s later.
    njam_start_lt = _lt(objects, "Njam")
    end_lt = objects.named("Lightning1")["values"]["EndPos"]
    stop = frame.point([end_lt[0], 0, end_lt[2]])
    stop = (stop[0], stop[1], points["NJamMarker"][2])            # on NJamMarker's floor (convert.py's point, +2)
    run_seconds = _dist((njam_start_lt[0], njam_start_lt[2]), (end_lt[0], end_lt[2])) / NJAM_RUN
    # His place is at the foot of the ramp up to the hall (the compiled floor rises from his feet, z 2563, to 2737 at
    # x 6935, then steps to the hall's 2775): the run goes up the ramp first, so no point of it is under the floor
    # (a cue's place under the floor is refused).
    feet = scene_feet(STEM, njam)
    ramp_t = (RAMP_TOP_X - feet[0]) / (stop[0] - feet[0])
    ramp_top = (RAMP_TOP_X, feet[1] + (stop[1] - feet[1]) * ramp_t, RAMP_TOP_Z)
    t_arrive = t_start + run_seconds
    t_panic = t_arrive + 1.0                                      # WG_hand.scr Wait 1 1 OnDone -> :OnHandDone
    length, keys_abc = cutscenes.abc_animation("NJAM", "njam_wingame")
    key = {name.lower(): at for at, name in keys_abc}
    t_switch, t_ball = t_panic + key["cameraswitch"], t_panic + key["startball"]
    t_switch2, t_lightning = t_panic + key["cameraswitch2"], t_panic + key["lightning"]
    if not t_cam_done < t_panic:
        raise ValueError("njam_freeze_win: Njam arrives before NjamCam's path ends")
    # Shot5Cam Play: Wait .5 OnBackUp, MoveToPos Shot5Mk at 100 -> :OnPanUp.
    eye5, fwd5 = cam("WG_Shot5Cam")
    mk5 = frame.point(_lt(objects, "Shot5Mk"))
    _, back_seconds = move_to_pos(eye5, mk5, frame.speed(100), 0)
    t_panup = t_switch2 + 0.5 + back_seconds
    t_return, t_camb = t_panup + 0.6, t_panup + 0.6 + 3.0
    t_off = t_lightning + LIGHTNING_SECONDS                       # :OnLightningOff -> WinMan :OnFrozen
    t_finish = t_off + 2.0                                        # ScreenFadeOut 1, Wait 1 2 OnFinish
    if not t_camb < t_off:
        raise ValueError("njam_freeze_win: Shot5CamB comes after the freeze")
    # Shot7Cam Play: Wait .2 (fade in), Wait 2, the path Shot7Mk0-3 at 75 -> WinMan :OnCutTo (fade 2, Wait 2).
    eye7, fwd7 = cam("WG_Shot7Cam")
    path, at, last = [(0.0, eye7)], 2.2, eye7
    for name in ("Shot7Mk0", "Shot7Mk1", "Shot7Mk2", "Shot7Mk3"):
        point = frame.point(_lt(objects, name))
        if at == 2.2:
            path.append((at, last))
        at += _dist(last, point) / frame.speed(75)
        path.append((at, point))
        last = point
    t_cut = t_finish + at
    t_exit = t_cut + 2.0

    cinema.party(t_start, note="OnUse: the party's view while the screen fades out (ScreenFadeOut 1, Wait 2)")
    cinema.moving(t_cam_done - t_start, keys, easing="linear",
                  note="NjamCam (WG_NjamCam.scr: MoveToPos NjamCamMk1 at 100, FaceDir 70, MoveToPos NjamCamMk2 at 130)")
    eye2, fwd2 = cam("WG_Shot2Cam")
    cinema.fixed(t_panic - t_cam_done, eye2, direction=fwd2, fov=FOV, note="WG_Shot2Cam (the switch) until :OnHandDone")
    eye3, fwd3 = cam("WG_Shot3Cam")
    cinema.fixed(t_switch - t_panic, eye3, direction=fwd3, fov=FOV, note="WG_Shot3Cam (:OnHandDone, Njam's Panic)")
    eye4, fwd4 = cam("WG_Shot4Cam")
    cinema.fixed(t_switch2 - t_switch, eye4, direction=fwd4, fov=FOV, note="WG_Shot4Cam (njam_wingame CameraSwitch)")
    cinema.moving(t_panup - t_switch2, [(0.0, eye5, {"direction": fwd5, "fov": FOV}),
                                        (0.5, eye5, {"direction": fwd5, "fov": FOV}),
                                        (0.5 + back_seconds, mk5, {"direction": fwd5, "fov": FOV})],
                  easing="linear", note="WG_Shot5Cam (CameraSwitch2; Wait .5, MoveToPos Shot5Mk at 100)")
    eye6, fwd6 = cam("Wg_Shot6Cam")
    cinema.fixed(0.6, eye6, direction=fwd6, fov=FOV, note="Wg_Shot6Cam (:OnPanUp, Wait .6)")
    cinema.fixed(3.0, mk5, direction=fwd5, fov=FOV, note="WG_Shot5Cam again, where it backed up to (Wait 3)")
    eyeb, fwdb = cam("WG_Shot5Camb")
    cinema.fixed(t_finish - t_camb, eyeb, direction=fwdb, fov=FOV, note="WG_Shot5CamB (:LightingCamera2) to :OnFinish")
    cinema.moving(t_exit - t_finish, [(k, p, {"direction": fwd7, "fov": FOV}) for k, p in path], easing="linear",
                  note="WG_Shot7Cam (Wait .2, fade in, Wait 2, Shot7Mk0-3 at 75), :OnCutTo's fade")

    # Fades (MM9's ScreenFadeOut/In intent).
    cinema.fade(0.0, "out", 1.0, note="OnUse ScreenFadeOut 1")
    cinema.fade(t_start, "in", 1.0, note="StartFilm ScreenFadeIn 1")
    cinema.fade(t_cam_done, "in", 1.0, note="NjamCam OnArrive2 ScreenFadeOut 1 + Shot2Cam ScreenFadein 1")
    cinema.fade(t_off, "out", 1.0, note=":OnFrozen ScreenFadeOut 1")
    cinema.fade(t_finish + 0.2, "in", 1.0, note="WG_Shot7Cam OnFinish2 ScreenFadein 1")
    cinema.fade(t_cut, "out", 2.0, note=":OnCutTo Screenfadeout 2")
    # Sounds.
    cinema.sound(0.0, SOUNDS["switch"], note=":onSwitch (the lever up)")
    cinema.sound(0.0, SOUNDS["windup"], note="OnUse Windup10")
    cinema.sound(t_start, SOUNDS["portal"], note="NjamFreeze.scr :OnChase TownPortal")
    cinema.sound(t_cam_done, SOUNDS["switch"], note="WG_Shot2Cam Play: WinMan switch (the lever down)")
    cinema.sound(t_panic, SOUNDS["arms"], note=":OnHandDone Armsofearth01")
    cinema.sound(t_ball, SOUNDS["column"], note="njam_wingame StartBall: column01")
    for k in range(3):
        cinema.sound(t_lightning + 2.5 * k, SOUNDS["thunder"], note="Lightning1/2 strikes")
    t_skin = t_lightning + 3.0
    for k in range(7):
        cinema.sound(t_skin + 0.4 * k, SOUNDS["purify"], note=f"NjamFreeze.scr :OnFreezeSkin2 Njam{k + 1}.dtx")
    # Njam: shown, runs, panics, twitches and freezes (clips of mm9_njam.glb: Running, WinGame, Twitch, Frozen).
    cinema.actor(t_start, njam, "show", note="NjamFreeze.scr :OnChase: Visible")
    cinema._cue(t_start, "faces his run", actor=njam, action="face", look_at=[round(c, 1) for c in stop], seconds=0)
    cinema._cue(t_start, "RunTo", actor=njam, action="clip", clip="Running", loop=True)
    cinema.actor(t_start, njam, "move", to=ramp_top, seconds=run_seconds * ramp_t, note="RunTo NJamMarker at 200 LT/s: the ramp")
    step_up = (RAMP_TOP_X + 1, ramp_top[1], stop[2])               # onto the hall's floor level at the ramp's top
    cinema.actor(t_start + run_seconds * ramp_t, njam, "move", to=step_up, seconds=0.05, note="the step at the top")
    cinema.actor(t_start + run_seconds * ramp_t + 0.05, njam, "move", to=stop, seconds=run_seconds * (1 - ramp_t) - 0.05,
                 note="RunTo NJamMarker: the hall")
    cinema._cue(t_arrive, ":OnArrive", actor=njam, action="clip", clip="Standing", loop=True)
    cinema._cue(t_panic, ":OnPanic PlayAnim njam_wingame", actor=njam, action="clip", clip="WinGame", loop=False)
    cinema._cue(t_lightning, ":OnLightning Loopanim njam_twitch", actor=njam, action="clip", clip="Twitch", loop=True)
    cinema._cue(t_skin + 0.4 * 7, ":OnFreezeSkin2 counter 8: Loopanim njam_frozen", actor=njam, action="clip",
                clip="Frozen", loop=True)
    # Earthquake (Njam's Panic triggers it, :OnLightningOff turns it off): a chain of shakes so it lasts that long.
    t = t_panic
    while t < t_off:
        seconds = min(1.5, t_off - t + QUAKE_DECAY_SECONDS)
        cinema.shake(t, QUAKE_INTENSITY, seconds, note="Earthquake (ShakeAmount 1 of 12, 400 LT)")
        t += 1.0

    winman = frame.point(_lt(objects, "WinMan"))
    radius = DESTROY_RADIUS_LT * cutscenes.SCALE
    wx, wy, wz = (int(round(c)) for c in winman)
    scene.step(0.0, "win", f"""
if MM9.hasKey(109) == 0 then MM9.giveExperience(WIN_EXPERIENCE) end
MM9.playSound("sounds/events/quest.wav")
-- :DestroyMonsters: up to {DESTROY_MAX} monsters within {DESTROY_RADIUS_LT} LT of the switch, not Njam (`scan`, not
-- `index`: pack growth's Lua scan, density.py, takes every `index` for one)
local removed, scan = 0, 0
while removed < {DESTROY_MAX} do
    local ax, ay, az = evt.GetMapActorPosition(scan)
    if ax == nil then break end
    if scan ~= ACTOR.Njam and scan ~= ACTOR.NjamtheMeddler0 and evt.IsMapActorHostile(scan)
            and (ax - {wx}) ^ 2 + (ay - {wy}) ^ 2 + (az - {wz}) ^ 2 < {int(round(radius))} ^ 2 then
        MM9.removeActor(scan)
        removed = removed + 1
    end
    scan = scan + 1
end""", note="OnUse: GiveExp 234000 (without key 109), quest.wav, DestroyMonsters")
    sx, sy, sz = (int(round(c)) for c in stop)
    scene.step(t_ball, "ball", f'evt.SpawnWorldEffect("mm9:Njam_lightball_for_cutscene", {sx}, {sy}, {sz + 160}, 1)',
               note="njam_wingame StartBall: DoClientFX 'Njam lightball for cutscene'")
    scene.step(t_lightning, "lightning", lightning_lua(frame, objects, LIGHTNING_SECONDS),
               note="njam_wingame Lightning: Lightning1/2 on for 7 s")
    x, y, z, facing = arrival
    scene.step(t_exit, "exit", f"""
MM9.giveKey(109)
set("Won", 1)
evt.MoveToMap({x}, {y}, {z}, {facing}, 0, 0, 0, 0, "hallofthegods.blv")""",
               note="WG_NjamCam StartFilm's key 109 (at the end: it is the world's completion, D3), :ChangeLevel ExitTrigger1")
    scene.step(t_cam_done, "switch", "winSwitch()", note="WG_Shot2Cam :OnPlay: WinMan switch (:onSwitch, on camera)")
    float_safe(cinema)
    return scene


# --- njam_taunt -----------------------------------------------------------------------------------------------------
def scene_feet(stem: str, index: int) -> tuple:
    """A map actor's feet in the map's scene (the review root's, else assets_dev's): its placed position (MM9's floor
    under the DAT object; a conversion does not move it)."""
    import json
    for root in (cutscenes.ROOT / "output/mm9_rework/assets_dev", cutscenes.INSTALLED):
        path = root / f"worlds/mm9/maps/{stem}.scene.yml"
        if path.exists():
            for a in json.loads(path.read_text())["initial_state"]["actors"]:
                if a["actor_index"] == index:
                    return (a["position"]["x"], a["position"]["y"], a["position"]["z"])
    raise SystemExit(f"{stem}: no scene with actor {index}")


def njam_taunt(frame: Frame, objects: Objects, actor: dict, points: dict) -> Scene:
    njam = actor["NjamtheMeddler0"]
    scene = Scene(TAUNT_ID, TAUNT_BASE, source="TauntMan.scr :OnStart..:FadeOut2, NjamTaunt.scr")
    cinema = scene.cinema
    start = scene_feet(STEM, njam)                        # his place behind Door0 (the SpawnNjam cameos move him)
    marker = tuple(points["TauntMarker"])                 # convert.py's point: on the floor (+2)
    start_lt, marker_lt = _lt(objects, "NjamtheMeddler0"), _lt(objects, "TauntMarker")
    walk = _dist((start_lt[0], start_lt[2]), (marker_lt[0], marker_lt[2])) / NJAM_WALK
    t_fade_in, t_walk = 1.0, 2.0                          # Wait 1 1 FadeIn, Wait 1 1 TriggerNjam
    t_arrive = t_walk + walk                              # NjamTaunt :OnArrive -> TauntMan Arrive (:OnCloseUp)
    camb, _ = frame.camera(objects, "TauntCamB")
    walk_yaw = math.atan2(marker[1] - start[1], marker[0] - start[0])
    cam_yaw = math.atan2(camb[1] - marker[1], camb[0] - marker[0])
    turn = abs(math.degrees(math.remainder(cam_yaw - walk_yaw, 2 * math.pi))) / 10.0   # FaceObject TauntCamB 10
    t_text1, t_text2 = t_arrive + 1.0, t_arrive + 5.0      # Wait 1 1 OnText1 (RolloverText 15), Wait 4 (16)
    t_vanish = t_arrive + 9.0                               # Wait 4 OnVanish: TauntMan VanishStart (:OnFarCam)
    t_gone, t_done = t_vanish + 1.0, t_vanish + 2.0        # Vanish2b (invisible), Vanish2c -> VanishDone (fade out)
    t_end = t_done + 1.0                                    # :FadeOut2: letterbox off, TauntCam off, fade in

    eye, fwd = frame.camera(objects, "TauntCam")
    eyeb, fwdb = frame.camera(objects, "TauntCamB")
    cinema.party(t_fade_in, note=":OnStart ScreenFadeOut 1, Wait 1")
    cinema.fixed(t_arrive - t_fade_in, eye, direction=fwd, fov=FOV, note="TauntCam (:FadeIn)")
    cinema.fixed(t_vanish - t_arrive, eyeb, direction=fwdb, fov=FOV, note="TauntCamB (:OnCloseUp)")
    cinema.fixed(t_end - t_vanish, eye, direction=fwd, fov=FOV, note="TauntCam (:OnFarCam)")
    cinema.party(1.0, note=":FadeOut2: the party's view, ScreenFadeIn 1")
    cinema.fade(0.0, "out", 1.0, note=":OnStart ScreenFadeOut 1")
    cinema.fade(t_fade_in, "in", 1.0, note=":FadeIn ScreenFadeIn 1")
    cinema.fade(t_done, "out", 1.0, note=":OnFadeOut ScreenFadeOut 1")
    cinema.fade(t_end, "in", 1.0, note=":FadeOut2 ScreenFadeIn 1")
    cinema.actor(0.0, njam, "hide", note="NjamTaunt.scr's Njam (also the SpawnNjam cameos': convert.py)")
    cinema.actor(t_fade_in, njam, "place", to=start, note="his DAT place behind Door0")
    cinema.actor(t_fade_in, njam, "show")
    cinema._cue(t_fade_in, "faces TauntMarker", actor=njam, action="face", look_at=[round(c, 1) for c in marker],
                seconds=0)
    cinema._cue(t_walk, "WalkTo TauntMarker", actor=njam, action="clip", clip="Walking", loop=True)
    cinema.actor(t_walk, njam, "move", to=marker, seconds=walk, note="WalkTo TauntMarker at 75 LT/s")
    cinema._cue(t_arrive, ":OnArrive", actor=njam, action="clip", clip="Standing", loop=True)
    cinema._cue(t_arrive, "FaceObject TauntCamB 10", actor=njam, action="face", look_at=[round(c, 1) for c in camb],
                seconds=round(turn, 3))
    cinema._cue(t_text1, "RolloverText 15", actor=njam, action="clip", clip="Conv", loop=False)
    cinema.subtitle(t_text1, " ".join(rollover_text(15).split()), t_text2 - t_text1,
                    note="RolloverText 15 (MMIXSCRIPTTEXT.csv)")
    cinema._cue(t_text2, "RolloverText 16", actor=njam, action="clip", clip="Conv1", loop=False)
    cinema.subtitle(t_text2, " ".join(rollover_text(16).split()), t_vanish - t_text2,
                    note="RolloverText 16 (MMIXSCRIPTTEXT.csv)")
    cinema.sound(t_vanish, SOUNDS["windup"], note=":OnVanish Windup10")
    cinema.actor(t_gone, njam, "hide", note="Vanish2b: clearflag visible")
    cinema.sound(t_gone, SOUNDS["teleport"], note="Vanish2b teleport.wav")

    scene.step(0.0, "key", f"MM9.giveKey(497) evt.SetMonGroupBit({NJAM_TAUNT_GROUP}, MonsterBits.Hostile, false)",
               note=":OnStart givekey 497; the taunting Njam is no SpawnNjam hunter (convert.py njamAppear)")
    scene.step(t_fade_in, "door_open", 'openGroup("Door0")', note=":FadeIn Door0 open")
    # the end demon's death opens the gate for good (EndDemon.scr :OnDeath, convert.py's kill hook): a taunt after it
    # leaves it open, or the win switch behind it could not be reached
    scene.step(t_arrive, "door_close", 'if var("EndDemonDead") ~= 1 then closeGroup("Door0") end',
               note=":OnCloseUp Door0 Close (not after the end demon's death)")
    mx, my, mz = (int(round(c)) for c in marker)
    scene.step(t_vanish, "vanish", f'evt.SpawnWorldEffect("mm9:GreaterDemon", {mx}, {my}, {mz}, 1)',
               note=":OnVanish DoClientFX GreaterDemon")
    return scene


# --- chess_capture --------------------------------------------------------------------------------------------------
def chess_scenes(frame: Frame, objects: Objects) -> tuple[list[Scene], list[int]]:
    """One cinematic per attacked square (convert.py's CHESS order: sorted squares), the camera where the party stands
    at ChessCam's height (MM9: the party's eye + 38 LT) looking at the first attacker still on the board (a pawn that
    can queen last) for the slide's 2 s. The party's facing is not known to the file: the shot starts on the piece
    (MM9 turns to it at 360 degrees a second)."""
    import convert
    shim = SimpleNamespace(objects=[{"name": e["values"].get("Name"), "properties": e["values"]}
                                    for e in objects.by_index.values() if e["values"].get("Name")])
    attackers = convert.chess_attackers(shim)
    queens = set(convert.queening_pawns(shim))
    height = _lt(objects, "ChessCam")[1]
    scenes, squares = [], sorted(attackers)
    if len(squares) > 49:
        raise ValueError("chess_capture: more squares than the event block holds")
    for i, k in enumerate(squares):
        pieces = sorted(attackers[k], key=lambda name: name in queens)
        board = _lt(objects, f"BoardObj{k}")
        eye = frame.point([board[0], height, board[2]])
        piece = frame.point(_lt(objects, pieces[0]))
        scene = Scene(f"{CHESS_PREFIX}{k}", CHESS_BASE + i,
                      source=f"ChessCamera.scr :ViewChessPiece: square {k}, {pieces[0]} attacks")
        # aimed along the line to the piece's centre (a look_at its centre reads as hidden behind its own faces)
        aim = tuple(p - e for p, e in zip(piece, eye))
        scene.cinema.fixed(CHESS_SLIDE_SECONDS, eye, direction=aim, fov=FOV,
                           note=f"ChessCam at BoardObj{k}, FaceObject {pieces[0]} 360")
        # CameraOn / CameraOff: LetterBox TRUE / FALSE (the default bars, written out: a cinematic needs a cue)
        scene.cinema.letterbox_cue(0.0, True, 0.3, note="ChessCamera.scr :CameraOn LetterBox TRUE")
        scene.cinema.letterbox_cue(CHESS_SLIDE_SECONDS - 0.3, False, 0.3, note=":CameraOff LetterBox FALSE")
        scenes.append(scene)
    return scenes, squares


CHESS_LUA = """
-- ChessBase.inc :StartCamera (the poll calls this when a piece attacks the party's square): the square's cinematic,
-- once per square (MM9 plays it on every attack: its pieces move, ours stand).
local CHESS_CAPTURE_SQUARES = {%s}
function MM9Cinematic.chessCapture(c)
    for i, entry in ipairs(CHESS) do
        if entry == c then MM9Cinematic.start("chess_capture_" .. CHESS_CAPTURE_SQUARES[i]) return end
    end
end
"""


def scenes(actor: dict, points: dict, arrival: tuple) -> list[Scene]:
    """Every Thousand Terrors cinematic: actor = DAT name -> map actor index (convert.py's ACTOR), points = its native
    object points (markers on their floor), arrival = the Hall of the Gods' StartPoint0 (hall_of_gods_arrival())."""
    frame, objects = Frame(PROJECT), Objects.load(STEM)
    chess, _ = chess_scenes(frame, objects)
    return [njam_freeze_win(frame, objects, actor, points, arrival), njam_taunt(frame, objects, actor, points)] + chess


def lua_block(scene_list: list[Scene]) -> str:
    """The map Lua's cinematics part: cutscenes.lua_block, WIN_EXPERIENCE, and the chess capture lookup."""
    squares = [int(s.id[len(CHESS_PREFIX):]) for s in scene_list if s.id.startswith(CHESS_PREFIX)]
    return cutscenes.lua_block(scene_list) + CHESS_LUA % ", ".join(map(str, squares))


def win_handler(event: int, experience_lua: str, min_y: float, frame: Frame, objects: Objects) -> list[str]:
    """WinMan.scr :OnUse (convert.py's handler for the switch): the TELP guard, without key 108 only the switch and
    the lightning (7 s), with it the cinematic."""
    return [
        "-- WinMan.scr :onSwitch, on each use and on WG_Shot2Cam's switch in the cinematic: PlayAnim up while bUp is",
        "-- FALSE, else Down, and bUp flips. bUp starts FALSE on a wheel at rest (up), so the first use shows only up's",
        "-- 200 ms blend, a twitch: nothing here. WinWheel: 0 never used, 1 up (bUp TRUE), 2 down (bUp FALSE); the",
        "-- clips are runtime only, so map load shows a wheel left down at the end of down.",
        "local function winSwitch()",
        "    if var(\"WinWheel\") == 1 then",
        "        set(\"WinWheel\", 2)",
        f"        evt.PlayDecorationClip({COG_WINMAN}, \"down\")",
        "    else",
        f"        if var(\"WinWheel\") == 2 then evt.PlayDecorationClip({COG_WINMAN}, \"up\") end",
        "        set(\"WinWheel\", 1)",
        "    end",
        "end",
        "-- The win switch (WinMan.scr :OnUse): nothing from beyond the wall (LT z below -3680); without key 108 it only",
        "-- throws the lightning (Lightning1/2, 7 s); with it the cinematic njam_freeze_win (cinematics_1000t.py).",
        f"WIN_EXPERIENCE = {experience_lua}",
        f"handlers[{event}] = function()",
        "    local _, py = evt.GetPartyPosition()",
        f"    if py < {int(round(min_y))} then return end",
        "    winSwitch()",
        "    if MM9.hasKey(108) == 0 then",
        f"        MM9.playSound({lua_quote(SOUNDS['switch'])})",
        f"        MM9.playSound({lua_quote(SOUNDS['thunder'])})",
        *["        " + line for line in lightning_lua(frame, objects, LIGHTNING_SECONDS).split("\n")],
        "        set(\"SwitchThrown\", var(\"SwitchThrown\") + 1)",
        "        return",
        "    end",
        f"    MM9Cinematic.start(\"{WIN_ID}\")",
        "end",
    ]


def lua_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\") + '"'


def switch_min_y(frame: Frame) -> float:
    return frame.point([0, 0, SWITCH_MIN_Z_LT])[1]


# --- sounds ---------------------------------------------------------------------------------------------------------
def sound_files(scene_list: list[Scene]) -> list[tuple[str, Path]]:
    """The cues' MM9 sounds (not voices: the world has those) as (worlds/mm9/audio relative path, MM9 source)."""
    sys.path.insert(0, str(cutscenes.ROOT / "tools/mm9_import_discovery"))
    import generate_mm9_events as mm9_events
    index = mm9_events.build_source_sound_index(cutscenes.SOUNDS)
    names = {cue["sound"] for s in scene_list for cue in s.cinema.cues if "sound" in cue} | set(SOUNDS.values())
    out = []
    for name in sorted(names):
        relative = mm9_events.normalize_mm9_sound_name(name).lower()
        source = mm9_events.find_source_sound_path(index, relative)
        if source is None:
            raise SystemExit(f"cinematic sound {name}: no MM9 source")
        out.append((f"worlds/mm9/audio/{relative}", source))
    return out


def install(scene_list: list[Scene]) -> None:
    """A conversion's install: the cinematics file and the cues' sounds the world lacks, into the review root."""
    import review_root
    cutscenes.install(STEM, scene_list)
    for relative, source in sound_files(scene_list):
        if not review_root.mirror_path(relative).is_file():
            review_root.install(relative, source.read_bytes())
