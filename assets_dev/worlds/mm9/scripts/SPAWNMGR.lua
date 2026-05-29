-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPAWNMGR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 23, path = "BaseGlobals.inc" }

-- SpawnMgr.scr
-- by SJR
-- 09-21-01
-- Purpose:Used in conjunction with SourceCreature.scr
-- to spawn out of sight and unlock doors
-- when enough have been killed
-- -DEDIT INFO-
-- ScriptParams are:
-- p0 = How many to kill before respawn
-- p1 = How many to spawn each time
-- p2 = name of creature type
-- p3 = name to notify OnSpawn
-- Trigger to change spawn location: SetLocation
-- Trigger to change creature type: <creaturename>
-- Trigger to force a spawn: ForceSpawn
-- Trigger to shut off completely: Off
-- Trigger to turn back on: On
-- parameter builder stuff
script.labels["Main"] = function(ctx)
    -- SPAWNMGR.scr:50
    ctx:getParam(0, "SpawnCycle") -- SPAWNMGR.scr:52
    ctx:getParam(1, "SpawnSize") -- SPAWNMGR.scr:53
    ctx:getParam(2, "NAME") -- SPAWNMGR.scr:54
    ctx:getParam(3, "sNotifyName") -- SPAWNMGR.scr:55
    ctx:onEvent("OnPostStartWorld", "InitSpawnMgr") -- SPAWNMGR.scr:57
    ctx:onEvent("OnPostMiniSaveLoad", "InitSpawnMgr") -- SPAWNMGR.scr:58
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- SPAWNMGR.scr:59
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:61
end

script.labels["CacheFiles"] = function(ctx)
    -- SPAWNMGR.scr:64
    ctx:cacheScript("SpawnCreature.scr") -- SPAWNMGR.scr:66
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:68
end

script.labels["InitSpawnMgr"] = function(ctx)
    -- SPAWNMGR.scr:71
    ctx:addTrigger("SetLocation", "SetLocation") -- SPAWNMGR.scr:73
    ctx:addTrigger("Respawn", "OnCreatureDied") -- SPAWNMGR.scr:74
    ctx:addTrigger("ForceSpawn", "SpawnCreature") -- SPAWNMGR.scr:75
    ctx:addTrigger("Off", "TurnOff") -- SPAWNMGR.scr:76
    ctx:addTrigger("On", "TurnOn") -- SPAWNMGR.scr:77
    ctx:state().hNotify = ctx:objectOrNil("sNotifyName") -- SPAWNMGR.scr:79
    if ctx:condition("hNotify!=0") then -- SPAWNMGR.scr:80
        ctx:self():link(ctx:object("hNotify")) -- SPAWNMGR.scr:81
    end -- SPAWNMGR.scr:82
    ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- SPAWNMGR.scr:83
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:85
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- SPAWNMGR.scr:88
    ctx:state().hNotify = nil -- SPAWNMGR.scr:90
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:92
end

script.labels["OnCreatureDied"] = function(ctx)
    -- SPAWNMGR.scr:95
    -- when creature dies, check
    -- if can respawn, then do it
    mm9.gosub(script, ctx, "AdjustTotals") -- SPAWNMGR.scr:99
    ctx:set("IsNotDivisible", "NumKilled") -- SPAWNMGR.scr:100
    ctx:mod("IsNotDivisible", "SpawnCycle") -- SPAWNMGR.scr:101
    -- only spawn every time X are killed
    if ctx:condition("IsNotDivisible==0") then -- SPAWNMGR.scr:103
        ctx:trigger("hSpawnMarker", "spawn") -- SPAWNMGR.scr:104
    end -- SPAWNMGR.scr:105
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:106
end

script.labels["SpawnCreature"] = function(ctx)
    -- SPAWNMGR.scr:109
    -- spawn a batch of creatures at
    -- the current point
    -- check creature quantity cap
    if ctx:condition("NumKilled>=10") then -- SPAWNMGR.scr:114
        do return ctx:exit("TRUE") end -- SPAWNMGR.scr:115
    end -- SPAWNMGR.scr:116
    if ctx:condition("hNotify!=0") then -- SPAWNMGR.scr:118
        ctx:trigger("hNotify", "trigger") -- SPAWNMGR.scr:119
    end -- SPAWNMGR.scr:120
    -- add these guys to total
    ctx:set("NumOnScreen", "NumOnScreen + SpawnSize") -- SPAWNMGR.scr:123
    ctx:set("nTemp", "SpawnSize") -- SPAWNMGR.scr:124
    -- make string parameter thingy
    if ctx:condition("sCreatureName==\"LesserDemon\"") then -- SPAWNMGR.scr:127
        ctx:set("sCreatureName", "LESSERDEMON") -- SPAWNMGR.scr:128
    else -- SPAWNMGR.scr:129
        ctx:set("sCreatureName", "NAME + SCRIPT") -- SPAWNMGR.scr:130
    end -- SPAWNMGR.scr:131
    -- loop spawning to spawn whole batch
    while ctx:condition("nTemp>0") do -- SPAWNMGR.scr:134
        ctx:state().hDummy = ctx:spawn("Spawnx", "Spawny", "Spawnz", "sCreatureName") -- SPAWNMGR.scr:135
        ctx:set("nTemp", "nTemp - 1") -- SPAWNMGR.scr:136
    end -- SPAWNMGR.scr:137
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:138
end

script.labels["AdjustTotals"] = function(ctx)
    -- SPAWNMGR.scr:141
    -- keep track of deaths
    ctx:set("NumKilled", "NumKilled + 1") -- SPAWNMGR.scr:144
    ctx:set("NumOnScreen", "NumOnScreen - 1") -- SPAWNMGR.scr:145
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:146
end

script.labels["TurnOn"] = function(ctx)
    -- SPAWNMGR.scr:149
    -- enable OnDeath respawning
    ctx:removeTrigger("Respawn") -- SPAWNMGR.scr:152
    ctx:addTrigger("Respawn", "OnCreatureDied") -- SPAWNMGR.scr:153
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:154
end

script.labels["TurnOff"] = function(ctx)
    -- SPAWNMGR.scr:157
    -- disable OnDeath respawning
    -- can still forcespawn though
    ctx:removeTrigger("Respawn") -- SPAWNMGR.scr:161
    -- keep track of deaths to avoid
    -- going over the cap
    ctx:addTrigger("Respawn", "AdjustTotals") -- SPAWNMGR.scr:164
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:165
end

script.labels["SetLocation"] = function(ctx)
    -- SPAWNMGR.scr:168
    -- set spawn location to triggerer
    ctx:getParam(0, "hSpawnMarker") -- SPAWNMGR.scr:171
    ctx:state().Spawnx, ctx:state().Spawny, ctx:state().Spawnz = ctx:object("hSpawnMarker"):pos() -- SPAWNMGR.scr:172
    ctx:getConsoleStrVar("SPAWN_TYPE", "sCreatureName") -- SPAWNMGR.scr:173
    if ctx:condition("sCreatureName!=\"\"") then -- SPAWNMGR.scr:174
        ctx:set("NAME", "sCreatureName") -- SPAWNMGR.scr:175
    end -- SPAWNMGR.scr:176
    do return ctx:exit("TRUE") end -- SPAWNMGR.scr:177
end

return script
