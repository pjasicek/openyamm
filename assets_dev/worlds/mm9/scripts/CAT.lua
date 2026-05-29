-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CAT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "baseWander.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "baseRun.inc" }

-- Cat.Scr
-- Jeff Leggett
-- 08/03/2001
-- Behavior:
-- - Go from actor to actor and hang out with them
-- - When a dog comes after me, run away in various
-- directions
script.labels["OnHangoutObstacle"] = function(ctx)
    -- CAT.scr:25
    mm9.gosub(script, ctx, "DoneHangingOut") -- CAT.scr:28
    do return ctx:exit("TRUE") end -- CAT.scr:30
end

script.labels["OnHangoutStuckDone"] = function(ctx)
    -- CAT.scr:33
    mm9.gosub(script, ctx, "DoneHangingOut") -- CAT.scr:36
    do return ctx:exit("TRUE") end -- CAT.scr:38
end

script.labels["DisableWandering"] = function(ctx)
    -- CAT.scr:42
    -- Do all things necessary to disable
    -- Wandering...
    mm9.gosub(script, ctx, "BaseWanderStop") -- CAT.scr:49
    ctx:onEvent("OnObstacle", "OnHangoutObstacle") -- CAT.scr:51
    ctx:onEvent("OnStuckDone", "OnHangoutStuckDone") -- CAT.scr:52
    ctx:onEvent("OnStuck") -- CAT.scr:53
    do return ctx:exit("") end -- CAT.scr:55
end

script.labels["LookForPerson"] = function(ctx)
    -- CAT.scr:58
    -- Just turn on the OnFoundPlayer again..
    ctx:onEvent("OnFoundTarget", "FoundTarget") -- CAT.scr:64
    do return ctx:exit("") end -- CAT.scr:66
end

script.labels["DoneHangingOut"] = function(ctx)
    -- CAT.scr:69
    -- Time to move on from this guy... (ie: stop following)
    -- Cancel out some timers...
    ctx:wait("HANGOUT_WAIT", 0, "DoNothing") -- CAT.scr:75
    ctx:wait("SITTING_WAIT", 0, "DoNothing") -- CAT.scr:76
    ctx:onEvent("OnTargetBeyondDist", 0, "DoNothing") -- CAT.scr:77
    ctx:state().g_bSitting = false -- CAT.scr:79
    ctx:state().g_hTarget = nil -- CAT.scr:80
    ctx:self():setTarget(nil) -- CAT.scr:81
    ctx:self():stop() -- CAT.scr:82
    mm9.gosub(script, ctx, "BaseWanderStart") -- CAT.scr:84
    ctx:onEvent("OnFoundTarget", "DoNothing") -- CAT.scr:86
    ctx:randomInt(10, 20, "g_nRandom") -- CAT.scr:88
    ctx:wait("HANGOUT_WAIT", "g_nRandom", "LookForPerson") -- CAT.scr:90
    do return ctx:exit("") end -- CAT.scr:92
end

script.labels["FoundTarget"] = function(ctx)
    -- CAT.scr:95
    -- Note: Target for cat is all NPCs and player.
    if ctx:condition("g_hTarget!=NULL") then -- CAT.scr:101
        do return ctx:exit("") end -- CAT.scr:102
    end -- CAT.scr:103
    if ctx:condition("g_bRunning==TRUE") then -- CAT.scr:105
        do return ctx:exit("") end -- CAT.scr:106
    end -- CAT.scr:107
    ctx:getParam(0, "g_hTarget") -- CAT.scr:109
    ctx:self():setTarget(ctx:object("g_hTarget")) -- CAT.scr:110
    mm9.gosub(script, ctx, "DisableWandering") -- CAT.scr:112
    ctx:self():walkTo(ctx:object("g_hTarget"), 0, "OnHangoutArrival") -- CAT.scr:114
    do return ctx:exit("") end -- CAT.scr:115
end

script.labels["SitDownFidget"] = function(ctx)
    -- CAT.scr:119
    ctx:randomInt(0, 1, "g_nRandom") -- CAT.scr:122
    if ctx:condition("g_nRandom==0") then -- CAT.scr:124
        ctx:self():playAnimation("fidgetdown1", "HaveASeat") -- CAT.scr:125
    else -- CAT.scr:126
        ctx:self():playAnimation("fidgetdown2", "HaveASeat") -- CAT.scr:127
    end -- CAT.scr:128
    do return ctx:exit("") end -- CAT.scr:130
end

script.labels["HaveASeat"] = function(ctx)
    -- CAT.scr:133
    if ctx:condition("g_bSitting==FALSE") then -- CAT.scr:136
        do return ctx:exit("") end -- CAT.scr:137
    end -- CAT.scr:138
    ctx:self():loopAnimation("StandDown", 0) -- CAT.scr:140
    ctx:randomFloat(1, 4, "g_nRandom") -- CAT.scr:142
    ctx:wait("SITTING_WAIT", "g_nRandom", "SitDownFidget") -- CAT.scr:144
    do return ctx:exit("") end -- CAT.scr:146
end

script.labels["OnHangoutArrival"] = function(ctx)
    -- CAT.scr:149
    ctx:randomFloat(8, 15, "g_nRandom") -- CAT.scr:152
    ctx:wait("HANGOUT_WAIT", "g_nRandom", "DoneHangingOut") -- CAT.scr:154
    ctx:self():stop() -- CAT.scr:155
    ctx:onEvent("OnTargetBeyondDist", 120, "GoAfterHim") -- CAT.scr:157
    ctx:state().g_bSitting = true -- CAT.scr:158
    mm9.gosub(script, ctx, "HaveASeat") -- CAT.scr:159
    ctx:trigger("g_hTarget", "LookAtMe") -- CAT.scr:160
    do return ctx:exit("TRUE") end -- CAT.scr:162
end

script.labels["GoAfterHim"] = function(ctx)
    -- CAT.scr:165
    ctx:onEvent("OnTargetBeyondDist", 0) -- CAT.scr:168
    ctx:wait("SITTING_WAIT", 0, "DoNothing") -- CAT.scr:169
    ctx:state().g_bSitting = false -- CAT.scr:171
    ctx:self():stop() -- CAT.scr:173
    ctx:self():setIdle() -- CAT.scr:174
    ctx:self():walkTo(ctx:object("g_hTarget"), 0, "OnHangoutArrival") -- CAT.scr:176
    do return ctx:exit("") end -- CAT.scr:178
end

script.labels["DogChase"] = function(ctx)
    -- CAT.scr:181
    -- p0 - handle of the DOG...
    ctx:getParam(0, "g_hTarget") -- CAT.scr:185
    ctx:self():setTarget(ctx:object("g_hTarget")) -- CAT.scr:186
    mm9.gosub(script, ctx, "RunAway") -- CAT.scr:187
    ctx:randomInt(12, 18, "g_nRandom") -- CAT.scr:189
    ctx:wait("RUN_AWAY_STOP_WAIT", "g_nRandom", "BaseRunCancel") -- CAT.scr:191
    do return ctx:exit("") end -- CAT.scr:193
end

script.labels["DogGiveUp"] = function(ctx)
    -- CAT.scr:196
    -- Dog gave up, keep running for a little while longer..
    ctx:randomInt(5, 8, "g_nRandom") -- CAT.scr:201
    ctx:wait("RUN_AWAY_STOP_WAIT", "g_nRandom", "BaseRunCancel") -- CAT.scr:202
    do return ctx:exit("") end -- CAT.scr:204
end

script.labels["StartUp"] = function(ctx)
    -- CAT.scr:207
    ctx:state().g_bUseHidingPlaces = false -- CAT.scr:210
    ctx:self():setIdle() -- CAT.scr:212
    mm9.gosub(script, ctx, "BaseWanderForceStartup") -- CAT.scr:213
    do return ctx:exit("") end -- CAT.scr:215
end

script.labels["RunAway"] = function(ctx)
    -- CAT.scr:219
    -- Run Away from our target...
    if ctx:condition("g_hTarget==NULL") then -- CAT.scr:225
        do return ctx:exit("") end -- CAT.scr:226
    end -- CAT.scr:227
    mm9.gosub(script, ctx, "DisableWandering") -- CAT.scr:229
    ctx:self():stop() -- CAT.scr:231
    ctx:self():setIdle() -- CAT.scr:232
    -- Cancel some timers...
    ctx:wait("HANGOUT_WAIT", 0, "DoNothing") -- CAT.scr:237
    ctx:wait("SITTING_WAIT", 0, "DoNothing") -- CAT.scr:238
    ctx:wait("RUN_AWAY_WAIT", 0, "DoNothing") -- CAT.scr:239
    -- Not sitting anymore...
    ctx:state().g_bSitting = false -- CAT.scr:242
    mm9.gosub(script, ctx, "BaseRunAway") -- CAT.scr:244
    do return ctx:exit("") end -- CAT.scr:246
end

script.labels["BaseRunCancel"] = function(ctx)
    -- CAT.scr:249
    -- We're overloading the function here....
    mm9.gosub(script, ctx, "BaseRunCancel") -- CAT.scr:255
    ctx:wait("RUN_AWAY_STOP_WAIT", 0, "DoNothing") -- CAT.scr:257
    mm9.gosub(script, ctx, "DoneHangingOut") -- CAT.scr:258
    mm9.gosub(script, ctx, "BaseWanderGo") -- CAT.scr:259
    do return ctx:exit("") end -- CAT.scr:261
end

script.labels["OnProjectile"] = function(ctx)
    -- CAT.scr:264
    if ctx:condition("g_bRunning==TRUE") then -- CAT.scr:266
        do return ctx:exit("TRUE") end -- CAT.scr:267
    end -- CAT.scr:268
    ctx:getParam(1, "g_hObject") -- CAT.scr:270
    ctx:set("g_hTarget", "g_hObject") -- CAT.scr:272
    ctx:self():setTarget(ctx:object("g_hTarget")) -- CAT.scr:274
    if ctx:condition("g_hTarget!=NULL") then -- CAT.scr:276
        mm9.gosub(script, ctx, "RunAway") -- CAT.scr:277
        ctx:randomInt(10, 20, "g_nRandom") -- CAT.scr:278
        ctx:wait("RUN_AWAY_STOP_WAIT", "g_nRandom", "BaseRunCancel") -- CAT.scr:279
    end -- CAT.scr:280
    do return ctx:exit("TRUE") end -- CAT.scr:282
end

script.labels["BaseShouldRun"] = function(ctx)
    -- CAT.scr:285
    ctx:state().g_bTemp = true -- CAT.scr:287
    do return ctx:exit("") end -- CAT.scr:289
end

script.labels["Main"] = function(ctx)
    -- CAT.scr:292
    ctx:onEvent("OnFoundTarget", "FoundTarget") -- CAT.scr:298
    ctx:addTrigger("DogChase", "DogChase") -- CAT.scr:299
    ctx:addTrigger("DogGiveUp", "DogGiveUp") -- CAT.scr:300
    ctx:onEvent("OnProjectile", "OnProjectile") -- CAT.scr:302
    mm9.gosub(script, ctx, "BaseWanderInit") -- CAT.scr:304
    ctx:wait(0, 1.0, "StartUp") -- CAT.scr:305
    ctx:state().RUN_AWAY_TURN_MIN = 15 -- CAT.scr:307
    ctx:state().RUN_AWAY_TURN_MAX = 85 -- CAT.scr:308
    ctx:self():setIdle() -- CAT.scr:310
    do return ctx:exit("") end -- CAT.scr:312
end

return script
