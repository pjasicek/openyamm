#!/usr/bin/env python3
"""
The Bathhouse's cutscene and quake (devdocs/mm9_rework/MM9_CUTSCENES.md): one place for convert.py (the map Lua and
the installed bathhouse.cinematics.yml) and cinematics_pilot.py (the test without a conversion).

`ebora_escape` (EboraBath.scr :DeadConcubine -> EscapeTheTub, after the third concubine dies):
    TurnCameraOn (the TELP 1.3 overload): ScreenFadeIn 1, LetterBox, EboraCam1 on (EboraCam1.scr :CameraOn: FaceObject
    Ebora at rate 0, a snap: its yaw toward her, its pitch kept); RollOverText 11; PlayAnim launch -> :CastSpell
    PlayAnim Castspell -> :DitchTheJoint (the column of fire ClientFX and column03.wav, key 349 + 80 000 experience with
    key 348 else key 350; Wait 1 1 :ClearMe, she turns invisible; Wait 27 1.5 :TurnCameraOff).
    Timing: the two animations' lengths from EBORA.abc (launch 0.9 s, Castspell 1.5 s), then the two waits: the column
    at 2.4 s, her removal at 3.4 s, the end at 3.9 s.
    The subtitle is MM9's RollOverText 11 (MMIXSCRIPTTEXT.csv).

The EffectsMgr quake (EffectsMgr.scr on the EarthQuake EffectsMgr): the valve's first opening (GasRelease0 OpenTrigger3
-> TriggerEffects, ActivationCount 1) sends QuakeOn, BoxOff, DurationLong (QuakeDuration 12, four sound loops),
QuakeWeak (ShakeAmount 6) and StartScene: the quake object moves to the player and fires (DecayRate 1 from
SetupQuakeObject), and eqhammerpostimpactloop.wav plays four times back to back. Section 5's rule: intensity 6 / 12,
seconds 12 + 6 / 1, no point (the object stands on the party).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import cutscenes  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

STEM = "bathhouse"
CINEMA_ID = "ebora_escape"
EVENT_BASE = 36000                  # done 36000, steps 36001.. (MM9_CUTSCENES.md converters: 36000 + 50 k)
KEY_ERRAND, KEY_CLEANED, KEY_CLEANED_UNASKED, EBORA_EXPERIENCE = 348, 349, 350, 80000
# EboraBath.scr :EscapeTheTub RollOverText 11 (MMIXSCRIPTTEXT.csv, mm9r_common/script_text.py)
from script_text import rollover_text  # noqa: E402
ESCAPE_LINE = rollover_text(11)
COLUMN_EFFECT = "mm9:column_of_fire"        # ClientFX `spell-column of fire` (plays column03 itself)

# EffectsMgr.scr after TriggerEffects' messages (DurationLong, QuakeWeak; SetupQuakeObject's DecayRate 1).
QUAKE_AMOUNT, QUAKE_DURATION, QUAKE_DECAY, QUAKE_LOOPS = 6.0, 12.0, 1.0, 4
QUAKE_SOUND = "sounds/weapons/eqhammerpostimpactloop.wav"


def quake_shake() -> tuple[float, float]:
    """MM9_CUTSCENES.md section 5: (intensity, seconds)."""
    amount = min(QUAKE_AMOUNT, 12.0)
    return round(amount / 12.0, 3), round(QUAKE_DURATION + amount / QUAKE_DECAY, 3)


def quake_loop_polls(poll_seconds: float = 0.25) -> int:
    """The rumble loop's length in the map's poll ticks (the next loop starts when one ends: PlaySound's callback)."""
    return max(1, round(cutscenes.wav_seconds("sounds\\weapons\\eqhammerpostimpactloop.wav") / poll_seconds))


def quake_lua() -> list[str]:
    """The valve handler's first-opening lines (inside `if var("Furnace") == 0`)."""
    intensity, seconds = quake_shake()
    return [
        "        if var(\"Quaked\") == 0 then   -- TriggerEffects (once) -> EffectsMgr.scr: the weak long quake",
        "            set(\"Quaked\", 1)",
        f"            evt.CameraShake({intensity}, {seconds})",
        f"            evt.PlaySoundName(\"{QUAKE_SOUND}\", 0, 0, 0)",
        f"            rumble.left, rumble.ticks = {QUAKE_LOOPS - 1}, 0",
        "        end",
    ]


def rumble_poll_lua() -> list[str]:
    """The poll's lines that play the remaining rumble loops back to back."""
    return [
        "    -- the quake's rumble loops (EffectsMgr.scr PlaySoundLoop: the next when one ends)",
        "    if rumble.left > 0 then",
        "        rumble.ticks = rumble.ticks + 1",
        f"        if rumble.ticks >= {quake_loop_polls()} then",
        f"            rumble.left, rumble.ticks = rumble.left - 1, 0",
        f"            evt.PlaySoundName(\"{QUAKE_SOUND}\", 0, 0, 0)",
        "        end",
        "    end",
    ]


RUMBLE_LOCAL = "local rumble = {left = 0, ticks = 0}   -- EffectsMgr.scr's rumble loops still to play (transient)"


def scenes(ebora_actor: int) -> list[cutscenes.Scene]:
    """ebora_escape; `ebora_actor` is Ebora's map actor index (convert.py actor_index["Ebora"]). The step bodies use the
    map script's locals `set` and `EBORA`."""
    objects = cutscenes.Objects.load(STEM)
    frame = cutscenes.Frame(PROJECT)
    launch, _ = cutscenes.abc_animation("ebora", "launch")
    cast, _ = cutscenes.abc_animation("ebora", "Castspell")
    column = launch + cast                     # :DitchTheJoint
    clear = column + 1.0                       # Wait 1 1 ClearMe
    end = column + 1.5                         # Wait 27 1.5 TurnCameraOff

    eye, forward = frame.camera(objects, "EboraCam1")
    ebora = frame.point(objects.named("Ebora")["values"]["Pos"])
    facing, _ = cutscenes.face_toward(forward, eye, ebora, 0.0, 0.0)   # FaceObject hEbora, 0: a snap

    scene = cutscenes.Scene(CINEMA_ID, EVENT_BASE, source="EboraBath.scr :EscapeTheTub..:TurnCameraOff, EboraCam1.scr")
    cinema = scene.cinema
    cinema.fixed(end, eye, direction=facing, fov=cutscenes.MM9_CAMERA_FOV,
                 note="EboraCam1 on (FaceObject Ebora 0) until TurnCameraOff")
    cinema.fade(0.0, "in", 1.0, note="TurnCameraOn (TELP 1.3): ScreenFadeIn 1")
    cinema.subtitle(0.0, ESCAPE_LINE, end, note="RollOverText 11")
    cinema._cue(0.0, "PlayAnim launch", actor=ebora_actor, action="clip", clip="Launch", loop=False)
    cinema._cue(launch, ":CastSpell PlayAnim Castspell", actor=ebora_actor, action="clip", clip="AttackRanged",
                loop=False)
    scene.step(column, "column", "\n".join([
        "local x, y, z = evt.GetMapActorPosition(EBORA)",
        f"if x ~= nil then evt.SpawnWorldEffect(\"{COLUMN_EFFECT}\", x, y, z, 1) end",
        "set(\"EboraGone\", 1)",
        f"if MM9.hasKey({KEY_ERRAND}) == 1 then",
        f"    if MM9.hasKey({KEY_CLEANED}) == 0 then",
        f"        MM9.giveKey({KEY_CLEANED})",
        f"        {experience_lua(EBORA_EXPERIENCE, KEY_CLEANED)}",
        "        MM9.playSound(\"sounds/events/quest.wav\")",
        "    end",
        "else",
        f"    MM9.giveKey({KEY_CLEANED_UNASKED})",
        "end",
    ]), note=":DitchTheJoint: column of fire, column03.wav (in the effect), keys and experience")
    scene.step(clear, "clear", "MM9.removeActor(EBORA)", note=":ClearMe: ClearFlag hMe, FLAG_VISIBLE")
    return [scene]
