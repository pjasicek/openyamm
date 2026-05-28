-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TOWNSFOLKGIRL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "base.inc" }

-- townsfolkgirl.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
-- Creature type ok to attack bool
script.labels["townsfolkgirlAlert"] = function(ctx)
    -- TOWNSFOLKGIRL.scr:23
    ctx:getParam(0, "hAlertedBy") -- TOWNSFOLKGIRL.scr:26
    ctx:command("getclassname", "hAlertedBy, sAlertName") -- TOWNSFOLKGIRL.scr:27
    if ctx:condition("g_hTarget == NULL") then -- TOWNSFOLKGIRL.scr:29
        -- Check to see if the alert came from a NPC
        if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKGIRL.scr:31
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKGIRL.scr:32
        end -- TOWNSFOLKGIRL.scr:33
        if ctx:condition("sAlertName == townsfolkgirl") then -- TOWNSFOLKGIRL.scr:35
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKGIRL.scr:36
        end -- TOWNSFOLKGIRL.scr:37
        if ctx:condition("sAlertName == TownsFolkGirl") then -- TOWNSFOLKGIRL.scr:39
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKGIRL.scr:40
        end -- TOWNSFOLKGIRL.scr:41
        if ctx:condition("sAlertName == TownsFolkMale") then -- TOWNSFOLKGIRL.scr:43
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKGIRL.scr:44
        end -- TOWNSFOLKGIRL.scr:45
    end -- TOWNSFOLKGIRL.scr:47
    if ctx:condition("g_bOkAttackType == TRUE") then -- TOWNSFOLKGIRL.scr:49
        ctx:getParam(1, "g_hTarget") -- TOWNSFOLKGIRL.scr:50
        ctx:command("target", "g_hTarget") -- TOWNSFOLKGIRL.scr:51
        mm9.gosub(script, ctx, "BaseGoGetHim") -- TOWNSFOLKGIRL.scr:52
    end -- TOWNSFOLKGIRL.scr:53
    do return ctx:exit("") end -- TOWNSFOLKGIRL.scr:55
end

script.labels["townsfolkgirlAttackReady"] = function(ctx)
    -- TOWNSFOLKGIRL.scr:58
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("getclassname", "g_hTarget, sAlertName") -- TOWNSFOLKGIRL.scr:64
    if ctx:condition("sAlertName == townsfolkgirl") then -- TOWNSFOLKGIRL.scr:65
        do return ctx:exit("") end -- TOWNSFOLKGIRL.scr:66
    end -- TOWNSFOLKGIRL.scr:67
    if ctx:condition("sAlertName == TownsFolkGirl") then -- TOWNSFOLKGIRL.scr:69
        do return ctx:exit("") end -- TOWNSFOLKGIRL.scr:70
    end -- TOWNSFOLKGIRL.scr:71
    if ctx:condition("sAlertName == TownsFolkMale") then -- TOWNSFOLKGIRL.scr:73
        do return ctx:exit("") end -- TOWNSFOLKGIRL.scr:74
    end -- TOWNSFOLKGIRL.scr:75
    if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKGIRL.scr:77
        do return ctx:exit("") end -- TOWNSFOLKGIRL.scr:78
    end -- TOWNSFOLKGIRL.scr:79
    ctx:command("set", "g_bFighting, TRUE") -- TOWNSFOLKGIRL.scr:81
    ctx:command("gettime", "g_nLastAttackTime") -- TOWNSFOLKGIRL.scr:83
    ctx:command("attack", "") -- TOWNSFOLKGIRL.scr:85
    do return ctx:exit("") end -- TOWNSFOLKGIRL.scr:87
end

script.labels["Inittownsfolkgirl"] = function(ctx)
    -- TOWNSFOLKGIRL.scr:91
    -- Set NPC wander distance
    ctx:getParam(1, "g_nDistance") -- TOWNSFOLKGIRL.scr:94
    if ctx:condition("g_nDistance != 0") then -- TOWNSFOLKGIRL.scr:96
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- TOWNSFOLKGIRL.scr:97
    else -- TOWNSFOLKGIRL.scr:98
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 700") -- TOWNSFOLKGIRL.scr:99
    end -- TOWNSFOLKGIRL.scr:100
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 4") -- TOWNSFOLKGIRL.scr:103
    -- Set max time in seconds before idle check
    ctx:command("set", "g_IdleCheckMin, 7") -- TOWNSFOLKGIRL.scr:106
    ctx:command("set", "g_IdleCheckMax, 7") -- TOWNSFOLKGIRL.scr:107
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 0") -- TOWNSFOLKGIRL.scr:110
    do return ctx:exit("") end -- TOWNSFOLKGIRL.scr:112
end

script.labels["Main"] = function(ctx)
    -- TOWNSFOLKGIRL.scr:116
    -- Initialize boys behavior
    mm9.gosub(script, ctx, "Inittownsfolkgirl") -- TOWNSFOLKGIRL.scr:119
    -- Initialize attack behavior
    mm9.gosub(script, ctx, "InitBase") -- TOWNSFOLKGIRL.scr:122
    -- Initialize wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- TOWNSFOLKGIRL.scr:125
    -- Override these Base Calls
    ctx:command("onalert", "townsfolkgirlAlert") -- TOWNSFOLKGIRL.scr:128
    ctx:command("onattackready", "townsfolkgirlAttackReady") -- TOWNSFOLKGIRL.scr:129
    -- Monitoring this with no function will keep the AI from looking for players
    ctx:command("onfoundplayer", "") -- TOWNSFOLKGIRL.scr:132
    do return ctx:exit("") end -- TOWNSFOLKGIRL.scr:134
end

return script
