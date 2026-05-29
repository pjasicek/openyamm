-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PRINCESS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "basedoor.inc" }

-- Princess.Scr
-- Jeff Leggett
-- 09/28/2000
-- The princess follows the last player to
-- press the "use" key on her...
-- #number		WALK_RADIUS=120
script.labels["Stop"] = function(ctx)
    -- PRINCESS.scr:31
    -- Stop moving, and prepare to start walking again...
    ctx:self():stop() -- PRINCESS.scr:37
    ctx:state().bAvoidingObstacle = false -- PRINCESS.scr:39
    if ctx:condition("g_hTarget!=NULL") then -- PRINCESS.scr:41
        ctx:onEvent("OnTargetBeyondDist", "WALK_RADIUS", "StartWalking") -- PRINCESS.scr:42
    end -- PRINCESS.scr:43
    do return ctx:exit("") end -- PRINCESS.scr:45
end

script.labels["WalkAfterTarget"] = function(ctx)
    -- PRINCESS.scr:48
    -- Walk to target...
    ctx:self():runTo(ctx:object("g_hTarget"), "STOP_RADIUS", "Stop") -- PRINCESS.scr:54
    do return ctx:exit("") end -- PRINCESS.scr:56
end

script.labels["RunAfterTarget"] = function(ctx)
    -- PRINCESS.scr:59
    ctx:self():runTo(ctx:object("g_hTarget"), "WALK_RADIUS", "WalkAfterTarget") -- PRINCESS.scr:62
    do return ctx:exit("") end -- PRINCESS.scr:64
end

script.labels["StartWalking"] = function(ctx)
    -- PRINCESS.scr:67
    ctx:onEvent("OnTargetBeyondDist", "RUN_RADIUS", "StartRunning") -- PRINCESS.scr:70
    ctx:onEvent("OnTargetWithinDist", 0) -- PRINCESS.scr:71
    mm9.gosub(script, ctx, "WalkAfterTarget") -- PRINCESS.scr:72
    do return ctx:exit("") end -- PRINCESS.scr:74
end

script.labels["StartRunning"] = function(ctx)
    -- PRINCESS.scr:77
    if ctx:condition("bAvoidingObstacle==TRUE") then -- PRINCESS.scr:80
        do return ctx:exit("") end -- PRINCESS.scr:81
    end -- PRINCESS.scr:82
    ctx:onEvent("OnTargetBeyondDist", 0) -- PRINCESS.scr:84
    ctx:onEvent("OnTargetWithinDist", "WALK_RADIUS", "StartWalking") -- PRINCESS.scr:85
    mm9.gosub(script, ctx, "RunAfterTarget") -- PRINCESS.scr:87
    do return ctx:exit("") end -- PRINCESS.scr:89
end

script.labels["FollowTarget"] = function(ctx)
    -- PRINCESS.scr:92
    if ctx:condition("g_hTarget==NULL") then -- PRINCESS.scr:95
        do return ctx:exit("") end -- PRINCESS.scr:96
    end -- PRINCESS.scr:97
    ctx:state().distance = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- PRINCESS.scr:99
    if ctx:condition("distance > RUN_RADIUS") then -- PRINCESS.scr:101
        mm9.gosub(script, ctx, "StartRunning") -- PRINCESS.scr:102
    else -- PRINCESS.scr:103
        if ctx:condition("distance > WALK_RADIUS") then -- PRINCESS.scr:104
            mm9.gosub(script, ctx, "StartWalking") -- PRINCESS.scr:105
        else -- PRINCESS.scr:106
            -- We're close enough to just hang out...
            -- Make sure we're notified when they get too far away..
            mm9.gosub(script, ctx, "Stop") -- PRINCESS.scr:109
        end -- PRINCESS.scr:110
    end -- PRINCESS.scr:111
    do return ctx:exit("TRUE") end -- PRINCESS.scr:114
end

script.labels["FoundTarget"] = function(ctx)
    -- PRINCESS.scr:117
    ctx:getParam(0, "g_hObject") -- PRINCESS.scr:120
    if ctx:condition("g_hTarget!=NULL") then -- PRINCESS.scr:122
        -- Why is this callback set... Get rid of it!
        ctx:onEvent("OnFoundTarget") -- PRINCESS.scr:124
        do return ctx:exit("") end -- PRINCESS.scr:125
    end -- PRINCESS.scr:126
    if ctx:condition("g_hObject==hLastTarget") then -- PRINCESS.scr:128
        -- We found him again, start walking after him...
        ctx:onEvent("OnFoundTarget") -- PRINCESS.scr:130
        ctx:set("g_hTarget", "g_hObject") -- PRINCESS.scr:131
        ctx:self():setTarget(ctx:object("g_hTarget")) -- PRINCESS.scr:132
        mm9.gosub(script, ctx, "FollowTarget") -- PRINCESS.scr:133
    end -- PRINCESS.scr:134
    do return ctx:exit("") end -- PRINCESS.scr:136
end

script.labels["LostTarget"] = function(ctx)
    -- PRINCESS.scr:139
    -- Keep his handle around for a little while...
    do return ctx:exit("TRUE") end -- PRINCESS.scr:144
    if ctx:condition("g_hTarget!=NULL") then -- PRINCESS.scr:146
        ctx:trigger("g_hTarget", "PrincessLost") -- PRINCESS.scr:147
    end -- PRINCESS.scr:148
    ctx:set("hLastTarget", "g_hTarget") -- PRINCESS.scr:150
    ctx:state().g_hTarget = nil -- PRINCESS.scr:151
    ctx:trigger("g_hTarget", "PrincessLost") -- PRINCESS.scr:153
    ctx:self():setTarget(nil) -- PRINCESS.scr:155
    mm9.gosub(script, ctx, "Stop") -- PRINCESS.scr:156
    ctx:onEvent("OnFoundTarget", "FoundTarget") -- PRINCESS.scr:158
    do return ctx:exit("TRUE") end -- PRINCESS.scr:160
end

script.labels["StopFollowingTarget"] = function(ctx)
    -- PRINCESS.scr:163
    -- Send a trigger to that target to notify him that
    -- we're no longer with him....
    if ctx:condition("g_hTarget!=NULL") then -- PRINCESS.scr:169
        ctx:trigger("g_hTarget", "PrincessLost") -- PRINCESS.scr:170
    end -- PRINCESS.scr:171
    ctx:self():setTarget(nil) -- PRINCESS.scr:173
    ctx:state().g_hTarget = nil -- PRINCESS.scr:174
    do return ctx:exit("") end -- PRINCESS.scr:176
end

script.labels["TargetDead"] = function(ctx)
    -- PRINCESS.scr:179
    ctx:self():setTarget(nil) -- PRINCESS.scr:182
    ctx:state().g_hTarget = nil -- PRINCESS.scr:183
    mm9.gosub(script, ctx, "Stop") -- PRINCESS.scr:185
    do return ctx:exit("") end -- PRINCESS.scr:187
end

script.labels["OnUse"] = function(ctx)
    -- PRINCESS.scr:190
    -- If that player is already our target, then
    -- we want to stop following them....
    if ctx:condition("bRescued==TRUE") then -- PRINCESS.scr:196
        -- Already rescued thank you!
        do return ctx:exit("") end -- PRINCESS.scr:198
    end -- PRINCESS.scr:199
    ctx:getParam(0, "g_hObject") -- PRINCESS.scr:201
    ctx:state().hLastTarget = nil -- PRINCESS.scr:203
    if ctx:condition("g_hTarget==g_hObject") then -- PRINCESS.scr:205
        mm9.gosub(script, ctx, "StopFollowingTarget") -- PRINCESS.scr:206
        do return ctx:exit("TRUE") end -- PRINCESS.scr:207
    end -- PRINCESS.scr:208
    if ctx:condition("g_hTarget!=NULL") then -- PRINCESS.scr:210
        mm9.gosub(script, ctx, "StopFollowingTarget") -- PRINCESS.scr:211
    end -- PRINCESS.scr:212
    ctx:set("g_hTarget", "g_hObject") -- PRINCESS.scr:214
    ctx:self():setTarget(ctx:object("g_hTarget")) -- PRINCESS.scr:216
    ctx:onEvent("OnLostTarget", "LostTarget") -- PRINCESS.scr:217
    mm9.gosub(script, ctx, "FollowTarget") -- PRINCESS.scr:219
    ctx:self():faceObject(ctx:object("g_hTarget"), 180) -- PRINCESS.scr:221
    do return ctx:exit("TRUE") end -- PRINCESS.scr:223
end

script.labels["Init"] = function(ctx)
    -- PRINCESS.scr:226
    do return ctx:exit("") end -- PRINCESS.scr:231
end

script.labels["ObstacleAvoided"] = function(ctx)
    -- PRINCESS.scr:234
    ctx:state().bAvoidingObstacle = false -- PRINCESS.scr:237
    mm9.gosub(script, ctx, "FollowTarget") -- PRINCESS.scr:239
    ctx:onEvent("OnObstacleAvoided") -- PRINCESS.scr:240
    do return ctx:exit("") end -- PRINCESS.scr:242
end

script.labels["OnAvoidingObstacle"] = function(ctx)
    -- PRINCESS.scr:245
    -- p0	= obstacle
    -- p1	= avoid turn angle
    ctx:getParam(0, "g_hObject") -- PRINCESS.scr:250
    ctx:getParam(1, "g_nTemp") -- PRINCESS.scr:251
    if ctx:condition("g_nTemp > MAX_RUN_ANGLE") then -- PRINCESS.scr:253
        -- Let's walk around it...
        mm9.gosub(script, ctx, "StartWalking") -- PRINCESS.scr:255
        ctx:onEvent("OnObstacleAvoided", "ObstacleAvoided") -- PRINCESS.scr:256
        ctx:state().bAvoidingObstacle = true -- PRINCESS.scr:257
    end -- PRINCESS.scr:258
    do return ctx:exit("TRUE") end -- PRINCESS.scr:260
end

script.labels["OnStuckDone"] = function(ctx)
    -- PRINCESS.scr:263
    -- Keep on truck'n
    mm9.gosub(script, ctx, "FollowTarget") -- PRINCESS.scr:267
    do return ctx:exit("TRUE") end -- PRINCESS.scr:269
end

script.labels["OnRescued"] = function(ctx)
    -- PRINCESS.scr:273
    if ctx:condition("g_hTarget!=NULL") then -- PRINCESS.scr:276
        ctx:trigger("g_hTarget", "PrincessRescued") -- PRINCESS.scr:277
    end -- PRINCESS.scr:278
    ctx:state().bRescued = true -- PRINCESS.scr:280
    ctx:self():setTarget(nil) -- PRINCESS.scr:282
    ctx:state().g_hTarget = nil -- PRINCESS.scr:283
    mm9.gosub(script, ctx, "Stop") -- PRINCESS.scr:285
    do return ctx:exit("") end -- PRINCESS.scr:287
end

script.labels["ComeToMe"] = function(ctx)
    -- PRINCESS.scr:290
    mm9.gosub(script, ctx, "OnUse") -- PRINCESS.scr:292
    do return ctx:exit("") end -- PRINCESS.scr:294
end

script.labels["OnTargetTeleport"] = function(ctx)
    -- PRINCESS.scr:298
    ctx:self():setTarget(nil) -- PRINCESS.scr:301
    ctx:state().g_hTarget = nil -- PRINCESS.scr:302
    mm9.gosub(script, ctx, "Stop") -- PRINCESS.scr:303
    do return ctx:exit("") end -- PRINCESS.scr:305
end

script.labels["Main"] = function(ctx)
    -- PRINCESS.scr:308
    -- TraceON
    ctx:self():setIdle() -- PRINCESS.scr:312
    ctx:addTrigger("Use", "OnUse") -- PRINCESS.scr:314
    ctx:addTrigger("HostageRescued", "OnRescued") -- PRINCESS.scr:315
    ctx:addTrigger("ComeToMe", "ComeToMe") -- PRINCESS.scr:316
    ctx:addTrigger("TargetTeleported", "OnTargetTeleport") -- PRINCESS.scr:317
    ctx:onEvent("OnAvoidingObstacle", "OnAvoidingObstacle") -- PRINCESS.scr:318
    ctx:onEvent("OnStuckDone", "OnStuckDone") -- PRINCESS.scr:319
    ctx:onEvent("OnTargetDead", "TargetDead") -- PRINCESS.scr:320
    mm9.gosub(script, ctx, "BaseDoorInit") -- PRINCESS.scr:322
    ctx:wait(0, 0.1, "Init") -- PRINCESS.scr:324
    do return ctx:exit("") end -- PRINCESS.scr:326
end

return script
