-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASERANGE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "Base.Inc" }

-- BaseRange.inc
-- Default range attack implementation for
-- base monsters.... (that have a range attack)
script.labels["BaseRangeGoGetHim"] = function(ctx)
    -- BASERANGE.inc:22
    ctx:command("gettime", "g_nTemp") -- BASERANGE.inc:25
    ctx:command("lastattacktime", "= 0") -- BASERANGE.inc:26
    ctx:command("canreachtarget", "g_bTemp") -- BASERANGE.inc:28
    if ctx:condition("g_bTemp==FALSE") then -- BASERANGE.inc:30
        do return ctx:exit("TRUE") end -- BASERANGE.inc:31
    end -- BASERANGE.inc:32
    -- Re-start the attack check clock so that we get some time to move a little...
    ctx:command("wait", "ATTACK_CHECK_WAIT, GO_AFTER_MIN_WAIT_TIME, BaseRangeAttackCheck") -- BASERANGE.inc:35
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BASERANGE.inc:37
    do return ctx:exit("") end -- BASERANGE.inc:39
end

script.labels["BaseRangeAttackDone"] = function(ctx)
    -- BASERANGE.inc:42
    -- If we haven't hit the target for a while,
    -- maybe try moving....
    if ctx:condition("g_hTarget==NULL") then -- BASERANGE.inc:49
        do return ctx:exit("FALSE") end -- BASERANGE.inc:50
    end -- BASERANGE.inc:51
    if ctx:condition("lastAttackTime!=0") then -- BASERANGE.inc:53
        ctx:command("gettime", "g_nTemp") -- BASERANGE.inc:54
        ctx:command("sub", "g_nTemp, TARGET_HIT_WAIT_TIME") -- BASERANGE.inc:55
        if ctx:condition("g_nTemp > lastAttackTime") then -- BASERANGE.inc:56
            if ctx:condition("g_nTemp > lastTargetHit") then -- BASERANGE.inc:57
                ctx:command("lastattacktime", "= 0") -- BASERANGE.inc:58
                ctx:command("lasttargethit", "= 0") -- BASERANGE.inc:59
                -- Move after him....
                mm9.gosub(script, ctx, "BaseRangeGoGetHim") -- BASERANGE.inc:61
                do return ctx:exit("TRUE") end -- BASERANGE.inc:62
            end -- BASERANGE.inc:63
        end -- BASERANGE.inc:64
    end -- BASERANGE.inc:65
    do return ctx:exit("FALSE") end -- BASERANGE.inc:67
end

script.labels["BaseDoRangeAttack"] = function(ctx)
    -- BASERANGE.inc:70
    -- Launch our range attack!
    ctx:command("g_bfighting", "= TRUE") -- BASERANGE.inc:76
    if ctx:condition("lastAttackTime==0") then -- BASERANGE.inc:78
        ctx:command("gettime", "lastAttackTime") -- BASERANGE.inc:79
    end -- BASERANGE.inc:80
    ctx:command("rangeattack", "BaseRangeAttackDone") -- BASERANGE.inc:82
    do return ctx:exit("TRUE") end -- BASERANGE.inc:84
end

script.labels["BaseRotationDoneRangeAttack"] = function(ctx)
    -- BASERANGE.inc:87
    mm9.gosub(script, ctx, "BaseDoRangeAttack") -- BASERANGE.inc:90
    do return ctx:exit("TRUE") end -- BASERANGE.inc:92
end

script.labels["BaseRangeMaybeAttack"] = function(ctx)
    -- BASERANGE.inc:95
    -- If we can range attack, we randomly
    -- decide to do so here...
    ctx:command("canattack", "g_bCanAttack") -- BASERANGE.inc:101
    if ctx:condition("g_bCanAttack==FALSE") then -- BASERANGE.inc:103
        do return ctx:exit("FALSE") end -- BASERANGE.inc:104
    end -- BASERANGE.inc:105
    ctx:command("g_ntemp", "= 0") -- BASERANGE.inc:107
    ctx:command("estimaterangeattackhit", "g_hObject") -- BASERANGE.inc:108
    if ctx:condition("g_hObject==NULL") then -- BASERANGE.inc:109
        ctx:command("add", "g_nTemp, 20") -- BASERANGE.inc:110
    else -- BASERANGE.inc:111
        if ctx:condition("g_hObject==g_hTarget") then -- BASERANGE.inc:112
            ctx:command("g_ntemp", "= 100") -- BASERANGE.inc:113
        else -- BASERANGE.inc:114
            ctx:command("isclass", "g_hObject,AIBase, g_bTemp") -- BASERANGE.inc:115
            if ctx:condition("g_bTemp==TRUE") then -- BASERANGE.inc:116
                ctx:command("g_ntemp", "= 0") -- BASERANGE.inc:117
            end -- BASERANGE.inc:118
        end -- BASERANGE.inc:119
    end -- BASERANGE.inc:120
    if ctx:condition("g_hObject!=g_hTarget") then -- BASERANGE.inc:122
        do return ctx:exit("TRUE") end -- BASERANGE.inc:123
    end -- BASERANGE.inc:124
    ctx:command("getrandomint", "0, 100, g_nRandom") -- BASERANGE.inc:126
    if ctx:condition("g_nRandom <= g_nTemp") then -- BASERANGE.inc:127
        mm9.gosub(script, ctx, "BaseDoRangeAttack") -- BASERANGE.inc:128
    end -- BASERANGE.inc:129
    do return ctx:exit("TRUE") end -- BASERANGE.inc:132
end

script.labels["BaseRangeAwareDone"] = function(ctx)
    -- BASERANGE.inc:136
    mm9.gosub(script, ctx, "ChaseTargetTick") -- BASERANGE.inc:139
    do return ctx:exit("") end -- BASERANGE.inc:142
end

script.labels["BaseRangeFoundPlayer"] = function(ctx)
    -- BASERANGE.inc:145
    ctx:getParam(0, "g_hTarget") -- BASERANGE.inc:149
    if ctx:condition("g_hTarget==0") then -- BASERANGE.inc:151
        -- This shouldn't happen, but you can't be too careful!
        do return ctx:exit("FALSE") end -- BASERANGE.inc:153
    end -- BASERANGE.inc:154
    ctx:command("target", "g_hTarget, false") -- BASERANGE.inc:156
    ctx:command("getrandomint", "0, 100, g_nRandom") -- BASERANGE.inc:158
    ctx:command("target", "g_hTarget, FALSE") -- BASERANGE.inc:160
    ctx:command("aware", "BaseRangeAwareDone") -- BASERANGE.inc:161
    do return ctx:exit("TRUE") end -- BASERANGE.inc:163
end

script.labels["BaseRangeOnProjectile"] = function(ctx)
    -- BASERANGE.inc:167
    -- p0	- hProjectile
    -- p1	- hLaunchedFrom
    -- p2	- dist
    ctx:getParam(0, "g_hObject") -- BASERANGE.inc:172
    ctx:getParam(1, "g_nTemp") -- BASERANGE.inc:173
    if ctx:condition("g_hObject==g_nTemp") then -- BASERANGE.inc:175
        -- Don't take these seriously...
        do return ctx:exit("") end -- BASERANGE.inc:179
    end -- BASERANGE.inc:180
    if ctx:condition("g_hAttacker!=NULL") then -- BASERANGE.inc:182
        ctx:command("breakobjectlink", "g_hAttacker") -- BASERANGE.inc:183
    end -- BASERANGE.inc:184
    ctx:getParam(1, "g_hAttacker") -- BASERANGE.inc:186
    mm9.gosub(script, ctx, "BaseSetupAttacker") -- BASERANGE.inc:188
    mm9.gosub(script, ctx, "IsAttackerValidTarget") -- BASERANGE.inc:189
    if ctx:condition("g_bTemp==FALSE") then -- BASERANGE.inc:191
        do return ctx:exit("") end -- BASERANGE.inc:192
    end -- BASERANGE.inc:193
    -- You're my new best friend!
    ctx:command("g_htarget", "= g_hAttacker") -- BASERANGE.inc:196
    ctx:command("target", "g_hTarget") -- BASERANGE.inc:197
    do return ctx:exit("") end -- BASERANGE.inc:199
end

script.labels["BaseRangeAttackCheck"] = function(ctx)
    -- BASERANGE.inc:203
    -- If we have a target, see if it's time
    -- to try to attack him....
    -- If he's within hand attack range,
    -- do that, otherwise shoot him!
    if ctx:condition("g_hTarget==NULL") then -- BASERANGE.inc:212
        do return mm9.gotoLabel(script, ctx, "BaseRangeAttackCheckDone") end -- BASERANGE.inc:213
    end -- BASERANGE.inc:214
    mm9.gosub(script, ctx, "BaseRangeMaybeAttack") -- BASERANGE.inc:216
end

script.labels["BaseRangeAttackCheckDone"] = function(ctx)
    -- BASERANGE.inc:218
    ctx:command("getrandomfloat", "1.3, 2.0, g_nRandom") -- BASERANGE.inc:219
    ctx:command("wait", "ATTACK_CHECK_WAIT, g_nRandom, BaseRangeAttackCheck") -- BASERANGE.inc:220
    do return ctx:exit("") end -- BASERANGE.inc:222
end

script.labels["ChaseTargetTick"] = function(ctx)
    -- BASERANGE.inc:225
    -- Decide if we need to try to go after
    -- the target...
    -- If we have a clear shot, don't bother moving
    -- otherwize, randomly decide if we should go
    -- find him...
    if ctx:condition("g_hTarget==NULL") then -- BASERANGE.inc:236
        do return mm9.gotoLabel(script, ctx, "ChaseTargetTickDone") end -- BASERANGE.inc:237
    end -- BASERANGE.inc:238
    ctx:command("aigetdistance", "g_hTarget, g_nDist1") -- BASERANGE.inc:240
    ctx:command("getstat", "g_hMyObject, RangeAttackRange, g_nTemp") -- BASERANGE.inc:242
    if ctx:condition("g_nDist1 > g_nTemp") then -- BASERANGE.inc:244
        mm9.gosub(script, ctx, "BaseRangeGoGetHim") -- BASERANGE.inc:245
        do return mm9.gotoLabel(script, ctx, "ChaseTargetTickDone") end -- BASERANGE.inc:246
    end -- BASERANGE.inc:247
    ctx:command("estimaterangeattackhit", "g_hObject") -- BASERANGE.inc:249
    ctx:command("g_btemp", "= 0") -- BASERANGE.inc:251
    if ctx:condition("g_hObject!=NULL") then -- BASERANGE.inc:253
        if ctx:condition("g_hObject!=g_hTarget") then -- BASERANGE.inc:254
            -- Go after them
            mm9.gosub(script, ctx, "BaseRangeGoGetHim") -- BASERANGE.inc:256
            do return mm9.gotoLabel(script, ctx, "ChaseTargetTickDone") end -- BASERANGE.inc:257
        end -- BASERANGE.inc:258
    end -- BASERANGE.inc:259
end

script.labels["ChaseTargetTickDone"] = function(ctx)
    -- BASERANGE.inc:261
    ctx:command("wait", "CHASE_TARGET_WAIT, 1.0, ChaseTargetTick") -- BASERANGE.inc:262
    do return ctx:exit("") end -- BASERANGE.inc:264
end

script.labels["ChangeTargetWait"] = function(ctx)
    -- BASERANGE.inc:267
    if ctx:condition("g_hTarget==NULL") then -- BASERANGE.inc:270
        do return mm9.gotoLabel(script, ctx, "ChangeTargetWaitDone") end -- BASERANGE.inc:271
    end -- BASERANGE.inc:272
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- BASERANGE.inc:274
    ctx:command("aigetdistance", "g_hTarget, g_nDist1") -- BASERANGE.inc:275
    ctx:command("findtargets", "hTargetArray,16,g_nTemp,g_nDist1,0") -- BASERANGE.inc:277
    if ctx:condition("g_nTemp==0") then -- BASERANGE.inc:279
        do return mm9.gotoLabel(script, ctx, "ChangeTargetWaitDone") end -- BASERANGE.inc:280
    end -- BASERANGE.inc:281
    ctx:command("arrayget", "hTargetArray, 0, g_hObject") -- BASERANGE.inc:283
    if ctx:condition("g_hObject==g_hTarget") then -- BASERANGE.inc:285
        if ctx:condition("g_nTemp==1") then -- BASERANGE.inc:286
            do return mm9.gotoLabel(script, ctx, "ChangeTargetWaitDone") end -- BASERANGE.inc:287
        end -- BASERANGE.inc:288
        ctx:command("arrayget", "hTargetArray, 1, g_hObject") -- BASERANGE.inc:289
    end -- BASERANGE.inc:290
    ctx:command("g_htarget", "= g_hObject") -- BASERANGE.inc:292
    ctx:command("target", "g_hTarget") -- BASERANGE.inc:293
end

script.labels["ChangeTargetWaitDone"] = function(ctx)
    -- BASERANGE.inc:295
    ctx:command("wait", "CHANGE_TARGET_WAIT, 1.5, ChangeTargetWait") -- BASERANGE.inc:297
    do return ctx:exit("") end -- BASERANGE.inc:299
end

script.labels["BaseRangeTargetHit"] = function(ctx)
    -- BASERANGE.inc:302
    -- p0 = hTarget
    -- p1 = damageAmt
    ctx:getParam(0, "g_hObject") -- BASERANGE.inc:308
    if ctx:condition("g_hObject!=g_hTarget") then -- BASERANGE.inc:309
        do return ctx:exit("") end -- BASERANGE.inc:310
    end -- BASERANGE.inc:311
    ctx:command("gettime", "lastTargetHit") -- BASERANGE.inc:313
    do return ctx:exit("") end -- BASERANGE.inc:315
end

script.labels["BaseRangeInit"] = function(ctx)
    -- BASERANGE.inc:318
    -- Be sure to call this in your Main!
    mm9.gosub(script, ctx, "InitBase") -- BASERANGE.inc:324
    ctx:command("onfoundplayer", "BaseRangeFoundPlayer") -- BASERANGE.inc:326
    ctx:command("onprojectile", "BaseRangeOnProjectile, 200") -- BASERANGE.inc:327
    ctx:command("ontargethit", "BaseRangeTargetHit") -- BASERANGE.inc:328
    ctx:command("wait", "ATTACK_CHECK_WAIT,  1.5, BaseRangeAttackCheck") -- BASERANGE.inc:330
    -- Note, we're replacing the base.inc chase target wait with
    -- our own...
    ctx:command("wait", "CHANGE_TARGET_WAIT, 3.0, ChangeTargetWait") -- BASERANGE.inc:336
    do return ctx:exit("") end -- BASERANGE.inc:339
end

return script
