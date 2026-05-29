-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP2STEAM.scr"
script.includes = {}
script.labels = {}


-- DP2steam.scr
-- By Timmy
-- turns Fire Up and Down
-- Parameters:
-- P0 minimum fire scale
-- P1 Maximum fire scale
script.labels["FireOn"] = function(ctx)
    -- DP2STEAM.scr:15
    ctx:self():setNumberProperty("FireScale", "MaxScale") -- DP2STEAM.scr:19
    do return ctx:exit("") end -- DP2STEAM.scr:20
end

script.labels["FireOff"] = function(ctx)
    -- DP2STEAM.scr:24
    ctx:self():setNumberProperty("FireScale", "MinScale") -- DP2STEAM.scr:27
    do return ctx:exit("") end -- DP2STEAM.scr:29
end

script.labels["Main"] = function(ctx)
    -- DP2STEAM.scr:32
    -- TraceOn
    ctx:addTrigger("FireOn", "FireOn") -- DP2STEAM.scr:36
    ctx:addTrigger("FireOff", "FireOff") -- DP2STEAM.scr:37
    ctx:getParam(0, "MinScale") -- DP2STEAM.scr:38
    ctx:getParam(1, "MaxScale") -- DP2STEAM.scr:39
    do return ctx:exit("") end -- DP2STEAM.scr:40
end

return script
