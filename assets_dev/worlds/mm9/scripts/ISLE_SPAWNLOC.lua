-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLE_SPAWNLOC.scr"
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
    -- ISLE_SPAWNLOC.scr:17
    ctx:command("onpoststartworld", "InitSpawnLoc") -- ISLE_SPAWNLOC.scr:19
    do return ctx:exit(1) end -- ISLE_SPAWNLOC.scr:21
end

script.labels["InitSpawnLoc"] = function(ctx)
    -- ISLE_SPAWNLOC.scr:24
    ctx:addTrigger("On", "TurnOn") -- ISLE_SPAWNLOC.scr:26
    mm9.gosub(script, ctx, "TurnOn") -- ISLE_SPAWNLOC.scr:27
    ctx:command("getobjecthandle", "SpawnMgr, hSpawnMgr") -- ISLE_SPAWNLOC.scr:28
    do return ctx:exit(1) end -- ISLE_SPAWNLOC.scr:29
end

script.labels["RequestSpawn"] = function(ctx)
    -- ISLE_SPAWNLOC.scr:32
    -- ask Mgr to spawn here (spawn + focus)
    mm9.gosub(script, ctx, "RequestFocus") -- ISLE_SPAWNLOC.scr:35
    ctx:trigger("hSpawnMgr", "ForceSpawn") -- ISLE_SPAWNLOC.scr:36
    do return ctx:exit(1) end -- ISLE_SPAWNLOC.scr:37
end

script.labels["RequestFocus"] = function(ctx)
    -- ISLE_SPAWNLOC.scr:40
    -- make this the current spawn location (focus only)
    ctx:trigger("hSpawnMgr", "SetLocation") -- ISLE_SPAWNLOC.scr:43
    do return ctx:exit(1) end -- ISLE_SPAWNLOC.scr:44
end

script.labels["TurnOn"] = function(ctx)
    -- ISLE_SPAWNLOC.scr:47
    -- enable all messages
    ctx:addTrigger("spawn", "RequestSpawn") -- ISLE_SPAWNLOC.scr:50
    ctx:addTrigger("focus", "RequestFocus") -- ISLE_SPAWNLOC.scr:51
    ctx:addTrigger("off", "TurnOff") -- ISLE_SPAWNLOC.scr:52
    do return ctx:exit(1) end -- ISLE_SPAWNLOC.scr:53
end

script.labels["TurnOff"] = function(ctx)
    -- ISLE_SPAWNLOC.scr:56
    -- disable all messages except On
    ctx:command("removetrigger", "spawn") -- ISLE_SPAWNLOC.scr:59
    ctx:command("removetrigger", "focus") -- ISLE_SPAWNLOC.scr:60
    ctx:command("removetrigger", "off") -- ISLE_SPAWNLOC.scr:61
    do return ctx:exit(1) end -- ISLE_SPAWNLOC.scr:62
end

return script
