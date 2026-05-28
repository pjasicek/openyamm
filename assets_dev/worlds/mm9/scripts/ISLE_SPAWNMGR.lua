-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLE_SPAWNMGR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 21, path = "BaseGlobals.inc" }

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
-- p2 = String name of creature type
-- Trigger to change spawn location: SetLocation
-- Trigger to force a spawn: ForceSpawn
-- Trigger to shut off completely: Off
-- Trigger to turn back on: On
-- parameter builder stuff
script.labels["Main"] = function(ctx)
    -- ISLE_SPAWNMGR.scr:45
    ctx:getParam(0, "SpawnCycle") -- ISLE_SPAWNMGR.scr:47
    ctx:getParam(1, "SpawnSize") -- ISLE_SPAWNMGR.scr:48
    ctx:getParam(2, "NAME") -- ISLE_SPAWNMGR.scr:49
    ctx:command("onpoststartworld", "InitSpawnMgr") -- ISLE_SPAWNMGR.scr:51
    do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:53
end

script.labels["InitSpawnMgr"] = function(ctx)
    -- ISLE_SPAWNMGR.scr:56
    ctx:addTrigger("setlocation", "SetLocation") -- ISLE_SPAWNMGR.scr:58
    ctx:addTrigger("respawn", "OnCreatureDied") -- ISLE_SPAWNMGR.scr:59
    ctx:addTrigger("forcespawn", "SpawnCreature") -- ISLE_SPAWNMGR.scr:60
    ctx:addTrigger("off", "TurnOff") -- ISLE_SPAWNMGR.scr:61
    ctx:addTrigger("on", "TurnOn") -- ISLE_SPAWNMGR.scr:62
    ctx:command("screaturename", "= NAME + SCRIPT") -- ISLE_SPAWNMGR.scr:64
    do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:66
end

script.labels["OnCreatureDied"] = function(ctx)
    -- ISLE_SPAWNMGR.scr:69
    -- when creature dies, check
    -- if can respawn, then do it
    if ctx:condition("NumKilled>=9") then -- ISLE_SPAWNMGR.scr:73
        ctx:command("removetrigger", "respawn") -- ISLE_SPAWNMGR.scr:74
        ctx:command("removetrigger", "forcespawn") -- ISLE_SPAWNMGR.scr:75
    end -- ISLE_SPAWNMGR.scr:76
    mm9.gosub(script, ctx, "AdjustTotals") -- ISLE_SPAWNMGR.scr:78
    ctx:command("isnotdivisible", "= NumKilled") -- ISLE_SPAWNMGR.scr:79
    ctx:command("mod", "IsNotDivisible, SpawnCycle") -- ISLE_SPAWNMGR.scr:80
    -- only spawn every time X are killed
    if ctx:condition("IsNotDivisible==0") then -- ISLE_SPAWNMGR.scr:82
        mm9.gosub(script, ctx, "SpawnCreature") -- ISLE_SPAWNMGR.scr:83
    end -- ISLE_SPAWNMGR.scr:84
    do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:85
end

script.labels["SpawnCreature"] = function(ctx)
    -- ISLE_SPAWNMGR.scr:88
    -- spawn a batch of creatures at
    -- the current point
    -- check creature quantity cap
    if ctx:condition("NumKilled>=10") then -- ISLE_SPAWNMGR.scr:93
        do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:94
    end -- ISLE_SPAWNMGR.scr:95
    -- add these guys to total
    ctx:command("numonscreen", "= NumOnScreen + SpawnSize") -- ISLE_SPAWNMGR.scr:98
    ctx:command("ntemp", "= SpawnSize") -- ISLE_SPAWNMGR.scr:99
    -- loop spawning to spawn whole batch
    while ctx:condition("nTemp>0") do -- ISLE_SPAWNMGR.scr:101
        ctx:command("spawn", "hDummy, Spawnx,Spawny,Spawnz, sCreatureName") -- ISLE_SPAWNMGR.scr:102
        ctx:command("ntemp", "= nTemp - 1") -- ISLE_SPAWNMGR.scr:103
    end -- ISLE_SPAWNMGR.scr:104
    do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:105
end

script.labels["AdjustTotals"] = function(ctx)
    -- ISLE_SPAWNMGR.scr:108
    -- keep track of deaths
    ctx:command("numkilled", "= NumKilled + 1") -- ISLE_SPAWNMGR.scr:111
    ctx:command("numonscreen", "= NumOnScreen - 1") -- ISLE_SPAWNMGR.scr:112
    do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:113
end

script.labels["TurnOn"] = function(ctx)
    -- ISLE_SPAWNMGR.scr:116
    -- enable OnDeath respawning
    ctx:command("removetrigger", "Respawn") -- ISLE_SPAWNMGR.scr:119
    ctx:addTrigger("Respawn", "OnCreatureDied") -- ISLE_SPAWNMGR.scr:120
    do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:121
end

script.labels["TurnOff"] = function(ctx)
    -- ISLE_SPAWNMGR.scr:124
    -- disable OnDeath respawning
    -- can still forcespawn though
    ctx:command("removetrigger", "Respawn") -- ISLE_SPAWNMGR.scr:128
    -- keep track of deaths to avoid
    -- going over the cap
    ctx:addTrigger("Respawn", "AdjustTotals") -- ISLE_SPAWNMGR.scr:131
    do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:132
end

script.labels["SetLocation"] = function(ctx)
    -- ISLE_SPAWNMGR.scr:135
    -- set spawn location to triggerer
    ctx:getParam(0, "hSpawnMarker") -- ISLE_SPAWNMGR.scr:138
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- ISLE_SPAWNMGR.scr:139
    do return ctx:exit("TRUE") end -- ISLE_SPAWNMGR.scr:140
end

return script
