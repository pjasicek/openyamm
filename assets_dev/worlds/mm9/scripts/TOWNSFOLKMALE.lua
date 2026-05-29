-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TOWNSFOLKMALE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "base.inc" }

-- townsfolkmale.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
-- Creature type ok to attack bool
script.labels["townsfolkmaleAlert"] = function(ctx)
    -- TOWNSFOLKMALE.scr:23
    ctx:getParam(0, "hAlertedBy") -- TOWNSFOLKMALE.scr:26
    ctx:state().sAlertName = ctx:object("hAlertedBy"):className() -- TOWNSFOLKMALE.scr:27
    if ctx:condition("g_hTarget == NULL") then -- TOWNSFOLKMALE.scr:29
        -- Check to see if the alert came from a NPC
        if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKMALE.scr:31
            ctx:state().g_bOkAttackType = 1 -- TOWNSFOLKMALE.scr:32
        end -- TOWNSFOLKMALE.scr:33
        if ctx:condition("sAlertName == townsfolkmale") then -- TOWNSFOLKMALE.scr:35
            ctx:state().g_bOkAttackType = 1 -- TOWNSFOLKMALE.scr:36
        end -- TOWNSFOLKMALE.scr:37
        if ctx:condition("sAlertName == TownsFolkGirl") then -- TOWNSFOLKMALE.scr:39
            ctx:state().g_bOkAttackType = 1 -- TOWNSFOLKMALE.scr:40
        end -- TOWNSFOLKMALE.scr:41
        if ctx:condition("sAlertName == TownsFolkMale") then -- TOWNSFOLKMALE.scr:43
            ctx:state().g_bOkAttackType = 1 -- TOWNSFOLKMALE.scr:44
        end -- TOWNSFOLKMALE.scr:45
    end -- TOWNSFOLKMALE.scr:47
    if ctx:condition("g_bOkAttackType == TRUE") then -- TOWNSFOLKMALE.scr:49
        ctx:getParam(1, "g_hTarget") -- TOWNSFOLKMALE.scr:50
        ctx:self():setTarget(ctx:object("g_hTarget")) -- TOWNSFOLKMALE.scr:51
        mm9.gosub(script, ctx, "BaseGoGetHim") -- TOWNSFOLKMALE.scr:52
    end -- TOWNSFOLKMALE.scr:53
    do return ctx:exit("") end -- TOWNSFOLKMALE.scr:55
end

script.labels["townsfolkmaleAttackReady"] = function(ctx)
    -- TOWNSFOLKMALE.scr:58
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:state().sAlertName = ctx:object("g_hTarget"):className() -- TOWNSFOLKMALE.scr:64
    if ctx:condition("sAlertName == townsfolkmale") then -- TOWNSFOLKMALE.scr:65
        do return ctx:exit("") end -- TOWNSFOLKMALE.scr:66
    end -- TOWNSFOLKMALE.scr:67
    if ctx:condition("sAlertName == TownsFolkGirl") then -- TOWNSFOLKMALE.scr:69
        do return ctx:exit("") end -- TOWNSFOLKMALE.scr:70
    end -- TOWNSFOLKMALE.scr:71
    if ctx:condition("sAlertName == TownsFolkMale") then -- TOWNSFOLKMALE.scr:73
        do return ctx:exit("") end -- TOWNSFOLKMALE.scr:74
    end -- TOWNSFOLKMALE.scr:75
    if ctx:condition("sAlertName == TownsFolkFemale") then -- TOWNSFOLKMALE.scr:77
        do return ctx:exit("") end -- TOWNSFOLKMALE.scr:78
    end -- TOWNSFOLKMALE.scr:79
    ctx:state().g_bFighting = true -- TOWNSFOLKMALE.scr:81
    ctx:getTime("g_nLastAttackTime") -- TOWNSFOLKMALE.scr:83
    ctx:self():attack() -- TOWNSFOLKMALE.scr:85
    do return ctx:exit("") end -- TOWNSFOLKMALE.scr:87
end

script.labels["Inittownsfolkmale"] = function(ctx)
    -- TOWNSFOLKMALE.scr:91
    -- Set NPC wander distance
    ctx:getParam(1, "g_nDistance") -- TOWNSFOLKMALE.scr:94
    if ctx:condition("g_nDistance != 0") then -- TOWNSFOLKMALE.scr:96
        ctx:set("MAX_DIST_FROM_STARTPOINT", "g_nDistance") -- TOWNSFOLKMALE.scr:97
    else -- TOWNSFOLKMALE.scr:98
        ctx:state().MAX_DIST_FROM_STARTPOINT = 700 -- TOWNSFOLKMALE.scr:99
    end -- TOWNSFOLKMALE.scr:100
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:state().g_IdleFrequency = 4 -- TOWNSFOLKMALE.scr:103
    -- Set max time in seconds before idle check
    ctx:state().g_IdleCheckMin = 7 -- TOWNSFOLKMALE.scr:106
    ctx:state().g_IdleCheckMax = 7 -- TOWNSFOLKMALE.scr:107
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:state().g_SpecialAnimFrequency = 0 -- TOWNSFOLKMALE.scr:110
    do return ctx:exit("") end -- TOWNSFOLKMALE.scr:112
end

script.labels["Main"] = function(ctx)
    -- TOWNSFOLKMALE.scr:116
    -- Initialize boys behavior
    mm9.gosub(script, ctx, "Inittownsfolkmale") -- TOWNSFOLKMALE.scr:119
    -- Initialize attack behavior
    mm9.gosub(script, ctx, "InitBase") -- TOWNSFOLKMALE.scr:122
    -- Initialize wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- TOWNSFOLKMALE.scr:125
    -- Override these Base Calls
    ctx:onEvent("OnAlert", "townsfolkmaleAlert") -- TOWNSFOLKMALE.scr:128
    ctx:onEvent("OnAttackReady", "townsfolkmaleAttackReady") -- TOWNSFOLKMALE.scr:129
    -- Monitoring this with no function will keep the AI from looking for players
    ctx:onEvent("OnFoundPlayer") -- TOWNSFOLKMALE.scr:132
    do return ctx:exit("") end -- TOWNSFOLKMALE.scr:134
end

return script
