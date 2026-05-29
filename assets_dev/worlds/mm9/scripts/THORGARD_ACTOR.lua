-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THORGARD_ACTOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 21, path = "Jumper.Inc" }
script.includes[#script.includes + 1] = { line = 22, path = "BaseTimers.inc" }
script.includes[#script.includes + 1] = { line = 23, path = "BaseWander.inc" }
script.includes[#script.includes + 1] = { line = 24, path = "baseRun.inc" }

-- Thorgard_Actor.Scr
-- Jeff Leggett
-- 12/13/01
-- All the Thorgard actors go here...
-- Ken1-Ken3
-- - Setup to ambush the player at night in the dark
-- tunnel...
-- Jumper0-1
-- - Jump down from cliff at player
-- Jumper2-3
-- - Wait a little while before jumping down...
script.labels["Disable"] = function(ctx)
    -- THORGARD_ACTOR.scr:40
    ctx:self():setFlag("FLAG_VISIBLE", false) -- THORGARD_ACTOR.scr:42
    ctx:self():setFlag("FLAG_SOLID", false) -- THORGARD_ACTOR.scr:43
    ctx:state().bDisabled = true -- THORGARD_ACTOR.scr:44
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:45
end

script.labels["Enable"] = function(ctx)
    -- THORGARD_ACTOR.scr:48
    ctx:self():setFlag("FLAG_VISIBLE", true) -- THORGARD_ACTOR.scr:50
    ctx:self():setFlag("FLAG_SOLID", true) -- THORGARD_ACTOR.scr:51
    ctx:state().bDisabled = false -- THORGARD_ACTOR.scr:52
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:53
end

script.labels["CheckDisable"] = function(ctx)
    -- THORGARD_ACTOR.scr:56
    ctx:hasKey(201, "g_bTemp") -- THORGARD_ACTOR.scr:59
    if ctx:condition("g_bTemp==TRUE") then -- THORGARD_ACTOR.scr:61
        ctx:hasKey(202, "g_bTemp") -- THORGARD_ACTOR.scr:62
        if ctx:condition("g_bTemp==FALSE") then -- THORGARD_ACTOR.scr:63
            if ctx:condition("bDisabled==FALSE") then -- THORGARD_ACTOR.scr:64
                do return mm9.gotoLabel(script, ctx, "Disable") end -- THORGARD_ACTOR.scr:65
            else -- THORGARD_ACTOR.scr:66
                do return ctx:exit("") end -- THORGARD_ACTOR.scr:67
            end -- THORGARD_ACTOR.scr:68
        end -- THORGARD_ACTOR.scr:69
    end -- THORGARD_ACTOR.scr:70
    if ctx:condition("bDisabled==TRUE") then -- THORGARD_ACTOR.scr:72
        mm9.gosub(script, ctx, "Enable") -- THORGARD_ACTOR.scr:73
    end -- THORGARD_ACTOR.scr:74
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:76
end

script.labels["OnPostMiniSaveLoad"] = function(ctx)
    -- THORGARD_ACTOR.scr:79
    mm9.gosub(script, ctx, "CheckDisable") -- THORGARD_ACTOR.scr:81
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:82
end

script.labels["DisableCheckStart"] = function(ctx)
    -- THORGARD_ACTOR.scr:85
    ctx:onEvent("OnPostMiniSaveLoad", "OnPostMiniSaveLoad") -- THORGARD_ACTOR.scr:87
    do return mm9.gotoLabel(script, ctx, "CheckDisable") end -- THORGARD_ACTOR.scr:88
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:89
end

script.labels["IsNightTime"] = function(ctx)
    -- THORGARD_ACTOR.scr:93
    ctx:state().g_bTemp = false -- THORGARD_ACTOR.scr:96
    ctx:getGameTime("nHour", "nMinute") -- THORGARD_ACTOR.scr:98
    if ctx:condition("nHour >= 18") then -- THORGARD_ACTOR.scr:100
        ctx:state().g_bTemp = true -- THORGARD_ACTOR.scr:101
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:102
    end -- THORGARD_ACTOR.scr:103
    if ctx:condition("nHour < 5") then -- THORGARD_ACTOR.scr:105
        ctx:state().g_bTemp = true -- THORGARD_ACTOR.scr:106
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:107
    end -- THORGARD_ACTOR.scr:108
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:110
end

script.labels["GoRobPlayer"] = function(ctx)
    -- THORGARD_ACTOR.scr:113
    mm9.gosub(script, ctx, "RunNormalScript") -- THORGARD_ACTOR.scr:116
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:118
end

script.labels["OnRobPlayerTaunt"] = function(ctx)
    -- THORGARD_ACTOR.scr:121
    ctx:self():stop() -- THORGARD_ACTOR.scr:124
    ctx:self():setStat("WalkRunMode", "WALKRUNMODE_FORWARD") -- THORGARD_ACTOR.scr:126
    ctx:self():taunt("GoRobPlayer") -- THORGARD_ACTOR.scr:128
    do return ctx:exit("TRUE") end -- THORGARD_ACTOR.scr:130
end

script.labels["OnRobPlayer"] = function(ctx)
    -- THORGARD_ACTOR.scr:133
    mm9.gosub(script, ctx, "IsNightTime") -- THORGARD_ACTOR.scr:135
    if ctx:condition("g_bTemp==FALSE") then -- THORGARD_ACTOR.scr:137
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:138
    end -- THORGARD_ACTOR.scr:139
    ctx:removeTrigger("RobPlayer") -- THORGARD_ACTOR.scr:141
    ctx:self():setFlag("FLAG_VISIBLE", true) -- THORGARD_ACTOR.scr:143
    ctx:self():setFlag("FLAG_SOLID", true) -- THORGARD_ACTOR.scr:144
    ctx:self():setStat("Gravity", "TRUE") -- THORGARD_ACTOR.scr:146
    ctx:self():stop() -- THORGARD_ACTOR.scr:150
    ctx:self():setTarget(ctx:player()) -- THORGARD_ACTOR.scr:152
    ctx:self():setStat("WalkRunMode", "WALKRUNMODE_TARGET") -- THORGARD_ACTOR.scr:153
    ctx:set("sMarker", "sMyName + _Marker") -- THORGARD_ACTOR.scr:155
    ctx:state().g_hObject = ctx:objectOrNil("sMarker") -- THORGARD_ACTOR.scr:156
    ctx:self():walkTo(ctx:object("g_hObject"), 0, "OnRobPlayerTaunt") -- THORGARD_ACTOR.scr:158
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:160
end

script.labels["CacheFiles"] = function(ctx)
    -- THORGARD_ACTOR.scr:163
    ctx:state().g_sTemp = ctx:self():stringProperty("ScriptName") -- THORGARD_ACTOR.scr:165
    ctx:cacheScript("g_sTemp") -- THORGARD_ACTOR.scr:166
    ctx:cacheSound("splashSound") -- THORGARD_ACTOR.scr:168
    ctx:cacheSound("yellSound") -- THORGARD_ACTOR.scr:169
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:172
end

script.labels["SetupKen"] = function(ctx)
    -- THORGARD_ACTOR.scr:175
    ctx:addTrigger("RobPlayer", "OnRobPlayer") -- THORGARD_ACTOR.scr:178
    ctx:self():setFlag("FLAG_VISIBLE", false) -- THORGARD_ACTOR.scr:180
    ctx:self():setFlag("FLAG_SOLID", false) -- THORGARD_ACTOR.scr:181
    ctx:self():setStat("Gravity", "FALSE") -- THORGARD_ACTOR.scr:183
    ctx:self():loopAnimation(0, 0) -- THORGARD_ACTOR.scr:185
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:187
end

script.labels["JumperWaitGetPlayer"] = function(ctx)
    -- THORGARD_ACTOR.scr:190
    if ctx:condition("sMyName==Jumper2") then -- THORGARD_ACTOR.scr:193
        ctx:state().minWait = 10 -- THORGARD_ACTOR.scr:194
        ctx:state().maxWait = 25 -- THORGARD_ACTOR.scr:195
    end -- THORGARD_ACTOR.scr:196
    if ctx:condition("sMyName==Jumper3") then -- THORGARD_ACTOR.scr:198
        ctx:state().minWait = 30 -- THORGARD_ACTOR.scr:199
        ctx:state().maxWait = 45 -- THORGARD_ACTOR.scr:200
    end -- THORGARD_ACTOR.scr:201
    do return mm9.gotoLabel(script, ctx, "JumperWaitGetPlayer") end -- THORGARD_ACTOR.scr:203
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:205
end

script.labels["MagreebTauntDone"] = function(ctx)
    -- THORGARD_ACTOR.scr:209
    mm9.gosub(script, ctx, "RunNormalScript") -- THORGARD_ACTOR.scr:211
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:213
end

script.labels["MagreebJumpDone"] = function(ctx)
    -- THORGARD_ACTOR.scr:216
    ctx:onEvent("OnTouchNotify") -- THORGARD_ACTOR.scr:218
    ctx:self():stop() -- THORGARD_ACTOR.scr:219
    ctx:self():setVelocity(0, 0, 0) -- THORGARD_ACTOR.scr:220
    ctx:self():setPushBack(0, 0, 0, 0) -- THORGARD_ACTOR.scr:221
    ctx:state().g_hTarget = ctx:objectOrNil("Jim") -- THORGARD_ACTOR.scr:223
    ctx:self():setTarget(ctx:object("g_hTarget")) -- THORGARD_ACTOR.scr:224
    ctx:trigger("g_hTarget", "RunJimRun") -- THORGARD_ACTOR.scr:226
    ctx:object("Dean"):trigger("ComeGetMe") -- THORGARD_ACTOR.scr:228-229
    ctx:object("Walter"):trigger("ComeGetMe") -- THORGARD_ACTOR.scr:231-232
    ctx:self():taunt("MagreebTauntDone") -- THORGARD_ACTOR.scr:234
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:236
end

script.labels["MagreebTouchNotify"] = function(ctx)
    -- THORGARD_ACTOR.scr:239
    ctx:state().g_bTemp = ctx:self():isOnGround() -- THORGARD_ACTOR.scr:241
    if ctx:condition("g_bTemp==TRUE") then -- THORGARD_ACTOR.scr:243
        mm9.gosub(script, ctx, "MagreebJumpDone") -- THORGARD_ACTOR.scr:244
    end -- THORGARD_ACTOR.scr:245
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:247
end

script.labels["SetupMagreebTouch"] = function(ctx)
    -- THORGARD_ACTOR.scr:250
    ctx:self():setStat("GroundTouchNotify", "TRUE") -- THORGARD_ACTOR.scr:252
    ctx:onEvent("OnTouchNotify", "MagreebTouchNotify") -- THORGARD_ACTOR.scr:253
    ctx:playSound("yellSound", "DoNothing", 3000) -- THORGARD_ACTOR.scr:254
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:256
end

script.labels["OnMagreebAttack"] = function(ctx)
    -- THORGARD_ACTOR.scr:259
    ctx:wait(26, 0, "DoNothing") -- THORGARD_ACTOR.scr:262
    ctx:removeTrigger("Attack") -- THORGARD_ACTOR.scr:264
    if ctx:condition("bDisabled==TRUE") then -- THORGARD_ACTOR.scr:266
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:267
    end -- THORGARD_ACTOR.scr:268
    -- jsl-->2/5/02-->Give them the saw the magreeb key...
    ctx:giveKey(202) -- THORGARD_ACTOR.scr:271
    ctx:self():setStat("GaveTreasure", 1) -- THORGARD_ACTOR.scr:273
    ctx:self():setStat("HitPoints", 90) -- THORGARD_ACTOR.scr:274
    ctx:self():setStat("AC", 16) -- THORGARD_ACTOR.scr:275
    ctx:self():setNumberProperty("RunawayChance", 0) -- THORGARD_ACTOR.scr:276
    ctx:self():setNumberProperty("WanderON", "TRUE") -- THORGARD_ACTOR.scr:277
    ctx:self():setPos("startX", "startY", "startZ") -- THORGARD_ACTOR.scr:279
    ctx:self():setStat("Gravity", "TRUE") -- THORGARD_ACTOR.scr:280
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:self():rotation() -- THORGARD_ACTOR.scr:282
    ctx:self():loopAnimation("Run", 0) -- THORGARD_ACTOR.scr:283
    ctx:state().g_dirY = 0 -- THORGARD_ACTOR.scr:284
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:vecScale("g_dirX", "g_dirY", "g_dirZ", 500) -- THORGARD_ACTOR.scr:285
    ctx:self():setVelocity(0, 500, 0) -- THORGARD_ACTOR.scr:286
    ctx:self():setPushBack("g_dirX", "g_dirY", "g_dirZ", 2) -- THORGARD_ACTOR.scr:287
    -- setup our touch once we're in the air...
    ctx:playSound("splashSound", "DoNothing", 3000) -- THORGARD_ACTOR.scr:291
    ctx:wait(28, 0.5, "SetupMagreebTouch") -- THORGARD_ACTOR.scr:293
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:295
end

script.labels["MagreebAttackCheck"] = function(ctx)
    -- THORGARD_ACTOR.scr:299
    ctx:wait(26, 1, "MagreebAttackCheck") -- THORGARD_ACTOR.scr:301
    if ctx:condition("bDisabled==TRUE") then -- THORGARD_ACTOR.scr:303
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:304
    end -- THORGARD_ACTOR.scr:305
    ctx:state().g_hObject = ctx:player() -- THORGARD_ACTOR.scr:307
    if ctx:condition("g_hObject==NULL") then -- THORGARD_ACTOR.scr:309
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:310
    end -- THORGARD_ACTOR.scr:311
    ctx:state().g_nTemp = ctx:self():aiDistanceTo(ctx:object("g_hObject")) -- THORGARD_ACTOR.scr:313
    -- g_sTemp = BabyDistToPlayer__ + g_nTemp
    -- cprint g_sTemp
    if ctx:condition("g_nTemp > 1800") then -- THORGARD_ACTOR.scr:318
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:319
    end -- THORGARD_ACTOR.scr:320
    ctx:wait(26, 0, "DoNothing") -- THORGARD_ACTOR.scr:322
    mm9.gosub(script, ctx, "OnMagreebAttack") -- THORGARD_ACTOR.scr:324
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:327
end

script.labels["SetupMagreebBaby"] = function(ctx)
    -- THORGARD_ACTOR.scr:330
    mm9.gosub(script, ctx, "CheckDisable") -- THORGARD_ACTOR.scr:333
    ctx:self():setStat("Gravity", "FALSE") -- THORGARD_ACTOR.scr:335
    ctx:addTrigger("Attack", "OnMagreebAttack") -- THORGARD_ACTOR.scr:336
    ctx:state().startX, ctx:state().startY, ctx:state().startZ = ctx:self():pos() -- THORGARD_ACTOR.scr:337
    ctx:self():addEnemy("Burgler") -- THORGARD_ACTOR.scr:339
    mm9.gosub(script, ctx, "MagreebAttackCheck") -- THORGARD_ACTOR.scr:341
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:344
end

script.labels["BaseShouldRun"] = function(ctx)
    -- THORGARD_ACTOR.scr:347
    if ctx:condition("sMyName==Jim") then -- THORGARD_ACTOR.scr:349
        ctx:state().g_bTemp = true -- THORGARD_ACTOR.scr:350
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:351
    end -- THORGARD_ACTOR.scr:352
    mm9.gosub(script, ctx, "BaseShouldRun") -- THORGARD_ACTOR.scr:354
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:356
end

script.labels["AtHidingPlace"] = function(ctx)
    -- THORGARD_ACTOR.scr:359
    mm9.gosub(script, ctx, "RunNormalScript") -- THORGARD_ACTOR.scr:361
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:363
end

script.labels["JimDamageDone"] = function(ctx)
    -- THORGARD_ACTOR.scr:366
    mm9.gosub(script, ctx, "RunNormalScript") -- THORGARD_ACTOR.scr:369
    do return ctx:exit("TRUE") end -- THORGARD_ACTOR.scr:370
end

script.labels["RunJimRun"] = function(ctx)
    -- THORGARD_ACTOR.scr:373
    ctx:self():setStat("HitPoints", 1) -- THORGARD_ACTOR.scr:377
    ctx:getParam(0, "g_hTarget") -- THORGARD_ACTOR.scr:379
    ctx:self():setTarget(ctx:object("g_hTarget")) -- THORGARD_ACTOR.scr:381
    ctx:state().g_nTemp = ctx:self():getStat("RunVel") -- THORGARD_ACTOR.scr:383
    ctx:set("g_nTemp", "g_nTemp * 0.25") -- THORGARD_ACTOR.scr:384
    ctx:self():setStat("RunVel", "g_nTemp") -- THORGARD_ACTOR.scr:385
    ctx:state().g_hObject = ctx:objectOrNil("JimHidingPlace") -- THORGARD_ACTOR.scr:387
    ctx:self():runTo(ctx:object("g_hObject"), 0, "AtHidingPlace") -- THORGARD_ACTOR.scr:388
    ctx:onEvent("OnDamageDone", "JimDamageDone") -- THORGARD_ACTOR.scr:389
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:391
end

script.labels["SetupJim"] = function(ctx)
    -- THORGARD_ACTOR.scr:394
    ctx:onEvent("OnDamage", "LetsStart") -- THORGARD_ACTOR.scr:397
    ctx:self():setStat("HitPoints", 1) -- THORGARD_ACTOR.scr:398
    ctx:addTrigger("RunJimRun", "RunJimRun") -- THORGARD_ACTOR.scr:399
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:401
end

script.labels["DeanAttack"] = function(ctx)
    -- THORGARD_ACTOR.scr:405
    mm9.gosub(script, ctx, "RunNormalScript") -- THORGARD_ACTOR.scr:407
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:409
end

script.labels["DeanGetHim"] = function(ctx)
    -- THORGARD_ACTOR.scr:412
    ctx:getParam(0, "g_hTarget") -- THORGARD_ACTOR.scr:414
    ctx:self():setTarget(ctx:object("g_hTarget")) -- THORGARD_ACTOR.scr:415
    ctx:self():taunt() -- THORGARD_ACTOR.scr:417
    ctx:wait(24, 3, "DeanAttack") -- THORGARD_ACTOR.scr:419
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:421
end

script.labels["LetsStart"] = function(ctx)
    -- THORGARD_ACTOR.scr:424
    ctx:onEvent("OnDamage") -- THORGARD_ACTOR.scr:427
    ctx:object("MagreebBaby0"):trigger("Attack") -- THORGARD_ACTOR.scr:429-430
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:433
end

script.labels["SetupDean"] = function(ctx)
    -- THORGARD_ACTOR.scr:436
    ctx:addTrigger("ComeGetMe", "DeanGetHim") -- THORGARD_ACTOR.scr:438
    ctx:onEvent("OnDamage", "LetsStart") -- THORGARD_ACTOR.scr:439
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:441
end

script.labels["WalterGetHim"] = function(ctx)
    -- THORGARD_ACTOR.scr:444
    ctx:getParam(0, "g_hTarget") -- THORGARD_ACTOR.scr:447
    ctx:self():setTarget(ctx:object("g_hTarget")) -- THORGARD_ACTOR.scr:448
    do return mm9.gotoLabel(script, ctx, "RunNormalScript") end -- THORGARD_ACTOR.scr:449
end

script.labels["SetupWalter"] = function(ctx)
    -- THORGARD_ACTOR.scr:452
    ctx:addTrigger("ComeGetMe", "WalterGetHim") -- THORGARD_ACTOR.scr:454
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:456
end

script.labels["JumperSetupPos"] = function(ctx)
    -- THORGARD_ACTOR.scr:459
    if ctx:condition("sMyName==Jumper0") then -- THORGARD_ACTOR.scr:462
        ctx:state().startX = -1700 -- THORGARD_ACTOR.scr:463
        ctx:state().startY = 1646 -- THORGARD_ACTOR.scr:464
        ctx:state().startZ = -151 -- THORGARD_ACTOR.scr:465
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:466
    end -- THORGARD_ACTOR.scr:467
    if ctx:condition("sMyName==Jumper2") then -- THORGARD_ACTOR.scr:469
        ctx:state().startX = -1700 -- THORGARD_ACTOR.scr:470
        ctx:state().startY = 1646 -- THORGARD_ACTOR.scr:471
        ctx:state().startZ = -151 -- THORGARD_ACTOR.scr:472
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:473
    end -- THORGARD_ACTOR.scr:474
    if ctx:condition("sMyName==Jumper1") then -- THORGARD_ACTOR.scr:476
        ctx:state().startX = -583 -- THORGARD_ACTOR.scr:477
        ctx:state().startY = 1760 -- THORGARD_ACTOR.scr:478
        ctx:state().startZ = -29 -- THORGARD_ACTOR.scr:479
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:480
    end -- THORGARD_ACTOR.scr:481
    if ctx:condition("sMyName==Jumper3") then -- THORGARD_ACTOR.scr:483
        ctx:state().startX = -583 -- THORGARD_ACTOR.scr:484
        ctx:state().startY = 1760 -- THORGARD_ACTOR.scr:485
        ctx:state().startZ = -29 -- THORGARD_ACTOR.scr:486
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:487
    end -- THORGARD_ACTOR.scr:488
    do return mm9.gotoLabel(script, ctx, "JumperSetupPos") end -- THORGARD_ACTOR.scr:490
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:491
end

script.labels["Main"] = function(ctx)
    -- THORGARD_ACTOR.scr:494
    ctx:state().sMyName = ctx:self():name() -- THORGARD_ACTOR.scr:503
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- THORGARD_ACTOR.scr:505
    if ctx:condition("sMyName==Ken1") then -- THORGARD_ACTOR.scr:507
        mm9.gosub(script, ctx, "SetupKen") -- THORGARD_ACTOR.scr:508
    end -- THORGARD_ACTOR.scr:509
    if ctx:condition("sMyName==Ken2") then -- THORGARD_ACTOR.scr:510
        mm9.gosub(script, ctx, "SetupKen") -- THORGARD_ACTOR.scr:511
    end -- THORGARD_ACTOR.scr:512
    if ctx:condition("sMyName==Ken3") then -- THORGARD_ACTOR.scr:513
        mm9.gosub(script, ctx, "SetupKen") -- THORGARD_ACTOR.scr:514
    end -- THORGARD_ACTOR.scr:515
    ctx:state().bJumper = false -- THORGARD_ACTOR.scr:517
    ctx:state().startX, ctx:state().startY, ctx:state().startZ = ctx:self():pos() -- THORGARD_ACTOR.scr:519
    if ctx:condition("sMyName==Jumper0") then -- THORGARD_ACTOR.scr:521
        ctx:state().bJumper = true -- THORGARD_ACTOR.scr:522
    end -- THORGARD_ACTOR.scr:523
    if ctx:condition("sMyName==Jumper2") then -- THORGARD_ACTOR.scr:525
        ctx:state().bJumper = true -- THORGARD_ACTOR.scr:526
    end -- THORGARD_ACTOR.scr:527
    if ctx:condition("sMyName==Jumper1") then -- THORGARD_ACTOR.scr:529
        ctx:state().bJumper = true -- THORGARD_ACTOR.scr:530
    end -- THORGARD_ACTOR.scr:531
    if ctx:condition("sMyName==Jumper3") then -- THORGARD_ACTOR.scr:533
        ctx:state().bJumper = true -- THORGARD_ACTOR.scr:534
    end -- THORGARD_ACTOR.scr:535
    if ctx:condition("bJumper==TRUE") then -- THORGARD_ACTOR.scr:537
        mm9.gosub(script, ctx, "SetupJumper") -- THORGARD_ACTOR.scr:538
    end -- THORGARD_ACTOR.scr:539
    if ctx:condition("sMyName==MagreebBaby0") then -- THORGARD_ACTOR.scr:541
        mm9.gosub(script, ctx, "SetupMagreebBaby") -- THORGARD_ACTOR.scr:542
        mm9.gosub(script, ctx, "DisableCheckStart") -- THORGARD_ACTOR.scr:543
    end -- THORGARD_ACTOR.scr:544
    if ctx:condition("sMyName==Jim") then -- THORGARD_ACTOR.scr:546
        mm9.gosub(script, ctx, "SetupJim") -- THORGARD_ACTOR.scr:547
        mm9.gosub(script, ctx, "DisableCheckStart") -- THORGARD_ACTOR.scr:548
    end -- THORGARD_ACTOR.scr:549
    if ctx:condition("sMyName==Dean") then -- THORGARD_ACTOR.scr:551
        mm9.gosub(script, ctx, "SetupDean") -- THORGARD_ACTOR.scr:552
        mm9.gosub(script, ctx, "DisableCheckStart") -- THORGARD_ACTOR.scr:553
    end -- THORGARD_ACTOR.scr:554
    if ctx:condition("sMyName==Walter") then -- THORGARD_ACTOR.scr:556
        mm9.gosub(script, ctx, "SetupWalter") -- THORGARD_ACTOR.scr:557
        mm9.gosub(script, ctx, "DisableCheckStart") -- THORGARD_ACTOR.scr:558
    end -- THORGARD_ACTOR.scr:559
    if ctx:condition("sMyName==Dummy") then -- THORGARD_ACTOR.scr:561
        mm9.gosub(script, ctx, "DisableCheckStart") -- THORGARD_ACTOR.scr:562
        do return mm9.gotoLabel(script, ctx, "RunNormalScript") end -- THORGARD_ACTOR.scr:563
    end -- THORGARD_ACTOR.scr:564
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:566
end

return script
