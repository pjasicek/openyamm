-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WINMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- WinMan.scr
-- By Timmy
-- 11/16
-- Manager for the WinGame Cutscene
-- edited by Bones 04/29/03
-- TELP Patch 1.3 -- moved givekey 109 to WG_NJAMCAM.SCR
-- protected switch from access through wall
-- prevented access to last sequence without quest
script.labels["OnUse"] = function(ctx)
    -- WINMAN.scr:25
    ctx:state().g_hPlayer = ctx:player() -- WINMAN.scr:28
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:player():pos() -- WINMAN.scr:29
    if ctx:condition("g_posZ < -3680") then -- WINMAN.scr:30
        do return ctx:exit("") end -- WINMAN.scr:31
    end -- WINMAN.scr:32
    if not ctx:hasKey(108) then -- WINMAN.scr:34-35
        mm9.gosub(script, ctx, "OnSwitch") -- WINMAN.scr:37
        ctx:object("Lightning1"):trigger("On") -- WINMAN.scr:38-39
        ctx:object("Lightning2"):trigger("On") -- WINMAN.scr:40-41
        ctx:wait(1, 7, "OnLightningOff") -- WINMAN.scr:42
        do return ctx:exit("") end -- WINMAN.scr:43
    end -- WINMAN.scr:44
    mm9.gosub(script, ctx, "OnSwitch") -- WINMAN.scr:46
    if not ctx:hasKey(109) then -- WINMAN.scr:48-49
        ctx:giveExp(234000) -- WINMAN.scr:50
    end -- WINMAN.scr:51
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- WINMAN.scr:53
    mm9.gosub(script, ctx, "DestroyMonsters") -- WINMAN.scr:54
    -- Camera
    ctx:screenFadeOut(1) -- WINMAN.scr:57
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- WINMAN.scr:58
    ctx:wait(1, 2, "OnStart") -- WINMAN.scr:59
    do return ctx:exit("") end -- WINMAN.scr:60
end

script.labels["onSwitch"] = function(ctx)
    -- WINMAN.scr:63
    if ctx:condition("bUp==FALSE") then -- WINMAN.scr:65
        ctx:playSound("\\Sounds\\door\\cell_door_close.wav", "DoNothing", 100, 24000, "FALSE", 100) -- WINMAN.scr:66
        ctx:self():playAnimation("up", "DoNothing") -- WINMAN.scr:67
        ctx:state().bUp = true -- WINMAN.scr:68
    else -- WINMAN.scr:69
        ctx:playSound("\\Sounds\\door\\cell_door_close.wav", "DoNothing", 100, 24000, "FALSE", 100) -- WINMAN.scr:70
        ctx:self():playAnimation("Down", "DoNothing") -- WINMAN.scr:71
        ctx:state().bUp = false -- WINMAN.scr:72
    end -- WINMAN.scr:73
    do return ctx:exit("") end -- WINMAN.scr:75
end

script.labels["DestroyMonsters"] = function(ctx)
    -- WINMAN.scr:78
    -- traceon
    ctx:state().g_ntemp = 0 -- WINMAN.scr:83
    ctx:getObjects("AIBase", 1024, 10, "g_hMonsterArray", "g_nMonsterCount") -- WINMAN.scr:85
    if ctx:condition("g_nMonsterCount==0") then -- WINMAN.scr:87
        do return ctx:exit("") end -- WINMAN.scr:88
    end -- WINMAN.scr:89
    while ctx:condition("g_nTemp < g_nMonsterCount") do -- WINMAN.scr:91
        ctx:arrayGet("g_hMonsterArray", "g_nTemp", "g_hObject") -- WINMAN.scr:93
        ctx:state().g_btemp = ctx:object("g_hObject"):isClass("NjamtheMeddler") -- WINMAN.scr:94
        if ctx:condition("g_btemp!=TRUE") then -- WINMAN.scr:96
            ctx:object("g_hobject"):remove() -- WINMAN.scr:98
        end -- WINMAN.scr:100
        ctx:set("g_nTemp", "g_nTemp + 1") -- WINMAN.scr:102
        if ctx:condition("g_ntemp > 10") then -- WINMAN.scr:104
            do return ctx:exit("") end -- WINMAN.scr:105
        end -- WINMAN.scr:106
    end -- WINMAN.scr:108
    -- traceoff
    do return ctx:exit("") end -- WINMAN.scr:111
end

script.labels["OnLightningOff"] = function(ctx)
    -- WINMAN.scr:114
    ctx:object("Lightning1"):trigger("Off") -- WINMAN.scr:118-119
    ctx:object("Lightning2"):trigger("Off") -- WINMAN.scr:120-121
    do return ctx:exit("") end -- WINMAN.scr:122
end

script.labels["OnStart"] = function(ctx)
    -- WINMAN.scr:126
    ctx:state().g_hobject = ctx:objectOrNil("NjamCam") -- WINMAN.scr:129
    -- trigger g_hobject On
    ctx:trigger("g_hobject", "Play") -- WINMAN.scr:131
    ctx:object("Njam"):trigger("chase") -- WINMAN.scr:134-135
    do return ctx:exit("") end -- WINMAN.scr:137
end

script.labels["OnNjamCamDone"] = function(ctx)
    -- WINMAN.scr:140
    ctx:object("NjamCam"):trigger("Off") -- WINMAN.scr:142-143
    local object = ctx:object("WG_Shot2Cam") -- WINMAN.scr:146
    object:trigger("On") -- WINMAN.scr:147
    object:trigger("play") -- WINMAN.scr:148
    do return ctx:exit("") end -- WINMAN.scr:149
end

script.labels["OnHandDone"] = function(ctx)
    -- WINMAN.scr:153
    ctx:object("WG_Shot2Cam"):trigger("Off") -- WINMAN.scr:156-157
    ctx:object("WG_Shot3Cam"):trigger("On") -- WINMAN.scr:159-160
    ctx:object("Njam"):trigger("Panic") -- WINMAN.scr:161-162
    ctx:playSound("\\Sounds\\spells\\Armsofearth01.wav", "DoNothing", 100, 24000, "FALSE", 100) -- WINMAN.scr:163
    do return ctx:exit("") end -- WINMAN.scr:164
end

script.labels["OnCameraSwitch"] = function(ctx)
    -- WINMAN.scr:167
    ctx:object("WG_Shot3Cam"):trigger("Off") -- WINMAN.scr:170-171
    ctx:object("WG_Shot4Cam"):trigger("On") -- WINMAN.scr:173-174
    do return ctx:exit("") end -- WINMAN.scr:176
end

script.labels["OnCameraSwitch2"] = function(ctx)
    -- WINMAN.scr:180
    ctx:object("WG_Shot4Cam"):trigger("Off") -- WINMAN.scr:183-184
    local object = ctx:object("WG_Shot5Cam") -- WINMAN.scr:186
    object:trigger("On") -- WINMAN.scr:187
    object:trigger("Play") -- WINMAN.scr:188
    do return ctx:exit("") end -- WINMAN.scr:190
end

script.labels["OnBallStart"] = function(ctx)
    -- WINMAN.scr:193
    do return ctx:exit("") end -- WINMAN.scr:196
end

script.labels["OnFrozen"] = function(ctx)
    -- WINMAN.scr:199
    ctx:screenFadeOut(1) -- WINMAN.scr:202
    ctx:wait(1, 2, "OnFinish") -- WINMAN.scr:204
    do return ctx:exit("") end -- WINMAN.scr:205
    do return ctx:exit("") end -- WINMAN.scr:207
end

script.labels["OnFinish"] = function(ctx)
    -- WINMAN.scr:210
    ctx:object("WG_Shot5CamB"):trigger("Off") -- WINMAN.scr:213-214
    local object = ctx:object("WG_Shot7Cam") -- WINMAN.scr:217
    object:trigger("On") -- WINMAN.scr:218
    object:trigger("Play") -- WINMAN.scr:219
    do return ctx:exit("") end -- WINMAN.scr:221
end

script.labels["OnPanUp"] = function(ctx)
    -- WINMAN.scr:226
    ctx:object("WG_Shot5Cam"):trigger("Off") -- WINMAN.scr:229-230
    ctx:object("WG_Shot6Cam"):trigger("On") -- WINMAN.scr:232-233
    ctx:wait(1, .6, "OnPanReturn") -- WINMAN.scr:235
    do return ctx:exit("") end -- WINMAN.scr:236
end

script.labels["OnPanReturn"] = function(ctx)
    -- WINMAN.scr:239
    ctx:object("WG_Shot6Cam"):trigger("Off") -- WINMAN.scr:242-243
    ctx:object("WG_Shot5Cam"):trigger("On") -- WINMAN.scr:245-246
    ctx:wait(1, 3, "LightingCamera2") -- WINMAN.scr:248
    do return ctx:exit("") end -- WINMAN.scr:249
end

script.labels["LightingCamera2"] = function(ctx)
    -- WINMAN.scr:252
    ctx:object("WG_Shot5Cam"):trigger("Off") -- WINMAN.scr:255-256
    ctx:object("WG_Shot5CamB"):trigger("On") -- WINMAN.scr:258-259
    do return ctx:exit("") end -- WINMAN.scr:260
end

script.labels["OnCutTo"] = function(ctx)
    -- WINMAN.scr:263
    ctx:screenFadeOut(2) -- WINMAN.scr:265
    ctx:wait(1, 2, "ChangeLevel") -- WINMAN.scr:266
    do return ctx:exit("") end -- WINMAN.scr:267
end

script.labels["ChangeLevel"] = function(ctx)
    -- WINMAN.scr:271
    -- getobjecthandle WG_Shot7Cam g_hobject
    -- trigger g_hobject Off
    -- Letterbox False
    ctx:object("ExitTrigger1"):trigger("trigger") -- WINMAN.scr:276-277
    -- screenfadein 1
    do return ctx:exit("") end -- WINMAN.scr:279
end

script.labels["OnKrohn"] = function(ctx)
    -- WINMAN.scr:282
    -- Screenfadeout 1
    ctx:letterBox("True") -- WINMAN.scr:286
    ctx:wait(1, 1, "StartPart2") -- WINMAN.scr:287
    do return ctx:exit("") end -- WINMAN.scr:288
end

script.labels["StartPart2"] = function(ctx)
    -- WINMAN.scr:291
    ctx:object("Skraelos0"):trigger("start") -- WINMAN.scr:294-295
    ctx:object("Krohn"):trigger("start") -- WINMAN.scr:296-297
    ctx:object("Hanndl"):trigger("start") -- WINMAN.scr:298-299
    ctx:object("Krohn0"):trigger("stop") -- WINMAN.scr:300-301
    local object = ctx:object("WG_Scene7Cam1") -- WINMAN.scr:304
    object:trigger("On") -- WINMAN.scr:305
    object:trigger("play") -- WINMAN.scr:306
    ctx:object("Hanndl"):trigger("action") -- WINMAN.scr:307-308
    ctx:screenFadeIn(1) -- WINMAN.scr:309
    do return ctx:exit("") end -- WINMAN.scr:310
end

script.labels["OnKrohnCut"] = function(ctx)
    -- WINMAN.scr:313
    ctx:screenFadeOut(.5) -- WINMAN.scr:318
    ctx:object("WG_Scene7Cam1"):trigger("Off") -- WINMAN.scr:319-320
    local object = ctx:object("WG_Scene7Cam2") -- WINMAN.scr:321
    object:trigger("On") -- WINMAN.scr:322
    object:trigger("play") -- WINMAN.scr:323
    ctx:screenFadeIn(1) -- WINMAN.scr:324
    ctx:screenFadeIn(1) -- WINMAN.scr:325
    ctx:wait(1, 3.5, "KrohnCut") -- WINMAN.scr:326
    do return ctx:exit("") end -- WINMAN.scr:327
end

script.labels["KrohnCut"] = function(ctx)
    -- WINMAN.scr:330
    ctx:object("WG_Scene7Cam2"):trigger("Off") -- WINMAN.scr:333-334
    local object = ctx:object("WG_Scene7Cam3") -- WINMAN.scr:335
    object:trigger("On") -- WINMAN.scr:336
    object:trigger("play") -- WINMAN.scr:337
    do return ctx:exit("") end -- WINMAN.scr:338
end

script.labels["OnHanndl1"] = function(ctx)
    -- WINMAN.scr:341
    ctx:object("WG_Scene7Cam3"):trigger("Off") -- WINMAN.scr:345-346
    ctx:object("WG_Scene7Cam4"):trigger("On") -- WINMAN.scr:347-348
    ctx:object("hanndl"):trigger("Hanndl1") -- WINMAN.scr:349-350
    do return ctx:exit("") end -- WINMAN.scr:351
end

script.labels["OnHanndl2"] = function(ctx)
    -- WINMAN.scr:355
    ctx:object("WG_Scene7Cam3"):trigger("Off") -- WINMAN.scr:359-360
    ctx:object("WG_Scene7Cam5"):trigger("On") -- WINMAN.scr:361-362
    ctx:object("hanndl"):trigger("Hanndl2") -- WINMAN.scr:363-364
    do return ctx:exit("") end -- WINMAN.scr:365
end

script.labels["OnHanndl3"] = function(ctx)
    -- WINMAN.scr:368
    ctx:object("WG_Scene7Cam6"):trigger("Off") -- WINMAN.scr:371-372
    ctx:object("WG_Scene7Cam5"):trigger("On") -- WINMAN.scr:373-374
    ctx:object("hanndl"):trigger("Hanndl3") -- WINMAN.scr:375-376
    do return ctx:exit("") end -- WINMAN.scr:378
end

script.labels["OnHanndl4"] = function(ctx)
    -- WINMAN.scr:383
    ctx:object("WG_Scene7Cam7"):trigger("Off") -- WINMAN.scr:386-387
    ctx:object("WG_Scene7Cam5"):trigger("On") -- WINMAN.scr:388-389
    ctx:object("hanndl"):trigger("Hanndl4") -- WINMAN.scr:390-391
    ctx:wait(1, 6, "OnHanndl4b") -- WINMAN.scr:392
    do return ctx:exit("") end -- WINMAN.scr:393
end

script.labels["OnHanndl4b"] = function(ctx)
    -- WINMAN.scr:396
    ctx:object("WG_Scene7Cam5"):trigger("Off") -- WINMAN.scr:399-400
    ctx:object("WG_Scene7Cam9"):trigger("On") -- WINMAN.scr:401-402
    do return ctx:exit("") end -- WINMAN.scr:403
end

script.labels["OnHanndl5"] = function(ctx)
    -- WINMAN.scr:406
    ctx:object("WG_Scene7Cam11"):trigger("Off") -- WINMAN.scr:410-411
    ctx:object("WG_Scene7Cam5"):trigger("On") -- WINMAN.scr:412-413
    ctx:object("hanndl"):trigger("Hanndl5") -- WINMAN.scr:414-415
    do return ctx:exit("") end -- WINMAN.scr:416
end

script.labels["OnHanndl6"] = function(ctx)
    -- WINMAN.scr:419
    ctx:object("WG_Scene7Cam6"):trigger("Off") -- WINMAN.scr:423-424
    ctx:object("WG_Scene7Cam10"):trigger("On") -- WINMAN.scr:425-426
    ctx:object("hanndl"):trigger("Hanndl6") -- WINMAN.scr:427-428
    do return ctx:exit("") end -- WINMAN.scr:429
end

script.labels["OnHanndlClose"] = function(ctx)
    -- WINMAN.scr:432
    ctx:object("WG_Scene7Cam6"):trigger("Off") -- WINMAN.scr:436-437
    ctx:object("WG_Scene7Cam8"):trigger("On") -- WINMAN.scr:438-439
    ctx:object("hanndl"):trigger("Embarassed") -- WINMAN.scr:440-441
    -- Hanndl looks down, embarassed
    do return ctx:exit("") end -- WINMAN.scr:444
end

script.labels["OnKrohn1"] = function(ctx)
    -- WINMAN.scr:447
    ctx:object("WG_Scene7Cam4"):trigger("Off") -- WINMAN.scr:451-452
    ctx:object("WG_Scene7Cam3"):trigger("On") -- WINMAN.scr:453-454
    ctx:object("Krohn"):trigger("Krohn1") -- WINMAN.scr:455-456
    do return ctx:exit("") end -- WINMAN.scr:457
end

script.labels["OnKrohn2"] = function(ctx)
    -- WINMAN.scr:460
    ctx:object("WG_Scene7Cam5"):trigger("Off") -- WINMAN.scr:464-465
    ctx:object("WG_Scene7Cam6"):trigger("On") -- WINMAN.scr:466-467
    ctx:object("Krohn"):trigger("Krohn2") -- WINMAN.scr:468-469
    do return ctx:exit("") end -- WINMAN.scr:470
end

script.labels["OnKrohn3"] = function(ctx)
    -- WINMAN.scr:473
    ctx:object("WG_Scene7Cam4"):trigger("Off") -- WINMAN.scr:476-477
    ctx:object("WG_Scene7Cam7"):trigger("On") -- WINMAN.scr:478-479
    ctx:object("Krohn"):trigger("Krohn3") -- WINMAN.scr:480-481
    do return ctx:exit("") end -- WINMAN.scr:482
end

script.labels["OnKrohn4"] = function(ctx)
    -- WINMAN.scr:485
    ctx:object("WG_Scene7Cam9"):trigger("Off") -- WINMAN.scr:488-489
    ctx:object("WG_Scene7Cam6"):trigger("On") -- WINMAN.scr:490-491
    ctx:object("Krohn"):trigger("Krohn4") -- WINMAN.scr:492-493
    do return ctx:exit("") end -- WINMAN.scr:494
end

script.labels["OnKrohn5"] = function(ctx)
    -- WINMAN.scr:497
    ctx:object("WG_Scene7Cam5"):trigger("Off") -- WINMAN.scr:500-501
    ctx:object("WG_Scene7Cam6"):trigger("On") -- WINMAN.scr:502-503
    ctx:object("Krohn"):trigger("Krohn5") -- WINMAN.scr:504-505
    do return ctx:exit("") end -- WINMAN.scr:506
end

script.labels["OnKrohn6"] = function(ctx)
    -- WINMAN.scr:509
    ctx:object("WG_Scene7Cam10"):trigger("Off") -- WINMAN.scr:512-513
    ctx:object("WG_Scene7Cam11"):trigger("On") -- WINMAN.scr:514-515
    ctx:object("Krohn"):trigger("Krohn6") -- WINMAN.scr:516-517
    do return ctx:exit("") end -- WINMAN.scr:518
end

script.labels["OnKrohn7"] = function(ctx)
    -- WINMAN.scr:521
    ctx:object("WG_Scene7Cam5"):trigger("Off") -- WINMAN.scr:524-525
    ctx:object("WG_Scene7Cam6"):trigger("On") -- WINMAN.scr:526-527
    ctx:object("Krohn"):trigger("Krohn7") -- WINMAN.scr:528-529
    do return ctx:exit("") end -- WINMAN.scr:530
end

script.labels["OnKrohnClose"] = function(ctx)
    -- WINMAN.scr:533
    ctx:object("WG_Scene7Cam8"):trigger("Off") -- WINMAN.scr:536-537
    ctx:object("WG_Scene7Cam7"):trigger("On") -- WINMAN.scr:538-539
    do return ctx:exit("") end -- WINMAN.scr:540
end

script.labels["OnEver"] = function(ctx)
    -- WINMAN.scr:543
    ctx:object("WG_Scene7Cam7"):trigger("Off") -- WINMAN.scr:546-547
    ctx:object("WG_Scene7Cam11"):trigger("On") -- WINMAN.scr:548-549
    do return ctx:exit("") end -- WINMAN.scr:550
end

script.labels["End"] = function(ctx)
    -- WINMAN.scr:553
    ctx:screenFadeOut(1) -- WINMAN.scr:556
    ctx:giveItem(394) -- WINMAN.scr:559
    ctx:wait(1, 3, "Release") -- WINMAN.scr:560
    do return ctx:exit("") end -- WINMAN.scr:561
end

script.labels["Release"] = function(ctx)
    -- WINMAN.scr:564
    -- load Arslegard here
    ctx:object("WG_Scene7Cam11"):trigger("Off") -- WINMAN.scr:568-569
    ctx:object("Skraelos0"):trigger("stop") -- WINMAN.scr:570-571
    ctx:object("Krohn"):trigger("stop") -- WINMAN.scr:572-573
    ctx:object("Hanndl"):trigger("stop") -- WINMAN.scr:574-575
    ctx:object("Krohn0"):trigger("start") -- WINMAN.scr:576-577
    ctx:letterBox("False") -- WINMAN.scr:578
    ctx:screenFadeIn(1) -- WINMAN.scr:579
    ctx:doHighScore() -- WINMAN.scr:580
    do return ctx:exit("") end -- WINMAN.scr:581
end

script.labels["Init"] = function(ctx)
    -- WINMAN.scr:584
    if ctx:condition("sPart!=Part2") then -- WINMAN.scr:587
        do return ctx:exit("") end -- WINMAN.scr:588
    end -- WINMAN.scr:589
    if ctx:hasItem(394) then -- WINMAN.scr:591-592
        do return ctx:exit("") end -- WINMAN.scr:593
    end -- WINMAN.scr:594
    if not ctx:hasKey(109) then -- WINMAN.scr:596-597
        do return ctx:exit("") end -- WINMAN.scr:598
    end -- WINMAN.scr:599
    ctx:wait(1, .1, "OnKrohn") -- WINMAN.scr:601
    do return ctx:exit("") end -- WINMAN.scr:602
end

script.labels["Main"] = function(ctx)
    -- WINMAN.scr:605
    -- TraceOn ;delete me!!
    ctx:getParam(0, "sPart") -- WINMAN.scr:609
    ctx:addTrigger("Use", "OnUse") -- WINMAN.scr:611
    ctx:addTrigger("NjamCamDone", "OnNjamCamDone") -- WINMAN.scr:612
    ctx:addTrigger("HandDone", "ONHandDone") -- WINMAN.scr:613
    ctx:addTrigger("BallStart", "OnBallStart") -- WINMAN.scr:614
    ctx:addTrigger("CameraSwitch", "OnCameraSwitch") -- WINMAN.scr:615
    ctx:addTrigger("CameraSwitch2", "OnCameraSwitch2") -- WINMAN.scr:616
    ctx:addTrigger("Frozen", "OnFrozen") -- WINMAN.scr:617
    ctx:addTrigger("Panup", "OnPanUp") -- WINMAN.scr:618
    ctx:addTrigger("CutTo", "OnCutTo") -- WINMAN.scr:619
    ctx:addTrigger("Krohn", "OnKrohn") -- WINMAN.scr:620
    -- Addtrigger Start ONForceStart
    ctx:addTrigger("CutToKrohn", "OnKrohnCut") -- WINMAN.scr:622
    ctx:addTrigger("krohn1", "OnKrohn1") -- WINMAN.scr:624
    ctx:addTrigger("Krohn2", "OnKrohn2") -- WINMAN.scr:625
    ctx:addTrigger("krohn3", "OnKrohn3") -- WINMAN.scr:626
    ctx:addTrigger("Krohn4", "OnKrohn4") -- WINMAN.scr:627
    ctx:addTrigger("krohn5", "OnKrohn5") -- WINMAN.scr:628
    ctx:addTrigger("Krohn6", "OnKrohn6") -- WINMAN.scr:629
    ctx:addTrigger("krohn7", "OnKrohn7") -- WINMAN.scr:630
    ctx:addTrigger("krohnClose", "OnKrohnClose") -- WINMAN.scr:631
    ctx:addTrigger("Ever", "OnEver") -- WINMAN.scr:632
    ctx:addTrigger("Hanndl1", "OnHanndl1") -- WINMAN.scr:636
    ctx:addTrigger("Hanndl2", "OnHanndl2") -- WINMAN.scr:637
    ctx:addTrigger("Hanndl3", "OnHanndl3") -- WINMAN.scr:638
    ctx:addTrigger("Hanndl4", "OnHanndl4") -- WINMAN.scr:639
    ctx:addTrigger("Hanndl5", "OnHanndl5") -- WINMAN.scr:640
    ctx:addTrigger("Hanndl6", "OnHanndl6") -- WINMAN.scr:641
    ctx:addTrigger("HanndlClose", "OnHanndlClose") -- WINMAN.scr:642
    ctx:addTrigger("switch", "onSwitch") -- WINMAN.scr:644
    ctx:addTrigger("End", "End") -- WINMAN.scr:646
    ctx:onEvent("OnPostStartWorld", "Init") -- WINMAN.scr:648
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- WINMAN.scr:649
    ctx:onEvent("OnPostSaveLoad", "Init") -- WINMAN.scr:650
    ctx:wait(1, .4, "Init") -- WINMAN.scr:651
    do return ctx:exit("") end -- WINMAN.scr:654
end

script.labels["Init"] = function(ctx)
    -- WINMAN.scr:658
    -- overloaded -- Bones
    ctx:hasKey(108, "g_bTemp") -- WINMAN.scr:662
    if ctx:condition("g_bTemp == FALSE") then -- WINMAN.scr:663
        local object = ctx:object("FoyerDoorSouth1") -- WINMAN.scr:664
        object:trigger("close") -- WINMAN.scr:665
        object:trigger("lock") -- WINMAN.scr:666
        local object = ctx:object("FoyerDoorSouth2") -- WINMAN.scr:667
        object:trigger("close") -- WINMAN.scr:668
        object:trigger("lock") -- WINMAN.scr:669
        do return ctx:exit("") end -- WINMAN.scr:670
    else -- WINMAN.scr:671
        ctx:object("FoyerDoorSouth1"):trigger("unlock") -- WINMAN.scr:672-673
        ctx:object("FoyerDoorSouth2"):trigger("unlock") -- WINMAN.scr:674-675
        do return mm9.gotoLabel(script, ctx, "Init") end -- WINMAN.scr:676
    end -- WINMAN.scr:677
end

return script
