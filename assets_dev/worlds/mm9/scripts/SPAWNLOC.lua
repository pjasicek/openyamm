-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPAWNLOC.scr"
script.includes = {}
script.labels = {}


-- SpawnLoc.scr
-- by SJR
-- 11-02-01
-- Purpose:be a location for
-- SpawnMgr.
-- Triggers:
-- "On" = enable
-- "Off" = disable
-- "Spawn" = change location and spawn
-- "Focus" = change location
script.labels["Main"] = function(ctx)
    -- SPAWNLOC.scr:18
    ctx:getParam(0, "sCreatureName") -- SPAWNLOC.scr:20
    ctx:onEvent("OnPostStartWorld", "InitSpawnLoc") -- SPAWNLOC.scr:22
    ctx:onEvent("OnPostMiniSaveLoad", "InitSpawnLoc") -- SPAWNLOC.scr:23
    do return ctx:exit(1) end -- SPAWNLOC.scr:25
end

script.labels["InitSpawnLoc"] = function(ctx)
    -- SPAWNLOC.scr:28
    ctx:addTrigger("On", "TurnOn") -- SPAWNLOC.scr:30
    mm9.gosub(script, ctx, "TurnOn") -- SPAWNLOC.scr:31
    ctx:state().hSpawnMgr = ctx:objectOrNil("SpawnMgr") -- SPAWNLOC.scr:33
    if ctx:condition("hSpawnMgr==0") then -- SPAWNLOC.scr:34
        do return ctx:exit(1) end -- SPAWNLOC.scr:35
    end -- SPAWNLOC.scr:36
    do return ctx:exit(1) end -- SPAWNLOC.scr:38
end

script.labels["RequestSpawn"] = function(ctx)
    -- SPAWNLOC.scr:41
    -- ask Mgr to spawn here (spawn + focus)
    ctx:setConsoleStrVar("SPAWN_TYPE", "sCreatureName") -- SPAWNLOC.scr:44
    mm9.gosub(script, ctx, "RequestFocus") -- SPAWNLOC.scr:45
    ctx:trigger("hSpawnMgr", "ForceSpawn") -- SPAWNLOC.scr:46
    do return ctx:exit(1) end -- SPAWNLOC.scr:47
end

script.labels["RequestFocus"] = function(ctx)
    -- SPAWNLOC.scr:50
    -- make this the current spawn location (focus only)
    ctx:setConsoleStrVar("SPAWN_TYPE", "sCreatureName") -- SPAWNLOC.scr:53
    ctx:trigger("hSpawnMgr", "SetLocation") -- SPAWNLOC.scr:54
    do return ctx:exit(1) end -- SPAWNLOC.scr:55
end

script.labels["TurnOn"] = function(ctx)
    -- SPAWNLOC.scr:58
    -- enable all messages
    ctx:addTrigger("spawn", "RequestSpawn") -- SPAWNLOC.scr:61
    ctx:addTrigger("focus", "RequestFocus") -- SPAWNLOC.scr:62
    ctx:addTrigger("off", "TurnOff") -- SPAWNLOC.scr:63
    do return ctx:exit(1) end -- SPAWNLOC.scr:64
end

script.labels["TurnOff"] = function(ctx)
    -- SPAWNLOC.scr:67
    -- disable all messages except On
    ctx:removeTrigger("spawn") -- SPAWNLOC.scr:70
    ctx:removeTrigger("focus") -- SPAWNLOC.scr:71
    ctx:removeTrigger("off") -- SPAWNLOC.scr:72
    do return ctx:exit(1) end -- SPAWNLOC.scr:73
end

return script
