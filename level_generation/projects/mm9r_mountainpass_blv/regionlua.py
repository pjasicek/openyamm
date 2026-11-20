"""
Mountain Pass map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/SCRIPTS;
behaviour spec: work/scr_spec.md). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests
and ForadWorld.scr (devdocs/mm9_rework/REGIONS_FINISH.md step 2).

- Crossing the pass (MountainPass.scr on the ScriptObject "Mountain"): Trigger0 near the Thjorgard end and Trigger1
  near the Thronheim end each send "Use" once (then switch themselves off); the second one counted rewards the
  crossing: key 80 and 14 000 experience when the party holds key 79 without 80, else key 176 and 14 000 experience
  once. Here the two volumes are polled twice a second (their DAT boxes, Pos +- Dims) along the party's path since the
  last poll: a party running with Fleet Foot covers more than a volume's depth (about 730) in half a second, and a
  point test let it run through Trigger1 unseen (the user's 2026-11-11 playthrough). The pass also counts as found once
  every monster in it is dead, as "Find and clear the Mountain Pass" asks: a party that cleared the pass without
  stepping on both volumes (the mountainsides go round them) gets the award at the next poll, on a later visit too.

- The lookout imp (MP_Imp.scr on Imply0): a second after the load it walks to ImpMarker1 and watches; on seeing the
  party it winces (wince1: its Hit clip), runs to ImpMarker2 by the imps' camp and calls them (help): the camp's
  imps and the lookout take the party.
"""

from __future__ import annotations

import numpy as np
from dungeon import lua
from quest_xp import balanced_experience, experience_note

T_POLL = 600            # the trigger volumes' poll
T_IMP, EV_IMP_HELP = 601, 602   # MP_Imp.scr: the lookout's start and watch (a timer), its arrival at ImpMarker2
IMP = "Imply0"
IMP_SIGHT = 1536        # native: its SightDistance (600 LT), the range it sees the party at
IMP_HELP_RADIUS = 1024  # native: the imps by ImpMarker2 that its help call reaches (the camp, 400 LT)
IMP_RUN_SECONDS = 20    # a run to ImpMarker2 not done by then calls the camp from where the imp is
IMP_CALL_DISTANCE = 512 # native: it calls once this near ImpMarker2 (the camp's imps stand round the marker)
TRIGGERS = ("Trigger0", "Trigger1")
MARGIN = 37             # native units around a volume: the party's radius, as the dungeons' trigger polls
MAX_STEP = 2048         # native: farther between two polls than any run (Fleet Foot about 750) is a jump (a load)


def box(build, name: str) -> tuple[list, list]:
    """A DAT Trigger's volume (Pos +- Dims, LithTech) as a native box (low, high)."""
    p = build.source.properties(name)
    centre, dims = np.array(p["Pos"], float), np.array(p.get("Dims") or [0, 0, 0], float)
    low, high = build.project.native(centre - dims), build.project.native(centre + dims)
    return (np.minimum(low, high).round().astype(int).tolist(), np.maximum(low, high).round().astype(int).tolist())


def point(p) -> str:
    return "{" + ", ".join(str(v) for v in p) + "}"


def extend(hooks, build, script) -> None:
    boxes = ", ".join(f"{{name = \"{name}\", low = {point(low)}, high = {point(high)}}}"
                      for name, (low, high) in ((name, box(build, name)) for name in TRIGGERS))
    lines = [
        "-- MountainPass.scr :OnStep (Trigger0, Trigger1 send \"Use\" once each) and :OnAward on the second.",
        f"local PASS_TRIGGERS = {{{boxes}}}",
        "-- A volume grown by the party's radius (its feet may stand 170 below it), and whether the party's path since the",
        "-- last poll (a straight segment) passes through it.",
        "local function passBounds(b)",
        f"    return {{b.low[1] - {MARGIN}, b.low[2] - {MARGIN}, b.low[3] - 170}}, "
        f"{{b.high[1] + {MARGIN}, b.high[2] + {MARGIN}, b.high[3] + {MARGIN}}}",
        "end",
        "local function crossesPassBox(b, from, to)",
        "    local low, high = passBounds(b)",
        "    local t0, t1 = 0, 1",
        "    for k = 1, 3 do",
        "        local d = to[k] - from[k]",
        "        if d == 0 then",
        "            if from[k] < low[k] or from[k] > high[k] then return false end",
        "        else",
        "            local ta, tb = (low[k] - from[k]) / d, (high[k] - from[k]) / d",
        "            if ta > tb then ta, tb = tb, ta end",
        "            if ta > t0 then t0 = ta end",
        "            if tb < t1 then t1 = tb end",
        "            if t0 > t1 then return false end",
        "        end",
        "    end",
        "    return true",
        "end",
        "local function passAward()",
        "    if has(80) or has(176) then return end   -- once (MM9 paid key 176's branch again after key 80)",
        f"    local xp = {balanced_experience(14000, 80, 'mountainpass.scr', 'OnAward')}"
        f"{experience_note(14000, 80, 'mountainpass.scr', 'OnAward')}",
        "    if has(79) then reward(80, xp, 0) else reward(176, xp, 0) end",
        "end",
        "local lastPartyPos = nil   -- runtime: the party's position at the previous poll (none after a load)",
        f"handlers[{T_POLL}] = function()",
        "    if has(80) or has(176) then return end",
        "    local x, y, z = evt.GetPartyPosition()",
        "    local here = {x, y, z}",
        "    local from = lastPartyPos or here",
        f"    if (x - from[1]) ^ 2 + (y - from[2]) ^ 2 > {MAX_STEP} ^ 2 then from = here end   -- a jump, not a run",
        "    lastPartyPos = here",
        "    for _, b in ipairs(PASS_TRIGGERS) do",
        "        if var(\"Stepped\" .. b.name) == 0 and crossesPassBox(b, from, here) then",
        "            set(\"Stepped\" .. b.name, 1)   -- the trigger turns itself off",
        "            set(\"PassSteps\", var(\"PassSteps\") + 1)",
        "            if var(\"PassSteps\") == 2 then passAward() end",
        "        end",
        "    end",
        "    -- cleared: every monster in the pass is dead",
        "    if evt.CheckMonstersKilled(ActorKillCheck.Hostile, 0, 0, false) then passAward() end",
        "end",
        "",
    ]
    script.add(lines)
    script.hooks.append(f'RegisterMapTimerEvent({T_POLL}, seconds(0.5), handlers[{T_POLL}], "Mountain Pass triggers", '
                        f'"", seconds(0.5))')
    imp_lines(build, script)


def marker(build, name: str) -> list:
    """A DAT Marker's native point, on the ground (MM9 markers float a little over it; the walk takes x and y)."""
    p = build.source.properties(name)["Pos"]
    return build.project.native(p).round().astype(int).tolist()


def imp_lines(build, script) -> None:
    """MP_Imp.scr (Imply0): :Main waits a second, :OnStart walks it to ImpMarker1 (WalkTo 8) with OnFoundTarget armed;
    :TargetFound plays wince1 and runs it to ImpMarker2 (RunTo 32); :StartAttack calls `help` on its target and
    fights (BaseInit)."""
    actors = {record["anchor"]: record["actor_index"] for record in build.content.report["actors"]}
    if IMP not in actors:
        return
    imp = actors[IMP]
    first, second = marker(build, "ImpMarker1"), marker(build, "ImpMarker2")
    monster = next(r["monster_id"] for r in build.content.report["actors"] if r["actor_index"] == imp)
    wince = round(lua.model_clip_seconds(monster)["hit"], 2)          # wince1 is the HD body's Hit
    helpers = []
    for record in build.content.report["actors"]:
        o = build.source.by_name.get(record["anchor"].lower())
        if record["anchor"] == IMP or o is None or record.get("friendly"):
            continue
        at = build.project.native(o["properties"]["Pos"])
        if np.hypot(at[0] - second[0], at[1] - second[1]) <= IMP_HELP_RADIUS:
            helpers.append(record["actor_index"])
    lines = [
        "-- MP_Imp.scr (Imply0, the lookout): :Main waits 1 s, :OnStart walks it to ImpMarker1 and arms OnFoundTarget;",
        "-- :TargetFound (it sees the party) plays wince1 (its Hit clip) and runs it to ImpMarker2, the imps' camp;",
        "-- :StartAttack: help (the camp's imps take the party) and it fights (BaseInit). Map var ImpAlarm: it has seen",
        "-- the party (afterwards it is an ordinary imp), 2 it called; walks are not saved: a load during its wince or",
        "-- run calls the camp at once.",
        f"local IMP = {imp}",
        f"local IMP_MARKER1, IMP_MARKER2 = {point(first)}, {point(second)}",
        f"local IMP_CAMP = {{{', '.join(map(str, helpers))}}}   -- within {IMP_HELP_RADIUS} of ImpMarker2",
        "local impPhase, impRun = 0, 0   -- runtime: 0 before :OnStart, 1 watching, 2 wincing (held), 3 running (ticks)",
        "local function impHelp()   -- :StartAttack",
        "    set(\"ImpAlarm\", 2)",
        "    if not MM9.actorAlive(IMP) then return end",
        "    evt.SetActorImmobile(IMP, false)",
        "    for _, a in ipairs(IMP_CAMP) do if MM9.actorAlive(a) then evt.SetActorTarget(a, \"party\") end end",
        "    evt.SetActorTarget(IMP, \"party\")",
        "end",
        f"handlers[{T_IMP}] = function()",
        f"    evt.StopTimer({T_IMP})",
        "    if var(\"ImpAlarm\") == 2 or not MM9.actorAlive(IMP) then return end",
        "    if var(\"ImpAlarm\") == 1 then",
        "        if impPhase == 2 then   -- the wince is over: RunTo ImpMarker2",
        "            impPhase, impRun = 3, 0",
        "            evt.SetActorImmobile(IMP, false)",
        f"            evt.MoveActorTo(IMP, IMP_MARKER2[1], IMP_MARKER2[2], IMP_MARKER2[3], {EV_IMP_HELP}, true)",
        "        elseif impPhase == 3 then   -- running: by the camp (its imps crowd the marker), or out of time",
        "            impRun = impRun + 1",
        "            local x, y = evt.GetMapActorPosition(IMP)",
        f"            if impRun >= {IMP_RUN_SECONDS * 2} or (x ~= nil and (x - IMP_MARKER2[1]) ^ 2 + (y - IMP_MARKER2[2]) ^ 2 "
        f"<= {IMP_CALL_DISTANCE} ^ 2) then",
        "                evt.StopActorMove(IMP)",
        "                impHelp()",
        "                return",
        "            end",
        "        end",
        f"        evt.StartTimer({T_IMP}, seconds(0.5))",
        "        return",
        "    end",
        "    if impPhase == 0 then   -- :OnStart",
        "        impPhase = 1",
        "        evt.MoveActorTo(IMP, IMP_MARKER1[1], IMP_MARKER1[2], IMP_MARKER1[3])",
        f"    elseif evt.ActorSeesParty(IMP, {IMP_SIGHT}) then   -- :TargetFound",
        "        set(\"ImpAlarm\", 1)",
        "        impPhase = 2",
        "        evt.StopActorMove(IMP)",
        "        evt.SetActorImmobile(IMP, true)",
        "        evt.PlayActorClip(IMP, \"hit\", false)",
        f"        evt.StartTimer({T_IMP}, seconds({wince}))",
        "        return",
        "    end",
        f"    evt.StartTimer({T_IMP}, seconds(0.5))",
        "end",
        f"handlers[{EV_IMP_HELP}] = function() if var(\"ImpAlarm\") == 1 then impHelp() end end",
        "handlers.regionLoad = function()",
        "    if var(\"ImpAlarm\") == 1 then impHelp() end",
        "end",
        "",
    ]
    script.add(lines, (EV_IMP_HELP, "Lookout imp", None))
    script.hooks.append(f'RegisterMapTimerEvent({T_IMP}, seconds(1), handlers[{T_IMP}], "Lookout imp", "", seconds(1))')
