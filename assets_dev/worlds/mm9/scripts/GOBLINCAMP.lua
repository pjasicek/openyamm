-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GOBLINCAMP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "base.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "aiglobals.inc" }

-- Goblincamp.scr
-- John Machin
-- This script uses base.inc and extends
-- it to allow for this Goblin camp to attack
-- the Goblin camp nearby
script.labels["GoblinGoGetHim"] = function(ctx)
    -- GOBLINCAMP.scr:26
    if ctx:condition("g_hTarget==NULL") then -- GOBLINCAMP.scr:29
        do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:30
    end -- GOBLINCAMP.scr:31
    ctx:state().g_bAttacking = ctx:self():isAttacking() -- GOBLINCAMP.scr:33
    if ctx:condition("g_bAttacking==TRUE") then -- GOBLINCAMP.scr:35
        do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:36
    end -- GOBLINCAMP.scr:37
    ctx:state().g_bInAttackRange = ctx:self():isTargetInRange() -- GOBLINCAMP.scr:39
    if ctx:condition("g_bInAttackRange==TRUE") then -- GOBLINCAMP.scr:41
        ctx:state().g_bCanAttack = ctx:self():canAttack() -- GOBLINCAMP.scr:42
        if ctx:condition("g_bCanAttack==TRUE") then -- GOBLINCAMP.scr:44
            mm9.gosub(script, ctx, "GoblinAttackReady") -- GOBLINCAMP.scr:45
        end -- GOBLINCAMP.scr:46
        do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:48
    end -- GOBLINCAMP.scr:49
    ctx:self():runTo(ctx:object("g_hTarget")) -- GOBLINCAMP.scr:51
    ctx:self():setTargetLostTime(30) -- GOBLINCAMP.scr:53
    do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:55
end

script.labels["OnUse"] = function(ctx)
    -- GOBLINCAMP.scr:60
    ctx:getParam(0, "g_hObject") -- GOBLINCAMP.scr:63
    ctx:self():faceObject(ctx:object("g_hObject"), 180) -- GOBLINCAMP.scr:65
    do return ctx:exit("") end -- GOBLINCAMP.scr:67
end

script.labels["GoblinOnAlert"] = function(ctx)
    -- GOBLINCAMP.scr:70
    ctx:getParam(0, "hAlertedBy") -- GOBLINCAMP.scr:72
    ctx:state().sAlertName = ctx:object("hAlertedBy"):className() -- GOBLINCAMP.scr:73
    if ctx:condition("g_hTarget == NULL") then -- GOBLINCAMP.scr:75
        -- Check to see if the alert came from a hen or another rooster
        if ctx:condition("sAlertName == Goblin") then -- GOBLINCAMP.scr:77
            ctx:state().g_bOkAttackType = true -- GOBLINCAMP.scr:78
        end -- GOBLINCAMP.scr:79
    end -- GOBLINCAMP.scr:80
    if ctx:condition("g_bOkAttackType == TRUE") then -- GOBLINCAMP.scr:82
        ctx:state().sAlertName = ctx:object("g_hTarget"):className() -- GOBLINCAMP.scr:83
        -- Make sure we don't hit our fellow dwarves
        if ctx:condition("sAlertName == Goblin") then -- GOBLINCAMP.scr:86
            mm9.gosub(script, ctx, "GoblinFindTarget") -- GOBLINCAMP.scr:87
        end -- GOBLINCAMP.scr:88
        ctx:getParam(1, "g_hTarget") -- GOBLINCAMP.scr:90
        if ctx:condition("g_hTarget != NULL") then -- GOBLINCAMP.scr:91
            ctx:self():setTarget(ctx:object("g_hTarget")) -- GOBLINCAMP.scr:92
            mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:93
        end -- GOBLINCAMP.scr:94
    end -- GOBLINCAMP.scr:96
    do return ctx:exit("") end -- GOBLINCAMP.scr:98
end

script.labels["GoblinFindTarget"] = function(ctx)
    -- GOBLINCAMP.scr:101
    ctx:getObjects("Dwarf", 50000, 5, "g_hDwarfArray", "g_nObjects") -- GOBLINCAMP.scr:103
    if ctx:condition("g_nObjects != NULL") then -- GOBLINCAMP.scr:105
        if ctx:condition("g_hTarget == NULL") then -- GOBLINCAMP.scr:106
            -- Randomly pick a target from the three
            ctx:state().g_nObjects = (tonumber(ctx:state().g_nObjects) or 0) - 1 -- GOBLINCAMP.scr:108
            ctx:randomInt(0, "g_nObjects", "g_nRandom") -- GOBLINCAMP.scr:109
            ctx:arrayGet("g_hDwarfArray", "g_nRandom", "g_hTarget") -- GOBLINCAMP.scr:110
            ctx:self():setTarget(ctx:object("g_hTarget")) -- GOBLINCAMP.scr:111
            if ctx:condition("g_hTarget != NULL") then -- GOBLINCAMP.scr:112
                mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:113
            end -- GOBLINCAMP.scr:114
        end -- GOBLINCAMP.scr:116
    else -- GOBLINCAMP.scr:117
        ctx:wait(0, 1, "GoblinFindTarget") -- GOBLINCAMP.scr:118
    end -- GOBLINCAMP.scr:119
    do return ctx:exit("") end -- GOBLINCAMP.scr:121
end

script.labels["GoblinTargetDead"] = function(ctx)
    -- GOBLINCAMP.scr:124
    ctx:getParam(0, "g_nTemp") -- GOBLINCAMP.scr:127
    ctx:self():setTarget(nil) -- GOBLINCAMP.scr:129
    ctx:state().g_hTarget = nil -- GOBLINCAMP.scr:130
    if ctx:condition("g_nTemp==g_hMyObject") then -- GOBLINCAMP.scr:132
        -- We killed him!
        -- taunt him
        -- Taunt GoblinFindTarget
        mm9.gosub(script, ctx, "GoblinFindTarget") -- GOBLINCAMP.scr:136
    else -- GOBLINCAMP.scr:137
        -- just go home...
        mm9.gosub(script, ctx, "GoblinFindTarget") -- GOBLINCAMP.scr:139
    end -- GOBLINCAMP.scr:140
    do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:142
end

script.labels["GoblinDamageDone"] = function(ctx)
    -- GOBLINCAMP.scr:145
    -- We were attacked, now we want to run
    -- after whoever attacked us!
    if ctx:condition("g_hAttacker==g_hMyObject") then -- GOBLINCAMP.scr:152
        do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:153
    end -- GOBLINCAMP.scr:154
    ctx:state().sAlertName = ctx:object("g_hAttacker"):className() -- GOBLINCAMP.scr:156
    -- Make sure we don't attack fellow dwarves
    if ctx:condition("sAlertName == Goblin") then -- GOBLINCAMP.scr:159
        mm9.gosub(script, ctx, "GoblinFindTarget") -- GOBLINCAMP.scr:160
    end -- GOBLINCAMP.scr:161
    ctx:state().g_nTemp = (ctx:object("g_hAttacker"):isActor() and 1 or 0) -- GOBLINCAMP.scr:163
    if ctx:condition("g_nTemp==FALSE") then -- GOBLINCAMP.scr:165
        -- Not an actor, therefore
        -- never go after it...
        if ctx:condition("g_hTarget!=NULL") then -- GOBLINCAMP.scr:168
            mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:169
            do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:170
        else -- GOBLINCAMP.scr:171
            do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:172
        end -- GOBLINCAMP.scr:173
    end -- GOBLINCAMP.scr:174
    if ctx:condition("g_hTarget==NULL") then -- GOBLINCAMP.scr:176
        ctx:set("g_hTarget", "g_hAttacker") -- GOBLINCAMP.scr:177
        ctx:state().g_bFighting = true -- GOBLINCAMP.scr:178
    else -- GOBLINCAMP.scr:179
        ctx:state().g_bInAttackRange = ctx:self():isTargetInRange() -- GOBLINCAMP.scr:180
        if ctx:condition("g_hAttacker!=NULL") then -- GOBLINCAMP.scr:182
            if ctx:condition("g_hAttacker!=g_hTarget") then -- GOBLINCAMP.scr:183
                ctx:state().g_sTemp = ctx:object("g_hAttacker"):className() -- GOBLINCAMP.scr:184
                if ctx:condition("g_sTemp!=Player") then -- GOBLINCAMP.scr:185
                    do return mm9.gotoLabel(script, ctx, "GoblinSkipTargetSwitch") end -- GOBLINCAMP.scr:186
                end -- GOBLINCAMP.scr:187
                -- 70% chance we'll switch to the damager
                ctx:state().g_nTemp = 70 -- GOBLINCAMP.scr:189
                if ctx:condition("g_bInAttackRange==TRUE") then -- GOBLINCAMP.scr:190
                    -- we're already in attack range of our current target
                    -- so lower chances of switching
                    ctx:state().g_nTemp = 10 -- GOBLINCAMP.scr:193
                end -- GOBLINCAMP.scr:194
                ctx:state().g_nDist1 = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- GOBLINCAMP.scr:196
                ctx:state().g_nDist2 = ctx:self():aiDistanceTo(ctx:object("g_hAttacker")) -- GOBLINCAMP.scr:197
                if ctx:condition("g_nDist2 > g_nDist1") then -- GOBLINCAMP.scr:199
                    -- reduce odds even further...
                    ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) / 2 -- GOBLINCAMP.scr:201
                end -- GOBLINCAMP.scr:202
                ctx:randomInt(0, 100, "g_nRandom") -- GOBLINCAMP.scr:204
                if ctx:condition("g_nRandom < g_nTemp") then -- GOBLINCAMP.scr:205
                    -- Okay, we decided to switch our current target to the
                    -- attacker!
                    ctx:set("g_hTarget", "g_hAttacker") -- GOBLINCAMP.scr:210
                end -- GOBLINCAMP.scr:211
            end -- GOBLINCAMP.scr:212
        end -- GOBLINCAMP.scr:213
    end -- GOBLINCAMP.scr:214
end

script.labels["GoblinSkipTargetSwitch"] = function(ctx)
    -- GOBLINCAMP.scr:216
    if ctx:condition("g_hTarget==0") then -- GOBLINCAMP.scr:218
        -- FALSE means have the AI do its default handling of this event.
        do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:219
    end -- GOBLINCAMP.scr:220
    -- Go after the Target...
    ctx:self():setTarget(ctx:object("g_hTarget")) -- GOBLINCAMP.scr:224
    mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:226
    do return ctx:exit("") end -- GOBLINCAMP.scr:228
end

script.labels["GoblinAttackReady"] = function(ctx)
    -- GOBLINCAMP.scr:232
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:state().sAlertName = ctx:object("g_hTarget"):className() -- GOBLINCAMP.scr:239
    if ctx:condition("sAlertName == Goblin") then -- GOBLINCAMP.scr:240
        mm9.gosub(script, ctx, "GoblinFindTarget") -- GOBLINCAMP.scr:241
    end -- GOBLINCAMP.scr:242
    ctx:state().g_bFighting = true -- GOBLINCAMP.scr:244
    ctx:getTime("g_nLastAttackTime") -- GOBLINCAMP.scr:246
    ctx:self():attack() -- GOBLINCAMP.scr:248
    do return ctx:exit("") end -- GOBLINCAMP.scr:250
end

script.labels["GoblinLostTarget"] = function(ctx)
    -- GOBLINCAMP.scr:253
    -- We lost the target.  Reaquire and attack;
    if ctx:condition("g_hTarget != NULL") then -- GOBLINCAMP.scr:257
        ctx:self():setTarget(ctx:object("g_hTarget")) -- GOBLINCAMP.scr:258
        mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:259
    else -- GOBLINCAMP.scr:260
        ctx:state().g_hTarget = nil -- GOBLINCAMP.scr:261
        mm9.gosub(script, ctx, "GoblinFindTarget") -- GOBLINCAMP.scr:262
    end -- GOBLINCAMP.scr:263
    do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:265
end

script.labels["GoblinOutOfRangeWait"] = function(ctx)
    -- GOBLINCAMP.scr:268
    -- We don't want to run after target
    -- until it's far enough away or we are
    -- ready to attack...
    if ctx:condition("g_hTarget==NULL") then -- GOBLINCAMP.scr:275
        do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:276
    end -- GOBLINCAMP.scr:277
    ctx:state().g_bAttacking = ctx:self():isAttacking() -- GOBLINCAMP.scr:279
    if ctx:condition("g_bAttacking==TRUE") then -- GOBLINCAMP.scr:281
        ctx:wait(0, 0.5, "GoblinOutOfRangeWait") -- GOBLINCAMP.scr:282
        do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:283
    end -- GOBLINCAMP.scr:284
    ctx:state().g_bCanAttack = ctx:self():canAttack() -- GOBLINCAMP.scr:286
    if ctx:condition("g_bCanAttack==TRUE") then -- GOBLINCAMP.scr:287
        mm9.gosub(script, ctx, "GoblinMaybeRangeAttack") -- GOBLINCAMP.scr:288
        ctx:state().g_bAttacking = ctx:self():isAttacking() -- GOBLINCAMP.scr:290
        if ctx:condition("g_bAttacking==TRUE") then -- GOBLINCAMP.scr:292
            do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:293
        end -- GOBLINCAMP.scr:294
        mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:296
        do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:297
    end -- GOBLINCAMP.scr:298
    -- randomly play a taunt animation...
    ctx:randomInt(0, 100, "g_nRandom") -- GOBLINCAMP.scr:301
    if ctx:condition("g_nRandom < 30") then -- GOBLINCAMP.scr:303
        if ctx:condition("g_nRandom < 15") then -- GOBLINCAMP.scr:304
            ctx:self():taunt("GoblinAttackWaitAnimDone") -- GOBLINCAMP.scr:305
        else -- GOBLINCAMP.scr:306
            ctx:self():aware("GoblinAttackWaitAnimDone") -- GOBLINCAMP.scr:307
        end -- GOBLINCAMP.scr:308
        do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:309
    end -- GOBLINCAMP.scr:310
    -- AIGetDistance g_hTarget, g_nDist1
    -- if ( g_nDist1 > 200 )		; if they are too far away...
    ctx:self():walkTo(ctx:object("g_hTarget")) -- GOBLINCAMP.scr:315
    -- Wait 0, 0.5, GoblinOutOfRangeWalkingWait
    -- Exit TRUE
    -- endif
    -- Continue waiting....
    ctx:wait(0, 0.5, "GoblinOutOfRangeWait") -- GOBLINCAMP.scr:322
    do return ctx:exit("") end -- GOBLINCAMP.scr:324
end

script.labels["GoblinStuckDone"] = function(ctx)
    -- GOBLINCAMP.scr:327
    -- This is called when a stuck animation
    -- has finished... We'll just re-attempt
    -- to run after our target...
    if ctx:condition("g_hTarget==NULL") then -- GOBLINCAMP.scr:334
        do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:335
    end -- GOBLINCAMP.scr:336
    -- for now, don't wait when stuck..
    mm9.gosub(script, ctx, "GoblinFindTarget") -- GOBLINCAMP.scr:341
    do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:342
    if ctx:condition("g_nStuckTime==0.0") then -- GOBLINCAMP.scr:344
        ctx:getTime("g_nStuckTime") -- GOBLINCAMP.scr:345
    else -- GOBLINCAMP.scr:346
        ctx:getTime("g_nTemp") -- GOBLINCAMP.scr:347
        ctx:sub("g_nTemp", "g_nStuckTime") -- GOBLINCAMP.scr:348
        if ctx:condition("g_nTemp > MIN_STUCK_TIME") then -- GOBLINCAMP.scr:350
            ctx:state().g_nStuckTime = 0 -- GOBLINCAMP.scr:351
            mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:352
            do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:353
        end -- GOBLINCAMP.scr:354
    end -- GOBLINCAMP.scr:355
    do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:357
end

script.labels["GoblinOutOfRangeWalkingWait"] = function(ctx)
    -- GOBLINCAMP.scr:361
    -- Once we start walking after target,
    -- we want to start running as soon as
    -- we are attack ready...
    ctx:state().g_bCanAttack = ctx:self():canAttack() -- GOBLINCAMP.scr:369
    if ctx:condition("g_bCanAttack==TRUE") then -- GOBLINCAMP.scr:370
        mm9.gosub(script, ctx, "GoblinMaybeRangeAttack") -- GOBLINCAMP.scr:371
        ctx:state().g_bAttacking = ctx:self():isAttacking() -- GOBLINCAMP.scr:372
        if ctx:condition("g_bAttacking==TRUE") then -- GOBLINCAMP.scr:374
            do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:375
        end -- GOBLINCAMP.scr:376
        mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:378
        do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:379
    end -- GOBLINCAMP.scr:380
    ctx:wait(0, 0.5, "GoblinOutOfRangeWait") -- GOBLINCAMP.scr:382
    do return ctx:exit("") end -- GOBLINCAMP.scr:384
end

script.labels["GoblinAttackWaitAnimDone"] = function(ctx)
    -- GOBLINCAMP.scr:388
    mm9.gosub(script, ctx, "GoblinOutOfRangeWait") -- GOBLINCAMP.scr:391
    do return ctx:exit("") end -- GOBLINCAMP.scr:393
end

script.labels["GoblinMaybeRangeAttack"] = function(ctx)
    -- GOBLINCAMP.scr:396
    -- If we can range attack, we randomly
    -- decide to do so here...
    if ctx:condition("g_bHasRangeAttack==FALSE") then -- GOBLINCAMP.scr:402
        do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:403
    end -- GOBLINCAMP.scr:404
    ctx:state().g_bCanAttack = ctx:self():canAttack() -- GOBLINCAMP.scr:406
    if ctx:condition("g_bCanAttack==FALSE") then -- GOBLINCAMP.scr:408
        do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:409
    end -- GOBLINCAMP.scr:410
    ctx:randomInt(0, 100, "g_nRandom") -- GOBLINCAMP.scr:412
    ctx:state().g_nTemp = 0 -- GOBLINCAMP.scr:413
    ctx:self():estimateRangeAttackHit(ctx:object("g_hObject")) -- GOBLINCAMP.scr:414
    if ctx:condition("g_hObject==NULL") then -- GOBLINCAMP.scr:415
        ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) + 20 -- GOBLINCAMP.scr:416
    else -- GOBLINCAMP.scr:417
        if ctx:condition("g_hObject==g_hTarget") then -- GOBLINCAMP.scr:418
            ctx:state().g_nTemp = 80 -- GOBLINCAMP.scr:419
        else -- GOBLINCAMP.scr:420
            ctx:state().g_bTemp = ctx:object("g_hObject"):isClass("AIBase") -- GOBLINCAMP.scr:421
            if ctx:condition("g_bTemp==TRUE") then -- GOBLINCAMP.scr:422
                ctx:state().g_nTemp = 0 -- GOBLINCAMP.scr:423
            end -- GOBLINCAMP.scr:424
        end -- GOBLINCAMP.scr:425
    end -- GOBLINCAMP.scr:426
    if ctx:condition("g_nRandom <= g_nTemp") then -- GOBLINCAMP.scr:428
        mm9.gosub(script, ctx, "GoblinDoRangeAttack") -- GOBLINCAMP.scr:429
    end -- GOBLINCAMP.scr:430
    do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:433
end

script.labels["GoblinRangeAttackDone"] = function(ctx)
    -- GOBLINCAMP.scr:437
    if ctx:condition("g_hTarget==NULL") then -- GOBLINCAMP.scr:440
        do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:441
    end -- GOBLINCAMP.scr:442
    mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:444
    do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:446
end

script.labels["GoblinDoRangeAttack"] = function(ctx)
    -- GOBLINCAMP.scr:449
    ctx:state().g_bFighting = true -- GOBLINCAMP.scr:452
    ctx:self():rangeAttack("GoblinRangeAttackDone") -- GOBLINCAMP.scr:453
    do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:455
end

script.labels["GoblinTargetOutOfRange"] = function(ctx)
    -- GOBLINCAMP.scr:458
    -- Target moved out of our weapon range.
    -- Go after him!
    ctx:state().g_bCanAttack = ctx:self():canAttack() -- GOBLINCAMP.scr:465
    ctx:state().g_bAttacking = ctx:self():isAttacking() -- GOBLINCAMP.scr:466
    if ctx:condition("g_bAttacking==TRUE") then -- GOBLINCAMP.scr:468
        ctx:wait(0, 0.5, "GoblinOutOfRangeWait") -- GOBLINCAMP.scr:469
    end -- GOBLINCAMP.scr:470
    if ctx:condition("g_bCanAttack==TRUE") then -- GOBLINCAMP.scr:472
        mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:473
    else -- GOBLINCAMP.scr:474
        ctx:wait(0, 0.5, "GoblinOutOfRangeWait") -- GOBLINCAMP.scr:475
    end -- GOBLINCAMP.scr:476
    do return ctx:exit("") end -- GOBLINCAMP.scr:478
end

script.labels["GoblinObstacleRange"] = function(ctx)
    -- GOBLINCAMP.scr:481
    -- AI that have range attacks, sometimes
    -- fire at the target when they hit an
    -- obstacle...
    ctx:state().g_nTemp = ctx:self():canAttack() -- GOBLINCAMP.scr:488
    if ctx:condition("g_nTemp==FALSE") then -- GOBLINCAMP.scr:490
        ctx:state().g_nTemp = ctx:self():isAttacking() -- GOBLINCAMP.scr:491
        if ctx:condition("g_nTemp==FALSE") then -- GOBLINCAMP.scr:492
            mm9.gosub(script, ctx, "GoblinObstacle") -- GOBLINCAMP.scr:493
            do return ctx:exit("") end -- GOBLINCAMP.scr:494
        end -- GOBLINCAMP.scr:495
        do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:497
    end -- GOBLINCAMP.scr:498
    mm9.gosub(script, ctx, "GoblinMaybeRangeAttack") -- GOBLINCAMP.scr:500
    do return ctx:exit("TRUE") end -- GOBLINCAMP.scr:502
end

script.labels["GoblinObstacle"] = function(ctx)
    -- GOBLINCAMP.scr:505
    -- GetRandomInt 0, 100, g_nRandom
    -- if ( g_nRandom > 3 )
    -- Exit FALSE
    -- endif
    -- small pct chance we'll taunt him when we hit an obstacle....
    ctx:self():taunt("GoblinGoGetHim") -- GOBLINCAMP.scr:516
    do return ctx:exit("") end -- GOBLINCAMP.scr:518
end

script.labels["GoblinDeathDone"] = function(ctx)
    -- GOBLINCAMP.scr:523
    ctx:trigger("g_hCampDirector", "GoblinDeath") -- GOBLINCAMP.scr:525
    do return ctx:exit("FALSE") end -- GOBLINCAMP.scr:527
end

script.labels["Init"] = function(ctx)
    -- GOBLINCAMP.scr:530
    ctx:state().g_hCampDirector = ctx:objectOrNil("CampDirector") -- GOBLINCAMP.scr:533
    ctx:state().g_hTarget = ctx:self():target() -- GOBLINCAMP.scr:535
    if ctx:condition("g_hTarget!=NULL") then -- GOBLINCAMP.scr:536
        mm9.gosub(script, ctx, "GoblinGoGetHim") -- GOBLINCAMP.scr:537
    else -- GOBLINCAMP.scr:538
        mm9.gosub(script, ctx, "GoblinFindTarget") -- GOBLINCAMP.scr:539
    end -- GOBLINCAMP.scr:540
    do return ctx:exit("") end -- GOBLINCAMP.scr:542
end

script.labels["Main"] = function(ctx)
    -- GOBLINCAMP.scr:545
    -- This routine is automatically run
    -- at script startup...
    -- Setup our event handlers...
    -- Base callbacks
    ctx:onEvent("OnDamage", "BaseDamage") -- GOBLINCAMP.scr:558
    ctx:onEvent("OnPathClear", "BasePathClear") -- GOBLINCAMP.scr:559
    ctx:onEvent("OnObstacle", "BaseObstacle") -- GOBLINCAMP.scr:560
    -- Goblin script call backs
    ctx:onEvent("OnAlert", "GoblinOnAlert") -- GOBLINCAMP.scr:563
    ctx:onEvent("OnTargetDead", "GoblinTargetDead") -- GOBLINCAMP.scr:564
    ctx:onEvent("OnDamageDone", "GoblinDamageDone") -- GOBLINCAMP.scr:565
    ctx:onEvent("OnAttackReady", "GoblinAttackReady") -- GOBLINCAMP.scr:566
    ctx:onEvent("OnLostTarget", "GoblinLostTarget") -- GOBLINCAMP.scr:567
    ctx:onEvent("OnDeathDone", "GoblinDeathDone") -- GOBLINCAMP.scr:568
    ctx:onEvent("OnTargetOutOfRange", "GoblinTargetOutOfRange") -- GOBLINCAMP.scr:569
    ctx:onEvent("OnStuckDone", "GoblinStuckDone") -- GOBLINCAMP.scr:570
    ctx:state().g_bHasRangeAttack = ctx:self():hasRangeAttack() -- GOBLINCAMP.scr:572
    if ctx:condition("g_bHasRangeAttack == TRUE") then -- GOBLINCAMP.scr:574
        ctx:onEvent("OnObstacle", "GoblinObstacleRange") -- GOBLINCAMP.scr:575
        -- OnFoundPlayer BaseFoundPlayerRange
    end -- GOBLINCAMP.scr:577
    -- See if we already have a target (this would normally happen if
    -- the ai were running another script and then decided to start running
    -- this one...
    ctx:wait(0, 0.1, "Init") -- GOBLINCAMP.scr:585
    do return ctx:exit("") end -- GOBLINCAMP.scr:587
end

return script
