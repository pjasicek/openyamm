-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DWARFCAMP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "base.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "aiglobals.inc" }

-- dwarfcamp.scr
-- John Machin
-- This script uses base.inc and extends
-- it to allow for this dwarf camp to attack
-- the Zombie camp.
script.labels["OnUse"] = function(ctx)
    -- DWARFCAMP.scr:32
    ctx:getParam(0, "g_hObject") -- DWARFCAMP.scr:35
    ctx:self():faceObject(ctx:object("g_hObject"), 180) -- DWARFCAMP.scr:37
    do return ctx:exit("") end -- DWARFCAMP.scr:39
end

script.labels["DwarfOnAlert"] = function(ctx)
    -- DWARFCAMP.scr:42
    if ctx:condition("g_hTarget!=NULL") then -- DWARFCAMP.scr:44
        -- only a small chance we'll go consider switching targets...
        ctx:randomInt(0, 100, "g_nRandom") -- DWARFCAMP.scr:46
        if ctx:condition("g_nRandom > 10") then -- DWARFCAMP.scr:47
            do return ctx:exit("FALSE") end -- DWARFCAMP.scr:48
        end -- DWARFCAMP.scr:49
    end -- DWARFCAMP.scr:50
    ctx:getParam(0, "hAlertedBy") -- DWARFCAMP.scr:52
    ctx:state().sAlertName = ctx:object("hAlertedBy"):className() -- DWARFCAMP.scr:53
    if ctx:condition("sAlertName != g_sMyClassName") then -- DWARFCAMP.scr:55
        do return ctx:exit("FALSE") end -- DWARFCAMP.scr:56
    end -- DWARFCAMP.scr:57
    -- Ok, we were alerted by our buddies, therefore
    -- let's see if we want to attack the guy who
    -- is attacking our buddy!
    ctx:getParam(1, "g_hObject") -- DWARFCAMP.scr:63
    ctx:state().g_sTemp = ctx:object("g_hObject"):className() -- DWARFCAMP.scr:64
    if ctx:condition("g_sTemp==g_sMyClassName") then -- DWARFCAMP.scr:66
        do return ctx:exit("FALSE") end -- DWARFCAMP.scr:67
    end -- DWARFCAMP.scr:68
    ctx:set("g_hTarget", "g_hObject") -- DWARFCAMP.scr:70
    ctx:self():setTarget(ctx:object("g_hTarget")) -- DWARFCAMP.scr:71
    mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:73
    do return ctx:exit("") end -- DWARFCAMP.scr:75
end

script.labels["DwarfFindTarget"] = function(ctx)
    -- DWARFCAMP.scr:78
    ctx:getObjects("g_sEnemyName", 1000, 10, "g_hEnemyArray", "g_nObjects") -- DWARFCAMP.scr:80
    if ctx:condition("g_nObjects != NULL") then -- DWARFCAMP.scr:82
        if ctx:condition("g_hTarget == NULL") then -- DWARFCAMP.scr:83
            -- Randomly pick a target
            ctx:state().g_nObjects = (tonumber(ctx:state().g_nObjects) or 0) - 1 -- DWARFCAMP.scr:85
            ctx:randomInt(0, "g_nObjects", "g_nRandom") -- DWARFCAMP.scr:86
            ctx:arrayGet("g_hEnemyArray", "g_nRandom", "g_hTarget") -- DWARFCAMP.scr:87
            ctx:self():setTarget(ctx:object("g_hTarget")) -- DWARFCAMP.scr:88
            mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:89
        end -- DWARFCAMP.scr:90
    else -- DWARFCAMP.scr:91
        ctx:self():setIdle() -- DWARFCAMP.scr:92
        ctx:wait(0, 5, "DwarfFindTarget") -- DWARFCAMP.scr:93
    end -- DWARFCAMP.scr:94
    do return ctx:exit("") end -- DWARFCAMP.scr:96
end

script.labels["DwarfTargetDead"] = function(ctx)
    -- DWARFCAMP.scr:99
    ctx:getParam(0, "g_nTemp") -- DWARFCAMP.scr:102
    ctx:self():setTarget(nil) -- DWARFCAMP.scr:104
    ctx:state().g_hTarget = nil -- DWARFCAMP.scr:105
    if ctx:condition("g_nTemp==g_hMyObject") then -- DWARFCAMP.scr:107
        -- We killed him!
        -- taunt him, and go home....
        ctx:self():taunt("DwarfFindTarget") -- DWARFCAMP.scr:112
    else -- DWARFCAMP.scr:113
        -- just go home...
        mm9.gosub(script, ctx, "DwarfFindTarget") -- DWARFCAMP.scr:115
    end -- DWARFCAMP.scr:116
    do return ctx:exit("TRUE") end -- DWARFCAMP.scr:118
end

script.labels["DwarfDamageDone"] = function(ctx)
    -- DWARFCAMP.scr:121
    -- We were attacked, now we want to run
    -- after whoever attacked us!
    if ctx:condition("g_hAttacker==g_hMyObject") then -- DWARFCAMP.scr:128
        do return ctx:exit("FALSE") end -- DWARFCAMP.scr:129
    end -- DWARFCAMP.scr:130
    ctx:state().sAlertName = ctx:object("g_hAttacker"):className() -- DWARFCAMP.scr:132
    -- Make sure we don't attack fellow dwarves
    if ctx:condition("sAlertName == g_sMyClassName") then -- DWARFCAMP.scr:135
        do return ctx:exit("FALSE") end -- DWARFCAMP.scr:136
    end -- DWARFCAMP.scr:137
    mm9.gosub(script, ctx, "BaseDamageDone") -- DWARFCAMP.scr:139
    do return ctx:exit("") end -- DWARFCAMP.scr:141
end

script.labels["DwarfAttackReady"] = function(ctx)
    -- DWARFCAMP.scr:144
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:state().sAlertName = ctx:object("g_hTarget"):className() -- DWARFCAMP.scr:151
    if ctx:condition("sAlertName == g_sMyClassName") then -- DWARFCAMP.scr:152
        ctx:self():setTarget(nil) -- DWARFCAMP.scr:153
        ctx:state().g_hTarget = nil -- DWARFCAMP.scr:154
        mm9.gosub(script, ctx, "DwarfFindTarget") -- DWARFCAMP.scr:155
    else -- DWARFCAMP.scr:156
        ctx:state().g_bFighting = true -- DWARFCAMP.scr:157
        ctx:getTime("g_nLastAttackTime") -- DWARFCAMP.scr:159
        ctx:self():attack() -- DWARFCAMP.scr:161
    end -- DWARFCAMP.scr:162
    do return ctx:exit("") end -- DWARFCAMP.scr:164
end

script.labels["DwarfOnLostTarget"] = function(ctx)
    -- DWARFCAMP.scr:167
    -- We lost the target.  But in this we
    -- don't want this to happen so we exit
    -- TRUE
    -- This will keep us from losing the target
    if ctx:condition("g_hTarget != NULL") then -- DWARFCAMP.scr:174
        ctx:self():setTarget(ctx:object("g_hTarget")) -- DWARFCAMP.scr:175
        mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:176
    else -- DWARFCAMP.scr:177
        ctx:self():setTarget(nil) -- DWARFCAMP.scr:178
        ctx:state().g_hTarget = nil -- DWARFCAMP.scr:179
        mm9.gosub(script, ctx, "DwarfFindTarget") -- DWARFCAMP.scr:180
    end -- DWARFCAMP.scr:181
    do return ctx:exit("TRUE") end -- DWARFCAMP.scr:183
end

script.labels["DwarfTargetOutOfRange"] = function(ctx)
    -- DWARFCAMP.scr:186
    -- Target moved out of our weapon range.
    -- Go after him!
    ctx:state().g_bCanAttack = ctx:self():canAttack() -- DWARFCAMP.scr:193
    ctx:state().g_bAttacking = ctx:self():isAttacking() -- DWARFCAMP.scr:194
    if ctx:condition("g_bAttacking==TRUE") then -- DWARFCAMP.scr:196
        ctx:wait(0, 0.5, "DwarfOutOfRangeWait") -- DWARFCAMP.scr:197
    end -- DWARFCAMP.scr:198
    if ctx:condition("g_bCanAttack==TRUE") then -- DWARFCAMP.scr:200
        mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:201
    else -- DWARFCAMP.scr:202
        ctx:wait(0, 0.5, "DwarfOutOfRangeWait") -- DWARFCAMP.scr:203
    end -- DWARFCAMP.scr:204
    do return ctx:exit("") end -- DWARFCAMP.scr:206
end

script.labels["DwarfOutOfRangeWait"] = function(ctx)
    -- DWARFCAMP.scr:209
    -- We don't want to run after target
    -- until it's far enough away or we are
    -- ready to attack...
    if ctx:condition("g_hTarget==NULL") then -- DWARFCAMP.scr:216
        do return ctx:exit("TRUE") end -- DWARFCAMP.scr:217
    end -- DWARFCAMP.scr:218
    ctx:state().g_bAttacking = ctx:self():isAttacking() -- DWARFCAMP.scr:220
    if ctx:condition("g_bAttacking==TRUE") then -- DWARFCAMP.scr:222
        ctx:wait(0, 0.5, "DwarfOutOfRangeWait") -- DWARFCAMP.scr:223
        do return ctx:exit("TRUE") end -- DWARFCAMP.scr:224
    end -- DWARFCAMP.scr:225
    ctx:state().g_bCanAttack = ctx:self():canAttack() -- DWARFCAMP.scr:227
    if ctx:condition("g_bCanAttack==TRUE") then -- DWARFCAMP.scr:228
        ctx:state().g_bAttacking = ctx:self():isAttacking() -- DWARFCAMP.scr:229
        if ctx:condition("g_bAttacking==TRUE") then -- DWARFCAMP.scr:231
            do return ctx:exit("TRUE") end -- DWARFCAMP.scr:232
        end -- DWARFCAMP.scr:233
        mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:235
        do return ctx:exit("TRUE") end -- DWARFCAMP.scr:236
    end -- DWARFCAMP.scr:237
    -- randomly play a taunt animation...
    ctx:randomInt(0, 100, "g_nRandom") -- DWARFCAMP.scr:240
    if ctx:condition("g_nRandom < 30") then -- DWARFCAMP.scr:242
        if ctx:condition("g_nRandom < 15") then -- DWARFCAMP.scr:243
            ctx:self():taunt("DwarfAttackWaitAnimDone") -- DWARFCAMP.scr:244
        else -- DWARFCAMP.scr:245
            ctx:self():aware("DwarfAttackWaitAnimDone") -- DWARFCAMP.scr:246
        end -- DWARFCAMP.scr:247
        do return ctx:exit("TRUE") end -- DWARFCAMP.scr:248
    end -- DWARFCAMP.scr:249
    -- AIGetDistance g_hTarget, g_nDist1
    -- if ( g_nDist1 > 200 )		; if they are too far away...
    ctx:self():walkTo(ctx:object("g_hTarget")) -- DWARFCAMP.scr:254
    -- Wait 0, 0.5, DwarfOutOfRangeWalkingWait
    -- Exit TRUE
    -- endif
    -- Continue waiting....
    ctx:wait(0, 0.5, "DwarfOutOfRangeWait") -- DWARFCAMP.scr:261
    do return ctx:exit("") end -- DWARFCAMP.scr:263
end

script.labels["DwarfStuckDone"] = function(ctx)
    -- DWARFCAMP.scr:266
    -- This is called when a stuck animation
    -- has finished... We'll just re-attempt
    -- to run after our target...
    if ctx:condition("g_hTarget==NULL") then -- DWARFCAMP.scr:273
        mm9.gosub(script, ctx, "DwarfFindTarget") -- DWARFCAMP.scr:274
        do return ctx:exit("TRUE") end -- DWARFCAMP.scr:275
    end -- DWARFCAMP.scr:276
    -- for now, don't wait when stuck..just get another target
    mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:280
    do return ctx:exit("TRUE") end -- DWARFCAMP.scr:282
end

script.labels["DwarfOutOfRangeWalkingWait"] = function(ctx)
    -- DWARFCAMP.scr:286
    -- Once we start walking after target,
    -- we want to start running as soon as
    -- we are attack ready...
    ctx:state().g_bCanAttack = ctx:self():canAttack() -- DWARFCAMP.scr:294
    if ctx:condition("g_bCanAttack==TRUE") then -- DWARFCAMP.scr:295
        ctx:state().g_bAttacking = ctx:self():isAttacking() -- DWARFCAMP.scr:296
        if ctx:condition("g_bAttacking==TRUE") then -- DWARFCAMP.scr:298
            do return ctx:exit("TRUE") end -- DWARFCAMP.scr:299
        end -- DWARFCAMP.scr:300
        mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:302
        do return ctx:exit("TRUE") end -- DWARFCAMP.scr:303
    end -- DWARFCAMP.scr:304
    ctx:wait(0, 0.5, "DwarfOutOfRangeWait") -- DWARFCAMP.scr:306
    do return ctx:exit("") end -- DWARFCAMP.scr:308
end

script.labels["DwarfAttackWaitAnimDone"] = function(ctx)
    -- DWARFCAMP.scr:312
    mm9.gosub(script, ctx, "DwarfOutOfRangeWait") -- DWARFCAMP.scr:315
    do return ctx:exit("") end -- DWARFCAMP.scr:317
end

script.labels["DwarfObstacle"] = function(ctx)
    -- DWARFCAMP.scr:320
    ctx:getParam(0, "g_hObstacle") -- DWARFCAMP.scr:323
    ctx:state().g_sObstacleName = ctx:object("g_hObstacle"):className() -- DWARFCAMP.scr:324
    if ctx:condition("g_sObstacleName == g_sEnemyName") then -- DWARFCAMP.scr:326
        ctx:randomInt(0, 10, "g_nRandom") -- DWARFCAMP.scr:327
        if ctx:condition("g_nRandom > 3") then -- DWARFCAMP.scr:328
            ctx:set("g_hTarget", "g_hObstacle") -- DWARFCAMP.scr:329
            ctx:self():setTarget(ctx:object("g_hTarget")) -- DWARFCAMP.scr:330
            mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:331
            do return ctx:exit("TRUE") end -- DWARFCAMP.scr:333
        end -- DWARFCAMP.scr:334
    end -- DWARFCAMP.scr:335
    mm9.gosub(script, ctx, "BaseObstacle") -- DWARFCAMP.scr:337
    do return ctx:exit("") end -- DWARFCAMP.scr:339
end

script.labels["DwarfDeathDone"] = function(ctx)
    -- DWARFCAMP.scr:343
    -- Report death of dwarf to the director
    ctx:trigger("g_hCampDirector", "DwarfDeath") -- DWARFCAMP.scr:346
    do return ctx:exit("FALSE") end -- DWARFCAMP.scr:348
end

script.labels["Init"] = function(ctx)
    -- DWARFCAMP.scr:351
    ctx:state().g_hCampDirector = ctx:objectOrNil("CampDirector") -- DWARFCAMP.scr:354
    -- See if we already have a target (this would normally happen if
    -- the ai were running another script and then decided to start running
    -- this one...
    ctx:state().g_hTarget = ctx:self():target() -- DWARFCAMP.scr:360
    if ctx:condition("g_hTarget!=NULL") then -- DWARFCAMP.scr:362
        mm9.gosub(script, ctx, "BaseGoGetHim") -- DWARFCAMP.scr:363
    else -- DWARFCAMP.scr:364
        -- commented because I don't want dwarfs running out and killing at this time
        -- Wait 0.1, DwarfFindTarget
    end -- DWARFCAMP.scr:367
    do return ctx:exit("") end -- DWARFCAMP.scr:369
end

script.labels["DoNothing"] = function(ctx)
    -- DWARFCAMP.scr:372
    do return ctx:exit("TRUE") end -- DWARFCAMP.scr:374
end

script.labels["Main"] = function(ctx)
    -- DWARFCAMP.scr:377
    -- This routine is automatically run
    -- at script startup...
    ctx:state().g_sMyClassName = ctx:self():className() -- DWARFCAMP.scr:383
    mm9.gosub(script, ctx, "InitBase") -- DWARFCAMP.scr:385
    -- Setup our event handlers...
    -- Base callbacks
    ctx:onEvent("OnDamage", "BaseDamage") -- DWARFCAMP.scr:392
    ctx:onEvent("OnCongestion", "BaseCongestion") -- DWARFCAMP.scr:393
    ctx:onEvent("OnPathClear", "BasePathClear") -- DWARFCAMP.scr:394
    -- Dwarf script call backs
    ctx:onEvent("OnDamageDone", "DwarfDamageDone") -- DWARFCAMP.scr:397
    ctx:onEvent("OnAlert", "DwarfOnAlert") -- DWARFCAMP.scr:398
    ctx:onEvent("OnTargetDead", "DwarfTargetDead") -- DWARFCAMP.scr:399
    ctx:onEvent("OnAttackReady", "DwarfAttackReady") -- DWARFCAMP.scr:400
    ctx:onEvent("OnLostTarget", "DwarfOnLostTarget") -- DWARFCAMP.scr:401
    ctx:onEvent("OnDeathDone", "DwarfDeathDone") -- DWARFCAMP.scr:402
    ctx:onEvent("OnTargetOutOfRange", "DwarfTargetOutOfRange") -- DWARFCAMP.scr:403
    ctx:onEvent("OnStuckDone", "DwarfStuckDone") -- DWARFCAMP.scr:404
    ctx:onEvent("OnObstacle", "DwarfObstacle") -- DWARFCAMP.scr:405
    ctx:onEvent("OnFoundPlayer", "DoNothing") -- DWARFCAMP.scr:406
    ctx:state().g_bAlwaysRunToTarget = true -- DWARFCAMP.scr:408
    ctx:set("g_sEnemyName", "Zombie") -- DWARFCAMP.scr:409
    ctx:wait(0, 0.1, "Init") -- DWARFCAMP.scr:411
    do return ctx:exit("") end -- DWARFCAMP.scr:413
end

return script
