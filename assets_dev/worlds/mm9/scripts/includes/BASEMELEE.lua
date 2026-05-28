-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASEMELEE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 22, path = "basecrawl.inc" }
script.includes[#script.includes + 1] = { line = 23, path = "baseevade.inc" }

-- BaseMelee.inc
-- Jeff Leggett
-- 10/03/2001
-- Base script for melee monsters that can blend their
-- animations and therefore be capable of strafe attacks
-- along with basic evasive maneuvers..
-- Note:
-- This script is much cleaner and more modular
-- than base.inc.  It is also less of a frame-rate
-- hit due to the need for fewer constant TICKS.
-- Base.Inc should be phased out as soon as possible...
-- Uses basecrawl.inc for basic AI and builds on top of it
script.labels["TargetMoving"] = function(ctx)
    -- BASEMELEE.inc:34
    mm9.gosub(script, ctx, "TargetMoving") -- BASEMELEE.inc:37
    do return ctx:exit("") end -- BASEMELEE.inc:39
end

script.labels["TargetStill"] = function(ctx)
    -- BASEMELEE.inc:42
    -- if we're not strafing, just call parent which will
    -- stop us.
    -- If we are strafing, don't call parent so that we
    -- will continue to strafe...
    if ctx:condition("g_bStrafeAttack==FALSE") then -- BASEMELEE.inc:52
        mm9.gosub(script, ctx, "TargetStill") -- BASEMELEE.inc:53
    end -- BASEMELEE.inc:54
    do return ctx:exit("") end -- BASEMELEE.inc:56
end

script.labels["AttackObstacle"] = function(ctx)
    -- BASEMELEE.inc:59
    -- p0 - hObstacle
    -- if the obstacle is our target, then if they're not
    -- moving we'll want to stop...  If not, then just
    -- ignore the obstacle and our speed throttling will
    -- take over for us... (ie: exit TRUE)
    ctx:getParam(0, "g_hObject") -- BASEMELEE.inc:71
    if ctx:condition("g_hObject==g_hTarget") then -- BASEMELEE.inc:73
        mm9.gosub(script, ctx, "IsTargetMoving") -- BASEMELEE.inc:74
        if ctx:condition("g_bTemp==FALSE") then -- BASEMELEE.inc:76
            ctx:command("stop", "") -- BASEMELEE.inc:77
            do return ctx:exit("TRUE") end -- BASEMELEE.inc:78
        end -- BASEMELEE.inc:79
        do return ctx:exit("TRUE") end -- BASEMELEE.inc:81
    end -- BASEMELEE.inc:83
    do return ctx:exit("FALSE") end -- BASEMELEE.inc:85
end

script.labels["PostAttack"] = function(ctx)
    -- BASEMELEE.inc:89
    -- overloaded to potentially do a strafe attack...
    ctx:command("g_bstrafeattack", "= FALSE") -- BASEMELEE.inc:95
    mm9.gosub(script, ctx, "PostAttack") -- BASEMELEE.inc:97
    ctx:command("isturnbased", "g_bTemp") -- BASEMELEE.inc:99
    if ctx:condition("g_bTemp==TRUE") then -- BASEMELEE.inc:101
        do return ctx:exit("") end -- BASEMELEE.inc:102
    end -- BASEMELEE.inc:103
    ctx:command("ismoving", "g_bTemp") -- BASEMELEE.inc:105
    if ctx:condition("g_bTemp==TRUE") then -- BASEMELEE.inc:107
        mm9.gosub(script, ctx, "IsTargetMoving") -- BASEMELEE.inc:108
        if ctx:condition("g_bTemp==FALSE") then -- BASEMELEE.inc:109
            ctx:command("getrandomint", "0, 100, g_nRandom") -- BASEMELEE.inc:110
            if ctx:condition("g_nRandom < g_nStrafeAttackPct") then -- BASEMELEE.inc:111
                ctx:command("g_bpickdir", "= TRUE") -- BASEMELEE.inc:112
                ctx:command("target", "g_hTarget,TRUE") -- BASEMELEE.inc:113
                mm9.gosub(script, ctx, "BE_AttackStrafe") -- BASEMELEE.inc:114
                ctx:command("g_bpickdir", "= TRUE") -- BASEMELEE.inc:115
                ctx:command("g_bstrafeattack", "= TRUE") -- BASEMELEE.inc:116
            end -- BASEMELEE.inc:117
        end -- BASEMELEE.inc:118
    end -- BASEMELEE.inc:119
    do return ctx:exit("") end -- BASEMELEE.inc:121
end

script.labels["ShouldEvade"] = function(ctx)
    -- BASEMELEE.inc:124
    -- Returns TRUE or FALSE in g_bTemp
    ctx:command("getrandomint", "0,100,g_nRandom") -- BASEMELEE.inc:129
    ctx:command("getstat", "g_hMyObject, EvadeChance, g_nEvadeChance") -- BASEMELEE.inc:131
    -- IsTurnBased g_bTemp
    -- if ( g_bTemp==TRUE )
    -- g_bTemp = FALSE
    -- exit
    -- endif
    if ctx:condition("g_nRandom < g_nEvadeChance") then -- BASEMELEE.inc:139
        ctx:command("g_btemp", "= TRUE") -- BASEMELEE.inc:140
    else -- BASEMELEE.inc:141
        ctx:command("g_btemp", "= FALSE") -- BASEMELEE.inc:142
    end -- BASEMELEE.inc:143
    do return ctx:exit("") end -- BASEMELEE.inc:145
end

script.labels["CancelEvade"] = function(ctx)
    -- BASEMELEE.inc:148
    mm9.gosub(script, ctx, "BaseEvadeStop") -- BASEMELEE.inc:151
    mm9.gosub(script, ctx, "AggressiveStart") -- BASEMELEE.inc:152
    do return ctx:exit("") end -- BASEMELEE.inc:154
end

script.labels["DoEvade"] = function(ctx)
    -- BASEMELEE.inc:157
    -- Backup and/or strafe a little...
    ctx:command("getstat", "g_hMyObject,RecoveryTime,g_nEvadeTime") -- BASEMELEE.inc:163
    mm9.gosub(script, ctx, "SpeedThrottleStop") -- BASEMELEE.inc:164
    mm9.gosub(script, ctx, "AggressiveStop") -- BASEMELEE.inc:165
    ctx:command("ontargetbeyonddist", "g_nMaxEvadeDist, CancelEvade") -- BASEMELEE.inc:166
    mm9.gosub(script, ctx, "BaseEvadeStart") -- BASEMELEE.inc:168
    -- Mul g_nTemp, 0.8
    ctx:command("g_ntemp", "= g_nEvadeTime") -- BASEMELEE.inc:172
    ctx:command("g_ntemp", "= 2") -- BASEMELEE.inc:173
    if ctx:condition("g_nTemp < 1") then -- BASEMELEE.inc:174
        ctx:command("g_ntemp", "= 1") -- BASEMELEE.inc:175
    end -- BASEMELEE.inc:176
    ctx:command("wait", "AGGRESSIVE_WAIT, g_nTemp, CancelEvade") -- BASEMELEE.inc:179
    do return ctx:exit("") end -- BASEMELEE.inc:181
end

script.labels["BackpedalTauntDone"] = function(ctx)
    -- BASEMELEE.inc:184
    mm9.gosub(script, ctx, "AttackDone") -- BASEMELEE.inc:187
    do return ctx:exit("") end -- BASEMELEE.inc:188
end

script.labels["AttackBackpedalDone"] = function(ctx)
    -- BASEMELEE.inc:191
    mm9.gosub(script, ctx, "BaseEvadeStop") -- BASEMELEE.inc:193
    ctx:command("getrandomint", "0,100,g_nRandom") -- BASEMELEE.inc:195
    -- Don't waste time in turn based mode.....
    ctx:command("isturnbased", "g_bTemp") -- BASEMELEE.inc:200
    if ctx:condition("g_bTemp==TRUE") then -- BASEMELEE.inc:201
        ctx:command("g_nrandom", "= 99") -- BASEMELEE.inc:202
    end -- BASEMELEE.inc:203
    -- 40% of time, do our taunt here...
    if ctx:condition("g_nRandom < 40") then -- BASEMELEE.inc:208
        ctx:command("taunt", "BackpedalTauntDone") -- BASEMELEE.inc:209
    else -- BASEMELEE.inc:210
        mm9.gosub(script, ctx, "AttackDone") -- BASEMELEE.inc:211
    end -- BASEMELEE.inc:212
    do return ctx:exit("") end -- BASEMELEE.inc:214
end

script.labels["AttackDone"] = function(ctx)
    -- BASEMELEE.inc:217
    -- overloaded to potentially back/strafe away from target
    mm9.gosub(script, ctx, "ShouldEvade") -- BASEMELEE.inc:223
    if ctx:condition("g_bTemp==FALSE") then -- BASEMELEE.inc:225
        ctx:command("g_bevading", "= FALSE") -- BASEMELEE.inc:226
        -- if we did a strafe attack, but we don't want to
        -- evade, then, just backoff...
        if ctx:condition("g_bStrafeAttack==TRUE") then -- BASEMELEE.inc:231
            mm9.gosub(script, ctx, "BE_BackPedal") -- BASEMELEE.inc:232
            ctx:command("wait", "AGGRESSIVE_WAIT, 0.3, AttackBackpedalDone") -- BASEMELEE.inc:233
            do return ctx:exit("") end -- BASEMELEE.inc:234
        end -- BASEMELEE.inc:235
        mm9.gosub(script, ctx, "AttackDone") -- BASEMELEE.inc:237
    else -- BASEMELEE.inc:238
        mm9.gosub(script, ctx, "AttackTickCancel") -- BASEMELEE.inc:239
        mm9.gosub(script, ctx, "DoEvade") -- BASEMELEE.inc:240
    end -- BASEMELEE.inc:241
    do return ctx:exit("") end -- BASEMELEE.inc:243
end

script.labels["BE_AttackStrafeObstacle"] = function(ctx)
    -- BASEMELEE.inc:246
    -- if we have an obstacle and decide to backup,
    -- go ahead and cancel speed throttle...
    mm9.gosub(script, ctx, "BE_AttackStrafeObstacle") -- BASEMELEE.inc:253
    if ctx:condition("g_bTemp==TRUE") then -- BASEMELEE.inc:255
        mm9.gosub(script, ctx, "SpeedThrottleStop") -- BASEMELEE.inc:256
    end -- BASEMELEE.inc:257
    do return ctx:exit("") end -- BASEMELEE.inc:259
end

script.labels["BaseInit"] = function(ctx)
    -- BASEMELEE.inc:263
    mm9.gosub(script, ctx, "BaseCrawlInit") -- BASEMELEE.inc:266
    ctx:command("getstat", "g_hMyObject, StrafeAttackPct, g_nStrafeAttackPct") -- BASEMELEE.inc:268
    ctx:command("getstat", "g_hMyObject, CanBlendAnim, g_bCanBlendAnim") -- BASEMELEE.inc:269
    ctx:command("getstat", "g_hMyObject, CanHeadTurn, g_bCanHeadTurn") -- BASEMELEE.inc:270
    do return ctx:exit("") end -- BASEMELEE.inc:272
end

return script
