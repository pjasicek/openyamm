-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ENDCOUNTTRIGGER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }

script.labels["EndCountTrigger.scr"] = function(ctx)
    -- ENDCOUNTTRIGGER.scr:2
end

-- Timmy
-- This triggers the spawner counter to spawn the last demon
-- in the Tomb of a Thousand Terrors
script.labels["OnSpawn"] = function(ctx)
    -- ENDCOUNTTRIGGER.scr:18
    ctx:object("sSpawnCounter"):trigger("Spawned") -- ENDCOUNTTRIGGER.scr:21-22
    do return ctx:exit("FALSE") end -- ENDCOUNTTRIGGER.scr:25
end

script.labels["Main"] = function(ctx)
    -- ENDCOUNTTRIGGER.scr:28
    -- TraceOn
    ctx:addTrigger("default", "OnSpawn") -- ENDCOUNTTRIGGER.scr:33
    ctx:addTrigger("Count", "OnSpawn") -- ENDCOUNTTRIGGER.scr:34
    do return ctx:exit("") end -- ENDCOUNTTRIGGER.scr:36
end

return script
