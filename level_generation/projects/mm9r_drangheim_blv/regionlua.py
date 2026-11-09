"""
Drangheim (the region) map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/
SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests and ForadWorld.scr
(devdocs/mm9_rework/REGIONS_FINISH.md step 2). RUDE exits are event 50000 + the DAT object index (game/mm9/
Mm9RudeDialogue.h).

- The Yobboe chieftain's promotion quest (key 128; NPC91-93.scr): Hring's plough (item 371), Ragnheid's herbs (372)
  and Tyock's doll (370) lie in the region (Plow.scr, Herbs.scr, Dolly.scr) while the quest runs: world items
  (../mm9r_common/dungeon/pickups.py), shown with key 128, picked up as any ground item, giving keys 130/131/132. Their owners reward it on the dialogue's exit when the quest's row says so
  (keys 133/134/135): the item taken, 2 000 experience, 500 gold, keys 200/198/199.
- The great book (RealBook.scr, on Capstone0): with the fake book (item 244) a click gives items 347 and 560, keys 283
  and 290, and the book goes; it stays gone once key 283 or 284 is held.
- RotatingDoor0 (doorlock.scr "244"): it opens only while the party carries the fake book.

- YobboeMan (TM_HardRock.scr "6 129 6000"): a kill counter, not destructibles. The seven bandits whose
  DeathTriggerTarget is YobboeMan ("OneDown": Bandit0/1, Burgler0-4) count their deaths; the sixth gives key 129
  ("killed all the yobboes": Keith Bloodaxe's Crusader promotion, NPC89.scr) and 6 000 experience, once.

- Ivsar Forktooth outside the prison (NPC90.scr "Drangheim Main"/"Drangheim Well", PrisonerHuman2MaleA0/A1): both
  copies stand while key 17 (rescued in the prison) is held and 242 is not (:Init). The first that perceives the party
  (OnFoundPlayer, event 56000 + index) or is clicked (53000 + index) runs :OnUse: key 194, the other copy goes, his
  voice and RUDE 90, whose "What is it, General?" (requires 194) gives 242. :OnRude (the exit, 50000 + index): with
  242 key 194 is taken and both copies go (Sturmford's copy appears with 242). MM9's small SetPos at :OnUse and its
  re-opened dialogue on an early exit are left out: 194 stays until 242, so a later click offers the row again.

Not here: his walk to Sturmford (FollowPlayer.inc: the Sturmford copy stands in, as in MM9 once 242 is held) and the
shopkeeper's voice line (Shopkeeper.scr OnUse).
"""

from __future__ import annotations

from quest_xp import balanced_experience

EV_PROP = 330           # a scripted prop's click: EV_PROP + k
EV_KILL = 601           # monster killed hook: YobboeMan's counter (TM_HardRock.scr :OneDown)
HARDROCK = ("YobboeMan", 6, 129, 6000)   # TM_HardRock.scr's object and parameters: deaths, key, experience
COG_PROP = 400          # its SetSprite key (hide or show): COG_PROP + k
# DAT name -> (script, shown while)
PROPS = {
    "Capstone0": ("realbook.scr", "not has(283) and not has(284)"),
}
KEYED_DOORS = {"RotatingDoor0": 244}
IVSAR = ("PrisonerHuman2MaleA0", "PrisonerHuman2MaleA1")   # NPC90.scr "Drangheim Main", "Drangheim Well"
IVSAR_RUDE = 90


def prop_events(build) -> tuple[dict, dict]:
    events = {name: EV_PROP + k for k, name in enumerate(PROPS)}
    cogs = {name: COG_PROP + k for k, name in enumerate(PROPS)}
    return events, cogs


def rude_exit(build, name: str) -> int:
    return 50000 + build.source.by_name[name.lower()]["index"]


def extend(hooks, build, script) -> None:
    events, cogs = prop_events(build)
    tag = "drangheim"
    ivsar_lines, ivsar_load, ivsar_registrations = ivsar(hooks, build)
    lines = ivsar_lines + [
        "-- The great book (RealBook.scr): shown or gone by its keys on every load; a click takes it.",
        "handlers.regionLoad = function()",
    ]
    for name, (scr, shown) in PROPS.items():
        lines.append(f"    evt.SetSprite({cogs[name]}, ({shown}) and 1 or 0, \"0\")   -- {name} ({scr})")
    lines += ivsar_load
    lines += ["end", ""]
    lines += [
        f"handlers[{events['Capstone0']}] = function()   -- Capstone0 (realbook.scr)",
        "    if has(283) or MM9.hasItem(244, \"drangheim:RealBook\") ~= 1 then return end",
        f"    MM9.giveItem(347, \"{tag}:RealBook\"); MM9.giveItem(560, \"{tag}:RealBook\")",
        "    MM9.giveKey(283); MM9.giveKey(290)",
        f"    evt.SetSprite({cogs['Capstone0']}, 0, \"0\")",
        "end",
        "",
        "-- NPC91-93.scr: the owners reward their item on the dialogue's exit (keys 133-135 from their RUDE rows).",
    ]
    for name, need, done, item, who in (("RUDEProp6", 133, 200, 371, "Hring, NPC91.scr"),
                                         ("RUDEProp7", 134, 198, 372, "Ragnheid, NPC92.scr"),
                                         ("RUDEProp8", 135, 199, 370, "Tyock, NPC93.scr")):
        lines += [
            f"handlers[{rude_exit(build, name)}] = function()   -- {who}",
            f"    if has({need}) and not has({done}) then MM9.takeItem({item}, \"{tag}:{name}\"); "
            f"reward({done}, {balanced_experience(2000, done)}, 500) end",
            "end",
        ]
    counter, deaths, key, experience = HARDROCK
    senders = sorted(o["name"] for o in build.source.objects
                     if str(o["properties"].get("DeathTriggerTarget") or "") == counter
                     and str(o["properties"].get("DeathTriggerMessage") or "").lower() == "onedown")
    placed = {a["anchor"]: a["actor_index"] for a in build.content.report["actors"]}
    indices = [placed[name] for name in senders if name in placed]
    if indices:
        lines += [
            f"-- {counter} (TM_HardRock.scr \"{deaths} {key} {experience}\"): the bandits' deaths send \"OneDown\";",
            f"-- the {deaths}th gives key {key} and {experience} experience, once ({', '.join(senders)}).",
            f"local YOBBOES = {{{', '.join(f'[{i}] = true' for i in indices)}}}",
            f"handlers[{EV_KILL}] = function(context)",
            "    if not YOBBOES[context.actorIndex] or has(" + str(key) + ") then return end",
            "    set(\"YobboesDown\", var(\"YobboesDown\") + 1)",
            f"    if var(\"YobboesDown\") >= {deaths} then "
            f"reward({key}, {balanced_experience(experience, key)}, 0) end",
            "end",
        ]
        script.hooks.append(f'RegisterMonsterKilledHook({EV_KILL}, "Yobboes down", handlers[{EV_KILL}])')
    lines.append("")
    registrations = [(events[name], name, "Prop") for name in PROPS]
    registrations += [(rude_exit(build, name), name, None) for name in ("RUDEProp6", "RUDEProp7", "RUDEProp8")]
    registrations += ivsar_registrations
    script.add(lines, *registrations)


def ivsar(hooks, build) -> tuple[list, list, list]:
    """NPC90.scr's Drangheim copies (module docstring): the handlers, regionLoad's lines and the registrations."""
    actors = getattr(hooks, "npc_actor", {})
    placed = [name for name in IVSAR if name in actors]
    if not placed:
        return [], [], []
    shown = "has(17) and not has(242)"
    load = [f"    ivsarShow({shown})   -- Ivsar Forktooth (NPC90.scr :Init)"]
    lines = [
        "-- NPC90.scr (Ivsar Forktooth, \"Drangheim Main\"/\"Drangheim Well\"): shown with key 17 until 242.",
        "local IVSAR = {" + ", ".join(f"[{build.source.by_name[name.lower()]['index']}] = {actors[name]}"
                                     for name in placed) + "}",
        "local function ivsarShow(on)",
        "    for _, a in pairs(IVSAR) do evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "end",
        "-- :OnUse (\"drangheim\"): key 194, the other copy goes, his voice and RUDE 90 (row \"What is it, General?\").",
        "local function ivsarUse(source)",
        "    if not has(17) or has(242) then return end",
        "    MM9.giveKey(194)",
        "    for index, a in pairs(IVSAR) do",
        "        if index ~= source then evt.SetMonsterBit(a, ActorAttribute.Invisible, 1) end",
        "    end",
        "    MM9.playSound(\"voices/npc/npc_090.wav\")",
        f"    MM9.openRude({IVSAR_RUDE})",
        "end",
        "-- :OnRude (the exit): with 242 he is on his way to Sturmford: key 194 taken, both copies gone.",
        "local function ivsarExit()",
        "    if has(242) then MM9.takeKey(194); ivsarShow(false) end",
        "end",
    ]
    registrations = []
    for name in placed:
        index = build.source.by_name[name.lower()]["index"]
        lines += [
            f"handlers[{53000 + index}] = function() ivsarUse({index}) end   -- {name}: click",
            f"handlers[{56000 + index}] = function() ivsarUse({index}) end   -- {name}: OnFoundPlayer",
            f"handlers[{50000 + index}] = ivsarExit   -- {name}: RUDE exit",
        ]
        registrations += [(53000 + index, "Ivsar Forktooth", None), (56000 + index, "Ivsar Forktooth", None),
                          (50000 + index, "Ivsar Forktooth", None)]
    lines.append("")
    return lines, load, registrations
