-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP2WATERDAMAGE.scr"
script.includes = {}
script.labels = {}


-- DP2waterdamage.scr
-- By Timmy
-- sets damage for water
-- parameters
-- p0  amount of damage
script.labels["DamageOn"] = function(ctx)
    -- DP2WATERDAMAGE.scr:15
    ctx:self():setStringProperty("Damagetype", "DT_BURN") -- DP2WATERDAMAGE.scr:18
    ctx:self():setNumberProperty("Damage", "Damage_Amount") -- DP2WATERDAMAGE.scr:19
    do return ctx:exit("") end -- DP2WATERDAMAGE.scr:20
end

script.labels["DamageOff"] = function(ctx)
    -- DP2WATERDAMAGE.scr:24
    ctx:self():setStringProperty("Damagetype", "DT_UNSPECIFIED") -- DP2WATERDAMAGE.scr:27
    ctx:self():setNumberProperty("Damage", 0) -- DP2WATERDAMAGE.scr:28
    do return ctx:exit("") end -- DP2WATERDAMAGE.scr:30
end

script.labels["Main"] = function(ctx)
    -- DP2WATERDAMAGE.scr:33
    ctx:getParam(0, "Damage_Amount") -- DP2WATERDAMAGE.scr:37
    ctx:addTrigger("DamageOn", "DamageOn") -- DP2WATERDAMAGE.scr:38
    ctx:addTrigger("DamageOff", "DamageOff") -- DP2WATERDAMAGE.scr:39
    do return ctx:exit("") end -- DP2WATERDAMAGE.scr:40
end

return script
