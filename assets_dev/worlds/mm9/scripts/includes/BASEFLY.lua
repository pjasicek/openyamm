-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASEFLY.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "AICommon.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "baseevade.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "basewander.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "flags.inc" }

-- BaseFly.Inc
-- Jeff Leggett
-- 09/27/2001
-- Basic implementation of flying creatures..
script.labels["AlertStart"] = function(ctx)
    -- BASEFLY.inc:48
    mm9.gosub(script, ctx, "AlertTick") -- BASEFLY.inc:50
    do return ctx:exit("") end -- BASEFLY.inc:51
end

script.labels["AlertTick"] = function(ctx)
    -- BASEFLY.inc:54
    ctx:wait("ALERT_WAIT", "g_nRandom", "AlertTick") -- BASEFLY.inc:56
    if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:58
        do return ctx:exit("") end -- BASEFLY.inc:59
    end -- BASEFLY.inc:60
    ctx:self():sendAlert(ctx:object("g_hTarget")) -- BASEFLY.inc:62
    do return ctx:exit("") end -- BASEFLY.inc:64
end

script.labels["AlertStop"] = function(ctx)
    -- BASEFLY.inc:67
    ctx:wait("ALERT_WAIT", 0, "DoNothing") -- BASEFLY.inc:69
    do return ctx:exit("") end -- BASEFLY.inc:70
end

script.labels["GetTimeToTarget"] = function(ctx)
    -- BASEFLY.inc:74
    -- returns in g_nTimeToTarget
    ctx:state().g_nTargetDist = 0 -- BASEFLY.inc:79
    ctx:state().g_nTimeToTarget = 0 -- BASEFLY.inc:80
    if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:82
        do return ctx:exit("") end -- BASEFLY.inc:83
    end -- BASEFLY.inc:84
    ctx:state().g_nTargetDist = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASEFLY.inc:86
    ctx:set("g_nTimeToTarget", "g_nTargetDist / g_flyVel") -- BASEFLY.inc:88
    do return ctx:exit("") end -- BASEFLY.inc:90
end

script.labels["BaseFlyGetHim"] = function(ctx)
    -- BASEFLY.inc:94
    ctx:onEvent("OnObstacle", "AggressiveObstacle") -- BASEFLY.inc:100
    if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:102
        do return ctx:exit("") end -- BASEFLY.inc:103
    end -- BASEFLY.inc:104
    ctx:self():runTo(ctx:object("g_hTarget"), "g_runToRange", "BaseFlyArrival") -- BASEFLY.inc:106
    do return ctx:exit("") end -- BASEFLY.inc:108
end

script.labels["AggressiveObstacle"] = function(ctx)
    -- BASEFLY.inc:111
    ctx:getParam(0, "g_hObject") -- BASEFLY.inc:114
    if ctx:condition("g_hObject==g_hTarget") then -- BASEFLY.inc:116
        ctx:debugOut("Ran", "into", "target!", "stopping....") -- BASEFLY.inc:117
        ctx:self():stop() -- BASEFLY.inc:118
        do return ctx:exit("TRUE") end -- BASEFLY.inc:119
    end -- BASEFLY.inc:120
    do return ctx:exit("FALSE") end -- BASEFLY.inc:122
end

script.labels["BaseFlyArrival"] = function(ctx)
    -- BASEFLY.inc:125
    if ctx:condition("g_bAggressive==TRUE") then -- BASEFLY.inc:128
        mm9.gosub(script, ctx, "AggressiveTick") -- BASEFLY.inc:129
    end -- BASEFLY.inc:130
    do return ctx:exit("TRUE") end -- BASEFLY.inc:132
end

script.labels["AggressiveStart"] = function(ctx)
    -- BASEFLY.inc:135
    ctx:self():setStat("flyVel", "g_flyVel") -- BASEFLY.inc:138
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "AggressiveTick") -- BASEFLY.inc:140
    ctx:state().g_bAggressive = true -- BASEFLY.inc:141
    do return ctx:exit("") end -- BASEFLY.inc:144
end

script.labels["AggressiveStop"] = function(ctx)
    -- BASEFLY.inc:147
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "DoNothing") -- BASEFLY.inc:150
    ctx:state().g_bAggressive = false -- BASEFLY.inc:152
    ctx:onEvent("OnObstacle") -- BASEFLY.inc:154
    do return ctx:exit("") end -- BASEFLY.inc:156
end

script.labels["AggressiveTick"] = function(ctx)
    -- BASEFLY.inc:160
    -- See's if we are within range to attack and such...
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "AggressiveTick") -- BASEFLY.inc:166
    if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:168
        do return ctx:exit("") end -- BASEFLY.inc:169
    end -- BASEFLY.inc:170
    ctx:getTime("g_nTime") -- BASEFLY.inc:172
    ctx:set("g_nTemp", "g_nLastAttackTime + MAX_CHASE_TIME") -- BASEFLY.inc:174
    if ctx:condition("g_nTime > g_nTemp") then -- BASEFLY.inc:176
        -- Time to give up on this target!
        mm9.gosub(script, ctx, "GiveUpOnTarget") -- BASEFLY.inc:178
        do return ctx:exit("") end -- BASEFLY.inc:179
    end -- BASEFLY.inc:180
    -- if we are within attack range do our attack...
    ctx:state().g_nTemp = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASEFLY.inc:187
    if ctx:condition("g_nTemp < g_attackRange") then -- BASEFLY.inc:189
        ctx:state().g_bTemp = ctx:self():canAttack() -- BASEFLY.inc:190
        if ctx:condition("g_bTemp==FALSE") then -- BASEFLY.inc:191
            ctx:getTime("g_nLastAttackTime") -- BASEFLY.inc:192
            mm9.gosub(script, ctx, "Backoff") -- BASEFLY.inc:193
        else -- BASEFLY.inc:194
            mm9.gosub(script, ctx, "BaseFlyAttack") -- BASEFLY.inc:195
            do return ctx:exit("") end -- BASEFLY.inc:196
        end -- BASEFLY.inc:197
    else -- BASEFLY.inc:198
        mm9.gosub(script, ctx, "BaseFlyGetHim") -- BASEFLY.inc:199
    end -- BASEFLY.inc:200
    do return ctx:exit("") end -- BASEFLY.inc:202
end

script.labels["SwoopDone"] = function(ctx)
    -- BASEFLY.inc:206
    ctx:state().g_bSwooping = false -- BASEFLY.inc:209
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASEFLY.inc:211
    mm9.gosub(script, ctx, "AggressiveStart") -- BASEFLY.inc:212
    do return ctx:exit("") end -- BASEFLY.inc:214
end

script.labels["SwoopIn"] = function(ctx)
    -- BASEFLY.inc:217
    -- Instead of coming right at target, fly towards him
    -- at an angle for a little bit...
    -- "Swoop" in for the kill!
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- BASEFLY.inc:225
    ctx:state().g_targetDirY = 0 -- BASEFLY.inc:227
    ctx:state().g_bSwooping = true -- BASEFLY.inc:228
    ctx:randomInt(30, 50, "g_nRandom") -- BASEFLY.inc:230
    ctx:randomInt(0, 1, "g_nTemp") -- BASEFLY.inc:232
    if ctx:condition("g_nTemp==0") then -- BASEFLY.inc:234
        ctx:state().g_nRandom = (tonumber(ctx:state().g_nRandom) or 0) * -1 -- BASEFLY.inc:235
    end -- BASEFLY.inc:236
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASEFLY.inc:238
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:rotateDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", "g_nRandom") -- BASEFLY.inc:240
    ctx:self():faceDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", 180) -- BASEFLY.inc:241
    ctx:self():strafe("g_targetDirX", "g_targetDirY", "g_targetDirZ", "TRUE") -- BASEFLY.inc:243
    ctx:wait("AGGRESSIVE_WAIT", 1, "SwoopDone") -- BASEFLY.inc:245
    do return ctx:exit("") end -- BASEFLY.inc:247
end

script.labels["BackOffTick"] = function(ctx)
    -- BASEFLY.inc:250
    ctx:wait("AGGRESSIVE_WAIT", "BACKOFF_TICK", "BackOffTick") -- BASEFLY.inc:253
    mm9.gosub(script, ctx, "DoBackoff") -- BASEFLY.inc:254
    do return ctx:exit("") end -- BASEFLY.inc:256
end

script.labels["BackoffDone"] = function(ctx)
    -- BASEFLY.inc:259
    ctx:self():setStat("flyVel", "g_flyVel") -- BASEFLY.inc:261
    ctx:state().g_bBackingOff = false -- BASEFLY.inc:263
    mm9.gosub(script, ctx, "BackoffStop") -- BASEFLY.inc:265
    -- gosub AggressiveStart
    if ctx:condition("g_hTarget!=NULL") then -- BASEFLY.inc:268
        ctx:self():sendAlert(ctx:object("g_hTarget")) -- BASEFLY.inc:269
    end -- BASEFLY.inc:270
    mm9.gosub(script, ctx, "SwoopIn") -- BASEFLY.inc:272
    do return ctx:exit("") end -- BASEFLY.inc:274
end

script.labels["DoBackoff"] = function(ctx)
    -- BASEFLY.inc:277
    ctx:state().g_bBackingOff = true -- BASEFLY.inc:280
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- BASEFLY.inc:282
    ctx:state().g_targetDirY = 0 -- BASEFLY.inc:284
    ctx:self():faceDir("g_targetDirX", 0, "g_targetDirZ", 360) -- BASEFLY.inc:286
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:rotateDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", 180) -- BASEFLY.inc:287
    ctx:set("g_targetDirY", "g_backOffYVal") -- BASEFLY.inc:289
    if ctx:condition("g_hTarget!=NULL") then -- BASEFLY.inc:291
        ctx:state().g_bTemp = ctx:object("g_hTarget"):getStat("IsFlying") -- BASEFLY.inc:292
        if ctx:condition("g_bTemp==TRUE") then -- BASEFLY.inc:293
            ctx:state().g_targetDirY = 0 -- BASEFLY.inc:294
        end -- BASEFLY.inc:295
    end -- BASEFLY.inc:296
    ctx:self():strafe("g_targetDirX", "g_targetDirY", "g_targetDirZ", "TRUE") -- BASEFLY.inc:298
    do return ctx:exit("") end -- BASEFLY.inc:300
end

script.labels["BackOff"] = function(ctx)
    -- BASEFLY.inc:303
    ctx:self():setStat("flyVel", "g_flyVel") -- BASEFLY.inc:306
    mm9.gosub(script, ctx, "AggressiveStop") -- BASEFLY.inc:308
    ctx:wait("AGGRESSIVE_WAIT", "BACKOFF_TICK", "BackOffTick") -- BASEFLY.inc:310
    mm9.gosub(script, ctx, "DoBackoff") -- BASEFLY.inc:312
    ctx:wait("BASE_EVADE_WAIT", "g_backOffTime", "BackOffDone") -- BASEFLY.inc:314
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASEFLY.inc:316
    do return ctx:exit("") end -- BASEFLY.inc:319
end

script.labels["BackoffStop"] = function(ctx)
    -- BASEFLY.inc:322
    ctx:wait("AGGRESSIVE_WAIT", 0.1, "DoNothing") -- BASEFLY.inc:324
    do return ctx:exit("") end -- BASEFLY.inc:326
end

script.labels["BaseFlyAttackDone"] = function(ctx)
    -- BASEFLY.inc:329
    -- Now back off....
    ctx:self():setStat("FlyVel", "g_flyVel") -- BASEFLY.inc:335
    ctx:self():setStat("RunVel", "g_runVel") -- BASEFLY.inc:336
    if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:338
        do return ctx:exit("TRUE") end -- BASEFLY.inc:339
    end -- BASEFLY.inc:340
    mm9.gosub(script, ctx, "BackOff") -- BASEFLY.inc:342
    do return ctx:exit("TRUE") end -- BASEFLY.inc:345
end

script.labels["AttackArrival"] = function(ctx)
    -- BASEFLY.inc:348
    do return ctx:exit("TRUE") end -- BASEFLY.inc:351
end

script.labels["TargetMoving"] = function(ctx)
    -- BASEFLY.inc:354
    ctx:state().g_nTemp = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- BASEFLY.inc:357
    if ctx:condition("g_nTemp < g_attackRange") then -- BASEFLY.inc:359
        mm9.gosub(script, ctx, "AttackStrafe") -- BASEFLY.inc:360
    else -- BASEFLY.inc:361
        ctx:self():runTo(ctx:object("g_hTarget"), "g_runToRange", "AttackArrival") -- BASEFLY.inc:362
    end -- BASEFLY.inc:363
    do return ctx:exit("") end -- BASEFLY.inc:365
end

script.labels["TargetStill"] = function(ctx)
    -- BASEFLY.inc:368
    mm9.gosub(script, ctx, "AttackStrafe") -- BASEFLY.inc:371
    do return ctx:exit("") end -- BASEFLY.inc:373
end

script.labels["AttackTick"] = function(ctx)
    -- BASEFLY.inc:376
    -- Keep us strafing near the target as we go by...
    mm9.gosub(script, ctx, "IsTargetMoving") -- BASEFLY.inc:382
    if ctx:condition("g_bTemp==FALSE") then -- BASEFLY.inc:384
        ctx:set("g_nTemp", "g_runVel * 0.8") -- BASEFLY.inc:385
        ctx:self():setStat("RunVel", "g_nTemp") -- BASEFLY.inc:386
        ctx:set("g_nTemp", "g_flyVel * 0.8") -- BASEFLY.inc:388
        if ctx:condition("g_flyVel > MAX_ATTACK_FLY_VEL") then -- BASEFLY.inc:390
            ctx:set("g_nTemp", "MAX_ATTACK_FLY_VEL") -- BASEFLY.inc:391
        end -- BASEFLY.inc:392
        ctx:self():setStat("FlyVel", "g_nTemp") -- BASEFLY.inc:394
    else -- BASEFLY.inc:395
        ctx:self():setStat("FlyVel", "g_flyVel") -- BASEFLY.inc:396
    end -- BASEFLY.inc:397
    if ctx:condition("g_bAttackPerformed==TRUE") then -- BASEFLY.inc:399
        do return ctx:exit("") end -- BASEFLY.inc:400
    end -- BASEFLY.inc:401
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "AttackTick") -- BASEFLY.inc:403
    if ctx:condition("g_bTemp==TRUE") then -- BASEFLY.inc:405
        mm9.gosub(script, ctx, "TargetMoving") -- BASEFLY.inc:406
    else -- BASEFLY.inc:407
        mm9.gosub(script, ctx, "TargetStill") -- BASEFLY.inc:408
    end -- BASEFLY.inc:409
    do return ctx:exit("") end -- BASEFLY.inc:411
end

script.labels["AttackStrafeObstacle"] = function(ctx)
    -- BASEFLY.inc:414
    -- p0 - hObstacle
    -- p1-3 - normal
    ctx:getParam(0, "g_hObject") -- BASEFLY.inc:421
    if ctx:condition("g_hObject==g_hTarget") then -- BASEFLY.inc:423
        -- bumping into target... strafing on...
        mm9.gosub(script, ctx, "AttackStrafe") -- BASEFLY.inc:425
        do return ctx:exit("TRUE") end -- BASEFLY.inc:426
    end -- BASEFLY.inc:427
    ctx:debugOut("bumped", "into", "something", "during", "attack...", "stopping") -- BASEFLY.inc:429
    ctx:self():stop() -- BASEFLY.inc:431
    do return ctx:exit("TRUE") end -- BASEFLY.inc:433
end

script.labels["AttackStrafe"] = function(ctx)
    -- BASEFLY.inc:436
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- BASEFLY.inc:438
    ctx:state().g_targetDirY = 0 -- BASEFLY.inc:440
    ctx:onEvent("OnObstacle", "AttackStrafeObstacle") -- BASEFLY.inc:442
    ctx:self():faceDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", 180) -- BASEFLY.inc:444
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:rotateDir("g_targetDirX", "g_targetDirY", "g_targetDirZ", "g_attackStrafeAngle") -- BASEFLY.inc:446
    ctx:self():strafe("g_targetDirX", 0, "g_targetDirZ", "TRUE") -- BASEFLY.inc:447
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASEFLY.inc:448
    do return ctx:exit("") end -- BASEFLY.inc:450
end

script.labels["BaseFlyAttack"] = function(ctx)
    -- BASEFLY.inc:453
    if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:456
        ctx:debugOut("(BaseFlyAttack)", "ASSERT(g_hTarget!=NULL)") -- BASEFLY.inc:457
        ctx:self():stop() -- BASEFLY.inc:458
        do return ctx:exit("") end -- BASEFLY.inc:459
    end -- BASEFLY.inc:460
    ctx:getTime("g_nLastAttackTime") -- BASEFLY.inc:462
    mm9.gosub(script, ctx, "AggressiveStop") -- BASEFLY.inc:464
    ctx:wait("AGGRESSIVE_WAIT", "AGGRESSIVE_TICK", "AttackTick") -- BASEFLY.inc:466
    ctx:state().g_bAttackPerformed = false -- BASEFLY.inc:468
    ctx:randomInt(0, 1, "g_nRandom") -- BASEFLY.inc:470
    if ctx:condition("g_nRandom==1") then -- BASEFLY.inc:472
        ctx:state().g_attackStrafeAngle = 45 -- BASEFLY.inc:473
    else -- BASEFLY.inc:474
        ctx:state().g_attackStrafeAngle = -45 -- BASEFLY.inc:475
    end -- BASEFLY.inc:476
    mm9.gosub(script, ctx, "AttackStrafe") -- BASEFLY.inc:478
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASEFLY.inc:480
    ctx:self():attack("BaseFlyAttackDone") -- BASEFLY.inc:482
    do return ctx:exit("") end -- BASEFLY.inc:484
end

script.labels["TauntDone"] = function(ctx)
    -- BASEFLY.inc:487
    mm9.gosub(script, ctx, "AggressiveStart") -- BASEFLY.inc:490
    do return ctx:exit("") end -- BASEFLY.inc:492
end

script.labels["SetupTarget"] = function(ctx)
    -- BASEFLY.inc:495
    mm9.gosub(script, ctx, "DisableWandering") -- BASEFLY.inc:497
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BASEFLY.inc:499
    mm9.gosub(script, ctx, "AlertStart") -- BASEFLY.inc:500
    ctx:getTime("g_nLastAttackTime") -- BASEFLY.inc:502
    do return ctx:exit("") end -- BASEFLY.inc:504
end

script.labels["OnFoundTarget"] = function(ctx)
    -- BASEFLY.inc:507
    -- p0	- hPlayer
    ctx:getParam(0, "g_hTarget") -- BASEFLY.inc:513
    mm9.gosub(script, ctx, "SetupTarget") -- BASEFLY.inc:515
    mm9.gosub(script, ctx, "AggressiveStop") -- BASEFLY.inc:516
    ctx:self():taunt("TauntDone") -- BASEFLY.inc:518
    do return ctx:exit("") end -- BASEFLY.inc:520
end

script.labels["OnDamage"] = function(ctx)
    -- BASEFLY.inc:523
    -- p0 - hDamager
    ctx:getParam(0, "g_hAttacker") -- BASEFLY.inc:529
    mm9.gosub(script, ctx, "SetupAttacker") -- BASEFLY.inc:531
    do return ctx:exit("") end -- BASEFLY.inc:533
end

script.labels["OnDamageDone"] = function(ctx)
    -- BASEFLY.inc:536
    ctx:self():setStat("FlyVel", "g_flyVel") -- BASEFLY.inc:539
    if ctx:condition("g_hAttacker!=NULL") then -- BASEFLY.inc:541
        ctx:state().g_hTarget = ctx:self():target() -- BASEFLY.inc:542
        if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:544
            ctx:set("g_hTarget", "g_hAttacker") -- BASEFLY.inc:545
            mm9.gosub(script, ctx, "SetupTarget") -- BASEFLY.inc:546
            mm9.gosub(script, ctx, "AggressiveStart") -- BASEFLY.inc:547
            do return ctx:exit("TRUE") end -- BASEFLY.inc:548
        end -- BASEFLY.inc:549
        ctx:randomInt(0, 100, "g_nRandom") -- BASEFLY.inc:551
        if ctx:condition("g_nRandom < 50") then -- BASEFLY.inc:553
            ctx:set("g_hTarget", "g_hAttacker") -- BASEFLY.inc:554
            mm9.gosub(script, ctx, "SetupTarget") -- BASEFLY.inc:555
            mm9.gosub(script, ctx, "AggressiveStart") -- BASEFLY.inc:556
            do return ctx:exit("TRUE") end -- BASEFLY.inc:557
        end -- BASEFLY.inc:558
    end -- BASEFLY.inc:559
    if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:561
        mm9.gosub(script, ctx, "ClearTarget") -- BASEFLY.inc:562
        do return ctx:exit("") end -- BASEFLY.inc:563
    end -- BASEFLY.inc:564
    ctx:state().g_bTemp = ctx:self():canAttack() -- BASEFLY.inc:566
    if ctx:condition("g_bTemp==TRUE") then -- BASEFLY.inc:568
        mm9.gosub(script, ctx, "AggressiveStart") -- BASEFLY.inc:569
    else -- BASEFLY.inc:570
        mm9.gosub(script, ctx, "Backoff") -- BASEFLY.inc:571
    end -- BASEFLY.inc:572
    do return ctx:exit("TRUE") end -- BASEFLY.inc:574
end

script.labels["GiveUpOnTarget"] = function(ctx)
    -- BASEFLY.inc:577
    mm9.gosub(script, ctx, "ClearTarget") -- BASEFLY.inc:580
    do return ctx:exit("") end -- BASEFLY.inc:582
end

script.labels["ClearTarget"] = function(ctx)
    -- BASEFLY.inc:585
    mm9.gosub(script, ctx, "AggressiveStop") -- BASEFLY.inc:588
    mm9.gosub(script, ctx, "BackoffStop") -- BASEFLY.inc:589
    mm9.gosub(script, ctx, "AlertStop") -- BASEFLY.inc:590
    ctx:state().g_hTarget = nil -- BASEFLY.inc:592
    ctx:self():setTarget(nil) -- BASEFLY.inc:593
    ctx:self():stop() -- BASEFLY.inc:594
    mm9.gosub(script, ctx, "BaseWanderStart") -- BASEFLY.inc:596
    do return ctx:exit("") end -- BASEFLY.inc:598
end

script.labels["OnLostTarget"] = function(ctx)
    -- BASEFLY.inc:601
    mm9.gosub(script, ctx, "ClearTarget") -- BASEFLY.inc:604
    do return ctx:exit("") end -- BASEFLY.inc:606
end

script.labels["OnTargetDead"] = function(ctx)
    -- BASEFLY.inc:609
    mm9.gosub(script, ctx, "ClearTarget") -- BASEFLY.inc:612
    do return ctx:exit("") end -- BASEFLY.inc:614
end

script.labels["NewTargetCheck"] = function(ctx)
    -- BASEFLY.inc:617
    -- Fill in g_hObject with the potential new target,
    -- and this function takes care of the rest....
    if ctx:condition("g_hObject==NULL") then -- BASEFLY.inc:624
        do return ctx:exit("") end -- BASEFLY.inc:625
    end -- BASEFLY.inc:626
    if ctx:condition("g_hObject==g_hMyObject") then -- BASEFLY.inc:628
        do return ctx:exit("FALSE") end -- BASEFLY.inc:629
    end -- BASEFLY.inc:630
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- BASEFLY.inc:632
    if ctx:condition("g_bTemp==TRUE") then -- BASEFLY.inc:634
        do return ctx:exit("FALSE") end -- BASEFLY.inc:635
    end -- BASEFLY.inc:636
    ctx:getTime("g_nLastAttackTime") -- BASEFLY.inc:638
    if ctx:condition("g_hTarget==NULL") then -- BASEFLY.inc:640
        ctx:set("g_hTarget", "g_hObject") -- BASEFLY.inc:641
        ctx:self():setTarget(ctx:object("g_hTarget")) -- BASEFLY.inc:642
        mm9.gosub(script, ctx, "AggressiveStart") -- BASEFLY.inc:643
        do return ctx:exit("TRUE") end -- BASEFLY.inc:644
    end -- BASEFLY.inc:645
    do return ctx:exit("") end -- BASEFLY.inc:647
end

script.labels["OnAlert"] = function(ctx)
    -- BASEFLY.inc:650
    ctx:getParam(0, "g_hObject") -- BASEFLY.inc:652
    mm9.gosub(script, ctx, "NewTargetCheck") -- BASEFLY.inc:653
    do return ctx:exit("") end -- BASEFLY.inc:655
end

script.labels["OnProjectile"] = function(ctx)
    -- BASEFLY.inc:658
    ctx:getParam(1, "g_hObject") -- BASEFLY.inc:661
    mm9.gosub(script, ctx, "NewTargetCheck") -- BASEFLY.inc:662
    do return ctx:exit("") end -- BASEFLY.inc:665
end

script.labels["FlyAttackPerformed"] = function(ctx)
    -- BASEFLY.inc:668
    ctx:state().g_bAttackPerformed = true -- BASEFLY.inc:670
    do return ctx:exit("FALSE") end -- BASEFLY.inc:671
end

script.labels["DisableWandering"] = function(ctx)
    -- BASEFLY.inc:674
    -- Do all things necessary to disable
    -- Wandering...
    mm9.gosub(script, ctx, "BaseWanderStop") -- BASEFLY.inc:681
    ctx:state().bWanderDisabled = true -- BASEFLY.inc:683
    ctx:onEvent("OnObstacle") -- BASEFLY.inc:685
    ctx:onEvent("OnStuckDone") -- BASEFLY.inc:686
    ctx:onEvent("OnStuck") -- BASEFLY.inc:687
    do return ctx:exit("") end -- BASEFLY.inc:689
end

script.labels["EnableWandering"] = function(ctx)
    -- BASEFLY.inc:692
    -- Do all things necessary to disable
    -- Wandering...
    ctx:state().bWanderDisabled = false -- BASEFLY.inc:699
    mm9.gosub(script, ctx, "BaseWanderStart") -- BASEFLY.inc:700
    do return ctx:exit("") end -- BASEFLY.inc:702
end

script.labels["BaseWanderStartWalking"] = function(ctx)
    -- BASEFLY.inc:705
    -- Override this so we can slow down our flying speed
    ctx:self():setStat("FlyVel", "g_walkVel") -- BASEFLY.inc:711
    mm9.gosub(script, ctx, "BaseWanderStartWalking") -- BASEFLY.inc:712
    do return ctx:exit("") end -- BASEFLY.inc:714
end

script.labels["BaseWanderGo"] = function(ctx)
    -- BASEFLY.inc:717
    mm9.gosub(script, ctx, "BaseWanderGo") -- BASEFLY.inc:719
    ctx:self():setStat("CheckForObstacles", "FALSE") -- BASEFLY.inc:720
    if ctx:condition("nWanderPathCount!=0") then -- BASEFLY.inc:722
        -- SetStat g_hMyObject,AllowRotateY,TRUE
        -- SetStat g_hMyObject,FaceVelocity,TRUE
    end -- BASEFLY.inc:725
    do return ctx:exit("") end -- BASEFLY.inc:727
end

script.labels["BaseWanderStop"] = function(ctx)
    -- BASEFLY.inc:731
    ctx:self():setStat("CheckForObstacles", "TRUE") -- BASEFLY.inc:734
    ctx:self():setStat("FlyVel", "g_flyVel") -- BASEFLY.inc:735
    -- SetStat g_hMyObject,AllowRotateY,FALSE
    -- SetStat g_hMyObject,FaceVelocity,FALSE
    mm9.gosub(script, ctx, "BaseWanderStop") -- BASEFLY.inc:739
    do return ctx:exit("") end -- BASEFLY.inc:741
end

script.labels["OnHelp"] = function(ctx)
    -- BASEFLY.inc:745
    -- p0 - hPoorSlob
    -- p1 - hBadGuy
    if ctx:condition("g_hTarget!=NULL") then -- BASEFLY.inc:751
        do return ctx:exit("") end -- BASEFLY.inc:752
    end -- BASEFLY.inc:753
    ctx:getParam(0, "g_hObject") -- BASEFLY.inc:755
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hObject")) -- BASEFLY.inc:757
    if ctx:condition("g_bTemp==FALSE") then -- BASEFLY.inc:759
        do return ctx:exit("") end -- BASEFLY.inc:760
    end -- BASEFLY.inc:761
    ctx:getParam(1, "g_hObject") -- BASEFLY.inc:763
    mm9.gosub(script, ctx, "NewTargetCheck") -- BASEFLY.inc:764
    do return ctx:exit("") end -- BASEFLY.inc:766
end

script.labels["BaseFlyInitCallbacks"] = function(ctx)
    -- BASEFLY.inc:770
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- BASEFLY.inc:773
    ctx:onEvent("OnLostTarget", "OnLostTarget") -- BASEFLY.inc:774
    ctx:onEvent("OnDamageDone", "OnDamageDone") -- BASEFLY.inc:775
    ctx:onEvent("OnDamage", "OnDamage") -- BASEFLY.inc:776
    ctx:onEvent("OnTargetDead", "OnTargetDead") -- BASEFLY.inc:777
    ctx:onEvent("OnAlert", "OnAlert") -- BASEFLY.inc:778
    ctx:onEvent("OnProjectile", "OnProjectile") -- BASEFLY.inc:779
    ctx:onEvent("OnHelp", "OnHelp") -- BASEFLY.inc:780
    do return ctx:exit("") end -- BASEFLY.inc:782
end

script.labels["OnGetPlayer"] = function(ctx)
    -- BASEFLY.inc:785
    ctx:state().g_hObject = ctx:player() -- BASEFLY.inc:787
    if ctx:condition("g_hObject==g_hTarget") then -- BASEFLY.inc:789
        do return ctx:exit("") end -- BASEFLY.inc:790
    end -- BASEFLY.inc:791
    if ctx:condition("g_hTarget!=NULL") then -- BASEFLY.inc:793
        mm9.gosub(script, ctx, "ClearTarget") -- BASEFLY.inc:794
    end -- BASEFLY.inc:795
    ctx:set("g_hTarget", "g_hObject") -- BASEFLY.inc:797
    mm9.gosub(script, ctx, "AggressiveStart") -- BASEFLY.inc:798
    do return ctx:exit("") end -- BASEFLY.inc:800
end

script.labels["OnGetMe"] = function(ctx)
    -- BASEFLY.inc:803
    ctx:getParam(0, "g_hObject") -- BASEFLY.inc:805
    if ctx:condition("g_hObject==g_hTarget") then -- BASEFLY.inc:807
        do return ctx:exit("") end -- BASEFLY.inc:808
    end -- BASEFLY.inc:809
    if ctx:condition("g_hTarget!=NULL") then -- BASEFLY.inc:811
        mm9.gosub(script, ctx, "ClearTarget") -- BASEFLY.inc:812
    end -- BASEFLY.inc:813
    ctx:set("g_hTarget", "g_hObject") -- BASEFLY.inc:815
    mm9.gosub(script, ctx, "AggressiveStart") -- BASEFLY.inc:816
    do return ctx:exit("") end -- BASEFLY.inc:818
end

script.labels["BaseFlyInit"] = function(ctx)
    -- BASEFLY.inc:822
    mm9.gosub(script, ctx, "BaseFlyInitCallbacks") -- BASEFLY.inc:827
    mm9.gosub(script, ctx, "InitCommon") -- BASEFLY.inc:828
    ctx:addModelKey("rAttack", "FlyAttackPerformed") -- BASEFLY.inc:830
    ctx:addModelKey("lAttack", "FlyAttackPerformed") -- BASEFLY.inc:831
    ctx:addModelKey("Bite", "FlyAttackPerformed") -- BASEFLY.inc:832
    ctx:addModelKey("rKick", "FlyAttackPerformed") -- BASEFLY.inc:833
    ctx:addModelKey("lKick", "FlyAttackPerformed") -- BASEFLY.inc:834
    ctx:state().g_runVel = ctx:self():getStat("RunVel") -- BASEFLY.inc:836
    ctx:state().g_walkVel = ctx:self():getStat("WalkVel") -- BASEFLY.inc:837
    ctx:state().g_flyVel = ctx:self():getStat("flyVel") -- BASEFLY.inc:838
    ctx:state().g_attackRange = ctx:self():getStat("AttackRange") -- BASEFLY.inc:839
    ctx:set("g_runToRange", "g_attackRange * 0.95") -- BASEFLY.inc:841
    ctx:addTrigger("GetPlayer", "OnGetPlayer") -- BASEFLY.inc:844
    ctx:addTrigger("GetMe", "OnGetMe") -- BASEFLY.inc:845
    mm9.gosub(script, ctx, "BaseWanderInit") -- BASEFLY.inc:847
    ctx:state().g_hTarget = ctx:self():target() -- BASEFLY.inc:849
    if ctx:condition("g_hTarget!=NULL") then -- BASEFLY.inc:850
        mm9.gosub(script, ctx, "SetupTarget") -- BASEFLY.inc:851
    end -- BASEFLY.inc:852
    do return ctx:exit("") end -- BASEFLY.inc:854
end

return script
