-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "1000T_CIRCLESHOOTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 20, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 21, path = "ListMaker.inc" }

-- 1000t_CircleShooter.scr
-- by SJR
-- 11-20-01
-- FeltUP slightly by Karl 12-1-01
-- Purpose:circle around player and
-- shoot stuff
-- Triggers:
-- "Start" = begin shooting
-- ScriptParams:
-- p0 = LISTNAME
-- p1 = LISTFIRST
-- p2 = LISTLAST
-- p3 = time inbetween shots
-- p4 = object to trigger when started
-- p5 = object to trigger when stopped
script.labels["Main"] = function(ctx)
    -- 1000T_CIRCLESHOOTER.scr:37
    ctx:getParam(0, "LISTNAME") -- 1000T_CIRCLESHOOTER.scr:39
    ctx:getParam(1, "LISTFIRST") -- 1000T_CIRCLESHOOTER.scr:40
    ctx:getParam(2, "LISTLAST") -- 1000T_CIRCLESHOOTER.scr:41
    ctx:getParam(3, "nShootDelay") -- 1000T_CIRCLESHOOTER.scr:43
    ctx:getParam(4, "sStartName") -- 1000T_CIRCLESHOOTER.scr:44
    ctx:getParam(5, "sStopName") -- 1000T_CIRCLESHOOTER.scr:45
    -- OnPostStartWorld InitCircleShooter
    ctx:command("wait", "0, 5, InitCircleShooter") -- 1000T_CIRCLESHOOTER.scr:48
    do return ctx:exit("TRUE") end -- 1000T_CIRCLESHOOTER.scr:49
end

script.labels["InitCircleShooter"] = function(ctx)
    -- 1000T_CIRCLESHOOTER.scr:52
    ctx:addTrigger("go", "StartShooting") -- 1000T_CIRCLESHOOTER.scr:54
    ctx:command("getplayerhandle", "hPlayer") -- 1000T_CIRCLESHOOTER.scr:56
    ctx:command("getmyhandle", "hMe") -- 1000T_CIRCLESHOOTER.scr:57
    do return ctx:exit("TRUE") end -- 1000T_CIRCLESHOOTER.scr:59
end

script.labels["StartShooting"] = function(ctx)
    -- 1000T_CIRCLESHOOTER.scr:62
    mm9.gosub(script, ctx, "GetFirstObject") -- 1000T_CIRCLESHOOTER.scr:64
    ctx:command("target", "hPlayer, TRUE") -- 1000T_CIRCLESHOOTER.scr:65
    mm9.gosub(script, ctx, "Fire") -- 1000T_CIRCLESHOOTER.scr:66
    do return ctx:exit("TRUE") end -- 1000T_CIRCLESHOOTER.scr:68
end

script.labels["UpdatePOS"] = function(ctx)
    -- 1000T_CIRCLESHOOTER.scr:71
    ctx:trigger("hMe", "On") -- 1000T_CIRCLESHOOTER.scr:73
    mm9.gosub(script, ctx, "GetNextObject") -- 1000T_CIRCLESHOOTER.scr:74
    if ctx:condition("LISTINDEX==LISTFIRST") then -- 1000T_CIRCLESHOOTER.scr:75
        mm9.gosub(script, ctx, "StopShooting") -- 1000T_CIRCLESHOOTER.scr:76
    else -- 1000T_CIRCLESHOOTER.scr:77
        mm9.gosub(script, ctx, "Fire") -- 1000T_CIRCLESHOOTER.scr:79
    end -- 1000T_CIRCLESHOOTER.scr:81
    do return ctx:exit("TRUE") end -- 1000T_CIRCLESHOOTER.scr:83
end

script.labels["Fire"] = function(ctx)
    -- 1000T_CIRCLESHOOTER.scr:86
    ctx:trigger("hMe", "Off") -- 1000T_CIRCLESHOOTER.scr:88
    ctx:command("getpos", "LISTOBJECT, xMe,yMe,zMe") -- 1000T_CIRCLESHOOTER.scr:89
    ctx:command("movetopos", "xMe,yMe,zMe, 500, UpdatePOS") -- 1000T_CIRCLESHOOTER.scr:90
    do return ctx:exit("TRUE") end -- 1000T_CIRCLESHOOTER.scr:93
end

script.labels["StopShooting"] = function(ctx)
    -- 1000T_CIRCLESHOOTER.scr:96
    ctx:command("getobjecthandle", "sStopName, hTrigger") -- 1000T_CIRCLESHOOTER.scr:98
    ctx:trigger("hTrigger", "trigger") -- 1000T_CIRCLESHOOTER.scr:99
    ctx:trigger("hMe", "Off") -- 1000T_CIRCLESHOOTER.scr:100
    ctx:command("target", "NULL") -- 1000T_CIRCLESHOOTER.scr:101
    do return ctx:exit("TRUE") end -- 1000T_CIRCLESHOOTER.scr:103
end

return script
