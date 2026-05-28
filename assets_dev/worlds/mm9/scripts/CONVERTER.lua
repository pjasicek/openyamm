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
    ctx:command("onpoststartworld", "InitConverter") -- CONVERTER.scr:35
    ctx:command("onpostminisaveload", "InitConverter") -- CONVERTER.scr:36
    ctx:command("oncachefiles", "CacheFiles") -- CONVERTER.scr:37
    do return ctx:exit("TRUE") end -- CONVERTER.scr:39
end

script.labels["CacheFiles"] = function(ctx)
    -- CONVERTER.scr:42
    ctx:command("cachesound", "\"sounds\\magic\\projectile14.wav\"") -- CONVERTER.scr:44
    ctx:command("cachesound", "\"sounds\\magic\\wizardeyeloop.wav\"") -- CONVERTER.scr:45
    ctx:command("cachesound", "\"sounds\\animsounds\\pig\\wince1.wav\"") -- CONVERTER.scr:46
    do return ctx:exit("TRUE") end -- CONVERTER.scr:48
end

script.labels["InitConverter"] = function(ctx)
    -- CONVERTER.scr:51
    ctx:command("getobjecthandle", "sLocationName, hLocation") -- CONVERTER.scr:53
    ctx:command("getobjecthandle", "sEffectsName, hEffects") -- CONVERTER.scr:54
    if ctx:condition("hLocation!=0") then -- CONVERTER.scr:55
        ctx:command("getpos", "hLocation, xLoc, yLoc, zLoc") -- CONVERTER.scr:56
    end -- CONVERTER.scr:57
    ctx:addTrigger("create", "SpawnCreature") -- CONVERTER.scr:59
    ctx:addTrigger("convert", "TransformCreature") -- CONVERTER.scr:60
    do return ctx:exit("TRUE") end -- CONVERTER.scr:62
end

script.labels["SpawnCreature"] = function(ctx)
    -- CONVERTER.scr:65
    -- spawn one, kill it, spawn another there
    ctx:command("removetrigger", "create") -- CONVERTER.scr:68
    ctx:command("getpos", "hLocation, xLoc, yLoc, zLoc") -- CONVERTER.scr:70
    ctx:command("spawn_param", "= sFromName + SCRIPT_NAME") -- CONVERTER.scr:72
    ctx:command("hcreature", "= NULL") -- CONVERTER.scr:73
    ctx:command("spawn", "hCreature, xLoc, yLoc, zLoc, SPAWN_PARAM") -- CONVERTER.scr:74
    ctx:command("wait", "0, 2, SignalCreature") -- CONVERTER.scr:75
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
        ctx:command("getpos", "hCreature, xLoc, yLoc, zLoc") -- CONVERTER.scr:95
        ctx:command("removeobject", "hCreature") -- CONVERTER.scr:96
        ctx:command("hcreature", "= NULL") -- CONVERTER.scr:97
    end -- CONVERTER.scr:98
    ctx:command("playsound", "\"sounds\\magic\\projectile14.wav\", DoNothing, 1, 500, FALSE, 100") -- CONVERTER.scr:100
    ctx:command("spawn", "hCreature, xLoc, yLoc, zLoc, sToName") -- CONVERTER.scr:101
    ctx:command("setstat", "hCreature, GaveTreasure, TRUE") -- CONVERTER.scr:103
    ctx:addTrigger("create", "SpawnCreature") -- CONVERTER.scr:105
    do return ctx:exit("TRUE") end -- CONVERTER.scr:107
end

return script
