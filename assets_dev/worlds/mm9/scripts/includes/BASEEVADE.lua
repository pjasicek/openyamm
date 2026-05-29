-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASEEVADE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "basetimers.inc" }

-- BaseEvade.Inc
-- Jeff Leggett
-- 09/07/2001
-- Basic Evasive Maneuvers..
-- Defaults to a 3 second evade time...
script.labels["BE_GetTargetDir"] = function(ctx)
    -- BASEEVADE.inc:41
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- BASEEVADE.inc:44
    ctx:state().g_targetDirX, ctx:state().g_targetdirY, ctx:state().g_targetDirZ = ctx:object("g_hTarget"):pos() -- BASEEVADE.inc:45
    ctx:set("g_posY", "g_targetdirY") -- BASEEVADE.inc:47
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:vecSub("g_targetDirX", "g_targetDirY", "g_targetDirZ", "g_posX", "g_posY", "g_posZ") -- BASEEVADE.inc:49
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:vecNorm("g_targetDirX", "g_targetDirY", "g_targetDirZ") -- BASEEVADE.inc:50
    do return ctx:exit("") end -- BASEEVADE.inc:52
end

script.labels["BE_StrafeObstacle"] = function(ctx)
    -- BASEEVADE.inc:55
    mm9.gosub(script, ctx, "BE_BackpedalObstacle") -- BASEEVADE.inc:58
    do return ctx:exit("TRUE") end -- BASEEVADE.inc:61
end

script.labels["BE_AttackStrafeObstacle"] = function(ctx)
    -- BASEEVADE.inc:64
    -- p0 - hObstacle
    ctx:getParam(0, "g_hObject") -- BASEEVADE.inc:70
    if ctx:condition("g_hObject!=g_hTarget") then -- BASEEVADE.inc:72
        ctx:self():stop() -- BASEEVADE.inc:73
        do return ctx:exit("TRUE") end -- BASEEVADE.inc:74
    end -- BASEEVADE.inc:75
    ctx:state().g_bTemp = ctx:self():isAttacking() -- BASEEVADE.inc:77
    ctx:state().g_bTemp = true -- BASEEVADE.inc:79
    if ctx:condition("g_bTemp==TRUE") then -- BASEEVADE.inc:81
        ctx:state().g_bBackpedalRun = false -- BASEEVADE.inc:82
        mm9.gosub(script, ctx, "BE_Backpedal") -- BASEEVADE.inc:83
        ctx:state().g_bBackpedalRun = true -- BASEEVADE.inc:84
    else -- BASEEVADE.inc:85
        ctx:self():stop() -- BASEEVADE.inc:86
    end -- BASEEVADE.inc:87
    do return ctx:exit("TRUE") end -- BASEEVADE.inc:89
end

script.labels["BE_AttackStrafe"] = function(ctx)
    -- BASEEVADE.inc:92
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- BASEEVADE.inc:94
    ctx:self():faceDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", 360) -- BASEEVADE.inc:96
    if ctx:condition("g_bPickDir==TRUE") then -- BASEEVADE.inc:98
        ctx:randomInt(0, 1, "g_nRandom") -- BASEEVADE.inc:99
        if ctx:condition("g_nRandom==0") then -- BASEEVADE.inc:101
            ctx:state().g_nStrafeAngle = 45 -- BASEEVADE.inc:102
        else -- BASEEVADE.inc:103
            ctx:state().g_nStrafeAngle = -45 -- BASEEVADE.inc:104
        end -- BASEEVADE.inc:105
    end -- BASEEVADE.inc:106
    ctx:state().g_bPickDir = false -- BASEEVADE.inc:108
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:rotateDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", "g_nStrafeAngle") -- BASEEVADE.inc:110
    ctx:self():strafe("g_targetDirX", "g_targetDirY", "g_targetDirZ", "g_bAttackStrafeRun") -- BASEEVADE.inc:112
    ctx:onEvent("OnObstacle", "BE_AttackStrafeObstacle") -- BASEEVADE.inc:113
    do return ctx:exit("") end -- BASEEVADE.inc:115
end

script.labels["BE_Strafe"] = function(ctx)
    -- BASEEVADE.inc:119
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- BASEEVADE.inc:121
    ctx:self():faceDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", 360) -- BASEEVADE.inc:123
    if ctx:condition("g_bPickDir==TRUE") then -- BASEEVADE.inc:125
        ctx:randomInt(0, 1, "g_nRandom") -- BASEEVADE.inc:126
        if ctx:condition("g_nRandom==0") then -- BASEEVADE.inc:128
            ctx:state().g_nStrafeAngle = 65 -- BASEEVADE.inc:129
        else -- BASEEVADE.inc:130
            ctx:state().g_nStrafeAngle = -65 -- BASEEVADE.inc:131
        end -- BASEEVADE.inc:132
    end -- BASEEVADE.inc:133
    ctx:state().g_bPickDir = false -- BASEEVADE.inc:135
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:rotateDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", "g_nStrafeAngle") -- BASEEVADE.inc:137
    ctx:self():strafe("g_targetDirX", "g_targetDirY", "g_targetDirZ", "TRUE") -- BASEEVADE.inc:139
    ctx:onEvent("OnObstacle", "BE_AttackStrafeObstacle") -- BASEEVADE.inc:140
    do return ctx:exit("") end -- BASEEVADE.inc:142
end

script.labels["BE_BackpedalTick"] = function(ctx)
    -- BASEEVADE.inc:145
    ctx:state().g_bTemp = ctx:self():getStat("IsIdle") -- BASEEVADE.inc:148
    if ctx:condition("g_bTemp==TRUE") then -- BASEEVADE.inc:150
        -- if we've stopped for some reason, then we don't want to continue with evading...
        do return ctx:exit("") end -- BASEEVADE.inc:152
    end -- BASEEVADE.inc:153
    mm9.gosub(script, ctx, "BE_Strafe") -- BASEEVADE.inc:155
    ctx:randomFloat(0.1, 0.4, "g_nRandom") -- BASEEVADE.inc:157
    ctx:wait("BASE_EVADE_WAIT", "g_nRandom", "BE_BackpedalTick") -- BASEEVADE.inc:159
    do return ctx:exit("") end -- BASEEVADE.inc:161
end

script.labels["BE_BackpedalDone"] = function(ctx)
    -- BASEEVADE.inc:164
    mm9.gosub(script, ctx, "BE_BackpedalTick") -- BASEEVADE.inc:167
    do return ctx:exit("") end -- BASEEVADE.inc:169
end

script.labels["BE_BackpedalObstacle"] = function(ctx)
    -- BASEEVADE.inc:172
    -- p0 - hObstacle
    -- p1-3 - normal vector
    ctx:getParam(0, "g_hObject") -- BASEEVADE.inc:178
    if ctx:condition("g_hObject!=g_hTarget") then -- BASEEVADE.inc:180
        ctx:self():stop() -- BASEEVADE.inc:181
        do return ctx:exit("TRUE") end -- BASEEVADE.inc:182
    end -- BASEEVADE.inc:183
    ctx:getTime("g_nTemp") -- BASEEVADE.inc:185
    ctx:set("g_nTemp", "g_nTemp - g_nLastObstacleTime") -- BASEEVADE.inc:187
    if ctx:condition("g_nTemp < MIN_BACKPEDAL_OBSTACLE") then -- BASEEVADE.inc:189
        -- Keep us from "freaking out" too much... (ie: continuously banging against something...)
        ctx:self():stop() -- BASEEVADE.inc:191
        do return ctx:exit("TRUE") end -- BASEEVADE.inc:192
    end -- BASEEVADE.inc:193
    ctx:getTime("g_nLastObstacleTime") -- BASEEVADE.inc:195
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- BASEEVADE.inc:197
    ctx:self():strafe("g_targetDirX", 0, "g_targetDirZ", "TRUE") -- BASEEVADE.inc:199
    -- gosub BE_BackPedal
    do return ctx:exit("TRUE") end -- BASEEVADE.inc:203
end

script.labels["BE_Backpedal"] = function(ctx)
    -- BASEEVADE.inc:206
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- BASEEVADE.inc:209
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:rotateDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", 180) -- BASEEVADE.inc:211
    ctx:randomInt(5, 35, "g_nRandom") -- BASEEVADE.inc:212
    ctx:randomInt(0, 1, "g_nTemp") -- BASEEVADE.inc:213
    if ctx:condition("g_nTemp==1") then -- BASEEVADE.inc:214
        ctx:set("g_nRandom", "g_nRandom * -1") -- BASEEVADE.inc:215
    end -- BASEEVADE.inc:216
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:rotateDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", "g_nRandom") -- BASEEVADE.inc:218
    ctx:self():strafe("g_targetDirX", 0, "g_targetDirZ", "g_bBackpedalRun") -- BASEEVADE.inc:220
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:rotateDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", 180) -- BASEEVADE.inc:222
    ctx:self():faceDir("g_targetDirX", 0, "g_targetDirZ", 360) -- BASEEVADE.inc:223
    ctx:onEvent("OnObstacle", "BE_BackpedalObstacle") -- BASEEVADE.inc:225
    do return ctx:exit("") end -- BASEEVADE.inc:227
end

script.labels["BE_BackpedalStart"] = function(ctx)
    -- BASEEVADE.inc:231
    ctx:state().g_bBackpedalRun = true -- BASEEVADE.inc:234
    mm9.gosub(script, ctx, "BE_BackPedal") -- BASEEVADE.inc:235
    ctx:set("g_nTemp", "g_nEvadeTime * g_nBackpedalPct") -- BASEEVADE.inc:237
    ctx:getTime("g_nEvadeStart") -- BASEEVADE.inc:239
    ctx:wait("BASE_EVADE_WAIT", "g_nTemp", "BE_BackpedalDone") -- BASEEVADE.inc:241
    do return ctx:exit("") end -- BASEEVADE.inc:243
end

script.labels["BaseEvadeStart"] = function(ctx)
    -- BASEEVADE.inc:247
    ctx:onEvent("OnPathClear") -- BASEEVADE.inc:250
    ctx:onEvent("OnObstacle") -- BASEEVADE.inc:251
    if ctx:condition("g_hTarget==NULL") then -- BASEEVADE.inc:253
        ctx:debugOut("What", "am", "I", "evading???") -- BASEEVADE.inc:254
        do return ctx:exit("") end -- BASEEVADE.inc:255
    end -- BASEEVADE.inc:256
    ctx:state().g_bEvading = true -- BASEEVADE.inc:258
    ctx:state().g_bPickDir = true -- BASEEVADE.inc:259
    -- See if we need to backpedal...
    mm9.gosub(script, ctx, "IsTargetMoving") -- BASEEVADE.inc:263
    if ctx:condition("g_bTemp==FALSE") then -- BASEEVADE.inc:265
        mm9.gosub(script, ctx, "BE_BackpedalStart") -- BASEEVADE.inc:266
        do return ctx:exit("") end -- BASEEVADE.inc:267
    end -- BASEEVADE.inc:268
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- BASEEVADE.inc:270
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:object("g_hTarget"):velocity() -- BASEEVADE.inc:272
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:vecNorm("g_velX", "g_velY", "g_velZ") -- BASEEVADE.inc:273
    ctx:state().g_nTemp = ctx:vecAngle("g_dirX", "g_dirY", "g_dirZ", "g_velX", "g_velY", "g_velZ") -- BASEEVADE.inc:274
    if ctx:condition("g_nTemp < 0") then -- BASEEVADE.inc:276
        ctx:set("g_nTemp", "g_nTemp * -1") -- BASEEVADE.inc:277
    end -- BASEEVADE.inc:278
    if ctx:condition("g_nTemp < 30") then -- BASEEVADE.inc:280
        mm9.gosub(script, ctx, "BE_BackpedalTick") -- BASEEVADE.inc:281
    else -- BASEEVADE.inc:282
        mm9.gosub(script, ctx, "BE_BackpedalStart") -- BASEEVADE.inc:283
    end -- BASEEVADE.inc:284
    do return ctx:exit("") end -- BASEEVADE.inc:286
end

script.labels["BaseEvadeStop"] = function(ctx)
    -- BASEEVADE.inc:289
    ctx:onEvent("OnTargetBeyondDist", 0) -- BASEEVADE.inc:292
    ctx:onEvent("OnObstacle") -- BASEEVADE.inc:293
    ctx:wait("BASE_EVADE_WAIT", 0, "DoNothing") -- BASEEVADE.inc:295
    ctx:state().g_bEvading = false -- BASEEVADE.inc:296
    do return ctx:exit("") end -- BASEEVADE.inc:298
end

return script
