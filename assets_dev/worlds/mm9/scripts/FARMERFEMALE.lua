-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FARMERFEMALE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- femalefarmer.scr
-- John Machin
-- Default script for wanderers
-- #hobject	hAlertedBy
-- #string		sAlertName
-- #hobject	hAttacker
-- #hobject	hTouchedBy
-- Passed in Parameter to get Wander distance
script.labels["OnSpecial"] = function(ctx)
    -- FARMERFEMALE.scr:28
    -- Feeding the chickens
    -- Randomly pick between the 2 chicken feeding anims
    ctx:command("getrandomint", "1, 10, g_nRandom") -- FARMERFEMALE.scr:33
    if ctx:condition("g_nRandom <= 5") then -- FARMERFEMALE.scr:34
        ctx:command("playanim", "feedchicken1, OnFeedChickenDone") -- FARMERFEMALE.scr:35
    else -- FARMERFEMALE.scr:36
        ctx:command("playanim", "feedchicken2, OnFeedChickenDone") -- FARMERFEMALE.scr:37
    end -- FARMERFEMALE.scr:38
    -- Alert the chickens
    mm9.gosub(script, ctx, "FarmerFeedChickens") -- FARMERFEMALE.scr:41
    do return ctx:exit("") end -- FARMERFEMALE.scr:44
end

script.labels["FarmerFeedChickens"] = function(ctx)
    -- FARMERFEMALE.scr:48
    ctx:command("getobjects", "Hen, 500, 50, g_hHenArray, g_nObjects") -- FARMERFEMALE.scr:50
end

script.labels["GetHens"] = function(ctx)
    -- FARMERFEMALE.scr:52
    if ctx:condition("g_nCtr < g_nObjects") then -- FARMERFEMALE.scr:53
        ctx:command("arrayget", "g_hHenArray, g_nCtr, g_hCurrHen") -- FARMERFEMALE.scr:54
        ctx:command("add", "g_nCtr, 1") -- FARMERFEMALE.scr:55
        ctx:trigger("g_hCurrHen", "Feeding") -- FARMERFEMALE.scr:57
        mm9.gosub(script, ctx, "GetHens") -- FARMERFEMALE.scr:59
    end -- FARMERFEMALE.scr:60
    do return ctx:exit("") end -- FARMERFEMALE.scr:62
end

script.labels["OnFeedChickenDone"] = function(ctx)
    -- FARMERFEMALE.scr:66
    ctx:command("wait", "1, WanderTick") -- FARMERFEMALE.scr:68
    do return ctx:exit("") end -- FARMERFEMALE.scr:70
end

script.labels["OnSpecialDone"] = function(ctx)
    -- FARMERFEMALE.scr:74
    -- Were done just exit
    do return ctx:exit("") end -- FARMERFEMALE.scr:78
end

script.labels["Main"] = function(ctx)
    -- FARMERFEMALE.scr:81
    -- Set Rooster wander distance
    ctx:getParam(1, "g_nDistance") -- FARMERFEMALE.scr:85
    if ctx:condition("g_nDistance != 0") then -- FARMERFEMALE.scr:87
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- FARMERFEMALE.scr:88
    else -- FARMERFEMALE.scr:89
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 350") -- FARMERFEMALE.scr:90
    end -- FARMERFEMALE.scr:91
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 10") -- FARMERFEMALE.scr:94
    -- Set max time in seconds before idle check
    ctx:command("set", "g_IdleCheckMin, 2") -- FARMERFEMALE.scr:97
    ctx:command("set", "g_IdleCheckMax, 6") -- FARMERFEMALE.scr:98
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpeicalAnimFrequency, 5") -- FARMERFEMALE.scr:101
    -- OnDamage FarmerOnDamage
    mm9.gosub(script, ctx, "WanderInit") -- FARMERFEMALE.scr:105
    ctx:addTrigger("SpecialAnim", "OnSpecial") -- FARMERFEMALE.scr:107
    do return ctx:exit("") end -- FARMERFEMALE.scr:109
end

return script
