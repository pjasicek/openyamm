-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SOURCECREATURE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "baseMelee.inc" }

-- SourceCreature.scr
-- by SJR
-- 09-21-01
-- Purpose:Used in conjunction with SourceMan.scr
-- to continuously spawn out of sight w/ a limit
script.labels["Main"] = function(ctx)
    -- SOURCECREATURE.scr:16
    ctx:command("wait", "0, .1, InitSourceCreature") -- SOURCECREATURE.scr:18
    do return ctx:exit("TRUE") end -- SOURCECREATURE.scr:19
end

script.labels["InitSourceCreature"] = function(ctx)
    -- SOURCECREATURE.scr:22
    ctx:command("getobjecthandle", "SourceManager, hSourceManager") -- SOURCECREATURE.scr:24
    ctx:command("getobjecthandle", "RallyPoint, hGoal") -- SOURCECREATURE.scr:25
    ctx:command("ondeath", "NotifyManager") -- SOURCECREATURE.scr:27
    -- init wander,door,evade,melee
    mm9.gosub(script, ctx, "BaseInit") -- SOURCECREATURE.scr:29
    ctx:command("runto", "hGoal, 50, BaseWanderStart") -- SOURCECREATURE.scr:31
    do return ctx:exit("TRUE") end -- SOURCECREATURE.scr:33
end

script.labels["NotifyManager"] = function(ctx)
    -- SOURCECREATURE.scr:36
    ctx:trigger("hSourceManager", "ReSpawn") -- SOURCECREATURE.scr:38
    do return ctx:exit("TRUE") end -- SOURCECREATURE.scr:39
end

return script
