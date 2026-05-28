-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPAWNCREATURE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "baseMelee.inc" }

-- SpawnCreature.scr
-- by SJR
-- 09-21-01
-- Purpose:Used in conjunction with SpawnMgr.scr
-- to continuously spawn out of sight w/ a limit
-- Will run to "SpawnRally" or player if it does not exist
script.labels["Main"] = function(ctx)
    -- SPAWNCREATURE.scr:16
    ctx:command("wait", "0, .1, InitSpawnCreature") -- SPAWNCREATURE.scr:18
    do return ctx:exit("TRUE") end -- SPAWNCREATURE.scr:20
end

script.labels["InitSpawnCreature"] = function(ctx)
    -- SPAWNCREATURE.scr:23
    ctx:setPropNumber("CheckForAIBarriers", "TRUE") -- SPAWNCREATURE.scr:25
    ctx:setPropNumber("CheckForCliffs", "TRUE") -- SPAWNCREATURE.scr:26
    ctx:command("getobjecthandle", "SpawnMgr, hSpawnMgr") -- SPAWNCREATURE.scr:28
    ctx:command("getobjecthandle", "SpawnRally, hRally") -- SPAWNCREATURE.scr:29
    mm9.gosub(script, ctx, "BaseInit") -- SPAWNCREATURE.scr:31
    -- message Mgr when dead
    ctx:command("ondeath", "OnDeath") -- SPAWNCREATURE.scr:34
    if ctx:condition("hRally==0") then -- SPAWNCREATURE.scr:36
        ctx:command("getplayerhandle", "g_hTarget") -- SPAWNCREATURE.scr:37
        mm9.gosub(script, ctx, "SetupTarget") -- SPAWNCREATURE.scr:38
        mm9.gosub(script, ctx, "AggressiveStart") -- SPAWNCREATURE.scr:39
    else -- SPAWNCREATURE.scr:40
        ctx:command("runto", "hRally, 10, DoNothing") -- SPAWNCREATURE.scr:41
    end -- SPAWNCREATURE.scr:42
    do return ctx:exit("TRUE") end -- SPAWNCREATURE.scr:44
end

script.labels["OnDeath"] = function(ctx)
    -- SPAWNCREATURE.scr:47
    -- when dead, notify Mgr for respawn
    if ctx:condition("hSpawnMgr!=0") then -- SPAWNCREATURE.scr:50
        ctx:trigger("hSpawnMgr", "Respawn") -- SPAWNCREATURE.scr:51
    end -- SPAWNCREATURE.scr:52
    do return ctx:exit("TRUE") end -- SPAWNCREATURE.scr:54
end

return script
