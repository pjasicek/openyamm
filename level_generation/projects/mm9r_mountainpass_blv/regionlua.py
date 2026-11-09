"""
Mountain Pass map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/SCRIPTS;
behaviour spec: work/scr_spec.md). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests
and ForadWorld.scr (devdocs/mm9_rework/REGIONS_FINISH.md step 2).

- Crossing the pass (MountainPass.scr on the ScriptObject "Mountain"): Trigger0 near the Thjorgard end and Trigger1
  near the Thronheim end each send "Use" once (then switch themselves off); the second one counted rewards the
  crossing: key 80 and 14 000 experience when the party holds key 79 without 80, else key 176 and 14 000 experience
  once. Here the two volumes are polled twice a second (their DAT boxes, Pos +- Dims).

Not here: the imp that walks to ImpMarker1, winces on seeing the party and runs to ImpMarker2 to call its friends
(MP_Imp.scr on Imply0): scripted monster movement, the monster AI's (work/scr_spec.md).
"""

from __future__ import annotations

import numpy as np
from quest_xp import balanced_experience, experience_note

T_POLL = 600            # the trigger volumes' poll
TRIGGERS = ("Trigger0", "Trigger1")
MARGIN = 37             # native units around a volume: the party's radius, as the dungeons' trigger polls


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
        "local function inPassBox(b, x, y, z)",
        f"    return x >= b.low[1] - {MARGIN} and x <= b.high[1] + {MARGIN} and y >= b.low[2] - {MARGIN} "
        f"and y <= b.high[2] + {MARGIN}",
        f"        and z + 170 >= b.low[3] and z <= b.high[3] + {MARGIN}",
        "end",
        "local function passAward()",
        "    if has(80) or has(176) then return end   -- once (MM9 paid key 176's branch again after key 80)",
        f"    local xp = {balanced_experience(14000, 80, 'mountainpass.scr', 'OnAward')}"
        f"{experience_note(14000, 80, 'mountainpass.scr', 'OnAward')}",
        "    if has(79) then reward(80, xp, 0) else reward(176, xp, 0) end",
        "end",
        f"handlers[{T_POLL}] = function()",
        "    local x, y, z = evt.GetPartyPosition()",
        "    for _, b in ipairs(PASS_TRIGGERS) do",
        "        if var(\"Stepped\" .. b.name) == 0 and inPassBox(b, x, y, z) then",
        "            set(\"Stepped\" .. b.name, 1)   -- the trigger turns itself off",
        "            set(\"PassSteps\", var(\"PassSteps\") + 1)",
        "            if var(\"PassSteps\") == 2 then passAward() end",
        "        end",
        "    end",
        "end",
        "",
    ]
    script.add(lines)
    script.hooks.append(f'RegisterMapTimerEvent({T_POLL}, seconds(0.5), handlers[{T_POLL}], "Mountain Pass triggers", '
                        f'"", seconds(0.5))')
