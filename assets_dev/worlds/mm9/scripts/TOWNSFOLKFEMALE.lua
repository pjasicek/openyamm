-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TOWNSFOLKFEMALE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "base.inc" }

-- TownsFolkFemale.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
-- Creature type ok to attack bool
script.labels["TownsFolkFemaleAlert"] = function(ctx)
    -- TOWNSFOLKFEMALE.scr:23
    ctx:getParam(0, "hAlertedBy") -- TOWNSFOLKFEMALE.scr:26
    ctx:command("getclassname", "hAlertedBy, sAlertName") -- TOWNSFOLKFEMALE.scr:27
    if ctx:condition("g_hTarget == NULL") then -- TOWNSFOLKFEMALE.scr:29
        -- Check to see if the alert came from a NPC
        if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKFEMALE.scr:31
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKFEMALE.scr:32
        end -- TOWNSFOLKFEMALE.scr:33
        if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKFEMALE.scr:35
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKFEMALE.scr:36
        end -- TOWNSFOLKFEMALE.scr:37
        if ctx:condition("sAlertName == TownsFolkGirl") then -- TOWNSFOLKFEMALE.scr:39
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKFEMALE.scr:40
        end -- TOWNSFOLKFEMALE.scr:41
        if ctx:condition("sAlertName == TownsFolkMale") then -- TOWNSFOLKFEMALE.scr:43
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKFEMALE.scr:44
        end -- TOWNSFOLKFEMALE.scr:45
    end -- TOWNSFOLKFEMALE.scr:47
    if ctx:condition("g_bOkAttackType == TRUE") then -- TOWNSFOLKFEMALE.scr:49
        ctx:getParam(1, "g_hTarget") -- TOWNSFOLKFEMALE.scr:50
        ctx:command("target", "g_hTarget") -- TOWNSFOLKFEMALE.scr:51
        mm9.gosub(script, ctx, "BaseGoGetHim") -- TOWNSFOLKFEMALE.scr:52
    end -- TOWNSFOLKFEMALE.scr:53
    do return ctx:exit("") end -- TOWNSFOLKFEMALE.scr:55
end

script.labels["TownsFolkFemaleAttackReady"] = function(ctx)
    -- TOWNSFOLKFEMALE.scr:58
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("getclassname", "g_hTarget, sAlertName") -- TOWNSFOLKFEMALE.scr:64
    if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKFEMALE.scr:65
        do return ctx:exit("") end -- TOWNSFOLKFEMALE.scr:66
    end -- TOWNSFOLKFEMALE.scr:67
    if ctx:condition("sAlertName == TownsFolkGirl") then -- TOWNSFOLKFEMALE.scr:69
        do return ctx:exit("") end -- TOWNSFOLKFEMALE.scr:70
    end -- TOWNSFOLKFEMALE.scr:71
    if ctx:condition("sAlertName == TownsFolkMale") then -- TOWNSFOLKFEMALE.scr:73
        do return ctx:exit("") end -- TOWNSFOLKFEMALE.scr:74
    end -- TOWNSFOLKFEMALE.scr:75
    if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKFEMALE.scr:77
        do return ctx:exit("") end -- TOWNSFOLKFEMALE.scr:78
    end -- TOWNSFOLKFEMALE.scr:79
    ctx:command("set", "g_bFighting, TRUE") -- TOWNSFOLKFEMALE.scr:81
    ctx:command("gettime", "g_nLastAttackTime") -- TOWNSFOLKFEMALE.scr:83
    ctx:command("attack", "") -- TOWNSFOLKFEMALE.scr:85
    do return ctx:exit("") end -- TOWNSFOLKFEMALE.scr:87
end

script.labels["InitTownsFolkFemale"] = function(ctx)
    -- TOWNSFOLKFEMALE.scr:91
    -- Set NPC wander distance
    ctx:getParam(1, "g_nDistance") -- TOWNSFOLKFEMALE.scr:94
    if ctx:condition("g_nDistance != 0") then -- TOWNSFOLKFEMALE.scr:96
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- TOWNSFOLKFEMALE.scr:97
    else -- TOWNSFOLKFEMALE.scr:98
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 700") -- TOWNSFOLKFEMALE.scr:99
    end -- TOWNSFOLKFEMALE.scr:100
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 4") -- TOWNSFOLKFEMALE.scr:103
    -- Set max time in seconds before idle check
    ctx:command("set", "g_IdleCheckMin, 7") -- TOWNSFOLKFEMALE.scr:106
    ctx:command("set", "g_IdleCheckMax, 7") -- TOWNSFOLKFEMALE.scr:107
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 0") -- TOWNSFOLKFEMALE.scr:110
    do return ctx:exit("") end -- TOWNSFOLKFEMALE.scr:112
end

script.labels["Main"] = function(ctx)
    -- TOWNSFOLKFEMALE.scr:116
    -- Initialize boys behavior
    mm9.gosub(script, ctx, "InitTownsFolkFemale") -- TOWNSFOLKFEMALE.scr:119
    -- Initialize attack behavior
    mm9.gosub(script, ctx, "InitBase") -- TOWNSFOLKFEMALE.scr:122
    -- Initialize wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- TOWNSFOLKFEMALE.scr:125
    -- Override these Base Calls
    ctx:command("onalert", "TownsFolkFemaleAlert") -- TOWNSFOLKFEMALE.scr:128
    ctx:command("onattackready", "TownsFolkFemaleAttackReady") -- TOWNSFOLKFEMALE.scr:129
    -- Monitoring this with no function will keep the AI from looking for players
    ctx:command("onfoundplayer", "") -- TOWNSFOLKFEMALE.scr:132
    do return ctx:exit("") end -- TOWNSFOLKFEMALE.scr:134
end

return script
