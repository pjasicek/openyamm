-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ATTACK.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- attack.inc
-- John Machin
-- Attack script
-- Need to setup g_hTarget and call Init Attack to initiate
-- Setup attack stuff
script.labels["InitAttack"] = function(ctx)
    -- ATTACK.inc:21
    if ctx:condition("g_hTarget == NULL") then -- ATTACK.inc:23
        do return ctx:exit("FALSE") end -- ATTACK.inc:24
    end -- ATTACK.inc:25
    ctx:command("isattacking", "g_bAttacking") -- ATTACK.inc:27
    if ctx:condition("g_bAttacking==TRUE") then -- ATTACK.inc:29
        do return ctx:exit("TRUE") end -- ATTACK.inc:30
    end -- ATTACK.inc:31
    ctx:command("istargetinrange", "g_bInAttackRange") -- ATTACK.inc:33
    if ctx:condition("g_bInAttackRange==TRUE") then -- ATTACK.inc:35
        ctx:command("canattack", "g_bCanAttack") -- ATTACK.inc:36
        if ctx:condition("g_bCanAttack==TRUE") then -- ATTACK.inc:38
            mm9.gosub(script, ctx, "AttackReady") -- ATTACK.inc:39
        end -- ATTACK.inc:40
        do return ctx:exit("TRUE") end -- ATTACK.inc:42
    end -- ATTACK.inc:43
    -- if ( g_bFighting==TRUE )
    ctx:command("runto", "g_hTarget") -- ATTACK.inc:46
    -- else
    -- WalkTo g_hTarget
    -- endif
    do return ctx:exit("TRUE") end -- ATTACK.inc:51
end

script.labels["AttackReady"] = function(ctx)
    -- ATTACK.inc:54
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("set", "g_bFighting, TRUE") -- ATTACK.inc:61
    ctx:command("gettime", "g_nLastAttackTime") -- ATTACK.inc:63
    ctx:command("attack", "") -- ATTACK.inc:65
    do return ctx:exit("") end -- ATTACK.inc:67
end

script.labels["HandleTargetOutOfRange"] = function(ctx)
    -- ATTACK.inc:70
    -- Target moved out of our weapon range.
    -- Go after him!
    ctx:command("canattack", "g_bCanAttack") -- ATTACK.inc:77
    ctx:command("isattacking", "g_bAttacking") -- ATTACK.inc:78
    -- if ( g_bAttacking==TRUE )
    -- Wait 0.5, OutOfRangeWait
    -- endif
    -- if ( g_bCanAttack==TRUE )
    mm9.gosub(script, ctx, "InitAttack") -- ATTACK.inc:85
    -- else
    -- Wait 0.5, OutOfRangeWait
    -- endif
    do return ctx:exit("") end -- ATTACK.inc:90
end

script.labels["HandleLostTarget"] = function(ctx)
    -- ATTACK.inc:93
    -- We've lost the target, so let's go idle.
    ctx:command("set", "g_hTarget, NULL") -- ATTACK.inc:98
    ctx:command("set", "g_bFighting, FALSE") -- ATTACK.inc:99
    ctx:command("target", "NULL") -- ATTACK.inc:100
    ctx:command("setidle", "") -- ATTACK.inc:103
    do return ctx:exit("") end -- ATTACK.inc:105
end

script.labels["OutOfRangeWait"] = function(ctx)
    -- ATTACK.inc:109
    -- We don't want to run after target
    -- until it's far enough away or we are
    -- ready to attack...
    if ctx:condition("g_hTarget==NULL") then -- ATTACK.inc:116
        do return ctx:exit("TRUE") end -- ATTACK.inc:117
    end -- ATTACK.inc:118
    ctx:command("isattacking", "g_bAttacking") -- ATTACK.inc:120
    if ctx:condition("g_bAttacking==TRUE") then -- ATTACK.inc:122
        ctx:command("wait", "0.5, OutOfRangeWait") -- ATTACK.inc:123
        do return ctx:exit("TRUE") end -- ATTACK.inc:124
    end -- ATTACK.inc:125
    ctx:command("canattack", "g_bCanAttack") -- ATTACK.inc:127
    if ctx:condition("g_bCanAttack==TRUE") then -- ATTACK.inc:128
        -- gosub BaseMaybeRangeAttack
        ctx:command("isattacking", "g_bAttacking") -- ATTACK.inc:131
        if ctx:condition("g_bAttacking==TRUE") then -- ATTACK.inc:133
            do return ctx:exit("TRUE") end -- ATTACK.inc:134
        end -- ATTACK.inc:135
        mm9.gosub(script, ctx, "InitAttack") -- ATTACK.inc:137
        do return ctx:exit("TRUE") end -- ATTACK.inc:138
    end -- ATTACK.inc:139
    -- randomly play a taunt animation...
    -- GetRandomInt 0, 100, g_nRandom
    -- if ( g_nRandom < 30 )
    -- if ( g_nRandom < 15 )
    -- Taunt BaseAttackWaitAnimDone
    -- else
    -- Aware BaseAttackWaitAnimDone
    -- endif
    -- Exit TRUE
    -- endif
    -- AIGetDistance g_hTarget, g_nDist1
    -- if ( g_nDist1 > 200 )		; if they are too far away...
    -- WalkTo g_hTarget
    -- Wait 0.5, OutOfRangeWalkingWait
    -- Exit TRUE
    -- endif
    -- Continue waiting....
    ctx:command("wait", "0.5, OutOfRangeWait") -- ATTACK.inc:163
    do return ctx:exit("") end -- ATTACK.inc:165
end

script.labels["HandleAttackReady"] = function(ctx)
    -- ATTACK.inc:168
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("set", "g_bFighting, TRUE") -- ATTACK.inc:176
    ctx:command("gettime", "g_nLastAttackTime") -- ATTACK.inc:178
    ctx:command("attack", "") -- ATTACK.inc:180
    do return ctx:exit("") end -- ATTACK.inc:182
end

script.labels["HandleDamageDone"] = function(ctx)
    -- ATTACK.inc:185
    -- We were attacked, now we want to run
    -- after whoever attacked us!
    if ctx:condition("g_hAttacker==g_hMyObject") then -- ATTACK.inc:192
        do return ctx:exit("FALSE") end -- ATTACK.inc:193
    end -- ATTACK.inc:194
    ctx:command("isactor", "g_hAttacker, g_nTemp") -- ATTACK.inc:196
    if ctx:condition("g_nTemp==FALSE") then -- ATTACK.inc:198
        -- Not an actor, therefore
        -- never go after it...
        if ctx:condition("g_hTarget!=NULL") then -- ATTACK.inc:201
            mm9.gosub(script, ctx, "InitAttack") -- ATTACK.inc:202
            do return ctx:exit("TRUE") end -- ATTACK.inc:203
        else -- ATTACK.inc:204
            do return ctx:exit("FALSE") end -- ATTACK.inc:205
        end -- ATTACK.inc:206
    end -- ATTACK.inc:207
    if ctx:condition("g_hTarget==NULL") then -- ATTACK.inc:209
        ctx:command("set", "g_hTarget, g_hAttacker") -- ATTACK.inc:210
        ctx:command("set", "g_bFighting, TRUE") -- ATTACK.inc:211
    else -- ATTACK.inc:212
        ctx:command("istargetinrange", "g_bInAttackRange") -- ATTACK.inc:213
        if ctx:condition("g_hAttacker!=NULL") then -- ATTACK.inc:215
            if ctx:condition("g_hAttacker!=g_hTarget") then -- ATTACK.inc:216
                ctx:command("getclassname", "g_hAttacker, g_sTemp") -- ATTACK.inc:217
                if ctx:condition("g_sTemp!=Player") then -- ATTACK.inc:218
                    do return mm9.gotoLabel(script, ctx, "SkipTargetSwitch") end -- ATTACK.inc:219
                end -- ATTACK.inc:220
                -- 70% chance we'll switch to the damager
                ctx:command("set", "g_nTemp, 70") -- ATTACK.inc:222
                if ctx:condition("g_bInAttackRange==TRUE") then -- ATTACK.inc:223
                    -- we're already in attack range of our current target
                    -- so lower chances of switching
                    ctx:command("set", "g_nTemp, 10") -- ATTACK.inc:226
                end -- ATTACK.inc:227
                ctx:command("aigetdistance", "g_hTarget, g_nDist1") -- ATTACK.inc:229
                ctx:command("aigetdistance", "g_hAttacker, g_nDist2") -- ATTACK.inc:230
                if ctx:condition("g_nDist2 > g_nDist1") then -- ATTACK.inc:232
                    -- reduce odds even further...
                    ctx:command("divide", "g_nTemp, 2") -- ATTACK.inc:234
                end -- ATTACK.inc:235
                ctx:command("getrandomint", "0, 100, g_nRandom") -- ATTACK.inc:237
                if ctx:condition("g_nRandom < g_nTemp") then -- ATTACK.inc:238
                    -- Okay, we decided to switch our current target to the
                    -- attacker!
                    ctx:command("set", "g_hTarget, g_hAttacker") -- ATTACK.inc:243
                end -- ATTACK.inc:244
            end -- ATTACK.inc:245
        end -- ATTACK.inc:246
    end -- ATTACK.inc:247
end

script.labels["SkipTargetSwitch"] = function(ctx)
    -- ATTACK.inc:250
    if ctx:condition("g_hTarget==0") then -- ATTACK.inc:253
        -- FALSE means have the AI do its default handling of this event.
        do return ctx:exit("FALSE") end -- ATTACK.inc:254
    end -- ATTACK.inc:255
    -- Go after the Target...
    ctx:command("target", "g_hTarget") -- ATTACK.inc:259
    mm9.gosub(script, ctx, "InitAttack") -- ATTACK.inc:261
    do return ctx:exit("") end -- ATTACK.inc:263
end

script.labels["OutOfRangeWalkingWait"] = function(ctx)
    -- ATTACK.inc:266
    -- Once we start walking after target,
    -- we want to start running as soon as
    -- we are attack ready...
    ctx:command("canattack", "g_bCanAttack") -- ATTACK.inc:274
    if ctx:condition("g_bCanAttack==TRUE") then -- ATTACK.inc:275
        -- gosub BaseMaybeRangeAttack
        ctx:command("isattacking", "g_bAttacking") -- ATTACK.inc:277
        if ctx:condition("g_bAttacking==TRUE") then -- ATTACK.inc:279
            do return ctx:exit("TRUE") end -- ATTACK.inc:280
        end -- ATTACK.inc:281
        mm9.gosub(script, ctx, "InitAttack") -- ATTACK.inc:283
        do return ctx:exit("TRUE") end -- ATTACK.inc:284
    end -- ATTACK.inc:285
    ctx:command("wait", "0.5, OutOfRangeWait") -- ATTACK.inc:287
    do return ctx:exit("") end -- ATTACK.inc:289
end

script.labels["HandleDamage"] = function(ctx)
    -- ATTACK.inc:293
    -- p0 = hAttacker
    -- p1 = HitPoints
    -- p2 = DamageType
    ctx:getParam(0, "g_hAttacker") -- ATTACK.inc:301
    ctx:getParam(1, "g_nLastDamage") -- ATTACK.inc:302
    ctx:getParam(2, "g_lastDamageType") -- ATTACK.inc:303
    ctx:command("sendalert", "g_hAttacker") -- ATTACK.inc:305
    if ctx:condition("g_nLastDamage == 0") then -- ATTACK.inc:307
        mm9.gosub(script, ctx, "HandleDamageDone") -- ATTACK.inc:308
    end -- ATTACK.inc:309
    do return ctx:exit("FALSE") end -- ATTACK.inc:311
end

script.labels["HandlePathClear"] = function(ctx)
    -- ATTACK.inc:314
    if ctx:condition("g_hTarget!=NULL") then -- ATTACK.inc:317
        ctx:command("runto", "g_hTarget, 120, NearTarget") -- ATTACK.inc:318
    end -- ATTACK.inc:319
    do return ctx:exit("TRUE") end -- ATTACK.inc:321
end

script.labels["NearTarget"] = function(ctx)
    -- ATTACK.inc:324
    -- Only walk up to them if the fight hasn't
    -- started yet...
    if ctx:condition("g_bFighting!=TRUE") then -- ATTACK.inc:331
        ctx:command("walkto", "g_hTarget") -- ATTACK.inc:332
    end -- ATTACK.inc:333
    do return ctx:exit("") end -- ATTACK.inc:335
end

script.labels["HandleCongestion"] = function(ctx)
    -- ATTACK.inc:340
    -- If there is congestion in the way,
    -- start walking
    if ctx:condition("g_hTarget!=NULL") then -- ATTACK.inc:346
        ctx:command("walkto", "g_hTarget") -- ATTACK.inc:347
    end -- ATTACK.inc:348
    do return ctx:exit("TRUE") end -- ATTACK.inc:350
end

script.labels["HandleTargetDead"] = function(ctx)
    -- ATTACK.inc:353
    ctx:getParam(0, "g_nTemp") -- ATTACK.inc:356
    ctx:command("target", "NULL") -- ATTACK.inc:358
    ctx:command("set", "g_hTarget, NULL") -- ATTACK.inc:359
    if ctx:condition("g_nTemp==g_hMyObject") then -- ATTACK.inc:361
        -- We killed him!
        -- taunt him, and go home....
        ctx:command("taunt", "GoHome") -- ATTACK.inc:366
    else -- ATTACK.inc:367
        -- just go home...
        mm9.gosub(script, ctx, "GoHome") -- ATTACK.inc:369
    end -- ATTACK.inc:370
    do return ctx:exit("TRUE") end -- ATTACK.inc:372
end

script.labels["GoHome"] = function(ctx)
    -- ATTACK.inc:375
    -- Sends ai back to where it started
    -- NOTE: if we ge stuck on way back home,
    -- we will just stay there...
    -- for now, just go back into idle loop...
    ctx:command("setidle", "") -- ATTACK.inc:384
    -- Set g_nGoingHome, TRUE
    -- WalkToPos g_homeX, g_homeY, g_homeZ, BaseImHome
    do return ctx:exit("") end -- ATTACK.inc:389
end

return script
