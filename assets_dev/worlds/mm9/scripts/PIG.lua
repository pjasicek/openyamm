-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PIG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }

-- pig.scr
-- John Machin
-- Default script for wanderers
script.labels["OnSpecial"] = function(ctx)
    -- PIG.scr:17
    -- GetRandomInt 1, 10, g_nRandom
    -- LoopAnim sit, g_nRandom, OnSpecialDone
    if ctx:condition("g_nRandom < 3") then -- PIG.scr:21
        -- We will sit and rest
        ctx:command("playanim", "Standdown, OnStandDownRestDone") -- PIG.scr:23
    else -- PIG.scr:24
        ctx:command("playanim", "Standdown, OnStandDownRollDone") -- PIG.scr:25
    end -- PIG.scr:26
    do return ctx:exit("") end -- PIG.scr:28
end

script.labels["OnStandDownRestDone"] = function(ctx)
    -- PIG.scr:31
    ctx:command("getrandomint", "9, 15, g_nRandom") -- PIG.scr:33
    ctx:command("loopanim", "Rest, g_nRandom, OnDownDone") -- PIG.scr:34
    ctx:command("wait", "0, 0, DoNothing") -- PIG.scr:36
    do return ctx:exit("") end -- PIG.scr:38
end

script.labels["OnStandDownRollDone"] = function(ctx)
    -- PIG.scr:41
    ctx:command("loopanim", "Roll, 4, OnDownRoll2Done") -- PIG.scr:43
    ctx:command("wait", "0, 0, DoNothing") -- PIG.scr:45
    do return ctx:exit("") end -- PIG.scr:47
end

script.labels["OnDownRoll2Done"] = function(ctx)
    -- PIG.scr:50
    ctx:command("getrandomint", "9, 15, g_nRandom") -- PIG.scr:52
    ctx:command("loopanim", "Rest, g_nRandom, OnDownDone") -- PIG.scr:53
    ctx:command("wait", "0, 0, DoNothing") -- PIG.scr:55
    do return ctx:exit("") end -- PIG.scr:57
end

script.labels["OnDownDone"] = function(ctx)
    -- PIG.scr:60
    ctx:command("playanim", "Standup") -- PIG.scr:62
    ctx:command("wait", "0, 1, WanderTick") -- PIG.scr:64
    do return ctx:exit("") end -- PIG.scr:66
end

script.labels["DoNothing"] = function(ctx)
    -- PIG.scr:70
    -- Nothing to see here
    do return ctx:exit("") end -- PIG.scr:74
end

script.labels["OnRun"] = function(ctx)
    -- PIG.scr:77
    ctx:command("getfacedir", "hAttacker, g_posX, g_posY, g_posZ") -- PIG.scr:80
    ctx:command("facedir", "g_PosX, g_PosY, g_PosZ") -- PIG.scr:82
    ctx:command("run", "") -- PIG.scr:84
    ctx:command("set", "g_IsRunning, TRUE") -- PIG.scr:86
    -- This will cause a more erratic runniing behavior
    ctx:command("set", "g_IdleCheckMin, 1") -- PIG.scr:88
    ctx:command("set", "g_IdleCheckMax, 1") -- PIG.scr:89
    -- Set turn degree min max for more erratic movement
    -- Set g_TurnDegreeMin, 40
    -- Set g_TurnDegreeMax, 90
    do return ctx:exit("") end -- PIG.scr:95
end

script.labels["OnRunning"] = function(ctx)
    -- PIG.scr:98
    -- We want to continue sending Alerts to nearby AI while running
    ctx:command("sendalert", "hAttacker") -- PIG.scr:101
    do return ctx:exit("") end -- PIG.scr:103
end

script.labels["OnStopRunning"] = function(ctx)
    -- PIG.scr:107
    -- Setup our stuff back to normal
    ctx:command("set", "g_IdleCheckMin, 7") -- PIG.scr:110
    ctx:command("set", "g_IdleCheckMax, 7") -- PIG.scr:111
    ctx:command("set", "g_TurnDegreeMin 15") -- PIG.scr:113
    ctx:command("set", "g_TurnDegreeMax 90") -- PIG.scr:114
    ctx:command("set", "g_IsRunning, FALSE") -- PIG.scr:116
    do return ctx:exit("") end -- PIG.scr:118
end

script.labels["PigOnDamage"] = function(ctx)
    -- PIG.scr:121
    -- Figure out who hit us
    ctx:getParam(0, "hAttacker") -- PIG.scr:124
    -- Get last damage done
    ctx:getParam(1, "g_nLastDamage") -- PIG.scr:127
    -- Alert nearby AI
    ctx:command("sendalert", "hAttacker") -- PIG.scr:130
    ctx:command("gettime", "g_StopRunTime") -- PIG.scr:132
    ctx:command("add", "g_StopRunTime, 15") -- PIG.scr:133
    if ctx:condition("g_nLastDamage == 0") then -- PIG.scr:135
        mm9.gosub(script, ctx, "PigOnDamageDone") -- PIG.scr:136
    end -- PIG.scr:137
    do return ctx:exit("FALSE") end -- PIG.scr:139
end

script.labels["PigOnDamageDone"] = function(ctx)
    -- PIG.scr:143
    mm9.gosub(script, ctx, "OnRun") -- PIG.scr:145
    do return ctx:exit("") end -- PIG.scr:147
end

script.labels["InitPig"] = function(ctx)
    -- PIG.scr:150
    -- Set the hens roaming distance
    ctx:getParam(1, "g_nDistance") -- PIG.scr:153
    if ctx:condition("g_nDistance != 0") then -- PIG.scr:155
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- PIG.scr:156
    else -- PIG.scr:157
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 350") -- PIG.scr:158
    end -- PIG.scr:159
    -- Set how often we stop at obstacle
    ctx:command("set", "g_nStopAtObstacle, 1") -- PIG.scr:162
    -- Set how often hen is idle 1 equals 10%
    ctx:command("set", "g_IdleFrequency, 5") -- PIG.scr:165
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 8") -- PIG.scr:168
    -- Set max time before idle check
    ctx:command("set", "g_IdleCheckMin, 8") -- PIG.scr:171
    ctx:command("set", "g_IdleCheckMax, 8") -- PIG.scr:172
    do return ctx:exit("") end -- PIG.scr:174
end

script.labels["Main"] = function(ctx)
    -- PIG.scr:177
    -- Initialize Pig behavior
    mm9.gosub(script, ctx, "InitPig") -- PIG.scr:180
    -- Initialize wandering behavior
    mm9.gosub(script, ctx, "WanderInit") -- PIG.scr:183
    -- override these callbacks
    ctx:command("ondamagedone", "PigOnDamageDone") -- PIG.scr:186
    ctx:command("ondamage", "PigOnDamage") -- PIG.scr:187
    -- setup these special triggers
    ctx:addTrigger("SpecialAnim", "OnSpecial") -- PIG.scr:190
    ctx:addTrigger("StopRunning", "OnStopRunning") -- PIG.scr:191
    ctx:addTrigger("Running", "OnRunning") -- PIG.scr:192
    do return ctx:exit("") end -- PIG.scr:196
end

return script
