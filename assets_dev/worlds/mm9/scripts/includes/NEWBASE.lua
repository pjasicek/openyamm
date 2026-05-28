-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NEWBASE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 19, path = "basecrawl.inc" }
script.includes[#script.includes + 1] = { line = 20, path = "baseevade.inc" }

-- NewBase.inc
-- Jeff Leggett
-- 10/03/2001
-- New and improved base script.
-- Cleaner
-- More modular
-- Makes more use of function overloading...
-- Additions to basecrawl.inc:
-- strafe attacks
-- evasive maneuvers
script.labels["TargetMoving"] = function(ctx)
    -- NEWBASE.inc:31
    mm9.gosub(script, ctx, "TargetMoving") -- NEWBASE.inc:34
    do return ctx:exit("") end -- NEWBASE.inc:36
end

script.labels["TargetStill"] = function(ctx)
    -- NEWBASE.inc:39
    -- if we're not strafing, just call parent which will
    -- stop us.
    -- If we are strafing, don't call parent so that we
    -- will continue to strafe...
    if ctx:condition("g_bStrafeAttack==FALSE") then -- NEWBASE.inc:49
        mm9.gosub(script, ctx, "TargetStill") -- NEWBASE.inc:50
    end -- NEWBASE.inc:51
    do return ctx:exit("") end -- NEWBASE.inc:53
end

script.labels["AttackObstacle"] = function(ctx)
    -- NEWBASE.inc:56
    -- p0 - hObstacle
    -- if the obstacle is our target, then if they're not
    -- moving we'll want to stop...  If not, then just
    -- ignore the obstacle and our speed throttling will
    -- take over for us... (ie: exit TRUE)
    ctx:getParam(0, "g_hObject") -- NEWBASE.inc:68
    if ctx:condition("g_hObject==g_hTarget") then -- NEWBASE.inc:70
        mm9.gosub(script, ctx, "IsTargetMoving") -- NEWBASE.inc:71
        if ctx:condition("g_bTemp==FALSE") then -- NEWBASE.inc:73
            ctx:command("stop", "") -- NEWBASE.inc:74
            do return ctx:exit("TRUE") end -- NEWBASE.inc:75
        end -- NEWBASE.inc:76
        do return ctx:exit("TRUE") end -- NEWBASE.inc:78
    end -- NEWBASE.inc:80
    do return ctx:exit("FALSE") end -- NEWBASE.inc:82
end

script.labels["PostAttack"] = function(ctx)
    -- NEWBASE.inc:86
    -- overloaded to potentially do a strafe attack...
    ctx:command("g_bstrafeattack", "= FALSE") -- NEWBASE.inc:92
    mm9.gosub(script, ctx, "PostAttack") -- NEWBASE.inc:94
    mm9.gosub(script, ctx, "IsTargetMoving") -- NEWBASE.inc:95
    if ctx:condition("g_bTemp==FALSE") then -- NEWBASE.inc:97
        ctx:command("getrandomint", "0, 100, g_nRandom") -- NEWBASE.inc:99
        if ctx:condition("g_nRandom < g_nStrafeAttackPct") then -- NEWBASE.inc:101
            ctx:command("g_bpickdir", "= TRUE") -- NEWBASE.inc:102
            mm9.gosub(script, ctx, "BE_AttackStrafe") -- NEWBASE.inc:103
            ctx:command("g_bpickdir", "= TRUE") -- NEWBASE.inc:104
            ctx:command("g_bstrafeattack", "= TRUE") -- NEWBASE.inc:105
        end -- NEWBASE.inc:106
    end -- NEWBASE.inc:107
    do return ctx:exit("") end -- NEWBASE.inc:109
end

script.labels["ShouldEvade"] = function(ctx)
    -- NEWBASE.inc:112
    -- Returns TRUE or FALSE in g_bTemp
    ctx:command("getrandomint", "0,100,g_nRandom") -- NEWBASE.inc:117
    ctx:command("getstat", "g_hMyObject, EvadeChance, g_nEvadeChance") -- NEWBASE.inc:119
    if ctx:condition("g_nRandom < g_nEvadeChance") then -- NEWBASE.inc:121
        ctx:command("g_btemp", "= TRUE") -- NEWBASE.inc:122
    else -- NEWBASE.inc:123
        ctx:command("g_btemp", "= FALSE") -- NEWBASE.inc:124
    end -- NEWBASE.inc:125
    do return ctx:exit("") end -- NEWBASE.inc:127
end

script.labels["CancelEvade"] = function(ctx)
    -- NEWBASE.inc:130
    mm9.gosub(script, ctx, "BaseEvadeStop") -- NEWBASE.inc:133
    mm9.gosub(script, ctx, "AggressiveStart") -- NEWBASE.inc:134
    do return ctx:exit("") end -- NEWBASE.inc:136
end

script.labels["DoEvade"] = function(ctx)
    -- NEWBASE.inc:139
    -- Backup and/or strafe a little...
    ctx:command("getstat", "g_hMyObject,RecoveryTime,g_nEvadeTime") -- NEWBASE.inc:145
    mm9.gosub(script, ctx, "SpeedThrottleStop") -- NEWBASE.inc:146
    mm9.gosub(script, ctx, "AggressiveStop") -- NEWBASE.inc:147
    ctx:command("ontargetbeyonddist", "g_nMaxEvadeDist, CancelEvade") -- NEWBASE.inc:148
    mm9.gosub(script, ctx, "BaseEvadeStart") -- NEWBASE.inc:150
    -- Mul g_nTemp, 0.8
    ctx:command("g_ntemp", "= g_nEvadeTime") -- NEWBASE.inc:154
    ctx:command("g_ntemp", "= 2") -- NEWBASE.inc:155
    if ctx:condition("g_nTemp < 1") then -- NEWBASE.inc:156
        ctx:command("g_ntemp", "= 1") -- NEWBASE.inc:157
    end -- NEWBASE.inc:158
    ctx:command("wait", "AGGRESSIVE_WAIT, g_nTemp, CancelEvade") -- NEWBASE.inc:161
    do return ctx:exit("") end -- NEWBASE.inc:163
end

script.labels["BackpedalTauntDone"] = function(ctx)
    -- NEWBASE.inc:166
    mm9.gosub(script, ctx, "AttackDone") -- NEWBASE.inc:169
    do return ctx:exit("") end -- NEWBASE.inc:170
end

script.labels["AttackBackpedalDone"] = function(ctx)
    -- NEWBASE.inc:173
    mm9.gosub(script, ctx, "BaseEvadeStop") -- NEWBASE.inc:175
    ctx:command("taunt", "BackpedalTauntDone") -- NEWBASE.inc:176
    do return ctx:exit("") end -- NEWBASE.inc:178
end

script.labels["AttackDone"] = function(ctx)
    -- NEWBASE.inc:181
    -- overloaded to potentially back/strafe away from target
    mm9.gosub(script, ctx, "ShouldEvade") -- NEWBASE.inc:187
    if ctx:condition("g_bTemp==FALSE") then -- NEWBASE.inc:189
        ctx:command("g_bevading", "= FALSE") -- NEWBASE.inc:190
        -- if we did a strafe attack, but we don't want to
        -- evade, then, just backoff...
        if ctx:condition("g_bStrafeAttack==TRUE") then -- NEWBASE.inc:195
            mm9.gosub(script, ctx, "BE_BackPedal") -- NEWBASE.inc:196
            ctx:command("wait", "AGGRESSIVE_WAIT, 0.3, AttackBackpedalDone") -- NEWBASE.inc:197
            do return ctx:exit("") end -- NEWBASE.inc:198
        end -- NEWBASE.inc:199
        mm9.gosub(script, ctx, "AttackDone") -- NEWBASE.inc:201
    else -- NEWBASE.inc:202
        mm9.gosub(script, ctx, "AttackTickCancel") -- NEWBASE.inc:203
        mm9.gosub(script, ctx, "DoEvade") -- NEWBASE.inc:204
    end -- NEWBASE.inc:205
    do return ctx:exit("") end -- NEWBASE.inc:207
end

script.labels["BE_AttackStrafeObstacle"] = function(ctx)
    -- NEWBASE.inc:210
    -- if we have an obstacle and decide to backup,
    -- go ahead and cancel speed throttle...
    mm9.gosub(script, ctx, "BE_AttackStrafeObstacle") -- NEWBASE.inc:217
    if ctx:condition("g_bTemp==TRUE") then -- NEWBASE.inc:219
        mm9.gosub(script, ctx, "SpeedThrottleStop") -- NEWBASE.inc:220
    end -- NEWBASE.inc:221
    do return ctx:exit("") end -- NEWBASE.inc:223
end

script.labels["BaseInit"] = function(ctx)
    -- NEWBASE.inc:227
    mm9.gosub(script, ctx, "BaseCrawlInit") -- NEWBASE.inc:230
    ctx:command("getstat", "g_hMyObject, StrafeAttackPct, g_nStrafeAttackPct") -- NEWBASE.inc:232
    ctx:command("getstat", "g_hMyObject, CanBlendAnim, g_bCanBlendAnim") -- NEWBASE.inc:233
    ctx:command("getstat", "g_hMyObject, CanHeadTurn, g_bCanHeadTurn") -- NEWBASE.inc:234
    do return ctx:exit("") end -- NEWBASE.inc:236
end

return script
