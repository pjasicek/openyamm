-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP2MEGAHYDRA.scr"
script.includes = {}
script.labels = {}


-- DP2megahydra.scr
-- By Timmy
-- turns megahydra damage on
script.labels["DamageOn"] = function(ctx)
    -- DP2MEGAHYDRA.scr:10
    ctx:self():setNumberProperty("CanDamage", 1) -- DP2MEGAHYDRA.scr:14
    do return ctx:exit("") end -- DP2MEGAHYDRA.scr:15
end

script.labels["Main"] = function(ctx)
    -- DP2MEGAHYDRA.scr:19
    -- TraceOn
    ctx:addTrigger("DamageOn", "DamageOn") -- DP2MEGAHYDRA.scr:23
    do return ctx:exit("") end -- DP2MEGAHYDRA.scr:26
end

return script
