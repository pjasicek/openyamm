-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASESWIM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "BaseSwim.inc" }

-- BaseSwim.Scr
-- Jeff Leggett
-- 11/07/2001
-- Base script for monsters that SWIM...
script.labels["Main"] = function(ctx)
    -- BASESWIM.scr:13
    mm9.gosub(script, ctx, "BaseSwimInit") -- BASESWIM.scr:14
    do return ctx:exit("") end -- BASESWIM.scr:15
end

return script
