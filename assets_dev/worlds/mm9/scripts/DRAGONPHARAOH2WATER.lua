-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAGONPHARAOH2WATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "water.inc" }

script.labels["dragonpharaoh2Water.scr"] = function(ctx)
    -- DRAGONPHARAOH2WATER.scr:2
end

-- Timmy
-- This script can be used to sink and fill water...
-- Parameters:
-- p1	- How many inches of water to leave (when sinking)
-- p2	- Sink Rate
-- p3	- Fill Rate
script.labels["DoneSinking"] = function(ctx)
    -- DRAGONPHARAOH2WATER.scr:20
    ctx:object("WallTorch0"):trigger("Enable") -- DRAGONPHARAOH2WATER.scr:25-26
    ctx:object("WallTorch1"):trigger("Enable") -- DRAGONPHARAOH2WATER.scr:27-28
    ctx:object("WallTorch2"):trigger("Enable") -- DRAGONPHARAOH2WATER.scr:29-30
    ctx:object("WallTorch3"):trigger("Enable") -- DRAGONPHARAOH2WATER.scr:31-32
    ctx:object("WallTorch4"):trigger("Enable") -- DRAGONPHARAOH2WATER.scr:33-34
    ctx:object("WallTorch5"):trigger("Enable") -- DRAGONPHARAOH2WATER.scr:35-36
    do return ctx:exit("") end -- DRAGONPHARAOH2WATER.scr:38
end

script.labels["main"] = function(ctx)
    -- DRAGONPHARAOH2WATER.scr:43
    mm9.gosub(script, ctx, "waterinit") -- DRAGONPHARAOH2WATER.scr:49
    ctx:setCallback(1, "DoneSinking") -- DRAGONPHARAOH2WATER.scr:50
    do return ctx:exit("") end -- DRAGONPHARAOH2WATER.scr:52
end

return script
