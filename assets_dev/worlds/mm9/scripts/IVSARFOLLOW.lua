-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IVSARFOLLOW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }

-- Princess.Scr
-- Jeff Leggett
-- 09/28/2000
-- The princess follows the last player to
-- press the "use" key on her...
-- #number		WALK_RADIUS=120
script.labels["Stop"] = function(ctx)
    -- IVSARFOLLOW.scr:30
    -- Stop moving, and prepare to start walking again...
    ctx:self():stop() -- IVSARFOLLOW.scr:36
    ctx:state().bAvoidingObstacle = false -- IVSARFOLLOW.scr:38
    if ctx:condition("g_hTarget!=NULL") then -- IVSARFOLLOW.scr:40
        ctx:onEvent("OnTargetBeyondDist", "WALK_RADIUS", "StartWalking") -- IVSARFOLLOW.scr:41
    end -- IVSARFOLLOW.scr:42
    do return ctx:exit("") end -- IVSARFOLLOW.scr:44
end

script.labels["WalkAfterTarget"] = function(ctx)
    -- IVSARFOLLOW.scr:47
    -- Walk to target...
    ctx:self():runTo(ctx:object("g_hTarget"), "STOP_RADIUS", "Stop") -- IVSARFOLLOW.scr:53
    do return ctx:exit("") end -- IVSARFOLLOW.scr:55
end

script.labels["RunAfterTarget"] = function(ctx)
    -- IVSARFOLLOW.scr:58
    ctx:self():runTo(ctx:object("g_hTarget"), "WALK_RADIUS", "WalkAfterTarget") -- IVSARFOLLOW.scr:61
    do return ctx:exit("") end -- IVSARFOLLOW.scr:63
end

script.labels["StartWalking"] = function(ctx)
    -- IVSARFOLLOW.scr:66
    ctx:onEvent("OnTargetBeyondDist", "RUN_RADIUS", "StartRunning") -- IVSARFOLLOW.scr:69
    ctx:onEvent("OnTargetWithinDist", 0) -- IVSARFOLLOW.scr:70
    mm9.gosub(script, ctx, "WalkAfterTarget") -- IVSARFOLLOW.scr:71
    do return ctx:exit("") end -- IVSARFOLLOW.scr:73
end

script.labels["StartRunning"] = function(ctx)
    -- IVSARFOLLOW.scr:76
    if ctx:condition("bAvoidingObstacle==TRUE") then -- IVSARFOLLOW.scr:79
        do return ctx:exit("") end -- IVSARFOLLOW.scr:80
    end -- IVSARFOLLOW.scr:81
    ctx:onEvent("OnTargetBeyondDist", 0) -- IVSARFOLLOW.scr:83
    ctx:onEvent("OnTargetWithinDist", "WALK_RADIUS", "StartWalking") -- IVSARFOLLOW.scr:84
    mm9.gosub(script, ctx, "RunAfterTarget") -- IVSARFOLLOW.scr:86
    do return ctx:exit("") end -- IVSARFOLLOW.scr:88
end

script.labels["FollowTarget"] = function(ctx)
    -- IVSARFOLLOW.scr:91
    if ctx:condition("g_hTarget==NULL") then -- IVSARFOLLOW.scr:94
        do return ctx:exit("") end -- IVSARFOLLOW.scr:95
    end -- IVSARFOLLOW.scr:96
    ctx:state().distance = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- IVSARFOLLOW.scr:98
    if ctx:condition("distance > RUN_RADIUS") then -- IVSARFOLLOW.scr:100
        mm9.gosub(script, ctx, "StartRunning") -- IVSARFOLLOW.scr:101
    else -- IVSARFOLLOW.scr:102
        if ctx:condition("distance > WALK_RADIUS") then -- IVSARFOLLOW.scr:103
            mm9.gosub(script, ctx, "StartWalking") -- IVSARFOLLOW.scr:104
        else -- IVSARFOLLOW.scr:105
            -- We're close enough to just hang out...
            -- Make sure we're notified when they get too far away..
            mm9.gosub(script, ctx, "Stop") -- IVSARFOLLOW.scr:108
        end -- IVSARFOLLOW.scr:109
    end -- IVSARFOLLOW.scr:110
    do return ctx:exit("TRUE") end -- IVSARFOLLOW.scr:113
end

script.labels["FoundTarget"] = function(ctx)
    -- IVSARFOLLOW.scr:116
    ctx:getParam(0, "g_hObject") -- IVSARFOLLOW.scr:119
    if ctx:condition("g_hTarget!=NULL") then -- IVSARFOLLOW.scr:121
        -- Why is this callback set... Get rid of it!
        ctx:onEvent("OnFoundTarget") -- IVSARFOLLOW.scr:123
        do return ctx:exit("") end -- IVSARFOLLOW.scr:124
    end -- IVSARFOLLOW.scr:125
    if ctx:condition("g_hObject==hLastTarget") then -- IVSARFOLLOW.scr:127
        -- We found him again, start walking after him...
        ctx:onEvent("OnFoundTarget") -- IVSARFOLLOW.scr:129
        ctx:set("g_hTarget", "g_hObject") -- IVSARFOLLOW.scr:130
        ctx:self():setTarget(ctx:object("g_hTarget")) -- IVSARFOLLOW.scr:131
        mm9.gosub(script, ctx, "FollowTarget") -- IVSARFOLLOW.scr:132
    end -- IVSARFOLLOW.scr:133
    do return ctx:exit("") end -- IVSARFOLLOW.scr:135
end

script.labels["LostTarget"] = function(ctx)
    -- IVSARFOLLOW.scr:138
    -- Keep his handle around for a little while...
    do return ctx:exit("TRUE") end -- IVSARFOLLOW.scr:143
    if ctx:condition("g_hTarget!=NULL") then -- IVSARFOLLOW.scr:145
        ctx:trigger("g_hTarget", "PrincessLost") -- IVSARFOLLOW.scr:146
    end -- IVSARFOLLOW.scr:147
    ctx:set("hLastTarget", "g_hTarget") -- IVSARFOLLOW.scr:149
    ctx:state().g_hTarget = nil -- IVSARFOLLOW.scr:150
    ctx:trigger("g_hTarget", "PrincessLost") -- IVSARFOLLOW.scr:152
    ctx:self():setTarget(nil) -- IVSARFOLLOW.scr:154
    mm9.gosub(script, ctx, "Stop") -- IVSARFOLLOW.scr:155
    ctx:onEvent("OnFoundTarget", "FoundTarget") -- IVSARFOLLOW.scr:157
    do return ctx:exit("TRUE") end -- IVSARFOLLOW.scr:159
end

script.labels["StopFollowingTarget"] = function(ctx)
    -- IVSARFOLLOW.scr:162
    -- Send a trigger to that target to notify him that
    -- we're no longer with him....
    if ctx:condition("g_hTarget!=NULL") then -- IVSARFOLLOW.scr:168
        ctx:trigger("g_hTarget", "PrincessLost") -- IVSARFOLLOW.scr:169
    end -- IVSARFOLLOW.scr:170
    ctx:self():setTarget(nil) -- IVSARFOLLOW.scr:172
    ctx:state().g_hTarget = nil -- IVSARFOLLOW.scr:173
    do return ctx:exit("") end -- IVSARFOLLOW.scr:175
end

script.labels["TargetDead"] = function(ctx)
    -- IVSARFOLLOW.scr:178
    ctx:self():setTarget(nil) -- IVSARFOLLOW.scr:181
    ctx:state().g_hTarget = nil -- IVSARFOLLOW.scr:182
    mm9.gosub(script, ctx, "Stop") -- IVSARFOLLOW.scr:184
    do return ctx:exit("") end -- IVSARFOLLOW.scr:186
end

script.labels["IvsarStart"] = function(ctx)
    -- IVSARFOLLOW.scr:189
    -- If that player is already our target, then
    -- we want to stop following them....
    if ctx:condition("bRescued==TRUE") then -- IVSARFOLLOW.scr:195
        -- Already rescued thank you!
        do return ctx:exit("") end -- IVSARFOLLOW.scr:197
    end -- IVSARFOLLOW.scr:198
    ctx:getParam(0, "g_hObject") -- IVSARFOLLOW.scr:200
    ctx:state().hLastTarget = nil -- IVSARFOLLOW.scr:202
    if ctx:condition("g_hTarget==g_hObject") then -- IVSARFOLLOW.scr:204
        mm9.gosub(script, ctx, "StopFollowingTarget") -- IVSARFOLLOW.scr:205
        do return ctx:exit("TRUE") end -- IVSARFOLLOW.scr:206
    end -- IVSARFOLLOW.scr:207
    if ctx:condition("g_hTarget!=NULL") then -- IVSARFOLLOW.scr:209
        mm9.gosub(script, ctx, "StopFollowingTarget") -- IVSARFOLLOW.scr:210
    end -- IVSARFOLLOW.scr:211
    ctx:set("g_hTarget", "g_hObject") -- IVSARFOLLOW.scr:213
    ctx:self():setTarget(ctx:object("g_hTarget")) -- IVSARFOLLOW.scr:215
    ctx:onEvent("OnLostTarget", "LostTarget") -- IVSARFOLLOW.scr:216
    mm9.gosub(script, ctx, "FollowTarget") -- IVSARFOLLOW.scr:218
    ctx:self():faceObject(ctx:object("g_hTarget"), 180) -- IVSARFOLLOW.scr:220
    do return ctx:exit("TRUE") end -- IVSARFOLLOW.scr:222
end

script.labels["Init"] = function(ctx)
    -- IVSARFOLLOW.scr:225
    do return ctx:exit("") end -- IVSARFOLLOW.scr:230
end

script.labels["ObstacleAvoided"] = function(ctx)
    -- IVSARFOLLOW.scr:233
    ctx:state().bAvoidingObstacle = false -- IVSARFOLLOW.scr:236
    mm9.gosub(script, ctx, "FollowTarget") -- IVSARFOLLOW.scr:238
    ctx:onEvent("OnObstacleAvoided") -- IVSARFOLLOW.scr:239
    do return ctx:exit("") end -- IVSARFOLLOW.scr:241
end

script.labels["OnAvoidingObstacle"] = function(ctx)
    -- IVSARFOLLOW.scr:244
    -- p0	= obstacle
    -- p1	= avoid turn angle
    ctx:getParam(0, "g_hObject") -- IVSARFOLLOW.scr:249
    ctx:getParam(1, "g_nTemp") -- IVSARFOLLOW.scr:250
    if ctx:condition("g_nTemp > MAX_RUN_ANGLE") then -- IVSARFOLLOW.scr:252
        -- Let's walk around it...
        mm9.gosub(script, ctx, "StartWalking") -- IVSARFOLLOW.scr:254
        ctx:onEvent("OnObstacleAvoided", "ObstacleAvoided") -- IVSARFOLLOW.scr:255
        ctx:state().bAvoidingObstacle = true -- IVSARFOLLOW.scr:256
    end -- IVSARFOLLOW.scr:257
    do return ctx:exit("TRUE") end -- IVSARFOLLOW.scr:259
end

script.labels["OnStuckDone"] = function(ctx)
    -- IVSARFOLLOW.scr:262
    -- Keep on truck'n
    mm9.gosub(script, ctx, "FollowTarget") -- IVSARFOLLOW.scr:266
    do return ctx:exit("TRUE") end -- IVSARFOLLOW.scr:268
end

script.labels["OnRescued"] = function(ctx)
    -- IVSARFOLLOW.scr:272
    if ctx:condition("g_hTarget!=NULL") then -- IVSARFOLLOW.scr:275
        ctx:trigger("g_hTarget", "PrincessRescued") -- IVSARFOLLOW.scr:276
    end -- IVSARFOLLOW.scr:277
    ctx:state().bRescued = true -- IVSARFOLLOW.scr:279
    ctx:self():setTarget(nil) -- IVSARFOLLOW.scr:281
    ctx:state().g_hTarget = nil -- IVSARFOLLOW.scr:282
    mm9.gosub(script, ctx, "Stop") -- IVSARFOLLOW.scr:284
    do return ctx:exit("") end -- IVSARFOLLOW.scr:286
end

script.labels["ComeToMe"] = function(ctx)
    -- IVSARFOLLOW.scr:289
    mm9.gosub(script, ctx, "IvsarStart") -- IVSARFOLLOW.scr:291
    do return ctx:exit("") end -- IVSARFOLLOW.scr:293
end

script.labels["OnTargetTeleport"] = function(ctx)
    -- IVSARFOLLOW.scr:297
    ctx:self():setTarget(nil) -- IVSARFOLLOW.scr:300
    ctx:state().g_hTarget = nil -- IVSARFOLLOW.scr:301
    mm9.gosub(script, ctx, "Stop") -- IVSARFOLLOW.scr:302
    do return ctx:exit("") end -- IVSARFOLLOW.scr:304
end

script.labels["IvsarFollowInit"] = function(ctx)
    -- IVSARFOLLOW.scr:307
    -- TraceON
    ctx:self():setIdle() -- IVSARFOLLOW.scr:311
    -- AddTrigger Use, OnUse
    ctx:addTrigger("HostageRescued", "OnRescued") -- IVSARFOLLOW.scr:314
    ctx:addTrigger("ComeToMe", "ComeToMe") -- IVSARFOLLOW.scr:315
    ctx:addTrigger("TargetTeleported", "OnTargetTeleport") -- IVSARFOLLOW.scr:316
    ctx:onEvent("OnAvoidingObstacle", "OnAvoidingObstacle") -- IVSARFOLLOW.scr:317
    ctx:onEvent("OnStuckDone", "OnStuckDone") -- IVSARFOLLOW.scr:318
    ctx:onEvent("OnTargetDead", "TargetDead") -- IVSARFOLLOW.scr:319
    ctx:wait(0, 0.1, "Init") -- IVSARFOLLOW.scr:321
    do return ctx:exit("") end -- IVSARFOLLOW.scr:323
end

return script
