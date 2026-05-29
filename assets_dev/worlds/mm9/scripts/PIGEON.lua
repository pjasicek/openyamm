-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PIGEON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "wanderair.inc" }

-- Pigeon.scr
-- Simple pigeon script
script.labels["Main"] = function(ctx)
    -- PIGEON.scr:13
    mm9.gosub(script, ctx, "WanderAirInit") -- PIGEON.scr:18
    ctx:self():setIdle() -- PIGEON.scr:20
    do return ctx:exit("") end -- PIGEON.scr:22
end

return script
