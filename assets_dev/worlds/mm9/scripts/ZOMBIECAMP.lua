-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ZOMBIECAMP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "base.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "aiglobals.inc" }

-- Zombiecamp.scr
-- John Machin
-- This script uses base.inc and extends
-- it to allow for this Zombie camp to attack
-- the Zombie camp nearby
script.labels["OnUse"] = function(ctx)
    -- ZOMBIECAMP.scr:34
    ctx:getParam(0, "g_hObject") -- ZOMBIECAMP.scr:37
    ctx:command("faceobject", "g_hObject, 180") -- ZOMBIECAMP.scr:39
    do return ctx:exit("") end -- ZOMBIECAMP.scr:41
end

script.labels["ZombieOnAlert"] = function(ctx)
    -- ZOMBIECAMP.scr:44
    if ctx:condition("g_hTarget!=NULL") then -- ZOMBIECAMP.scr:46
        -- only a small chance we'll go consider switching targets...
        ctx:command("getrandomint", "0,100,g_nRandom") -- ZOMBIECAMP.scr:48
        if ctx:condition("g_nRandom > 10") then -- ZOMBIECAMP.scr:49
            do return ctx:exit("FALSE") end -- ZOMBIECAMP.scr:50
        end -- ZOMBIECAMP.scr:51
    end -- ZOMBIECAMP.scr:52
    ctx:getParam(0, "hAlertedBy") -- ZOMBIECAMP.scr:54
    ctx:command("getclassname", "hAlertedBy, sAlertName") -- ZOMBIECAMP.scr:55
    if ctx:condition("sAlertName != g_sMyClassName") then -- ZOMBIECAMP.scr:57
        do return ctx:exit("FALSE") end -- ZOMBIECAMP.scr:58
    end -- ZOMBIECAMP.scr:59
    -- Ok, we were alerted by our buddies, therefore
    -- let's see if we want to attack the guy who
    -- is attacking our buddy!
    ctx:getParam(1, "g_hObject") -- ZOMBIECAMP.scr:65
    ctx:command("getclassname", "g_hObject, g_sTemp") -- ZOMBIECAMP.scr:66
    if ctx:condition("g_sTemp==g_sMyClassName") then -- ZOMBIECAMP.scr:68
        do return ctx:exit("FALSE") end -- ZOMBIECAMP.scr:69
    end -- ZOMBIECAMP.scr:70
    ctx:command("set", "g_hTarget, g_hObject") -- ZOMBIECAMP.scr:72
    ctx:command("target", "g_hTarget") -- ZOMBIECAMP.scr:73
    mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:75
    do return ctx:exit("") end -- ZOMBIECAMP.scr:77
end

script.labels["ZombieFindTarget"] = function(ctx)
    -- ZOMBIECAMP.scr:80
    ctx:command("getobjects", "g_sEnemyName, 50000, 5, g_hEnemyArray, g_nObjects") -- ZOMBIECAMP.scr:82
    if ctx:condition("g_nObjects != NULL") then -- ZOMBIECAMP.scr:84
        if ctx:condition("g_hTarget == NULL") then -- ZOMBIECAMP.scr:85
            -- Randomly pick a target from the three
            ctx:command("sub", "g_nObjects, 1") -- ZOMBIECAMP.scr:87
            ctx:command("getrandomint", "0, g_nObjects, g_nRandom") -- ZOMBIECAMP.scr:88
            ctx:command("arrayget", "g_hEnemyArray, g_nRandom, g_hTarget") -- ZOMBIECAMP.scr:89
            ctx:command("target", "g_hTarget") -- ZOMBIECAMP.scr:90
            if ctx:condition("g_hTarget != NULL") then -- ZOMBIECAMP.scr:91
                mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:92
            end -- ZOMBIECAMP.scr:93
        end -- ZOMBIECAMP.scr:95
    else -- ZOMBIECAMP.scr:96
        ctx:command("setidle", "") -- ZOMBIECAMP.scr:97
        ctx:command("wait", "0, 5, ZombieFindTarget") -- ZOMBIECAMP.scr:98
    end -- ZOMBIECAMP.scr:99
    do return ctx:exit("") end -- ZOMBIECAMP.scr:101
end

script.labels["ZombieTargetDead"] = function(ctx)
    -- ZOMBIECAMP.scr:104
    ctx:getParam(0, "g_nTemp") -- ZOMBIECAMP.scr:107
    ctx:command("target", "NULL") -- ZOMBIECAMP.scr:109
    ctx:command("set", "g_hTarget, NULL") -- ZOMBIECAMP.scr:110
    if ctx:condition("g_nTemp==g_hMyObject") then -- ZOMBIECAMP.scr:112
        -- We killed him!
        -- taunt him
        -- Taunt ZombieFindTarget
        mm9.gosub(script, ctx, "ZombieFindTarget") -- ZOMBIECAMP.scr:116
    else -- ZOMBIECAMP.scr:117
        -- just go home...
        mm9.gosub(script, ctx, "ZombieFindTarget") -- ZOMBIECAMP.scr:119
    end -- ZOMBIECAMP.scr:120
    do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:122
end

script.labels["ZombieDamageDone"] = function(ctx)
    -- ZOMBIECAMP.scr:125
    -- We were attacked, now we want to run
    -- after whoever attacked us!
    if ctx:condition("g_hAttacker==g_hMyObject") then -- ZOMBIECAMP.scr:132
        do return ctx:exit("FALSE") end -- ZOMBIECAMP.scr:133
    end -- ZOMBIECAMP.scr:134
    ctx:command("getclassname", "g_hAttacker, sAlertName") -- ZOMBIECAMP.scr:136
    -- Make sure we don't attack fellow zombies
    if ctx:condition("sAlertName == g_sMyClassName") then -- ZOMBIECAMP.scr:139
        do return ctx:exit("FALSE") end -- ZOMBIECAMP.scr:140
    end -- ZOMBIECAMP.scr:141
    mm9.gosub(script, ctx, "BaseDamageDone") -- ZOMBIECAMP.scr:143
    do return ctx:exit("") end -- ZOMBIECAMP.scr:145
end

script.labels["ZombieAttackReady"] = function(ctx)
    -- ZOMBIECAMP.scr:149
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("getclassname", "g_hTarget, sAlertName") -- ZOMBIECAMP.scr:156
    if ctx:condition("sAlertName == g_sMyClassName") then -- ZOMBIECAMP.scr:157
        ctx:command("target", "NULL") -- ZOMBIECAMP.scr:158
        ctx:command("set", "g_hTarget, NULL") -- ZOMBIECAMP.scr:159
        mm9.gosub(script, ctx, "ZombieFindTarget") -- ZOMBIECAMP.scr:160
    else -- ZOMBIECAMP.scr:161
        ctx:command("set", "g_bFighting, TRUE") -- ZOMBIECAMP.scr:162
        ctx:command("gettime", "g_nLastAttackTime") -- ZOMBIECAMP.scr:163
        ctx:command("attack", "") -- ZOMBIECAMP.scr:164
    end -- ZOMBIECAMP.scr:165
    do return ctx:exit("") end -- ZOMBIECAMP.scr:167
end

script.labels["ZombieLostTarget"] = function(ctx)
    -- ZOMBIECAMP.scr:170
    -- We lost the target.  Reaquire and attack;
    if ctx:condition("g_hTarget != NULL") then -- ZOMBIECAMP.scr:174
        ctx:command("target", "g_hTarget") -- ZOMBIECAMP.scr:175
        mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:176
    else -- ZOMBIECAMP.scr:177
        ctx:command("target", "NULL") -- ZOMBIECAMP.scr:178
        ctx:command("set", "g_hTarget, NULL") -- ZOMBIECAMP.scr:179
        mm9.gosub(script, ctx, "ZombieFindTarget") -- ZOMBIECAMP.scr:180
    end -- ZOMBIECAMP.scr:181
    do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:183
end

script.labels["ZombieOutOfRangeWait"] = function(ctx)
    -- ZOMBIECAMP.scr:186
    -- We don't want to run after target
    -- until it's far enough away or we are
    -- ready to attack...
    if ctx:condition("g_hTarget==NULL") then -- ZOMBIECAMP.scr:193
        do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:194
    end -- ZOMBIECAMP.scr:195
    ctx:command("isattacking", "g_bAttacking") -- ZOMBIECAMP.scr:197
    if ctx:condition("g_bAttacking==TRUE") then -- ZOMBIECAMP.scr:199
        ctx:command("wait", "0, 0.5, ZombieOutOfRangeWait") -- ZOMBIECAMP.scr:200
        do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:201
    end -- ZOMBIECAMP.scr:202
    ctx:command("canattack", "g_bCanAttack") -- ZOMBIECAMP.scr:204
    if ctx:condition("g_bCanAttack==TRUE") then -- ZOMBIECAMP.scr:205
        ctx:command("isattacking", "g_bAttacking") -- ZOMBIECAMP.scr:206
        if ctx:condition("g_bAttacking==TRUE") then -- ZOMBIECAMP.scr:208
            do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:209
        end -- ZOMBIECAMP.scr:210
        mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:212
        do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:213
    end -- ZOMBIECAMP.scr:214
    -- randomly play a taunt animation...
    ctx:command("getrandomint", "0, 100, g_nRandom") -- ZOMBIECAMP.scr:217
    if ctx:condition("g_nRandom < 30") then -- ZOMBIECAMP.scr:219
        if ctx:condition("g_nRandom < 15") then -- ZOMBIECAMP.scr:220
            ctx:command("taunt", "ZombieAttackWaitAnimDone") -- ZOMBIECAMP.scr:221
        else -- ZOMBIECAMP.scr:222
            ctx:command("aware", "ZombieAttackWaitAnimDone") -- ZOMBIECAMP.scr:223
        end -- ZOMBIECAMP.scr:224
        do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:225
    end -- ZOMBIECAMP.scr:226
    -- AIGetDistance g_hTarget, g_nDist1
    -- if ( g_nDist1 > 200 )		; if they are too far away...
    ctx:command("walkto", "g_hTarget") -- ZOMBIECAMP.scr:231
    -- Wait 0, 0.5, ZombieOutOfRangeWalkingWait
    -- Exit TRUE
    -- endif
    -- Continue waiting....
    ctx:command("wait", "0, 0.5, ZombieOutOfRangeWait") -- ZOMBIECAMP.scr:238
    do return ctx:exit("") end -- ZOMBIECAMP.scr:240
end

script.labels["ZombieStuckDone"] = function(ctx)
    -- ZOMBIECAMP.scr:243
    -- This is called when a stuck animation
    -- has finished... We'll just re-attempt
    -- to run after our target...
    if ctx:condition("g_hTarget==NULL") then -- ZOMBIECAMP.scr:250
        do return ctx:exit("FALSE") end -- ZOMBIECAMP.scr:251
    end -- ZOMBIECAMP.scr:252
    -- for now, don't Wait 0, when stuck..
    mm9.gosub(script, ctx, "ZombieFindTarget") -- ZOMBIECAMP.scr:257
    do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:258
    if ctx:condition("g_nStuckTime==0.0") then -- ZOMBIECAMP.scr:260
        ctx:command("gettime", "g_nStuckTime") -- ZOMBIECAMP.scr:261
    else -- ZOMBIECAMP.scr:262
        ctx:command("gettime", "g_nTemp") -- ZOMBIECAMP.scr:263
        ctx:command("sub", "g_nTemp, g_nStuckTime") -- ZOMBIECAMP.scr:264
        if ctx:condition("g_nTemp > MIN_STUCK_TIME") then -- ZOMBIECAMP.scr:266
            ctx:command("set", "g_nStuckTime, 0") -- ZOMBIECAMP.scr:267
            mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:268
            do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:269
        end -- ZOMBIECAMP.scr:270
    end -- ZOMBIECAMP.scr:271
    do return ctx:exit("FALSE") end -- ZOMBIECAMP.scr:273
end

script.labels["ZombieOutOfRangeWalkingWait"] = function(ctx)
    -- ZOMBIECAMP.scr:277
    -- Once we start walking after target,
    -- we want to start running as soon as
    -- we are attack ready...
    ctx:command("canattack", "g_bCanAttack") -- ZOMBIECAMP.scr:285
    if ctx:condition("g_bCanAttack==TRUE") then -- ZOMBIECAMP.scr:286
        ctx:command("isattacking", "g_bAttacking") -- ZOMBIECAMP.scr:287
        if ctx:condition("g_bAttacking==TRUE") then -- ZOMBIECAMP.scr:289
            do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:290
        end -- ZOMBIECAMP.scr:291
        mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:293
        do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:294
    end -- ZOMBIECAMP.scr:295
    ctx:command("wait", "0, 0.5, ZombieOutOfRangeWait") -- ZOMBIECAMP.scr:297
    do return ctx:exit("") end -- ZOMBIECAMP.scr:299
end

script.labels["ZombieAttackWaitAnimDone"] = function(ctx)
    -- ZOMBIECAMP.scr:303
    mm9.gosub(script, ctx, "ZombieOutOfRangeWait") -- ZOMBIECAMP.scr:306
    do return ctx:exit("") end -- ZOMBIECAMP.scr:308
end

script.labels["ZombieTargetOutOfRange"] = function(ctx)
    -- ZOMBIECAMP.scr:312
    -- Target moved out of our weapon range.
    -- Go after him!
    ctx:command("canattack", "g_bCanAttack") -- ZOMBIECAMP.scr:319
    ctx:command("isattacking", "g_bAttacking") -- ZOMBIECAMP.scr:320
    if ctx:condition("g_bAttacking==TRUE") then -- ZOMBIECAMP.scr:322
        ctx:command("wait", "0, 0.5, ZombieOutOfRangeWait") -- ZOMBIECAMP.scr:323
    end -- ZOMBIECAMP.scr:324
    if ctx:condition("g_bCanAttack==TRUE") then -- ZOMBIECAMP.scr:326
        mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:327
    else -- ZOMBIECAMP.scr:328
        ctx:command("wait", "0, 0.5, ZombieOutOfRangeWait") -- ZOMBIECAMP.scr:329
    end -- ZOMBIECAMP.scr:330
    do return ctx:exit("") end -- ZOMBIECAMP.scr:332
end

script.labels["ZombieObstacle"] = function(ctx)
    -- ZOMBIECAMP.scr:336
    ctx:getParam(0, "g_hObstacle") -- ZOMBIECAMP.scr:339
    ctx:command("getclassname", "g_hObstacle, g_sObstacleName") -- ZOMBIECAMP.scr:340
    if ctx:condition("g_sObstacleName == g_sEnemyName") then -- ZOMBIECAMP.scr:342
        ctx:command("getrandomint", "0, 10, g_nRandom") -- ZOMBIECAMP.scr:343
        if ctx:condition("g_nRandom > 3") then -- ZOMBIECAMP.scr:344
            ctx:command("set", "g_hTarget, g_hObstacle") -- ZOMBIECAMP.scr:345
            ctx:command("target", "g_hTarget") -- ZOMBIECAMP.scr:346
            mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:347
            do return ctx:exit("TRUE") end -- ZOMBIECAMP.scr:349
        end -- ZOMBIECAMP.scr:350
    end -- ZOMBIECAMP.scr:351
    mm9.gosub(script, ctx, "BaseObstacle") -- ZOMBIECAMP.scr:353
    do return ctx:exit("") end -- ZOMBIECAMP.scr:355
end

script.labels["ZombieDeathDone"] = function(ctx)
    -- ZOMBIECAMP.scr:360
    ctx:trigger("g_hCampDirector", "ZombieDeath") -- ZOMBIECAMP.scr:362
    do return ctx:exit("FALSE") end -- ZOMBIECAMP.scr:364
end

script.labels["Init"] = function(ctx)
    -- ZOMBIECAMP.scr:367
    ctx:command("getobjecthandle", "CampDirector, g_hCampDirector") -- ZOMBIECAMP.scr:370
    ctx:command("gettarget", "g_hTarget") -- ZOMBIECAMP.scr:372
    if ctx:condition("g_hTarget!=NULL") then -- ZOMBIECAMP.scr:373
        mm9.gosub(script, ctx, "BaseGoGetHim") -- ZOMBIECAMP.scr:374
    else -- ZOMBIECAMP.scr:375
        mm9.gosub(script, ctx, "ZombieFindTarget") -- ZOMBIECAMP.scr:376
    end -- ZOMBIECAMP.scr:377
    do return ctx:exit("") end -- ZOMBIECAMP.scr:379
end

script.labels["Main"] = function(ctx)
    -- ZOMBIECAMP.scr:382
    -- This routine is automatically run
    -- at script startup...
    ctx:command("getmyhandle", "g_hMyObject") -- ZOMBIECAMP.scr:387
    ctx:command("getclassname", "g_hMyObject, g_sMyClassName") -- ZOMBIECAMP.scr:388
    -- Setup our event handlers...
    -- Base callbacks
    ctx:command("ondamage", "BaseDamage") -- ZOMBIECAMP.scr:396
    ctx:command("onpathclear", "BasePathClear") -- ZOMBIECAMP.scr:397
    -- OnObstacle					BaseObstacle
    -- Zombie script call backs
    ctx:command("onalert", "ZombieOnAlert") -- ZOMBIECAMP.scr:401
    ctx:command("ontargetdead", "ZombieTargetDead") -- ZOMBIECAMP.scr:402
    ctx:command("ondamagedone", "ZombieDamageDone") -- ZOMBIECAMP.scr:403
    ctx:command("onattackready", "ZombieAttackReady") -- ZOMBIECAMP.scr:404
    ctx:command("onlosttarget", "ZombieLostTarget") -- ZOMBIECAMP.scr:405
    ctx:command("ondeathdone", "ZombieDeathDone") -- ZOMBIECAMP.scr:406
    ctx:command("ontargetoutofrange", "ZombieTargetOutOfRange") -- ZOMBIECAMP.scr:407
    ctx:command("onstuckdone", "ZombieStuckDone") -- ZOMBIECAMP.scr:408
    ctx:command("onobstacle", "ZombieObstacle") -- ZOMBIECAMP.scr:409
    ctx:command("hasrangeattack", "g_bHasRangeAttack") -- ZOMBIECAMP.scr:412
    if ctx:condition("g_bHasRangeAttack == TRUE") then -- ZOMBIECAMP.scr:414
        -- OnFoundPlayer BaseFoundPlayerRange
    end -- ZOMBIECAMP.scr:416
    ctx:command("settargetlosttime", "30") -- ZOMBIECAMP.scr:418
    ctx:command("set", "g_bAlwaysRunToTarget, TRUE") -- ZOMBIECAMP.scr:419
    ctx:command("set", "g_sEnemyName,Dwarf") -- ZOMBIECAMP.scr:420
    -- See if we already have a target (this would normally happen if
    -- the ai were running another script and then decided to start running
    -- this one...
    ctx:command("wait", "0, 0.1, Init") -- ZOMBIECAMP.scr:428
    do return ctx:exit("") end -- ZOMBIECAMP.scr:430
end

return script
