"""
Lindisfarne (the region) map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/
SCRIPTS/SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests and
ForadWorld.scr (devdocs/mm9_rework/REGIONS_FINISH.md step 2; the behaviour spec of every script is work/scr_spec.md).

- The monastery's healer for hire (Retainer.scr "\\voices\\npc\\NPC_308.wav 462", RUDE 308): hidden while hired (key
  462), checked on every load as MM9's :Init does; hiring and dismissing work through RUDE.
- Books0 (Book.scr): a click turns its pages (MM9 plays the open, turn and close animations; the book has no text).
- The Magreebs (MAGREEB.scr, the Magreeb and Armored Magreeb rows' script; the 16 placed): the first
  that finds the party as its target while the Scholar quest waits for its Magreeb (key 201 without 202) gives key
  202 with the quest sound (:OnFoundTarget): MM9's second route to the Scholar promotion (Thjorgard's Magreeb is the
  other). Here a one-second poll: a living Magreeb that sees the party (evt.ActorSeesParty) within its SightDistance.

Not here: Monk0 (DoRude.scr "305": a wandering monk whose click opens RUDE 305) is not placed, since its DAT object
has no `DoRude 1` (shared `npcs()`, work/scr_spec.md); the shopkeepers' and the healer's voice lines on a click
(Shopkeeper.scr, Retainer.scr OnUse; the dialogues and shops work); the pickaxes (PropAnim.scr "onside": a pose,
placed as static props) and StatStone0 (not placed).
"""

from __future__ import annotations

EV_PROP = 330           # a scripted prop's click: EV_PROP + k
T_MAGREEB = 340         # timer: the Magreebs' sighting poll (MAGREEB.scr :OnFoundTarget)
SCALE = 2.56            # MM9 units -> engine units (tools/mm9_import_discovery/mm9_units.py)
MAGREEB_ROWS = (9277, 9278)    # MM9 Magreeb, Armored Magreeb: MONSTERS.txt's script MAGREEB.scr
PROPS = {"Books0": "book.scr"}
RETAINERS = {"CommonerHuman2MaleA16": 462}     # DAT name -> the key MM9 holds while it is hired (Retainer.scr p1)


def prop_events(build) -> tuple[dict, dict]:
    return {name: EV_PROP + k for k, name in enumerate(PROPS)}, {}


def extend(hooks, build, script) -> None:
    events, _ = prop_events(build)
    lines = [
        f"handlers[{events['Books0']}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0) end"
        "   -- Books0 (Book.scr: pages turn, no text)",
        "",
    ]
    registrations = [(events["Books0"], "Books0", "Book")]
    shown = [(name, hooks.npc_actor[name], key) for name, key in RETAINERS.items() if name in hooks.npc_actor]
    if shown:
        lines += ["-- Retainer.scr :Init: a retainer is hidden while hired (its key) and back once dismissed.",
                  "handlers.regionLoad = function()"]
        lines += [f"    evt.SetMonsterBit({actor}, ActorAttribute.Invisible, has({key}) and 1 or 0)"
                  f"   -- {name}, key {key}" for name, actor, key in shown]
        lines += ["end", ""]
    lines += magreeb_lines(build)
    script.add(lines, *registrations)
    if any(record["monster_id"] in MAGREEB_ROWS for record in build.content.report["actors"]):
        script.hooks.append(f'RegisterMapTimerEvent({T_MAGREEB}, seconds(1), handlers[{T_MAGREEB}], "Magreebs", "", '
                            'seconds(1))')


def magreeb_lines(build) -> list:
    """MAGREEB.scr :OnFoundTarget (module docstring): {actor index, sight in engine units} of the placed Magreebs and
    the poll that gives key 202."""
    found = []
    for record in build.content.report["actors"]:
        if record["monster_id"] not in MAGREEB_ROWS:
            continue
        sight = float(build.source.by_name[record["anchor"].lower()]["properties"].get("SightDistance") or 600.0)
        found.append((record["actor_index"], int(round(sight * SCALE)), record["anchor"]))
    if not found:
        return []
    return [
        "-- MAGREEB.scr :OnFoundTarget: a Magreeb that finds the party during the Scholar quest (201, not 202) gives",
        f"-- key 202 and the quest sound ({', '.join(name for _, _, name in found)}).",
        "local MAGREEBS = {" + ", ".join(f"{{{index}, {sight}}}" for index, sight, _ in found) + "}",
        f"handlers[{T_MAGREEB}] = function()",
        "    if not has(201) or has(202) then return end",
        "    for _, m in ipairs(MAGREEBS) do",
        "        if evt.ActorSeesParty(m[1], m[2]) then",
        "            MM9.giveKey(202); MM9.playSound(\"sounds/events/quest.wav\")",
        "            return",
        "        end",
        "    end",
        "end",
        "",
    ]
