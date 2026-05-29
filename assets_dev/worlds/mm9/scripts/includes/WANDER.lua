-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WANDER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "aiglobals.inc" }

-- Wander.inc
-- Jeff Leggett
-- 2/22/2000
-- Include file used by actors that wander around...
-- Number is a percentage 1 is 10% 2 is 20% ect.
-- Sets the amount of time between idle checks.
-- AI States
-- Turning degree
-- time to see when we were last attacked
-- How fast do you want the ai to turn around when
-- they encounter an obstacle?
-- Farm animals will sometimes stop at obstacless
-- instead of turning
script.labels["WanderObstacle"] = function(ctx)
    -- WANDER.inc:62
    -- p0		- handle to obstacle
    -- p1-3	- Normal of the collision...
    -- For now, just go the opposite direction +- a little..
    -- If we are running just go around
    if ctx:condition("g_IsRunning == TRUE") then -- WANDER.inc:69
        do return mm9.gotoLabel(script, ctx, "GoAroundObstacle") end -- WANDER.inc:70
    else -- WANDER.inc:71
        -- if we are already stopped we go around it
        if ctx:condition("g_bStoppedAtObstacle == TRUE") then -- WANDER.inc:74
            ctx:set("g_rotX", "g_StoppedRotX") -- WANDER.inc:75
            ctx:set("g_rotY", "g_StoppedRotY") -- WANDER.inc:76
            ctx:set("g_rotZ", "g_StoppedRotZ") -- WANDER.inc:77
            do return mm9.gotoLabel(script, ctx, "GoAroundObstacle") end -- WANDER.inc:78
        end -- WANDER.inc:79
        ctx:randomInt(1, 10, "g_nRandom") -- WANDER.inc:81
        if ctx:condition("g_nRandom > g_nStopAtObstacle") then -- WANDER.inc:82
            do return mm9.gotoLabel(script, ctx, "GoAroundObstacle") end -- WANDER.inc:83
        else -- WANDER.inc:84
            -- Save the rotation
            ctx:getParam(1, "g_StoppedRotX") -- WANDER.inc:86
            ctx:getParam(2, "g_StoppedRotY") -- WANDER.inc:87
            ctx:getParam(3, "g_StoppedRotZ") -- WANDER.inc:88
            -- We are stopped so save that off as well
            ctx:state().g_bStoppedAtObstacle = true -- WANDER.inc:91
            ctx:self():stop() -- WANDER.inc:93
        end -- WANDER.inc:94
    end -- WANDER.inc:95
end

script.labels["GoAroundObstacle"] = function(ctx)
    -- WANDER.inc:98
    ctx:state().g_bStoppedAtObstacle = false -- WANDER.inc:99
    ctx:getParam(1, "g_rotX") -- WANDER.inc:101
    ctx:getParam(2, "g_rotY") -- WANDER.inc:102
    ctx:getParam(3, "g_rotZ") -- WANDER.inc:103
    ctx:randomFloat(0.2, 0.6, "g_nRandom") -- WANDER.inc:105
    ctx:randomInt(0, 1, "g_nTemp") -- WANDER.inc:106
    if ctx:condition("g_nTemp==1") then -- WANDER.inc:108
        ctx:state().g_nRandom = (tonumber(ctx:state().g_nRandom) or 0) * -1 -- WANDER.inc:109
    end -- WANDER.inc:110
    ctx:add("g_rotX", "g_nRandom") -- WANDER.inc:112
    ctx:randomFloat(0.2, 0.6, "g_nRandom") -- WANDER.inc:114
    ctx:randomInt(0, 1, "g_nTemp") -- WANDER.inc:115
    if ctx:condition("g_nTemp==1") then -- WANDER.inc:117
        ctx:state().g_nRandom = (tonumber(ctx:state().g_nRandom) or 0) * -1 -- WANDER.inc:118
    end -- WANDER.inc:119
    ctx:add("g_rotZ", "g_nRandom") -- WANDER.inc:121
    ctx:self():faceDir("g_rotX", "g_rotY", "g_rotZ", "g_wanderObstacleRotRate") -- WANDER.inc:123
    if ctx:condition("g_IsRunning == FALSE") then -- WANDER.inc:125
        ctx:self():walk() -- WANDER.inc:126
    else -- WANDER.inc:127
        ctx:self():run() -- WANDER.inc:128
    end -- WANDER.inc:129
    -- Setup next tick
    ctx:randomFloat("g_IdleCheckMin", "g_IdleCheckMax", "g_nRandom") -- WANDER.inc:133
    ctx:wait("WANDER_WAIT_NBR", "g_nRandom", "WanderTick") -- WANDER.inc:134
    do return ctx:exit("TRUE") end -- WANDER.inc:137
end

script.labels["WanderGo"] = function(ctx)
    -- WANDER.inc:140
    -- Picks a direction and goes...
    ctx:randomFloat("g_TurnDegreeMin", "g_TurnDegreeMax", "g_turnDeg") -- WANDER.inc:145
    -- GetRandomFloat 20, 50, g_turnRate
    -- Set g_turnRate, g_turnDeg
    if ctx:condition("g_IsRunning == FALSE") then -- WANDER.inc:150
        ctx:state().g_turnRate = 10 -- WANDER.inc:151
    else -- WANDER.inc:152
        ctx:state().g_turnRate = 45 -- WANDER.inc:153
    end -- WANDER.inc:154
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- WANDER.inc:156
    ctx:state().g_dist = ctx:vecDist("g_posX", "g_posY", "g_posZ", "g_startX", "g_startY", "g_startZ") -- WANDER.inc:158
    if ctx:condition("g_dist>MAX_DIST_FROM_STARTPOINT") then -- WANDER.inc:160
        -- Too far away from original starting point!!
        ctx:self():facePos("g_startX", "g_startY", "g_startZ", 180) -- WANDER.inc:162
    else -- WANDER.inc:163
        ctx:randomInt(0, 1, "g_nRandom") -- WANDER.inc:164
        if ctx:condition("g_nRandom==0") then -- WANDER.inc:166
            ctx:state().g_turnDeg = (tonumber(ctx:state().g_turnDeg) or 0) * -1 -- WANDER.inc:167
        end -- WANDER.inc:168
        ctx:self():rotate(0, 1, 0, "g_turnDeg", "g_turnRate") -- WANDER.inc:170
    end -- WANDER.inc:171
    if ctx:condition("g_IsRunning == FALSE") then -- WANDER.inc:173
        ctx:self():walk() -- WANDER.inc:174
    else -- WANDER.inc:175
        ctx:self():run() -- WANDER.inc:176
    end -- WANDER.inc:177
    ctx:randomFloat("g_IdleCheckMin", "g_IdleCheckMax", "g_nRandom") -- WANDER.inc:179
    ctx:wait("WANDER_WAIT_NBR", "g_nRandom", "WanderTick") -- WANDER.inc:180
    do return ctx:exit("") end -- WANDER.inc:182
end

script.labels["WanderPause"] = function(ctx)
    -- WANDER.inc:185
    if ctx:condition("g_IsAttacking == FALSE") then -- WANDER.inc:187
        if ctx:condition("g_IsRunning == FALSE") then -- WANDER.inc:188
            ctx:randomInt(1, 10, "g_nRandom") -- WANDER.inc:189
            if ctx:condition("g_nRandom <= g_SpecialAnimFrequency") then -- WANDER.inc:190
                ctx:trigger("g_hMyObject", "SpecialAnim") -- WANDER.inc:191
            else -- WANDER.inc:192
                ctx:self():setIdle() -- WANDER.inc:193
            end -- WANDER.inc:194
        end -- WANDER.inc:195
    end -- WANDER.inc:196
    ctx:randomFloat("g_IdleCheckMin", "g_IdleCheckMax", "g_nRandom") -- WANDER.inc:198
    ctx:wait("WANDER_WAIT_NBR", "g_nRandom", "WanderTick") -- WANDER.inc:199
    do return ctx:exit("") end -- WANDER.inc:201
end

script.labels["WanderTick"] = function(ctx)
    -- WANDER.inc:204
    if ctx:condition("g_IsRunning == TRUE") then -- WANDER.inc:206
        ctx:getTime("g_CurrTime") -- WANDER.inc:207
        if ctx:condition("g_CurrTime > g_StopRunTime") then -- WANDER.inc:209
            ctx:trigger("g_hMyObject", "StopRunning") -- WANDER.inc:210
        else -- WANDER.inc:211
            ctx:trigger("g_hMyObject", "Running") -- WANDER.inc:212
        end -- WANDER.inc:213
        mm9.gosub(script, ctx, "WanderGo") -- WANDER.inc:215
    else -- WANDER.inc:216
        ctx:randomInt(0, 10, "g_nRandom") -- WANDER.inc:217
        if ctx:condition("g_nRandom <= g_IdleFrequency") then -- WANDER.inc:218
            mm9.gosub(script, ctx, "WanderPause") -- WANDER.inc:219
        else -- WANDER.inc:220
            mm9.gosub(script, ctx, "WanderGo") -- WANDER.inc:221
        end -- WANDER.inc:222
    end -- WANDER.inc:223
    do return ctx:exit("") end -- WANDER.inc:225
end

script.labels["WanderStuckDone"] = function(ctx)
    -- WANDER.inc:228
    mm9.gosub(script, ctx, "WanderTick") -- WANDER.inc:231
    do return ctx:exit("TRUE") end -- WANDER.inc:232
end

script.labels["WanderStartup"] = function(ctx)
    -- WANDER.inc:235
    ctx:state().g_startX, ctx:state().g_startY, ctx:state().g_startZ = ctx:self():pos() -- WANDER.inc:238
    mm9.gosub(script, ctx, "WanderTick") -- WANDER.inc:240
    do return ctx:exit("TRUE") end -- WANDER.inc:242
end

script.labels["WanderInit"] = function(ctx)
    -- WANDER.inc:245
    ctx:onEvent("OnObstacle", "WanderObstacle") -- WANDER.inc:249
    ctx:onEvent("OnStuckDone", "WanderStuckDone") -- WANDER.inc:250
    -- Must wait and do some stuff after initial execution...
    ctx:wait("WANDER_WAIT_NBR", 0.1, "WanderStartup") -- WANDER.inc:253
    do return ctx:exit("") end -- WANDER.inc:255
end

return script
