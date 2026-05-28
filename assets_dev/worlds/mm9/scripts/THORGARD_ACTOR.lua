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
    ctx:command("clearflag", "g_hMyObject,FLAG_VISIBLE") -- THORGARD_ACTOR.scr:42
    ctx:command("clearflag", "g_hMyObject,FLAG_SOLID") -- THORGARD_ACTOR.scr:43
    ctx:command("bdisabled", "= TRUE") -- THORGARD_ACTOR.scr:44
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:45
end

script.labels["Enable"] = function(ctx)
    -- THORGARD_ACTOR.scr:48
    ctx:command("setflag", "g_hMyObject,FLAG_VISIBLE") -- THORGARD_ACTOR.scr:50
    ctx:command("setflag", "g_hMyObject,FLAG_SOLID") -- THORGARD_ACTOR.scr:51
    ctx:command("bdisabled", "= FALSE") -- THORGARD_ACTOR.scr:52
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
    ctx:command("onpostminisaveload", "OnPostMiniSaveLoad") -- THORGARD_ACTOR.scr:87
    do return mm9.gotoLabel(script, ctx, "CheckDisable") end -- THORGARD_ACTOR.scr:88
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:89
end

script.labels["IsNightTime"] = function(ctx)
    -- THORGARD_ACTOR.scr:93
    ctx:command("g_btemp", "= FALSE") -- THORGARD_ACTOR.scr:96
    ctx:command("getgametime", "nHour,nMinute") -- THORGARD_ACTOR.scr:98
    if ctx:condition("nHour >= 18") then -- THORGARD_ACTOR.scr:100
        ctx:command("g_btemp", "= TRUE") -- THORGARD_ACTOR.scr:101
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:102
    end -- THORGARD_ACTOR.scr:103
    if ctx:condition("nHour < 5") then -- THORGARD_ACTOR.scr:105
        ctx:command("g_btemp", "= TRUE") -- THORGARD_ACTOR.scr:106
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
    ctx:command("stop", "") -- THORGARD_ACTOR.scr:124
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_FORWARD") -- THORGARD_ACTOR.scr:126
    ctx:command("taunt", "GoRobPlayer") -- THORGARD_ACTOR.scr:128
    do return ctx:exit("TRUE") end -- THORGARD_ACTOR.scr:130
end

script.labels["OnRobPlayer"] = function(ctx)
    -- THORGARD_ACTOR.scr:133
    mm9.gosub(script, ctx, "IsNightTime") -- THORGARD_ACTOR.scr:135
    if ctx:condition("g_bTemp==FALSE") then -- THORGARD_ACTOR.scr:137
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:138
    end -- THORGARD_ACTOR.scr:139
    ctx:command("removetrigger", "RobPlayer") -- THORGARD_ACTOR.scr:141
    ctx:command("setflag", "g_hMyObject,FLAG_VISIBLE") -- THORGARD_ACTOR.scr:143
    ctx:command("setflag", "g_hMyObject,FLAG_SOLID") -- THORGARD_ACTOR.scr:144
    ctx:command("setstat", "g_hMyObject,Gravity,TRUE") -- THORGARD_ACTOR.scr:146
    ctx:command("getplayerhandle", "hPlayer") -- THORGARD_ACTOR.scr:148
    ctx:command("stop", "") -- THORGARD_ACTOR.scr:150
    ctx:command("target", "hPlayer,TRUE") -- THORGARD_ACTOR.scr:152
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_TARGET") -- THORGARD_ACTOR.scr:153
    ctx:command("smarker", "= sMyName + _Marker") -- THORGARD_ACTOR.scr:155
    ctx:command("getobjecthandle", "sMarker,g_hObject") -- THORGARD_ACTOR.scr:156
    ctx:command("walkto", "g_hObject,0,OnRobPlayerTaunt") -- THORGARD_ACTOR.scr:158
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:160
end

script.labels["CacheFiles"] = function(ctx)
    -- THORGARD_ACTOR.scr:163
    ctx:command("getstatstr", "g_hMyObject,ScriptName,g_sTemp") -- THORGARD_ACTOR.scr:165
    ctx:command("cachescript", "g_sTemp") -- THORGARD_ACTOR.scr:166
    ctx:command("cachesound", "splashSound") -- THORGARD_ACTOR.scr:168
    ctx:command("cachesound", "yellSound") -- THORGARD_ACTOR.scr:169
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:172
end

script.labels["SetupKen"] = function(ctx)
    -- THORGARD_ACTOR.scr:175
    ctx:addTrigger("RobPlayer", "OnRobPlayer") -- THORGARD_ACTOR.scr:178
    ctx:command("clearflag", "g_hMyObject,FLAG_VISIBLE") -- THORGARD_ACTOR.scr:180
    ctx:command("clearflag", "g_hMyObject,FLAG_SOLID") -- THORGARD_ACTOR.scr:181
    ctx:command("setstat", "g_hMyObject,Gravity,FALSE") -- THORGARD_ACTOR.scr:183
    ctx:command("loopanim", "0,0") -- THORGARD_ACTOR.scr:185
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:187
end

script.labels["JumperWaitGetPlayer"] = function(ctx)
    -- THORGARD_ACTOR.scr:190
    if ctx:condition("sMyName==Jumper2") then -- THORGARD_ACTOR.scr:193
        ctx:command("minwait", "= 10") -- THORGARD_ACTOR.scr:194
        ctx:command("maxwait", "= 25") -- THORGARD_ACTOR.scr:195
    end -- THORGARD_ACTOR.scr:196
    if ctx:condition("sMyName==Jumper3") then -- THORGARD_ACTOR.scr:198
        ctx:command("minwait", "= 30") -- THORGARD_ACTOR.scr:199
        ctx:command("maxwait", "= 45") -- THORGARD_ACTOR.scr:200
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
    ctx:command("ontouchnotify", "") -- THORGARD_ACTOR.scr:218
    ctx:command("stop", "") -- THORGARD_ACTOR.scr:219
    ctx:command("setvelocity", "g_hMyObject,0,0,0") -- THORGARD_ACTOR.scr:220
    ctx:command("setpushback", "0,0,0,0") -- THORGARD_ACTOR.scr:221
    ctx:command("getobjecthandle", "Jim,g_hTarget") -- THORGARD_ACTOR.scr:223
    ctx:command("target", "g_hTarget,TRUE") -- THORGARD_ACTOR.scr:224
    ctx:trigger("g_hTarget", "RunJimRun") -- THORGARD_ACTOR.scr:226
    ctx:command("getobjecthandle", "Dean,g_hObject") -- THORGARD_ACTOR.scr:228
    ctx:trigger("g_hObject", "ComeGetMe") -- THORGARD_ACTOR.scr:229
    ctx:command("getobjecthandle", "Walter,g_hObject") -- THORGARD_ACTOR.scr:231
    ctx:trigger("g_hObject", "ComeGetMe") -- THORGARD_ACTOR.scr:232
    ctx:command("taunt", "MagreebTauntDone") -- THORGARD_ACTOR.scr:234
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:236
end

script.labels["MagreebTouchNotify"] = function(ctx)
    -- THORGARD_ACTOR.scr:239
    ctx:command("isonground", "g_bTemp") -- THORGARD_ACTOR.scr:241
    if ctx:condition("g_bTemp==TRUE") then -- THORGARD_ACTOR.scr:243
        mm9.gosub(script, ctx, "MagreebJumpDone") -- THORGARD_ACTOR.scr:244
    end -- THORGARD_ACTOR.scr:245
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:247
end

script.labels["SetupMagreebTouch"] = function(ctx)
    -- THORGARD_ACTOR.scr:250
    ctx:command("setstat", "g_hMyObject,GroundTouchNotify,TRUE") -- THORGARD_ACTOR.scr:252
    ctx:command("ontouchnotify", "MagreebTouchNotify") -- THORGARD_ACTOR.scr:253
    ctx:command("playsound", "yellSound,DoNothing,3000") -- THORGARD_ACTOR.scr:254
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:256
end

script.labels["OnMagreebAttack"] = function(ctx)
    -- THORGARD_ACTOR.scr:259
    ctx:command("wait", "26,0,DoNothing") -- THORGARD_ACTOR.scr:262
    ctx:command("removetrigger", "Attack,OnMagreebAttack") -- THORGARD_ACTOR.scr:264
    if ctx:condition("bDisabled==TRUE") then -- THORGARD_ACTOR.scr:266
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:267
    end -- THORGARD_ACTOR.scr:268
    -- jsl-->2/5/02-->Give them the saw the magreeb key...
    ctx:giveKey(202) -- THORGARD_ACTOR.scr:271
    ctx:command("setstat", "g_hMyObject,GaveTreasure,1") -- THORGARD_ACTOR.scr:273
    ctx:command("setstat", "g_hMyObject,HitPoints,90") -- THORGARD_ACTOR.scr:274
    ctx:command("setstat", "g_hMyObject,AC,16") -- THORGARD_ACTOR.scr:275
    ctx:setPropNumber("RunawayChance", 0) -- THORGARD_ACTOR.scr:276
    ctx:setPropNumber("WanderON", "TRUE") -- THORGARD_ACTOR.scr:277
    ctx:command("setpos", "g_hMyObject,startX,startY,startZ") -- THORGARD_ACTOR.scr:279
    ctx:command("setstat", "g_hMyObject,Gravity,TRUE") -- THORGARD_ACTOR.scr:280
    ctx:command("getfacedir", "g_hMyObject,g_dirX,g_dirY,g_dirZ") -- THORGARD_ACTOR.scr:282
    ctx:command("loopanim", "Run,0") -- THORGARD_ACTOR.scr:283
    ctx:command("g_diry", "= 0") -- THORGARD_ACTOR.scr:284
    ctx:command("vecscale", "g_dirX,g_dirY,g_dirZ,500") -- THORGARD_ACTOR.scr:285
    ctx:command("setvelocity", "g_hMyObject,0,500,0") -- THORGARD_ACTOR.scr:286
    ctx:command("setpushback", "g_dirX,g_dirY,g_dirZ,2") -- THORGARD_ACTOR.scr:287
    -- setup our touch once we're in the air...
    ctx:command("playsound", "splashSound,DoNothing,3000") -- THORGARD_ACTOR.scr:291
    ctx:command("wait", "28,0.5,SetupMagreebTouch") -- THORGARD_ACTOR.scr:293
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:295
end

script.labels["MagreebAttackCheck"] = function(ctx)
    -- THORGARD_ACTOR.scr:299
    ctx:command("wait", "26,1,MagreebAttackCheck") -- THORGARD_ACTOR.scr:301
    if ctx:condition("bDisabled==TRUE") then -- THORGARD_ACTOR.scr:303
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:304
    end -- THORGARD_ACTOR.scr:305
    ctx:command("getplayerhandle", "g_hObject") -- THORGARD_ACTOR.scr:307
    if ctx:condition("g_hObject==NULL") then -- THORGARD_ACTOR.scr:309
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:310
    end -- THORGARD_ACTOR.scr:311
    ctx:command("aigetdistance", "g_hObject,g_nTemp") -- THORGARD_ACTOR.scr:313
    -- g_sTemp = BabyDistToPlayer__ + g_nTemp
    -- cprint g_sTemp
    if ctx:condition("g_nTemp > 1800") then -- THORGARD_ACTOR.scr:318
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:319
    end -- THORGARD_ACTOR.scr:320
    ctx:command("wait", "26,0,DoNothing") -- THORGARD_ACTOR.scr:322
    mm9.gosub(script, ctx, "OnMagreebAttack") -- THORGARD_ACTOR.scr:324
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:327
end

script.labels["SetupMagreebBaby"] = function(ctx)
    -- THORGARD_ACTOR.scr:330
    mm9.gosub(script, ctx, "CheckDisable") -- THORGARD_ACTOR.scr:333
    ctx:command("setstat", "g_hMyObject,Gravity,FALSE") -- THORGARD_ACTOR.scr:335
    ctx:addTrigger("Attack", "OnMagreebAttack") -- THORGARD_ACTOR.scr:336
    ctx:command("getpos", "g_hMyObject,startX,startY,startZ") -- THORGARD_ACTOR.scr:337
    ctx:command("addenemy", "Burgler") -- THORGARD_ACTOR.scr:339
    mm9.gosub(script, ctx, "MagreebAttackCheck") -- THORGARD_ACTOR.scr:341
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:344
end

script.labels["BaseShouldRun"] = function(ctx)
    -- THORGARD_ACTOR.scr:347
    if ctx:condition("sMyName==Jim") then -- THORGARD_ACTOR.scr:349
        ctx:command("g_btemp", "= TRUE") -- THORGARD_ACTOR.scr:350
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
    ctx:command("setstat", "g_hMyObject,HitPoints,1") -- THORGARD_ACTOR.scr:377
    ctx:getParam(0, "g_hTarget") -- THORGARD_ACTOR.scr:379
    ctx:command("target", "g_hTarget,FALSE") -- THORGARD_ACTOR.scr:381
    ctx:command("getstat", "g_hMyObject,RunVel,g_nTemp") -- THORGARD_ACTOR.scr:383
    ctx:command("g_ntemp", "= g_nTemp * 0.25") -- THORGARD_ACTOR.scr:384
    ctx:command("setstat", "g_hMyObject,RunVel,g_nTemp") -- THORGARD_ACTOR.scr:385
    ctx:command("getobjecthandle", "JimHidingPlace,g_hObject") -- THORGARD_ACTOR.scr:387
    ctx:command("runto", "g_hObject,0,AtHidingPlace") -- THORGARD_ACTOR.scr:388
    ctx:command("ondamagedone", "JimDamageDone") -- THORGARD_ACTOR.scr:389
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:391
end

script.labels["SetupJim"] = function(ctx)
    -- THORGARD_ACTOR.scr:394
    ctx:command("ondamage", "LetsStart") -- THORGARD_ACTOR.scr:397
    ctx:command("setstat", "g_hMyObject,HitPoints,1") -- THORGARD_ACTOR.scr:398
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
    ctx:command("target", "g_hTarget,TRUE") -- THORGARD_ACTOR.scr:415
    ctx:command("taunt", "") -- THORGARD_ACTOR.scr:417
    ctx:command("wait", "24,3,DeanAttack") -- THORGARD_ACTOR.scr:419
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:421
end

script.labels["LetsStart"] = function(ctx)
    -- THORGARD_ACTOR.scr:424
    ctx:command("ondamage", "") -- THORGARD_ACTOR.scr:427
    ctx:command("getobjecthandle", "MagreebBaby0,g_hObject") -- THORGARD_ACTOR.scr:429
    ctx:trigger("g_hObject", "Attack") -- THORGARD_ACTOR.scr:430
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:433
end

script.labels["SetupDean"] = function(ctx)
    -- THORGARD_ACTOR.scr:436
    ctx:addTrigger("ComeGetMe", "DeanGetHim") -- THORGARD_ACTOR.scr:438
    ctx:command("ondamage", "LetsStart") -- THORGARD_ACTOR.scr:439
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:441
end

script.labels["WalterGetHim"] = function(ctx)
    -- THORGARD_ACTOR.scr:444
    ctx:getParam(0, "g_hTarget") -- THORGARD_ACTOR.scr:447
    ctx:command("target", "g_hTarget") -- THORGARD_ACTOR.scr:448
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
        ctx:command("startx", "= -1700") -- THORGARD_ACTOR.scr:463
        ctx:command("starty", "= 1646") -- THORGARD_ACTOR.scr:464
        ctx:command("startz", "= -151") -- THORGARD_ACTOR.scr:465
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:466
    end -- THORGARD_ACTOR.scr:467
    if ctx:condition("sMyName==Jumper2") then -- THORGARD_ACTOR.scr:469
        ctx:command("startx", "= -1700") -- THORGARD_ACTOR.scr:470
        ctx:command("starty", "= 1646") -- THORGARD_ACTOR.scr:471
        ctx:command("startz", "= -151") -- THORGARD_ACTOR.scr:472
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:473
    end -- THORGARD_ACTOR.scr:474
    if ctx:condition("sMyName==Jumper1") then -- THORGARD_ACTOR.scr:476
        ctx:command("startx", "= -583") -- THORGARD_ACTOR.scr:477
        ctx:command("starty", "= 1760") -- THORGARD_ACTOR.scr:478
        ctx:command("startz", "= -29") -- THORGARD_ACTOR.scr:479
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:480
    end -- THORGARD_ACTOR.scr:481
    if ctx:condition("sMyName==Jumper3") then -- THORGARD_ACTOR.scr:483
        ctx:command("startx", "= -583") -- THORGARD_ACTOR.scr:484
        ctx:command("starty", "= 1760") -- THORGARD_ACTOR.scr:485
        ctx:command("startz", "= -29") -- THORGARD_ACTOR.scr:486
        do return ctx:exit("") end -- THORGARD_ACTOR.scr:487
    end -- THORGARD_ACTOR.scr:488
    do return mm9.gotoLabel(script, ctx, "JumperSetupPos") end -- THORGARD_ACTOR.scr:490
    do return ctx:exit("") end -- THORGARD_ACTOR.scr:491
end

script.labels["Main"] = function(ctx)
    -- THORGARD_ACTOR.scr:494
    ctx:command("getmyhandle", "g_hMyObject") -- THORGARD_ACTOR.scr:501
    ctx:command("getobjectname", "g_hMyObject,sMyName") -- THORGARD_ACTOR.scr:503
    ctx:command("oncachefiles", "CacheFiles") -- THORGARD_ACTOR.scr:505
    if ctx:condition("sMyName==Ken1") then -- THORGARD_ACTOR.scr:507
        mm9.gosub(script, ctx, "SetupKen") -- THORGARD_ACTOR.scr:508
    end -- THORGARD_ACTOR.scr:509
    if ctx:condition("sMyName==Ken2") then -- THORGARD_ACTOR.scr:510
        mm9.gosub(script, ctx, "SetupKen") -- THORGARD_ACTOR.scr:511
    end -- THORGARD_ACTOR.scr:512
    if ctx:condition("sMyName==Ken3") then -- THORGARD_ACTOR.scr:513
        mm9.gosub(script, ctx, "SetupKen") -- THORGARD_ACTOR.scr:514
    end -- THORGARD_ACTOR.scr:515
    ctx:command("bjumper", "= FALSE") -- THORGARD_ACTOR.scr:517
    ctx:command("getpos", "g_hMyObject,startX,startY,startZ") -- THORGARD_ACTOR.scr:519
    if ctx:condition("sMyName==Jumper0") then -- THORGARD_ACTOR.scr:521
        ctx:command("bjumper", "= TRUE") -- THORGARD_ACTOR.scr:522
    end -- THORGARD_ACTOR.scr:523
    if ctx:condition("sMyName==Jumper2") then -- THORGARD_ACTOR.scr:525
        ctx:command("bjumper", "= TRUE") -- THORGARD_ACTOR.scr:526
    end -- THORGARD_ACTOR.scr:527
    if ctx:condition("sMyName==Jumper1") then -- THORGARD_ACTOR.scr:529
        ctx:command("bjumper", "= TRUE") -- THORGARD_ACTOR.scr:530
    end -- THORGARD_ACTOR.scr:531
    if ctx:condition("sMyName==Jumper3") then -- THORGARD_ACTOR.scr:533
        ctx:command("bjumper", "= TRUE") -- THORGARD_ACTOR.scr:534
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
