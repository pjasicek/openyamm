-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AICOMMON.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "AIGlobals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "BaseTimers.inc" }

-- AICommon.inc
-- Jeff Leggett
-- 11/29/2001
-- Data and functions that are common to all types of AI...
-- Set true when we are resurrecting someone else AND when we are being resurrected...
-- Tracks who was my target when I died...
script.labels["AlertStart"] = function(ctx)
    -- AICOMMON.inc:35
    mm9.gosub(script, ctx, "AlertTick") -- AICOMMON.inc:37
    do return ctx:exit("") end -- AICOMMON.inc:38
end

script.labels["AlertTick"] = function(ctx)
    -- AICOMMON.inc:41
    ctx:wait("ALERT_WAIT", "g_nRandom", "AlertTick") -- AICOMMON.inc:43
    if ctx:condition("g_hTarget==NULL") then -- AICOMMON.inc:45
        do return ctx:exit("") end -- AICOMMON.inc:46
    end -- AICOMMON.inc:47
    ctx:self():sendAlert(ctx:object("g_hTarget")) -- AICOMMON.inc:49
    do return ctx:exit("") end -- AICOMMON.inc:51
end

script.labels["AlertStop"] = function(ctx)
    -- AICOMMON.inc:54
    ctx:wait("ALERT_WAIT", 0, "DoNothing") -- AICOMMON.inc:56
    do return ctx:exit("") end -- AICOMMON.inc:57
end

script.labels["CanBeResurrected"] = function(ctx)
    -- AICOMMON.inc:62
    -- returns TRUE or FALSE in g_bCanBeResurrected
    ctx:state().g_bCanBeResurrected = ctx:self():getStat("CanBeResurrected") -- AICOMMON.inc:67
    if ctx:condition("g_bCanBeResurrected==FALSE") then -- AICOMMON.inc:69
        do return ctx:exit("") end -- AICOMMON.inc:70
    end -- AICOMMON.inc:71
    ctx:self():getAnimationNumber("Resurrect", "g_bCanBeResurrected") -- AICOMMON.inc:73
    if ctx:condition("g_bCanBeResurrected==-1") then -- AICOMMON.inc:74
        ctx:state().g_bCanBeResurrected = false -- AICOMMON.inc:75
    else -- AICOMMON.inc:76
        ctx:state().g_bCanBeResurrected = true -- AICOMMON.inc:77
    end -- AICOMMON.inc:78
    do return ctx:exit("") end -- AICOMMON.inc:81
end

script.labels["OnLinkBroken"] = function(ctx)
    -- AICOMMON.inc:84
    ctx:getParam(0, "g_hObject") -- AICOMMON.inc:87
    if ctx:condition("g_hObject==g_hAttacker") then -- AICOMMON.inc:88
        ctx:state().g_hAttacker = nil -- AICOMMON.inc:89
    end -- AICOMMON.inc:90
    if ctx:condition("g_hObject==g_hResurrect") then -- AICOMMON.inc:92
        ctx:state().g_hResurrect = nil -- AICOMMON.inc:93
    end -- AICOMMON.inc:94
    if ctx:condition("g_hObject==g_hDeathTarget") then -- AICOMMON.inc:96
        ctx:state().g_hDeathTarget = nil -- AICOMMON.inc:97
    end -- AICOMMON.inc:98
    do return ctx:exit("FALSE") end -- AICOMMON.inc:100
end

script.labels["AskForResurrection"] = function(ctx)
    -- AICOMMON.inc:103
    -- See if anyone nearby could potentially resurrect us.
    -- if so, trigger them and see what happens...
    -- cprint LOOKING for someone to resurrect me...
    ctx:getObjects("AIBase", "MAX_RESURRECT_DIST", "MAX_OBJECTS", "g_hObjectArray", "g_nTemp") -- AICOMMON.inc:113
    if ctx:condition("g_nTemp>0") then -- AICOMMON.inc:115
        ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) - 1 -- AICOMMON.inc:117
        while ctx:condition("g_nTemp>=0") do -- AICOMMON.inc:119
            ctx:arrayGet("g_hObjectArray", "g_nTemp", "g_hObject") -- AICOMMON.inc:121
            ctx:state().g_bTemp = true -- AICOMMON.inc:123
            if ctx:condition("g_hDeathTarget!=NULL") then -- AICOMMON.inc:125
                ctx:state().g_hObject2 = ctx:object("g_hObject"):target() -- AICOMMON.inc:126
                if ctx:condition("g_hObject2!=NULL") then -- AICOMMON.inc:127
                    if ctx:condition("g_hObject2!=g_hDeathTarget") then -- AICOMMON.inc:128
                        ctx:state().g_bTemp = false -- AICOMMON.inc:129
                    end -- AICOMMON.inc:130
                end -- AICOMMON.inc:131
            end -- AICOMMON.inc:132
            if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:134
                ctx:state().g_bTemp = ctx:object("g_hObject"):isActive() -- AICOMMON.inc:135
            end -- AICOMMON.inc:136
            if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:138
                if ctx:condition("g_hObject!=g_hMyObject") then -- AICOMMON.inc:139
                    ctx:state().g_bTemp = false -- AICOMMON.inc:140
                    ctx:state().g_bTemp = ctx:object("g_hObject"):getStat("IsResurrecter") -- AICOMMON.inc:141
                    if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:143
                        ctx:state().g_bAskedForResurrection = true -- AICOMMON.inc:144
                        ctx:trigger("g_hObject", "TMSG_RESURRECTME") -- AICOMMON.inc:145
                        ctx:isTurnBased("g_bTemp") -- AICOMMON.inc:146
                        if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:147
                            ctx:wait("RESURRECT_WAIT", 4, "AskForResurrection") -- AICOMMON.inc:148
                        else -- AICOMMON.inc:149
                            ctx:wait("RESURRECT_WAIT", 5, "AskForResurrection") -- AICOMMON.inc:150
                        end -- AICOMMON.inc:151
                        do return ctx:exit("") end -- AICOMMON.inc:152
                    end -- AICOMMON.inc:153
                end -- AICOMMON.inc:154
            end -- AICOMMON.inc:155
            ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) - 1 -- AICOMMON.inc:157
        end -- AICOMMON.inc:159
    end -- AICOMMON.inc:161
    -- cprint NO ONE TO RESURRECT ME! boo hoo...
    if ctx:condition("g_bAskedForResurrection==TRUE") then -- AICOMMON.inc:165
        -- cprint removing myself...
        ctx:state().g_bTemp = ctx:self():getStat("IsResurrecter") -- AICOMMON.inc:168
        if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:170
            -- Just resurrect myself!
            ctx:randomFloat(2, 10, "g_nRandom") -- AICOMMON.inc:172
            ctx:wait("RESURRECT_WAIT", "g_nRandom", "OnResurrect") -- AICOMMON.inc:173
            do return ctx:exit("") end -- AICOMMON.inc:174
        end -- AICOMMON.inc:175
        -- If we've already asked to be resurrected, and it hasn't happened yet, and
        -- there is no one around to resurrect us...  Time to go bye-bye...
        ctx:state().g_bTemp = ctx:self():getStat("IsGibber") -- AICOMMON.inc:181
        -- Don't want gibbers do be removed.  There gibs will fall from the sky!
        if ctx:condition("g_bTemp==FALSE") then -- AICOMMON.inc:185
            ctx:self():remove() -- AICOMMON.inc:186
        end -- AICOMMON.inc:187
    end -- AICOMMON.inc:189
    do return ctx:exit("") end -- AICOMMON.inc:191
end

script.labels["ResurrectMe"] = function(ctx)
    -- AICOMMON.inc:194
    -- p0	- Who's asking for it...
    if ctx:condition("g_hResurrect!=NULL") then -- AICOMMON.inc:200
        -- currently we can only handle 1 at a time...
        -- cprint I'VE BEEN REQUESTED TO RESURRECT SOMEONE, BUT I'M BUSY!
        do return ctx:exit("") end -- AICOMMON.inc:203
    end -- AICOMMON.inc:204
    -- cprint I'VE BEEN REQUESTED TO RESURRECT SOMEONE...
    ctx:getParam(0, "g_hResurrect") -- AICOMMON.inc:208
    ctx:isTurnBased("g_bTemp") -- AICOMMON.inc:210
    if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:212
        ctx:randomFloat(1, 2, "g_nRandom") -- AICOMMON.inc:213
    else -- AICOMMON.inc:214
        ctx:randomFloat(3, 6, "g_nRandom") -- AICOMMON.inc:215
    end -- AICOMMON.inc:216
    ctx:wait("RESURRECT_WAIT", "g_nRandom", "DoResurrection") -- AICOMMON.inc:218
    do return ctx:exit("") end -- AICOMMON.inc:220
end

script.labels["DoResurrection"] = function(ctx)
    -- AICOMMON.inc:223
    -- Time to resurrect.  Be sure to override this function
    -- to stop whatever it was that you were doing and then
    -- call this function...
    if ctx:condition("g_hResurrect==NULL") then -- AICOMMON.inc:231
        -- cprint NO ONE TO RESURRECT??
        do return ctx:exit("") end -- AICOMMON.inc:233
    end -- AICOMMON.inc:234
    ctx:state().g_bTemp = ctx:self():isDead() -- AICOMMON.inc:236
    if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:237
        ctx:state().g_hResurrect = nil -- AICOMMON.inc:238
        do return ctx:exit("") end -- AICOMMON.inc:239
    end -- AICOMMON.inc:240
    ctx:state().g_bTemp = ctx:object("g_hResurrect"):isDead() -- AICOMMON.inc:242
    if ctx:condition("g_bTemp==FALSE") then -- AICOMMON.inc:244
        ctx:state().g_hResurrect = nil -- AICOMMON.inc:245
        do return ctx:exit("") end -- AICOMMON.inc:246
    end -- AICOMMON.inc:247
    -- cprint TIME TO RESURRECT HIM!!
    ctx:state().g_bResurrecting = true -- AICOMMON.inc:251
    ctx:self():faceObject(ctx:object("g_hResurrect"), 450) -- AICOMMON.inc:253
    ctx:self():playAnimation("ResurrectSpell", "DoResurrectionDone") -- AICOMMON.inc:255
    do return ctx:exit("") end -- AICOMMON.inc:257
end

script.labels["DoResurrectionTrigger"] = function(ctx)
    -- AICOMMON.inc:260
    -- cprint GOT resurrect trigger!
    if ctx:condition("g_hResurrect==NULL") then -- AICOMMON.inc:265
        -- cprint NO ONE TO RESURRECT?
        do return ctx:exit("") end -- AICOMMON.inc:267
    end -- AICOMMON.inc:268
    if ctx:condition("g_bResurrecting==FALSE") then -- AICOMMON.inc:270
        -- cprint I'M NOT RESURRECTING??
        do return ctx:exit("") end -- AICOMMON.inc:272
    end -- AICOMMON.inc:273
    ctx:trigger("g_hResurrect", "TMSG_RESURRECT") -- AICOMMON.inc:275
    ctx:self():unlink(ctx:object("g_hResurrect")) -- AICOMMON.inc:277
    ctx:state().g_hResurrect = nil -- AICOMMON.inc:278
    do return ctx:exit("") end -- AICOMMON.inc:280
end

script.labels["DoResurrectionDone"] = function(ctx)
    -- AICOMMON.inc:283
    -- Overload this...
    ctx:state().g_bResurrecting = false -- AICOMMON.inc:289
    do return ctx:exit("") end -- AICOMMON.inc:291
end

script.labels["CanResurrectNow"] = function(ctx)
    -- AICOMMON.inc:294
    ctx:state().g_radius = ctx:self():getStat("Radius") -- AICOMMON.inc:300
    ctx:set("g_radius", "g_radius * 2") -- AICOMMON.inc:302
    ctx:getObjects("Actor", "g_radius", 20, "g_hArray", "g_nArrayCount") -- AICOMMON.inc:304
    if ctx:condition("g_nArrayCount!=0") then -- AICOMMON.inc:306
        -- cprint Somebody is too close... can't resurrect now...
        ctx:state().g_bCanResurrectNow = 0 -- AICOMMON.inc:308
        do return ctx:exit("") end -- AICOMMON.inc:309
    end -- AICOMMON.inc:310
    -- cprint OK, time to resurrect...
    ctx:state().g_bCanResurrectNow = 1 -- AICOMMON.inc:313
    do return ctx:exit("") end -- AICOMMON.inc:315
end

script.labels["OnResurrect"] = function(ctx)
    -- AICOMMON.inc:319
    -- OK, time to resurrect...
    -- Set our Resurrect stat to TRUE and play our animation...
    -- This will make us visible and put our bounding box
    -- where it should be...
    -- Cancel any pending resurrection requests...
    ctx:wait("RESURRECT_WAIT", 0, "DoNothing") -- AICOMMON.inc:335
    mm9.gosub(script, ctx, "CanResurrectNow") -- AICOMMON.inc:337
    if ctx:condition("g_bCanResurrectNow==FALSE") then -- AICOMMON.inc:339
        -- Try again in 1/2 second...
        ctx:wait("RESURRECT_WAIT", 0.5, "OnResurrect") -- AICOMMON.inc:341
        do return ctx:exit("") end -- AICOMMON.inc:342
    end -- AICOMMON.inc:343
    ctx:self():setStat("Resurrect", "TRUE") -- AICOMMON.inc:346
    ctx:self():playAnimation("Resurrect", "ResurrectDone") -- AICOMMON.inc:347
    ctx:state().g_bResurrecting = true -- AICOMMON.inc:349
    do return ctx:exit("") end -- AICOMMON.inc:351
end

script.labels["ResurrectDone"] = function(ctx)
    -- AICOMMON.inc:354
    -- Overload this to go back to being an evil bastard...
    ctx:state().g_bResurrecting = false -- AICOMMON.inc:360
    do return ctx:exit("") end -- AICOMMON.inc:362
end

script.labels["OnDeath"] = function(ctx)
    -- AICOMMON.inc:365
    -- if we can be resurrected, notify any monsters that
    -- can resurrect that we are ready!
    if ctx:condition("g_bCanBeResurrected==FALSE") then -- AICOMMON.inc:371
        -- cprint I DIED and CANNOT be resurrected!
        do return ctx:exit("FALSE") end -- AICOMMON.inc:373
    end -- AICOMMON.inc:374
    ctx:self():setStat("WaitForResurrect", "TRUE") -- AICOMMON.inc:376
    ctx:state().g_hDeathTarget = ctx:self():target() -- AICOMMON.inc:378
    ctx:self():setTarget(nil) -- AICOMMON.inc:380
    if ctx:condition("g_hDeathTarget!=NULL") then -- AICOMMON.inc:382
        ctx:self():link(ctx:object("g_hDeathTarget")) -- AICOMMON.inc:383
    end -- AICOMMON.inc:384
    do return ctx:exit("FALSE") end -- AICOMMON.inc:386
end

script.labels["OnDeathDone"] = function(ctx)
    -- AICOMMON.inc:389
    if ctx:condition("g_bCanBeResurrected==TRUE") then -- AICOMMON.inc:391
        -- cprint I DIED and CAN be resurrected!
        mm9.gosub(script, ctx, "AskForResurrection") -- AICOMMON.inc:393
        ctx:state().g_bAskedForResurrection = true -- AICOMMON.inc:394
        ctx:isTurnBased("g_bTemp") -- AICOMMON.inc:395
        if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:396
            ctx:wait("RESURRECT_WAIT", 2, "AskForResurrection") -- AICOMMON.inc:397
        else -- AICOMMON.inc:398
            ctx:wait("RESURRECT_WAIT", 5, "AskForResurrection") -- AICOMMON.inc:399
        end -- AICOMMON.inc:400
        ctx:state().g_bCanBeResurrected = false -- AICOMMON.inc:402
    end -- AICOMMON.inc:403
    do return ctx:exit("FALSE") end -- AICOMMON.inc:404
end

script.labels["SetupAttacker"] = function(ctx)
    -- AICOMMON.inc:407
    if ctx:condition("g_hAttacker==NULL") then -- AICOMMON.inc:409
        -- wtf?
        do return ctx:exit("") end -- AICOMMON.inc:411
    end -- AICOMMON.inc:412
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hAttacker")) -- AICOMMON.inc:414
    if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:416
        ctx:state().g_hAttacker = nil -- AICOMMON.inc:417
        do return ctx:exit("") end -- AICOMMON.inc:418
    end -- AICOMMON.inc:419
    ctx:self():link(ctx:object("g_hAttacker")) -- AICOMMON.inc:421
    do return ctx:exit("") end -- AICOMMON.inc:423
end

script.labels["ClearAttacker"] = function(ctx)
    -- AICOMMON.inc:426
    if ctx:condition("g_hAttacker!=NULL") then -- AICOMMON.inc:428
        ctx:self():unlink(ctx:object("g_hAttacker")) -- AICOMMON.inc:429
        ctx:state().g_hAttacker = nil -- AICOMMON.inc:430
    end -- AICOMMON.inc:431
    do return ctx:exit("") end -- AICOMMON.inc:432
end

script.labels["OnHateAll"] = function(ctx)
    -- AICOMMON.inc:435
    ctx:self():addEnemy("AIBase") -- AICOMMON.inc:438
    do return ctx:exit("") end -- AICOMMON.inc:439
end

script.labels["OnStopHateAll"] = function(ctx)
    -- AICOMMON.inc:442
    ctx:self():removeEnemy("AIBase") -- AICOMMON.inc:445
    do return ctx:exit("") end -- AICOMMON.inc:446
end

script.labels["OnHateAllOthers"] = function(ctx)
    -- AICOMMON.inc:450
    ctx:self():addEnemy("AIBase") -- AICOMMON.inc:452
    ctx:state().g_sTemp = ctx:self():className() -- AICOMMON.inc:454
    ctx:self():addFriend("g_sTemp") -- AICOMMON.inc:455
    do return ctx:exit("") end -- AICOMMON.inc:457
end

script.labels["OnStopHateAllOthers"] = function(ctx)
    -- AICOMMON.inc:460
    ctx:self():removeEnemy("AIBase") -- AICOMMON.inc:463
    ctx:state().g_sTemp = ctx:self():className() -- AICOMMON.inc:464
    ctx:self():removeFriend("g_sTemp") -- AICOMMON.inc:465
    do return ctx:exit("") end -- AICOMMON.inc:467
end

script.labels["ClearTarget"] = function(ctx)
    -- AICOMMON.inc:471
    -- This is overloaded everywhere....
    ctx:self():stop() -- AICOMMON.inc:477
    ctx:state().g_hTarget = nil -- AICOMMON.inc:478
    ctx:self():setTarget(nil) -- AICOMMON.inc:479
    do return ctx:exit("") end -- AICOMMON.inc:481
end

script.labels["OnEnrage"] = function(ctx)
    -- AICOMMON.inc:484
    -- Just stop and clear our target.
    -- OnFoundTarget will take over from there....
    mm9.gosub(script, ctx, "ClearTarget") -- AICOMMON.inc:491
    do return ctx:exit("") end -- AICOMMON.inc:493
end

script.labels["OnEnrageDone"] = function(ctx)
    -- AICOMMON.inc:496
    -- Just stop and clear our target.
    -- OnFoundTarget will take over from there....
    mm9.gosub(script, ctx, "ClearTarget") -- AICOMMON.inc:503
    do return ctx:exit("") end -- AICOMMON.inc:505
end

script.labels["InitCommon"] = function(ctx)
    -- AICOMMON.inc:509
    ctx:onEvent("OnDeath", "OnDeath") -- AICOMMON.inc:513
    ctx:onEvent("OnDeathDone", "OnDeathDone") -- AICOMMON.inc:514
    ctx:onEvent("OnObjectLinkBroken", "OnLinkBroken") -- AICOMMON.inc:515
    ctx:onEvent("OnEnrage", "OnEnrage") -- AICOMMON.inc:516
    ctx:onEvent("OnEnrageDone", "OnEnrageDone") -- AICOMMON.inc:517
    mm9.gosub(script, ctx, "CanBeResurrected") -- AICOMMON.inc:519
    -- If we're able to Resurrect others, setup a callback
    -- for the resurrectme request...
    ctx:state().g_bTemp = ctx:self():getStat("IsResurrecter") -- AICOMMON.inc:525
    if ctx:condition("g_bTemp==TRUE") then -- AICOMMON.inc:527
        ctx:addTrigger("TMSG_RESURRECTME", "ResurrectMe") -- AICOMMON.inc:528
        ctx:addModelKey("DoResurrection", "DoResurrectionTrigger") -- AICOMMON.inc:529
    end -- AICOMMON.inc:530
    if ctx:condition("g_bCanBeResurrected==TRUE") then -- AICOMMON.inc:532
        ctx:addTrigger("TMSG_RESURRECT", "OnResurrect") -- AICOMMON.inc:533
    end -- AICOMMON.inc:534
    ctx:addTrigger("HateAll", "OnHateAll") -- AICOMMON.inc:536
    ctx:addTrigger("StopHateAll", "OnStopHateAll") -- AICOMMON.inc:537
    ctx:addTrigger("HateAllOthers", "OnHateAllOthers") -- AICOMMON.inc:539
    ctx:addTrigger("StopHateAllOthers", "OnStopHateAllOthers") -- AICOMMON.inc:540
    do return ctx:exit("") end -- AICOMMON.inc:542
end

return script
