-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PRIEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }

-- Priest.scr
-- John Machin
-- Default script for wanderers
script.labels["DoNothing"] = function(ctx)
    -- PRIEST.scr:20
    -- Do nothing here...
    do return ctx:exit("") end -- PRIEST.scr:24
end

script.labels["OnRun"] = function(ctx)
    -- PRIEST.scr:27
    -- Get direction of player face that way and RUN!
    ctx:command("getfacedir", "hAttacker, g_posX, g_posY, g_posZ") -- PRIEST.scr:31
    ctx:command("facedir", "g_PosX, g_PosY, g_PosZ") -- PRIEST.scr:32
    -- This will cause a more erratic running behavior
    ctx:command("set", "g_IdleCheckMin, 1") -- PRIEST.scr:35
    ctx:command("set", "g_IdleCheckMax, 1") -- PRIEST.scr:36
    -- Set turn degree min max for more erratic movement
    ctx:command("set", "g_TurnDegreeMin, 60") -- PRIEST.scr:39
    ctx:command("set", "g_TurnDegreeMax, 90") -- PRIEST.scr:40
    ctx:command("run", "") -- PRIEST.scr:42
    ctx:command("set", "g_IsRunning, TRUE") -- PRIEST.scr:44
    do return ctx:exit("") end -- PRIEST.scr:46
end

script.labels["OnRunning"] = function(ctx)
    -- PRIEST.scr:49
    -- We want to continue sending Alerts to nearby AI while running
    ctx:command("sendalert", "hAttacker") -- PRIEST.scr:52
    do return ctx:exit("") end -- PRIEST.scr:54
end

script.labels["OnStopRunning"] = function(ctx)
    -- PRIEST.scr:57
    -- Setup our stuff back to normal
    ctx:command("set", "g_IdleCheckMin, 2") -- PRIEST.scr:60
    ctx:command("set", "g_IdleCheckMax, 6") -- PRIEST.scr:61
    ctx:command("set", "g_TurnDegreeMin 15") -- PRIEST.scr:63
    ctx:command("set", "g_TurnDegreeMax 90") -- PRIEST.scr:64
    ctx:command("set", "g_IsRunning, FALSE") -- PRIEST.scr:66
    do return ctx:exit("") end -- PRIEST.scr:68
end

script.labels["PriestOnDamage"] = function(ctx)
    -- PRIEST.scr:71
    -- Figure out who hit us
    ctx:getParam(0, "hAttacker") -- PRIEST.scr:75
    -- Get last dmg done
    ctx:getParam(1, "g_nLastDamage") -- PRIEST.scr:78
    -- Alert nearby AI
    ctx:command("sendalert", "hAttacker") -- PRIEST.scr:81
    ctx:command("gettime", "g_StopRunTime") -- PRIEST.scr:83
    ctx:command("add", "g_StopRunTime, 15") -- PRIEST.scr:84
    if ctx:condition("g_nLastDamage == 0") then -- PRIEST.scr:86
        mm9.gosub(script, ctx, "PriestOnDamageDone") -- PRIEST.scr:87
    end -- PRIEST.scr:88
    do return ctx:exit("FALSE") end -- PRIEST.scr:90
end

script.labels["PriestOnDamageDone"] = function(ctx)
    -- PRIEST.scr:93
    mm9.gosub(script, ctx, "OnRun") -- PRIEST.scr:95
    do return ctx:exit("") end -- PRIEST.scr:97
end

script.labels["InitPriest"] = function(ctx)
    -- PRIEST.scr:100
    -- Set the NPCs roaming distance
    ctx:getParam(1, "g_nDistance") -- PRIEST.scr:103
    if ctx:condition("g_nDistance != 0") then -- PRIEST.scr:105
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- PRIEST.scr:106
    else -- PRIEST.scr:107
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 350") -- PRIEST.scr:108
    end -- PRIEST.scr:109
    -- Set how often the NPC is idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 8") -- PRIEST.scr:112
    -- Set max time in seconds before idle check
    ctx:command("set", "g_IdleCheckMin, 5") -- PRIEST.scr:115
    ctx:command("set", "g_IdleCheckMax, 10") -- PRIEST.scr:116
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 0") -- PRIEST.scr:119
    do return ctx:exit("") end -- PRIEST.scr:121
end

script.labels["Main"] = function(ctx)
    -- PRIEST.scr:125
    -- Initialize priest
    mm9.gosub(script, ctx, "InitPriest") -- PRIEST.scr:129
    -- Initialize Wandering Behavior
    mm9.gosub(script, ctx, "WanderInit") -- PRIEST.scr:132
    -- Monitor these callbacks
    ctx:command("ondamage", "PriestOnDamage") -- PRIEST.scr:135
    ctx:command("ondamagedone", "PriestOnDamageDone") -- PRIEST.scr:136
    -- Handle these triggers
    ctx:addTrigger("StopRunning", "OnStopRunning") -- PRIEST.scr:139
    ctx:addTrigger("Running", "OnRunning") -- PRIEST.scr:140
    do return ctx:exit("") end -- PRIEST.scr:142
end

return script
