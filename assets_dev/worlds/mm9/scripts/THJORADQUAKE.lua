-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THJORADQUAKE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }

-- ThjoradQuake.scr
-- by SJR
-- Purpose:quakes
script.labels["Main"] = function(ctx)
    -- THJORADQUAKE.scr:17
    ctx:command("getmyhandle", "hMe") -- THJORADQUAKE.scr:19
    ctx:setPropNumber("InnerRadius", 0) -- THJORADQUAKE.scr:21
    ctx:setPropNumber("OuterRadius", 1000) -- THJORADQUAKE.scr:22
    ctx:setPropNumber("InnerDamage", 0) -- THJORADQUAKE.scr:23
    ctx:setPropNumber("DecayRate", 1) -- THJORADQUAKE.scr:24
    ctx:setPropNumber("QuakeDuration", 0) -- THJORADQUAKE.scr:26
    ctx:setPropNumber("ShakeAmount", 0) -- THJORADQUAKE.scr:27
    ctx:setPropNumber("NeedsTick", 1) -- THJORADQUAKE.scr:29
    mm9.gosub(script, ctx, "ExecuteQuakeLoop") -- THJORADQUAKE.scr:31
    do return ctx:exit("TRUE") end -- THJORADQUAKE.scr:33
end

script.labels["RandomizeValues"] = function(ctx)
    -- THJORADQUAKE.scr:36
    ctx:command("getrandomint", "3, 8, nTemp") -- THJORADQUAKE.scr:38
    ctx:setPropNumber("QuakeDuration", "nTemp") -- THJORADQUAKE.scr:39
    ctx:command("getrandomint", "2, 5, nTemp") -- THJORADQUAKE.scr:40
    ctx:setPropNumber("ShakeAmount", "nTemp") -- THJORADQUAKE.scr:41
    do return ctx:exit("TRUE") end -- THJORADQUAKE.scr:43
end

script.labels["ExecuteQuakeLoop"] = function(ctx)
    -- THJORADQUAKE.scr:46
    mm9.gosub(script, ctx, "RandomizeValues") -- THJORADQUAKE.scr:48
    mm9.gosub(script, ctx, "ExecuteQuake") -- THJORADQUAKE.scr:49
    ctx:command("getrandomint", "300, 600, nTemp") -- THJORADQUAKE.scr:51
    ctx:command("wait", "0, nTemp, ExecuteQuakeLoop") -- THJORADQUAKE.scr:53
    do return ctx:exit("TRUE") end -- THJORADQUAKE.scr:55
end

script.labels["ExecuteQuake"] = function(ctx)
    -- THJORADQUAKE.scr:58
    if ctx:condition("hPlayer==0") then -- THJORADQUAKE.scr:60
        ctx:command("getplayerhandle", "hPlayer") -- THJORADQUAKE.scr:61
    end -- THJORADQUAKE.scr:62
    if ctx:condition("hPlayer!=0") then -- THJORADQUAKE.scr:64
        ctx:command("getpos", "hPlayer, xMe, yMe, zMe") -- THJORADQUAKE.scr:65
        ctx:command("setpos", "hMe, xMe, yMe, zMe") -- THJORADQUAKE.scr:66
    end -- THJORADQUAKE.scr:67
    ctx:trigger("hMe", "trigger") -- THJORADQUAKE.scr:69
    do return ctx:exit("TRUE") end -- THJORADQUAKE.scr:71
end

return script
