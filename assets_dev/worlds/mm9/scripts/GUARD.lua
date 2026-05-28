-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "base.inc" }

-- guard.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
-- Creature type ok to attack bool
script.labels["guardAlert"] = function(ctx)
    -- GUARD.scr:23
    ctx:getParam(0, "hAlertedBy") -- GUARD.scr:26
    ctx:command("getclassname", "hAlertedBy, sAlertName") -- GUARD.scr:27
    if ctx:condition("g_hTarget == NULL") then -- GUARD.scr:29
        -- Check to see if the alert came from a NPC
        if ctx:condition("sAlertName == TownsFolkFemale") then -- GUARD.scr:31
            ctx:command("set", "g_bOkAttackType, 1") -- GUARD.scr:32
        end -- GUARD.scr:33
        if ctx:condition("sAlertName == guard") then -- GUARD.scr:35
            ctx:command("set", "g_bOkAttackType, 1") -- GUARD.scr:36
        end -- GUARD.scr:37
        if ctx:condition("sAlertName == TownsFolkGirl") then -- GUARD.scr:39
            ctx:command("set", "g_bOkAttackType, 1") -- GUARD.scr:40
        end -- GUARD.scr:41
        if ctx:condition("sAlertName == TownsFolkMale") then -- GUARD.scr:43
            ctx:command("set", "g_bOkAttackType, 1") -- GUARD.scr:44
        end -- GUARD.scr:45
        if ctx:condition("sAlertName == Guard") then -- GUARD.scr:47
            ctx:command("set", "g_bOKAttackType, 1") -- GUARD.scr:48
        end -- GUARD.scr:49
    end -- GUARD.scr:51
    if ctx:condition("g_bOkAttackType == TRUE") then -- GUARD.scr:53
        ctx:getParam(1, "g_hTarget") -- GUARD.scr:54
        ctx:command("target", "g_hTarget") -- GUARD.scr:55
        mm9.gosub(script, ctx, "BaseGoGetHim") -- GUARD.scr:56
    end -- GUARD.scr:57
    do return ctx:exit("") end -- GUARD.scr:59
end

script.labels["guardAttackReady"] = function(ctx)
    -- GUARD.scr:62
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("getclassname", "g_hTarget, sAlertName") -- GUARD.scr:68
    if ctx:condition("sAlertName == guard") then -- GUARD.scr:69
        do return ctx:exit("") end -- GUARD.scr:70
    end -- GUARD.scr:71
    if ctx:condition("sAlertName == TownsFolkGirl") then -- GUARD.scr:73
        do return ctx:exit("") end -- GUARD.scr:74
    end -- GUARD.scr:75
    if ctx:condition("sAlertName == TownsFolkMale") then -- GUARD.scr:77
        do return ctx:exit("") end -- GUARD.scr:78
    end -- GUARD.scr:79
    if ctx:condition("sAlertName == TownsFolkFemale") then -- GUARD.scr:81
        do return ctx:exit("") end -- GUARD.scr:82
    end -- GUARD.scr:83
    ctx:command("set", "g_bFighting, TRUE") -- GUARD.scr:85
    ctx:command("gettime", "g_nLastAttackTime") -- GUARD.scr:87
    ctx:command("attack", "") -- GUARD.scr:89
    do return ctx:exit("") end -- GUARD.scr:91
end

script.labels["Initguard"] = function(ctx)
    -- GUARD.scr:95
    -- Set NPC wander distance
    ctx:getParam(1, "g_nDistance") -- GUARD.scr:98
    if ctx:condition("g_nDistance != 0") then -- GUARD.scr:100
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- GUARD.scr:101
    else -- GUARD.scr:102
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 700") -- GUARD.scr:103
    end -- GUARD.scr:104
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 4") -- GUARD.scr:107
    -- Set max time in seconds before idle check
    ctx:command("set", "g_IdleCheckMin, 7") -- GUARD.scr:110
    ctx:command("set", "g_IdleCheckMax, 7") -- GUARD.scr:111
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 0") -- GUARD.scr:114
    do return ctx:exit("") end -- GUARD.scr:116
end

script.labels["Main"] = function(ctx)
    -- GUARD.scr:120
    -- Initialize boys behavior
    mm9.gosub(script, ctx, "Initguard") -- GUARD.scr:123
    -- Initialize attack behavior
    mm9.gosub(script, ctx, "InitBase") -- GUARD.scr:126
    -- Initialize wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- GUARD.scr:129
    -- Override these Base Calls
    ctx:command("onalert", "guardAlert") -- GUARD.scr:132
    ctx:command("onattackready", "guardAttackReady") -- GUARD.scr:133
    -- Monitoring this with no function will keep the AI from looking for players
    ctx:command("onfoundplayer", "") -- GUARD.scr:136
    do return ctx:exit("") end -- GUARD.scr:138
end

return script
