-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPAWNFACE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "range.inc" }

-- SpawnFace.scr
-- Handles facing of a spawned monster.
script.labels["Target"] = function(ctx)
    -- SPAWNFACE.scr:12
    ctx:command("getplayerhandle", "g_hplayer") -- SPAWNFACE.scr:15
    ctx:command("target", "g_hplayer") -- SPAWNFACE.scr:16
    do return ctx:exit("") end -- SPAWNFACE.scr:17
end

script.labels["Main"] = function(ctx)
    -- SPAWNFACE.scr:20
    mm9.gosub(script, ctx, "Target") -- SPAWNFACE.scr:23
    mm9.gosub(script, ctx, "baseinit") -- SPAWNFACE.scr:24
    -- gosub RangeInit
    do return ctx:exit("") end -- SPAWNFACE.scr:27
end

return script
