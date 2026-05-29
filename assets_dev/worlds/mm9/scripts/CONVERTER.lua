-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CONVERTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseGlobals.inc" }

-- Converter.scr
-- by SJR
-- 11-01-01
-- Purpose:convert creature into
-- other creature the painful
-- way. Will be normal or will
-- be player's buddy
script.labels["Main"] = function(ctx)
    -- CONVERTER.scr:28
    ctx:getParam(0, "sFromName") -- CONVERTER.scr:30
    ctx:getParam(1, "sToName") -- CONVERTER.scr:31
    ctx:getParam(2, "sEffectsName") -- CONVERTER.scr:32
    ctx:getParam(3, "sLocationName") -- CONVERTER.scr:33
    ctx:onEvent("OnPostStartWorld", "InitConverter") -- CONVERTER.scr:35
    ctx:onEvent("OnPostMiniSaveLoad", "InitConverter") -- CONVERTER.scr:36
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- CONVERTER.scr:37
    do return ctx:exit("TRUE") end -- CONVERTER.scr:39
end

script.labels["CacheFiles"] = function(ctx)
    -- CONVERTER.scr:42
    ctx:cacheSound("sounds\\magic\\projectile14.wav") -- CONVERTER.scr:44
    ctx:cacheSound("sounds\\magic\\wizardeyeloop.wav") -- CONVERTER.scr:45
    ctx:cacheSound("sounds\\animsounds\\pig\\wince1.wav") -- CONVERTER.scr:46
    do return ctx:exit("TRUE") end -- CONVERTER.scr:48
end

script.labels["InitConverter"] = function(ctx)
    -- CONVERTER.scr:51
    ctx:state().hLocation = ctx:objectOrNil("sLocationName") -- CONVERTER.scr:53
    ctx:state().hEffects = ctx:objectOrNil("sEffectsName") -- CONVERTER.scr:54
    if ctx:condition("hLocation!=0") then -- CONVERTER.scr:55
        ctx:state().xLoc, ctx:state().yLoc, ctx:state().zLoc = ctx:object("hLocation"):pos() -- CONVERTER.scr:56
    end -- CONVERTER.scr:57
    ctx:addTrigger("create", "SpawnCreature") -- CONVERTER.scr:59
    ctx:addTrigger("convert", "TransformCreature") -- CONVERTER.scr:60
    do return ctx:exit("TRUE") end -- CONVERTER.scr:62
end

script.labels["SpawnCreature"] = function(ctx)
    -- CONVERTER.scr:65
    -- spawn one, kill it, spawn another there
    ctx:removeTrigger("create") -- CONVERTER.scr:68
    ctx:state().xLoc, ctx:state().yLoc, ctx:state().zLoc = ctx:object("hLocation"):pos() -- CONVERTER.scr:70
    ctx:set("SPAWN_PARAM", "sFromName + SCRIPT_NAME") -- CONVERTER.scr:72
    ctx:state().hCreature = nil -- CONVERTER.scr:73
    ctx:state().hCreature = ctx:spawn("xLoc", "yLoc", "zLoc", "SPAWN_PARAM") -- CONVERTER.scr:74
    ctx:wait(0, 2, "SignalCreature") -- CONVERTER.scr:75
    do return ctx:exit("TRUE") end -- CONVERTER.scr:77
end

script.labels["SignalCreature"] = function(ctx)
    -- CONVERTER.scr:80
    -- kills the peasant, spawns the skeleton
    ctx:trigger("hCreature", "walk") -- CONVERTER.scr:83
    do return ctx:exit("TRUE") end -- CONVERTER.scr:85
end

script.labels["TransformCreature"] = function(ctx)
    -- CONVERTER.scr:88
    -- kills the peasant, spawns the skeleton
    if ctx:condition("hEffects!=0") then -- CONVERTER.scr:91
        ctx:trigger("hEffects", "trigger") -- CONVERTER.scr:92
    end -- CONVERTER.scr:93
    if ctx:condition("hDummy!=0") then -- CONVERTER.scr:94
        ctx:state().xLoc, ctx:state().yLoc, ctx:state().zLoc = ctx:object("hCreature"):pos() -- CONVERTER.scr:95
        ctx:object("hCreature"):remove() -- CONVERTER.scr:96
        ctx:state().hCreature = nil -- CONVERTER.scr:97
    end -- CONVERTER.scr:98
    ctx:playSound("sounds\\magic\\projectile14.wav", "DoNothing", 1, 500, "FALSE", 100) -- CONVERTER.scr:100
    ctx:state().hCreature = ctx:spawn("xLoc", "yLoc", "zLoc", "sToName") -- CONVERTER.scr:101
    ctx:object("hCreature"):setStat("GaveTreasure", "TRUE") -- CONVERTER.scr:103
    ctx:addTrigger("create", "SpawnCreature") -- CONVERTER.scr:105
    do return ctx:exit("TRUE") end -- CONVERTER.scr:107
end

return script
