-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DOOKSLEEPGAURD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 21, path = "DookHostility.inc" }

-- DookSleepGaurd.scr
-- by Ed Campos
-- 10-22-01
-- Purpose: Gaurds Stand in place
-- With the ability to Fall Asleep
-- Possibly have Player able to Sneak
-- past the sleeping Gaurd
-- -DEDIT NOTES-
-- ScriptParams are:
-- p0->p7 = in order waypoint names for Patroling Gaurds
-- SJR( added all hostility stuff)
-- endSJR
script.labels["InitDookSleepGaurd"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:37
    mm9.gosub(script, ctx, "InitDookHostility") -- DOOKSLEEPGAURD.scr:39
    ctx:command("getobjecthandle", "sTarget0, hTarget") -- DOOKSLEEPGAURD.scr:41
    ctx:command("getobjecthandle", "sWayPoint0, hWayPoint") -- DOOKSLEEPGAURD.scr:42
    ctx:command("wait", "0, 2, SleepRoutine") -- DOOKSLEEPGAURD.scr:43
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:45
end

script.labels["SleepRoutine"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:48
    ctx:command("stop", "") -- DOOKSLEEPGAURD.scr:50
    ctx:command("loopanim", "Sleep, 0, DoNothing") -- DOOKSLEEPGAURD.scr:51
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:53
end

script.labels["WakeUp"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:56
    ctx:command("faceobject", ", hTarget, 180, DoNothing") -- DOOKSLEEPGAURD.scr:58
    ctx:command("playanim", "Cowerstart, GoCower") -- DOOKSLEEPGAURD.scr:59
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:62
end

script.labels["GoCower"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:65
    ctx:command("wait", "1, 4, EndCower") -- DOOKSLEEPGAURD.scr:67
    ctx:command("playanim", "CowerEnd, DoNothing") -- DOOKSLEEPGAURD.scr:68
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:70
end

script.labels["EndCower"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:73
    ctx:command("getfacedir", "hWayPoint, SleepMarkerX, SleepMarkerY, SleepMarkerZ") -- DOOKSLEEPGAURD.scr:75
    ctx:command("facedir", "SleepMarkerX, SleepMarkerY, SleepMarkerZ, 500,GoWait") -- DOOKSLEEPGAURD.scr:76
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:78
end

script.labels["GoWait"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:81
    ctx:command("stop", "") -- DOOKSLEEPGAURD.scr:83
    ctx:command("wait", "0,10, DoFidget3") -- DOOKSLEEPGAURD.scr:85
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:87
end

script.labels["DoFidget3"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:90
    ctx:command("stop", "") -- DOOKSLEEPGAURD.scr:92
    ctx:command("wait", "0,10, DoFidget2") -- DOOKSLEEPGAURD.scr:94
    ctx:command("playanim", "Fidget3, DoNothing") -- DOOKSLEEPGAURD.scr:96
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:98
end

script.labels["DoFidget2"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:101
    ctx:command("stop", "") -- DOOKSLEEPGAURD.scr:103
    ctx:command("wait", "0,20, SleepRoutine") -- DOOKSLEEPGAURD.scr:105
    ctx:command("playanim", "Fidget2, DoNothing") -- DOOKSLEEPGAURD.scr:107
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:109
end

script.labels["Main"] = function(ctx)
    -- DOOKSLEEPGAURD.scr:112
    ctx:addTrigger("WakeUp", "WakeUp") -- DOOKSLEEPGAURD.scr:114
    ctx:getParam(0, "sTarget0") -- DOOKSLEEPGAURD.scr:116
    ctx:getParam(1, "sWayPoint0") -- DOOKSLEEPGAURD.scr:117
    ctx:command("onpoststartworld", "InitDookSleepGaurd") -- DOOKSLEEPGAURD.scr:119
    do return ctx:exit("TRUE") end -- DOOKSLEEPGAURD.scr:121
end

return script
