-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PEASANTTRANSFORMEE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseGlobals.inc" }

-- PeasantTransformee.scr
-- by SJR
-- 11-01-01
-- Purpose:convert creature into
-- other creature the painful
-- way. Will be normal or will
-- be player's buddy
script.labels["Main"] = function(ctx)
    -- PEASANTTRANSFORMEE.scr:21
    ctx:command("wait", "0, .1, InitPeasantTransformee") -- PEASANTTRANSFORMEE.scr:23
    do return ctx:exit("TRUE") end -- PEASANTTRANSFORMEE.scr:25
end

script.labels["InitPeasantTransformee"] = function(ctx)
    -- PEASANTTRANSFORMEE.scr:28
    ctx:command("getmyhandle", "hMe") -- PEASANTTRANSFORMEE.scr:30
    ctx:addTrigger("walk", "WalkToSpawner") -- PEASANTTRANSFORMEE.scr:31
    ctx:command("onstuck", "OnStuck") -- PEASANTTRANSFORMEE.scr:32
    do return ctx:exit("TRUE") end -- PEASANTTRANSFORMEE.scr:34
end

script.labels["WalkToSpawner"] = function(ctx)
    -- PEASANTTRANSFORMEE.scr:37
    ctx:getParam(0, "hSpawner") -- PEASANTTRANSFORMEE.scr:39
    ctx:command("getpos", "hSpawner, x,t,z") -- PEASANTTRANSFORMEE.scr:40
    ctx:command("getpos", "hMe, t,y,t") -- PEASANTTRANSFORMEE.scr:41
    ctx:command("walktopos", "x,y,z, 5, PlayMagicSound") -- PEASANTTRANSFORMEE.scr:43
    do return ctx:exit("TRUE") end -- PEASANTTRANSFORMEE.scr:45
end

script.labels["OnStuck"] = function(ctx)
    -- PEASANTTRANSFORMEE.scr:48
    ctx:command("stop", "") -- PEASANTTRANSFORMEE.scr:50
    ctx:command("wait", "0, 1, Continue") -- PEASANTTRANSFORMEE.scr:51
    do return ctx:exit("TRUE") end -- PEASANTTRANSFORMEE.scr:53
end

script.labels["Continue"] = function(ctx)
    -- PEASANTTRANSFORMEE.scr:56
    ctx:command("walktopos", "x,y,z, 5, PlayMagicSound") -- PEASANTTRANSFORMEE.scr:58
    do return ctx:exit("TRUE") end -- PEASANTTRANSFORMEE.scr:60
end

script.labels["PlayMagicSound"] = function(ctx)
    -- PEASANTTRANSFORMEE.scr:63
    ctx:command("stop", "") -- PEASANTTRANSFORMEE.scr:65
    ctx:command("loopanim", "cower, 1, TriggerSpawner") -- PEASANTTRANSFORMEE.scr:66
    ctx:command("playsound", "\"sounds\\magic\\wizardeyeloop.wav\", DoNothing, 1, 1000, FALSE, 100") -- PEASANTTRANSFORMEE.scr:67
    do return ctx:exit("TRUE") end -- PEASANTTRANSFORMEE.scr:69
end

script.labels["TriggerSpawner"] = function(ctx)
    -- PEASANTTRANSFORMEE.scr:72
    ctx:command("playsound", "\"sounds\\animsounds\\pig\\wince1.wav\", DoNothing, 1, 500, FALSE, 100") -- PEASANTTRANSFORMEE.scr:74
    ctx:trigger("hSpawner", "convert") -- PEASANTTRANSFORMEE.scr:75
    do return ctx:exit("TRUE") end -- PEASANTTRANSFORMEE.scr:77
end

return script
