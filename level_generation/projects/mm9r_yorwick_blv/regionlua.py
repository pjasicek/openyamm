"""
Yorwick (the region) map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/
SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests and ForadWorld.scr
(devdocs/mm9_rework/REGIONS_FINISH.md step 2; the behaviour spec of every script is work/scr_spec.md). RUDE exits are
event 50000 + the DAT object index (game/mm9/Mm9RudeDialogue.h).

- The five letters (BookLetter.scr "<row> Letter"): a click shows their BOOK AND SCROLL TEXT.csv row, as in the cities.
- Prop2, the Penance Quest's prop (Hidemodel.scr "102 Unhide"): shown only once the Six Fires of Penance are lit (key
  102), checked on every load.
- The battlefield (Svenspeech.scr on Sven, with BattleCam1.scr's cameras): arriving with Bikki's prize delivered (key
  95) and the battle not yet seen (key 97), MM9 plays the battlefield cutscene (Sven's speech over the fallen) and
  pays 114 000 experience and key 97 at its fourth line: the cinematic battlefield_sven (yorwick.cinematics.yml,
  `scenes()` here; devdocs/mm9_rework/MM9_CUTSCENES.md). Key 97 carries the main quest (the Writ of Fate, "Get your
  army back") and the journal's chapter "II: The Battlefield". SvenShowTake.inc's tableau (the guard, Kira, the
  fallen, the swords and arrows: one SetSprite key, COG_TABLEAU) and Sven (an actor: overrides.yml people) show only
  while the cutscene is due, as its :Init; the cinematic's last step hides them under its fade (MM9 kept them until
  the next load, which hides them).
- The gate (CTgate) is barred by gateboard (a destructible, 15 HP; its DeathTrigger: CTgate open): BARRED_DOORS, the
  shared rule. The five boards (board0-4, 10 HP) break with no trigger (dungeon/destructibles.py).
- Mary the shepherdess (NPC312.scr, RUDE 312): her sheep returned (her dialogue gives key 467), leaving the dialogue
  pays 2 gold and 20 000 experience (key 468).
- Mary's ewe (MarySheep.scr on Ewe0, an `outdoor.people` actor so that its click runs event 53000 + index): a click
  (:OnUse, FollowPlayer.inc) makes it follow the party: a half-second poll sends it after the party by
  evt.MoveActorTo (it runs when far behind). Within 512 LT of Mary (NPC312.scr :ONTarget, OnTargetWithinDist 512
  :RuntoMe): key 466 (her row "Here's your sheep") and the ewe runs to her (MarySheep.scr :OnRun) and stays there.

Not here: Sven's 43.7 s speech animation (SVEN.abc Sven_scene06: mm9_sven.glb has no such clip; he plays Talk), the
dead Bjarni (Kira0), Sigmund and Tryggva of the tableau (no dead figures: placements.py LEFT_OUT), the ewe's wandering before the click and after
(BaseWander.inc, Cat.scr: it stands), the shopkeepers' and Mary's voice lines on a click, the pickaxes (PropAnim.scr "onside": placed as static
props) and StatStone0 (not placed).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import cutscenes
from quest_xp import balanced_experience, experience_note

ROOT = Path(__file__).resolve().parents[3]
SCALE = 2.56                    # MM9 units -> engine units (tools/mm9_import_discovery/mm9_units.py)
LETTER_TEXTS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
EV_PROP = 330           # a scripted prop's click: EV_PROP + k
COG_PROP = 400          # its SetSprite key (hide or show): COG_PROP + k
LETTERS = {"Prop80": 477, "Prop81": 478, "Prop82": 475, "Prop83": 474, "Prop84": 476}    # BookLetter.scr p0
HIDDEN = {"Prop2": ("hidemodel.scr \"102 Unhide\"", "has(102)")}                        # DAT name -> (script, shown)
BATTLE_SEEN_KEY, BATTLE_PRIZE_KEY, BATTLE_XP = 97, 95, 114000
COG_TABLEAU = COG_PROP + len(HIDDEN)   # SvenShowTake.inc's RemoveAll props (one SetSprite key for all)
SVEN = "Sven"                           # Svenspeech.scr's object: an actor (overrides.yml outdoor.people)
CINEMA_ID, CINEMA_EVENTS = "battlefield_sven", 36000     # done event; its steps 36001..
BATTLE_AMBIENT = [f"AmbientSound{k}" for k in range(8)]  # Svenspeech.scr :OnStart off, :FadeOut2 on
VOICES = ROOT / "mm9/extracted/VOICES/VOICES"
BARRED_DOORS = {"CTgate": "gateboard"}                                                 # door group -> destructible
MARY, EWE = "CommonerChildHuman2ChildA0", "Ewe0"    # NPC312.scr, MarySheep.scr
T_EWE = 340                                         # timer: the ewe's follow poll
EWE_AT_MARY_LT = 512                                # NPC312.scr :ONTarget OnTargetWithinDist 512
EWE_FOLLOW_GAP = 300                                # engine units: the ewe stops this close behind the party
EWE_RUN_GAP = 1200                                  # and runs when further behind


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTER_TEXTS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTER_TEXTS}")


def tableau_names() -> list[str]:
    """SvenShowTake.inc :RemoveAll's objects but Sven (an actor here): the battlefield's posed dead and weapons."""
    text = (cutscenes.SCRIPTS / "SVENSHOWTAKE.inc").read_bytes().decode("latin-1")
    body = text.split(":RemoveAll", 1)[1].split(":Clear", 1)[0]
    return [name for name in re.findall(r"getobjecthandle\s+(\S+)", body, re.I) if name != SVEN]


def prop_events(build) -> tuple[dict, dict]:
    events = {name: EV_PROP + k for k, name in enumerate(LETTERS)}
    cogs = {name: COG_PROP + k for k, name in enumerate(HIDDEN)}
    # getobjecthandle ignores case (the script's Sigmund is the DAT's sigmund): the key goes by the DAT's spelling
    cogs.update({build.source.by_name[name.lower()]["name"]: COG_TABLEAU for name in tableau_names()
                 if name.lower() in build.source.by_name})
    return events, cogs


def voice_seconds(name: str) -> float:
    """A cinema voice's length (VOICES/CINEMA/BATTLEFIELD/<name>.wav)."""
    import wave
    with wave.open(str(VOICES / "CINEMA/BATTLEFIELD" / f"{name.upper()}.wav")) as stream:
        return stream.getnframes() / float(stream.getframerate())


def ambient_keys() -> list[int]:
    """The map's AmbientSound keys (their DAT indices: dungeon/ambient.py) that Svenspeech.scr switches."""
    objects = cutscenes.Objects.load("yorwick")
    return [objects.named(name)["index"] for name in BATTLE_AMBIENT]


def scenes(sven_actor: int) -> list:
    """Svenspeech.scr's cutscene (Init with key 95 and not 97, wait .3 :OnStart, fade out 1, :FadeIn; the cinematic
    starts at :FadeIn): Camera0 MoveToPos CameraMarker0 at 70 (BattleCam1.scr :OnPlay; its arrival sends Sven Done),
    Camera1 to the marker Camera2 at 40, Camera3 to Camera4 at 10 (:Cam2, :Cam3), then Camera5 (:Cam5) while Sven plays
    Sven_scene06 (43.7 s), whose keys cut to Camera6/7/8 and start sven01-04.wav; :Award at Sven04 (key 97, 114 000
    experience); the anim's FadeOut key: wait 1, fade out 1, :FadeOut2 (ambient sounds on, quest.wav, letterbox off,
    fade in 1). Fixed cameras look along their DAT rotation (Target does not aim in MM9); fov MM9_CAMERA_FOV."""
    project = Path(__file__).resolve().parent
    objects = cutscenes.Objects.load("yorwick")
    frame = cutscenes.Frame(project)
    fov = cutscenes.MM9_CAMERA_FOV
    scene = cutscenes.Scene(CINEMA_ID, CINEMA_EVENTS, source="Svenspeech.scr :Init..:FadeOut2, BattleCam1.scr")
    cinema = scene.cinema
    t = 0.0

    def move(camera: str, marker: str, lt_speed: float, note: str) -> float:
        eye, forward = frame.camera(objects, camera)
        target, _ = frame.camera(objects, marker)
        _, arrival = cutscenes.move_to_pos(eye, target, frame.speed(lt_speed), 0.0)
        cinema.moving(arrival, [(0.0, eye, {"direction": forward, "fov": fov}),
                                (arrival, target, {"direction": forward, "fov": fov})], easing="linear", note=note)
        return arrival

    # :FadeIn: letterbox, Camera0 On and Play, fade in 1; each arrival sends Sven Done (:OnDone -> :Cam2/3/5)
    cinema.fade(t, "in", 1.0, note=":OnStart screenfadeout 1, :FadeIn screenfadein 1")
    scene.step(t, "start", "\n".join(
        ["battlefield(true)   -- SvenShowTake.inc :RemoveAll with ShowAll TRUE (:Init)"]
        + [f"set(\"AmbientSound{k}\", 2)   -- {name} off (:OnStart)" for name, k in zip(BATTLE_AMBIENT, ambient_keys())]),
        note=":OnStart: AmbientSound0-7 off")
    t += move("Camera0", "CameraMarker0", 70.0, "Camera0 MoveToPos CameraMarker0 at 70 (:FadeIn)")
    cinema.fade(t, "in", 1.0, note=":Cam2 screenfadein 1")
    t += move("Camera1", "Camera2", 40.0, "Camera1 MoveToPos Camera2 at 40 (:Cam2)")
    cinema.fade(t, "in", 1.0, note=":Cam3 screenfadein 1")
    t += move("Camera3", "Camera4", 10.0, "Camera3 MoveToPos Camera4 at 10 (:Cam3)")
    # :Cam5: Camera5 On, PlaySpeech: Sven_scene06 with its model keys (AddModelKey)
    cinema.fade(t, "in", 0.5, note=":Cam5 screenfadein .5")
    speech = t
    length, keys = cutscenes.abc_animation("SVEN", "Sven_scene06")
    key = {name: at for at, name in keys}
    eye5, _ = frame.camera(objects, "Camera5")
    cinema._cue(speech, "Sven turns to the camera (Sven_scene06 faces Camera5)", actor=int(sven_actor),
                action="face", look_at=[round(v, 1) for v in eye5], seconds=0.0)
    cinema._cue(speech, "Sven_scene06 (not in mm9_sven.glb): his conversation clip", actor=int(sven_actor),
                action="clip", clip="Talk", loop=True)
    cuts = [("Camera5", 0.0), ("Camera6", key["Camera6"]), ("Camera7", key["Camera7"]), ("Camera8", key["Camera8"])]
    end_anim = speech + length
    fade_out = end_anim + 1.0          # :OnFadeOut wait 1 -> :FadeOut screenFadeout 1
    finale = fade_out + 1.0            # wait 1 -> :FadeOut2
    for k, (camera, at) in enumerate(cuts):
        until = speech + cuts[k + 1][1] if k + 1 < len(cuts) else finale
        eye, forward = frame.camera(objects, camera)
        cinema.fixed(until - (speech + at), eye, direction=forward, fov=fov,
                     note=f"{camera}" + (f" (Sven_scene06 key {camera} at {at:g} s)" if at else " (:Cam5)"))
    for number in range(1, 5):
        name = f"sven0{number}"
        at = speech + key[f"Sven0{number}"]
        cinema.sound(at, f"voices\\cinema\\battlefield\\{name}.wav",
                     note=f"Sven_scene06 key Sven0{number}: :OnSven0{number} ({voice_seconds(name):.1f} s)")
    xp = balanced_experience(BATTLE_XP, BATTLE_SEEN_KEY)
    scene.step(speech + key["Sven04"], "award",
               f"if not has({BATTLE_SEEN_KEY}) and has({BATTLE_PRIZE_KEY}) then MM9.giveKey({BATTLE_SEEN_KEY}); "
               f"MM9.giveExperience({xp}) end",
               note=":OnSven04 gosub Award: key 97, 114 000 experience")
    cinema.fade(fade_out, "out", 1.0, note="Sven_scene06 key FadeOut: wait 1, :FadeOut screenFadeout 1")
    scene.step(finale, "finale", "\n".join(
        [f"set(\"AmbientSound{k}\", 1)   -- {name} on" for name, k in zip(BATTLE_AMBIENT, ambient_keys())]
        + ["battlefield(false)   -- the tableau as every later load leaves it (:Init with key 97)"]),
        note=":FadeOut2: AmbientSound0-7 on, letterbox false, Camera8 Off")
    cinema.sound(finale, "sounds\\events\\quest.wav", note=":FadeOut2")
    cinema.fade(finale, "in", 1.0, note=":FadeOut2 screenFadeIn 1")
    cinema.party(1.0, note="the party's view again (:FadeOut2 Camera8 Off)")
    return [scene]


def battlefield_lines(sven_actor: int) -> list[str]:
    """The map Lua's part of Svenspeech.scr: the tableau and Sven shown or hidden (SvenShowTake.inc), and the load
    that starts the cinematic (:Init)."""
    return [
        f"-- Svenspeech.scr :Init with SvenShowTake.inc: the battlefield's tableau (SetSprite key {COG_TABLEAU}) and Sven",
        f"-- (actor {sven_actor}) are shown only while Bikki's prize is delivered (key {BATTLE_PRIZE_KEY}) and the battle "
        f"not seen (key {BATTLE_SEEN_KEY});",
        f"-- then the cinematic {CINEMA_ID} plays (its :Award gives key 97 and the experience).",
        "local function battlefield(shown)",
        f"    evt.SetSprite({COG_TABLEAU}, shown and 1 or 0, \"0\")",
        f"    evt.SetMonsterBit({sven_actor}, ActorAttribute.Invisible, shown and 0 or 1)   -- Sven",
        "end",
    ]


def battlefield_load_lines() -> list[str]:
    return [
        f"    local battle = has({BATTLE_PRIZE_KEY}) and not has({BATTLE_SEEN_KEY})",
        f"    battlefield(battle)   -- Sven (svenspeech.scr :Init)",
        f"    if battle then MM9Cinematic.start(\"{CINEMA_ID}\") end",
    ]


def rude_exit(build, name: str) -> int:
    return 50000 + build.source.by_name[name.lower()]["index"]


def extend(hooks, build, script) -> None:
    events, cogs = prop_events(build)
    lines = ["-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows)."]
    for name, number in LETTERS.items():
        title, text = letter(number)
        lines.append(f"handlers[{events[name]}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0); "
                     f"evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end   -- {name} ({number})")
    lines += [
        "",
    ]
    sven_actor = hooks.npc_actor[SVEN]
    lines += battlefield_lines(sven_actor)
    lines += [
        "",
        "-- Hidemodel.scr :Init (Prop2) shows the Penance Quest's prop once key 102 is held.",
        "handlers.regionLoad = function()",
    ]
    for name, (scr, shown) in HIDDEN.items():
        lines.append(f"    evt.SetSprite({cogs[name]}, ({shown}) and 1 or 0, \"0\")   -- {name} ({scr})")
    lines += battlefield_load_lines()
    lines += [
        "end",
        "",
    ]
    mary = MARY
    lines += [
        "-- NPC312.scr :OnRude (Mary, RUDE 312): her sheep back (key 467 from her row \"Here's your sheep\"): 2 gold,",
        "-- 20 000 experience, key 468.",
        f"handlers[{rude_exit(build, mary)}] = function()",
        f"    if has(467) and not has(468) then reward(468, {balanced_experience(20000, 468)}, 2) end"
        f"{experience_note(20000, 468)}",
        "end",
        "",
    ]
    registrations = [(events[name], name, "Read") for name in LETTERS]
    registrations.append((rude_exit(build, mary), "Mary", None))
    ewe_lines, ewe_registrations = ewe(hooks, build)
    lines += ewe_lines
    registrations += ewe_registrations
    script.add(lines, *registrations)
    if ewe_lines:
        script.hooks.append(f'RegisterMapTimerEvent({T_EWE}, seconds(0.5), handlers[{T_EWE}], "The ewe follows", "", '
                            'seconds(0.5))')
    # The cutscene's steps, done event and start function (mm9r_common/cutscenes.py), and its yml beside the map
    cinematic_scenes = scenes(sven_actor)
    script.add(cutscenes.lua_block(cinematic_scenes).split("\n"))
    if build.project.install:
        print(f"cinematics installed: {cutscenes.install(build.project.stem, cinematic_scenes)} ({CINEMA_ID})")


def ewe(hooks, build) -> tuple[list, list]:
    """MarySheep.scr and NPC312.scr's :ONTarget/:RuntoMe (module docstring): the ewe's click and its follow poll.
    State: map var EweFollow (1 following the party, 2 back with Mary)."""
    actors = getattr(hooks, "npc_actor", {})
    if EWE not in actors or MARY not in actors:
        return [], []
    ewe_actor, mary_actor = actors[EWE], actors[MARY]
    ewe_index = build.source.by_name[EWE.lower()]["index"]
    at_mary = round(EWE_AT_MARY_LT * SCALE)
    lines = [
        f"-- MarySheep.scr :OnUse (the ewe, actor {ewe_actor}): it follows the party (FollowPlayer.inc) until it is within",
        f"-- {EWE_AT_MARY_LT} LT of Mary (actor {mary_actor}; NPC312.scr :RuntoMe): key 466, and it runs to her and stays.",
        "-- MM9's lifecycle (MM9.receives, MM9.actorAlive): the click sends Mary \"Target\", which a slain Mary does not",
        "-- take (map var EweUnwatched 1: no key from this walk); :RuntoMe is her OnTargetWithinDist, which fires only",
        "-- while she lives; a slain ewe follows no more and takes no RuntoMe.",
        f"handlers[{53000 + ewe_index}] = function()   -- {EWE}",
        "    if has(466) or var(\"EweFollow\") ~= 0 then return end",
        "    set(\"EweFollow\", 1)",
        f"    set(\"EweUnwatched\", MM9.receives(\"yorwick\", \"{MARY}\", \"Target\", {mary_actor}) and 0 or 1)",
        "end",
        f"handlers[{T_EWE}] = function()",
        "    if var(\"EweFollow\") ~= 1 then return end",
        f"    local ex, ey = evt.GetMapActorPosition({ewe_actor})",
        f"    local mx, my, mz = evt.GetMapActorPosition({mary_actor})",
        "    if ex == nil or mx == nil then return end",
        f"    if var(\"EweUnwatched\") == 0 and MM9.actorAlive({mary_actor}) and (ex - mx) ^ 2 + (ey - my) ^ 2 <= "
        f"{at_mary} ^ 2 then",
        "        set(\"EweFollow\", 2)",
        "        MM9.giveKey(466)",
        f"        if MM9.receives(\"yorwick\", \"{EWE}\", \"RuntoMe\", {ewe_actor}) then",
        f"            evt.MoveActorTo({ewe_actor}, mx, my, mz, 0, true)   -- :OnRun: runto Mary",
        "        end",
        "        return",
        "    end",
        f"    if not MM9.actorAlive({ewe_actor}) then return end   -- FollowPlayer.inc: the ewe's own walk",
        "    local px, py, pz = evt.GetPartyPosition()",
        "    local gap = math.sqrt((ex - px) ^ 2 + (ey - py) ^ 2)",
        f"    if gap > {EWE_FOLLOW_GAP} then evt.MoveActorTo({ewe_actor}, px, py, pz, 0, gap > {EWE_RUN_GAP})",
        f"    else evt.StopActorMove({ewe_actor}) end",
        "end",
        "",
    ]
    return lines, [(53000 + ewe_index, "Mary's ewe", None)]
