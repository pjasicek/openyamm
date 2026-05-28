-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BIRD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "wanderair.inc" }

-- Bird.scr
-- Simple bird script
script.labels["Main"] = function(ctx)
    -- BIRD.scr:13
    mm9.gosub(script, ctx, "WanderAirInit") -- BIRD.scr:18
    -- SetIdle
    do return ctx:exit("") end -- BIRD.scr:22
end

return script
