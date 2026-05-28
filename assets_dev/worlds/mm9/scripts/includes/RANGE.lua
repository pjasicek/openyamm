-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RANGE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 31, path = "AIGLOBALS.INC" }
script.includes[#script.includes + 1] = { line = 32, path = "BaseTimers.inc" }

-- Range.inc
-- Jeff Leggett
-- 10/17/2001
-- Type1: (Legends-like)
-- - Prefers MELEE combat.
-- - Runs after target
-- - Shoots in periodic intervals
-- - Shoots when target out of range
-- - Shoots when cannot reach the target..
-- Type2:
-- - For AI that does not chase after the target
-- - Stays at it's spot and simply shoots at the
-- target when it has a shot.
-- - After each shot, dodges to hiding place (if there)
-- - When ready to fire again, it peaks back out and
-- looks for target...
-- - If the target gets within Melee range, it turns into
-- Type1
-- Note: .SCR file needs to include either basecrawl.inc or
-- basemelee.inc depending on the type of melee system
-- you want to use...
-- #include basecrawl.inc
script.labels["PreRangeAttack"] = function(ctx)
    -- RANGE.inc:71
    ctx:command("gettime", "g_nLastAttackTime") -- RANGE.inc:73
    if ctx:condition("g_rangeAttackType==RANGE_TYPE2") then -- RANGE.inc:75
        ctx:command("stop", "") -- RANGE.inc:76
    else -- RANGE.inc:77
        mm9.gosub(script, ctx, "GetTimeToTarget") -- RANGE.inc:78
        if ctx:condition("g_nTimeToTarget < 1") then -- RANGE.inc:79
            ctx:command("stop", "") -- RANGE.inc:80
        end -- RANGE.inc:81
    end -- RANGE.inc:82
    -- Make sure we face our target during the attack anim...
    ctx:command("target", "g_hTarget, TRUE") -- RANGE.inc:85
    ctx:command("faceobject", "g_hTarget, 360") -- RANGE.inc:87
    do return ctx:exit("") end -- RANGE.inc:89
end

script.labels["DoRangeAttack"] = function(ctx)
    -- RANGE.inc:92
    ctx:command("gettime", "g_nLastAttackTime") -- RANGE.inc:95
    ctx:command("gettime", "g_lastRangeAttack") -- RANGE.inc:96
    ctx:command("rangeattack", "RangeAttackDone") -- RANGE.inc:98
    do return ctx:exit("") end -- RANGE.inc:100
end

script.labels["PostRangeAttack"] = function(ctx)
    -- RANGE.inc:103
    -- virtual function only..
    do return ctx:exit("") end -- RANGE.inc:109
end

script.labels["StartRangeAttack"] = function(ctx)
    -- RANGE.inc:113
    mm9.gosub(script, ctx, "PreRangeAttack") -- RANGE.inc:116
    mm9.gosub(script, ctx, "DoRangeAttack") -- RANGE.inc:117
    mm9.gosub(script, ctx, "PostRangeAttack") -- RANGE.inc:118
    do return ctx:exit("") end -- RANGE.inc:120
end

script.labels["CanRangeAttack"] = function(ctx)
    -- RANGE.inc:124
    -- Set's g_bCanAttack to TRUE or FALSE
    if ctx:condition("g_bResurrecting==TRUE") then -- RANGE.inc:130
        ctx:command("g_bcanattack", "= FALSE") -- RANGE.inc:131
        do return ctx:exit("") end -- RANGE.inc:132
    end -- RANGE.inc:133
    ctx:command("canrangeattack", "g_bCanAttack") -- RANGE.inc:135
    do return ctx:exit("") end -- RANGE.inc:137
end

script.labels["EstimateRangeAttackHit"] = function(ctx)
    -- RANGE.inc:140
    -- Put value in g_hObject
    ctx:command("estimaterangeattackhit", "g_hObject") -- RANGE.inc:146
    do return ctx:exit("") end -- RANGE.inc:148
end

script.labels["CheckRangeTick"] = function(ctx)
    -- RANGE.inc:151
    -- See if we can range attack the target....
    ctx:command("getrandomfloat", "RANGE_ATTACK_CHECK_MIN, RANGE_ATTACK_CHECK_MAX, g_nRandom") -- RANGE.inc:157
    ctx:command("wait", "ATTACK_CHECK_WAIT, g_nRandom, CheckRangeTick") -- RANGE.inc:159
    if ctx:condition("g_hTarget==NULL") then -- RANGE.inc:161
        do return ctx:exit("") end -- RANGE.inc:162
    end -- RANGE.inc:163
    mm9.gosub(script, ctx, "CanRangeAttack") -- RANGE.inc:165
    if ctx:condition("g_bCanAttack==FALSE") then -- RANGE.inc:167
        do return ctx:exit("") end -- RANGE.inc:168
    end -- RANGE.inc:169
    -- Don't range attack if they're within melee attack range...
    ctx:command("aigetdistance", "g_hTarget, g_nDist1") -- RANGE.inc:174
    if ctx:condition("g_nDist1 < g_attackRange") then -- RANGE.inc:176
        do return ctx:exit("") end -- RANGE.inc:177
    end -- RANGE.inc:178
    if ctx:condition("g_nDist1 > g_rangeAttackRange") then -- RANGE.inc:180
        do return ctx:exit("") end -- RANGE.inc:181
    end -- RANGE.inc:182
    mm9.gosub(script, ctx, "EstimateRangeAttackHit") -- RANGE.inc:184
    ctx:command("g_attackchance", "= 0") -- RANGE.inc:187
    if ctx:condition("g_hObject==NULL") then -- RANGE.inc:189
        ctx:command("g_attackchance", "= 20") -- RANGE.inc:190
    else -- RANGE.inc:191
        if ctx:condition("g_hObject==g_hTarget") then -- RANGE.inc:192
            ctx:command("g_attackchance", "= 100") -- RANGE.inc:193
        else -- RANGE.inc:194
            ctx:command("isclass", "g_hObject,AIBase,g_bTemp") -- RANGE.inc:195
            if ctx:condition("g_bTemp==TRUE") then -- RANGE.inc:197
                ctx:command("g_attackchance", "= 0") -- RANGE.inc:198
            else -- RANGE.inc:199
                ctx:command("isworldobject", "g_hObject, g_bTemp") -- RANGE.inc:200
                if ctx:condition("g_bTemp==TRUE") then -- RANGE.inc:201
                    ctx:command("g_attackchance", "= 0") -- RANGE.inc:202
                else -- RANGE.inc:203
                    ctx:command("g_attackchance", "= 15") -- RANGE.inc:204
                end -- RANGE.inc:205
            end -- RANGE.inc:206
        end -- RANGE.inc:207
    end -- RANGE.inc:208
    if ctx:condition("g_attackChance==0") then -- RANGE.inc:210
        do return ctx:exit("") end -- RANGE.inc:211
    end -- RANGE.inc:212
    ctx:command("getrandomint", "0, 100, g_nRandom") -- RANGE.inc:214
    if ctx:condition("g_nRandom > g_attackChance") then -- RANGE.inc:216
        -- See if we should run away
        mm9.gosub(script, ctx, "CheckForHidingPlace") -- RANGE.inc:218
        do return ctx:exit("") end -- RANGE.inc:219
    end -- RANGE.inc:220
    mm9.gosub(script, ctx, "StartRangeAttack") -- RANGE.inc:222
    do return ctx:exit("") end -- RANGE.inc:224
end

script.labels["CheckRangeAttackStart"] = function(ctx)
    -- RANGE.inc:227
    ctx:command("getrandomfloat", "RANGE_ATTACK_CHECK_MIN, RANGE_ATTACK_CHECK_MAX, g_nRandom") -- RANGE.inc:230
    ctx:command("wait", "ATTACK_CHECK_WAIT, g_nRandom, CheckRangeTick") -- RANGE.inc:231
    do return ctx:exit("") end -- RANGE.inc:233
end

script.labels["CheckRangeAttackStop"] = function(ctx)
    -- RANGE.inc:236
    ctx:command("wait", "ATTACK_CHECK_WAIT, 0, DoNothing") -- RANGE.inc:239
    do return ctx:exit("") end -- RANGE.inc:241
end

script.labels["SetupTarget"] = function(ctx)
    -- RANGE.inc:244
    mm9.gosub(script, ctx, "SetupTarget") -- RANGE.inc:247
    mm9.gosub(script, ctx, "CheckRangeAttackStart") -- RANGE.inc:248
    do return ctx:exit("") end -- RANGE.inc:250
end

script.labels["ClearTarget"] = function(ctx)
    -- RANGE.inc:253
    mm9.gosub(script, ctx, "ClearTarget") -- RANGE.inc:256
    mm9.gosub(script, ctx, "CheckRangeAttackStop") -- RANGE.inc:257
    do return ctx:exit("") end -- RANGE.inc:259
end

script.labels["MeleeAttack"] = function(ctx)
    -- RANGE.inc:262
    -- if we're doing a melee attack, postpone our range attack
    -- check...
    mm9.gosub(script, ctx, "CheckRangeAttackStart") -- RANGE.inc:268
    mm9.gosub(script, ctx, "MeleeAttack") -- RANGE.inc:269
    ctx:command("g_bmeleeattack", "= TRUE") -- RANGE.inc:271
    do return ctx:exit("") end -- RANGE.inc:273
end

script.labels["BaseRunAway"] = function(ctx)
    -- RANGE.inc:276
    mm9.gosub(script, ctx, "CheckRangeAttackStop") -- RANGE.inc:279
    mm9.gosub(script, ctx, "BaseRunAway") -- RANGE.inc:280
    do return ctx:exit("") end -- RANGE.inc:282
end

-- Type 2-specific code goes here...
script.labels["AggressiveOutOfRange"] = function(ctx)
    -- RANGE.inc:292
    -- in TYPE2 mode, we don't want to run after them....
    if ctx:condition("g_rangeAttackType!=RANGE_TYPE2") then -- RANGE.inc:298
        mm9.gosub(script, ctx, "AggressiveOutOfRange") -- RANGE.inc:299
        do return ctx:exit("") end -- RANGE.inc:300
    end -- RANGE.inc:301
    if ctx:condition("g_bMeleeAttack==TRUE") then -- RANGE.inc:303
        ctx:command("aigetdistance", "g_hTarget, g_nDist1") -- RANGE.inc:304
        ctx:command("g_ndist2", "= g_attackRange * 3") -- RANGE.inc:306
        if ctx:condition("g_nDist1 > g_nDist2") then -- RANGE.inc:308
            ctx:command("g_bmeleeattack", "= FALSE") -- RANGE.inc:309
        end -- RANGE.inc:310
        if ctx:condition("g_bMeleeAttack==TRUE") then -- RANGE.inc:311
            mm9.gosub(script, ctx, "AggressiveOutOfRange") -- RANGE.inc:312
        end -- RANGE.inc:313
    end -- RANGE.inc:314
    do return ctx:exit("") end -- RANGE.inc:316
end

script.labels["HideDone"] = function(ctx)
    -- RANGE.inc:320
    ctx:command("stop", "") -- RANGE.inc:323
    -- SetPos g_hMyObject, g_startPosX, g_startPosY, g_startPosZ
    mm9.gosub(script, ctx, "AggressiveStart") -- RANGE.inc:326
    mm9.gosub(script, ctx, "CheckRangeAttackStart") -- RANGE.inc:327
    mm9.gosub(script, ctx, "CheckRangeTick") -- RANGE.inc:328
    ctx:command("gettime", "g_nLastHideTime") -- RANGE.inc:330
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_FORWARD") -- RANGE.inc:332
    do return ctx:exit("") end -- RANGE.inc:335
end

script.labels["EndHide"] = function(ctx)
    -- RANGE.inc:338
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- RANGE.inc:341
    -- g_targetDirX = g_startPosX
    -- g_targetDirY = g_posY
    -- g_targetDirZ = g_startPosZ
    -- VecDist g_posX, g_posY, g_posZ, g_startPosX,g_posY,g_startPosZ, g_nDist1
    -- VecSub g_targetDirX,g_targetDirY,g_targetDirZ,g_posX,g_posY,g_posZ
    -- VecNorm g_targetDirX,g_targetDirY,g_targetDirZ
    -- Strafe g_targetDirX,0,g_targetDirZ, TRUE
    -- g_hideTime = g_nDist1 / g_runVel
    -- Wait HIDE_WAIT, g_hideTime, HideDone
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_TARGET") -- RANGE.inc:352
    ctx:command("walktopos", "g_startPosX, g_posY, g_startPosZ,5,HideDone") -- RANGE.inc:353
    do return ctx:exit("") end -- RANGE.inc:356
end

script.labels["AtHidingPlace"] = function(ctx)
    -- RANGE.inc:359
    ctx:command("stop", "") -- RANGE.inc:361
    ctx:command("getstat", "g_hMyObject,RecoveryTimeLeft,g_nTemp") -- RANGE.inc:363
    ctx:command("g_ntemp", "= g_nTemp - g_hideTime") -- RANGE.inc:365
    if ctx:condition("g_nTemp <= 0") then -- RANGE.inc:367
        ctx:command("g_ntemp", "= 0.2") -- RANGE.inc:368
    end -- RANGE.inc:369
    ctx:command("getrandomfloat", "0.4, 2.0, g_nRandom") -- RANGE.inc:371
    ctx:command("g_ntemp", "= g_nTemp + g_nRandom") -- RANGE.inc:373
    ctx:command("wait", "HIDE_WAIT, g_nTemp, EndHide") -- RANGE.inc:375
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_FORWARD") -- RANGE.inc:377
    do return ctx:exit("") end -- RANGE.inc:379
end

script.labels["DoHidingPlace"] = function(ctx)
    -- RANGE.inc:383
    mm9.gosub(script, ctx, "CheckRangeAttackStop") -- RANGE.inc:385
    mm9.gosub(script, ctx, "AggressiveStop") -- RANGE.inc:386
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_TARGET") -- RANGE.inc:388
    ctx:command("runto", "g_hHidingPlace,0,AtHidingPlace") -- RANGE.inc:389
    do return ctx:exit("") end -- RANGE.inc:390
    -- g_hObject = g_hTarget
    -- g_hTarget = g_hHidingPlace
    -- gosub BE_GetTargetDir
    -- g_hTarget = g_hObject
    -- g_hideDirX = g_targetDirX
    -- g_hideDirY = g_targetDirY
    -- g_hideDirZ = g_targetDirZ
    -- GetPos g_hHidingPlace, g_velX, g_velY, g_velZ
    -- GetPos g_hMyObject, g_posX, g_posY, g_posZ
    -- VecDist g_posX, g_posY, g_posZ, g_velX, g_posY, g_velZ, g_nDist1
    -- g_hideTime = g_nDist1 / g_runVel
    -- Strafe g_hideDirX, 0, g_hideDirZ, TRUE
    -- Wait HIDE_WAIT, g_hideTime, AtHidingPlace
    do return ctx:exit("") end -- RANGE.inc:413
end

script.labels["CheckForHidingPlace"] = function(ctx)
    -- RANGE.inc:416
    -- JSL--> Unused/Untested feature causing problems...
    -- Killed it on 2/18/2002
    ctx:command("g_hhidingplace", "= NULL") -- RANGE.inc:423
    -- jsl-->2/18/2002
    do return ctx:exit("") end -- RANGE.inc:426
    if ctx:condition("g_rangeAttackType != RANGE_TYPE2") then -- RANGE.inc:428
        do return ctx:exit("") end -- RANGE.inc:429
    end -- RANGE.inc:430
    mm9.gosub(script, ctx, "EstimateRangeAttackHit") -- RANGE.inc:432
    if ctx:condition("g_hObject==g_hTarget") then -- RANGE.inc:434
        ctx:command("g_ntemp", "= 85") -- RANGE.inc:435
    else -- RANGE.inc:436
        ctx:command("g_ntemp", "= 20") -- RANGE.inc:437
    end -- RANGE.inc:438
    ctx:command("getrandomint", "0,100,g_nRandom") -- RANGE.inc:440
    if ctx:condition("g_nRandom < g_nTemp") then -- RANGE.inc:442
        do return ctx:exit("") end -- RANGE.inc:443
    end -- RANGE.inc:444
    ctx:command("gettime", "g_nTemp") -- RANGE.inc:446
    ctx:command("sub", "g_nTemp,g_nLastHideTime") -- RANGE.inc:448
    if ctx:condition("g_nTemp < MIN_HIDE_TIME") then -- RANGE.inc:450
        do return ctx:exit("") end -- RANGE.inc:451
    end -- RANGE.inc:452
    ctx:command("findhidingplace", "g_hHidingPlace") -- RANGE.inc:454
    if ctx:condition("g_hHidingPlace==NULL") then -- RANGE.inc:456
        do return ctx:exit("") end -- RANGE.inc:457
    end -- RANGE.inc:458
    mm9.gosub(script, ctx, "DoHidingPlace") -- RANGE.inc:460
    do return ctx:exit("") end -- RANGE.inc:462
end

script.labels["RangeAttackDone"] = function(ctx)
    -- RANGE.inc:465
    -- if Type2, see if we've got a hiding place to go to..
    mm9.gosub(script, ctx, "AttackTickCancel") -- RANGE.inc:470
    ctx:command("ontargetbeyonddist", "0") -- RANGE.inc:472
    ctx:command("setstat", "g_hMyObject,RunVel,g_runVel") -- RANGE.inc:474
    mm9.gosub(script, ctx, "AggressiveStart") -- RANGE.inc:476
    if ctx:condition("g_rangeAttackType == RANGE_TYPE2") then -- RANGE.inc:478
        mm9.gosub(script, ctx, "CheckForHidingPlace") -- RANGE.inc:479
    end -- RANGE.inc:480
    do return ctx:exit("TRUE") end -- RANGE.inc:482
end

script.labels["SetupRangeAttackType"] = function(ctx)
    -- RANGE.inc:485
    if ctx:condition("g_rangeAttackType==RANGE_TYPE2") then -- RANGE.inc:487
        ctx:command("range_attack_check_min", "= RANGE_ATTACK1_CHECK_MIN") -- RANGE.inc:488
        ctx:command("range_attack_check_max", "= RANGE_ATTACK1_CHECK_MAX") -- RANGE.inc:489
    end -- RANGE.inc:490
    do return ctx:exit("") end -- RANGE.inc:492
end

script.labels["ShouldRunAfter"] = function(ctx)
    -- RANGE.inc:496
    -- If it's time to do a range attack, let's not run
    -- after them...
    ctx:command("aigetdistance", "g_hTarget, g_nTargetDist") -- RANGE.inc:503
    if ctx:condition("g_nTargetDist >= g_rangeAttackRange") then -- RANGE.inc:505
        mm9.gosub(script, ctx, "ShouldRunAfter") -- RANGE.inc:506
        do return ctx:exit("") end -- RANGE.inc:507
    end -- RANGE.inc:508
    if ctx:condition("g_lastRangeAttack==0") then -- RANGE.inc:510
        ctx:command("gettime", "g_lastRangeAttack") -- RANGE.inc:511
    end -- RANGE.inc:512
    ctx:command("gettime", "g_nTemp") -- RANGE.inc:514
    ctx:command("sub", "g_nTemp,g_lastRangeAttack") -- RANGE.inc:515
    if ctx:condition("g_nTemp > MAX_RANGE_ATTACK_INTERVAL") then -- RANGE.inc:517
        ctx:command("canrangeattack", "g_bTemp") -- RANGE.inc:518
        if ctx:condition("g_bTemp==TRUE") then -- RANGE.inc:519
            mm9.gosub(script, ctx, "EstimateRangeAttackHit") -- RANGE.inc:520
            if ctx:condition("g_hObject==g_hTarget") then -- RANGE.inc:521
                ctx:command("g_btemp", "= FALSE") -- RANGE.inc:522
                -- cprint Not Running after target, it's time to range attack!!
                do return ctx:exit("") end -- RANGE.inc:524
            end -- RANGE.inc:525
        end -- RANGE.inc:526
    end -- RANGE.inc:527
    mm9.gosub(script, ctx, "ShouldRunAfter") -- RANGE.inc:529
    do return ctx:exit("") end -- RANGE.inc:531
end

script.labels["RangeInit"] = function(ctx)
    -- RANGE.inc:534
    ctx:command("getmyhandle", "g_hMyObject") -- RANGE.inc:537
    ctx:command("getstat", "g_hMyObject,RangeAttackType,g_rangeAttackType") -- RANGE.inc:539
    ctx:command("getstat", "g_hMyObject,RangeAttackRange,g_rangeAttackRange") -- RANGE.inc:540
    mm9.gosub(script, ctx, "SetupRangeAttackType") -- RANGE.inc:542
    ctx:command("getpos", "g_hMyObject,g_startPosX,g_startPosY,g_startPosZ") -- RANGE.inc:544
    do return ctx:exit("") end -- RANGE.inc:546
end

return script
