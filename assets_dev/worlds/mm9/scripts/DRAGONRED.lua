-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAGONRED.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 48, path = "aiglobals.inc" }

-- DragonRed.scr
-- Jeff Leggett
-- 09/27/2000
-- Implementation of the Red dragon.
-- The dragon starts out asleep.  It doesn't notice anyone
-- until they do damage.  We then wake up and start
-- attacking.
-- We have 4 attacks:
-- 1.  Fireball attack
-- - This attack is a simple fireball projectile that
-- does radius damage on impact.
-- 2.	FlameThrower attack
-- - This attack sends continuous bursts of fire
-- in the direction that we're pointing...
-- 3.	Wing attack
-- - This does no damage, but can be used to push
-- players away from us...
-- 4.	Hand Attack
-- - We do this instead of a wing attack sometimes.
-- After each attack, if we've attacked the current
-- target long enough, we decide whether we should
-- switch to another target.  Targets that are out
-- of range are ignored.  Targets that we don't have
-- a clear shot at are randomly ignored.  The last
-- target to do damage to us gets a higher priority.
-- This higher priority is proportional to his distance
-- away from us...  (ie: if someone along way off is
-- hitting us, while we have many more targets near us,
-- we have a less chance of switching to that target than
-- if they're close to us...
-- After each attack, we also check to see if there are
-- a lot of targets within our wing attack distance.
-- if so, we'll switch to one of them and do our wing attack...
-- 75% of the time, ignore a target that you don't have a clear shot at...
-- Chance that if the target is close enough, that we'll do a hand attack
-- instead of a wing attack...
-- Array Find Routine variables..
script.labels["DoNothing"] = function(ctx)
    -- DRAGONRED.scr:118
    do return ctx:exit("") end -- DRAGONRED.scr:121
end

script.labels["ClearAttackTimer"] = function(ctx)
    -- DRAGONRED.scr:124
    ctx:command("wait", "ATTACK_WAIT_NBR, 0, DoNothing") -- DRAGONRED.scr:126
    do return ctx:exit("") end -- DRAGONRED.scr:128
end

script.labels["OnLostTarget"] = function(ctx)
    -- DRAGONRED.scr:131
    -- Lost Target, go back to idle...
    ctx:command("set", "g_hTarget, NULL") -- DRAGONRED.scr:136
    ctx:command("target", "NULL") -- DRAGONRED.scr:137
    mm9.gosub(script, ctx, "ClearAttackTimer") -- DRAGONRED.scr:139
    do return ctx:exit("") end -- DRAGONRED.scr:141
end

script.labels["AttackDone"] = function(ctx)
    -- DRAGONRED.scr:144
    ctx:command("set", "bAttacking, FALSE") -- DRAGONRED.scr:147
    ctx:command("target", "g_hTarget, FALSE") -- DRAGONRED.scr:149
    mm9.gosub(script, ctx, "MaybeSwitchTarget") -- DRAGONRED.scr:151
    if ctx:condition("g_hTarget!=NULL") then -- DRAGONRED.scr:153
        mm9.gosub(script, ctx, "SetupAttack") -- DRAGONRED.scr:154
    else -- DRAGONRED.scr:155
        ctx:command("setidle", "") -- DRAGONRED.scr:156
    end -- DRAGONRED.scr:157
    do return ctx:exit("") end -- DRAGONRED.scr:159
end

script.labels["AttackFaceTargetDone"] = function(ctx)
    -- DRAGONRED.scr:162
    if ctx:condition("bAttacking==TRUE") then -- DRAGONRED.scr:165
        ctx:command("target", "g_hTarget, TRUE") -- DRAGONRED.scr:166
    end -- DRAGONRED.scr:167
    do return ctx:exit("") end -- DRAGONRED.scr:169
end

script.labels["GetTargetHeight"] = function(ctx)
    -- DRAGONRED.scr:173
    -- input: g_hTarget
    -- output: targetHeight	(compared to where our feet are)
    ctx:command("set", "targetHeight, 0") -- DRAGONRED.scr:177
    if ctx:condition("g_hTarget==NULL") then -- DRAGONRED.scr:179
        do return ctx:exit("") end -- DRAGONRED.scr:180
    end -- DRAGONRED.scr:181
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- DRAGONRED.scr:183
    ctx:command("sub", "g_posY, dimsY") -- DRAGONRED.scr:184
    ctx:command("getpos", "g_hTarget, g_posX, targetHeight, g_posZ") -- DRAGONRED.scr:186
    ctx:command("sub", "targetHeight, g_posY") -- DRAGONRED.scr:187
    do return ctx:exit("") end -- DRAGONRED.scr:189
end

script.labels["DoBreathAttack"] = function(ctx)
    -- DRAGONRED.scr:192
    -- if the target is above a certain
    -- distance, we'll play the higher
    -- breath attack
    if ctx:condition("g_hTarget!=NULL") then -- DRAGONRED.scr:200
        mm9.gosub(script, ctx, "GetTargetHeight") -- DRAGONRED.scr:202
        if ctx:condition("targetHeight > dimsZ") then -- DRAGONRED.scr:204
            ctx:command("getrandomint", "0,100, g_nRandom") -- DRAGONRED.scr:205
            if ctx:condition("g_nRandom > 60") then -- DRAGONRED.scr:206
                ctx:command("playanim", "rAttack3, AttackDone") -- DRAGONRED.scr:207
            else -- DRAGONRED.scr:208
                ctx:command("playanim", "rAttack1, AttackDone") -- DRAGONRED.scr:209
            end -- DRAGONRED.scr:210
        else -- DRAGONRED.scr:211
            ctx:command("playanim", "rAttack2, AttackDone") -- DRAGONRED.scr:212
        end -- DRAGONRED.scr:213
    else -- DRAGONRED.scr:214
        ctx:command("playanim", "rAttack2, AttackDone") -- DRAGONRED.scr:215
    end -- DRAGONRED.scr:216
    do return ctx:exit("") end -- DRAGONRED.scr:217
end

script.labels["DoWingAttack"] = function(ctx)
    -- DRAGONRED.scr:220
    ctx:command("playanim", "WingAttack, WingAttackDone") -- DRAGONRED.scr:223
    do return ctx:exit("") end -- DRAGONRED.scr:225
end

script.labels["DoFireBoltAttack"] = function(ctx)
    -- DRAGONRED.scr:228
    ctx:command("playanim", "rAttack1, AttackDone") -- DRAGONRED.scr:231
    do return ctx:exit("") end -- DRAGONRED.scr:233
end

script.labels["DoAttack"] = function(ctx)
    -- DRAGONRED.scr:236
    if ctx:condition("g_hTarget==NULL") then -- DRAGONRED.scr:239
        ctx:command("setidle", "") -- DRAGONRED.scr:240
        do return ctx:exit("") end -- DRAGONRED.scr:241
    end -- DRAGONRED.scr:242
    ctx:command("aigetdistance", "g_hTarget, g_nTemp") -- DRAGONRED.scr:244
    ctx:command("faceobject", "g_hTarget, 180, AttackFaceTargetDone") -- DRAGONRED.scr:246
    ctx:command("set", "bAttacking, TRUE") -- DRAGONRED.scr:248
    if ctx:condition("g_nTemp < WING_ATTACK_DIST") then -- DRAGONRED.scr:250
        mm9.gosub(script, ctx, "DoCloseAttack") -- DRAGONRED.scr:251
    else -- DRAGONRED.scr:252
        if ctx:condition("g_nTemp < BREATH_ATTACK_DIST") then -- DRAGONRED.scr:253
            mm9.gosub(script, ctx, "DoBreathAttack") -- DRAGONRED.scr:254
        else -- DRAGONRED.scr:255
            if ctx:condition("g_nTemp < MAX_ATTACK_DIST") then -- DRAGONRED.scr:256
                mm9.gosub(script, ctx, "DoFireBoltAttack") -- DRAGONRED.scr:257
            else -- DRAGONRED.scr:258
                -- Just re-setup our attack...
                ctx:command("setidle", "") -- DRAGONRED.scr:260
                ctx:command("set", "bAttacking, FALSE") -- DRAGONRED.scr:261
                mm9.gosub(script, ctx, "SetupAttack") -- DRAGONRED.scr:262
            end -- DRAGONRED.scr:263
        end -- DRAGONRED.scr:264
    end -- DRAGONRED.scr:265
    do return ctx:exit("") end -- DRAGONRED.scr:267
end

script.labels["WingAttackDone"] = function(ctx)
    -- DRAGONRED.scr:270
    ctx:command("target", "g_hTarget, FALSE") -- DRAGONRED.scr:273
    mm9.gosub(script, ctx, "SetupPostWingAttack") -- DRAGONRED.scr:274
    do return ctx:exit("") end -- DRAGONRED.scr:276
end

script.labels["DoHandAttack"] = function(ctx)
    -- DRAGONRED.scr:280
    ctx:command("playanim", "hAttack1, AttackDone") -- DRAGONRED.scr:283
    do return ctx:exit("") end -- DRAGONRED.scr:285
end

script.labels["DoCloseAttack"] = function(ctx)
    -- DRAGONRED.scr:288
    -- Randomly pick between using hand
    -- attack and wing attack
    if ctx:condition("g_hTarget==NULL") then -- DRAGONRED.scr:294
        mm9.gosub(script, ctx, "SetupAttack") -- DRAGONRED.scr:295
    end -- DRAGONRED.scr:296
    ctx:command("set", "g_nTemp, 0") -- DRAGONRED.scr:298
    ctx:command("aigetdistance", "g_hTarget, currTargetDist") -- DRAGONRED.scr:300
    -- DebugOut currTargetDist
    if ctx:condition("currTargetDist < MAX_HAND_ATTACK_DIST") then -- DRAGONRED.scr:302
        ctx:command("add", "g_nTemp, HAND_ATTACK_CHANCE") -- DRAGONRED.scr:303
    end -- DRAGONRED.scr:304
    mm9.gosub(script, ctx, "GetTargetHeight") -- DRAGONRED.scr:306
    if ctx:condition("targetHeight > 100") then -- DRAGONRED.scr:307
        ctx:command("set", "g_nTemp, 0") -- DRAGONRED.scr:308
    end -- DRAGONRED.scr:309
    ctx:command("getrandomint", "0,100,g_nRandom") -- DRAGONRED.scr:311
    if ctx:condition("g_nRandom < g_nTemp") then -- DRAGONRED.scr:313
        mm9.gosub(script, ctx, "DoHandAttack") -- DRAGONRED.scr:314
        do return ctx:exit("") end -- DRAGONRED.scr:315
    end -- DRAGONRED.scr:316
    ctx:command("getrandomint", "0, 100, g_nRandom") -- DRAGONRED.scr:318
    ctx:command("set", "g_nTemp, 20") -- DRAGONRED.scr:320
    if ctx:condition("currTargetDist < 100") then -- DRAGONRED.scr:322
        ctx:command("set", "g_nTemp, 5") -- DRAGONRED.scr:323
    end -- DRAGONRED.scr:324
    if ctx:condition("g_nRandom < g_nTemp") then -- DRAGONRED.scr:326
        mm9.gosub(script, ctx, "DoBreathAttack") -- DRAGONRED.scr:327
    else -- DRAGONRED.scr:328
        mm9.gosub(script, ctx, "DoWingAttack") -- DRAGONRED.scr:329
    end -- DRAGONRED.scr:330
    do return ctx:exit("") end -- DRAGONRED.scr:332
end

script.labels["TargetDead"] = function(ctx)
    -- DRAGONRED.scr:336
    ctx:command("target", "NULL") -- DRAGONRED.scr:338
    ctx:command("set", "g_hTarget, NULL") -- DRAGONRED.scr:339
    mm9.gosub(script, ctx, "FindTarget") -- DRAGONRED.scr:341
    if ctx:condition("hFoundTarget==NULL") then -- DRAGONRED.scr:343
        do return ctx:exit("") end -- DRAGONRED.scr:344
    end -- DRAGONRED.scr:345
    ctx:command("set", "g_hTarget, hFoundTarget") -- DRAGONRED.scr:347
    mm9.gosub(script, ctx, "ClearAttackTimer") -- DRAGONRED.scr:349
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGONRED.scr:350
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGONRED.scr:351
    do return ctx:exit("") end -- DRAGONRED.scr:353
end

script.labels["SetupAttack"] = function(ctx)
    -- DRAGONRED.scr:356
    ctx:command("getrandomfloat", "MIN_ATTACK_WAIT, MAX_ATTACK_WAIT, random") -- DRAGONRED.scr:359
    ctx:command("ontargetdead", "TargetDead") -- DRAGONRED.scr:361
    ctx:command("wait", "ATTACK_WAIT_NBR, random, DoAttack") -- DRAGONRED.scr:363
    -- See if we want to switch targets
    do return ctx:exit("") end -- DRAGONRED.scr:370
end

script.labels["SetupWingAttack"] = function(ctx)
    -- DRAGONRED.scr:373
    ctx:command("getrandomfloat", "MIN_WING_ATTACK_WAIT, MAX_WING_ATTACK_WAIT, random") -- DRAGONRED.scr:376
    ctx:command("ontargetdead", "TargetDead") -- DRAGONRED.scr:377
    ctx:command("wait", "ATTACK_WAIT_NBR, random, DoCloseAttack") -- DRAGONRED.scr:378
    do return ctx:exit("") end -- DRAGONRED.scr:380
end

script.labels["SetupPostWingAttack"] = function(ctx)
    -- DRAGONRED.scr:383
    ctx:command("ontargetdead", "TargetDead") -- DRAGONRED.scr:386
    mm9.gosub(script, ctx, "DoAttack") -- DRAGONRED.scr:388
    -- GetRandomFloat MIN_POST_WING_ATTACK_WAIT, MAX_POST_WING_ATTACK_WAIT, random
    -- Wait ATTACK_WAIT_NBR, random, DoAttack
    do return ctx:exit("") end -- DRAGONRED.scr:393
end

script.labels["WakingUpDamage"] = function(ctx)
    -- DRAGONRED.scr:396
    -- p0 = hAttacker
    -- p1 = HitPoints
    -- p2 = DamageType
    ctx:getParam(0, "hObject") -- DRAGONRED.scr:403
    if ctx:condition("hWakeUpTarget!=hObject") then -- DRAGONRED.scr:405
        ctx:command("breakobjectlink", "hWakeUpTarget") -- DRAGONRED.scr:406
        ctx:command("createobjectlink", "hObject") -- DRAGONRED.scr:407
    end -- DRAGONRED.scr:408
    do return ctx:exit("TRUE") end -- DRAGONRED.scr:410
end

script.labels["OnDamage"] = function(ctx)
    -- DRAGONRED.scr:413
    -- p1	= hAttacker
    -- p2	= HitPoints
    -- p3  = DamageType
    ctx:getParam(0, "hObject") -- DRAGONRED.scr:420
    if ctx:condition("hLastAttacker!=hObject") then -- DRAGONRED.scr:422
        ctx:command("set", "hLastAttacker, hObject") -- DRAGONRED.scr:423
        ctx:command("createobjectlink", "hLastAttacker") -- DRAGONRED.scr:424
    end -- DRAGONRED.scr:425
    -- See if we want to switch targets..
    -- For now, always switch target...
    if ctx:condition("g_hTarget==NULL") then -- DRAGONRED.scr:430
        ctx:command("set", "g_hTarget, hObject") -- DRAGONRED.scr:431
        mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGONRED.scr:432
        mm9.gosub(script, ctx, "SetupAttack") -- DRAGONRED.scr:433
    else -- DRAGONRED.scr:434
        if ctx:condition("hObject!=g_hTarget") then -- DRAGONRED.scr:435
            -- Hurry up on switching maybe... 20% chance
            ctx:command("getrandomint", "0, 100, g_nRandom") -- DRAGONRED.scr:437
            if ctx:condition("g_nRandom > 80") then -- DRAGONRED.scr:438
                ctx:command("add", "switchHurryTime, 0.5") -- DRAGONRED.scr:439
            end -- DRAGONRED.scr:440
        end -- DRAGONRED.scr:441
    end -- DRAGONRED.scr:442
    do return ctx:exit("TRUE") end -- DRAGONRED.scr:445
end

script.labels["OnFoundTarget"] = function(ctx)
    -- DRAGONRED.scr:449
    ctx:getParam(0, "g_hTarget") -- DRAGONRED.scr:452
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGONRED.scr:454
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGONRED.scr:455
    do return ctx:exit("") end -- DRAGONRED.scr:457
end

script.labels["ArrayFind"] = function(ctx)
    -- DRAGONRED.scr:461
    -- Attempts to find hArrayFind in hTargetArray
    -- returns index in nArrayFindIndex
    -- ( -1 if not found )
    -- input:	hArrayFind
    -- hTargetArray
    -- nTargetsFound
    -- output: nArrayFindIndex
    if ctx:condition("hArrayFind==NULL") then -- DRAGONRED.scr:474
        do return ctx:exit("") end -- DRAGONRED.scr:475
    end -- DRAGONRED.scr:476
    ctx:command("set", "g_nCounter, 0") -- DRAGONRED.scr:478
    ctx:command("set", "nArrayFindIndex, -1") -- DRAGONRED.scr:479
    while ctx:condition("g_nCounter < nTargetsFound") do -- DRAGONRED.scr:481
        ctx:command("arrayget", "hTargetArray, g_nCounter, g_hObject") -- DRAGONRED.scr:482
        if ctx:condition("g_hObject==hArrayFind") then -- DRAGONRED.scr:484
            ctx:command("set", "nArrayFindIndex, g_nCounter") -- DRAGONRED.scr:485
            do return ctx:exit("") end -- DRAGONRED.scr:486
        end -- DRAGONRED.scr:487
        ctx:command("add", "g_nCounter, 1") -- DRAGONRED.scr:489
    end -- DRAGONRED.scr:490
    do return ctx:exit("") end -- DRAGONRED.scr:492
end

script.labels["CheckClearShot"] = function(ctx)
    -- DRAGONRED.scr:495
    -- See if we have a clear shot.  If not,
    -- decide if we should go ahead and use
    -- the target anyway...
    -- input:	hFoundTarget
    -- output: bClearShot
    ctx:command("set", "bClearShot, FALSE") -- DRAGONRED.scr:506
    ctx:command("isclearshot", "hFoundTarget, bClearShot") -- DRAGONRED.scr:508
    if ctx:condition("bClearShot==FALSE") then -- DRAGONRED.scr:510
        -- Randomly decide if we should target them
        -- anyway...
        ctx:command("getrandomint", "0,100,g_nRandom") -- DRAGONRED.scr:513
        if ctx:condition("g_nRandom < NO_CLEAR_SHOT_IGNORE_CHANCE") then -- DRAGONRED.scr:514
            ctx:command("set", "bClearShot, FALSE") -- DRAGONRED.scr:515
            -- DebugOut Using Target WITHOUT clear shot!
        else -- DRAGONRED.scr:517
            -- DebugOut NOT USING TARGET without clear shot
        end -- DRAGONRED.scr:519
    end -- DRAGONRED.scr:520
    do return ctx:exit("") end -- DRAGONRED.scr:522
end

script.labels["FindTarget"] = function(ctx)
    -- DRAGONRED.scr:525
    -- Sets hFoundTarget to NULL if none found
    -- input: none
    -- output: hFoundTarget
    -- DebugOut XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    -- DebugOut FindTarget IN
    -- DebugOut XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ctx:command("set", "hFoundTarget, NULL") -- DRAGONRED.scr:538
    -- Most every time thru here, we
    -- check to see if there are many
    -- targets within our wind distance
    -- If so, we'll target them because
    -- they have the potential to do the
    -- most damage...
    ctx:command("getrandomint", "0, 100, g_nRandom") -- DRAGONRED.scr:549
    ctx:command("set", "nTargetsFound, 0") -- DRAGONRED.scr:550
    ctx:command("set", "g_nTemp, 50") -- DRAGONRED.scr:552
    if ctx:condition("g_hTarget!=hLastAttacker") then -- DRAGONRED.scr:554
        -- If we're not attacking the last attacker, then reduce
        -- chances that we'll only look at the closer guys...
        ctx:command("set", "g_nTemp, 20") -- DRAGONRED.scr:557
    end -- DRAGONRED.scr:558
    if ctx:condition("g_nRandom < 50") then -- DRAGONRED.scr:560
        ctx:command("findtargets", "hTargetArray,MAX_TARGETS,nTargetsFound,WING_ATTACK_DIST,0") -- DRAGONRED.scr:561
    end -- DRAGONRED.scr:562
    if ctx:condition("nTargetsFound==0") then -- DRAGONRED.scr:564
        ctx:command("findtargets", "hTargetArray,MAX_TARGETS,nTargetsFound,0,0") -- DRAGONRED.scr:565
    else -- DRAGONRED.scr:566
        -- DebugOut Found local targets!
    end -- DRAGONRED.scr:568
    if ctx:condition("nTargetsFound==0") then -- DRAGONRED.scr:570
        do return ctx:exit("") end -- DRAGONRED.scr:571
    end -- DRAGONRED.scr:572
    -- Give the last attacker higher
    -- priority....
    ctx:command("set", "hArrayFind, hLastAttacker") -- DRAGONRED.scr:581
    mm9.gosub(script, ctx, "ArrayFind") -- DRAGONRED.scr:582
    if ctx:condition("nArrayFindIndex!=-1") then -- DRAGONRED.scr:584
        -- DebugOut Last attacker is in our target array!
        ctx:command("set", "g_nTemp, nArrayFindIndex") -- DRAGONRED.scr:586
        ctx:command("div", "g_nTemp, nTargetsFound") -- DRAGONRED.scr:587
        ctx:command("mul", "g_nTemp, 100") -- DRAGONRED.scr:588
        ctx:command("add", "g_nTemp, 15") -- DRAGONRED.scr:590
        ctx:command("getrandomint", "0, 100, g_nRandom") -- DRAGONRED.scr:592
        if ctx:condition("g_nRandom > g_nTemp") then -- DRAGONRED.scr:594
            -- Use last attacker...
            ctx:command("set", "hFoundTarget, hLastAttacker") -- DRAGONRED.scr:596
            ctx:command("aigetdistance", "hFoundTarget, g_nTemp") -- DRAGONRED.scr:598
            if ctx:condition("g_nTemp >= BREATH_ATTACK_DIST") then -- DRAGONRED.scr:600
                mm9.gosub(script, ctx, "CheckClearShot") -- DRAGONRED.scr:601
                if ctx:condition("bClearShot==FALSE") then -- DRAGONRED.scr:602
                    ctx:command("set", "hFoundTarget, NULL") -- DRAGONRED.scr:603
                end -- DRAGONRED.scr:604
            end -- DRAGONRED.scr:605
            if ctx:condition("hFoundTarget!=NULL") then -- DRAGONRED.scr:607
                -- DebugOut using LAST ATTACKER
                do return mm9.gotoLabel(script, ctx, "FindTargetDone") end -- DRAGONRED.scr:609
            end -- DRAGONRED.scr:610
        end -- DRAGONRED.scr:611
        -- DebugOut NOT using last attacker!
    else -- DRAGONRED.scr:614
        -- DebugOut Last attacker is NOT in our target array!!
    end -- DRAGONRED.scr:616
    -- Okay, just go thru the list of targets and pick
    -- one that we've got a good shot at...
    ctx:command("set", "g_nCounter, 0") -- DRAGONRED.scr:624
    while ctx:condition("g_nCounter < nTargetsFound") do -- DRAGONRED.scr:627
        ctx:command("arrayget", "hTargetArray, g_nCounter, hFoundTarget") -- DRAGONRED.scr:629
        if ctx:condition("hFoundTarget==g_hTarget") then -- DRAGONRED.scr:631
            -- Don't allow current target to be a potential "new" target...
            ctx:command("set", "hFoundTarget, NULL") -- DRAGONRED.scr:633
            do return mm9.gotoLabel(script, ctx, "FindTargetNext") end -- DRAGONRED.scr:634
        end -- DRAGONRED.scr:635
        -- If we're going to use the fireball
        -- attack, see if we have a clear shot at him
        ctx:command("aigetdistance", "hFoundTarget, g_nTemp") -- DRAGONRED.scr:644
        if ctx:condition("g_nTemp >= BREATH_ATTACK_DIST") then -- DRAGONRED.scr:645
            mm9.gosub(script, ctx, "CheckClearShot") -- DRAGONRED.scr:647
            if ctx:condition("bClearShot==FALSE") then -- DRAGONRED.scr:649
                do return mm9.gotoLabel(script, ctx, "FindTargetNext") end -- DRAGONRED.scr:650
            end -- DRAGONRED.scr:651
        end -- DRAGONRED.scr:652
        -- If they're too far away, don't consider
        -- them a target
        if ctx:condition("g_nTemp > MAX_ATTACK_DIST") then -- DRAGONRED.scr:660
            -- DebugOut TARGET TOO FAR!
            do return mm9.gotoLabel(script, ctx, "FindTargetNext") end -- DRAGONRED.scr:662
        end -- DRAGONRED.scr:663
        if ctx:condition("hFoundTarget!=NULL") then -- DRAGONRED.scr:665
            do return mm9.gotoLabel(script, ctx, "FindTargetDone") end -- DRAGONRED.scr:666
        end -- DRAGONRED.scr:667
    end -- implicit close before DRAGONRED.scr:669
end

script.labels["FindTargetNext"] = function(ctx)
    -- DRAGONRED.scr:669
    ctx:command("add", "g_nCounter, 1") -- DRAGONRED.scr:671
    -- unmatched endwhile at DRAGONRED.scr:673
end

script.labels["FindTargetDone"] = function(ctx)
    -- DRAGONRED.scr:675
    -- DebugOut XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    -- DebugOut FindTarget OUT
    -- DebugOut XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    do return ctx:exit("") end -- DRAGONRED.scr:681
end

script.labels["MaybeSwitchTarget"] = function(ctx)
    -- DRAGONRED.scr:684
    -- Figure out if we want to switch target
    -- or not..
    ctx:command("gettime", "g_nTemp") -- DRAGONRED.scr:691
    -- See if it's too soon to switch targets....
    ctx:command("sub", "g_nTemp, MIN_SAME_TARGET_TIME") -- DRAGONRED.scr:694
    ctx:command("add", "g_nTemp, switchHurryTime") -- DRAGONRED.scr:695
    if ctx:condition("g_nTemp < lastTargetSwitch") then -- DRAGONRED.scr:696
        do return ctx:exit("") end -- DRAGONRED.scr:697
    end -- DRAGONRED.scr:698
    mm9.gosub(script, ctx, "FindTarget") -- DRAGONRED.scr:700
    if ctx:condition("hFoundTarget==NULL") then -- DRAGONRED.scr:702
        do return ctx:exit("") end -- DRAGONRED.scr:703
    end -- DRAGONRED.scr:704
    if ctx:condition("g_hTarget==NULL") then -- DRAGONRED.scr:706
        do return mm9.gotoLabel(script, ctx, "NewTarget") end -- DRAGONRED.scr:707
    end -- DRAGONRED.scr:708
    if ctx:condition("hFoundTarget==g_hTarget") then -- DRAGONRED.scr:710
        do return ctx:exit("") end -- DRAGONRED.scr:711
    end -- DRAGONRED.scr:712
    ctx:command("set", "switchChance, 20") -- DRAGONRED.scr:714
    ctx:command("aigetdistance", "g_hTarget, currTargetDist") -- DRAGONRED.scr:716
    ctx:command("aigetdistance", "hFoundTarget, foundTargetDist") -- DRAGONRED.scr:717
    if ctx:condition("currTargetDist > foundTargetDist") then -- DRAGONRED.scr:719
        ctx:command("set", "switchChance, 80") -- DRAGONRED.scr:720
    end -- DRAGONRED.scr:721
    if ctx:condition("hFoundTarget==hLastAttacker") then -- DRAGONRED.scr:723
        ctx:command("add", "switchChance, 45") -- DRAGONRED.scr:724
    end -- DRAGONRED.scr:725
    ctx:command("gettime", "g_nTemp") -- DRAGONRED.scr:727
    ctx:command("sub", "g_nTemp, MAX_SAME_TARGET_TIME") -- DRAGONRED.scr:729
    ctx:command("add", "g_nTemp, switchHurryTime") -- DRAGONRED.scr:730
    if ctx:condition("g_nTemp > lastTargetSwitch") then -- DRAGONRED.scr:732
        do return mm9.gotoLabel(script, ctx, "NewTarget") end -- DRAGONRED.scr:733
    end -- DRAGONRED.scr:734
    ctx:command("getrandomint", "0, 100, random") -- DRAGONRED.scr:736
    if ctx:condition("random > switchChance") then -- DRAGONRED.scr:738
        do return ctx:exit("") end -- DRAGONRED.scr:739
    end -- DRAGONRED.scr:740
end

script.labels["NewTarget"] = function(ctx)
    -- DRAGONRED.scr:743
    ctx:command("set", "g_hTarget, hFoundTarget") -- DRAGONRED.scr:746
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGONRED.scr:748
    do return ctx:exit("") end -- DRAGONRED.scr:750
end

script.labels["SetupNewTarget"] = function(ctx)
    -- DRAGONRED.scr:753
    ctx:command("gettime", "lastTargetSwitch") -- DRAGONRED.scr:756
    ctx:command("set", "switchHurryTime, 0") -- DRAGONRED.scr:757
    ctx:command("target", "g_hTarget, FOLLOW_TARGET") -- DRAGONRED.scr:758
    do return ctx:exit("") end -- DRAGONRED.scr:760
end

script.labels["DragonAwake"] = function(ctx)
    -- DRAGONRED.scr:763
    -- Now we're awake, go get him...
    if ctx:condition("hWakeUpTarget!=NULL") then -- DRAGONRED.scr:768
        ctx:command("set", "g_hTarget, hWakeUpTarget") -- DRAGONRED.scr:769
    end -- DRAGONRED.scr:770
    ctx:command("ondamage", "OnDamage") -- DRAGONRED.scr:772
    ctx:command("onlosttarget", "OnLostTarget") -- DRAGONRED.scr:773
    ctx:command("onfoundtarget", "OnFoundTarget, MAX_ATTACK_DIST") -- DRAGONRED.scr:774
    -- jsl--> I think we just want to find a target normal, ie: doesn't HAVE to
    -- be the guy that just shot us...
    ctx:command("set", "g_hTarget, NULL") -- DRAGONRED.scr:780
    if ctx:condition("g_hTarget==NULL") then -- DRAGONRED.scr:782
        -- Try to find one...
        mm9.gosub(script, ctx, "FindTarget") -- DRAGONRED.scr:785
        if ctx:condition("hFoundTarget==NULL") then -- DRAGONRED.scr:786
            ctx:command("setidle", "") -- DRAGONRED.scr:787
            do return ctx:exit("") end -- DRAGONRED.scr:788
        end -- DRAGONRED.scr:789
        ctx:command("set", "g_hTarget, hFoundTarget") -- DRAGONRED.scr:791
    end -- DRAGONRED.scr:792
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGONRED.scr:794
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGONRED.scr:795
    do return ctx:exit("") end -- DRAGONRED.scr:797
end

script.labels["DamageWakeUp"] = function(ctx)
    -- DRAGONRED.scr:800
    ctx:getParam(0, "hWakeUpTarget") -- DRAGONRED.scr:802
    if ctx:condition("hWakeUpTarget!=0") then -- DRAGONRED.scr:804
        ctx:command("createobjectlink", "hWakeUpTarget") -- DRAGONRED.scr:805
    end -- DRAGONRED.scr:806
    mm9.gosub(script, ctx, "WakeUp") -- DRAGONRED.scr:808
    do return ctx:exit("") end -- DRAGONRED.scr:810
end

script.labels["WakeUpTrigger"] = function(ctx)
    -- DRAGONRED.scr:813
    ctx:getParam(0, "hWakeUpTarget") -- DRAGONRED.scr:815
    if ctx:condition("hWakeUpTarget!=0") then -- DRAGONRED.scr:817
        ctx:command("createobjectlink", "hWakeUpTarget") -- DRAGONRED.scr:818
    end -- DRAGONRED.scr:819
    mm9.gosub(script, ctx, "WakeUp") -- DRAGONRED.scr:821
    do return ctx:exit("") end -- DRAGONRED.scr:823
end

script.labels["WakeUp"] = function(ctx)
    -- DRAGONRED.scr:826
    -- Wake up and go get 'em boy!
    ctx:command("onfoundplayer", "") -- DRAGONRED.scr:832
    ctx:command("onattackready", "") -- DRAGONRED.scr:833
    ctx:command("ondamage", "WakingUpDamage") -- DRAGONRED.scr:834
    ctx:command("playanim", "WakeUp, DragonAwake") -- DRAGONRED.scr:836
    do return ctx:exit("TRUE") end -- DRAGONRED.scr:838
end

script.labels["SetupSleeping"] = function(ctx)
    -- DRAGONRED.scr:841
    -- Setup the dragon as asleep....
    -- Loop our sleeping animation
    ctx:command("loopanim", "Sleep,0") -- DRAGONRED.scr:848
    -- When we find the player, we'll need to wake up...
    ctx:command("ondamage", "DamageWakeUp") -- DRAGONRED.scr:851
    do return ctx:exit("") end -- DRAGONRED.scr:853
end

script.labels["OnCongestion"] = function(ctx)
    -- DRAGONRED.scr:856
    -- Don't do anything here...
    do return ctx:exit("FALSE") end -- DRAGONRED.scr:862
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- DRAGONRED.scr:865
    ctx:getParam(0, "hObject") -- DRAGONRED.scr:868
    if ctx:condition("hObject==hWakeUpTarget") then -- DRAGONRED.scr:870
        ctx:command("set", "hWakeUpTarget, NULL") -- DRAGONRED.scr:871
    end -- DRAGONRED.scr:872
    if ctx:condition("hObject==hLastAttacker") then -- DRAGONRED.scr:874
        ctx:command("set", "hLastAttacker, NULL") -- DRAGONRED.scr:875
    end -- DRAGONRED.scr:876
    if ctx:condition("hObject==g_hTarget") then -- DRAGONRED.scr:878
        ctx:command("target", "NULL") -- DRAGONRED.scr:879
        ctx:command("set", "g_hTarget, NULL") -- DRAGONRED.scr:880
    end -- DRAGONRED.scr:881
    do return ctx:exit("") end -- DRAGONRED.scr:883
end

script.labels["OnTest"] = function(ctx)
    -- DRAGONRED.scr:886
    ctx:command("playanim", "rAttack2, AttackDone") -- DRAGONRED.scr:889
    do return ctx:exit("") end -- DRAGONRED.scr:892
end

script.labels["TargetTooFar"] = function(ctx)
    -- DRAGONRED.scr:895
    ctx:command("target", "NULL") -- DRAGONRED.scr:898
    ctx:command("set", "g_hTarget, NULL") -- DRAGONRED.scr:899
    mm9.gosub(script, ctx, "ClearAttackTimer") -- DRAGONRED.scr:900
    ctx:command("setidle", "") -- DRAGONRED.scr:901
    ctx:command("ontargetbeyonddist", "MAX_ATTACK_DIST, TargetTooFar") -- DRAGONRED.scr:902
    do return ctx:exit("") end -- DRAGONRED.scr:904
end

script.labels["OnWinceDone"] = function(ctx)
    -- DRAGONRED.scr:907
    -- Called when the Dragon's wince animation
    -- is finished...
    -- Just setup our next attack...
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGONRED.scr:915
    do return ctx:exit("TRUE") end -- DRAGONRED.scr:917
end

script.labels["Main"] = function(ctx)
    -- DRAGONRED.scr:920
    -- Parameters:
    -- p0 ==> bIsSleeping
    -- TraceOn
    ctx:getParam(0, "g_nTemp") -- DRAGONRED.scr:930
    ctx:command("set", "g_nTemp, TRUE") -- DRAGONRED.scr:932
    if ctx:condition("g_nTemp!=FALSE") then -- DRAGONRED.scr:934
        mm9.gosub(script, ctx, "SetupSleeping") -- DRAGONRED.scr:935
    end -- DRAGONRED.scr:936
    ctx:command("getmyhandle", "g_hMyObject") -- DRAGONRED.scr:938
    ctx:command("getstat", "g_hMyObject, VisibleRange, g_nTemp") -- DRAGONRED.scr:939
    if ctx:condition("g_nTemp > MAX_ATTACK_DIST") then -- DRAGONRED.scr:941
        -- Don't go less than our default...
        ctx:command("set", "MAX_ATTACK_DIST, g_nTemp") -- DRAGONRED.scr:943
    end -- DRAGONRED.scr:944
    ctx:command("oncongestion", "OnCongestion") -- DRAGONRED.scr:946
    ctx:command("onobjectlinkbroken", "OnObjectLinkBroken") -- DRAGONRED.scr:947
    ctx:command("ontargetwithindist", "WING_ATTACK_DIST, SetupWingAttack") -- DRAGONRED.scr:948
    ctx:command("ontargetbeyonddist", "MAX_ATTACK_DIST, TargetTooFar") -- DRAGONRED.scr:949
    ctx:addTrigger("WakeUp", "WakeUpTrigger") -- DRAGONRED.scr:952
    ctx:addTrigger("Test", "OnTest") -- DRAGONRED.scr:953
    ctx:addTrigger("DragonWinceDone", "OnWinceDone") -- DRAGONRED.scr:954
    ctx:command("getdims", "g_hMyObject, dimsX, dimsY, dimsZ") -- DRAGONRED.scr:957
    do return ctx:exit("") end -- DRAGONRED.scr:960
end

return script
