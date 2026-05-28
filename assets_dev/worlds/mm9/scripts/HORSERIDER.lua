-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HORSERIDER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "base.inc" }

-- horserider.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
-- Creature type ok to attack bool
-- NOTE:
-- I am leaving the attack stuff in here and have it commented out.  Currently this
-- model only has a walking animation.  Leaving just in case they add attack anims in
-- the future
script.labels["InitHorseRider"] = function(ctx)
    -- HORSERIDER.scr:30
    -- Set Rooster wander distance
    ctx:getParam(1, "g_nDistance") -- HORSERIDER.scr:33
    if ctx:condition("g_nDistance != 0") then -- HORSERIDER.scr:35
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- HORSERIDER.scr:36
    else -- HORSERIDER.scr:37
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 350") -- HORSERIDER.scr:38
    end -- HORSERIDER.scr:39
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 0") -- HORSERIDER.scr:42
    -- Set max time in seconds before idle check
    -- Set g_IdleCheckMin, 5
    -- Set g_IdleCheckMax, 10
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 3") -- HORSERIDER.scr:49
    do return ctx:exit("") end -- HORSERIDER.scr:51
end

script.labels["HorseRiderAttackReady"] = function(ctx)
    -- HORSERIDER.scr:54
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("getclassname", "g_hTarget, sAlertName") -- HORSERIDER.scr:61
    if ctx:condition("sAlertName == HorseRider") then -- HORSERIDER.scr:62
        do return ctx:exit("") end -- HORSERIDER.scr:63
    end -- HORSERIDER.scr:64
    ctx:command("set", "g_bFighting, TRUE") -- HORSERIDER.scr:66
    ctx:command("gettime", "g_nLastAttackTime") -- HORSERIDER.scr:68
    ctx:command("attack", "") -- HORSERIDER.scr:70
    do return ctx:exit("") end -- HORSERIDER.scr:72
end

script.labels["HorseRiderAlert"] = function(ctx)
    -- HORSERIDER.scr:75
    ctx:getParam(0, "hAlertedBy") -- HORSERIDER.scr:78
    ctx:command("getclassname", "hAlertedBy, sAlertName") -- HORSERIDER.scr:79
    if ctx:condition("g_hTarget == NULL") then -- HORSERIDER.scr:81
        -- Check to see if the alert came from a hen or another rooster
        if ctx:condition("sAlertName == HorseRider") then -- HORSERIDER.scr:83
            ctx:command("set", "g_bOkAttackType, 1") -- HORSERIDER.scr:84
        end -- HORSERIDER.scr:85
    end -- HORSERIDER.scr:86
    if ctx:condition("g_bOkAttackType == TRUE") then -- HORSERIDER.scr:88
        ctx:getParam(1, "g_hTarget") -- HORSERIDER.scr:89
        ctx:command("target", "g_hTarget") -- HORSERIDER.scr:90
        mm9.gosub(script, ctx, "BaseGoGetHim") -- HORSERIDER.scr:91
    end -- HORSERIDER.scr:92
    do return ctx:exit("") end -- HORSERIDER.scr:94
end

script.labels["Main"] = function(ctx)
    -- HORSERIDER.scr:99
    -- Initialize Horserider
    mm9.gosub(script, ctx, "InitHorseRider") -- HORSERIDER.scr:103
    -- Initialize Attack Behavior
    -- gosub InitBase
    -- Initialize Wander Behavior
    mm9.gosub(script, ctx, "WanderInit") -- HORSERIDER.scr:109
    -- Override these Base Calls
    ctx:command("onalert", "HorseRiderAlert") -- HORSERIDER.scr:112
    ctx:command("onattackready", "HorseRiderAttackReady") -- HORSERIDER.scr:113
    -- Monitoring this with no function will keep the AI from looking for players
    ctx:command("onfoundplayer", "") -- HORSERIDER.scr:116
    do return ctx:exit("") end -- HORSERIDER.scr:120
end

return script
