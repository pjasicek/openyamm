-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LOBBER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 17, path = "AIGlobals.inc" }

-- Lobber.Scr
-- Jeff Leggett
-- 07/31/2001
-- The lobber creature has 2 attacks.  One attack spawns out
-- the LobberPod creature.  The 2nd attack shoots a green
-- and nasty poison-looking projectile.
-- When the lobber dies, it falls to the floor.
-- edited by Bones 9/11/02
-- TELP Patch 1.3 -- repositions Frosgard IceLobber
script.labels["DoNothing"] = function(ctx)
    -- LOBBER.scr:39
    do return ctx:exit("") end -- LOBBER.scr:42
end

script.labels["TargetSearchOn"] = function(ctx)
    -- LOBBER.scr:45
    ctx:command("getrandomfloat", "5, 15, g_nRandom") -- LOBBER.scr:48
    ctx:command("wait", "TARGET_SEARCH_WAIT,g_nRandom,DoTargetSearch") -- LOBBER.scr:49
    do return ctx:exit("") end -- LOBBER.scr:50
end

script.labels["DoTargetSearch"] = function(ctx)
    -- LOBBER.scr:53
    ctx:command("getfacedir", "g_hMyObject, g_dirX,g_dirY,g_dirZ") -- LOBBER.scr:56
    ctx:command("g_diry", "= 0") -- LOBBER.scr:58
    ctx:command("getrandomfloat", "20, 120, g_nRandom") -- LOBBER.scr:60
    ctx:command("getrandomint", "0,1,g_nTemp") -- LOBBER.scr:62
    if ctx:condition("g_nTemp==1") then -- LOBBER.scr:64
        ctx:command("mul", "g_nRandom,-1") -- LOBBER.scr:65
    end -- LOBBER.scr:66
    ctx:command("rotatedir", "g_dirX,g_dirY,g_dirZ,g_nRandom") -- LOBBER.scr:68
    ctx:command("facedir", "g_dirX,g_dirY,g_dirZ,180,DoNothing") -- LOBBER.scr:69
    mm9.gosub(script, ctx, "TargetSearchOn") -- LOBBER.scr:71
    do return ctx:exit("") end -- LOBBER.scr:73
end

script.labels["TargetSearchCancel"] = function(ctx)
    -- LOBBER.scr:76
    ctx:command("wait", "TARGET_SEARCH_WAIT,0,DoNothing") -- LOBBER.scr:78
    do return ctx:exit("") end -- LOBBER.scr:80
end

script.labels["LaunchPodDone"] = function(ctx)
    -- LOBBER.scr:84
    do return ctx:exit("") end -- LOBBER.scr:87
end

script.labels["StartLobberLaunch"] = function(ctx)
    -- LOBBER.scr:90
    ctx:command("gettime", "g_nLastAttackTime") -- LOBBER.scr:93
    ctx:command("playanim", "LaunchPod,LaunchPodDone") -- LOBBER.scr:94
    do return ctx:exit("") end -- LOBBER.scr:96
end

script.labels["StartAttackCheck"] = function(ctx)
    -- LOBBER.scr:99
    ctx:command("wait", "ATTACK_CHECK_WAIT, 1, AttackCheck") -- LOBBER.scr:101
    do return ctx:exit("") end -- LOBBER.scr:103
end

script.labels["StopAttackCheck"] = function(ctx)
    -- LOBBER.scr:106
    ctx:command("wait", "ATTACK_CHECK_WAIT, 0, DoNothing") -- LOBBER.scr:108
    do return ctx:exit("") end -- LOBBER.scr:110
end

script.labels["ClearTarget"] = function(ctx)
    -- LOBBER.scr:113
    ctx:command("target", "NULL") -- LOBBER.scr:115
    ctx:command("g_htarget", "=\tNULL") -- LOBBER.scr:116
    mm9.gosub(script, ctx, "StopAttackCheck") -- LOBBER.scr:117
    mm9.gosub(script, ctx, "TargetSearchOn") -- LOBBER.scr:118
    do return ctx:exit("") end -- LOBBER.scr:119
end

script.labels["AttackCheck"] = function(ctx)
    -- LOBBER.scr:122
    -- Decide whether we want to Lob another LobPod, or do a range
    -- attack....
    ctx:command("wait", "ATTACK_CHECK_WAIT, 1, AttackCheck") -- LOBBER.scr:129
    if ctx:condition("g_hTarget==NULL") then -- LOBBER.scr:131
        do return ctx:exit("") end -- LOBBER.scr:132
    end -- LOBBER.scr:133
    ctx:command("g_bclearshot", "= FALSE") -- LOBBER.scr:135
    ctx:command("isclearshot", "g_hTarget, g_bClearShot") -- LOBBER.scr:136
    ctx:command("gettime", "g_nTemp") -- LOBBER.scr:138
    ctx:command("sub", "g_nTemp,g_nLastAttackTime") -- LOBBER.scr:140
    if ctx:condition("g_nTemp > 30") then -- LOBBER.scr:142
        mm9.gosub(script, ctx, "ClearTarget") -- LOBBER.scr:143
        do return ctx:exit("") end -- LOBBER.scr:144
    end -- LOBBER.scr:145
    ctx:command("gettime", "g_nTemp") -- LOBBER.scr:147
    ctx:command("sub", "g_nTemp,g_lastLobberLaunch") -- LOBBER.scr:149
    if ctx:condition("g_lastLobberLaunch==0") then -- LOBBER.scr:151
        ctx:command("g_ntemp", "= MAX_LOBBER_LAUNCH_WAIT") -- LOBBER.scr:152
    end -- LOBBER.scr:153
    if ctx:condition("g_nTemp > MIN_LOBBER_LAUNCH_WAIT") then -- LOBBER.scr:155
        ctx:command("getstat", "g_hMyObject, CanLob, g_bTemp") -- LOBBER.scr:156
        if ctx:condition("g_bTemp==TRUE") then -- LOBBER.scr:158
            mm9.gosub(script, ctx, "StartLobberLaunch") -- LOBBER.scr:159
            do return ctx:exit("") end -- LOBBER.scr:160
        end -- LOBBER.scr:161
    end -- LOBBER.scr:162
    ctx:command("canattack", "g_bCanAttack") -- LOBBER.scr:164
    if ctx:condition("g_bCanAttack==FALSE") then -- LOBBER.scr:166
        do return ctx:exit("") end -- LOBBER.scr:167
    end -- LOBBER.scr:168
    ctx:command("aigetdistance", "g_hTarget, g_nDist1") -- LOBBER.scr:170
    if ctx:condition("g_nDist1 > g_attackRange") then -- LOBBER.scr:172
        do return ctx:exit("") end -- LOBBER.scr:173
    end -- LOBBER.scr:174
    if ctx:condition("g_bClearShot==FALSE") then -- LOBBER.scr:176
        -- Randomly decide if we should target them
        -- anyway...
        ctx:command("getrandomint", "0,100,g_nRandom") -- LOBBER.scr:179
        if ctx:condition("g_nRandom < NO_CLEAR_SHOT_IGNORE_CHANCE") then -- LOBBER.scr:180
            do return ctx:exit("") end -- LOBBER.scr:181
        end -- LOBBER.scr:182
    end -- LOBBER.scr:183
    ctx:command("gettime", "g_nLastAttackTime") -- LOBBER.scr:185
    ctx:command("rangeattack", "") -- LOBBER.scr:186
    do return ctx:exit("") end -- LOBBER.scr:188
end

script.labels["AwareDone"] = function(ctx)
    -- LOBBER.scr:191
    -- We've done our Aware... Now begin the attacks!
    mm9.gosub(script, ctx, "StartAttackCheck") -- LOBBER.scr:197
    do return ctx:exit("") end -- LOBBER.scr:199
end

script.labels["FoundTarget"] = function(ctx)
    -- LOBBER.scr:202
    -- Get him!!!!
    ctx:getParam(0, "g_hTarget") -- LOBBER.scr:208
    if ctx:condition("g_hTarget==0") then -- LOBBER.scr:210
        -- This shouldn't happen, but you can't be too careful!
        do return ctx:exit("FALSE") end -- LOBBER.scr:212
    end -- LOBBER.scr:213
    mm9.gosub(script, ctx, "TargetSearchCancel") -- LOBBER.scr:215
    ctx:command("sendalert", "g_hTarget") -- LOBBER.scr:216
    ctx:command("gettime", "g_nLastAttackTime") -- LOBBER.scr:218
    ctx:command("target", "g_hTarget, TRUE") -- LOBBER.scr:219
    ctx:command("aware", "AwareDone") -- LOBBER.scr:220
    do return ctx:exit("") end -- LOBBER.scr:222
end

script.labels["TargetDead"] = function(ctx)
    -- LOBBER.scr:225
    -- OK, go back into idle mode...
    ctx:command("target", "NULL") -- LOBBER.scr:231
    ctx:command("set", "g_hTarget, NULL") -- LOBBER.scr:232
    -- cprint LOBBER TARGET DEAD!!
    mm9.gosub(script, ctx, "StopAttackCheck") -- LOBBER.scr:235
    ctx:command("setidle", "") -- LOBBER.scr:236
    mm9.gosub(script, ctx, "TargetSearchOn") -- LOBBER.scr:238
    do return ctx:exit("TRUE") end -- LOBBER.scr:240
end

script.labels["Alert"] = function(ctx)
    -- LOBBER.scr:243
    if ctx:condition("g_hTarget!=NULL") then -- LOBBER.scr:246
        do return ctx:exit("") end -- LOBBER.scr:247
    end -- LOBBER.scr:248
    ctx:getParam(1, "g_hTarget") -- LOBBER.scr:250
    ctx:command("isfriend", "g_hTarget, g_bTemp") -- LOBBER.scr:252
    if ctx:condition("g_bTemp==TRUE") then -- LOBBER.scr:254
        do return ctx:exit("FALSE") end -- LOBBER.scr:255
    end -- LOBBER.scr:256
    ctx:command("target", "g_hTarget, TRUE") -- LOBBER.scr:258
    ctx:command("aware", "AwareDone") -- LOBBER.scr:259
    do return ctx:exit("TRUE") end -- LOBBER.scr:260
end

script.labels["LostTarget"] = function(ctx)
    -- LOBBER.scr:264
    -- clear target..
    ctx:command("target", "NULL") -- LOBBER.scr:270
    ctx:command("g_htarget", "= NULL") -- LOBBER.scr:271
    ctx:command("setidle", "") -- LOBBER.scr:273
    mm9.gosub(script, ctx, "StopAttackCheck") -- LOBBER.scr:275
    mm9.gosub(script, ctx, "TargetSearchOn") -- LOBBER.scr:276
    do return ctx:exit("TRUE") end -- LOBBER.scr:278
end

script.labels["OnDamage"] = function(ctx)
    -- LOBBER.scr:281
    ctx:getParam(0, "g_hAttacker") -- LOBBER.scr:284
    ctx:command("isfriend", "g_hAttacker, g_bTemp") -- LOBBER.scr:286
    if ctx:condition("g_bTemp==TRUE") then -- LOBBER.scr:288
        do return ctx:exit("FALSE") end -- LOBBER.scr:289
    end -- LOBBER.scr:290
    ctx:command("sendalert", "g_hAttacker") -- LOBBER.scr:292
    if ctx:condition("g_hTarget!=NULL") then -- LOBBER.scr:294
        do return ctx:exit("FALSE") end -- LOBBER.scr:295
    end -- LOBBER.scr:296
    ctx:command("g_htarget", "= g_hAttacker") -- LOBBER.scr:298
    ctx:command("target", "g_hTarget, TRUE") -- LOBBER.scr:300
    ctx:command("aware", "AwareDone") -- LOBBER.scr:301
    do return ctx:exit("FALSE") end -- LOBBER.scr:303
end

script.labels["Init"] = function(ctx)
    -- LOBBER.scr:306
    ctx:command("setidle", "") -- LOBBER.scr:308
    do return ctx:exit("") end -- LOBBER.scr:309
end

script.labels["Main"] = function(ctx)
    -- LOBBER.scr:312
    ctx:command("getmyhandle", "g_hMyObject") -- LOBBER.scr:315
    ctx:command("getpos", "g_hMyObject g_posX g_posY g_posZ") -- LOBBER.scr:317
    if ctx:condition("g_posX==-4224") then -- LOBBER.scr:318
        if ctx:condition("g_posY==912") then -- LOBBER.scr:319
            if ctx:condition("g_posZ==1664") then -- LOBBER.scr:320
                ctx:command("set", "g_posY 864") -- LOBBER.scr:321
                ctx:command("setpos", "g_hMyObject g_posX g_posY g_posZ") -- LOBBER.scr:322
            end -- LOBBER.scr:323
        end -- LOBBER.scr:324
    end -- LOBBER.scr:325
    ctx:command("set", "g_nPad2 1") -- LOBBER.scr:326
    ctx:command("onfoundtarget", "FoundTarget") -- LOBBER.scr:328
    ctx:command("ontargetdead", "TargetDead") -- LOBBER.scr:329
    ctx:command("onalert", "Alert") -- LOBBER.scr:330
    ctx:command("onlosttarget", "LostTarget") -- LOBBER.scr:331
    ctx:command("ondamage", "OnDamage") -- LOBBER.scr:332
    ctx:command("getstat", "g_hMyObject, RangeAttackRange, g_attackRange") -- LOBBER.scr:334
    ctx:command("wait", "0,0.1,Init") -- LOBBER.scr:336
    mm9.gosub(script, ctx, "TargetSearchOn") -- LOBBER.scr:338
    do return ctx:exit("") end -- LOBBER.scr:340
end

script.labels["FoundTarget"] = function(ctx)
    -- LOBBER.scr:343
    -- overloaded -- Bones
    if ctx:condition("g_nPad2 == 0") then -- LOBBER.scr:347
        ctx:command("getpos", "g_hMyObject g_posX g_posY g_posZ") -- LOBBER.scr:348
        if ctx:condition("g_posX==-4224") then -- LOBBER.scr:349
            if ctx:condition("g_posY==912") then -- LOBBER.scr:350
                if ctx:condition("g_posZ==1664") then -- LOBBER.scr:351
                    ctx:command("set", "g_posY 864") -- LOBBER.scr:352
                    ctx:command("setpos", "g_hMyObject g_posX g_posY g_posZ") -- LOBBER.scr:353
                end -- LOBBER.scr:354
            end -- LOBBER.scr:355
        end -- LOBBER.scr:356
        ctx:command("set", "g_nPad2 1") -- LOBBER.scr:357
    end -- LOBBER.scr:358
    do return mm9.gotoLabel(script, ctx, "FoundTarget") end -- LOBBER.scr:360
end

return script
