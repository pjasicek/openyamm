"""
The Afterworld map Lua: Skraelos' Six Fires of Penance as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/
SCRIPTS; behaviour spec: work/scr_spec.md). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared
doors, chests and ForadWorld.scr (devdocs/mm9_rework/REGIONS_FINISH.md step 2). RUDE exits are event 50000 + the DAT
object index, a click before the dialogue 53000 + index, found-player events 56000 + index (game/mm9/Mm9RudeDialogue.h).

Skraelos (NPC336.scr "Afterworld" with SixFires.inc and SvenShowTake.inc; RUDE 336) runs the six fires on his
dialogue's exit, by the keys its rows give (Hall of the Gods' NPC336 sends the party here with key 379):
- Guilt (key 380): MM9 flies a camera over the battlefield (Camera9, AfterWorldCam1.scr); its arrival sends "Done":
  key 381, the quest sound, a 2 s fade out, and he greets the party again (key 379, his dialogue): the cinematic
  afterworld_guilt (afterworld.cinematics.yml, `scenes()` here; devdocs/mm9_rework/MM9_CUTSCENES.md).
- Confession (key 382): the six fallen heroes (Bjarni, Kira, Markel, Sigmund, Sven, Tryggva; hidden until now) stand
  in the Afterworld and their dialogues take the confessions (keys 501-506); a click on Skraelos with all six gives
  key 383 and 52 000 experience; the next exit sends the heroes away.
- Suffering (key 384): the party is poisoned and diseased and the Questioner's dialogue (RUDE 432) opens; its right
  answers give key 385, and the next exit cures the party and gives key 491 and 52 000 experience.
- Retribution (key 386): key 5021 and Forad Darre appears; his death sends RetributionCounter "OneDown"
  (TM_Hardrock.scr "1 387": key 387 and the quest sound).
- Absolution (key 388): key 492, 52 000 experience and the five heroes' swords appear on the battlefield (Givetake.scr
  "<item> TRUE": world items, ../mm9r_common/dungeon/pickups.py, shown with key 492; Sven's 563 lies there from the
  start); a click on Skraelos with all five takes them: key 389 and
  52 000 experience.
- Rebirth (key 390): ExitTrigger1 in the blazing fire opens; stepping in (PropTrigger.scr "Skraelos0 Reborn") gives
  keys 391 and 102 and 52 000 experience (once): the map's leave event, when the party leaves by that exit.
- Failure (key 392, "No, it was not our fault"): keys 379-392 taken and the party is sent to the Hall of the Gods
  (`trigger ExitTrigger0`: its transitions row's arrival).

The Six Fires (GuiltFire ... RebirthFire: Fire objects with On 0 that the stages switch "On"; `populate` places
their flames, the gate fire's mm9_gatefire_x8 at FireScale 1, each with its SetSprite key COG_FIRE + k) burn once
their stage is done: Guilt 381, Confession 383, Suffering 491, Retribution 387 (MM9 lights it at Absolution's start),
Absolution 389, Rebirth 391; checked on every load and after each stage (sixFires()). MM9 never sends GuiltFire
"On" (no script names it): here it lights with key 381 like the others. Their lights and fire sounds are not
switched (the always-on fires' are static: dungeon/objects.py place_fires).

Not here (work/scr_spec.md): BattleCam1.scr's cameras (Camera0-8 and 10: a copy of Yorwick's set no script here
uses), the posed dead on the battlefield (Propanim.scr, left out on purpose; SvenShowTake.inc
shows them at Absolution), the clan soldiers and hordes of SixFires.inc :Spawn and :GoodGuys (no caller: dead code)
and the 5 s pause before the Questioner. The stages' spawns are carried (SPAWNS): Retribution's twelve Horde Leaders
and Warriors at BadGuys0/1 with Forad, Absolution's and every Rebirth exit's Zombie, Ghast and five Frights at
BadGuys0/1 and GoodGuys0 (2026-11-06, devdocs/mm9_rework/MM9_ACTOR_COMPLETENESS.md).

ExitTrigger1 is off until Rebirth (key 390): the map var Mm9ExitDisabled105, which the engine's exit triggers read.
Forad Darre (ForadDarre0, hostile row 9252: overrides.yml monster_classes and mm9_monster_legacy_replacements.tsv
row 252) is hidden until Retribution (key 5021); his death gives key 387.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

import cutscenes
from quest_xp import balanced_experience, experience_lua, experience_note

EV_LEAVE = 600          # the map's leave event: PropTrigger.scr on ExitTrigger1 -> NPC336.scr :OnReborn
EV_KILL = 601           # monster killed hook: Forad Darre's DeathTriggerTarget (TM_Hardrock.scr :OneDown)
COG_FIRE = 420          # the Six Fires' SetSprite keys: COG_FIRE + k
# The Six Fires (DAT name -> the key whose stage lights it: NPC336.scr and SixFires.inc `trigger <fire> On`)
FIRES = {"GuiltFire": 381, "ConfessionFire": 383, "SufferingFire": 491, "RetributionFire": 387,
         "AbsolutionFire": 389, "RebirthFire": 391}
SKRAELOS = "Skraelos0"
FORAD = "ForadDarre0"
HEROES = ("BjarniThorvaldssen0", "KiratheCold0", "MarkeltheGreat0", "SigmundtheStressed0", "SvenSvenssen0",
          "TryggvaRavenlocks0")
SKRAELOS = "Skraelos0"
FORAD = "ForadDarre0"
HEROES = ("BjarniThorvaldssen0", "KiratheCold0", "MarkeltheGreat0", "SigmundtheStressed0", "SvenSvenssen0",
          "TryggvaRavenlocks0")
# DAT name -> (item, shown from the start): Givetake.scr "<item> TRUE"; SvenSword is the only one MM9 shows (Visible 1)
SWORDS = {
    "SvenSword": (563, True),
    "BjarniSword": (564, False),
    "SigmundSword": (565, False),
    "TryygvaSword": (566, False),
    "KiraSword": (567, False),
}
# SixFires.inc's spawns, (marker, MM9 MONSTERS.txt row + 9000, count) per stage: :Retribution sMonsterB HordeLeader
# and sMonsterC HordeWarrior (B B C C B at BadGuys0, B B C C B B B at BadGuys1); :Absolution and :Rebirth set
# sMonsterA-C to Zombie, Ghast and Fright (A at Badguys0, B at BadGuys1, five C at GoodGuys0). Hostile, as Spawn makes them.
HORDE_WARRIOR, HORDE_LEADER, ZOMBIE, GHAST, FRIGHT = 9130, 9131, 9182, 9174, 9162
SPAWNS = {
    "Retribution": (("BadGuys0", HORDE_LEADER, 3), ("BadGuys0", HORDE_WARRIOR, 2),
                    ("BadGuys1", HORDE_LEADER, 5), ("BadGuys1", HORDE_WARRIOR, 2)),
    "Undead": (("BadGuys0", ZOMBIE, 1), ("BadGuys1", GHAST, 1), ("GoodGuys0", FRIGHT, 5)),
}
CINEMA_ID, CINEMA_EVENTS = "afterworld_guilt", 36000     # done event; its steps 36001..
HALL_ROW = "mm9:transition/afterworld/95"       # ExitTrigger0: NPC336.scr :Failure `trigger g_hobject trigger`


def greeting_lua() -> str:
    """NPC336.scr :DoRude (OnFoundPlayer, and SixFires.inc :FadeIn2): key 379, his dialogue and voice. The talk names
    its speaker (SKRAELOS_ACTOR, which extend declares) so that its close runs his exit (skraelosExit): opened by the
    cinematic, outside his click, it would otherwise end without it and Confession's Jarls would not appear."""
    return "MM9.giveKey(379); MM9.openRude(336, SKRAELOS_ACTOR); MM9.playSound(\"voices/npc/npc_336.wav\")"


GUILT_LINES = [
    "    if has(380) and not has(381) then   -- :Guilt: the cinematic " + CINEMA_ID + " (key 381, then his greeting)",
    f"        MM9Cinematic.start(\"{CINEMA_ID}\")",
    "        return",
    "    end",
]


def scenes() -> list:
    """SixFires.inc :Guilt (NPC336.scr :OnRude with key 380, not 381): screenfadeout 1, wait 1 :FadeIn (the cinematic
    starts here): letterbox, Camera9 On and Play: AfterWorldCam1.scr MoveToPos AfterMarker0 at 100 (Camera9's
    ScriptParams), its arrival sends Skraelos0 Done: NPC336.scr :OnDone (quest.wav, key 381, :End: screenfadeout 2,
    wait 2 :FadeIn2: letterbox false, Camera9 Off, screenfadein 1, OnFoundPlayer :DoRude). The camera looks along its
    DAT rotation (64 degrees down over the battlefield); fov MM9_CAMERA_FOV. The greeting opens as the party's view has
    faded in (MM9 opens it at the start of that fade)."""
    project = Path(__file__).resolve().parent
    objects = cutscenes.Objects.load("afterworld")
    frame = cutscenes.Frame(project)
    fov = cutscenes.MM9_CAMERA_FOV
    camera = objects.named("Camera9")["values"]
    marker, speed = str(camera["ScriptParams"]).split()
    eye, forward = frame.camera(objects, "Camera9")
    target, _ = frame.camera(objects, marker)
    _, arrival = cutscenes.move_to_pos(eye, target, frame.speed(float(speed)), 0.0)
    scene = cutscenes.Scene(CINEMA_ID, CINEMA_EVENTS, source="SixFires.inc :Guilt..:FadeIn2, AfterWorldCam1.scr")
    cinema = scene.cinema
    cinema.moving(arrival, [(0.0, eye, {"direction": forward, "fov": fov}),
                            (arrival, target, {"direction": forward, "fov": fov})], easing="linear",
                  note=f"Camera9 MoveToPos {marker} at {speed} (:FadeIn)")
    cinema.fixed(2.0, target, direction=forward, fov=fov, note="Camera9 at the marker (:End screenfadeout 2)")
    cinema.party(1.0, note=":FadeIn2 Camera9 Off, screenfadein 1")
    cinema.fade(0.0, "in", 1.0, note=":Guilt screenfadeout 1, :FadeIn screenfadein 1")
    scene.step(arrival, "done", "if not has(381) then MM9.giveKey(381) end",
               note="AfterWorldCam1.scr :OnArrive -> NPC336.scr :OnDone: key 381")
    cinema.sound(arrival, "sounds\\events\\quest.wav", note=":OnDone")
    cinema.fade(arrival, "out", 2.0, note=":End screenfadeout 2")
    cinema.fade(arrival + 2.0, "in", 1.0, note=":FadeIn2 screenfadein 1")
    scene.step(arrival + 3.0, "greeting", greeting_lua(), note=":FadeIn2 OnFoundPlayer :DoRude: key 379, RUDE 336")
    return [scene]



def populate(hooks, build) -> None:
    """The Six Fires' flames (module docstring), shown by sixFires() in the map Lua (outdoor_blv.py populate)."""
    from dungeon.objects import fire_decoration
    for k, name in enumerate(FIRES):
        o = build.source.by_name.get(name.lower())
        if o is None:
            continue
        decoration = fire_decoration(o["properties"])
        if decoration not in build.content.ids:
            print(f"WARNING: {name}: no decoration row {decoration} (props/mm9_outdoor_regions_claude/scripts/"
                  "converter_rows.py)")
            continue
        native = build.project.native(np.asarray(o["properties"]["Pos"], float))
        build.content.entity(f"fire_{name}", decoration, native, 0, primary=COG_FIRE + k)


def fire_lines(build) -> list[str]:
    """sixFires(): each placed fire burns once its stage's key is held."""
    placed = [(k, name, key) for k, (name, key) in enumerate(FIRES.items()) if name.lower() in build.source.by_name]
    return ["local function sixFires()   -- the Six Fires, by their stages' keys (SixFires.inc, NPC336.scr \"On\")"] + [
        f"    evt.SetSprite({COG_FIRE + k}, has({key}) and 1 or 0, \"0\")   -- {name}" for k, name, key in placed
    ] + ["end"]


def index_of(build, name: str) -> int:
    return build.source.by_name[name.lower()]["index"]


def hall_arrival() -> tuple:
    """ExitTrigger0's row in the review root's transitions table: the Hall of the Gods' StartPoint0 arrival."""
    import review_root
    path = review_root.mirror_path("worlds/mm9/data_tables/map_transitions.txt")
    lines = path.read_text(encoding="latin-1").split("\n")
    column = {name: k for k, name in enumerate(lines[0].rstrip("\r").split("\t"))}
    for line in lines[1:]:
        cells = line.rstrip("\r").split("\t")
        if cells[0] == HALL_ROW:
            return (int(float(cells[column["ArrivalX"]])), int(float(cells[column["ArrivalY"]])),
                    int(float(cells[column["ArrivalZ"]])), int(float(cells[column["FacingYawUnits"]])),
                    cells[column["DestinationMapFile"]])
    raise SystemExit(f"{HALL_ROW}: no transition row in {path}")


def native_point(build, name: str) -> list:
    return build.project.native(build.source.properties(name)["Pos"]).round().astype(int).tolist()


def spawn_lines(build, stage: str, indent: str) -> list[str]:
    """SixFires.inc's Spawn calls of a stage: each at its marker, on the floor under it (Spawn drops the creature)."""
    out = []
    for marker, row, count in SPAWNS[stage]:
        pos = build.source.properties(marker)["Pos"]
        floor = build.content.floor_at(pos[0], pos[2], pos[1] + 50)
        x, y, z = build.project.native([pos[0], pos[1] if floor is None else floor, pos[2]]).round().astype(int)
        out.append(f"{indent}evt.SummonMonstersById({{monster = {row}, x = {x}, y = {y}, z = {z + 1}, radius = 128, "
                   f"count = {count}}})   -- {marker}")
    return out


def extend(hooks, build, script) -> None:
    tag = "afterworld"
    npc = getattr(hooks, "npc_actor", {})
    skraelos = index_of(build, SKRAELOS)
    heroes = [(name, npc[name]) for name in HEROES if name in npc]
    forad = next((a["actor_index"] for a in build.content.report["actors"] if a["anchor"] == FORAD), None)
    hx, hy, hz, hyaw, hmap = hall_arrival()
    exit0, exit1 = native_point(build, "ExitTrigger0"), native_point(build, "ExitTrigger1")
    exit1_source = index_of(build, "ExitTrigger1")      # its transitions row: the engine skips it while disabled

    hero_list = ", ".join(str(actor) for _, actor in heroes)
    lines = [
        f"SKRAELOS_ACTOR = {npc[SKRAELOS]}   -- {SKRAELOS}: the speaker of the talks his scenes open (greeting_lua)",
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        f"local HEROES = {{{hero_list}}}   -- {', '.join(name for name, _ in heroes)}",
        "local function showHeroes(on)",
        "    set(\"HeroesShown\", on and 1 or 0)",
        "    for _, a in ipairs(HEROES) do show(a, on) end",
        "end",
        "local function allKeys(first, last) for k = first, last do if not has(k) then return false end end return true end",
        *fire_lines(build),
        "",
        "-- On load: the Six Fires; the heroes as SixFires.inc :Confession left them, Forad Darre while Retribution waits for his death,",

        "handlers.regionLoad = function()",
        "    sixFires()",
        "    showHeroes(var(\"HeroesShown\") == 1)",
        f"    set(\"Mm9ExitDisabled{exit1_source}\", has(390) and 0 or 1)   -- ExitTrigger1 (StartOn 0) until :Rebirth",
    ]
    if forad is not None:
        lines.append(f"    show({forad}, has(5021) and not has(387))   -- {FORAD}")
    lines += ["end", ""]

    lines += [
        "",
        "-- NPC336.scr :OnUse (a click on Skraelos, then his dialogue): Confession's six confessions (keys 501-506) give",
        "-- key 383; Absolution's five swords (items 563-567) are taken for key 389. 52 000 experience each.",
        f"handlers[{53000 + skraelos}] = function()   -- {SKRAELOS}",
        "    if has(382) and not has(383) and allKeys(501, 506) then",
        f"        reward(383, {balanced_experience(52000, 383)}, 0)   -- ConfessionFire On"
        f"{experience_note(52000, 383)}",
        "    end",
        "    if has(388) and not has(389) then",
        "        local swords = 0",
        f"        for item = 563, 567 do swords = swords + MM9.hasItem(item, \"{tag}:NPC336\") end",
        "        if swords == 5 then",
        f"            for item = 563, 567 do MM9.takeItem(item, \"{tag}:NPC336\") end",
        f"            reward(389, {balanced_experience(52000, 389, 'npc336.scr', 'OnUse')}, 0)   -- AbsolutionFire On"
        f"{experience_note(52000, 389, 'npc336.scr', 'OnUse')}",
        "        end",
        "    end",
        "    sixFires()",
        "    MM9.openRude(336)",
        "end",
        "-- NPC336.scr :Init (\"Afterworld\") -> OnFoundPlayer :DoRude: key 379, his dialogue and voice (each visit).",
        f"handlers[{56000 + skraelos}] = function()   -- {SKRAELOS}",
        "    MM9.giveKey(379)",
        "    MM9.openRude(336)",
        "    MM9.playSound(\"voices/npc/npc_336.wav\")",
        "end",
        "",
        "-- NPC336.scr :OnRude with SixFires.inc: the fire whose key the dialogue just gave (then the fires shown).",
        "local function skraelosExit()",
        "    if has(392) then   -- :Failure",
        "        for k = 379, 392 do MM9.takeKey(k) end",
        f"        evt.MoveToMap({hx}, {hy}, {hz}, {hyaw}, 0, 0, 0, 0, \"{hmap}\")   -- ExitTrigger0's row",
        "        return",
        "    end",
        *GUILT_LINES,
        "    if has(382) then showHeroes(not has(383)) end   -- :Confession",
        "    if has(384) and not has(491) then   -- :Suffering",
        "        if has(385) then",
        f"            MM9.giveKey(491); {experience_lua(52000, 491)}",
        "            evt.ForPlayer(Players.All); MM9.clearCondition(13)   -- SufferingFire On",
        "            quest()",
        "            set(\"Questioned\", 0)",
        "        elseif var(\"Questioned\") == 1 then",
        "            set(\"Questioned\", 0)   -- the Questioner's own exit: asked again on the next talk",
        "        else",
        "            set(\"Questioned\", 1)   -- :Questioner: SetCondition 13 (poisoned and diseased), DoRude 432",
        "            evt.ForPlayer(Players.All); SetValue(VarTag.PoisonedGreen, 0); SetValue(VarTag.DiseasedGreen, 0)",
        "            MM9.openRude(432)",
        "            return",
        "        end",
        "    end",
        "    if has(386) and not has(387) and not has(5021) then   -- :Retribution",
        "        MM9.giveKey(5021)",
    ]
    if forad is not None:
        lines.append(f"        show({forad}, true)   -- {FORAD} setflag visible")
    lines += spawn_lines(build, "Retribution", "        ")
    lines += [
        "    end",
        "    if has(388) and not has(492) then   -- :Absolution (RetributionFire On)",
        f"        reward(492, {balanced_experience(52000, 492, 'sixfires.inc', 'Absolution')}, 0)"
        f"{experience_note(52000, 492, 'sixfires.inc', 'Absolution')}",
    ]
    lines += spawn_lines(build, "Undead", "        ")
    lines += [
        "    end",
        "    if has(390) then   -- :Rebirth: ExitTrigger1 on; its undead come again at every exit, as MM9's",
        f"        set(\"Mm9ExitDisabled{exit1_source}\", 0)",
        *spawn_lines(build, "Undead", "        "),
        "    end",
        "end",
        f"handlers[{50000 + skraelos}] = function() skraelosExit(); sixFires() end   -- {SKRAELOS}",
        "",
        "-- PropTrigger.scr on ExitTrigger1 (\"Skraelos0 Reborn\", on touch) -> NPC336.scr :OnReborn: after :Rebirth (key",
        "-- 390) leaving by ExitTrigger1 (nearer it than ExitTrigger0) gives keys 391 and 102 and 52 000 experience.",
        "-- A slain Skraelos takes no Reborn (MM9.receives, scr_audit README \"Implicit engine semantics\").",
        f"handlers[{EV_LEAVE}] = function()",
        "    if not has(390) or has(391) then return end",
        "    local x, y = evt.GetPartyPosition()",
        f"    local d0 = (x - {exit0[0]}) ^ 2 + (y - {exit0[1]}) ^ 2",
        f"    local d1 = (x - {exit1[0]}) ^ 2 + (y - {exit1[1]}) ^ 2",
        "    if d1 > d0 then return end",
        f"    if not MM9.receives(\"afterworld\", \"{SKRAELOS}\", \"Reborn\", {npc.get(SKRAELOS, 'nil')}) then return end",
        f"    MM9.giveKey(391); MM9.giveKey(102); "
        f"MM9.giveExperience({balanced_experience(52000, 391, 'npc336.scr', 'OnReborn')}); "
        f"quest()   -- RebirthFire On{experience_note(52000, 391, 'npc336.scr', 'OnReborn')}",
        "end",
    ]
    registrations = [(53000 + skraelos, "Skraelos", None), (56000 + skraelos, "Skraelos", None),
                      (50000 + skraelos, "Skraelos", None)]
    if forad is not None:
        lines += [
            "-- TM_Hardrock.scr \"1 387\" (RetributionCounter, Forad Darre's DeathTriggerTarget \"OneDown\"): one death",
            "-- completes it: key 387 and the quest sound.",
            f"handlers[{EV_KILL}] = function(context)",
            f"    if context.actorIndex == {forad} and not has(387) then MM9.giveKey(387); quest(); sixFires() end",
            "end",
        ]
        script.hooks.append(f'RegisterMonsterKilledHook({EV_KILL}, "Forad Darre killed", handlers[{EV_KILL}])')
    lines.append("")
    script.add(lines, *registrations)
    script.hooks.append(f'RegisterMapOnLeaveEvent({EV_LEAVE}, "Reborn", handlers[{EV_LEAVE}])')
    # :Guilt's cutscene: its steps, done event and start function (mm9r_common/cutscenes.py), its yml beside the map
    cinematic_scenes = scenes()
    script.add(cutscenes.lua_block(cinematic_scenes).split("\n"))
    if build.project.install:
        print(f"cinematics installed: {cutscenes.install(build.project.stem, cinematic_scenes)} ({CINEMA_ID})")
