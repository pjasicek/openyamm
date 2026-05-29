-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NOBLEMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "base.inc" }

-- Nobleman.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
-- Creature type ok to attack bool
script.labels["NoblemanAlert"] = function(ctx)
    -- NOBLEMAN.scr:23
    ctx:getParam(0, "hAlertedBy") -- NOBLEMAN.scr:26
    ctx:state().sAlertName = ctx:object("hAlertedBy"):className() -- NOBLEMAN.scr:27
    if ctx:condition("g_hTarget == NULL") then -- NOBLEMAN.scr:29
        -- Check to see if the alert came from a NPC
        if ctx:condition("sAlertName == TownsFolkFemale") then -- NOBLEMAN.scr:31
            ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:32
        end -- NOBLEMAN.scr:33
        if ctx:condition("sAlertName == Nobleman") then -- NOBLEMAN.scr:35
            ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:36
        end -- NOBLEMAN.scr:37
        if ctx:condition("sAlertName == TownsFolkGirl") then -- NOBLEMAN.scr:39
            ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:40
        end -- NOBLEMAN.scr:41
        if ctx:condition("sAlertName == TownsFolkMale") then -- NOBLEMAN.scr:43
            ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:44
        end -- NOBLEMAN.scr:45
    end -- NOBLEMAN.scr:47
    if ctx:condition("g_bOkAttackType == TRUE") then -- NOBLEMAN.scr:49
        ctx:getParam(1, "g_hTarget") -- NOBLEMAN.scr:50
        ctx:self():setTarget(ctx:object("g_hTarget")) -- NOBLEMAN.scr:51
        mm9.gosub(script, ctx, "BaseGoGetHim") -- NOBLEMAN.scr:52
    end -- NOBLEMAN.scr:53
    do return ctx:exit("") end -- NOBLEMAN.scr:55
end

script.labels["NoblemanAttackReady"] = function(ctx)
    -- NOBLEMAN.scr:58
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:state().sAlertName = ctx:object("g_hTarget"):className() -- NOBLEMAN.scr:64
    if ctx:condition("sAlertName == TownsFolkBoy") then -- NOBLEMAN.scr:65
        ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:66
    end -- NOBLEMAN.scr:67
    if ctx:condition("sAlertName == TownsFolkGirl") then -- NOBLEMAN.scr:69
        ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:70
    end -- NOBLEMAN.scr:71
    if ctx:condition("sAlertName == TownsFolkMale") then -- NOBLEMAN.scr:73
        ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:74
    end -- NOBLEMAN.scr:75
    if ctx:condition("sAlertName == TownsFolkFemale") then -- NOBLEMAN.scr:77
        ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:78
    end -- NOBLEMAN.scr:79
    if ctx:condition("sAlertName == TownsFolkFemale") then -- NOBLEMAN.scr:81
        ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:82
    end -- NOBLEMAN.scr:83
    if ctx:condition("sAlertName == Nobleman") then -- NOBLEMAN.scr:85
        ctx:state().g_bOkAttackType = 1 -- NOBLEMAN.scr:86
    end -- NOBLEMAN.scr:87
    ctx:state().g_bFighting = true -- NOBLEMAN.scr:89
    ctx:getTime("g_nLastAttackTime") -- NOBLEMAN.scr:91
    ctx:self():attack() -- NOBLEMAN.scr:93
    do return ctx:exit("") end -- NOBLEMAN.scr:95
end

script.labels["InitNobleman"] = function(ctx)
    -- NOBLEMAN.scr:99
    -- Set NPC wander distance
    ctx:getParam(1, "g_nDistance") -- NOBLEMAN.scr:102
    if ctx:condition("g_nDistance != 0") then -- NOBLEMAN.scr:104
        ctx:set("MAX_DIST_FROM_STARTPOINT", "g_nDistance") -- NOBLEMAN.scr:105
    else -- NOBLEMAN.scr:106
        ctx:state().MAX_DIST_FROM_STARTPOINT = 700 -- NOBLEMAN.scr:107
    end -- NOBLEMAN.scr:108
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:state().g_IdleFrequency = 4 -- NOBLEMAN.scr:111
    -- Set max time in seconds before idle check
    ctx:state().g_IdleCheckMin = 7 -- NOBLEMAN.scr:114
    ctx:state().g_IdleCheckMax = 7 -- NOBLEMAN.scr:115
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:state().g_SpecialAnimFrequency = 0 -- NOBLEMAN.scr:118
    do return ctx:exit("") end -- NOBLEMAN.scr:120
end

script.labels["Main"] = function(ctx)
    -- NOBLEMAN.scr:124
    -- Initialize boys behavior
    mm9.gosub(script, ctx, "InitNobleman") -- NOBLEMAN.scr:127
    -- Initialize attack behavior
    mm9.gosub(script, ctx, "InitBase") -- NOBLEMAN.scr:130
    -- Initialize wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- NOBLEMAN.scr:133
    -- Override these Base Calls
    ctx:onEvent("OnAlert", "NoblemanAlert") -- NOBLEMAN.scr:136
    ctx:onEvent("OnAttackReady", "NoblemanAttackReady") -- NOBLEMAN.scr:137
    -- Monitoring this with no function will keep the AI from looking for players
    ctx:onEvent("OnFoundPlayer") -- NOBLEMAN.scr:140
    do return ctx:exit("") end -- NOBLEMAN.scr:142
end

return script
