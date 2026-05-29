-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 16, path = "baseTimers.inc" }
script.includes[#script.includes + 1] = { line = 17, path = "baseWander.inc" }
script.includes[#script.includes + 1] = { line = 18, path = "BaseRun.inc" }
script.includes[#script.includes + 1] = { line = 19, path = "BaseEvade.inc" }
script.includes[#script.includes + 1] = { line = 20, path = "BaseDoor.inc" }
script.includes[#script.includes + 1] = { line = 21, path = "SpeedThrottle.inc" }

-- base.inc
-- Jeff Leggett
-- This include file contains base monster
-- handling.  Basically, the monster sees
-- the player.  Runs after him and keeps
-- attacking.  Nothing fancy here.
-- NOTE: Be sure to gosub InitBase in your
-- :main routine.
script.labels["BaseStuck"] = function(ctx)
    -- BASE.inc:69
    ctx:self():setIdle() -- BASE.inc:72
    do return ctx:exit("TRUE") end -- BASE.inc:74
end

script.labels["DisableWandering"] = function(ctx)
    -- BASE.inc:77
    -- Do all things necessary to disable
    -- Wandering...
    mm9.gosub(script, ctx, "BaseWanderStop") -- BASE.inc:84
    ctx:onEvent("OnObstacle", "BaseObstacle") -- BASE.inc:86
    ctx:onEvent("OnStuckDone", "BaseStuckDone") -- BASE.inc:87
    ctx:onEvent("OnStuck", "BaseStuck") -- BASE.inc:88
    do return ctx:exit("") end -- BASE.inc:90
end

script.labels["EnableWandering"] = function(ctx)
    -- BASE.inc:93
    -- Do all things necessary to disable
    -- Wandering...
    mm9.gosub(script, ctx, "BaseWanderStart") -- BASE.inc:100
    do return ctx:exit("") end -- BASE.inc:102
end

script.labels["ShouldAttack"] = function(ctx)
    -- BASE.inc:105
    -- output: g_bShouldAttack
    ctx:state().g_bShouldAttack = false -- BASE.inc:109
    ctx:state().g_bClearShot = ctx:self():isClearShot(ctx:object("g_hTarget")) -- BASE.inc:111
    if ctx:condition("g_bClearShot==TRUE") then -- BASE.inc:113
        ctx:state().g_bShouldAttack = true -- BASE.inc:114
        do return ctx:exit("") end -- BASE.inc:115
    end -- BASE.inc:116
    -- Even without a clear shot, sometimes we should
    -- go ahead and attack...
    -- GetRandomInt 0, 100, g_nRandom
    -- if ( g_nRandom < 20 )
    -- g_bShouldAttack = TRUE
    -- endif
    do return ctx:exit("") end -- BASE.inc:129
end

script.labels["BaseGoGetHim"] = function(ctx)
    -- BASE.inc:132
    -- Sets g_bBaseGoGetHim to FALSE if we
    -- didn't run/walk after him...
    ctx:state().g_bBaseGoGetHim = false -- BASE.inc:139
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:141
        do return ctx:exit("FALSE") end -- BASE.inc:142
    end -- BASE.inc:143
    if ctx:condition("g_bRunningAway==TRUE") then -- BASE.inc:145
        do return ctx:exit("TRUE") end -- BASE.inc:146
    end -- BASE.inc:147
    -- IsAttacking g_bAttacking
    -- if ( g_bAttacking==TRUE )
    -- Exit TRUE
    -- endif
    ctx:state().g_targetOutOfReachStart = 0 -- BASE.inc:156
    ctx:state().g_bInAttackRange = ctx:self():isTargetInRange() -- BASE.inc:158
    if ctx:condition("g_bInAttackRange==TRUE") then -- BASE.inc:160
        ctx:state().g_bCanAttack = ctx:self():canAttack() -- BASE.inc:161
        if ctx:condition("g_bCanAttack==TRUE") then -- BASE.inc:163
            mm9.gosub(script, ctx, "ShouldAttack") -- BASE.inc:164
            if ctx:condition("g_bShouldAttack==TRUE") then -- BASE.inc:166
                mm9.gosub(script, ctx, "BaseDoAttack") -- BASE.inc:167
                do return ctx:exit("TRUE") end -- BASE.inc:168
            else -- BASE.inc:169
                -- Go into stuck mode... (just pauses the action, when the stuck anim is done, we'll go after him again)
                -- SetStuck
                do return ctx:exit("TRUE") end -- BASE.inc:172
            end -- BASE.inc:173
        else -- BASE.inc:174
            do return ctx:exit("TRUE") end -- BASE.inc:175
        end -- BASE.inc:176
    end -- BASE.inc:177
    -- Make sure we're using the correct movement callbacks...
    ctx:onEvent("OnCongestion", "BaseCongestion") -- BASE.inc:183
    ctx:onEvent("OnPathClear", "BasePathClear") -- BASE.inc:184
    ctx:onEvent("OnObstacle", "BaseObstacle") -- BASE.inc:185
    ctx:set("g_nTemp", "g_attackRange") -- BASE.inc:187
    ctx:state().g_bTemp = ctx:self():isAttacking() -- BASE.inc:188
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:189
        ctx:mul("g_nTemp", 0.4) -- BASE.inc:190
    else -- BASE.inc:191
        ctx:mul("g_nTemp", 0.6) -- BASE.inc:192
    end -- BASE.inc:193
    if ctx:condition("g_bAlwaysRunToTarget==TRUE") then -- BASE.inc:195
        ctx:self():runTo(ctx:object("g_hTarget"), "g_nTemp", "AggressiveArrival") -- BASE.inc:196
    else -- BASE.inc:197
        if ctx:condition("g_bFighting==TRUE") then -- BASE.inc:199
            ctx:self():runTo(ctx:object("g_hTarget"), "g_nTemp", "AggressiveArrival") -- BASE.inc:200
        else -- BASE.inc:201
            ctx:self():walkTo(ctx:object("g_hTarget"), "g_nTemp", "AggressiveArrival") -- BASE.inc:202
        end -- BASE.inc:203
    end -- BASE.inc:204
    ctx:state().g_bBaseGoGetHim = true -- BASE.inc:206
    do return ctx:exit("TRUE") end -- BASE.inc:208
end

script.labels["AggressiveTick"] = function(ctx)
    -- BASE.inc:212
    ctx:wait("AGGRESSIVE_WAIT", 0.1, "AggressiveTick") -- BASE.inc:215
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:217
        do return ctx:exit("") end -- BASE.inc:218
    end -- BASE.inc:219
    ctx:state().g_bInAttackRange = ctx:self():isTargetInRange() -- BASE.inc:221
    if ctx:condition("g_bInAttackRange==FALSE") then -- BASE.inc:223
        ctx:state().g_bTemp = ctx:object("g_hTarget"):getStat("IsFlying") -- BASE.inc:224
        if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:226
            ctx:getTime("g_nTemp") -- BASE.inc:227
            ctx:set("g_nTemp", "g_nTemp - g_nLastCanReachCheck") -- BASE.inc:228
            ctx:state().g_bTemp = false -- BASE.inc:230
            if ctx:condition("g_bCanReach==FALSE") then -- BASE.inc:231
                if ctx:condition("g_nTemp > MIN_CHECK_REACH_TIME2") then -- BASE.inc:232
                    ctx:state().g_bTemp = true -- BASE.inc:233
                end -- BASE.inc:234
            else -- BASE.inc:235
                if ctx:condition("g_nTemp > MIN_CHECK_REACH_TIME") then -- BASE.inc:236
                    ctx:state().g_bTemp = true -- BASE.inc:237
                end -- BASE.inc:238
            end -- BASE.inc:239
            if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:241
                ctx:getTime("g_nLastCanReachCheck") -- BASE.inc:242
                ctx:state().g_bCanReach = ctx:self():canReachTarget() -- BASE.inc:243
                if ctx:condition("g_bCanReach==FALSE") then -- BASE.inc:244
                    ctx:self():stop() -- BASE.inc:245
                end -- BASE.inc:246
            end -- BASE.inc:247
        end -- BASE.inc:248
        if ctx:condition("g_bCanReach==TRUE") then -- BASE.inc:250
            mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:251
        end -- BASE.inc:252
        do return ctx:exit("") end -- BASE.inc:254
    else -- BASE.inc:255
        ctx:state().g_bCanReach = true -- BASE.inc:256
    end -- BASE.inc:257
    ctx:state().g_bTemp = ctx:self():canAttack() -- BASE.inc:259
    if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:261
        do return ctx:exit("") end -- BASE.inc:262
    end -- BASE.inc:263
    -- If we're backpedaling and want to go get him, let's stop...
    ctx:state().g_bTemp = ctx:self():getStat("BackPedaling") -- BASE.inc:266
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:267
        ctx:self():stop() -- BASE.inc:268
    end -- BASE.inc:269
    -- If we're strafing and want to go get him, let's stop...
    ctx:state().g_bTemp = ctx:self():getStat("Strafing") -- BASE.inc:272
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:273
        ctx:self():stop() -- BASE.inc:274
    end -- BASE.inc:275
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:277
    do return ctx:exit("") end -- BASE.inc:279
end

script.labels["AggressiveStart"] = function(ctx)
    -- BASE.inc:282
    ctx:wait("AGGRESSIVE_WAIT", 0.1, "AggressiveTick") -- BASE.inc:285
    do return ctx:exit("") end -- BASE.inc:286
end

script.labels["AggressiveStop"] = function(ctx)
    -- BASE.inc:289
    ctx:wait("AGGRESSIVE_WAIT", 0, "DoNothing") -- BASE.inc:291
    do return ctx:exit("") end -- BASE.inc:293
end

script.labels["AggressiveArrival"] = function(ctx)
    -- BASE.inc:296
    -- Decide if we should keep running after
    -- the target or not...
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:303
        do return ctx:exit("FALSE") end -- BASE.inc:304
    end -- BASE.inc:305
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:object("g_hTarget"):velocity() -- BASE.inc:307
    ctx:state().g_nDist1 = ctx:vecMag("g_velX", "g_velY", "g_velZ") -- BASE.inc:309
    ctx:set("g_nTemp", "g_walkVel * 0.5") -- BASE.inc:310
    if ctx:condition("g_nDist1 > g_nTemp") then -- BASE.inc:312
        do return ctx:exit("TRUE") end -- BASE.inc:313
    end -- BASE.inc:314
    -- Stop
    do return ctx:exit("TRUE") end -- BASE.inc:318
end

script.labels["BaseSetFaceTarget"] = function(ctx)
    -- BASE.inc:321
    if ctx:condition("g_bCanHeadTurn==TRUE") then -- BASE.inc:323
        ctx:state().g_bFaceTarget = false -- BASE.inc:324
    else -- BASE.inc:325
        ctx:state().g_bFaceTarget = true -- BASE.inc:326
    end -- BASE.inc:327
    do return ctx:exit("") end -- BASE.inc:329
end

script.labels["BaseRotationDone"] = function(ctx)
    -- BASE.inc:332
    mm9.gosub(script, ctx, "BaseSetFaceTarget") -- BASE.inc:335
    mm9.gosub(script, ctx, "BaseSetupTarget") -- BASE.inc:336
    ctx:randomInt(0, 100, "g_nRandom") -- BASE.inc:338
    -- Only do the aware sometimes...
    if ctx:condition("g_nRandom < 30") then -- BASE.inc:343
        ctx:self():aware("BaseAwareDone") -- BASE.inc:344
    else -- BASE.inc:345
        mm9.gosub(script, ctx, "BaseAwareDone") -- BASE.inc:346
    end -- BASE.inc:347
    do return ctx:exit("") end -- BASE.inc:349
end

script.labels["BaseAwareDone"] = function(ctx)
    -- BASE.inc:352
    -- In an attempt to keep AI from looking
    -- like they're doing everything in-sync,
    -- we'll wait a random amount of time
    -- before we go get him...
    ctx:randomFloat(0.1, 0.5, "g_nRandom") -- BASE.inc:360
    ctx:wait("AGGRESSIVE_WAIT", "g_nRandom", "BeAggressive") -- BASE.inc:361
    do return ctx:exit("TRUE") end -- BASE.inc:363
end

script.labels["BaseFoundPlayer"] = function(ctx)
    -- BASE.inc:366
    -- Found a player, set it as our current
    -- target and run after him!
    ctx:getParam(0, "g_hTarget") -- BASE.inc:372
    if ctx:condition("g_hTarget==0") then -- BASE.inc:374
        -- This shouldn't happen, but you can't be too careful!
        do return ctx:exit("FALSE") end -- BASE.inc:376
    end -- BASE.inc:377
    ctx:state().g_bTemp = ctx:self():shouldRunAwayFrom(ctx:object("g_hTarget")) -- BASE.inc:379
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:381
        ctx:self():setTarget(ctx:object("g_hTarget")) -- BASE.inc:382
        mm9.gosub(script, ctx, "BaseRunAway") -- BASE.inc:383
        do return ctx:exit("TRUE") end -- BASE.inc:384
    end -- BASE.inc:385
    ctx:self():sendAlert(ctx:object("g_hTarget")) -- BASE.inc:387
    mm9.gosub(script, ctx, "BaseSetFaceTarget") -- BASE.inc:389
    mm9.gosub(script, ctx, "BaseSetupTarget") -- BASE.inc:390
    -- Turn and face target before running after him!
    -- FaceObject g_hTarget, 180, BaseRotationDone
    ctx:self():faceObject(ctx:object("g_hTarget"), 180) -- BASE.inc:394
    mm9.gosub(script, ctx, "BaseRotationDone") -- BASE.inc:396
    do return ctx:exit("TRUE") end -- BASE.inc:398
end

script.labels["BaseEvadeDone"] = function(ctx)
    -- BASE.inc:402
    -- Stop
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:405
    do return ctx:exit("") end -- BASE.inc:407
end

script.labels["BaseAttackPerformed"] = function(ctx)
    -- BASE.inc:410
    ctx:state().g_bAttackPerformed = true -- BASE.inc:412
    do return ctx:exit("FALSE") end -- BASE.inc:414
end

script.labels["ShouldEvade"] = function(ctx)
    -- BASE.inc:417
    -- Returns TRUE or FALSE in g_bTemp
    ctx:randomInt(0, 100, "g_nRandom") -- BASE.inc:422
    ctx:state().g_nEvadeChance = ctx:self():getStat("EvadeChance") -- BASE.inc:423
    if ctx:condition("g_nRandom < g_nEvadeChance") then -- BASE.inc:425
        ctx:state().g_bTemp = true -- BASE.inc:426
    else -- BASE.inc:427
        ctx:state().g_bTemp = false -- BASE.inc:428
    end -- BASE.inc:429
    do return ctx:exit("") end -- BASE.inc:431
end

script.labels["BaseAttackDone"] = function(ctx)
    -- BASE.inc:434
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:437
        ctx:self():stop() -- BASE.inc:438
        do return ctx:exit("FALSE") end -- BASE.inc:439
    end -- BASE.inc:440
    -- Stop
    mm9.gosub(script, ctx, "ShouldEvade") -- BASE.inc:444
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:446
        ctx:state().g_nEvadeTime = ctx:self():getStat("RecoveryTime") -- BASE.inc:447
        mm9.gosub(script, ctx, "SpeedThrottleStop") -- BASE.inc:448
        mm9.gosub(script, ctx, "BaseEvadeStart") -- BASE.inc:449
        ctx:onEvent("OnTargetBeyondDist", "g_nMaxEvadeDist", "BeAggressive") -- BASE.inc:450
        ctx:set("g_nTemp", "g_nEvadeTime") -- BASE.inc:452
        -- Mul g_nTemp, 0.8
        if ctx:condition("g_nTemp < 1") then -- BASE.inc:455
            ctx:state().g_nTemp = 1 -- BASE.inc:456
        end -- BASE.inc:457
        ctx:wait("AGGRESSIVE_WAIT", "g_nTemp", "BeAggressive") -- BASE.inc:459
    else -- BASE.inc:460
        mm9.gosub(script, ctx, "IsTargetMoving") -- BASE.inc:461
        if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:462
            ctx:state().g_nDist1 = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASE.inc:463
            if ctx:condition("g_nDist1 < g_attackRange") then -- BASE.inc:465
                ctx:state().g_nEvadeTime = ctx:self():getStat("RecoveryTime") -- BASE.inc:466
                mm9.gosub(script, ctx, "SpeedThrottleStop") -- BASE.inc:467
                mm9.gosub(script, ctx, "BaseEvadeStart") -- BASE.inc:468
                ctx:onEvent("OnTargetBeyondDist", "g_nMaxEvadeDist", "BeAggressive") -- BASE.inc:469
                -- Back off, but don't go too far away...
                ctx:set("g_nTemp", "g_nEvadeTime * 0.5") -- BASE.inc:472
                ctx:wait("AGGRESSIVE_WAIT", "g_nTemp", "BeAggressive") -- BASE.inc:474
            else -- BASE.inc:475
                ctx:self():stop() -- BASE.inc:476
                ctx:randomInt(0, 100, "g_nRandom") -- BASE.inc:477
                if ctx:condition("g_nRandom < TAUNT_CHANCE") then -- BASE.inc:478
                    ctx:wait("AGGRESSIVE_WAIT", 1, "BeAggressive") -- BASE.inc:479
                    ctx:self():taunt("BeAggressive") -- BASE.inc:480
                end -- BASE.inc:481
            end -- BASE.inc:482
        end -- BASE.inc:483
    end -- BASE.inc:484
    -- Let our aggressive tick handle this stuff...
    -- gosub BaseSetFaceTarget
    -- Target g_hTarget, g_bFaceTarget
    -- gosub BaseGoGetHim
    do return ctx:exit("TRUE") end -- BASE.inc:494
end

script.labels["BaseEvadeStop"] = function(ctx)
    -- BASE.inc:497
    mm9.gosub(script, ctx, "BaseEvadeStop") -- BASE.inc:500
    ctx:onEvent("OnPathClear", "BasePathClear") -- BASE.inc:502
    ctx:onEvent("OnObstacle", "BaseObstacle") -- BASE.inc:503
    ctx:onEvent("OnTargetBeyondDist", 0) -- BASE.inc:504
    if ctx:condition("g_bCanBlendAnim==TRUE") then -- BASE.inc:506
        ctx:onEvent("OnTargetOutOfRange", "BaseTargetOutOfRange") -- BASE.inc:507
    end -- BASE.inc:508
    mm9.gosub(script, ctx, "SpeedThrottleStart") -- BASE.inc:510
    do return ctx:exit("") end -- BASE.inc:512
end

script.labels["BeAggressive"] = function(ctx)
    -- BASE.inc:516
    mm9.gosub(script, ctx, "BaseEvadeStop") -- BASE.inc:519
    ctx:state().g_bBaseGoGetHim = false -- BASE.inc:521
    mm9.gosub(script, ctx, "AggressiveTick") -- BASE.inc:522
    if ctx:condition("g_bBaseGoGetHim==FALSE") then -- BASE.inc:524
        -- Stop
    end -- BASE.inc:526
    do return ctx:exit("") end -- BASE.inc:528
end

script.labels["BaseDoAttack"] = function(ctx)
    -- BASE.inc:531
    ctx:state().g_bFighting = true -- BASE.inc:534
    ctx:getTime("g_nLastAttackTime") -- BASE.inc:536
    if ctx:condition("g_hTarget!=NULL") then -- BASE.inc:538
        ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:object("g_hTarget"):pos() -- BASE.inc:539
        ctx:self():facePos("g_posX", "g_posY", "g_posZ", 360) -- BASE.inc:540
    end -- BASE.inc:541
    ctx:state().g_bAttackPerformed = false -- BASE.inc:543
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASE.inc:544
    mm9.gosub(script, ctx, "IsTargetMoving") -- BASE.inc:546
    -- if they're not moving, attack and strafe past them..
    if ctx:condition("g_bCanBlendAnim==TRUE") then -- BASE.inc:550
        if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:551
            ctx:randomInt(0, 100, "g_nRandom") -- BASE.inc:553
            if ctx:condition("g_nRandom < g_nStrafeAttackPct") then -- BASE.inc:555
                ctx:state().g_bPickDir = true -- BASE.inc:556
                mm9.gosub(script, ctx, "BE_AttackStrafe") -- BASE.inc:557
                ctx:state().g_bPickDir = true -- BASE.inc:558
                ctx:state().g_bStrafeAttack = true -- BASE.inc:559
            else -- BASE.inc:560
                ctx:self():stop() -- BASE.inc:561
            end -- BASE.inc:562
        else -- BASE.inc:563
            ctx:state().g_bStrafeAttack = false -- BASE.inc:564
        end -- BASE.inc:565
    else -- BASE.inc:566
        ctx:state().g_bStrafeAttack = false -- BASE.inc:567
        ctx:self():stop() -- BASE.inc:568
    end -- BASE.inc:569
    ctx:self():attack("BaseAttackDone") -- BASE.inc:571
    ctx:wait("AGGRESSIVE_WAIT", 2, "AggressiveTick") -- BASE.inc:573
    do return ctx:exit("") end -- BASE.inc:576
end

script.labels["BaseAttackReady"] = function(ctx)
    -- BASE.inc:579
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    -- gosub ShouldAttack
    -- if ( g_bShouldAttack==TRUE )
    -- gosub BaseDoAttack
    -- Exit
    -- endif
    -- gosub BaseGoGetHim
    do return ctx:exit("TRUE") end -- BASE.inc:595
end

script.labels["BaseLostTarget"] = function(ctx)
    -- BASE.inc:598
    -- We've lost the target, so let's go idle.
    ctx:state().g_hTarget = nil -- BASE.inc:603
    ctx:state().g_bFighting = false -- BASE.inc:604
    mm9.gosub(script, ctx, "BaseClearTarget") -- BASE.inc:606
    ctx:self():setIdle() -- BASE.inc:608
    do return ctx:exit("") end -- BASE.inc:610
end

script.labels["BaseStuckDone"] = function(ctx)
    -- BASE.inc:613
    -- This is called when a stuck animation
    -- has finished... We'll just re-attempt
    -- to run after our target...
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:620
        do return ctx:exit("FALSE") end -- BASE.inc:621
    end -- BASE.inc:622
    -- for now, don't wait when stuck..
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:627
    if ctx:condition("g_bBaseGoGetHim==TRUE") then -- BASE.inc:629
        do return ctx:exit("TRUE") end -- BASE.inc:630
    end -- BASE.inc:631
    if ctx:condition("g_nStuckTime==0.0") then -- BASE.inc:633
        ctx:getTime("g_nStuckTime") -- BASE.inc:634
    else -- BASE.inc:635
        ctx:getTime("g_nTemp") -- BASE.inc:636
        ctx:sub("g_nTemp", "g_nStuckTime") -- BASE.inc:637
        if ctx:condition("g_nTemp > MIN_STUCK_TIME") then -- BASE.inc:639
            ctx:state().g_nStuckTime = 0 -- BASE.inc:640
            do return ctx:exit("FALSE") end -- BASE.inc:641
        end -- BASE.inc:642
    end -- BASE.inc:643
    ctx:self():setStuck() -- BASE.inc:645
    do return ctx:exit("TRUE") end -- BASE.inc:647
end

script.labels["IsAttackerValidTarget"] = function(ctx)
    -- BASE.inc:650
    -- Returns g_bTemp = TRUE or FALSE
    ctx:state().g_bTemp = false -- BASE.inc:655
    if ctx:condition("g_hAttacker==g_hMyObject") then -- BASE.inc:657
        do return ctx:exit("") end -- BASE.inc:658
    end -- BASE.inc:659
    if ctx:condition("g_hAttacker==NULL") then -- BASE.inc:661
        do return ctx:exit("") end -- BASE.inc:662
    end -- BASE.inc:663
    ctx:state().g_nTemp = (ctx:object("g_hAttacker"):isActor() and 1 or 0) -- BASE.inc:665
    if ctx:condition("g_nTemp==FALSE") then -- BASE.inc:667
        do return ctx:exit("") end -- BASE.inc:668
    end -- BASE.inc:669
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hAttacker")) -- BASE.inc:671
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:673
        ctx:state().g_bTemp = false -- BASE.inc:674
    else -- BASE.inc:675
        ctx:state().g_bTemp = true -- BASE.inc:676
    end -- BASE.inc:677
    -- GetClassName g_hAttacker, g_sTemp
    -- if ( g_sTemp==g_sMyClassName )
    -- exit
    -- endif
    -- Set g_bTemp, TRUE
    do return ctx:exit("") end -- BASE.inc:685
end

script.labels["BaseRunAway"] = function(ctx)
    -- BASE.inc:689
    -- Overloading on purpose....
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:694
        do return ctx:exit("") end -- BASE.inc:695
    end -- BASE.inc:696
    mm9.gosub(script, ctx, "BaseEvadeStop") -- BASE.inc:698
    ctx:onEvent("OnProjectile") -- BASE.inc:699
    ctx:onEvent("OnFoundPlayer") -- BASE.inc:700
    ctx:onEvent("OnTargetOutOfRange") -- BASE.inc:701
    mm9.gosub(script, ctx, "DisableWandering") -- BASE.inc:703
    mm9.gosub(script, ctx, "ChaseStop") -- BASE.inc:704
    mm9.gosub(script, ctx, "AggressiveStop") -- BASE.inc:705
    mm9.gosub(script, ctx, "BaseRunAway") -- BASE.inc:707
    do return ctx:exit("") end -- BASE.inc:709
end

script.labels["BaseRunCancel"] = function(ctx)
    -- BASE.inc:713
    -- We're overloading the function here....
    mm9.gosub(script, ctx, "BaseRunCancel") -- BASE.inc:719
    ctx:state().g_hTarget = nil -- BASE.inc:721
    ctx:self():setTarget(nil) -- BASE.inc:722
    ctx:self():stop() -- BASE.inc:723
    ctx:onEvent("OnProjectile", "BaseOnProjectile") -- BASE.inc:725
    ctx:onEvent("OnFoundPlayer", "BaseFoundPlayer") -- BASE.inc:726
    mm9.gosub(script, ctx, "EnableWandering") -- BASE.inc:728
    do return ctx:exit("") end -- BASE.inc:730
end

script.labels["BaseCheckAttacker"] = function(ctx)
    -- BASE.inc:734
    -- Looks at last attacker and decides
    -- if we want to go after him...
    mm9.gosub(script, ctx, "IsAttackerValidTarget") -- BASE.inc:740
    if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:742
        do return mm9.gotoLabel(script, ctx, "BaseSkipTargetSwitch") end -- BASE.inc:743
    end -- BASE.inc:744
    ctx:state().g_bTemp = ctx:self():shouldRunAwayFrom(ctx:object("g_hAttacker")) -- BASE.inc:746
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:748
        ctx:set("g_hTarget", "g_hAttacker") -- BASE.inc:749
        ctx:self():setTarget(ctx:object("g_hTarget")) -- BASE.inc:750
        mm9.gosub(script, ctx, "BaseRunAway") -- BASE.inc:751
        do return ctx:exit("TRUE") end -- BASE.inc:752
    end -- BASE.inc:753
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:755
        ctx:set("g_hTarget", "g_hAttacker") -- BASE.inc:756
        ctx:state().g_bFighting = true -- BASE.inc:757
    else -- BASE.inc:758
        ctx:state().g_bInAttackRange = ctx:self():isTargetInRange() -- BASE.inc:759
        if ctx:condition("g_hAttacker!=NULL") then -- BASE.inc:761
            if ctx:condition("g_hAttacker!=g_hTarget") then -- BASE.inc:762
                ctx:state().g_sTemp = ctx:object("g_hAttacker"):className() -- BASE.inc:763
                -- if ( g_sTemp!=Player )
                -- goto BaseSkipTargetSwitch
                -- endif
                -- 70% chance we'll switch to the damager
                ctx:state().g_nTemp = 70 -- BASE.inc:768
                if ctx:condition("g_bInAttackRange==TRUE") then -- BASE.inc:769
                    -- we're already in attack range of our current target
                    -- so lower chances of switching
                    ctx:state().g_nTemp = 45 -- BASE.inc:772
                end -- BASE.inc:773
                ctx:state().g_nDist1 = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASE.inc:775
                ctx:state().g_nDist2 = ctx:self():aiDistanceTo(ctx:object("g_hAttacker")) -- BASE.inc:776
                if ctx:condition("g_nDist2 > g_nDist1") then -- BASE.inc:778
                    -- reduce odds even further...
                    ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) / 2 -- BASE.inc:780
                end -- BASE.inc:781
                ctx:randomInt(0, 100, "g_nRandom") -- BASE.inc:783
                if ctx:condition("g_nRandom < g_nTemp") then -- BASE.inc:784
                    -- Okay, we decided to switch our current target to the
                    -- attacker!
                    ctx:set("g_hTarget", "g_hAttacker") -- BASE.inc:789
                end -- BASE.inc:790
            end -- BASE.inc:791
        end -- BASE.inc:792
    end -- BASE.inc:793
end

script.labels["BaseSkipTargetSwitch"] = function(ctx)
    -- BASE.inc:795
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:797
        -- FALSE means have the AI do its default handling of this event.
        do return ctx:exit("FALSE") end -- BASE.inc:798
    end -- BASE.inc:799
    -- Go after the Target...
    mm9.gosub(script, ctx, "BaseSetFaceTarget") -- BASE.inc:803
    mm9.gosub(script, ctx, "BaseSetupTarget") -- BASE.inc:804
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:806
    do return ctx:exit("") end -- BASE.inc:808
end

script.labels["BaseDamageDone"] = function(ctx)
    -- BASE.inc:811
    -- We were attacked, now we want to run
    -- after whoever attacked us!
    mm9.gosub(script, ctx, "BaseCheckAttacker") -- BASE.inc:818
    do return ctx:exit("") end -- BASE.inc:819
end

script.labels["BaseSetupAttacker"] = function(ctx)
    -- BASE.inc:822
    ctx:self():link(ctx:object("g_hAttacker")) -- BASE.inc:825
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hAttacker")) -- BASE.inc:828
    if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:830
        ctx:self():sendAlert(ctx:object("g_hAttacker")) -- BASE.inc:831
    end -- BASE.inc:832
    do return ctx:exit("") end -- BASE.inc:834
end

script.labels["BaseDamage"] = function(ctx)
    -- BASE.inc:837
    -- p0 = hAttacker
    -- p1 = HitPoints
    -- p2 = DamageType
    ctx:getParam(0, "g_hAttacker") -- BASE.inc:845
    ctx:getParam(1, "g_nLastDamage") -- BASE.inc:846
    ctx:getParam(2, "g_lastDamageType") -- BASE.inc:847
    mm9.gosub(script, ctx, "BaseSetupAttacker") -- BASE.inc:849
    if ctx:condition("g_nLastDamage == 0") then -- BASE.inc:851
        mm9.gosub(script, ctx, "BaseDamageDone") -- BASE.inc:852
    end -- BASE.inc:853
    do return ctx:exit("FALSE") end -- BASE.inc:855
end

script.labels["BaseObjectLinkBroken"] = function(ctx)
    -- BASE.inc:859
    -- Any object handle that I create a link
    -- for needs to be checked in this routine
    ctx:getParam(0, "g_hObject") -- BASE.inc:865
    if ctx:condition("g_hObject==g_hAttacker") then -- BASE.inc:867
        ctx:state().g_hAttacker = nil -- BASE.inc:868
    end -- BASE.inc:869
    if ctx:condition("g_hTarget==g_hObject") then -- BASE.inc:871
        mm9.gosub(script, ctx, "BaseClearTarget") -- BASE.inc:872
    end -- BASE.inc:873
    do return ctx:exit("") end -- BASE.inc:875
end

script.labels["BaseCongestion"] = function(ctx)
    -- BASE.inc:878
    -- If there is congestion in the way,
    -- start walking
    do return ctx:exit("FALSE") end -- BASE.inc:883
    if ctx:condition("g_hTarget!=NULL") then -- BASE.inc:885
        if ctx:condition("g_bRunningAway==FALSE") then -- BASE.inc:886
            ctx:self():walkTo(ctx:object("g_hTarget"), 0, "AggressiveArrival") -- BASE.inc:887
        end -- BASE.inc:888
    end -- BASE.inc:889
    do return ctx:exit("TRUE") end -- BASE.inc:891
end

script.labels["BasePathClear"] = function(ctx)
    -- BASE.inc:894
    if ctx:condition("g_hTarget!=NULL") then -- BASE.inc:897
        mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:898
    end -- BASE.inc:899
    do return ctx:exit("TRUE") end -- BASE.inc:901
end

script.labels["BaseTargetDead"] = function(ctx)
    -- BASE.inc:904
    ctx:getParam(0, "g_nTemp") -- BASE.inc:907
    mm9.gosub(script, ctx, "BaseClearTarget") -- BASE.inc:909
    -- if ( g_nTemp==g_hMyObject )
    -- We killed him!
    -- taunt him, and go home....
    -- Taunt BaseGoHome
    -- else
    -- just go home...
    -- gosub BaseGoHome
    -- endif
    do return ctx:exit("TRUE") end -- BASE.inc:923
end

script.labels["BaseImHome"] = function(ctx)
    -- BASE.inc:926
    -- I made it back home, now, rotate to
    -- face the way I was facing...
    do return ctx:exit("") end -- BASE.inc:933
end

script.labels["BaseGoHome"] = function(ctx)
    -- BASE.inc:936
    -- Sends ai back to where it started
    -- NOTE: if we ge stuck on way back home,
    -- we will just stay there...
    -- for now, just go back into idle loop...
    ctx:self():stop() -- BASE.inc:945
    ctx:self():setIdle() -- BASE.inc:946
    -- Set g_nGoingHome, TRUE
    -- WalkToPos g_homeX, g_homeY, g_homeZ, BaseImHome
    do return ctx:exit("") end -- BASE.inc:951
end

script.labels["BaseObstacle"] = function(ctx)
    -- BASE.inc:954
    if ctx:condition("g_bClearTargetOnObstacle==TRUE") then -- BASE.inc:958
        if ctx:condition("g_hTarget!=NULL") then -- BASE.inc:959
            ctx:state().g_bTemp = ctx:self():canReachTarget() -- BASE.inc:960
            if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:962
                ctx:self():stop() -- BASE.inc:963
                mm9.gosub(script, ctx, "BaseClearTarget") -- BASE.inc:964
            end -- BASE.inc:965
        end -- BASE.inc:967
    end -- BASE.inc:968
    ctx:randomInt(0, 100, "g_nRandom") -- BASE.inc:971
    if ctx:condition("g_nRandom > 3") then -- BASE.inc:973
        do return ctx:exit("FALSE") end -- BASE.inc:974
    end -- BASE.inc:975
    -- small pct chance we'll taunt him when we hit an obstacle....
    -- Taunt BaseGoGetHim
    do return ctx:exit("") end -- BASE.inc:980
end

script.labels["BaseAlert"] = function(ctx)
    -- BASE.inc:984
    -- p0	- Handle of AI who sent the alert
    -- p1	- Handle of that AI's target
    ctx:getParam(1, "g_hObject") -- BASE.inc:991
    if ctx:condition("g_hObject==g_hMyObject") then -- BASE.inc:993
        -- Someone yelped about us attacking them!
        do return ctx:exit("FALSE") end -- BASE.inc:995
    end -- BASE.inc:996
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- BASE.inc:998
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:1000
        -- We don't answer the call to attack our friends..
        do return ctx:exit("FALSE") end -- BASE.inc:1002
    end -- BASE.inc:1003
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:1005
        ctx:set("g_hTarget", "g_hObject") -- BASE.inc:1006
        ctx:state().g_bFaceTarget = true -- BASE.inc:1008
        mm9.gosub(script, ctx, "BaseSetupTarget") -- BASE.inc:1009
        ctx:randomFloat(0.2, 0.5, "g_nRandom") -- BASE.inc:1011
        ctx:wait("BASE_WAIT_NBR", "g_nRandom", "BaseGoGetHim") -- BASE.inc:1012
    else -- BASE.inc:1013
        if ctx:condition("g_hAttacker!=NULL") then -- BASE.inc:1014
            ctx:self():unlink(ctx:object("g_hAttacker")) -- BASE.inc:1015
        end -- BASE.inc:1016
        ctx:set("g_hAttacker", "g_hObject") -- BASE.inc:1017
        mm9.gosub(script, ctx, "BaseSetupAttacker") -- BASE.inc:1018
        mm9.gosub(script, ctx, "BaseCheckAttacker") -- BASE.inc:1019
    end -- BASE.inc:1020
    do return ctx:exit("TRUE") end -- BASE.inc:1023
end

script.labels["BaseHelp"] = function(ctx)
    -- BASE.inc:1026
    -- If we're not busy, and we feel like it,
    -- go after the target...
    -- p0 - hPoorSlob
    -- p1 - hBadGuy
    ctx:state().g_hObject = ctx:self():target() -- BASE.inc:1036
    if ctx:condition("g_hObject!=NULL") then -- BASE.inc:1037
        do return ctx:exit("") end -- BASE.inc:1038
    end -- BASE.inc:1039
    ctx:getParam(0, "g_hObject") -- BASE.inc:1041
    ctx:getParam(1, "g_hObject2") -- BASE.inc:1042
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- BASE.inc:1044
    if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:1046
        -- Not a friend aye?  Screw him!
        do return ctx:exit("") end -- BASE.inc:1048
    end -- BASE.inc:1049
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject2")) -- BASE.inc:1051
    if ctx:condition("g_bTemp==TRUE") then -- BASE.inc:1053
        -- He's complaining about a friend of mine.
        do return ctx:exit("") end -- BASE.inc:1055
    end -- BASE.inc:1056
    -- OK, now decide if we SHOULD go after him...
    ctx:state().g_bTemp = ctx:self():canReachObject(ctx:object("g_hObject2")) -- BASE.inc:1060
    if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:1062
        -- Don't have a way to get to him.  Nevermind...
        do return ctx:exit("") end -- BASE.inc:1064
    end -- BASE.inc:1065
    ctx:state().g_bFighting = true -- BASE.inc:1067
    ctx:set("g_hTarget", "g_hObject2") -- BASE.inc:1068
    mm9.gosub(script, ctx, "BaseSetFaceTarget") -- BASE.inc:1069
    mm9.gosub(script, ctx, "BaseSetupTarget") -- BASE.inc:1070
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:1071
    do return ctx:exit("") end -- BASE.inc:1073
end

script.labels["BaseOnProjectile"] = function(ctx)
    -- BASE.inc:1076
    -- p0	- hProjectile
    -- p1	- hLaunchedFrom
    -- p2	- dist
    ctx:getParam(0, "g_hObject") -- BASE.inc:1086
    ctx:getParam(1, "g_nTemp") -- BASE.inc:1087
    if ctx:condition("g_hObject==g_nTemp") then -- BASE.inc:1088
        -- Don't take these seriously...
        do return ctx:exit("") end -- BASE.inc:1092
    end -- BASE.inc:1093
    if ctx:condition("g_hTarget!=NULL") then -- BASE.inc:1095
        do return ctx:exit("") end -- BASE.inc:1096
    end -- BASE.inc:1097
    if ctx:condition("g_hAttacker!=NULL") then -- BASE.inc:1099
        ctx:self():unlink(ctx:object("g_hAttacker")) -- BASE.inc:1100
    end -- BASE.inc:1101
    ctx:getParam(1, "g_hAttacker") -- BASE.inc:1103
    mm9.gosub(script, ctx, "BaseSetupAttacker") -- BASE.inc:1105
    mm9.gosub(script, ctx, "BaseCheckAttacker") -- BASE.inc:1106
    do return ctx:exit("") end -- BASE.inc:1109
end

script.labels["ChaseStop"] = function(ctx)
    -- BASE.inc:1112
    ctx:wait("CHASE_TARGET_WAIT", 0, "DoNothing") -- BASE.inc:1114
    do return ctx:exit("") end -- BASE.inc:1116
end

script.labels["BaseChaseTargetTick"] = function(ctx)
    -- BASE.inc:1119
    -- A little heartbeat to make sure we
    -- never get stuck when we have a target
    ctx:wait("CHASE_TARGET_WAIT", 1.0, "BaseChaseTargetTick") -- BASE.inc:1126
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:1128
        -- No target?  No one to go after...
        do return ctx:exit("") end -- BASE.inc:1132
    end -- BASE.inc:1133
    ctx:state().g_bTemp = ctx:self():getStat("IsIdle") -- BASE.inc:1135
    if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:1137
        -- Only do this if we're idle...
        do return ctx:exit("") end -- BASE.inc:1141
    end -- BASE.inc:1142
    ctx:state().g_bTemp = ctx:self():canReachTarget() -- BASE.inc:1144
    if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:1146
        if ctx:condition("g_targetOutOfReachStart==0") then -- BASE.inc:1147
            ctx:getTime("g_targetOutOfReachStart") -- BASE.inc:1148
            do return ctx:exit("") end -- BASE.inc:1149
        else -- BASE.inc:1150
            ctx:getTime("g_nTemp") -- BASE.inc:1151
            ctx:sub("g_nTemp", "g_targetOutOfReachStart") -- BASE.inc:1152
            if ctx:condition("g_nTemp < BORED_WITH_TARGET_TIME") then -- BASE.inc:1154
                do return ctx:exit("") end -- BASE.inc:1155
            end -- BASE.inc:1156
            mm9.gosub(script, ctx, "BaseClearTarget") -- BASE.inc:1158
            mm9.gosub(script, ctx, "BaseWanderForceStartUp") -- BASE.inc:1159
        end -- BASE.inc:1160
    end -- BASE.inc:1161
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:1163
    do return ctx:exit("") end -- BASE.inc:1165
end

script.labels["BaseSetupTarget"] = function(ctx)
    -- BASE.inc:1168
    -- Sets up all the stuff for a new target
    if ctx:condition("g_hTarget==NULL") then -- BASE.inc:1174
        ctx:debugOut("Script", "ASSERT!!!!!", "[BaseSetupTarget]") -- BASE.inc:1175
        ctx:debugOut("Script", "ASSERT!!!!!", "[BaseSetupTarget]") -- BASE.inc:1176
        ctx:debugOut("Script", "ASSERT!!!!!", "[BaseSetupTarget]") -- BASE.inc:1177
        ctx:debugOut("Script", "ASSERT!!!!!", "[BaseSetupTarget]") -- BASE.inc:1178
        do return ctx:exit("") end -- BASE.inc:1179
    end -- BASE.inc:1180
    -- Once we've had a target, we can start wandering...
    ctx:state().g_nStuckTime = 0 -- BASE.inc:1184
    ctx:state().g_targetOutOfReachStart = 0 -- BASE.inc:1185
    mm9.gosub(script, ctx, "DisableWandering") -- BASE.inc:1187
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASE.inc:1189
    do return ctx:exit("") end -- BASE.inc:1191
end

script.labels["BaseClearTarget"] = function(ctx)
    -- BASE.inc:1194
    -- Sets up all the stuff for a new target
    ctx:state().g_nStuckTime = 0 -- BASE.inc:1200
    ctx:state().g_targetOutOfReachStart = 0 -- BASE.inc:1201
    ctx:state().g_hTarget = nil -- BASE.inc:1202
    ctx:self():setTarget(nil) -- BASE.inc:1203
    mm9.gosub(script, ctx, "BaseWanderStart") -- BASE.inc:1204
    -- gosub BaseWanderGo
    -- gosub EnableWandering
    do return ctx:exit("") end -- BASE.inc:1208
end

script.labels["BaseRunAwayTick"] = function(ctx)
    -- BASE.inc:1212
    mm9.gosub(script, ctx, "BaseRunAwayTick") -- BASE.inc:1214
    if ctx:condition("g_bRunningAway==TRUE") then -- BASE.inc:1216
        if ctx:condition("g_hTarget!=NULL") then -- BASE.inc:1217
            ctx:state().g_bTemp = ctx:self():shouldRunAwayFrom(ctx:object("g_hTarget")) -- BASE.inc:1218
            if ctx:condition("g_bTemp==FALSE") then -- BASE.inc:1219
                ctx:set("g_hObject", "g_hTarget") -- BASE.inc:1220
                mm9.gosub(script, ctx, "BaseRunCancel") -- BASE.inc:1221
                ctx:set("g_hTarget", "g_hObject") -- BASE.inc:1222
                mm9.gosub(script, ctx, "BaseSetFaceTarget") -- BASE.inc:1223
                mm9.gosub(script, ctx, "BaseSetupTarget") -- BASE.inc:1224
                mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:1225
            end -- BASE.inc:1226
        end -- BASE.inc:1227
    end -- BASE.inc:1228
    do return ctx:exit("") end -- BASE.inc:1230
end

script.labels["BaseTargetOutOfRange"] = function(ctx)
    -- BASE.inc:1233
    if ctx:condition("g_bAttackPerformed==TRUE") then -- BASE.inc:1236
        do return ctx:exit("") end -- BASE.inc:1237
    end -- BASE.inc:1238
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:object("g_hTarget"):velocity() -- BASE.inc:1240
    if ctx:condition("g_velX==0") then -- BASE.inc:1242
        if ctx:condition("g_velZ==0") then -- BASE.inc:1243
            do return ctx:exit("") end -- BASE.inc:1244
        end -- BASE.inc:1245
    end -- BASE.inc:1246
    ctx:self():setStat("RunVel", "g_runVel") -- BASE.inc:1248
    ctx:self():setStat("WalkVel", "g_walkVel") -- BASE.inc:1249
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:1251
    do return ctx:exit("") end -- BASE.inc:1253
end

script.labels["InitBase"] = function(ctx)
    -- BASE.inc:1256
    -- Main intialization code.
    -- This should be called by the actual
    -- script file..
    ctx:state().g_sMyClassName = ctx:self():className() -- BASE.inc:1265
    -- Setup our event handlers...
    ctx:onEvent("OnFoundPlayer", "BaseFoundPlayer") -- BASE.inc:1270
    ctx:onEvent("OnLostTarget", "BaseLostTarget") -- BASE.inc:1271
    -- OnAttackReady				BaseAttackReady
    ctx:onEvent("OnStuck", "BaseStuck") -- BASE.inc:1273
    ctx:onEvent("OnStuckDone", "BaseStuckDone") -- BASE.inc:1274
    ctx:onEvent("OnDamageDone", "BaseDamageDone") -- BASE.inc:1275
    ctx:onEvent("OnDamage", "BaseDamage") -- BASE.inc:1276
    ctx:onEvent("OnCongestion", "BaseCongestion") -- BASE.inc:1277
    ctx:onEvent("OnPathClear", "BasePathClear") -- BASE.inc:1278
    ctx:onEvent("OnTargetDead", "BaseTargetDead") -- BASE.inc:1279
    ctx:onEvent("OnObstacle", "BaseObstacle") -- BASE.inc:1280
    ctx:onEvent("OnAlert", "BaseAlert") -- BASE.inc:1281
    ctx:onEvent("OnHelp", "BaseHelp") -- BASE.inc:1282
    ctx:onEvent("OnProjectile", "BaseOnProjectile") -- BASE.inc:1283
    ctx:onEvent("OnObjectLinkBroken", "BaseObjectLinkBroken") -- BASE.inc:1284
    ctx:addModelKey("rAttack", "BaseAttackPerformed") -- BASE.inc:1285
    ctx:addModelKey("lAttack", "BaseAttackPerformed") -- BASE.inc:1286
    ctx:state().g_bCanHeadTurn = ctx:self():getStat("CanHeadTurn") -- BASE.inc:1288
    ctx:state().g_bCanBlendAnim = ctx:self():getStat("CanBlendAnim") -- BASE.inc:1289
    ctx:state().g_nStrafeAttackPct = ctx:self():getStat("StrafeAttackPct") -- BASE.inc:1290
    if ctx:condition("g_bCanBlendAnim==TRUE") then -- BASE.inc:1292
        ctx:onEvent("OnTargetOutOfRange", "BaseTargetOutOfRange") -- BASE.inc:1293
    end -- BASE.inc:1294
    -- Setup our chase target timer....
    -- Wait CHASE_TARGET_WAIT, 1.0, BaseChaseTargetTick
    -- See if we already have a target (this would normally happen if
    -- the ai were running another script and then decided to start running
    -- this one...
    ctx:state().g_hTarget = ctx:self():target() -- BASE.inc:1304
    if ctx:condition("g_hTarget!=NULL") then -- BASE.inc:1306
        mm9.gosub(script, ctx, "BaseGoGetHim") -- BASE.inc:1307
    end -- BASE.inc:1308
    mm9.gosub(script, ctx, "BaseWanderInit") -- BASE.inc:1310
    mm9.gosub(script, ctx, "AggressiveStart") -- BASE.inc:1312
    mm9.gosub(script, ctx, "BaseDoorInit") -- BASE.inc:1313
    mm9.gosub(script, ctx, "SpeedThrottleInit") -- BASE.inc:1314
    mm9.gosub(script, ctx, "SpeedThrottleStart") -- BASE.inc:1315
    mm9.gosub(script, ctx, "BaseRunInit") -- BASE.inc:1316
    -- TraceOn
    -- TraceRoutinesOn
    do return ctx:exit("") end -- BASE.inc:1321
end

return script
