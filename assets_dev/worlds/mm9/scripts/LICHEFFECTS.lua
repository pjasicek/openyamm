-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHEFFECTS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "CutSceneActor.inc" }

-- LichEffects.scr
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- LICHEFFECTS.scr:23
    ctx:getParam(0, "sEffect0Name") -- LICHEFFECTS.scr:25
    ctx:getParam(1, "sEffect1Name") -- LICHEFFECTS.scr:26
    ctx:getParam(2, "sEffect2Name") -- LICHEFFECTS.scr:27
    ctx:getParam(3, "sEffect3Name") -- LICHEFFECTS.scr:28
    ctx:addTrigger("play", "PlayEffects") -- LICHEFFECTS.scr:32
    do return ctx:exit("TRUE") end -- LICHEFFECTS.scr:34
end

script.labels["PlayEffects"] = function(ctx)
    -- LICHEFFECTS.scr:38
    ctx:state().hEffect0 = ctx:objectOrNil("sEffect0Name") -- LICHEFFECTS.scr:40
    ctx:state().hEffect1 = ctx:objectOrNil("sEffect1Name") -- LICHEFFECTS.scr:41
    ctx:state().hEffect2 = ctx:objectOrNil("sEffect2Name") -- LICHEFFECTS.scr:42
    ctx:state().hEffect3 = ctx:objectOrNil("sEffect3Name") -- LICHEFFECTS.scr:43
    mm9.gosub(script, ctx, "PlayEffectsLoop") -- LICHEFFECTS.scr:45
    do return ctx:exit("TRUE") end -- LICHEFFECTS.scr:47
end

script.labels["PlayEffectsLoop"] = function(ctx)
    -- LICHEFFECTS.scr:50
    if ctx:condition("nCounter>6") then -- LICHEFFECTS.scr:52
        mm9.gosub(script, ctx, "EndScene") -- LICHEFFECTS.scr:53
        do return ctx:exit("TRUE") end -- LICHEFFECTS.scr:54
    else -- LICHEFFECTS.scr:55
        ctx:set("nCounter", "nCounter + 1") -- LICHEFFECTS.scr:56
    end -- LICHEFFECTS.scr:57
    ctx:object("hEffect0"):doClientFx("SPELL_BLUEFIRE", "FALSE", "TRUE") -- LICHEFFECTS.scr:59
    ctx:object("hEffect1"):doClientFx("SPELL_BLUEFIRE", "FALSE", "TRUE") -- LICHEFFECTS.scr:60
    ctx:object("hEffect2"):doClientFx("SPELL_BLUEFIRE", "FALSE", "TRUE") -- LICHEFFECTS.scr:61
    ctx:object("hEffect3"):doClientFx("SPELL_BLUEFIRE", "FALSE", "TRUE") -- LICHEFFECTS.scr:62
    ctx:wait(0, 1, "PlayEffectsLoop") -- LICHEFFECTS.scr:64
    do return ctx:exit("TRUE") end -- LICHEFFECTS.scr:66
end

return script
