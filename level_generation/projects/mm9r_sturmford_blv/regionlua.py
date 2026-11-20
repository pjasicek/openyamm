"""
Sturmford (the region) map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/
SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests and ForadWorld.scr
(devdocs/mm9_rework/REGIONS_FINISH.md step 2; the behaviour spec of every script is work/scr_spec.md).

- Hatch1 and Hatch2 (DoorLock.scr "596"), Anskram Keep's tower hatches: they open only while the party carries
  item 596 (the shared keyed doors).
- Anskram Keep's defences (ak_disable.scr on "defense"): once they are down (key 47, or 372 when done before Jarl
  Sigmund's quest), the drawbridge, the portcullis and its chain door stand open on every load (:Init -> :Setup).

- Earning it (ak_disable.scr :OnDraw, :ONPortcullis, :Award): the drawbridge is barred by its two chains
  (DestructableBrush0/1, destructibles: BARRED_DOORS); breaking both opens it and destroys Drawbridgechain
  (DestructOn.scr); raising the portcullis counts too. Both done: key 47 with Jarl Sigmund's quest (key 44), else 372,
  10 000 experience and the quest sound, once.

- The Portcullislever (a Switch): its click (overrides.yml `drives`) toggles the Portcullis and DoorChain4, which take
  no click of their own (PushOpen 0); the drawbridge, once down, stays down (outdoor_blv.py: a PushOpen 0 barred door).

Not here: the shopkeeper's voice line (NPCShopkeeper.scr OnUse; his dialogue works) and StatStone0 (not placed).
"""

from __future__ import annotations

from quest_xp import balanced_experience

KEYED_DOORS = {"Hatch1": 596, "Hatch2": 596}
# ak_disable.scr :Setup opens the drawbridge and (as "Portaclis", a misspelt name that finds nothing in MM9) the
# portcullis; its comment says "opens portcullis", so the portcullis opens here, with its chain door (the lever's pair)
DEFENCE_DOORS = ("drawbridge", "Portcullis", "DoorChain4", "Portcullislever")
CHAINS = ("DestructableBrush0", "DestructableBrush1")
BARRED_DOORS = {"drawbridge": list(CHAINS)}


def extend(hooks, build, script) -> None:
    doors = [m["door_id"] for group in DEFENCE_DOORS for m in build.movers if m["group"] == group]
    if not doors:
        return
    calls = " ".join(f"evt.SetDoorState({d}, DoorAction.Open)" for d in doors)
    index = {name: build.source.by_name[name.lower()]["index"] for name in CHAINS + ("Drawbridgechain", "defense")}
    defense = index["defense"]
    destroy = " ".join(f"evt.DestroyDestructible({index[name]})" for name in CHAINS + ("Drawbridgechain",))
    lines = [
        "-- ak_disable.scr :Init (\"defense\"): Anskram Keep's defences are down (key 47, or 372 when done before the",
        "-- quest): the drawbridge, the portcullis and its chain door stand open, the chains gone (:Setup).",
        "handlers.regionLoad = function()",
        f"    if has(47) or has(372) then {calls} {destroy} end",
        "end",
        "",
        "-- ak_disable.scr :Award, once both the drawbridge (its chains broken) and the portcullis are down.",
        "local function defencesAward()",
        f"    if MM9.scrValue({defense}, \"bDrawbridge\") == 0 or MM9.scrValue({defense}, \"bPortcullis\") == 0 then "
        "return end",
        "    if has(47) or has(372) then return end",
        f"    MM9.giveKey(has(44) and 47 or 372); MM9.giveExperience({balanced_experience(10000, 47)}); quest()",
        "end",
        "-- :OnDraw: both chains broken, the drawbridge falls and Drawbridgechain goes (DestructOn.scr)",
        "handlers.barredOpened = function(group)",
        "    if group ~= \"drawbridge\" then return end",
        f"    evt.DestroyDestructible({index['Drawbridgechain']})",
        f"    MM9.setScrValue({defense}, \"bDrawbridge\", 1)",
        "    defencesAward()",
        "end",
    ]
    # :ONPortcullis: the portcullis rising (the Portcullislever's shared click toggles it) counts once
    portcullis = sorted({m["event"] for m in build.movers if "Portcullis" in (m["group"], *m.get("drives", []))
                         and m["event"]})
    for event in portcullis:
        lines += [f"local portcullisClick{event} = handlers[{event}]",
                  f"handlers[{event}] = function()",
                  f"    portcullisClick{event}()",
                  f"    MM9.setScrValue({defense}, \"bPortcullis\", 1)",
                  "    defencesAward()",
                  "end"]
    lines.append("")
    script.add(lines)
