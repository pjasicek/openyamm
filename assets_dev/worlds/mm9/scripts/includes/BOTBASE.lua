-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOTBASE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "botglobals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "botMove.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "botMission.Inc" }

-- botbase.inc
-- Jeff Leggett
-- Base functionality for bots...
script.labels["BB_AttackTarget"] = function(ctx)
    -- BOTBASE.inc:16
    -- Decide what to do, and do it...
    -- - Find target
    -- - If can attack, shoot at him
    -- - Decide what mode to go into
    ctx:command("set", "g_hObject, g_hTarget") -- BOTBASE.inc:27
    ctx:command("gettarget", "g_hTarget") -- BOTBASE.inc:28
    if ctx:condition("g_hTarget==NULL") then -- BOTBASE.inc:30
        if ctx:condition("g_hObject!=NULL") then -- BOTBASE.inc:31
            ctx:command("breakpoint", "") -- BOTBASE.inc:32
        end -- BOTBASE.inc:33
        do return ctx:exit("FALSE") end -- BOTBASE.inc:34
    end -- BOTBASE.inc:35
    ctx:command("isattacking", "g_bAttacking") -- BOTBASE.inc:37
    if ctx:condition("g_bAttacking==TRUE") then -- BOTBASE.inc:39
        do return ctx:exit("FALSE") end -- BOTBASE.inc:40
    end -- BOTBASE.inc:41
    ctx:command("istargetinrange", "g_bInAttackRange") -- BOTBASE.inc:43
    ctx:command("canattack", "g_bCanAttack") -- BOTBASE.inc:44
    if ctx:condition("g_bInAttackRange==TRUE") then -- BOTBASE.inc:46
    end -- BOTBASE.inc:48
    do return ctx:exit("") end -- BOTBASE.inc:50
end

script.labels["BB_OnDamage"] = function(ctx)
    -- BOTBASE.inc:55
    -- p0	- hDamager
    ctx:getParam(0, "g_hAttacker") -- BOTBASE.inc:60
    ctx:command("faceobject", "g_hAttacker") -- BOTBASE.inc:61
    do return ctx:exit("") end -- BOTBASE.inc:63
end

script.labels["BB_OnProjectile"] = function(ctx)
    -- BOTBASE.inc:66
    -- p0 - hProjectile
    -- p1 - hLaunchedFrom
    ctx:getParam(0, "hProjectile") -- BOTBASE.inc:72
    if ctx:condition("g_hTarget==NULL") then -- BOTBASE.inc:74
        ctx:getParam(1, "g_hTarget") -- BOTBASE.inc:75
        ctx:command("target", "g_hTarget, TRUE") -- BOTBASE.inc:76
        mm9.gosub(script, ctx, "BB_SetupAttack") -- BOTBASE.inc:77
    end -- BOTBASE.inc:78
    -- IsHeadingToward hProjectile, g_hMyObject, bHeadingToward
    -- if ( bHeadingToward==TRUE )
    -- gosub BE_AvoidProjectile
    -- endif
    do return ctx:exit("") end -- BOTBASE.inc:86
end

script.labels["BB_AttackDone"] = function(ctx)
    -- BOTBASE.inc:89
    -- Return TRUE so we don't go into idle
    -- mode...
    do return ctx:exit("TRUE") end -- BOTBASE.inc:95
end

script.labels["BB_AttackTick"] = function(ctx)
    -- BOTBASE.inc:98
    if ctx:condition("g_hTarget==NULL") then -- BOTBASE.inc:103
        mm9.gosub(script, ctx, "BB_ClearTarget") -- BOTBASE.inc:104
        do return ctx:exit("") end -- BOTBASE.inc:105
    end -- BOTBASE.inc:106
    ctx:command("attack", "BB_AttackDone") -- BOTBASE.inc:108
    ctx:command("add", "attackCount, 1") -- BOTBASE.inc:110
    if ctx:condition("attackCount < 5") then -- BOTBASE.inc:112
        ctx:command("set", "attackTime, 0.5") -- BOTBASE.inc:113
    else -- BOTBASE.inc:114
        ctx:command("set", "attackTime 0.8") -- BOTBASE.inc:115
        ctx:command("set", "attackCount, 0") -- BOTBASE.inc:116
    end -- BOTBASE.inc:117
    ctx:command("wait", "ATTACK_WAIT, attackTime, BB_AttackTick") -- BOTBASE.inc:119
    do return ctx:exit("") end -- BOTBASE.inc:121
end

script.labels["BB_SetupAttack"] = function(ctx)
    -- BOTBASE.inc:126
    mm9.gosub(script, ctx, "BB_AttackTick") -- BOTBASE.inc:129
    mm9.gosub(script, ctx, "BM_SetupEvade") -- BOTBASE.inc:130
    do return ctx:exit("") end -- BOTBASE.inc:132
end

script.labels["BB_FoundTarget"] = function(ctx)
    -- BOTBASE.inc:135
    -- We didn't have a target set, and a target
    -- appeared.....
    ctx:getParam(0, "g_hTarget") -- BOTBASE.inc:141
    ctx:command("target", "g_hTarget, TRUE") -- BOTBASE.inc:142
    mm9.gosub(script, ctx, "BB_SetupAttack") -- BOTBASE.inc:144
    do return ctx:exit("") end -- BOTBASE.inc:146
end

script.labels["BB_LostTarget"] = function(ctx)
    -- BOTBASE.inc:149
    mm9.gosub(script, ctx, "BB_ClearTarget") -- BOTBASE.inc:152
    do return ctx:exit("TRUE") end -- BOTBASE.inc:154
end

script.labels["BB_CancelAttack"] = function(ctx)
    -- BOTBASE.inc:158
    -- Clear out are target, etc..
    ctx:command("wait", "ATTACK_WAIT, 0, DoNothing") -- BOTBASE.inc:164
    do return ctx:exit("") end -- BOTBASE.inc:166
end

script.labels["BB_ClearTarget"] = function(ctx)
    -- BOTBASE.inc:169
    -- No more target, now maybe we want to
    -- continue on our current objective/mission
    ctx:command("stop", "") -- BOTBASE.inc:175
    ctx:command("target", "NULL") -- BOTBASE.inc:176
    ctx:command("set", "g_hTarget, NULL") -- BOTBASE.inc:177
    mm9.gosub(script, ctx, "BB_CancelAttack") -- BOTBASE.inc:178
    mm9.gosub(script, ctx, "BM_CancelEvade") -- BOTBASE.inc:179
    do return ctx:exit("") end -- BOTBASE.inc:181
end

script.labels["BB_TargetDead"] = function(ctx)
    -- BOTBASE.inc:184
    mm9.gosub(script, ctx, "BB_ClearTarget") -- BOTBASE.inc:187
    do return ctx:exit("") end -- BOTBASE.inc:189
end

script.labels["BB_MaybeSwitchTarget"] = function(ctx)
    -- BOTBASE.inc:192
    if ctx:condition("hLastAttacker!=g_hTarget") then -- BOTBASE.inc:197
        ctx:command("set", "g_hTarget, hLastAttacker") -- BOTBASE.inc:198
        ctx:command("target", "g_hTarget, TRUE") -- BOTBASE.inc:199
        mm9.gosub(script, ctx, "BB_SetupAttack") -- BOTBASE.inc:200
    end -- BOTBASE.inc:201
    do return ctx:exit("") end -- BOTBASE.inc:203
end

script.labels["BB_OnDamage"] = function(ctx)
    -- BOTBASE.inc:206
    ctx:getParam(0, "hLastAttacker") -- BOTBASE.inc:208
    mm9.gosub(script, ctx, "BB_MaybeSwitchTarget") -- BOTBASE.inc:210
    do return ctx:exit("FALSE") end -- BOTBASE.inc:213
end

script.labels["BotBaseInit"] = function(ctx)
    -- BOTBASE.inc:216
    -- You must call this in your :main routine...
    ctx:command("onfoundtarget", "BB_FoundTarget") -- BOTBASE.inc:222
    ctx:command("onlosttarget", "BB_LostTarget") -- BOTBASE.inc:223
    ctx:command("ontargetdead", "BB_TargetDead") -- BOTBASE.inc:224
    ctx:command("ondamage", "BB_OnDamage") -- BOTBASE.inc:225
    ctx:command("onprojectile", "BB_OnProjectile, 200") -- BOTBASE.inc:227
    ctx:command("gettarget", "g_hTarget") -- BOTBASE.inc:230
    ctx:command("getmyhandle", "g_hMyObject") -- BOTBASE.inc:232
    mm9.gosub(script, ctx, "BotMissInit") -- BOTBASE.inc:234
    -- TraceON
    do return ctx:exit("") end -- BOTBASE.inc:238
end

return script
