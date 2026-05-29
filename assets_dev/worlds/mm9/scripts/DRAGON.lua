-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAGON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 47, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 48, path = "flags.inc" }

-- Dragon.scr
-- Jeff Leggett
-- 11/14/2001
-- Implementation of the Dragon King
-- Optionally, the dragon can start out hidden.  When
-- Triggered, he will fly in from above and land.
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
script.labels["ClearAttackTimer"] = function(ctx)
    -- DRAGON.scr:129
    ctx:wait("ATTACK_WAIT_NBR", 0, "DoNothing") -- DRAGON.scr:131
    do return ctx:exit("") end -- DRAGON.scr:133
end

script.labels["OnLostTarget"] = function(ctx)
    -- DRAGON.scr:136
    -- Lost Target, go back to idle...
    ctx:state().g_hTarget = nil -- DRAGON.scr:141
    ctx:self():setTarget(nil) -- DRAGON.scr:142
    mm9.gosub(script, ctx, "ClearAttackTimer") -- DRAGON.scr:144
    do return ctx:exit("") end -- DRAGON.scr:146
end

script.labels["AttackDone"] = function(ctx)
    -- DRAGON.scr:149
    ctx:state().bAttacking = false -- DRAGON.scr:152
    ctx:self():setTarget(ctx:object("g_hTarget")) -- DRAGON.scr:154
    mm9.gosub(script, ctx, "MaybeSwitchTarget") -- DRAGON.scr:156
    if ctx:condition("g_hTarget!=NULL") then -- DRAGON.scr:158
        mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:159
    else -- DRAGON.scr:160
        ctx:self():setIdle() -- DRAGON.scr:161
    end -- DRAGON.scr:162
    do return ctx:exit("") end -- DRAGON.scr:164
end

script.labels["AttackFaceTargetDone"] = function(ctx)
    -- DRAGON.scr:167
    if ctx:condition("bAttacking==TRUE") then -- DRAGON.scr:170
        ctx:self():setTarget(ctx:object("g_hTarget")) -- DRAGON.scr:171
    end -- DRAGON.scr:172
    do return ctx:exit("") end -- DRAGON.scr:174
end

script.labels["GetTargetHeight"] = function(ctx)
    -- DRAGON.scr:178
    -- input: g_hTarget
    -- output: targetHeight	(compared to where our feet are)
    ctx:state().targetHeight = 0 -- DRAGON.scr:182
    if ctx:condition("g_hTarget==NULL") then -- DRAGON.scr:184
        do return ctx:exit("") end -- DRAGON.scr:185
    end -- DRAGON.scr:186
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- DRAGON.scr:188
    ctx:sub("g_posY", "dimsY") -- DRAGON.scr:189
    ctx:state().g_posX, ctx:state().targetHeight, ctx:state().g_posZ = ctx:object("g_hTarget"):pos() -- DRAGON.scr:191
    ctx:sub("targetHeight", "g_posY") -- DRAGON.scr:192
    do return ctx:exit("") end -- DRAGON.scr:194
end

script.labels["DoBreathAttack"] = function(ctx)
    -- DRAGON.scr:197
    -- if the target is above a certain
    -- distance, we'll play the higher
    -- breath attack
    if ctx:condition("g_hTarget!=NULL") then -- DRAGON.scr:205
        mm9.gosub(script, ctx, "GetTargetHeight") -- DRAGON.scr:207
        if ctx:condition("targetHeight > dimsZ") then -- DRAGON.scr:209
            ctx:self():playAnimation("rAttack1", "AttackDone") -- DRAGON.scr:210
        else -- DRAGON.scr:211
            ctx:self():playAnimation("rAttack3", "AttackDone") -- DRAGON.scr:212
        end -- DRAGON.scr:213
    else -- DRAGON.scr:214
        ctx:self():playAnimation("rAttack3", "AttackDone") -- DRAGON.scr:215
    end -- DRAGON.scr:216
    do return ctx:exit("") end -- DRAGON.scr:218
end

script.labels["DoWingAttack"] = function(ctx)
    -- DRAGON.scr:221
    ctx:self():playAnimation("WingAttack", "WingAttackDone") -- DRAGON.scr:224
    do return ctx:exit("") end -- DRAGON.scr:226
end

script.labels["DoFireBoltAttack"] = function(ctx)
    -- DRAGON.scr:229
    ctx:self():playAnimation("rAttack1", "AttackDone") -- DRAGON.scr:232
    do return ctx:exit("") end -- DRAGON.scr:234
end

script.labels["CantAttackRightNow"] = function(ctx)
    -- DRAGON.scr:237
    ctx:state().bAttacking = false -- DRAGON.scr:239
    -- CPRINT Dragon can't attack yet!!
    ctx:wait("ATTACK_WAIT_NBR", 0.2, "DoAttack") -- DRAGON.scr:242
    do return ctx:exit("") end -- DRAGON.scr:243
end

script.labels["GetTargetDir"] = function(ctx)
    -- DRAGON.scr:246
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- DRAGON.scr:249
    ctx:state().g_targetDirX, ctx:state().g_targetdirY, ctx:state().g_targetDirZ = ctx:object("g_hTarget"):pos() -- DRAGON.scr:250
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:vecSub("g_targetDirX", "g_targetDirY", "g_targetDirZ", "g_posX", "g_posY", "g_posZ") -- DRAGON.scr:252
    ctx:state().g_targetDirX, ctx:state().g_targetDirY, ctx:state().g_targetDirZ = ctx:vecNorm("g_targetDirX", "g_targetDirY", "g_targetDirZ") -- DRAGON.scr:253
    do return ctx:exit("") end -- DRAGON.scr:255
end

script.labels["DoAttack"] = function(ctx)
    -- DRAGON.scr:259
    if ctx:condition("g_hTarget==NULL") then -- DRAGON.scr:262
        ctx:self():setIdle() -- DRAGON.scr:263
        do return ctx:exit("") end -- DRAGON.scr:264
    end -- DRAGON.scr:265
    ctx:state().g_nTemp = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- DRAGON.scr:267
    ctx:self():faceObject(ctx:object("g_hTarget"), 180, "AttackFaceTargetDone") -- DRAGON.scr:269
    ctx:state().bAttacking = true -- DRAGON.scr:271
    if ctx:condition("g_nTemp < WING_ATTACK_DIST") then -- DRAGON.scr:273
        mm9.gosub(script, ctx, "DoCloseAttack") -- DRAGON.scr:274
    else -- DRAGON.scr:275
        ctx:state().g_bTemp = ctx:self():canRangeAttack() -- DRAGON.scr:276
        if ctx:condition("g_bTemp==FALSE") then -- DRAGON.scr:277
            do return mm9.gotoLabel(script, ctx, "CantAttackRightNow") end -- DRAGON.scr:278
        end -- DRAGON.scr:279
        -- g_sTemp = CurrTargetDist= + g_nTemp
        -- Cprint g_sTemp
        if ctx:condition("g_nTemp < BREATH_ATTACK_DIST") then -- DRAGON.scr:284
            mm9.gosub(script, ctx, "DoBreathAttack") -- DRAGON.scr:285
        else -- DRAGON.scr:286
            if ctx:condition("g_nTemp < MAX_ATTACK_DIST") then -- DRAGON.scr:287
                mm9.gosub(script, ctx, "DoFireBoltAttack") -- DRAGON.scr:288
            else -- DRAGON.scr:289
                -- Just re-setup our attack...
                ctx:self():setIdle() -- DRAGON.scr:291
                ctx:state().bAttacking = false -- DRAGON.scr:292
                mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:293
            end -- DRAGON.scr:294
        end -- DRAGON.scr:295
    end -- DRAGON.scr:296
    do return ctx:exit("") end -- DRAGON.scr:298
end

script.labels["WingAttackDone"] = function(ctx)
    -- DRAGON.scr:301
    ctx:self():setTarget(ctx:object("g_hTarget")) -- DRAGON.scr:304
    mm9.gosub(script, ctx, "SetupPostWingAttack") -- DRAGON.scr:305
    do return ctx:exit("") end -- DRAGON.scr:307
end

script.labels["DoHandAttack"] = function(ctx)
    -- DRAGON.scr:311
    ctx:self():playAnimation("hAttack1", "AttackDone") -- DRAGON.scr:314
    do return ctx:exit("") end -- DRAGON.scr:316
end

script.labels["DoCloseAttack"] = function(ctx)
    -- DRAGON.scr:319
    -- Randomly pick between using hand
    -- attack and wing attack
    if ctx:condition("g_hTarget==NULL") then -- DRAGON.scr:325
        mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:326
    end -- DRAGON.scr:327
    ctx:state().g_nTemp = 0 -- DRAGON.scr:329
    ctx:state().currTargetDist = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- DRAGON.scr:331
    if ctx:condition("currTargetDist < MAX_HAND_ATTACK_DIST") then -- DRAGON.scr:333
        ctx:add("g_nTemp", "HAND_ATTACK_CHANCE") -- DRAGON.scr:334
    end -- DRAGON.scr:335
    mm9.gosub(script, ctx, "GetTargetHeight") -- DRAGON.scr:337
    if ctx:condition("targetHeight > 100") then -- DRAGON.scr:338
        ctx:state().g_nTemp = 0 -- DRAGON.scr:339
    end -- DRAGON.scr:340
    ctx:randomInt(0, 100, "g_nRandom") -- DRAGON.scr:342
    -- jsl-->Don't have a hand attack just yet....
    -- if ( g_nRandom < g_nTemp )
    -- CanAttack g_bTemp
    -- if ( g_bTemp==FALSE )
    -- gosub DoHandAttack
    -- Exit
    -- endif
    -- endif
    ctx:randomInt(0, 100, "g_nRandom") -- DRAGON.scr:355
    ctx:set("g_nTemp", "WING_ATTACK_CHANCE") -- DRAGON.scr:357
    -- if ( currTargetDist < 100 )
    -- Set g_nTemp, 5
    -- endif
    -- TEST ->Force it to do breath attack...
    if ctx:condition("g_nRandom > g_nTemp") then -- DRAGON.scr:364
        ctx:state().g_bTemp = ctx:self():canAttack() -- DRAGON.scr:365
        if ctx:condition("g_bTemp==FALSE") then -- DRAGON.scr:366
            do return mm9.gotoLabel(script, ctx, "CantAttackRightNow") end -- DRAGON.scr:367
        end -- DRAGON.scr:368
        mm9.gosub(script, ctx, "DoBreathAttack") -- DRAGON.scr:369
        do return ctx:exit("") end -- DRAGON.scr:370
    else -- DRAGON.scr:371
        ctx:state().g_bTemp = ctx:self():canAttack() -- DRAGON.scr:372
        if ctx:condition("g_bTemp==FALSE") then -- DRAGON.scr:373
            do return mm9.gotoLabel(script, ctx, "CantAttackRightNow") end -- DRAGON.scr:374
        end -- DRAGON.scr:375
        mm9.gosub(script, ctx, "DoWingAttack") -- DRAGON.scr:376
        do return ctx:exit("") end -- DRAGON.scr:377
    end -- DRAGON.scr:378
    do return ctx:exit("") end -- DRAGON.scr:380
end

script.labels["TargetDead"] = function(ctx)
    -- DRAGON.scr:384
    ctx:self():setTarget(nil) -- DRAGON.scr:386
    ctx:state().g_hTarget = nil -- DRAGON.scr:387
    mm9.gosub(script, ctx, "FindTarget") -- DRAGON.scr:389
    if ctx:condition("hFoundTarget==NULL") then -- DRAGON.scr:391
        do return ctx:exit("") end -- DRAGON.scr:392
    end -- DRAGON.scr:393
    ctx:set("g_hTarget", "hFoundTarget") -- DRAGON.scr:395
    mm9.gosub(script, ctx, "ClearAttackTimer") -- DRAGON.scr:397
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGON.scr:398
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:399
    do return ctx:exit("") end -- DRAGON.scr:401
end

script.labels["SetupAttack"] = function(ctx)
    -- DRAGON.scr:404
    ctx:randomFloat("MIN_ATTACK_WAIT", "MAX_ATTACK_WAIT", "random") -- DRAGON.scr:407
    ctx:onEvent("OnTargetDead", "TargetDead") -- DRAGON.scr:409
    ctx:wait("ATTACK_WAIT_NBR", "random", "DoAttack") -- DRAGON.scr:411
    -- See if we want to switch targets
    do return ctx:exit("") end -- DRAGON.scr:418
end

script.labels["TargetWithinWindDist"] = function(ctx)
    -- DRAGON.scr:421
    -- gosub SetupWingAttack
    do return ctx:exit("") end -- DRAGON.scr:426
end

script.labels["SetupWingAttack"] = function(ctx)
    -- DRAGON.scr:429
    ctx:randomFloat("MIN_WING_ATTACK_WAIT", "MAX_WING_ATTACK_WAIT", "random") -- DRAGON.scr:432
    ctx:onEvent("OnTargetDead", "TargetDead") -- DRAGON.scr:433
    ctx:wait("ATTACK_WAIT_NBR", "random", "DoCloseAttack") -- DRAGON.scr:434
    do return ctx:exit("") end -- DRAGON.scr:436
end

script.labels["SetupPostWingAttack"] = function(ctx)
    -- DRAGON.scr:439
    ctx:onEvent("OnTargetDead", "TargetDead") -- DRAGON.scr:442
    mm9.gosub(script, ctx, "DoAttack") -- DRAGON.scr:444
    -- GetRandomFloat MIN_POST_WING_ATTACK_WAIT, MAX_POST_WING_ATTACK_WAIT, random
    -- Wait ATTACK_WAIT_NBR, random, DoAttack
    do return ctx:exit("") end -- DRAGON.scr:449
end

script.labels["WakingUpDamage"] = function(ctx)
    -- DRAGON.scr:452
    -- p0 = hAttacker
    -- p1 = HitPoints
    -- p2 = DamageType
    ctx:getParam(0, "hObject") -- DRAGON.scr:459
    if ctx:condition("hWakeUpTarget!=hObject") then -- DRAGON.scr:461
        ctx:self():unlink(ctx:object("hWakeUpTarget")) -- DRAGON.scr:462
        ctx:self():link(ctx:object("hObject")) -- DRAGON.scr:463
    end -- DRAGON.scr:464
    do return ctx:exit("TRUE") end -- DRAGON.scr:466
end

script.labels["OnDamage"] = function(ctx)
    -- DRAGON.scr:469
    -- p1	= hAttacker
    -- p2	= HitPoints
    -- p3  = DamageType
    ctx:getParam(0, "hObject") -- DRAGON.scr:476
    if ctx:condition("hLastAttacker!=hObject") then -- DRAGON.scr:478
        ctx:set("hLastAttacker", "hObject") -- DRAGON.scr:479
        ctx:self():link(ctx:object("hLastAttacker")) -- DRAGON.scr:480
    end -- DRAGON.scr:481
    -- See if we want to switch targets..
    -- For now, always switch target...
    if ctx:condition("g_hTarget==NULL") then -- DRAGON.scr:486
        ctx:set("g_hTarget", "hObject") -- DRAGON.scr:487
        mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGON.scr:488
        mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:489
    else -- DRAGON.scr:490
        if ctx:condition("hObject!=g_hTarget") then -- DRAGON.scr:491
            -- Hurry up on switching maybe... 20% chance
            ctx:randomInt(0, 100, "g_nRandom") -- DRAGON.scr:493
            if ctx:condition("g_nRandom > 80") then -- DRAGON.scr:494
                ctx:add("switchHurryTime", 0.5) -- DRAGON.scr:495
            end -- DRAGON.scr:496
        end -- DRAGON.scr:497
    end -- DRAGON.scr:498
    do return ctx:exit("TRUE") end -- DRAGON.scr:501
end

script.labels["OnFoundTarget"] = function(ctx)
    -- DRAGON.scr:505
    ctx:getParam(0, "g_hTarget") -- DRAGON.scr:508
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGON.scr:510
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:511
    do return ctx:exit("") end -- DRAGON.scr:513
end

script.labels["ArrayFind"] = function(ctx)
    -- DRAGON.scr:517
    -- Attempts to find hArrayFind in hTargetArray
    -- returns index in nArrayFindIndex
    -- ( -1 if not found )
    -- input:	hArrayFind
    -- hTargetArray
    -- nTargetsFound
    -- output: nArrayFindIndex
    if ctx:condition("hArrayFind==NULL") then -- DRAGON.scr:530
        do return ctx:exit("") end -- DRAGON.scr:531
    end -- DRAGON.scr:532
    ctx:state().g_nCounter = 0 -- DRAGON.scr:534
    ctx:state().nArrayFindIndex = -1 -- DRAGON.scr:535
    while ctx:condition("g_nCounter < nTargetsFound") do -- DRAGON.scr:537
        ctx:arrayGet("hTargetArray", "g_nCounter", "g_hObject") -- DRAGON.scr:538
        if ctx:condition("g_hObject==hArrayFind") then -- DRAGON.scr:540
            ctx:set("nArrayFindIndex", "g_nCounter") -- DRAGON.scr:541
            do return ctx:exit("") end -- DRAGON.scr:542
        end -- DRAGON.scr:543
        ctx:state().g_nCounter = (tonumber(ctx:state().g_nCounter) or 0) + 1 -- DRAGON.scr:545
    end -- DRAGON.scr:546
    do return ctx:exit("") end -- DRAGON.scr:548
end

script.labels["CheckClearShot"] = function(ctx)
    -- DRAGON.scr:551
    -- See if we have a clear shot.  If not,
    -- decide if we should go ahead and use
    -- the target anyway...
    -- input:	hFoundTarget
    -- output: bClearShot
    ctx:state().bClearShot = false -- DRAGON.scr:562
    ctx:state().bClearShot = ctx:self():isClearShot(ctx:object("hFoundTarget")) -- DRAGON.scr:564
    if ctx:condition("bClearShot==FALSE") then -- DRAGON.scr:566
        -- Randomly decide if we should target them
        -- anyway...
        ctx:randomInt(0, 100, "g_nRandom") -- DRAGON.scr:569
        if ctx:condition("g_nRandom < NO_CLEAR_SHOT_IGNORE_CHANCE") then -- DRAGON.scr:570
            ctx:state().bClearShot = false -- DRAGON.scr:571
            -- DebugOut Using Target WITHOUT clear shot!
        else -- DRAGON.scr:573
            -- DebugOut NOT USING TARGET without clear shot
        end -- DRAGON.scr:575
    end -- DRAGON.scr:576
    do return ctx:exit("") end -- DRAGON.scr:578
end

script.labels["FindTarget"] = function(ctx)
    -- DRAGON.scr:581
    -- Sets hFoundTarget to NULL if none found
    -- input: none
    -- output: hFoundTarget
    -- DebugOut XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    -- DebugOut FindTarget IN
    -- DebugOut XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ctx:state().hFoundTarget = nil -- DRAGON.scr:594
    -- Most every time thru here, we
    -- check to see if there are many
    -- targets within our wind distance
    -- If so, we'll target them because
    -- they have the potential to do the
    -- most damage...
    ctx:randomInt(0, 100, "g_nRandom") -- DRAGON.scr:605
    ctx:state().nTargetsFound = 0 -- DRAGON.scr:606
    ctx:state().g_nTemp = 50 -- DRAGON.scr:608
    if ctx:condition("g_hTarget!=hLastAttacker") then -- DRAGON.scr:610
        -- If we're not attacking the last attacker, then reduce
        -- chances that we'll only look at the closer guys...
        ctx:state().g_nTemp = 20 -- DRAGON.scr:613
    end -- DRAGON.scr:614
    if ctx:condition("g_nRandom < 50") then -- DRAGON.scr:616
        ctx:self():findTargets("hTargetArray", "MAX_TARGETS", "nTargetsFound", "WING_ATTACK_DIST", 0) -- DRAGON.scr:617
    end -- DRAGON.scr:618
    if ctx:condition("nTargetsFound==0") then -- DRAGON.scr:620
        ctx:self():findTargets("hTargetArray", "MAX_TARGETS", "nTargetsFound", 0, 0) -- DRAGON.scr:621
    else -- DRAGON.scr:622
        -- DebugOut Found local targets!
    end -- DRAGON.scr:624
    if ctx:condition("nTargetsFound==0") then -- DRAGON.scr:626
        do return ctx:exit("") end -- DRAGON.scr:627
    end -- DRAGON.scr:628
    -- Give the last attacker higher
    -- priority....
    ctx:set("hArrayFind", "hLastAttacker") -- DRAGON.scr:637
    mm9.gosub(script, ctx, "ArrayFind") -- DRAGON.scr:638
    if ctx:condition("nArrayFindIndex!=-1") then -- DRAGON.scr:640
        -- DebugOut Last attacker is in our target array!
        ctx:set("g_nTemp", "nArrayFindIndex") -- DRAGON.scr:642
        ctx:div("g_nTemp", "nTargetsFound") -- DRAGON.scr:643
        ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) * 100 -- DRAGON.scr:644
        ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) + 15 -- DRAGON.scr:646
        ctx:randomInt(0, 100, "g_nRandom") -- DRAGON.scr:648
        if ctx:condition("g_nRandom > g_nTemp") then -- DRAGON.scr:650
            -- Use last attacker...
            ctx:set("hFoundTarget", "hLastAttacker") -- DRAGON.scr:652
            ctx:state().g_nTemp = ctx:self():aiDistanceTo(ctx:object("hFoundTarget")) -- DRAGON.scr:654
            if ctx:condition("g_nTemp >= BREATH_ATTACK_DIST") then -- DRAGON.scr:656
                mm9.gosub(script, ctx, "CheckClearShot") -- DRAGON.scr:657
                if ctx:condition("bClearShot==FALSE") then -- DRAGON.scr:658
                    ctx:state().hFoundTarget = nil -- DRAGON.scr:659
                end -- DRAGON.scr:660
            end -- DRAGON.scr:661
            if ctx:condition("hFoundTarget!=NULL") then -- DRAGON.scr:663
                -- DebugOut using LAST ATTACKER
                do return mm9.gotoLabel(script, ctx, "FindTargetDone") end -- DRAGON.scr:665
            end -- DRAGON.scr:666
        end -- DRAGON.scr:667
        -- DebugOut NOT using last attacker!
    else -- DRAGON.scr:670
        -- DebugOut Last attacker is NOT in our target array!!
    end -- DRAGON.scr:672
    -- Okay, just go thru the list of targets and pick
    -- one that we've got a good shot at...
    ctx:state().g_nCounter = 0 -- DRAGON.scr:680
    while ctx:condition("g_nCounter < nTargetsFound") do -- DRAGON.scr:683
        ctx:arrayGet("hTargetArray", "g_nCounter", "hFoundTarget") -- DRAGON.scr:685
        if ctx:condition("hFoundTarget==g_hTarget") then -- DRAGON.scr:687
            -- Don't allow current target to be a potential "new" target...
            ctx:state().hFoundTarget = nil -- DRAGON.scr:689
            do return mm9.gotoLabel(script, ctx, "FindTargetNext") end -- DRAGON.scr:690
        end -- DRAGON.scr:691
        -- If we're going to use the fireball
        -- attack, see if we have a clear shot at him
        ctx:state().g_nTemp = ctx:self():aiDistanceTo(ctx:object("hFoundTarget")) -- DRAGON.scr:700
        if ctx:condition("g_nTemp >= BREATH_ATTACK_DIST") then -- DRAGON.scr:701
            mm9.gosub(script, ctx, "CheckClearShot") -- DRAGON.scr:703
            if ctx:condition("bClearShot==FALSE") then -- DRAGON.scr:705
                do return mm9.gotoLabel(script, ctx, "FindTargetNext") end -- DRAGON.scr:706
            end -- DRAGON.scr:707
        end -- DRAGON.scr:708
        -- If they're too far away, don't consider
        -- them a target
        if ctx:condition("g_nTemp > MAX_ATTACK_DIST") then -- DRAGON.scr:716
            -- DebugOut TARGET TOO FAR!
            do return mm9.gotoLabel(script, ctx, "FindTargetNext") end -- DRAGON.scr:718
        end -- DRAGON.scr:719
        if ctx:condition("hFoundTarget!=NULL") then -- DRAGON.scr:721
            do return mm9.gotoLabel(script, ctx, "FindTargetDone") end -- DRAGON.scr:722
        end -- DRAGON.scr:723
    end -- implicit close before DRAGON.scr:725
end

script.labels["FindTargetNext"] = function(ctx)
    -- DRAGON.scr:725
    ctx:state().g_nCounter = (tonumber(ctx:state().g_nCounter) or 0) + 1 -- DRAGON.scr:727
    -- unmatched endwhile at DRAGON.scr:729
end

script.labels["FindTargetDone"] = function(ctx)
    -- DRAGON.scr:731
    -- DebugOut XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    -- DebugOut FindTarget OUT
    -- DebugOut XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    do return ctx:exit("") end -- DRAGON.scr:737
end

script.labels["MaybeSwitchTarget"] = function(ctx)
    -- DRAGON.scr:740
    -- Figure out if we want to switch target
    -- or not..
    ctx:getTime("g_nTemp") -- DRAGON.scr:747
    -- See if it's too soon to switch targets....
    ctx:sub("g_nTemp", "MIN_SAME_TARGET_TIME") -- DRAGON.scr:750
    ctx:add("g_nTemp", "switchHurryTime") -- DRAGON.scr:751
    if ctx:condition("g_nTemp < lastTargetSwitch") then -- DRAGON.scr:752
        do return ctx:exit("") end -- DRAGON.scr:753
    end -- DRAGON.scr:754
    mm9.gosub(script, ctx, "FindTarget") -- DRAGON.scr:756
    if ctx:condition("hFoundTarget==NULL") then -- DRAGON.scr:758
        do return ctx:exit("") end -- DRAGON.scr:759
    end -- DRAGON.scr:760
    if ctx:condition("g_hTarget==NULL") then -- DRAGON.scr:762
        do return mm9.gotoLabel(script, ctx, "NewTarget") end -- DRAGON.scr:763
    end -- DRAGON.scr:764
    if ctx:condition("hFoundTarget==g_hTarget") then -- DRAGON.scr:766
        do return ctx:exit("") end -- DRAGON.scr:767
    end -- DRAGON.scr:768
    ctx:state().switchChance = 20 -- DRAGON.scr:770
    ctx:state().currTargetDist = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- DRAGON.scr:772
    ctx:state().foundTargetDist = ctx:self():aiDistanceTo(ctx:object("hFoundTarget")) -- DRAGON.scr:773
    if ctx:condition("currTargetDist > foundTargetDist") then -- DRAGON.scr:775
        ctx:state().switchChance = 80 -- DRAGON.scr:776
    end -- DRAGON.scr:777
    if ctx:condition("hFoundTarget==hLastAttacker") then -- DRAGON.scr:779
        ctx:state().switchChance = (tonumber(ctx:state().switchChance) or 0) + 45 -- DRAGON.scr:780
    end -- DRAGON.scr:781
    ctx:getTime("g_nTemp") -- DRAGON.scr:783
    ctx:sub("g_nTemp", "MAX_SAME_TARGET_TIME") -- DRAGON.scr:785
    ctx:add("g_nTemp", "switchHurryTime") -- DRAGON.scr:786
    if ctx:condition("g_nTemp > lastTargetSwitch") then -- DRAGON.scr:788
        do return mm9.gotoLabel(script, ctx, "NewTarget") end -- DRAGON.scr:789
    end -- DRAGON.scr:790
    ctx:randomInt(0, 100, "random") -- DRAGON.scr:792
    if ctx:condition("random > switchChance") then -- DRAGON.scr:794
        do return ctx:exit("") end -- DRAGON.scr:795
    end -- DRAGON.scr:796
end

script.labels["NewTarget"] = function(ctx)
    -- DRAGON.scr:799
    ctx:set("g_hTarget", "hFoundTarget") -- DRAGON.scr:802
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGON.scr:804
    do return ctx:exit("") end -- DRAGON.scr:806
end

script.labels["SetupNewTarget"] = function(ctx)
    -- DRAGON.scr:809
    ctx:getTime("lastTargetSwitch") -- DRAGON.scr:812
    ctx:state().switchHurryTime = 0 -- DRAGON.scr:813
    ctx:self():setTarget(ctx:object("g_hTarget")) -- DRAGON.scr:814
    do return ctx:exit("") end -- DRAGON.scr:816
end

script.labels["DragonAwake"] = function(ctx)
    -- DRAGON.scr:819
    -- Now we're awake, go get him...
    if ctx:condition("hWakeUpTarget!=NULL") then -- DRAGON.scr:824
        ctx:set("g_hTarget", "hWakeUpTarget") -- DRAGON.scr:825
    end -- DRAGON.scr:826
    ctx:onEvent("OnDamage", "OnDamage") -- DRAGON.scr:828
    ctx:onEvent("OnLostTarget", "OnLostTarget") -- DRAGON.scr:829
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- DRAGON.scr:830
    -- jsl--> I think we just want to find a target normal, ie: doesn't HAVE to
    -- be the guy that just shot us...
    ctx:state().g_hTarget = nil -- DRAGON.scr:836
    if ctx:condition("g_hTarget==NULL") then -- DRAGON.scr:838
        -- Try to find one...
        mm9.gosub(script, ctx, "FindTarget") -- DRAGON.scr:841
        if ctx:condition("hFoundTarget==NULL") then -- DRAGON.scr:842
            ctx:self():setIdle() -- DRAGON.scr:843
            do return ctx:exit("") end -- DRAGON.scr:844
        end -- DRAGON.scr:845
        ctx:set("g_hTarget", "hFoundTarget") -- DRAGON.scr:847
    end -- DRAGON.scr:848
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGON.scr:850
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:851
    do return ctx:exit("") end -- DRAGON.scr:853
end

script.labels["DamageWakeUp"] = function(ctx)
    -- DRAGON.scr:856
    ctx:getParam(0, "hWakeUpTarget") -- DRAGON.scr:858
    if ctx:condition("hWakeUpTarget!=0") then -- DRAGON.scr:860
        ctx:self():link(ctx:object("hWakeUpTarget")) -- DRAGON.scr:861
    end -- DRAGON.scr:862
    mm9.gosub(script, ctx, "WakeUp") -- DRAGON.scr:864
    do return ctx:exit("") end -- DRAGON.scr:866
end

script.labels["WakeUpTrigger"] = function(ctx)
    -- DRAGON.scr:869
    ctx:getParam(0, "hWakeUpTarget") -- DRAGON.scr:871
    if ctx:condition("hWakeUpTarget!=0") then -- DRAGON.scr:873
        ctx:self():link(ctx:object("hWakeUpTarget")) -- DRAGON.scr:874
    end -- DRAGON.scr:875
    mm9.gosub(script, ctx, "WakeUp") -- DRAGON.scr:877
    do return ctx:exit("") end -- DRAGON.scr:879
end

script.labels["WakeUp"] = function(ctx)
    -- DRAGON.scr:882
    -- Wake up and go get 'em boy!
    ctx:onEvent("OnFoundPlayer") -- DRAGON.scr:888
    ctx:onEvent("OnAttackReady") -- DRAGON.scr:889
    ctx:onEvent("OnDamage", "WakingUpDamage") -- DRAGON.scr:890
    ctx:self():playAnimation("WakeUp", "DragonAwake") -- DRAGON.scr:892
    do return ctx:exit("TRUE") end -- DRAGON.scr:894
end

script.labels["SetupSleeping"] = function(ctx)
    -- DRAGON.scr:897
    -- Setup the dragon as asleep....
    -- Loop our sleeping animation
    ctx:self():loopAnimation("Sleep", 0) -- DRAGON.scr:904
    -- When we find the player, we'll need to wake up...
    ctx:onEvent("OnDamage", "DamageWakeUp") -- DRAGON.scr:907
    do return ctx:exit("") end -- DRAGON.scr:909
end

script.labels["OnCongestion"] = function(ctx)
    -- DRAGON.scr:912
    -- Don't do anything here...
    do return ctx:exit("FALSE") end -- DRAGON.scr:918
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- DRAGON.scr:921
    ctx:getParam(0, "hObject") -- DRAGON.scr:924
    if ctx:condition("hObject==hWakeUpTarget") then -- DRAGON.scr:926
        ctx:state().hWakeUpTarget = nil -- DRAGON.scr:927
    end -- DRAGON.scr:928
    if ctx:condition("hObject==hLastAttacker") then -- DRAGON.scr:930
        ctx:state().hLastAttacker = nil -- DRAGON.scr:931
    end -- DRAGON.scr:932
    if ctx:condition("hObject==g_hTarget") then -- DRAGON.scr:934
        ctx:self():setTarget(nil) -- DRAGON.scr:935
        ctx:state().g_hTarget = nil -- DRAGON.scr:936
    end -- DRAGON.scr:937
    do return ctx:exit("") end -- DRAGON.scr:939
end

script.labels["OnTest"] = function(ctx)
    -- DRAGON.scr:942
    ctx:self():playAnimation("rAttack2", "AttackDone") -- DRAGON.scr:945
    do return ctx:exit("") end -- DRAGON.scr:948
end

script.labels["TargetTooFar"] = function(ctx)
    -- DRAGON.scr:951
    ctx:self():setTarget(nil) -- DRAGON.scr:954
    ctx:state().g_hTarget = nil -- DRAGON.scr:955
    mm9.gosub(script, ctx, "ClearAttackTimer") -- DRAGON.scr:956
    ctx:self():setIdle() -- DRAGON.scr:957
    ctx:onEvent("OnTargetBeyondDist", "MAX_ATTACK_DIST", "TargetTooFar") -- DRAGON.scr:958
    do return ctx:exit("") end -- DRAGON.scr:960
end

script.labels["OnWinceDone"] = function(ctx)
    -- DRAGON.scr:963
    -- Called when the Dragon's wince animation
    -- is finished...
    -- Just setup our next attack...
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:971
    do return ctx:exit("TRUE") end -- DRAGON.scr:973
end

script.labels["SpawnMutants"] = function(ctx)
    -- DRAGON.scr:976
    ctx:set("SPAWN_INTERVAL", "SPAWN_INTERVAL * 2") -- DRAGON.scr:982
    ctx:wait(22, "SPAWN_INTERVAL", "SpawnMutants") -- DRAGON.scr:984
    ctx:state().g_hObject = ctx:objectOrNil("MutantMarker0") -- DRAGON.scr:986
    if ctx:condition("g_hObject!=NULL") then -- DRAGON.scr:988
        ctx:state().x, ctx:state().y, ctx:state().z = ctx:object("g_hObject"):pos() -- DRAGON.scr:989
        ctx:state().g_hObject = ctx:spawn("x", "y", "z", "SpawnCmd") -- DRAGON.scr:990
        if ctx:condition("g_hObject!=NULL") then -- DRAGON.scr:991
            ctx:trigger("g_hObject", "GetMe") -- DRAGON.scr:992
        end -- DRAGON.scr:993
    end -- DRAGON.scr:994
    ctx:state().g_hObject = ctx:objectOrNil("MutantMarker1") -- DRAGON.scr:996
    if ctx:condition("g_hObject!=NULL") then -- DRAGON.scr:998
        ctx:state().x, ctx:state().y, ctx:state().z = ctx:object("g_hObject"):pos() -- DRAGON.scr:999
        ctx:state().g_hObject = ctx:spawn("x", "y", "z", "SpawnCmd") -- DRAGON.scr:1000
        if ctx:condition("g_hObject!=NULL") then -- DRAGON.scr:1001
            ctx:trigger("g_hObject", "GetMe") -- DRAGON.scr:1002
        end -- DRAGON.scr:1003
    end -- DRAGON.scr:1004
    do return ctx:exit("") end -- DRAGON.scr:1006
end

script.labels["NormalSetup"] = function(ctx)
    -- DRAGON.scr:1009
    ctx:state().g_nTemp = ctx:self():getStat("VisibleRange") -- DRAGON.scr:1011
    mm9.gosub(script, ctx, "DoBreathing") -- DRAGON.scr:1013
    if ctx:condition("g_nTemp > MAX_ATTACK_DIST") then -- DRAGON.scr:1015
        -- Don't go less than our default...
        ctx:set("MAX_ATTACK_DIST", "g_nTemp") -- DRAGON.scr:1017
    end -- DRAGON.scr:1018
    ctx:onEvent("OnCongestion", "OnCongestion") -- DRAGON.scr:1020
    ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- DRAGON.scr:1021
    ctx:onEvent("OnTargetWithinDist", "WING_ATTACK_DIST", "TargetWithinWindDist") -- DRAGON.scr:1022
    ctx:onEvent("OnTargetBeyondDist", "MAX_ATTACK_DIST", "TargetTooFar") -- DRAGON.scr:1023
    ctx:addTrigger("WakeUp", "WakeUpTrigger") -- DRAGON.scr:1026
    ctx:addTrigger("Test", "OnTest") -- DRAGON.scr:1027
    ctx:addTrigger("DragonWinceDone", "OnWinceDone") -- DRAGON.scr:1028
    ctx:state().dimsX, ctx:state().dimsY, ctx:state().dimsZ = ctx:self():dims() -- DRAGON.scr:1030
    ctx:onEvent("OnDamage", "OnDamage") -- DRAGON.scr:1032
    ctx:onEvent("OnLostTarget", "OnLostTarget") -- DRAGON.scr:1033
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- DRAGON.scr:1034
    ctx:wait(22, "SPAWN_INTERVAL", "SpawnMutants") -- DRAGON.scr:1036
    do return ctx:exit("") end -- DRAGON.scr:1038
end

script.labels["TauntDone"] = function(ctx)
    -- DRAGON.scr:1042
    ctx:self():stop() -- DRAGON.scr:1044
    ctx:self():setIdle() -- DRAGON.scr:1045
    mm9.gosub(script, ctx, "NormalSetup") -- DRAGON.scr:1046
    ctx:state().g_hTarget = ctx:player() -- DRAGON.scr:1048
    mm9.gosub(script, ctx, "SetupNewTarget") -- DRAGON.scr:1050
    mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:1051
    do return ctx:exit("") end -- DRAGON.scr:1054
end

script.labels["OnLanded"] = function(ctx)
    -- DRAGON.scr:1057
    ctx:self():playAnimation("Taunt", "TauntDone") -- DRAGON.scr:1059
    do return ctx:exit("") end -- DRAGON.scr:1061
end

script.labels["OnTrigger"] = function(ctx)
    -- DRAGON.scr:1064
    ctx:removeTrigger("Trigger") -- DRAGON.scr:1066
    ctx:self():setFlag("FLAG_VISIBLE", true) -- DRAGON.scr:1068
    ctx:self():setFlag("FLAG_SOLID", true) -- DRAGON.scr:1069
    ctx:self():playAnimation("Land", "OnLanded") -- DRAGON.scr:1071
    mm9.gosub(script, ctx, "DoBreathing") -- DRAGON.scr:1073
    do return ctx:exit("") end -- DRAGON.scr:1075
end

script.labels["HideSetup"] = function(ctx)
    -- DRAGON.scr:1078
    ctx:self():setFlag("FLAG_VISIBLE", false) -- DRAGON.scr:1081
    ctx:self():setFlag("FLAG_SOLID", false) -- DRAGON.scr:1082
    ctx:addTrigger("Trigger", "OnTrigger") -- DRAGON.scr:1083
    do return ctx:exit("") end -- DRAGON.scr:1085
end

script.labels["DoBreathing"] = function(ctx)
    -- DRAGON.scr:1088
    mm9.gosub(script, ctx, "DoBreath") -- DRAGON.scr:1090
    do return ctx:exit("") end -- DRAGON.scr:1091
end

script.labels["DoBreath"] = function(ctx)
    -- DRAGON.scr:1094
    ctx:wait("BREATHING_WAIT", 2.5, "DoBreath") -- DRAGON.scr:1096
    ctx:self():doClientFx("sDragonSmoke", "FALSE", "FALSE") -- DRAGON.scr:1098
    do return ctx:exit("") end -- DRAGON.scr:1100
end

script.labels["CacheFiles"] = function(ctx)
    -- DRAGON.scr:1104
    ctx:cacheClientFx("sDragonSmoke") -- DRAGON.scr:1107
    do return ctx:exit("") end -- DRAGON.scr:1109
end

script.labels["OnDeath"] = function(ctx)
    -- DRAGON.scr:1112
    ctx:getParam(0, "g_hObject") -- DRAGON.scr:1114
    ctx:state().g_bTemp = ctx:object("g_hObject"):isPlayer() -- DRAGON.scr:1116
    if ctx:condition("g_bTemp==TRUE") then -- DRAGON.scr:1117
        ctx:giveKey(472) -- DRAGON.scr:1118
        ctx:giveItem(577) -- DRAGON.scr:1119
    end -- DRAGON.scr:1120
    do return ctx:exit("FALSE") end -- DRAGON.scr:1122
end

script.labels["OnGrowl1"] = function(ctx)
    -- DRAGON.scr:1125
    ctx:playSound("sounds\\animsounds\\dragon\\wince1.wav", "DoNothing", 2000, 4000) -- DRAGON.scr:1127
    do return ctx:exit("") end -- DRAGON.scr:1129
end

script.labels["OnGrowl2"] = function(ctx)
    -- DRAGON.scr:1132
    ctx:playSound("sounds\\animsounds\\dragon\\wince2.wav", "DoNothing", 2000, 4000) -- DRAGON.scr:1134
    do return ctx:exit("") end -- DRAGON.scr:1136
end

script.labels["OnHitFloor"] = function(ctx)
    -- DRAGON.scr:1139
    ctx:playSound("sounds\\animsounds\\dragon\\land.wav", "DoNothing", 2000, 4000) -- DRAGON.scr:1141
    do return ctx:exit("") end -- DRAGON.scr:1144
end

script.labels["Main"] = function(ctx)
    -- DRAGON.scr:1147
    -- Parameters:
    -- p0 ==> bFlyInOnTrigger
    -- Dragons hate everyone....
    ctx:self():addEnemy("AIBase") -- DRAGON.scr:1158
    ctx:getParam(0, "g_bTemp") -- DRAGON.scr:1162
    if ctx:condition("g_bTemp==FALSE") then -- DRAGON.scr:1164
        mm9.gosub(script, ctx, "NormalSetup") -- DRAGON.scr:1165
    else -- DRAGON.scr:1166
        mm9.gosub(script, ctx, "HideSetup") -- DRAGON.scr:1167
    end -- DRAGON.scr:1168
    ctx:addTrigger("SpawnMutants", "SpawnMutants") -- DRAGON.scr:1170
    ctx:addModelKey("Growl1", "OnGrowl1") -- DRAGON.scr:1171
    ctx:addModelKey("Growl2", "OnGrowl2") -- DRAGON.scr:1172
    ctx:addModelKey("HitFloor", "OnHitFloor") -- DRAGON.scr:1173
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- DRAGON.scr:1174
    mm9.gosub(script, ctx, "CacheFiles") -- DRAGON.scr:1176
    ctx:onEvent("OnDeath", "OnDeath") -- DRAGON.scr:1178
    do return ctx:exit("") end -- DRAGON.scr:1180
end

return script
