-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WANDER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "wander.inc" }

-- wander.scr
-- Jeff Leggett
-- Default script for wanderers
script.labels["Main"] = function(ctx)
    -- WANDER.scr:13
    mm9.gosub(script, ctx, "WanderInit") -- WANDER.scr:16
    do return ctx:exit("") end -- WANDER.scr:18
end

return script
