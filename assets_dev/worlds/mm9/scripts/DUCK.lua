-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DUCK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- duck.scr
-- John Machin
-- Default script for wanderers
-- Passed in Parameter to get Wander distance
script.labels["HandleOnAlert"] = function(ctx)
    -- DUCK.scr:24
    ctx:getParam(0, "hAlertedBy") -- DUCK.scr:27
    ctx:state().sAlertName = ctx:object("hAlertedBy"):className() -- DUCK.scr:28
    do return ctx:exit("") end -- DUCK.scr:30
end

script.labels["OnRun"] = function(ctx)
    -- DUCK.scr:33
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:object("hAttacker"):rotation() -- DUCK.scr:36
    -- CalcDist g_posX,g_posY,g_posZ,g_startX,g_startY,g_startZ,g_dist
    -- if (g_dist>MAX_DIST_FROM_STARTPOINT)
    -- Too far away from original starting point!!
    -- FacePos g_startX, g_startY, g_startZ, 180
    -- endif
    ctx:self():faceDir("g_PosX", "g_PosY", "g_PosZ") -- DUCK.scr:44
    -- This will cause a more erratic running behavior
    ctx:state().g_IdleCheckMin = 1 -- DUCK.scr:47
    ctx:state().g_IdleCheckMax = 1 -- DUCK.scr:48
    -- Set turn degree min max for more erratic movement
    ctx:state().g_TurnDegreeMin = 60 -- DUCK.scr:51
    ctx:state().g_TurnDegreeMax = 90 -- DUCK.scr:52
    ctx:self():run() -- DUCK.scr:54
    ctx:state().g_IsRunning = true -- DUCK.scr:56
    do return ctx:exit("") end -- DUCK.scr:58
end

script.labels["OnRunning"] = function(ctx)
    -- DUCK.scr:61
    -- We want to continue sending Alerts to nearby AI while running
    ctx:self():sendAlert(ctx:object("hAttacker")) -- DUCK.scr:64
    do return ctx:exit("") end -- DUCK.scr:66
end

script.labels["OnStopRunning"] = function(ctx)
    -- DUCK.scr:69
    -- Setup our stuff back to normal
    ctx:state().g_IdleCheckMin = 7 -- DUCK.scr:72
    ctx:state().g_IdleCheckMax = 7 -- DUCK.scr:73
    ctx:state().g_TurnDegreeMin = 15 -- DUCK.scr:75
    ctx:state().g_TurnDegreeMax = 90 -- DUCK.scr:76
    ctx:state().g_IsRunning = false -- DUCK.scr:78
    do return ctx:exit("") end -- DUCK.scr:80
end

script.labels["DuckOnDamage"] = function(ctx)
    -- DUCK.scr:83
    -- Figure out who hit us
    ctx:getParam(0, "hAttacker") -- DUCK.scr:86
    -- Get last dmg done
    ctx:getParam(1, "g_nLastDamage") -- DUCK.scr:89
    -- Alert nearby AI
    ctx:self():sendAlert(ctx:object("hAttacker")) -- DUCK.scr:92
    ctx:getTime("g_StopRunTime") -- DUCK.scr:94
    ctx:state().g_StopRunTime = (tonumber(ctx:state().g_StopRunTime) or 0) + 15 -- DUCK.scr:95
    if ctx:condition("g_nLastDamage == 0") then -- DUCK.scr:97
        mm9.gosub(script, ctx, "DuckOnDamageDone") -- DUCK.scr:98
    end -- DUCK.scr:99
    do return ctx:exit("FALSE") end -- DUCK.scr:101
end

script.labels["DuckOnDamageDone"] = function(ctx)
    -- DUCK.scr:105
    mm9.gosub(script, ctx, "OnRun") -- DUCK.scr:107
    do return ctx:exit("") end -- DUCK.scr:109
end

script.labels["InitDuck"] = function(ctx)
    -- DUCK.scr:112
    -- Set Rooster wander distance
    ctx:getParam(1, "g_nDistance") -- DUCK.scr:115
    if ctx:condition("g_nDistance != 0") then -- DUCK.scr:117
        ctx:set("MAX_DIST_FROM_STARTPOINT", "g_nDistance") -- DUCK.scr:118
    else -- DUCK.scr:119
        ctx:state().MAX_DIST_FROM_STARTPOINT = 350 -- DUCK.scr:120
    end -- DUCK.scr:121
    -- Set how often we stop at an obstacle
    ctx:state().g_nStopAtObstacle = 2 -- DUCK.scr:124
    -- Set how often we idle 1 equals 10% valid numbers are 1 to 10
    ctx:state().g_IdleFrequency = 4 -- DUCK.scr:127
    -- Set max time in seconds before idle check
    ctx:state().g_IdleCheckMin = 7 -- DUCK.scr:130
    ctx:state().g_IdleCheckMax = 7 -- DUCK.scr:131
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:state().g_SpecialAnimFrequency = 0 -- DUCK.scr:134
    do return ctx:exit("") end -- DUCK.scr:136
end

script.labels["Main"] = function(ctx)
    -- DUCK.scr:139
    -- Monitor these callbacks
    ctx:onEvent("OnDamage", "DuckOnDamage") -- DUCK.scr:143
    ctx:onEvent("OnDamageDone", "DuckOnDamageDone") -- DUCK.scr:144
    -- Setup wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- DUCK.scr:147
    do return ctx:exit("") end -- DUCK.scr:149
end

return script
