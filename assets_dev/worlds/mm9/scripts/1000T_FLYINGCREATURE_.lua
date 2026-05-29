-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "1000T_FLYINGCREATURE_.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "ListTraverse.inc" }

-- 1000T_FlyingCreature_.scr
-- Karl Drown 11-20-01
-- First event in level: Flying creatures
-- path around the entryway to scare party.
-- SJR------> scare them with 3 FPS, homes!!!
script.labels["Main"] = function(ctx)
    -- 1000T_FLYINGCREATURE_.scr:16
    ctx:getParam(0, "LISTNAME") -- 1000T_FLYINGCREATURE_.scr:18
    ctx:getParam(1, "LISTFIRST") -- 1000T_FLYINGCREATURE_.scr:19
    ctx:getParam(2, "LISTLAST") -- 1000T_FLYINGCREATURE_.scr:20
    mm9.gosub(script, ctx, "InitFlyingCreature") -- 1000T_FLYINGCREATURE_.scr:22
    do return ctx:exit(1) end -- 1000T_FLYINGCREATURE_.scr:24
end

script.labels["InitFlyingCreature"] = function(ctx)
    -- 1000T_FLYINGCREATURE_.scr:27
    mm9.gosub(script, ctx, "SetTraverseRun") -- 1000T_FLYINGCREATURE_.scr:29
    ctx:self():setModelFilenames("models\\flyingicky.abc", "textures\\leveltextures\\misc\\black.dtx") -- 1000T_FLYINGCREATURE_.scr:31
    ctx:self():setFlag("2097152", true) -- 1000T_FLYINGCREATURE_.scr:34
    ctx:self():setStat("FlyVel", 900) -- 1000T_FLYINGCREATURE_.scr:35
    ctx:onEvent("OnStuck", "RemoveMe") -- 1000T_FLYINGCREATURE_.scr:37
    ctx:addTrigger("go", "TraverseBegin") -- 1000T_FLYINGCREATURE_.scr:39
    do return ctx:exit(1) end -- 1000T_FLYINGCREATURE_.scr:41
end

script.labels["OnTraverseDone"] = function(ctx)
    -- 1000T_FLYINGCREATURE_.scr:44
    if ctx:condition("LISTINDEX==LISTLAST") then -- 1000T_FLYINGCREATURE_.scr:46
        ctx:self():stop() -- 1000T_FLYINGCREATURE_.scr:47
        ctx:self():remove() -- 1000T_FLYINGCREATURE_.scr:48
    else -- 1000T_FLYINGCREATURE_.scr:49
        ctx:playSound("sounds\\animsounds\\evileyeflap.wav", "DoNothing", 500, 2000, 0, 100) -- 1000T_FLYINGCREATURE_.scr:50
    end -- 1000T_FLYINGCREATURE_.scr:51
    do return ctx:exit(1) end -- 1000T_FLYINGCREATURE_.scr:53
end

script.labels["RemoveMe"] = function(ctx)
    -- 1000T_FLYINGCREATURE_.scr:56
    ctx:self():stop() -- 1000T_FLYINGCREATURE_.scr:58
    ctx:self():remove() -- 1000T_FLYINGCREATURE_.scr:59
    do return ctx:exit(1) end -- 1000T_FLYINGCREATURE_.scr:61
end

script.labels["DoNothing"] = function(ctx)
    -- 1000T_FLYINGCREATURE_.scr:64
    do return ctx:exit(1) end -- 1000T_FLYINGCREATURE_.scr:66
end

return script
