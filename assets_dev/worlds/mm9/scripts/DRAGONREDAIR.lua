-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAGONREDAIR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "wanderair.inc" }

-- DragonRedAir.scr
-- Quick & Dirty RedDragon script so that he'll just fly around
script.labels["Main"] = function(ctx)
    -- DRAGONREDAIR.scr:11
    mm9.gosub(script, ctx, "WanderAirInit") -- DRAGONREDAIR.scr:14
    do return ctx:exit("") end -- DRAGONREDAIR.scr:16
end

return script
