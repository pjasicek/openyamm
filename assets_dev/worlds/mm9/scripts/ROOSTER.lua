-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ROOSTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "base.inc" }

-- rooster.scr
-- John Machin
-- Script to handle Rooster behavior
-- Passed in Parameter to get Wander distance
-- Creature type ok to attack bool
script.labels["RoosterAlert"] = function(ctx)
    -- ROOSTER.scr:24
    ctx:getParam(0, "hAlertedBy") -- ROOSTER.scr:27
    ctx:state().sAlertName = ctx:object("hAlertedBy"):className() -- ROOSTER.scr:28
    if ctx:condition("g_hTarget == NULL") then -- ROOSTER.scr:30
        -- Check to see if the alert came from a hen or another rooster
        if ctx:condition("sAlertName == Hen") then -- ROOSTER.scr:32
            ctx:state().g_bOkAttackType = 1 -- ROOSTER.scr:33
        end -- ROOSTER.scr:34
        if ctx:condition("sAlertName == Rooster") then -- ROOSTER.scr:36
            ctx:state().g_bOkAttackType = 1 -- ROOSTER.scr:37
        end -- ROOSTER.scr:38
    end -- ROOSTER.scr:39
    if ctx:condition("g_bOkAttackType == TRUE") then -- ROOSTER.scr:41
        ctx:getParam(1, "g_hTarget") -- ROOSTER.scr:42
        ctx:self():setTarget(ctx:object("g_hTarget")) -- ROOSTER.scr:43
        mm9.gosub(script, ctx, "BaseGoGetHim") -- ROOSTER.scr:44
    end -- ROOSTER.scr:45
    do return ctx:exit("") end -- ROOSTER.scr:47
end

script.labels["InitRooster"] = function(ctx)
    -- ROOSTER.scr:52
    -- Set Rooster wander distance
    ctx:getParam(1, "g_nDistance") -- ROOSTER.scr:56
    if ctx:condition("g_nDistance != 0") then -- ROOSTER.scr:58
        ctx:set("MAX_DIST_FROM_STARTPOINT", "g_nDistance") -- ROOSTER.scr:59
    else -- ROOSTER.scr:60
        ctx:state().MAX_DIST_FROM_STARTPOINT = 350 -- ROOSTER.scr:61
    end -- ROOSTER.scr:62
    -- Set how often we stop at an obstacle
    ctx:state().g_nStopAtObstacle = 2 -- ROOSTER.scr:65
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:state().g_IdleFrequency = 7 -- ROOSTER.scr:68
    -- Set max time in seconds before idle check
    ctx:state().g_IdleCheckMin = 7 -- ROOSTER.scr:71
    ctx:state().g_IdleCheckMax = 7 -- ROOSTER.scr:72
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:state().g_SpecialAnimFrequency = 0 -- ROOSTER.scr:75
    do return ctx:exit("") end -- ROOSTER.scr:77
end

script.labels["RoosterAttackReady"] = function(ctx)
    -- ROOSTER.scr:80
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:state().sAlertName = ctx:object("g_hTarget"):className() -- ROOSTER.scr:87
    if ctx:condition("sAlertName == Rooster") then -- ROOSTER.scr:88
        do return ctx:exit("") end -- ROOSTER.scr:89
    end -- ROOSTER.scr:90
    ctx:state().g_bFighting = true -- ROOSTER.scr:92
    ctx:getTime("g_nLastAttackTime") -- ROOSTER.scr:94
    ctx:self():attack() -- ROOSTER.scr:96
    do return ctx:exit("") end -- ROOSTER.scr:98
end

script.labels["Main"] = function(ctx)
    -- ROOSTER.scr:101
    -- Initialize Rooster Behavior
    mm9.gosub(script, ctx, "InitRooster") -- ROOSTER.scr:106
    -- Initialize Rooster Attack Behavior
    mm9.gosub(script, ctx, "InitBase") -- ROOSTER.scr:109
    -- Initialize Rooster Wandering
    mm9.gosub(script, ctx, "WanderInit") -- ROOSTER.scr:112
    -- Override these Base Calls
    ctx:onEvent("OnAlert", "RoosterAlert") -- ROOSTER.scr:115
    ctx:onEvent("OnAttackReady", "RoosterAttackReady") -- ROOSTER.scr:116
    -- Monitoring this with no function will keep the AI from looking for players
    ctx:onEvent("OnFoundPlayer") -- ROOSTER.scr:119
    do return ctx:exit("") end -- ROOSTER.scr:121
end

return script
