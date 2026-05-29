-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FOREMANMINERED.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 30, path = "globals.inc" }

-- ForemanMinerEd.scr
-- Ed Campos
-- 10-15-01
-- Script Sets up a Leading Dwarf that
-- Initiates the movement of group Miners
-- ScriptParams are:
-- p0 = Name of OrderArea0
-- p1 = Name of OrderArea1
-- p2 = Name of OrderArea2
-- p3 = Name of OrderArea3
-- p4 = Name of WorkArea0
-- p5 = Name of WorkArea1
-- p6 = Name of WorkArea2
-- p7 = Name of WorkArea3
-- p8 = Name of MidSpot
-- p9 = Name of place to run to during "panic"
-- p10 = Name of DwarvenMinion0
-- p11 = Name of DwarvenMinion1
-- p12 = Name of DwarvenMinion2
-- Miners will "panic" and run around
-- and start their emergency routine
-- when "FreakOut" is triggered
-- #number	TRUE = 1
-- #number	FALSE = 0
script.labels["InitForemanMiner"] = function(ctx)
    -- FOREMANMINERED.scr:82
    -- Get Handles on all Markers within
    -- the world. Set Triggers
    ctx:onEvent("OnAlert", "OnPanic") -- FOREMANMINERED.scr:89
    ctx:onEvent("OnDamage", "OnDamage") -- FOREMANMINERED.scr:90
    ctx:addTrigger("FreakOut", "FreakOut") -- FOREMANMINERED.scr:92
    ctx:state().hBunker = ctx:objectOrNil("sBunkerName") -- FOREMANMINERED.scr:94
    ctx:state().hMinionTarget0 = ctx:objectOrNil("DwarvenMinion0") -- FOREMANMINERED.scr:96
    ctx:state().hMinionTarget1 = ctx:objectOrNil("DwarvenMinion1") -- FOREMANMINERED.scr:97
    ctx:state().hMinionTarget2 = ctx:objectOrNil("DwarvenMinion2") -- FOREMANMINERED.scr:98
    ctx:state().hMidSpot = ctx:objectOrNil("TrackMarker4") -- FOREMANMINERED.scr:99
    -- @M 6 : 15, ArrivedMidSpot, NewArea1
    -- @M 7 : 30, GiveMoveOutOrders, NewArea2
    -- @M 9 : 00, GiveMoveOutOrders, NewArea1
    -- @M 10 : 30, GiveMoveOutOrders, NewArea2
    -- @M 12 : 00, GiveMoveOutOrders, NewArea1
    -- @M 13 : 30, GiveMoveOutOrders, NewArea2
    -- @M 15 : 00, GiveMoveOutOrders, NewArea1
    -- @M 16 : 30, GiveMoveOutOrders, NewArea2
    -- @M 18 : 00, GiveMoveOutOrders, NewArea1
    mm9.gosub(script, ctx, "ArrivedMidSpot") -- FOREMANMINERED.scr:112
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:113
end

script.labels["StartPositionA"] = function(ctx)
    -- FOREMANMINERED.scr:116
    ctx:state().hOrderSpot0 = ctx:objectOrNil("sOrderArea0Name") -- FOREMANMINERED.scr:120
    ctx:state().hOrderSpot1 = ctx:objectOrNil("sOrderArea1Name") -- FOREMANMINERED.scr:121
    -- GetObjectHandle sWorkArea0Name, hTarget0
    -- GetObjectHandle sWorkArea1Name, hTarget1
    -- GetObjectHandle sWorkArea2Name, hTarget2
    ctx:self():walkTo(ctx:object("hOrderSpot1"), 10, "Arrived1stSpot") -- FOREMANMINERED.scr:125
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:128
end

script.labels["StartPositionB"] = function(ctx)
    -- FOREMANMINERED.scr:131
    ctx:state().hOrderSpot0 = ctx:objectOrNil("sOrderArea3Name") -- FOREMANMINERED.scr:135
    ctx:state().hOrderSpot1 = ctx:objectOrNil("sOrderArea2Name") -- FOREMANMINERED.scr:136
    -- GetObjectHandle sWorkArea0Name, hTarget0
    -- GetObjectHandle sWorkArea1Name, hTarget1
    -- GetObjectHandle sWorkArea2Name, hTarget2
    ctx:self():walkTo(ctx:object("hOrderSpot1"), 10, "Arrived1stSpot") -- FOREMANMINERED.scr:140
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:143
end

script.labels["ArrivedMidSpot"] = function(ctx)
    -- FOREMANMINERED.scr:146
    if ctx:condition("NewArea == 0") then -- FOREMANMINERED.scr:149
        mm9.gosub(script, ctx, "StartPositionA") -- FOREMANMINERED.scr:151
    else -- FOREMANMINERED.scr:153
        mm9.gosub(script, ctx, "StartPositionB") -- FOREMANMINERED.scr:154
    end -- FOREMANMINERED.scr:155
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:157
end

script.labels["Arrived1stSpot"] = function(ctx)
    -- FOREMANMINERED.scr:160
    ctx:self():stop() -- FOREMANMINERED.scr:163
    ctx:self():setTarget(ctx:object("hMinionTarget0")) -- FOREMANMINERED.scr:164
    ctx:wait(0, .1, "ThreatenWorker") -- FOREMANMINERED.scr:165
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:167
end

script.labels["ThreatenWorker"] = function(ctx)
    -- FOREMANMINERED.scr:170
    ctx:doCallback(0) -- FOREMANMINERED.scr:174
    ctx:wait(0, 3, "MicroManage1") -- FOREMANMINERED.scr:175
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:177
end

script.labels["MicroManage1"] = function(ctx)
    -- FOREMANMINERED.scr:180
    ctx:self():setTarget(nil) -- FOREMANMINERED.scr:183
    ctx:self():walkTo(ctx:object("hOrderSpot0"), 0, "ThreatenWorker2") -- FOREMANMINERED.scr:184
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:186
end

script.labels["ThreatenWorker2"] = function(ctx)
    -- FOREMANMINERED.scr:189
    ctx:self():stop() -- FOREMANMINERED.scr:192
    ctx:self():faceObject(ctx:object("hMinionTarget2"), 180, "DoNothing") -- FOREMANMINERED.scr:193
    ctx:wait(0, 10, "ThreatenWorker2A") -- FOREMANMINERED.scr:194
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:195
end

script.labels["ThreatenWorker2A"] = function(ctx)
    -- FOREMANMINERED.scr:198
    ctx:doCallback(1) -- FOREMANMINERED.scr:202
    ctx:wait(0, 10, "MicroManage2") -- FOREMANMINERED.scr:203
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:204
end

script.labels["MicroManage2"] = function(ctx)
    -- FOREMANMINERED.scr:208
    ctx:self():setTarget(nil) -- FOREMANMINERED.scr:211
    ctx:self():walkTo(ctx:object("hOrderSpot1"), 0, "ChooseVictim1") -- FOREMANMINERED.scr:212
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:214
end

script.labels["ChooseVictim1"] = function(ctx)
    -- FOREMANMINERED.scr:216
    ctx:self():stop() -- FOREMANMINERED.scr:219
    ctx:self():faceObject(ctx:object("hMinionTarget1"), 180, "RandomTaunt1") -- FOREMANMINERED.scr:220
    ctx:wait(0, 10, "DoWait") -- FOREMANMINERED.scr:221
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:223
end

script.labels["DoWait"] = function(ctx)
    -- FOREMANMINERED.scr:225
    ctx:self():setTarget(nil) -- FOREMANMINERED.scr:228
    ctx:self():faceObject(ctx:object("hMinionTarget2"), 180, "RandomTaunt1") -- FOREMANMINERED.scr:229
    ctx:wait(0, 10, "Micromanage3") -- FOREMANMINERED.scr:230
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:231
end

script.labels["MicroManage3"] = function(ctx)
    -- FOREMANMINERED.scr:234
    ctx:self():setTarget(nil) -- FOREMANMINERED.scr:237
    ctx:self():walkTo(ctx:object("hOrderSpot0"), 0, "ChooseVictim2") -- FOREMANMINERED.scr:238
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:240
end

script.labels["ChooseVictim2"] = function(ctx)
    -- FOREMANMINERED.scr:242
    ctx:self():stop() -- FOREMANMINERED.scr:245
    ctx:self():setTarget(nil) -- FOREMANMINERED.scr:246
    ctx:self():faceObject(ctx:object("hMinionTarget0"), 180, "RandomTaunt1") -- FOREMANMINERED.scr:247
    ctx:wait(0, 20, "MicroManage4") -- FOREMANMINERED.scr:248
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:249
end

script.labels["MicroManage4"] = function(ctx)
    -- FOREMANMINERED.scr:251
    ctx:self():setTarget(nil) -- FOREMANMINERED.scr:254
    ctx:self():walkTo(ctx:object("hOrderSpot1"), 0, "ChooseVictim3") -- FOREMANMINERED.scr:255
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:257
end

script.labels["ChooseVictim3"] = function(ctx)
    -- FOREMANMINERED.scr:261
    ctx:self():stop() -- FOREMANMINERED.scr:264
    ctx:self():faceObject(ctx:object("hMinionTarget2"), 180, "RandomTaunt1") -- FOREMANMINERED.scr:265
    ctx:wait(0, 20, "TempMicromanage1C") -- FOREMANMINERED.scr:266
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:268
end

script.labels["TempMicromanage1C"] = function(ctx)
    -- FOREMANMINERED.scr:270
    ctx:self():stop() -- FOREMANMINERED.scr:272
    ctx:self():setTarget(nil) -- FOREMANMINERED.scr:273
    ctx:wait(0, 20, "DoNothing") -- FOREMANMINERED.scr:274
    ctx:self():walkTo(ctx:object("hOrderSpot1"), 10, "GiveMoveOutOrders") -- FOREMANMINERED.scr:275
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:277
end

script.labels["GiveMoveOutOrders"] = function(ctx)
    -- FOREMANMINERED.scr:279
    ctx:self():stop() -- FOREMANMINERED.scr:282
    ctx:trigger("hMinionTarget0", "NextSite") -- FOREMANMINERED.scr:284
    ctx:trigger("hMinionTarget1", "NextSite") -- FOREMANMINERED.scr:285
    ctx:trigger("hMinionTarget2", "NextSite") -- FOREMANMINERED.scr:286
    ctx:doCallback(3) -- FOREMANMINERED.scr:287
    ctx:wait(0, 20, "MoveOut") -- FOREMANMINERED.scr:288
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:291
end

script.labels["MoveOut"] = function(ctx)
    -- FOREMANMINERED.scr:295
    if ctx:condition("NewArea == 1") then -- FOREMANMINERED.scr:298
        ctx:state().NewArea = 0 -- FOREMANMINERED.scr:299
    end -- FOREMANMINERED.scr:301
    mm9.gosub(script, ctx, "ArrivedMidspot") -- FOREMANMINERED.scr:303
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:305
end

script.labels["GotoLunch"] = function(ctx)
    -- FOREMANMINERED.scr:308
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:312
end

script.labels["GotoBed"] = function(ctx)
    -- FOREMANMINERED.scr:315
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:319
end

script.labels["NewArea1"] = function(ctx)
    -- FOREMANMINERED.scr:322
    if ctx:condition("NewArea == 1") then -- FOREMANMINERED.scr:325
        mm9.gosub(script, ctx, "ArrivedMidSpot") -- FOREMANMINERED.scr:327
    else -- FOREMANMINERED.scr:329
    end -- FOREMANMINERED.scr:331
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:334
end

script.labels["NewArea2"] = function(ctx)
    -- FOREMANMINERED.scr:337
    if ctx:condition("NewArea == 0") then -- FOREMANMINERED.scr:340
        mm9.gosub(script, ctx, "ArrivedMidSpot") -- FOREMANMINERED.scr:342
    else -- FOREMANMINERED.scr:344
    end -- FOREMANMINERED.scr:346
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:349
end

script.labels["OnDamage"] = function(ctx)
    -- FOREMANMINERED.scr:353
    ctx:self():stop() -- FOREMANMINERED.scr:358
    -- play sound "monster!!!"
    ctx:state().StopWorking = true -- FOREMANMINERED.scr:360
    ctx:onEvent("OnAlert", "DoNothing") -- FOREMANMINERED.scr:361
    ctx:onEvent("OnDamage", "DoNothing") -- FOREMANMINERED.scr:362
    ctx:getParam(0, "hTarget") -- FOREMANMINERED.scr:363
    ctx:self():setTarget(ctx:object("hTarget")) -- FOREMANMINERED.scr:364
    ctx:wait(0, 1, "GoDamagePanic") -- FOREMANMINERED.scr:366
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:368
end

script.labels["OnPanic"] = function(ctx)
    -- FOREMANMINERED.scr:372
    ctx:self():stop() -- FOREMANMINERED.scr:376
    ctx:onEvent("OnAlert", "DoNothing") -- FOREMANMINERED.scr:377
    ctx:onEvent("OnDamage", "DoNothing") -- FOREMANMINERED.scr:378
    ctx:state().StopWorking = true -- FOREMANMINERED.scr:379
    -- GetParam 0, hTarget0
    -- GetParam 1, hTarget2
    ctx:wait(0, 2, "DoNothing") -- FOREMANMINERED.scr:382
    ctx:self():setTarget(ctx:object("hTarget")) -- FOREMANMINERED.scr:384
    ctx:wait(0, 1.3, "FindTarget") -- FOREMANMINERED.scr:385
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:387
end

script.labels["FindTarget"] = function(ctx)
    -- FOREMANMINERED.scr:391
    -- play sound "monster!!!"
    ctx:self():stop() -- FOREMANMINERED.scr:396
    ctx:self():setTarget(nil) -- FOREMANMINERED.scr:397
    -- GetParam 1, hTarget2
    -- Target hTarget2, TRUE
    ctx:wait(0, .7, "GoPanic") -- FOREMANMINERED.scr:401
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:403
end

script.labels["FreakOut"] = function(ctx)
    -- FOREMANMINERED.scr:406
    ctx:self():stop() -- FOREMANMINERED.scr:409
    -- GetObjectHandle Trigger0, hTarget3
    -- Target hTarget3, TRUE
    ctx:wait(0, 1, "GoPanic") -- FOREMANMINERED.scr:413
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:415
end

script.labels["GoDamagePanic"] = function(ctx)
    -- FOREMANMINERED.scr:418
    ctx:self():playAnimation("Aware", "GoDamagePanic2") -- FOREMANMINERED.scr:421
    ctx:self():sendAlert(nil) -- FOREMANMINERED.scr:422
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:425
end

script.labels["GoDamagePanic2"] = function(ctx)
    -- FOREMANMINERED.scr:428
    -- Target NULL
    mm9.gosub(script, ctx, "BunkerRun") -- FOREMANMINERED.scr:433
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:436
end

script.labels["GoPanic"] = function(ctx)
    -- FOREMANMINERED.scr:438
    ctx:self():playAnimation("Aware", "DoNothing") -- FOREMANMINERED.scr:441
    ctx:wait(0, 1, "BunkerRun") -- FOREMANMINERED.scr:442
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:444
end

script.labels["BunkerRun"] = function(ctx)
    -- FOREMANMINERED.scr:446
    ctx:self():runTo(ctx:object("hBunker"), 40, "GoLockDown") -- FOREMANMINERED.scr:448
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:450
end

script.labels["GoLockDown"] = function(ctx)
    -- FOREMANMINERED.scr:452
    ctx:self():stop() -- FOREMANMINERED.scr:454
    do return ctx:exit("") end -- FOREMANMINERED.scr:455
end

script.labels["RandomTaunt1"] = function(ctx)
    -- FOREMANMINERED.scr:458
    ctx:randomInt(1, 5, "rand") -- FOREMANMINERED.scr:461
    if ctx:condition("rand==1") then -- FOREMANMINERED.scr:462
        mm9.gosub(script, ctx, "Anim1") -- FOREMANMINERED.scr:463
    end -- FOREMANMINERED.scr:464
    if ctx:condition("rand==2") then -- FOREMANMINERED.scr:465
        mm9.gosub(script, ctx, "Anim2") -- FOREMANMINERED.scr:466
    end -- FOREMANMINERED.scr:467
    if ctx:condition("rand==3") then -- FOREMANMINERED.scr:468
        mm9.gosub(script, ctx, "Anim3") -- FOREMANMINERED.scr:469
    end -- FOREMANMINERED.scr:470
    if ctx:condition("rand==4") then -- FOREMANMINERED.scr:471
        mm9.gosub(script, ctx, "Anim4") -- FOREMANMINERED.scr:472
    end -- FOREMANMINERED.scr:473
    if ctx:condition("rand==5") then -- FOREMANMINERED.scr:474
        mm9.gosub(script, ctx, "Anim5") -- FOREMANMINERED.scr:475
    end -- FOREMANMINERED.scr:476
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:479
end

script.labels["Anim0"] = function(ctx)
    -- FOREMANMINERED.scr:481
    ctx:self():stop() -- FOREMANMINERED.scr:483
    ctx:playSound("Sounds\\AnimSounds\\dwarfkingAware.wav", "OnSoundFinished", "hSound", 10000, "FALSE", 100) -- FOREMANMINERED.scr:485
    ctx:self():playAnimation("WAttack2", "DoNothing") -- FOREMANMINERED.scr:486
    do return ctx:exit("") end -- FOREMANMINERED.scr:488
end

script.labels["Anim1"] = function(ctx)
    -- FOREMANMINERED.scr:491
    ctx:self():stop() -- FOREMANMINERED.scr:493
    ctx:playSound("Sounds\\AnimSounds\\dwarfkingTaunt.wav", "OnSoundFinished", "hSound", 10000, "FALSE", 100) -- FOREMANMINERED.scr:495
    ctx:self():playAnimation("HAttack1", "DoNothing") -- FOREMANMINERED.scr:496
    do return ctx:exit("") end -- FOREMANMINERED.scr:499
end

script.labels["Anim2"] = function(ctx)
    -- FOREMANMINERED.scr:501
    ctx:self():stop() -- FOREMANMINERED.scr:503
    ctx:playSound("Sounds\\AnimSounds\\dwarfkingAware.wav", "OnSoundFinished", "hSound", 10000, "FALSE", 100) -- FOREMANMINERED.scr:505
    ctx:self():playAnimation("Taunt", "DoNothing") -- FOREMANMINERED.scr:506
    do return ctx:exit("") end -- FOREMANMINERED.scr:508
end

script.labels["Anim3"] = function(ctx)
    -- FOREMANMINERED.scr:511
    ctx:self():stop() -- FOREMANMINERED.scr:513
    ctx:playSound("Sounds\\AnimSounds\\dwarfAware.wav", "OnSoundFinished", "hSound", 10000, "FALSE", 100) -- FOREMANMINERED.scr:515
    ctx:self():playAnimation("Aware", "DoNothing") -- FOREMANMINERED.scr:516
    do return ctx:exit("") end -- FOREMANMINERED.scr:518
end

script.labels["Anim4"] = function(ctx)
    -- FOREMANMINERED.scr:521
    ctx:self():stop() -- FOREMANMINERED.scr:523
    ctx:self():playAnimation("Search", "DoNothing") -- FOREMANMINERED.scr:526
    do return ctx:exit("") end -- FOREMANMINERED.scr:528
end

script.labels["Anim5"] = function(ctx)
    -- FOREMANMINERED.scr:531
    ctx:self():stop() -- FOREMANMINERED.scr:533
    ctx:self():playAnimation("Fidget1", "DoNothing") -- FOREMANMINERED.scr:535
    do return ctx:exit("") end -- FOREMANMINERED.scr:537
end

script.labels["OnSoundFinished"] = function(ctx)
    -- FOREMANMINERED.scr:539
    ctx:killSound("hSound") -- FOREMANMINERED.scr:541
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:542
end

script.labels["Main"] = function(ctx)
    -- FOREMANMINERED.scr:545
    -- Retrieve Parameters from AI Actor
    -- TraceOn
    ctx:getParam(0, "sOrderArea0Name") -- FOREMANMINERED.scr:552
    ctx:getParam(1, "sOrderArea1Name") -- FOREMANMINERED.scr:553
    ctx:getParam(2, "sOrderArea2Name") -- FOREMANMINERED.scr:554
    ctx:getParam(3, "sOrderArea3Name") -- FOREMANMINERED.scr:555
    ctx:getParam(4, "sWorkArea0Name") -- FOREMANMINERED.scr:556
    ctx:getParam(5, "sWorkArea1Name") -- FOREMANMINERED.scr:557
    ctx:getParam(6, "sWorkArea2Name") -- FOREMANMINERED.scr:558
    ctx:getParam(7, "sWorkArea3Name") -- FOREMANMINERED.scr:559
    ctx:getParam(8, "sWorkArea4Name") -- FOREMANMINERED.scr:560
    ctx:getParam(9, "sWorkArea5Name") -- FOREMANMINERED.scr:561
    ctx:getParam(10, "sMidSpotName") -- FOREMANMINERED.scr:562
    ctx:getParam(11, "sBunkerName") -- FOREMANMINERED.scr:563
    ctx:getParam(12, "sDwarvenMinion0Name") -- FOREMANMINERED.scr:564
    ctx:getParam(13, "sDwarvenMinion1Name") -- FOREMANMINERED.scr:565
    ctx:getParam(14, "sDwarvenMinion2Name") -- FOREMANMINERED.scr:566
    ctx:setCallback(0, "Anim0") -- FOREMANMINERED.scr:568
    ctx:setCallback(1, "Anim1") -- FOREMANMINERED.scr:569
    ctx:setCallback(2, "Anim2") -- FOREMANMINERED.scr:570
    ctx:setCallback(3, "Anim3") -- FOREMANMINERED.scr:571
    ctx:setCallback(4, "Anim4") -- FOREMANMINERED.scr:572
    ctx:setCallback(5, "Anim5") -- FOREMANMINERED.scr:573
    ctx:cacheSound("sounds\\AnimSounds\\dwarfkingTaunt.wav") -- FOREMANMINERED.scr:575
    ctx:cacheSound("sounds\\AnimSounds\\dwarfAware.wav") -- FOREMANMINERED.scr:576
    ctx:cacheSound("sounds\\AnimSounds\\dwarfkingAware.wav") -- FOREMANMINERED.scr:577
    ctx:wait(0, 5, "InitForemanMiner") -- FOREMANMINERED.scr:579
    do return ctx:exit("TRUE") end -- FOREMANMINERED.scr:581
end

return script
