-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "water.inc" }

script.labels["Water.scr"] = function(ctx)
    -- WATER.scr:2
end

-- Jeff Leggett
-- This script can be used to sink and fill water...
-- Parameters:
-- p1	- How many inches of water to leave (when sinking)
-- p2	- Sink Rate
-- p3	- Fill Rate
script.labels["main"] = function(ctx)
    -- WATER.scr:19
    mm9.gosub(script, ctx, "waterinit") -- WATER.scr:23
    do return ctx:exit("") end -- WATER.scr:24
end

return script
