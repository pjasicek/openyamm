-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "JUMPER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "Jumper.Inc" }

-- Jumper.Scr
-- Jeff Leggett
-- 01/08/2002
-- Base script used by AI that jump off cliffs at the
-- player...
script.labels["Main"] = function(ctx)
    -- JUMPER.scr:13
    mm9.gosub(script, ctx, "SetupJumper") -- JUMPER.scr:16
    do return ctx:exit("") end -- JUMPER.scr:19
end

return script
