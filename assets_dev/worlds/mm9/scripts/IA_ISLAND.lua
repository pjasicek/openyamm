-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IA_ISLAND.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "Globals.inc" }

-- IA_Island.scr
-- Timmy
-- 1/29/02
-- makes the island disappear after
-- leaving
script.labels["OnSinkSpeed"] = function(ctx)
    -- IA_ISLAND.scr:17
    ctx:setPropNumber("speed", 1000) -- IA_ISLAND.scr:20
    do return ctx:exit("") end -- IA_ISLAND.scr:21
end

script.labels["Main"] = function(ctx)
    -- IA_ISLAND.scr:24
    -- This routine is automatically run
    -- at script startup...
    ctx:addTrigger("SinkSpeed", "OnSinkSpeed") -- IA_ISLAND.scr:29
    do return ctx:exit("") end -- IA_ISLAND.scr:31
end

return script
