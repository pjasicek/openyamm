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
    ctx:wait(0, 5, "InitScurryCreature") -- SCURRYCREATURE.scr:27
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:29
end

script.labels["InitScurryCreature"] = function(ctx)
    -- SCURRYCREATURE.scr:32
    ctx:state().v = ctx:self():getStat("RunVel") -- SCURRYCREATURE.scr:35
    ctx:set("v", "v * 6") -- SCURRYCREATURE.scr:36
    ctx:self():setStat("RunVel", "v") -- SCURRYCREATURE.scr:37
    ctx:addTrigger("Hide", "GoHide") -- SCURRYCREATURE.scr:38
    ctx:onEvent("OnObstacle", "Turn") -- SCURRYCREATURE.scr:39
    ctx:onEvent("OnStuck", "Turn") -- SCURRYCREATURE.scr:40
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:42
end

script.labels["GoHide"] = function(ctx)
    -- SCURRYCREATURE.scr:45
    ctx:state().hHide = ctx:objectOrNil("sHideName") -- SCURRYCREATURE.scr:47
    ctx:playSound("sounds\\animsounds\\dragonflyhattackair1.wav", "DoNothing", 1, 500, 0, 100) -- SCURRYCREATURE.scr:48
    ctx:self():runTo(ctx:object("hHide"), 100, "Disappear") -- SCURRYCREATURE.scr:49
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:51
end

script.labels["Turn"] = function(ctx)
    -- SCURRYCREATURE.scr:54
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:self():rotation() -- SCURRYCREATURE.scr:56
    ctx:randomInt(-5, 5, "v") -- SCURRYCREATURE.scr:57
    ctx:set("x", "x * v") -- SCURRYCREATURE.scr:58
    ctx:set("z", "z * v") -- SCURRYCREATURE.scr:59
    ctx:self():faceDir("z", "y", "x", 0, "GoHide") -- SCURRYCREATURE.scr:60
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:62
end

script.labels["Disappear"] = function(ctx)
    -- SCURRYCREATURE.scr:65
    ctx:self():remove() -- SCURRYCREATURE.scr:67
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:69
end

script.labels["DoNothing"] = function(ctx)
    -- SCURRYCREATURE.scr:72
    do return ctx:exit(1) end -- SCURRYCREATURE.scr:74
end

return script
