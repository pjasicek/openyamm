-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ENDCOUNT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }

script.labels["EndCount.scr"] = function(ctx)
    -- ENDCOUNT.scr:2
end

-- Timmy
-- This counts the spawners to spawn the last demon
-- in the Tomb of a Thousand Terrors
script.labels["OnSpawn"] = function(ctx)
    -- ENDCOUNT.scr:31
    ctx:command("nspawncount", "= nSpawnCount + 1") -- ENDCOUNT.scr:34
    if ctx:condition("nSpawnCount==nSpawnMax") then -- ENDCOUNT.scr:36
        mm9.gosub(script, ctx, "SpawnDemon") -- ENDCOUNT.scr:37
    end -- ENDCOUNT.scr:38
    do return ctx:exit("") end -- ENDCOUNT.scr:40
end

script.labels["SpawnDemon"] = function(ctx)
    -- ENDCOUNT.scr:44
    ctx:command("getobjecthandle", "sSpawnMarker g_hobject") -- ENDCOUNT.scr:48
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- ENDCOUNT.scr:49
    ctx:command("spawn", "hDemon Xpos YPos ZPos sDemon") -- ENDCOUNT.scr:51
    do return ctx:exit("") end -- ENDCOUNT.scr:53
end

script.labels["Main"] = function(ctx)
    -- ENDCOUNT.scr:56
    -- TraceOn
    ctx:command("sdemon", "= sDemon + SCRIPT") -- ENDCOUNT.scr:62
    ctx:addTrigger("Spawned", "OnSpawn") -- ENDCOUNT.scr:64
    ctx:addTrigger("ForceSpawn", "SpawnDemon") -- ENDCOUNT.scr:65
    do return ctx:exit("") end -- ENDCOUNT.scr:67
end

return script
