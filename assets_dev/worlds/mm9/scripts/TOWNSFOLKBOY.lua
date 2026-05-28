-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TOWNSFOLKBOY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "base.inc" }

-- townsfolkboy.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
-- Creature type ok to attack bool
script.labels["TownsFolkBoyAlert"] = function(ctx)
    -- TOWNSFOLKBOY.scr:23
    ctx:getParam(0, "hAlertedBy") -- TOWNSFOLKBOY.scr:26
    ctx:command("getclassname", "hAlertedBy, sAlertName") -- TOWNSFOLKBOY.scr:27
    if ctx:condition("g_hTarget == NULL") then -- TOWNSFOLKBOY.scr:29
        -- Check to see if the alert came from a NPC
        if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKBOY.scr:31
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKBOY.scr:32
        end -- TOWNSFOLKBOY.scr:33
        if ctx:condition("sAlertName == TownsFolkBoy") then -- TOWNSFOLKBOY.scr:35
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKBOY.scr:36
        end -- TOWNSFOLKBOY.scr:37
        if ctx:condition("sAlertName == TownsFolkGirl") then -- TOWNSFOLKBOY.scr:39
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKBOY.scr:40
        end -- TOWNSFOLKBOY.scr:41
        if ctx:condition("sAlertName == TownsFolkMale") then -- TOWNSFOLKBOY.scr:43
            ctx:command("set", "g_bOkAttackType, 1") -- TOWNSFOLKBOY.scr:44
        end -- TOWNSFOLKBOY.scr:45
    end -- TOWNSFOLKBOY.scr:47
    if ctx:condition("g_bOkAttackType == TRUE") then -- TOWNSFOLKBOY.scr:49
        ctx:getParam(1, "g_hTarget") -- TOWNSFOLKBOY.scr:50
        ctx:command("target", "g_hTarget") -- TOWNSFOLKBOY.scr:51
        mm9.gosub(script, ctx, "BaseGoGetHim") -- TOWNSFOLKBOY.scr:52
    end -- TOWNSFOLKBOY.scr:53
    do return ctx:exit("") end -- TOWNSFOLKBOY.scr:55
end

script.labels["TownsFolkBoyAttackReady"] = function(ctx)
    -- TOWNSFOLKBOY.scr:58
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("getclassname", "g_hTarget, sAlertName") -- TOWNSFOLKBOY.scr:64
    if ctx:condition("sAlertName == TownsFolkBoy") then -- TOWNSFOLKBOY.scr:65
        do return ctx:exit("") end -- TOWNSFOLKBOY.scr:66
    end -- TOWNSFOLKBOY.scr:67
    if ctx:condition("sAlertName == TownsFolkGirl") then -- TOWNSFOLKBOY.scr:69
        do return ctx:exit("") end -- TOWNSFOLKBOY.scr:70
    end -- TOWNSFOLKBOY.scr:71
    if ctx:condition("sAlertName == TownsFolkMale") then -- TOWNSFOLKBOY.scr:73
        do return ctx:exit("") end -- TOWNSFOLKBOY.scr:74
    end -- TOWNSFOLKBOY.scr:75
    if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKBOY.scr:77
        do return ctx:exit("") end -- TOWNSFOLKBOY.scr:78
    end -- TOWNSFOLKBOY.scr:79
    ctx:command("set", "g_bFighting, TRUE") -- TOWNSFOLKBOY.scr:81
    ctx:command("gettime", "g_nLastAttackTime") -- TOWNSFOLKBOY.scr:83
    ctx:command("attack", "") -- TOWNSFOLKBOY.scr:85
    do return ctx:exit("") end -- TOWNSFOLKBOY.scr:87
end

script.labels["InitTownsFolkBoy"] = function(ctx)
    -- TOWNSFOLKBOY.scr:91
    -- Set NPC wander distance
    ctx:getParam(1, "g_nDistance") -- TOWNSFOLKBOY.scr:94
    if ctx:condition("g_nDistance != 0") then -- TOWNSFOLKBOY.scr:96
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- TOWNSFOLKBOY.scr:97
    else -- TOWNSFOLKBOY.scr:98
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 700") -- TOWNSFOLKBOY.scr:99
    end -- TOWNSFOLKBOY.scr:100
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 4") -- TOWNSFOLKBOY.scr:103
    -- Set max time in seconds before idle check
    ctx:command("set", "g_IdleCheckMin, 7") -- TOWNSFOLKBOY.scr:106
    ctx:command("set", "g_IdleCheckMax, 7") -- TOWNSFOLKBOY.scr:107
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 0") -- TOWNSFOLKBOY.scr:110
    do return ctx:exit("") end -- TOWNSFOLKBOY.scr:112
end

script.labels["Main"] = function(ctx)
    -- TOWNSFOLKBOY.scr:116
    -- Initialize boys behavior
    mm9.gosub(script, ctx, "InitTownsFolkBoy") -- TOWNSFOLKBOY.scr:119
    -- Initialize attack behavior
    mm9.gosub(script, ctx, "InitBase") -- TOWNSFOLKBOY.scr:122
    -- Initialize wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- TOWNSFOLKBOY.scr:125
    -- Override these Base Calls
    ctx:command("onalert", "TownsFolkBoyAlert") -- TOWNSFOLKBOY.scr:128
    ctx:command("onattackready", "TownsFolkBoyAttackReady") -- TOWNSFOLKBOY.scr:129
    -- Monitoring this with no function will keep the AI from looking for players
    ctx:command("onfoundplayer", "") -- TOWNSFOLKBOY.scr:132
    do return ctx:exit("") end -- TOWNSFOLKBOY.scr:134
end

return script
