-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SCURRYCREATURE.scr"
script.includes = {}
script.labels = {}


-- ScurryCreature.scr
-- by SJR
-- 10-14-01
-- Purpose:to scurry
-- Triggers:
-- "Hide" = bone out and disappear
script.labels["Main"] = function(ctx)
    -- SCURRYCREATURE.scr:22
    ctx:getParam(0, "sHideName") -- SCURRYCREATURE.scr:24
    -- OnPostStartWorld InitScurryCreature
    ctx:command("wait", "0, 5, InitScurryCreature") -- SCURRYCREATURE.scr:27
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:29
end

script.labels["InitScurryCreature"] = function(ctx)
    -- SCURRYCREATURE.scr:32
    ctx:command("getmyhandle", "hMe") -- SCURRYCREATURE.scr:34
    ctx:command("getstat", "hMe, RunVel, v") -- SCURRYCREATURE.scr:35
    ctx:command("v", "= v * 6") -- SCURRYCREATURE.scr:36
    ctx:command("setstat", "hMe, RunVel, v") -- SCURRYCREATURE.scr:37
    ctx:addTrigger("Hide", "GoHide") -- SCURRYCREATURE.scr:38
    ctx:command("onobstacle", "Turn") -- SCURRYCREATURE.scr:39
    ctx:command("onstuck", "Turn") -- SCURRYCREATURE.scr:40
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:42
end

script.labels["GoHide"] = function(ctx)
    -- SCURRYCREATURE.scr:45
    ctx:command("getobjecthandle", "sHideName, hHide") -- SCURRYCREATURE.scr:47
    ctx:command("playsound", "sounds\\animsounds\\dragonflyhattackair1.wav, DoNothing, 1, 500, 0, 100") -- SCURRYCREATURE.scr:48
    ctx:command("runto", "hHide, 100, Disappear") -- SCURRYCREATURE.scr:49
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:51
end

script.labels["Turn"] = function(ctx)
    -- SCURRYCREATURE.scr:54
    ctx:command("getfacedir", "hMe, x,y,z") -- SCURRYCREATURE.scr:56
    ctx:command("getrandomint", "-5, 5, v") -- SCURRYCREATURE.scr:57
    ctx:command("x", "= x * v") -- SCURRYCREATURE.scr:58
    ctx:command("z", "= z * v") -- SCURRYCREATURE.scr:59
    ctx:command("facedir", "z,y,x, 0, GoHide") -- SCURRYCREATURE.scr:60
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:62
end

script.labels["Disappear"] = function(ctx)
    -- SCURRYCREATURE.scr:65
    ctx:command("removeobject", "hMe") -- SCURRYCREATURE.scr:67
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:69
end

script.labels["DoNothing"] = function(ctx)
    -- SCURRYCREATURE.scr:72
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:74
end

return script
