-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASERANGE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "range.inc" }

-- BaseRange.Scr
-- Base script for simple AI that have range
-- attacks....
script.labels["Main"] = function(ctx)
    -- BASERANGE.scr:13
    mm9.gosub(script, ctx, "BaseInit") -- BASERANGE.scr:17
    mm9.gosub(script, ctx, "RangeInit") -- BASERANGE.scr:18
    do return ctx:exit("") end -- BASERANGE.scr:21
end

return script
