-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLE_SPAWNCREATURE.scr"
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
    -- ISLE_SPAWNCREATURE.scr:24
    ctx:wait(0, .1, "InitSpawnCreature") -- ISLE_SPAWNCREATURE.scr:26
    do return ctx:exit("TRUE") end -- ISLE_SPAWNCREATURE.scr:28
end

script.labels["InitSpawnCreature"] = function(ctx)
    -- ISLE_SPAWNCREATURE.scr:31
    ctx:self():setNumberProperty("CheckForAIBarriers", "TRUE") -- ISLE_SPAWNCREATURE.scr:33
    ctx:self():setNumberProperty("CheckForCliffs", "TRUE") -- ISLE_SPAWNCREATURE.scr:34
    ctx:onEvent("OnDeath", "OnDeath") -- ISLE_SPAWNCREATURE.scr:38
    ctx:state().hRally = ctx:objectOrNil("MarkerFrom") -- ISLE_SPAWNCREATURE.scr:40
    if ctx:condition("hRally!=0") then -- ISLE_SPAWNCREATURE.scr:41
        ctx:self():doClientFx("SPELL_ELEMBLAST", "FALSE", "TRUE") -- ISLE_SPAWNCREATURE.scr:42
        ctx:self():doClientFx("SPELL_COLUMNOFFIRE", "FALSE", "TRUE") -- ISLE_SPAWNCREATURE.scr:43
        ctx:self():runTo(ctx:object("hRally"), 10, "Teleport") -- ISLE_SPAWNCREATURE.scr:44
    end -- ISLE_SPAWNCREATURE.scr:45
    do return ctx:exit("TRUE") end -- ISLE_SPAWNCREATURE.scr:47
end

script.labels["OnDeath"] = function(ctx)
    -- ISLE_SPAWNCREATURE.scr:50
    -- when dead, notify Mgr for respawn
    ctx:state().hSpawnMgr = ctx:objectOrNil("LichSummoner") -- ISLE_SPAWNCREATURE.scr:53
    if ctx:condition("hSpawnMgr!=0") then -- ISLE_SPAWNCREATURE.scr:54
        ctx:trigger("hSpawnMgr", "spawn") -- ISLE_SPAWNCREATURE.scr:55
    end -- ISLE_SPAWNCREATURE.scr:56
    do return ctx:exit("TRUE") end -- ISLE_SPAWNCREATURE.scr:58
end

script.labels["Teleport"] = function(ctx)
    -- ISLE_SPAWNCREATURE.scr:61
    ctx:self():stop() -- ISLE_SPAWNCREATURE.scr:63
    ctx:state().hRally = ctx:objectOrNil("MarkerTo") -- ISLE_SPAWNCREATURE.scr:65
    if ctx:condition("hRally!=0") then -- ISLE_SPAWNCREATURE.scr:66
        ctx:state().x, ctx:state().y, ctx:state().z = ctx:object("hRally"):pos() -- ISLE_SPAWNCREATURE.scr:67
        ctx:self():setPos("x", "y", "z") -- ISLE_SPAWNCREATURE.scr:68
        ctx:self():doClientFx("SPELL_COLUMNOFFIRE", 0, 1) -- ISLE_SPAWNCREATURE.scr:69
    end -- ISLE_SPAWNCREATURE.scr:70
    mm9.gosub(script, ctx, "BaseInit") -- ISLE_SPAWNCREATURE.scr:72
    mm9.gosub(script, ctx, "BaseWanderStartup") -- ISLE_SPAWNCREATURE.scr:73
    do return ctx:exit("TRUE") end -- ISLE_SPAWNCREATURE.scr:75
end

return script
