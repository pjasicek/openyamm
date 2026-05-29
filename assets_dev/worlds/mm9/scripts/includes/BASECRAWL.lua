-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASECRAWL.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "AICommon.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "baseevade.inc" }
script.includes[#script.includes + 1] = { line = 16, path = "basewander.inc" }
script.includes[#script.includes + 1] = { line = 17, path = "SpeedThrottle.inc" }
script.includes[#script.includes + 1] = { line = 18, path = "BaseRun.inc" }
script.includes[#script.includes + 1] = { line = 19, path = "BaseDoor.inc" }

-- BaseCrawl.inc
-- Jeff Leggett
-- 10/03/2001
-- Script for our 4-legged friends.....
-- No strafe attacks
-- No dodging
-- Just run up and attack....
-- Max time to keep chasing a target if we haven't attacked them nor have we
-- been attacked.....
script.labels["CanReachTarget"] = function(ctx)
    -- BASECRAWL.inc:70
    -- Set's g_bCanReach to TRUE or FALSE
    ctx:getTime("g_nLastCanReachCheck") -- BASECRAWL.inc:76
    ctx:state().g_bCanReach = ctx:self():canReachTarget() -- BASECRAWL.inc:77
    do return ctx:exit("") end -- BASECRAWL.inc:79
end

script.labels["BaseCrawlGetHim"] = function(ctx)
    -- BASECRAWL.inc:82
    ctx:onEvent("OnObstacle", "AggressiveObstacle") -- BASECRAWL.inc:88
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:90
        do return ctx:exit("") end -- BASECRAWL.inc:91
    end -- BASECRAWL.inc:92
    ctx:self():runTo(ctx:object("g_hTarget"), "g_runToRange", "BaseCrawlArrival") -- BASECRAWL.inc:94
    do return ctx:exit("") end -- BASECRAWL.inc:96
end

script.labels["AggressiveObstacle"] = function(ctx)
    -- BASECRAWL.inc:99
    ctx:getParam(0, "g_hObject") -- BASECRAWL.inc:102
    if ctx:condition("g_hObject==g_hTarget") then -- BASECRAWL.inc:104
        ctx:debugOut("Ran", "into", "target!", "stopping....") -- BASECRAWL.inc:105
        ctx:self():stop() -- BASECRAWL.inc:106
        do return ctx:exit("TRUE") end -- BASECRAWL.inc:107
    end -- BASECRAWL.inc:108
    do return ctx:exit("FALSE") end -- BASECRAWL.inc:110
end

script.labels["BaseCrawlArrival"] = function(ctx)
    -- BASECRAWL.inc:113
    if ctx:condition("g_bAggressive==TRUE") then -- BASECRAWL.inc:116
        mm9.gosub(script, ctx, "AggressiveTick") -- BASECRAWL.inc:117
    end -- BASECRAWL.inc:118
    do return ctx:exit("TRUE") end -- BASECRAWL.inc:120
end

script.labels["AggressiveStart"] = function(ctx)
    -- BASECRAWL.inc:123
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "AggressiveTick") -- BASECRAWL.inc:126
    ctx:state().g_bAggressive = true -- BASECRAWL.inc:127
    mm9.gosub(script, ctx, "SpeedThrottleStart") -- BASECRAWL.inc:129
    ctx:onEvent("OnObstacle", "AggressiveObstacle") -- BASECRAWL.inc:131
    do return ctx:exit("") end -- BASECRAWL.inc:134
end

script.labels["AggressiveStop"] = function(ctx)
    -- BASECRAWL.inc:137
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "DoNothing") -- BASECRAWL.inc:140
    ctx:state().g_bAggressive = false -- BASECRAWL.inc:142
    ctx:onEvent("OnObstacle") -- BASECRAWL.inc:144
    do return ctx:exit("") end -- BASECRAWL.inc:146
end

script.labels["ShouldRunAfterNewTarget"] = function(ctx)
    -- BASECRAWL.inc:149
    mm9.gosub(script, ctx, "ShouldRunAway") -- BASECRAWL.inc:152
    -- ShouldRunAway g_hObject, g_bTemp
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:155
        ctx:state().g_bTemp = false -- BASECRAWL.inc:156
    else -- BASECRAWL.inc:157
        ctx:state().g_bTemp = true -- BASECRAWL.inc:158
    end -- BASECRAWL.inc:159
    do return ctx:exit("") end -- BASECRAWL.inc:161
end

script.labels["ShouldRunAway"] = function(ctx)
    -- BASECRAWL.inc:164
    -- Set g_hObject to the object you're asking about
    -- g_bTemp will be set to TRUE or FALSE
    ctx:state().g_bTemp = false -- BASECRAWL.inc:171
    if ctx:condition("g_hObject==NULL") then -- BASECRAWL.inc:172
        do return ctx:exit("") end -- BASECRAWL.inc:173
    end -- BASECRAWL.inc:174
    -- See if we should hold our ground for awhile...
    ctx:state().g_nTemp = ctx:self():isFear() -- BASECRAWL.inc:178
    if ctx:condition("g_nTemp==FALSE") then -- BASECRAWL.inc:179
        if ctx:condition("g_nLastRunawayTime!=0") then -- BASECRAWL.inc:180
            ctx:getTime("g_nTemp") -- BASECRAWL.inc:181
            ctx:sub("g_nTemp", "g_nLastRunawayTime") -- BASECRAWL.inc:182
            if ctx:condition("g_nTemp < MIN_RUN_AWAY_AGAIN_TIME") then -- BASECRAWL.inc:184
                do return ctx:exit("") end -- BASECRAWL.inc:185
            end -- BASECRAWL.inc:186
        end -- BASECRAWL.inc:187
    end -- BASECRAWL.inc:188
    ctx:state().g_bTemp = ctx:self():shouldRunAwayFrom(ctx:object("g_hObject")) -- BASECRAWL.inc:190
    do return ctx:exit("") end -- BASECRAWL.inc:192
end

script.labels["BaseRunCancel"] = function(ctx)
    -- BASECRAWL.inc:195
    mm9.gosub(script, ctx, "BaseRunCancel") -- BASECRAWL.inc:197
    ctx:onEvent("OnProjectile", "OnProjectile") -- BASECRAWL.inc:199
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- BASECRAWL.inc:200
    ctx:onEvent("OnHelp", "OnHelp") -- BASECRAWL.inc:201
    ctx:onEvent("OnAlert", "OnAlert") -- BASECRAWL.inc:202
    ctx:onEvent("OnLostTarget", "OnLostTarget") -- BASECRAWL.inc:203
    if ctx:condition("g_hTarget!=NULL") then -- BASECRAWL.inc:205
        mm9.gosub(script, ctx, "ClearTarget") -- BASECRAWL.inc:206
    end -- BASECRAWL.inc:207
    do return ctx:exit("") end -- BASECRAWL.inc:209
end

script.labels["BaseRunAway"] = function(ctx)
    -- BASECRAWL.inc:213
    ctx:self():stop() -- BASECRAWL.inc:216
    mm9.gosub(script, ctx, "AggressiveStop") -- BASECRAWL.inc:217
    mm9.gosub(script, ctx, "DisableWandering") -- BASECRAWL.inc:218
    mm9.gosub(script, ctx, "SpeedThrottleStop") -- BASECRAWL.inc:219
    ctx:onEvent("OnProjectile") -- BASECRAWL.inc:221
    ctx:onEvent("OnFoundPlayer") -- BASECRAWL.inc:222
    ctx:onEvent("OnTargetOutOfRange") -- BASECRAWL.inc:223
    ctx:onEvent("OnHelp") -- BASECRAWL.inc:224
    ctx:onEvent("OnAlert") -- BASECRAWL.inc:225
    mm9.gosub(script, ctx, "BaseRunAway") -- BASECRAWL.inc:227
    do return ctx:exit("") end -- BASECRAWL.inc:229
end

script.labels["ShouldAttack"] = function(ctx)
    -- BASECRAWL.inc:232
    -- Sets g_bTemp to TRUE or FALSE
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:237
        ctx:state().g_bTemp = false -- BASECRAWL.inc:238
        do return ctx:exit("") end -- BASECRAWL.inc:239
    end -- BASECRAWL.inc:240
    ctx:state().g_bTemp, ctx:state().g_hObstacle = ctx:self():isClearShot(ctx:object("g_hTarget")) -- BASECRAWL.inc:242
    do return ctx:exit("") end -- BASECRAWL.inc:244
end

script.labels["AggressiveInRange"] = function(ctx)
    -- BASECRAWL.inc:247
    -- They're within melee attack range....
    ctx:state().g_bCanReach = true -- BASECRAWL.inc:253
    ctx:state().g_bTemp = ctx:self():canAttack() -- BASECRAWL.inc:255
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:257
        mm9.gosub(script, ctx, "ShouldAttack") -- BASECRAWL.inc:258
    end -- BASECRAWL.inc:259
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:261
        if ctx:condition("g_hObstacle!=NULL") then -- BASECRAWL.inc:263
            ctx:state().g_btemp = ctx:object("g_hObject"):isClass("Actor") -- BASECRAWL.inc:265
            if ctx:condition("g_bTemp!=TRUE") then -- BASECRAWL.inc:267
                ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObstacle")) -- BASECRAWL.inc:268
                if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:270
                    -- If not a friend, then let's just set him up as our new target!
                    ctx:set("g_hTarget", "g_hObstacle") -- BASECRAWL.inc:274
                    mm9.gosub(script, ctx, "SetupTarget") -- BASECRAWL.inc:275
                    do return ctx:exit("") end -- BASECRAWL.inc:276
                end -- BASECRAWL.inc:277
                ctx:state().g_bTemp = ctx:object("g_hObstacle"):isClass("Actor") -- BASECRAWL.inc:279
                if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:281
                    mm9.gosub(script, ctx, "AggressiveOutOfRange") -- BASECRAWL.inc:282
                    do return ctx:exit("") end -- BASECRAWL.inc:283
                end -- BASECRAWL.inc:284
            end -- BASECRAWL.inc:285
        end -- BASECRAWL.inc:287
        ctx:set("g_nTemp", "g_attackRange * 0.75") -- BASECRAWL.inc:289
        if ctx:condition("g_nDist < g_nTemp") then -- BASECRAWL.inc:291
            mm9.gosub(script, ctx, "IsTargetMoving") -- BASECRAWL.inc:293
            if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:295
                ctx:self():stop() -- BASECRAWL.inc:296
            end -- BASECRAWL.inc:297
        end -- BASECRAWL.inc:298
    else -- BASECRAWL.inc:299
        mm9.gosub(script, ctx, "DoAttack") -- BASECRAWL.inc:300
    end -- BASECRAWL.inc:301
    do return ctx:exit("") end -- BASECRAWL.inc:303
end

script.labels["GetTimeToTarget"] = function(ctx)
    -- BASECRAWL.inc:307
    -- returns in g_nTimeToTarget
    ctx:state().g_nTargetDist = 0 -- BASECRAWL.inc:311
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:313
        do return ctx:exit("") end -- BASECRAWL.inc:314
    end -- BASECRAWL.inc:315
    ctx:state().g_nTargetDist = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASECRAWL.inc:317
    ctx:set("g_nTimeToTarget", "g_nTargetDist / g_runVel") -- BASECRAWL.inc:319
    do return ctx:exit("") end -- BASECRAWL.inc:321
end

script.labels["ShouldRunAfter"] = function(ctx)
    -- BASECRAWL.inc:324
    -- See if they are far enough away that by the time
    -- we get to them, we'll be ready to fight....
    ctx:state().g_bTemp = false -- BASECRAWL.inc:330
    if ctx:condition("g_bDoorOpening==TRUE") then -- BASECRAWL.inc:332
        -- CPRINT dooropening.. Not running after!!
        do return ctx:exit("") end -- BASECRAWL.inc:334
    end -- BASECRAWL.inc:335
    ctx:state().g_bTemp = ctx:self():canAttack() -- BASECRAWL.inc:337
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:339
        do return ctx:exit("") end -- BASECRAWL.inc:340
    end -- BASECRAWL.inc:341
    mm9.gosub(script, ctx, "GetTimeToTarget") -- BASECRAWL.inc:343
    ctx:state().g_nTemp = ctx:self():getStat("RecoveryTimeLeft") -- BASECRAWL.inc:345
    if ctx:condition("g_nTemp < g_nTimeToTarget") then -- BASECRAWL.inc:347
        ctx:state().g_bTemp = true -- BASECRAWL.inc:348
    end -- BASECRAWL.inc:349
    do return ctx:exit("") end -- BASECRAWL.inc:351
end

script.labels["AggressiveOutOfRange"] = function(ctx)
    -- BASECRAWL.inc:354
    -- They're beyond our attack range.  See if they are out of reach.  If so,
    -- just stop...
    -- Otherwise, try to go after him....
    ctx:state().g_bTemp = ctx:object("g_hTarget"):getStat("IsFlying") -- BASECRAWL.inc:362
    if ctx:condition("g_bCanReach==FALSE") then -- BASECRAWL.inc:364
        mm9.gosub(script, ctx, "CanReachTarget") -- BASECRAWL.inc:365
    end -- BASECRAWL.inc:366
    if ctx:condition("g_bCanReach==TRUE") then -- BASECRAWL.inc:368
        ctx:getTime("g_nTemp") -- BASECRAWL.inc:369
        ctx:set("g_nTemp", "g_nTemp - g_nLastCanReachCheck") -- BASECRAWL.inc:370
        ctx:state().g_bTemp = false -- BASECRAWL.inc:372
        if ctx:condition("g_bCanReach==FALSE") then -- BASECRAWL.inc:373
            if ctx:condition("g_nTemp > MIN_CHECK_REACH_TIME2") then -- BASECRAWL.inc:374
                ctx:state().g_bTemp = true -- BASECRAWL.inc:375
            end -- BASECRAWL.inc:376
        else -- BASECRAWL.inc:377
            if ctx:condition("g_nTemp > MIN_CHECK_REACH_TIME") then -- BASECRAWL.inc:378
                ctx:state().g_bTemp = true -- BASECRAWL.inc:379
            end -- BASECRAWL.inc:380
        end -- BASECRAWL.inc:381
        if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:383
            mm9.gosub(script, ctx, "CanReachTarget") -- BASECRAWL.inc:384
            if ctx:condition("g_bCanReach==FALSE") then -- BASECRAWL.inc:385
                ctx:self():stop() -- BASECRAWL.inc:386
            end -- BASECRAWL.inc:387
        end -- BASECRAWL.inc:388
    end -- BASECRAWL.inc:389
    if ctx:condition("g_bCanReach==TRUE") then -- BASECRAWL.inc:391
        mm9.gosub(script, ctx, "ShouldRunAfter") -- BASECRAWL.inc:392
        if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:393
            mm9.gosub(script, ctx, "BaseCrawlGetHim") -- BASECRAWL.inc:394
        else -- BASECRAWL.inc:395
            -- Stop
        end -- BASECRAWL.inc:397
    end -- BASECRAWL.inc:398
    do return ctx:exit("") end -- BASECRAWL.inc:400
end

script.labels["GiveUpOnTarget"] = function(ctx)
    -- BASECRAWL.inc:403
    mm9.gosub(script, ctx, "ClearTarget") -- BASECRAWL.inc:405
    do return ctx:exit("") end -- BASECRAWL.inc:407
end

script.labels["AggressiveTick"] = function(ctx)
    -- BASECRAWL.inc:410
    -- See's if we are within range to attack and such...
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "AggressiveTick") -- BASECRAWL.inc:416
    ctx:getTime("g_nTime") -- BASECRAWL.inc:418
    ctx:set("g_nTemp", "g_nLastAttackTime + MAX_CHASE_TIME") -- BASECRAWL.inc:420
    if ctx:condition("g_nTime > g_nTemp") then -- BASECRAWL.inc:422
        -- Time to give up on this target!
        mm9.gosub(script, ctx, "GiveUpOnTarget") -- BASECRAWL.inc:424
        do return ctx:exit("") end -- BASECRAWL.inc:425
    end -- BASECRAWL.inc:426
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:428
        do return ctx:exit("") end -- BASECRAWL.inc:429
    end -- BASECRAWL.inc:430
    ctx:set("g_hObject", "g_hTarget") -- BASECRAWL.inc:432
    mm9.gosub(script, ctx, "ShouldRunAway") -- BASECRAWL.inc:434
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:436
        mm9.gosub(script, ctx, "BaseRunAway") -- BASECRAWL.inc:437
        do return ctx:exit("") end -- BASECRAWL.inc:438
    end -- BASECRAWL.inc:439
    -- if we are within attack range do our attack...
    ctx:state().g_nTargetDist = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASECRAWL.inc:444
    if ctx:condition("g_nTargetDist < g_attackRange") then -- BASECRAWL.inc:446
        mm9.gosub(script, ctx, "AggressiveInRange") -- BASECRAWL.inc:447
    else -- BASECRAWL.inc:448
        mm9.gosub(script, ctx, "AggressiveOutOfRange") -- BASECRAWL.inc:449
    end -- BASECRAWL.inc:450
    do return ctx:exit("") end -- BASECRAWL.inc:452
end

script.labels["AttackArrival"] = function(ctx)
    -- BASECRAWL.inc:457
    do return ctx:exit("TRUE") end -- BASECRAWL.inc:460
end

script.labels["TargetMoving"] = function(ctx)
    -- BASECRAWL.inc:463
    -- Run after him....
    ctx:state().g_nDist = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASECRAWL.inc:469
    if ctx:condition("g_nDist > g_runAfterRange") then -- BASECRAWL.inc:471
        ctx:self():runTo(ctx:object("g_hTarget"), "g_runToRange", "AttackArrival") -- BASECRAWL.inc:472
    end -- BASECRAWL.inc:473
    do return ctx:exit("") end -- BASECRAWL.inc:475
end

script.labels["TargetStill"] = function(ctx)
    -- BASECRAWL.inc:478
    ctx:state().g_nDist = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASECRAWL.inc:481
    ctx:state().g_bTemp = ctx:self():isMoving() -- BASECRAWL.inc:483
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:485
        if ctx:condition("g_nDist < g_attackRange") then -- BASECRAWL.inc:486
            if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:487
                ctx:self():stop() -- BASECRAWL.inc:488
            end -- BASECRAWL.inc:489
        end -- BASECRAWL.inc:490
    else -- BASECRAWL.inc:491
        if ctx:condition("g_nDist > g_attackRange") then -- BASECRAWL.inc:492
            ctx:self():runTo(ctx:object("g_hTarget"), "g_runToRange", "AttackArrival") -- BASECRAWL.inc:493
        end -- BASECRAWL.inc:494
    end -- BASECRAWL.inc:495
    do return ctx:exit("") end -- BASECRAWL.inc:497
end

script.labels["AttackTick"] = function(ctx)
    -- BASECRAWL.inc:501
    -- Keep us near the target if they're moving....
    ctx:state().g_bTemp = ctx:self():isAttacking() -- BASECRAWL.inc:507
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:509
        mm9.gosub(script, ctx, "AttackDone") -- BASECRAWL.inc:510
        do return ctx:exit("") end -- BASECRAWL.inc:511
    end -- BASECRAWL.inc:512
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "AttackTick") -- BASECRAWL.inc:514
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:516
        do return ctx:exit("") end -- BASECRAWL.inc:517
    end -- BASECRAWL.inc:518
    mm9.gosub(script, ctx, "IsTargetMoving") -- BASECRAWL.inc:520
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:522
        mm9.gosub(script, ctx, "TargetMoving") -- BASECRAWL.inc:523
    else -- BASECRAWL.inc:524
        mm9.gosub(script, ctx, "TargetStill") -- BASECRAWL.inc:525
    end -- BASECRAWL.inc:526
    do return ctx:exit("") end -- BASECRAWL.inc:528
end

script.labels["AttackDoneCallback"] = function(ctx)
    -- BASECRAWL.inc:531
    -- Just exit TRUE.  This will cause us NOT to stop..
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:537
        ctx:self():stop() -- BASECRAWL.inc:538
    end -- BASECRAWL.inc:539
    do return ctx:exit("TRUE") end -- BASECRAWL.inc:541
end

script.labels["AttackObstacle"] = function(ctx)
    -- BASECRAWL.inc:544
    -- p0 - hObstacle
    ctx:getParam(0, "g_hObject") -- BASECRAWL.inc:549
    if ctx:condition("g_hObject==g_hTarget") then -- BASECRAWL.inc:551
        ctx:self():stop() -- BASECRAWL.inc:552
        do return ctx:exit("TRUE") end -- BASECRAWL.inc:553
    end -- BASECRAWL.inc:554
    do return ctx:exit("FALSE") end -- BASECRAWL.inc:556
end

script.labels["AttackTargetMoved"] = function(ctx)
    -- BASECRAWL.inc:559
    mm9.gosub(script, ctx, "IsTargetMoving") -- BASECRAWL.inc:561
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:563
        do return ctx:exit("") end -- BASECRAWL.inc:564
    end -- BASECRAWL.inc:565
    if ctx:condition("g_bResurrecting==TRUE") then -- BASECRAWL.inc:567
        do return ctx:exit("") end -- BASECRAWL.inc:568
    end -- BASECRAWL.inc:569
    ctx:self():runTo(ctx:object("g_hTarget"), "g_runToRange", "AttackArrival") -- BASECRAWL.inc:571
    do return ctx:exit("") end -- BASECRAWL.inc:573
end

script.labels["PreAttack"] = function(ctx)
    -- BASECRAWL.inc:576
    mm9.gosub(script, ctx, "AggressiveStop") -- BASECRAWL.inc:578
    ctx:getTime("g_nLastAttackTime") -- BASECRAWL.inc:580
    -- Make sure we face our target during the attack anim...
    ctx:self():faceObject(ctx:object("g_hTarget"), 360) -- BASECRAWL.inc:583
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASECRAWL.inc:584
    ctx:onEvent("OnObstacle", "AttackObstacle") -- BASECRAWL.inc:586
    ctx:onEvent("OnTargetBeyondDist", "g_runAfterRange", "AttackTargetMoved") -- BASECRAWL.inc:588
    do return ctx:exit("") end -- BASECRAWL.inc:591
end

script.labels["MeleeAttack"] = function(ctx)
    -- BASECRAWL.inc:594
    ctx:state().g_bAttackPerformed = false -- BASECRAWL.inc:597
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "AttackTick") -- BASECRAWL.inc:598
    ctx:self():attack("AttackDoneCallback") -- BASECRAWL.inc:599
    do return ctx:exit("") end -- BASECRAWL.inc:601
end

script.labels["PostAttack"] = function(ctx)
    -- BASECRAWL.inc:604
    -- virtual function only...
    do return ctx:exit("") end -- BASECRAWL.inc:608
end

script.labels["DoAttack"] = function(ctx)
    -- BASECRAWL.inc:611
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:614
        ctx:debugOut("(DoAttack)", "ASSERT(g_hTarget!=NULL)") -- BASECRAWL.inc:615
        ctx:self():stop() -- BASECRAWL.inc:616
        do return ctx:exit("") end -- BASECRAWL.inc:617
    end -- BASECRAWL.inc:618
    mm9.gosub(script, ctx, "PreAttack") -- BASECRAWL.inc:621
    mm9.gosub(script, ctx, "MeleeAttack") -- BASECRAWL.inc:622
    mm9.gosub(script, ctx, "PostAttack") -- BASECRAWL.inc:623
    do return ctx:exit("") end -- BASECRAWL.inc:626
end

script.labels["AttackTickCancel"] = function(ctx)
    -- BASECRAWL.inc:629
    ctx:wait("AGGRESSIVE_WAIT", 0, "DoNothing") -- BASECRAWL.inc:631
    do return ctx:exit("") end -- BASECRAWL.inc:632
end

script.labels["AttackDone"] = function(ctx)
    -- BASECRAWL.inc:635
    -- Cancel our attack tick...
    mm9.gosub(script, ctx, "AttackTickCancel") -- BASECRAWL.inc:643
    ctx:onEvent("OnTargetBeyondDist", 0) -- BASECRAWL.inc:645
    ctx:self():setStat("RunVel", "g_runVel") -- BASECRAWL.inc:647
    mm9.gosub(script, ctx, "IsTargetMoving") -- BASECRAWL.inc:649
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:651
        ctx:self():stop() -- BASECRAWL.inc:652
    end -- BASECRAWL.inc:653
    if ctx:condition("g_hTarget!=NULL") then -- BASECRAWL.inc:655
        ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hTarget")) -- BASECRAWL.inc:656
        if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:657
            ctx:self():stop() -- BASECRAWL.inc:658
            mm9.gosub(script, ctx, "ClearTarget") -- BASECRAWL.inc:659
            do return ctx:exit("TRUE") end -- BASECRAWL.inc:660
        end -- BASECRAWL.inc:661
    end -- BASECRAWL.inc:662
    mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:664
    do return ctx:exit("TRUE") end -- BASECRAWL.inc:666
end

script.labels["AwareDone"] = function(ctx)
    -- BASECRAWL.inc:670
    mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:673
    do return ctx:exit("") end -- BASECRAWL.inc:675
end

script.labels["SetupTarget"] = function(ctx)
    -- BASECRAWL.inc:678
    mm9.gosub(script, ctx, "BaseRunCowerStop") -- BASECRAWL.inc:681
    mm9.gosub(script, ctx, "DisableWandering") -- BASECRAWL.inc:682
    ctx:state().g_hAttacker = nil -- BASECRAWL.inc:684
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASECRAWL.inc:686
    mm9.gosub(script, ctx, "AlertStart") -- BASECRAWL.inc:688
    ctx:getTime("g_nLastAttackTime") -- BASECRAWL.inc:690
    -- Once we've seen the player, double our vision and hearing
    -- distances.  Make sure we see them a little better once we've
    -- targeted them
    ctx:state().g_bTemp = ctx:object("g_hTarget"):isPlayer() -- BASECRAWL.inc:697
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:699
        if ctx:condition("g_bFirstPlayerTime==FALSE") then -- BASECRAWL.inc:700
            ctx:state().g_bFirstPlayerTime = true -- BASECRAWL.inc:701
            ctx:state().g_nTemp = ctx:self():getStat("VisibleRange") -- BASECRAWL.inc:702
            ctx:set("g_nTemp", "g_nTemp * 2") -- BASECRAWL.inc:703
            ctx:self():setStat("VisibleRange", "g_nTemp") -- BASECRAWL.inc:704
            ctx:state().g_nTemp = ctx:self():getStat("HearingRange") -- BASECRAWL.inc:705
            ctx:set("g_nTemp", "g_nTemp * 2") -- BASECRAWL.inc:706
            ctx:self():setStat("HearingRange", "g_nTemp") -- BASECRAWL.inc:707
        end -- BASECRAWL.inc:708
    end -- BASECRAWL.inc:709
    do return ctx:exit("") end -- BASECRAWL.inc:711
end

script.labels["OnFoundTarget"] = function(ctx)
    -- BASECRAWL.inc:714
    -- p0	- hTarget
    if ctx:condition("g_bResurrecting==TRUE") then -- BASECRAWL.inc:720
        do return ctx:exit("") end -- BASECRAWL.inc:721
    end -- BASECRAWL.inc:722
    ctx:getParam(0, "g_hObject") -- BASECRAWL.inc:724
    mm9.gosub(script, ctx, "ShouldRunAfterNewTarget") -- BASECRAWL.inc:726
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:728
        ctx:set("g_hTarget", "g_hObject") -- BASECRAWL.inc:729
        ctx:self():setTarget(ctx:object("g_hTarget")) -- BASECRAWL.inc:730
        mm9.gosub(script, ctx, "BaseRunAway") -- BASECRAWL.inc:731
        do return ctx:exit("") end -- BASECRAWL.inc:732
    end -- BASECRAWL.inc:733
    ctx:set("g_hTarget", "g_hObject") -- BASECRAWL.inc:735
    mm9.gosub(script, ctx, "SetupTarget") -- BASECRAWL.inc:737
    mm9.gosub(script, ctx, "AggressiveStop") -- BASECRAWL.inc:738
    ctx:randomInt(0, 100, "g_nRandom") -- BASECRAWL.inc:740
    if ctx:condition("g_nRandom < AWARE_CHANCE") then -- BASECRAWL.inc:742
        ctx:self():taunt("AwareDone") -- BASECRAWL.inc:743
    else -- BASECRAWL.inc:744
        mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:745
    end -- BASECRAWL.inc:746
    do return ctx:exit("") end -- BASECRAWL.inc:748
end

script.labels["OnDamage"] = function(ctx)
    -- BASECRAWL.inc:751
    -- p0 - hDamager
    ctx:getParam(0, "g_hAttacker") -- BASECRAWL.inc:757
    if ctx:condition("g_hAttacker==g_hTarget") then -- BASECRAWL.inc:759
        ctx:getTime("g_lastDamageTime") -- BASECRAWL.inc:760
        do return ctx:exit("") end -- BASECRAWL.inc:761
    end -- BASECRAWL.inc:762
    mm9.gosub(script, ctx, "SetupAttacker") -- BASECRAWL.inc:764
    do return ctx:exit("") end -- BASECRAWL.inc:766
end

script.labels["OnDamageDone"] = function(ctx)
    -- BASECRAWL.inc:769
    if ctx:condition("g_hAttacker==NULL") then -- BASECRAWL.inc:772
        do return ctx:exit("FALSE") end -- BASECRAWL.inc:773
    end -- BASECRAWL.inc:774
    mm9.gosub(script, ctx, "NewTargetCheck") -- BASECRAWL.inc:776
    do return ctx:exit("") end -- BASECRAWL.inc:778
end

script.labels["ClearTarget"] = function(ctx)
    -- BASECRAWL.inc:781
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:784
        do return ctx:exit("") end -- BASECRAWL.inc:785
    end -- BASECRAWL.inc:786
    -- Don't need speed throttling when we're not attacking anyone..
    ctx:set("g_hLastTarget", "g_hTarget") -- BASECRAWL.inc:790
    ctx:state().g_hTarget = nil -- BASECRAWL.inc:791
    mm9.gosub(script, ctx, "BaseRunCancel") -- BASECRAWL.inc:793
    mm9.gosub(script, ctx, "SpeedThrottleStop") -- BASECRAWL.inc:794
    mm9.gosub(script, ctx, "AggressiveStop") -- BASECRAWL.inc:795
    mm9.gosub(script, ctx, "AlertStop") -- BASECRAWL.inc:796
    ctx:self():setTarget(nil) -- BASECRAWL.inc:798
    ctx:self():stop() -- BASECRAWL.inc:799
    mm9.gosub(script, ctx, "EnableWandering") -- BASECRAWL.inc:801
    do return ctx:exit("") end -- BASECRAWL.inc:803
end

script.labels["OnLostTarget"] = function(ctx)
    -- BASECRAWL.inc:806
    mm9.gosub(script, ctx, "ClearTarget") -- BASECRAWL.inc:809
    do return ctx:exit("") end -- BASECRAWL.inc:811
end

script.labels["KilledTargetTaunt"] = function(ctx)
    -- BASECRAWL.inc:814
    ctx:self():taunt() -- BASECRAWL.inc:816
    do return ctx:exit("") end -- BASECRAWL.inc:818
end

script.labels["OnTargetDead"] = function(ctx)
    -- BASECRAWL.inc:821
    -- p0 - hKiller
    -- To be safe, just clear this out as well.
    ctx:state().g_hAttacker = nil -- BASECRAWL.inc:830
    mm9.gosub(script, ctx, "ClearTarget") -- BASECRAWL.inc:832
    ctx:getParam(0, "g_hObject") -- BASECRAWL.inc:834
    if ctx:condition("g_hObject==g_hMyObject") then -- BASECRAWL.inc:836
        ctx:self():stop() -- BASECRAWL.inc:837
        ctx:wait("TAUNT_WAIT", 0.5, "KilledTargetTaunt") -- BASECRAWL.inc:838
    end -- BASECRAWL.inc:839
    do return ctx:exit("") end -- BASECRAWL.inc:841
end

script.labels["IsAttackerValidTarget"] = function(ctx)
    -- BASECRAWL.inc:844
    -- Returns g_bTemp = TRUE or FALSE
    ctx:state().g_bTemp = false -- BASECRAWL.inc:849
    if ctx:condition("g_hAttacker==g_hMyObject") then -- BASECRAWL.inc:851
        do return ctx:exit("") end -- BASECRAWL.inc:852
    end -- BASECRAWL.inc:853
    if ctx:condition("g_hAttacker==NULL") then -- BASECRAWL.inc:855
        do return ctx:exit("") end -- BASECRAWL.inc:856
    end -- BASECRAWL.inc:857
    if ctx:condition("g_hAttacker==g_hTarget") then -- BASECRAWL.inc:859
        do return ctx:exit("") end -- BASECRAWL.inc:860
    end -- BASECRAWL.inc:861
    ctx:state().g_bTemp = (ctx:object("g_hAttacker"):isActor() and 1 or 0) -- BASECRAWL.inc:863
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:865
        do return ctx:exit("") end -- BASECRAWL.inc:866
    end -- BASECRAWL.inc:867
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hAttacker")) -- BASECRAWL.inc:869
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:871
        ctx:state().g_bTemp = false -- BASECRAWL.inc:872
        do return ctx:exit("") end -- BASECRAWL.inc:873
    else -- BASECRAWL.inc:874
        ctx:state().g_bTemp = true -- BASECRAWL.inc:875
    end -- BASECRAWL.inc:876
    ctx:state().g_bTemp = ctx:object("g_hAttacker"):getStat("IsDead") -- BASECRAWL.inc:878
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:880
        ctx:state().g_bTemp = false -- BASECRAWL.inc:881
        do return ctx:exit("") end -- BASECRAWL.inc:882
    end -- BASECRAWL.inc:883
    ctx:state().g_bTemp = true -- BASECRAWL.inc:885
    do return ctx:exit("") end -- BASECRAWL.inc:887
end

script.labels["NewTargetCheck"] = function(ctx)
    -- BASECRAWL.inc:890
    -- Fill in g_hAttacker with the potential new target,
    -- and this function takes care of the rest....
    ctx:set("g_nTemp", "g_nLastAttackTime + MAX_CHASE_TIME") -- BASECRAWL.inc:897
    if ctx:condition("m_hTarget!=NULL") then -- BASECRAWL.inc:899
        ctx:getTime("g_nTime") -- BASECRAWL.inc:900
        if ctx:condition("g_nTime > g_nTemp") then -- BASECRAWL.inc:901
            -- Time to give up on this target!
            mm9.gosub(script, ctx, "GiveUpOnTarget") -- BASECRAWL.inc:903
        end -- BASECRAWL.inc:904
    end -- BASECRAWL.inc:905
    if ctx:condition("g_bResurrecting==TRUE") then -- BASECRAWL.inc:907
        do return mm9.gotoLabel(script, ctx, "NewTargetCheckFailed") end -- BASECRAWL.inc:908
    end -- BASECRAWL.inc:909
    if ctx:condition("g_hAttacker==NULL") then -- BASECRAWL.inc:911
        do return mm9.gotoLabel(script, ctx, "NewTargetCheckFailed") end -- BASECRAWL.inc:912
    end -- BASECRAWL.inc:913
    ctx:state().g_hTarget = ctx:self():target() -- BASECRAWL.inc:915
    mm9.gosub(script, ctx, "IsAttackerValidTarget") -- BASECRAWL.inc:917
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:919
        do return mm9.gotoLabel(script, ctx, "NewTargetCheckFailed") end -- BASECRAWL.inc:920
    end -- BASECRAWL.inc:921
    if ctx:condition("g_bRunningAway==TRUE") then -- BASECRAWL.inc:923
        do return mm9.gotoLabel(script, ctx, "NewTargetCheckFailed") end -- BASECRAWL.inc:924
    end -- BASECRAWL.inc:925
    if ctx:condition("g_bCowering==TRUE") then -- BASECRAWL.inc:927
        do return mm9.gotoLabel(script, ctx, "NewTargetCheckFailed") end -- BASECRAWL.inc:928
    end -- BASECRAWL.inc:929
    -- if we don't currently have a target, then he's our man....
    if ctx:condition("g_hTarget==NULL") then -- BASECRAWL.inc:934
        ctx:set("g_hTarget", "g_hAttacker") -- BASECRAWL.inc:935
        ctx:state().g_hAttacker = nil -- BASECRAWL.inc:936
        mm9.gosub(script, ctx, "SetupTarget") -- BASECRAWL.inc:937
        ctx:self():setTarget(ctx:object("g_hTarget")) -- BASECRAWL.inc:938
        mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:939
        do return ctx:exit("TRUE") end -- BASECRAWL.inc:940
    end -- BASECRAWL.inc:941
    -- We have a target, decide if we should switch.......
    ctx:state().g_bInAttackRange = ctx:self():isTargetInRange() -- BASECRAWL.inc:947
    -- 70% chance we'll switch to the damager
    ctx:state().g_nTemp = 70 -- BASECRAWL.inc:950
    if ctx:condition("g_bInAttackRange==TRUE") then -- BASECRAWL.inc:951
        -- we're already in attack range of our current target
        -- so lower chances of switching
        ctx:state().g_nTemp = 45 -- BASECRAWL.inc:954
    end -- BASECRAWL.inc:955
    ctx:state().g_nDist1 = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASECRAWL.inc:957
    ctx:state().g_nDist2 = ctx:self():aiDistanceTo(ctx:object("g_hAttacker")) -- BASECRAWL.inc:958
    if ctx:condition("g_nDist2 > g_nDist1") then -- BASECRAWL.inc:960
        -- reduce odds even further...
        ctx:set("g_nTemp", "g_nTemp / 2") -- BASECRAWL.inc:962
    else -- BASECRAWL.inc:963
        -- increase odds if attacker is less than 1/2 the distance to
        -- current target...
        ctx:set("g_nDist1", "g_nDist1 * 2") -- BASECRAWL.inc:968
        if ctx:condition("g_nDist2 < g_nDist1") then -- BASECRAWL.inc:970
            ctx:set("g_nTemp", "g_nTemp * 1.15") -- BASECRAWL.inc:971
        end -- BASECRAWL.inc:972
    end -- BASECRAWL.inc:973
    ctx:randomInt(0, 100, "g_nRandom") -- BASECRAWL.inc:975
    if ctx:condition("g_nRandom < g_nTemp") then -- BASECRAWL.inc:976
        -- Okay, we decided to switch our current target to the
        -- attacker!
        ctx:set("g_hTarget", "g_hAttacker") -- BASECRAWL.inc:981
        ctx:state().g_hAttacker = nil -- BASECRAWL.inc:982
        mm9.gosub(script, ctx, "SetupTarget") -- BASECRAWL.inc:983
        mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:984
    end -- BASECRAWL.inc:985
    do return ctx:exit("TRUE") end -- BASECRAWL.inc:987
end

script.labels["NewTargetCheckFailed"] = function(ctx)
    -- BASECRAWL.inc:989
    -- Break the link to it if needed...
    mm9.gosub(script, ctx, "ClearAttacker") -- BASECRAWL.inc:993
    do return ctx:exit("FALSE") end -- BASECRAWL.inc:995
end

script.labels["OnAlert"] = function(ctx)
    -- BASECRAWL.inc:998
    -- p0 - The alerter
    -- p1 - who he's alerting about....
    ctx:getParam(0, "g_hObject") -- BASECRAWL.inc:1004
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- BASECRAWL.inc:1006
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:1007
        do return ctx:exit("") end -- BASECRAWL.inc:1008
    end -- BASECRAWL.inc:1009
    ctx:getParam(1, "g_hAttacker") -- BASECRAWL.inc:1011
    mm9.gosub(script, ctx, "NewTargetCheck") -- BASECRAWL.inc:1012
    do return ctx:exit("") end -- BASECRAWL.inc:1014
end

script.labels["OnProjectile"] = function(ctx)
    -- BASECRAWL.inc:1017
    -- p0	- hProjectile
    -- p1	- hLaunchedFrom
    -- p2	- dist
    ctx:getParam(0, "g_nTemp") -- BASECRAWL.inc:1025
    ctx:getParam(1, "g_hObject") -- BASECRAWL.inc:1026
    if ctx:condition("g_hObject==g_nTemp") then -- BASECRAWL.inc:1028
        -- Don't take these seriously...
        do return ctx:exit("") end -- BASECRAWL.inc:1032
    end -- BASECRAWL.inc:1033
    mm9.gosub(script, ctx, "NewTargetCheck") -- BASECRAWL.inc:1035
    do return ctx:exit("") end -- BASECRAWL.inc:1037
end

script.labels["AttackPerformed"] = function(ctx)
    -- BASECRAWL.inc:1040
    ctx:state().g_bAttackPerformed = true -- BASECRAWL.inc:1042
    do return ctx:exit("FALSE") end -- BASECRAWL.inc:1043
end

script.labels["DisableWandering"] = function(ctx)
    -- BASECRAWL.inc:1046
    -- Do all things necessary to disable
    -- Wandering...
    mm9.gosub(script, ctx, "BaseWanderStop") -- BASECRAWL.inc:1053
    ctx:state().bWanderDisabled = true -- BASECRAWL.inc:1055
    ctx:onEvent("OnObstacle") -- BASECRAWL.inc:1057
    ctx:onEvent("OnStuckDone") -- BASECRAWL.inc:1058
    ctx:onEvent("OnStuck") -- BASECRAWL.inc:1059
    do return ctx:exit("") end -- BASECRAWL.inc:1061
end

script.labels["EnableWandering"] = function(ctx)
    -- BASECRAWL.inc:1064
    -- Do all things necessary to enable
    -- Wandering...
    ctx:state().bWanderDisabled = false -- BASECRAWL.inc:1071
    mm9.gosub(script, ctx, "BaseWanderStart") -- BASECRAWL.inc:1072
    do return ctx:exit("") end -- BASECRAWL.inc:1074
end

script.labels["OnHelp"] = function(ctx)
    -- BASECRAWL.inc:1078
    -- p0 - hPoorSlob
    -- p1 - hBadGuy
    if ctx:condition("g_hTarget!=NULL") then -- BASECRAWL.inc:1084
        do return ctx:exit("") end -- BASECRAWL.inc:1085
    end -- BASECRAWL.inc:1086
    ctx:getParam(0, "g_hObject") -- BASECRAWL.inc:1088
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- BASECRAWL.inc:1090
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:1092
        do return ctx:exit("") end -- BASECRAWL.inc:1093
    end -- BASECRAWL.inc:1094
    ctx:getParam(1, "g_hAttacker") -- BASECRAWL.inc:1096
    mm9.gosub(script, ctx, "NewTargetCheck") -- BASECRAWL.inc:1097
    do return ctx:exit("") end -- BASECRAWL.inc:1099
end

script.labels["ResurrectMe"] = function(ctx)
    -- BASECRAWL.inc:1102
    if ctx:condition("g_bRunningAway==TRUE") then -- BASECRAWL.inc:1104
        do return ctx:exit("") end -- BASECRAWL.inc:1105
    end -- BASECRAWL.inc:1106
    mm9.gosub(script, ctx, "ResurrectMe") -- BASECRAWL.inc:1108
    do return ctx:exit("") end -- BASECRAWL.inc:1110
end

script.labels["DelayResurrection"] = function(ctx)
    -- BASECRAWL.inc:1113
    ctx:wait("RESURRECT_WAIT", 0.1, "DoResurrection") -- BASECRAWL.inc:1115
    do return ctx:exit("") end -- BASECRAWL.inc:1116
end

script.labels["OnResurrect"] = function(ctx)
    -- BASECRAWL.inc:1119
    mm9.gosub(script, ctx, "AggressiveStop") -- BASECRAWL.inc:1121
    mm9.gosub(script, ctx, "BaseRunCancel") -- BASECRAWL.inc:1122
    mm9.gosub(script, ctx, "OnResurrect") -- BASECRAWL.inc:1123
    do return ctx:exit("") end -- BASECRAWL.inc:1125
end

script.labels["ResurrectDone"] = function(ctx)
    -- BASECRAWL.inc:1128
    mm9.gosub(script, ctx, "ResurrectDone") -- BASECRAWL.inc:1131
    ctx:set("g_hTarget", "g_hDeathTarget") -- BASECRAWL.inc:1133
    if ctx:condition("g_hTarget!=NULL") then -- BASECRAWL.inc:1135
        mm9.gosub(script, ctx, "SetupTarget") -- BASECRAWL.inc:1136
        mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:1137
    end -- BASECRAWL.inc:1138
    do return ctx:exit("") end -- BASECRAWL.inc:1140
end

script.labels["DoResurrection"] = function(ctx)
    -- BASECRAWL.inc:1143
    if ctx:condition("g_hResurrect==NULL") then -- BASECRAWL.inc:1146
        -- cprint NO ONE TO RESURRECT??
        do return ctx:exit("") end -- BASECRAWL.inc:1148
    end -- BASECRAWL.inc:1149
    ctx:state().g_bTemp = ctx:object("g_hResurrect"):isDead() -- BASECRAWL.inc:1151
    if ctx:condition("g_bTemp==FALSE") then -- BASECRAWL.inc:1153
        ctx:state().g_hResurrect = nil -- BASECRAWL.inc:1154
        do return ctx:exit("") end -- BASECRAWL.inc:1155
    end -- BASECRAWL.inc:1156
    if ctx:condition("g_hTarget!=NULL") then -- BASECRAWL.inc:1158
        ctx:self():setTarget(ctx:object("g_hTarget")) -- BASECRAWL.inc:1159
    end -- BASECRAWL.inc:1160
    ctx:state().g_bTemp = ctx:self():isAttacking() -- BASECRAWL.inc:1162
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:1164
        mm9.gosub(script, ctx, "DelayResurrection") -- BASECRAWL.inc:1165
        do return ctx:exit("") end -- BASECRAWL.inc:1166
    end -- BASECRAWL.inc:1167
    ctx:state().g_bTemp = ctx:self():getStat("IsWincing") -- BASECRAWL.inc:1169
    if ctx:condition("g_bTemp==TRUE") then -- BASECRAWL.inc:1171
        mm9.gosub(script, ctx, "DelayResurrection") -- BASECRAWL.inc:1172
        do return ctx:exit("") end -- BASECRAWL.inc:1173
    end -- BASECRAWL.inc:1174
    mm9.gosub(script, ctx, "DoResurrection") -- BASECRAWL.inc:1176
    mm9.gosub(script, ctx, "AggressiveStop") -- BASECRAWL.inc:1177
    mm9.gosub(script, ctx, "DisableWandering") -- BASECRAWL.inc:1178
    do return ctx:exit("") end -- BASECRAWL.inc:1180
end

script.labels["DoResurrectionDone"] = function(ctx)
    -- BASECRAWL.inc:1183
    mm9.gosub(script, ctx, "DoResurrectionDone") -- BASECRAWL.inc:1185
    mm9.gosub(script, ctx, "BaseRunCancel") -- BASECRAWL.inc:1187
    ctx:state().g_hTarget = ctx:self():target() -- BASECRAWL.inc:1189
    if ctx:condition("g_hTarget!=NULL") then -- BASECRAWL.inc:1191
        mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:1192
        ctx:self():setTarget(ctx:object("g_hTarget")) -- BASECRAWL.inc:1193
    else -- BASECRAWL.inc:1194
        ctx:self():setTarget(nil) -- BASECRAWL.inc:1195
        ctx:self():stop() -- BASECRAWL.inc:1196
        mm9.gosub(script, ctx, "EnableWandering") -- BASECRAWL.inc:1197
    end -- BASECRAWL.inc:1198
    do return ctx:exit("") end -- BASECRAWL.inc:1201
end

script.labels["InitCallbacks"] = function(ctx)
    -- BASECRAWL.inc:1203
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- BASECRAWL.inc:1206
    ctx:onEvent("OnLostTarget", "OnLostTarget") -- BASECRAWL.inc:1207
    ctx:onEvent("OnDamageDone", "OnDamageDone") -- BASECRAWL.inc:1208
    ctx:onEvent("OnDamage", "OnDamage") -- BASECRAWL.inc:1209
    ctx:onEvent("OnTargetDead", "OnTargetDead") -- BASECRAWL.inc:1210
    ctx:onEvent("OnAlert", "OnAlert") -- BASECRAWL.inc:1211
    ctx:onEvent("OnProjectile", "OnProjectile") -- BASECRAWL.inc:1212
    ctx:onEvent("OnHelp", "OnHelp") -- BASECRAWL.inc:1213
    mm9.gosub(script, ctx, "InitCommon") -- BASECRAWL.inc:1215
    do return ctx:exit("") end -- BASECRAWL.inc:1217
end

script.labels["OnDeath"] = function(ctx)
    -- BASECRAWL.inc:1220
    mm9.gosub(script, ctx, "OnDeath") -- BASECRAWL.inc:1222
    ctx:set("g_hObject", "g_hTarget") -- BASECRAWL.inc:1224
    mm9.gosub(script, ctx, "BaseRunCancel") -- BASECRAWL.inc:1225
    mm9.gosub(script, ctx, "ClearTarget") -- BASECRAWL.inc:1226
    mm9.gosub(script, ctx, "DisableWandering") -- BASECRAWL.inc:1227
    ctx:set("g_hTarget", "g_hObject") -- BASECRAWL.inc:1228
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASECRAWL.inc:1229
    do return ctx:exit("") end -- BASECRAWL.inc:1231
end

script.labels["OnGetPlayer"] = function(ctx)
    -- BASECRAWL.inc:1234
    mm9.gosub(script, ctx, "ClearTarget") -- BASECRAWL.inc:1236
    ctx:state().g_hTarget = ctx:player() -- BASECRAWL.inc:1237
    mm9.gosub(script, ctx, "SetupTarget") -- BASECRAWL.inc:1238
    mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:1239
    do return ctx:exit("") end -- BASECRAWL.inc:1241
end

script.labels["OnGetMe"] = function(ctx)
    -- BASECRAWL.inc:1244
    mm9.gosub(script, ctx, "ClearTarget") -- BASECRAWL.inc:1246
    ctx:getParam(0, "g_hTarget") -- BASECRAWL.inc:1247
    mm9.gosub(script, ctx, "SetupTarget") -- BASECRAWL.inc:1248
    mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:1249
    do return ctx:exit("") end -- BASECRAWL.inc:1251
end

script.labels["BaseCrawlInit"] = function(ctx)
    -- BASECRAWL.inc:1254
    mm9.gosub(script, ctx, "InitCallbacks") -- BASECRAWL.inc:1259
    ctx:addModelKey("rAttack", "AttackPerformed") -- BASECRAWL.inc:1261
    ctx:addModelKey("lAttack", "AttackPerformed") -- BASECRAWL.inc:1262
    ctx:addModelKey("Bite", "AttackPerformed") -- BASECRAWL.inc:1263
    ctx:addModelKey("rKick", "AttackPerformed") -- BASECRAWL.inc:1264
    ctx:addModelKey("lKick", "AttackPerformed") -- BASECRAWL.inc:1265
    ctx:addTrigger("GetPlayer", "OnGetPlayer") -- BASECRAWL.inc:1266
    ctx:state().g_runVel = ctx:self():getStat("RunVel") -- BASECRAWL.inc:1268
    ctx:state().g_walkVel = ctx:self():getStat("WalkVel") -- BASECRAWL.inc:1269
    ctx:state().g_attackRange = ctx:self():getStat("AttackRange") -- BASECRAWL.inc:1270
    ctx:set("g_runToRange", "g_attackRange * 0.95") -- BASECRAWL.inc:1272
    ctx:set("g_runAfterRange", "g_attackRange * 0.70") -- BASECRAWL.inc:1273
    mm9.gosub(script, ctx, "BaseWanderInit") -- BASECRAWL.inc:1275
    mm9.gosub(script, ctx, "BaseRunInit") -- BASECRAWL.inc:1276
    -- make sure we can open doors....
    mm9.gosub(script, ctx, "BaseDoorInit") -- BASECRAWL.inc:1277
    ctx:state().g_hTarget = ctx:self():target() -- BASECRAWL.inc:1279
    if ctx:condition("g_hTarget!=NULL") then -- BASECRAWL.inc:1281
        mm9.gosub(script, ctx, "SetupTarget") -- BASECRAWL.inc:1282
        mm9.gosub(script, ctx, "AggressiveStart") -- BASECRAWL.inc:1283
    end -- BASECRAWL.inc:1284
    do return ctx:exit("") end -- BASECRAWL.inc:1286
end

return script
