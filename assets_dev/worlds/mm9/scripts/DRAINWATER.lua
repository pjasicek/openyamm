-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAINWATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "BaseGlobals.inc" }

-- DrainWater.scr
-- by SJR
-- 10-12-01
-- Purpose:drain\fill area with liquid
-- ScriptParams:
-- p0 = name of fill marker
-- p1 = name of empty marker
-- p2 = name of thing to trigger
-- Triggers:
-- "Drain" = drain the brush
script.labels["Main"] = function(ctx)
    -- DRAINWATER.scr:35
    ctx:getParam(0, "sTopName") -- DRAINWATER.scr:37
    ctx:getParam(1, "sBottomName") -- DRAINWATER.scr:38
    ctx:getParam(2, "sFillTriggerName") -- DRAINWATER.scr:39
    ctx:getParam(3, "sDrainTriggerName") -- DRAINWATER.scr:40
    ctx:command("onpoststartworld", "InitDrainSwitch") -- DRAINWATER.scr:42
    ctx:command("onpostminisaveload", "InitDrainSwitch") -- DRAINWATER.scr:43
    do return ctx:exit("TRUE") end -- DRAINWATER.scr:45
end

script.labels["InitDrainSwitch"] = function(ctx)
    -- DRAINWATER.scr:48
    ctx:addTrigger("drain", "DrainWater") -- DRAINWATER.scr:50
    ctx:addTrigger("fill", "FillWater") -- DRAINWATER.scr:51
    ctx:command("getmyhandle", "hMe") -- DRAINWATER.scr:53
    ctx:command("getpos", "hMe, xMe, nTemp, zMe") -- DRAINWATER.scr:54
    ctx:command("getobjecthandle", "sFillTriggerName, hFillTrigger") -- DRAINWATER.scr:55
    ctx:command("getobjecthandle", "sDrainTriggerName, hDrainTrigger") -- DRAINWATER.scr:56
    ctx:command("getobjecthandle", "sBottomName, hFloor") -- DRAINWATER.scr:57
    ctx:command("getobjecthandle", "sTopName, hRoof") -- DRAINWATER.scr:58
    do return ctx:exit("TRUE") end -- DRAINWATER.scr:60
end

script.labels["FillWater"] = function(ctx)
    -- DRAINWATER.scr:63
    ctx:trigger("hFillTrigger", "trigger") -- DRAINWATER.scr:65
    ctx:addTrigger("drain", "DrainWater") -- DRAINWATER.scr:66
    ctx:command("removetrigger", "fill") -- DRAINWATER.scr:67
    ctx:command("playsound", "\"sounds\\ambient\\fountain_20.wav\", DoNothing, 1, 5000, FALSE, 100") -- DRAINWATER.scr:68
    ctx:command("getpos", "hRoof, nTemp,yMe,nTemp") -- DRAINWATER.scr:69
    ctx:command("movetopos", "xMe,yMe,zMe, 10, OnFillWater") -- DRAINWATER.scr:70
    do return ctx:exit("TRUE") end -- DRAINWATER.scr:72
end

script.labels["DrainWater"] = function(ctx)
    -- DRAINWATER.scr:75
    ctx:trigger("hDrainTrigger", "trigger") -- DRAINWATER.scr:77
    ctx:addTrigger("fill", "FillWater") -- DRAINWATER.scr:78
    ctx:command("removetrigger", "drain") -- DRAINWATER.scr:79
    ctx:command("playsound", "\"sounds\\ambient\\fountain_20.wav\", DoNothing, 1, 5000, FALSE, 100") -- DRAINWATER.scr:80
    ctx:command("getpos", "hFloor, nTemp,yMe,nTemp") -- DRAINWATER.scr:81
    ctx:command("movetopos", "xMe,yMe,zMe, 10, OnDrainWater") -- DRAINWATER.scr:82
    do return ctx:exit("TRUE") end -- DRAINWATER.scr:84
end

script.labels["OnFillWater"] = function(ctx)
    -- DRAINWATER.scr:87
    ctx:command("stop", "") -- DRAINWATER.scr:89
    do return ctx:exit("TRUE") end -- DRAINWATER.scr:91
end

script.labels["OnDrainWater"] = function(ctx)
    -- DRAINWATER.scr:94
    ctx:command("stop", "") -- DRAINWATER.scr:96
    do return ctx:exit("TRUE") end -- DRAINWATER.scr:98
end

return script
