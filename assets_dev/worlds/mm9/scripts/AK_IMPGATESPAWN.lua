-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AK_IMPGATESPAWN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "flags.inc" }

-- AK_ImpGateSpawn.scr
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- AK_IMPGATESPAWN.scr:10
    ctx:command("wait", "0, .1, InitImpGateSpawn") -- AK_IMPGATESPAWN.scr:12
    do return ctx:exit(1) end -- AK_IMPGATESPAWN.scr:14
end

script.labels["InitImpGateSpawn"] = function(ctx)
    -- AK_IMPGATESPAWN.scr:17
    mm9.gosub(script, ctx, "BaseInit") -- AK_IMPGATESPAWN.scr:19
    ctx:command("getplayerhandle", "g_hTarget") -- AK_IMPGATESPAWN.scr:20
    mm9.gosub(script, ctx, "SetupTarget") -- AK_IMPGATESPAWN.scr:21
    mm9.gosub(script, ctx, "AggressiveStart") -- AK_IMPGATESPAWN.scr:22
    do return ctx:exit(1) end -- AK_IMPGATESPAWN.scr:24
end

return script
