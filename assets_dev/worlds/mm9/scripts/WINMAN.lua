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
    ctx:command("getplayerhandle", "g_hPlayer") -- WINMAN.scr:28
    ctx:command("getpos", "g_hPlayer g_posX g_posY g_posZ") -- WINMAN.scr:29
    if ctx:condition("g_posZ < -3680") then -- WINMAN.scr:30
        do return ctx:exit("") end -- WINMAN.scr:31
    end -- WINMAN.scr:32
    if not ctx:hasKey(108) then -- WINMAN.scr:34-35
        mm9.gosub(script, ctx, "OnSwitch") -- WINMAN.scr:37
        ctx:command("getobjecthandle", "Lightning1 g_hobject") -- WINMAN.scr:38
        ctx:trigger("g_hobject", "On") -- WINMAN.scr:39
        ctx:command("getobjecthandle", "Lightning2 g_hobject") -- WINMAN.scr:40
        ctx:trigger("g_hobject", "On") -- WINMAN.scr:41
        ctx:command("wait", "1 7 OnLightningOff") -- WINMAN.scr:42
        do return ctx:exit("") end -- WINMAN.scr:43
    end -- WINMAN.scr:44
    mm9.gosub(script, ctx, "OnSwitch") -- WINMAN.scr:46
    if not ctx:hasKey(109) then -- WINMAN.scr:48-49
        ctx:giveExp(234000) -- WINMAN.scr:50
    end -- WINMAN.scr:51
    ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- WINMAN.scr:53
    mm9.gosub(script, ctx, "DestroyMonsters") -- WINMAN.scr:54
    -- Camera
    ctx:command("screenfadeout", "1") -- WINMAN.scr:57
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- WINMAN.scr:58
    ctx:command("wait", "1 2 OnStart") -- WINMAN.scr:59
    do return ctx:exit("") end -- WINMAN.scr:60
end

script.labels["onSwitch"] = function(ctx)
    -- WINMAN.scr:63
    if ctx:condition("bUp==FALSE") then -- WINMAN.scr:65
        ctx:command("playsound", "\\Sounds\\door\\cell_door_close.wav, DoNothing, 100, 24000, FALSE, 100") -- WINMAN.scr:66
        ctx:command("playanim", "up DoNothing") -- WINMAN.scr:67
        ctx:command("set", "bUp TRUE") -- WINMAN.scr:68
    else -- WINMAN.scr:69
        ctx:command("playsound", "\\Sounds\\door\\cell_door_close.wav, DoNothing, 100, 24000, FALSE, 100") -- WINMAN.scr:70
        ctx:command("playanim", "Down DoNothing") -- WINMAN.scr:71
        ctx:command("set", "bUp FALSE") -- WINMAN.scr:72
    end -- WINMAN.scr:73
    do return ctx:exit("") end -- WINMAN.scr:75
end

script.labels["DestroyMonsters"] = function(ctx)
    -- WINMAN.scr:78
    -- traceon
    ctx:command("set", "g_ntemp, 0") -- WINMAN.scr:83
    ctx:command("getobjects", "AIBase, 1024, 10, g_hMonsterArray, g_nMonsterCount") -- WINMAN.scr:85
    if ctx:condition("g_nMonsterCount==0") then -- WINMAN.scr:87
        do return ctx:exit("") end -- WINMAN.scr:88
    end -- WINMAN.scr:89
    while ctx:condition("g_nTemp < g_nMonsterCount") do -- WINMAN.scr:91
        ctx:command("arrayget", "g_hMonsterArray, g_nTemp, g_hObject") -- WINMAN.scr:93
        ctx:command("isclass", "g_hObject NjamtheMeddler g_btemp") -- WINMAN.scr:94
        if ctx:condition("g_btemp!=TRUE") then -- WINMAN.scr:96
            ctx:command("removeobject", "g_hobject") -- WINMAN.scr:98
        end -- WINMAN.scr:100
        ctx:command("g_ntemp", "= g_nTemp + 1") -- WINMAN.scr:102
        if ctx:condition("g_ntemp > 10") then -- WINMAN.scr:104
            do return ctx:exit("") end -- WINMAN.scr:105
        end -- WINMAN.scr:106
    end -- WINMAN.scr:108
    -- traceoff
    do return ctx:exit("") end -- WINMAN.scr:111
end

script.labels["OnLightningOff"] = function(ctx)
    -- WINMAN.scr:114
    ctx:command("getobjecthandle", "Lightning1 g_hobject") -- WINMAN.scr:118
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:119
    ctx:command("getobjecthandle", "Lightning2 g_hobject") -- WINMAN.scr:120
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:121
    do return ctx:exit("") end -- WINMAN.scr:122
end

script.labels["OnStart"] = function(ctx)
    -- WINMAN.scr:126
    ctx:command("getobjecthandle", "NjamCam g_hobject") -- WINMAN.scr:129
    -- trigger g_hobject On
    ctx:trigger("g_hobject", "Play") -- WINMAN.scr:131
    ctx:command("getobjecthandle", "Njam g_hobject") -- WINMAN.scr:134
    ctx:trigger("g_hobject", "chase") -- WINMAN.scr:135
    do return ctx:exit("") end -- WINMAN.scr:137
end

script.labels["OnNjamCamDone"] = function(ctx)
    -- WINMAN.scr:140
    ctx:command("getobjecthandle", "NjamCam g_hobject") -- WINMAN.scr:142
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:143
    ctx:command("getobjecthandle", "WG_Shot2Cam g_hobject") -- WINMAN.scr:146
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:147
    ctx:trigger("g_hobject", "play") -- WINMAN.scr:148
    do return ctx:exit("") end -- WINMAN.scr:149
end

script.labels["OnHandDone"] = function(ctx)
    -- WINMAN.scr:153
    ctx:command("getobjecthandle", "WG_Shot2Cam g_hobject") -- WINMAN.scr:156
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:157
    ctx:command("getobjecthandle", "WG_Shot3Cam g_hobject") -- WINMAN.scr:159
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:160
    ctx:command("getobjecthandle", "Njam g_hobject") -- WINMAN.scr:161
    ctx:trigger("g_hobject", "Panic") -- WINMAN.scr:162
    ctx:command("playsound", "\\Sounds\\spells\\Armsofearth01.wav, DoNothing, 100, 24000, FALSE, 100") -- WINMAN.scr:163
    do return ctx:exit("") end -- WINMAN.scr:164
end

script.labels["OnCameraSwitch"] = function(ctx)
    -- WINMAN.scr:167
    ctx:command("getobjecthandle", "WG_Shot3Cam g_hobject") -- WINMAN.scr:170
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:171
    ctx:command("getobjecthandle", "WG_Shot4Cam g_hobject") -- WINMAN.scr:173
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:174
    do return ctx:exit("") end -- WINMAN.scr:176
end

script.labels["OnCameraSwitch2"] = function(ctx)
    -- WINMAN.scr:180
    ctx:command("getobjecthandle", "WG_Shot4Cam g_hobject") -- WINMAN.scr:183
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:184
    ctx:command("getobjecthandle", "WG_Shot5Cam g_hobject") -- WINMAN.scr:186
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:187
    ctx:trigger("g_hobject", "Play") -- WINMAN.scr:188
    do return ctx:exit("") end -- WINMAN.scr:190
end

script.labels["OnBallStart"] = function(ctx)
    -- WINMAN.scr:193
    do return ctx:exit("") end -- WINMAN.scr:196
end

script.labels["OnFrozen"] = function(ctx)
    -- WINMAN.scr:199
    ctx:command("screenfadeout", "1") -- WINMAN.scr:202
    ctx:command("wait", "1 2 OnFinish") -- WINMAN.scr:204
    do return ctx:exit("") end -- WINMAN.scr:205
    do return ctx:exit("") end -- WINMAN.scr:207
end

script.labels["OnFinish"] = function(ctx)
    -- WINMAN.scr:210
    ctx:command("getobjecthandle", "WG_Shot5CamB g_hobject") -- WINMAN.scr:213
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:214
    ctx:command("getobjecthandle", "WG_Shot7Cam g_hobject") -- WINMAN.scr:217
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:218
    ctx:trigger("g_hobject", "Play") -- WINMAN.scr:219
    do return ctx:exit("") end -- WINMAN.scr:221
end

script.labels["OnPanUp"] = function(ctx)
    -- WINMAN.scr:226
    ctx:command("getobjecthandle", "WG_Shot5Cam g_hobject") -- WINMAN.scr:229
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:230
    ctx:command("getobjecthandle", "WG_Shot6Cam g_hobject") -- WINMAN.scr:232
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:233
    ctx:command("wait", "1 .6 OnPanReturn") -- WINMAN.scr:235
    do return ctx:exit("") end -- WINMAN.scr:236
end

script.labels["OnPanReturn"] = function(ctx)
    -- WINMAN.scr:239
    ctx:command("getobjecthandle", "WG_Shot6Cam g_hobject") -- WINMAN.scr:242
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:243
    ctx:command("getobjecthandle", "WG_Shot5Cam g_hobject") -- WINMAN.scr:245
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:246
    ctx:command("wait", "1 3 LightingCamera2") -- WINMAN.scr:248
    do return ctx:exit("") end -- WINMAN.scr:249
end

script.labels["LightingCamera2"] = function(ctx)
    -- WINMAN.scr:252
    ctx:command("getobjecthandle", "WG_Shot5Cam g_hobject") -- WINMAN.scr:255
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:256
    ctx:command("getobjecthandle", "WG_Shot5CamB g_hobject") -- WINMAN.scr:258
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:259
    do return ctx:exit("") end -- WINMAN.scr:260
end

script.labels["OnCutTo"] = function(ctx)
    -- WINMAN.scr:263
    ctx:command("screenfadeout", "2") -- WINMAN.scr:265
    ctx:command("wait", "1 2 ChangeLevel") -- WINMAN.scr:266
    do return ctx:exit("") end -- WINMAN.scr:267
end

script.labels["ChangeLevel"] = function(ctx)
    -- WINMAN.scr:271
    -- getobjecthandle WG_Shot7Cam g_hobject
    -- trigger g_hobject Off
    -- Letterbox False
    ctx:command("getobjecthandle", "ExitTrigger1 g_hobject") -- WINMAN.scr:276
    ctx:trigger("g_hobject", "trigger") -- WINMAN.scr:277
    -- screenfadein 1
    do return ctx:exit("") end -- WINMAN.scr:279
end

script.labels["OnKrohn"] = function(ctx)
    -- WINMAN.scr:282
    -- Screenfadeout 1
    ctx:command("letterbox", "True") -- WINMAN.scr:286
    ctx:command("wait", "1 1 StartPart2") -- WINMAN.scr:287
    do return ctx:exit("") end -- WINMAN.scr:288
end

script.labels["StartPart2"] = function(ctx)
    -- WINMAN.scr:291
    ctx:command("getobjecthandle", "Skraelos0 g_hobject") -- WINMAN.scr:294
    ctx:trigger("g_hobject", "start") -- WINMAN.scr:295
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:296
    ctx:trigger("g_hobject", "start") -- WINMAN.scr:297
    ctx:command("getobjecthandle", "Hanndl g_hobject") -- WINMAN.scr:298
    ctx:trigger("g_hobject", "start") -- WINMAN.scr:299
    ctx:command("getobjecthandle", "Krohn0 g_hobject") -- WINMAN.scr:300
    ctx:trigger("g_hobject", "stop") -- WINMAN.scr:301
    ctx:command("getobjecthandle", "WG_Scene7Cam1 g_hobject") -- WINMAN.scr:304
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:305
    ctx:trigger("g_hobject", "play") -- WINMAN.scr:306
    ctx:command("getobjecthandle", "Hanndl g_hobject") -- WINMAN.scr:307
    ctx:trigger("G_hobject", "action") -- WINMAN.scr:308
    ctx:command("screenfadein", "1") -- WINMAN.scr:309
    do return ctx:exit("") end -- WINMAN.scr:310
end

script.labels["OnKrohnCut"] = function(ctx)
    -- WINMAN.scr:313
    ctx:command("screenfadeout", ".5") -- WINMAN.scr:318
    ctx:command("getobjecthandle", "WG_Scene7Cam1 g_hobject") -- WINMAN.scr:319
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:320
    ctx:command("getobjecthandle", "WG_Scene7Cam2 g_hobject") -- WINMAN.scr:321
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:322
    ctx:trigger("g_hobject", "play") -- WINMAN.scr:323
    ctx:command("screenfadein", "1") -- WINMAN.scr:324
    ctx:command("screenfadein", "1") -- WINMAN.scr:325
    ctx:command("wait", "1 3.5 KrohnCut") -- WINMAN.scr:326
    do return ctx:exit("") end -- WINMAN.scr:327
end

script.labels["KrohnCut"] = function(ctx)
    -- WINMAN.scr:330
    ctx:command("getobjecthandle", "WG_Scene7Cam2 g_hobject") -- WINMAN.scr:333
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:334
    ctx:command("getobjecthandle", "WG_Scene7Cam3 g_hobject") -- WINMAN.scr:335
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:336
    ctx:trigger("g_hobject", "play") -- WINMAN.scr:337
    do return ctx:exit("") end -- WINMAN.scr:338
end

script.labels["OnHanndl1"] = function(ctx)
    -- WINMAN.scr:341
    ctx:command("getobjecthandle", "WG_Scene7Cam3 g_hobject") -- WINMAN.scr:345
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:346
    ctx:command("getobjecthandle", "WG_Scene7Cam4 g_hobject") -- WINMAN.scr:347
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:348
    ctx:command("getobjecthandle", "hanndl g_hobject") -- WINMAN.scr:349
    ctx:trigger("g_hobject", "Hanndl1") -- WINMAN.scr:350
    do return ctx:exit("") end -- WINMAN.scr:351
end

script.labels["OnHanndl2"] = function(ctx)
    -- WINMAN.scr:355
    ctx:command("getobjecthandle", "WG_Scene7Cam3 g_hobject") -- WINMAN.scr:359
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:360
    ctx:command("getobjecthandle", "WG_Scene7Cam5 g_hobject") -- WINMAN.scr:361
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:362
    ctx:command("getobjecthandle", "hanndl g_hobject") -- WINMAN.scr:363
    ctx:trigger("g_hobject", "Hanndl2") -- WINMAN.scr:364
    do return ctx:exit("") end -- WINMAN.scr:365
end

script.labels["OnHanndl3"] = function(ctx)
    -- WINMAN.scr:368
    ctx:command("getobjecthandle", "WG_Scene7Cam6 g_hobject") -- WINMAN.scr:371
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:372
    ctx:command("getobjecthandle", "WG_Scene7Cam5 g_hobject") -- WINMAN.scr:373
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:374
    ctx:command("getobjecthandle", "hanndl g_hobject") -- WINMAN.scr:375
    ctx:trigger("g_hobject", "Hanndl3") -- WINMAN.scr:376
    do return ctx:exit("") end -- WINMAN.scr:378
end

script.labels["OnHanndl4"] = function(ctx)
    -- WINMAN.scr:383
    ctx:command("getobjecthandle", "WG_Scene7Cam7 g_hobject") -- WINMAN.scr:386
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:387
    ctx:command("getobjecthandle", "WG_Scene7Cam5 g_hobject") -- WINMAN.scr:388
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:389
    ctx:command("getobjecthandle", "hanndl g_hobject") -- WINMAN.scr:390
    ctx:trigger("g_hobject", "Hanndl4") -- WINMAN.scr:391
    ctx:command("wait", "1 6 OnHanndl4b") -- WINMAN.scr:392
    do return ctx:exit("") end -- WINMAN.scr:393
end

script.labels["OnHanndl4b"] = function(ctx)
    -- WINMAN.scr:396
    ctx:command("getobjecthandle", "WG_Scene7Cam5 g_hobject") -- WINMAN.scr:399
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:400
    ctx:command("getobjecthandle", "WG_Scene7Cam9 g_hobject") -- WINMAN.scr:401
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:402
    do return ctx:exit("") end -- WINMAN.scr:403
end

script.labels["OnHanndl5"] = function(ctx)
    -- WINMAN.scr:406
    ctx:command("getobjecthandle", "WG_Scene7Cam11 g_hobject") -- WINMAN.scr:410
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:411
    ctx:command("getobjecthandle", "WG_Scene7Cam5 g_hobject") -- WINMAN.scr:412
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:413
    ctx:command("getobjecthandle", "hanndl g_hobject") -- WINMAN.scr:414
    ctx:trigger("g_hobject", "Hanndl5") -- WINMAN.scr:415
    do return ctx:exit("") end -- WINMAN.scr:416
end

script.labels["OnHanndl6"] = function(ctx)
    -- WINMAN.scr:419
    ctx:command("getobjecthandle", "WG_Scene7Cam6 g_hobject") -- WINMAN.scr:423
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:424
    ctx:command("getobjecthandle", "WG_Scene7Cam10 g_hobject") -- WINMAN.scr:425
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:426
    ctx:command("getobjecthandle", "hanndl g_hobject") -- WINMAN.scr:427
    ctx:trigger("g_hobject", "Hanndl6") -- WINMAN.scr:428
    do return ctx:exit("") end -- WINMAN.scr:429
end

script.labels["OnHanndlClose"] = function(ctx)
    -- WINMAN.scr:432
    ctx:command("getobjecthandle", "WG_Scene7Cam6 g_hobject") -- WINMAN.scr:436
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:437
    ctx:command("getobjecthandle", "WG_Scene7Cam8 g_hobject") -- WINMAN.scr:438
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:439
    ctx:command("getobjecthandle", "hanndl g_hobject") -- WINMAN.scr:440
    ctx:trigger("g_hobject", "Embarassed") -- WINMAN.scr:441
    -- Hanndl looks down, embarassed
    do return ctx:exit("") end -- WINMAN.scr:444
end

script.labels["OnKrohn1"] = function(ctx)
    -- WINMAN.scr:447
    ctx:command("getobjecthandle", "WG_Scene7Cam4 g_hobject") -- WINMAN.scr:451
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:452
    ctx:command("getobjecthandle", "WG_Scene7Cam3 g_hobject") -- WINMAN.scr:453
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:454
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:455
    ctx:trigger("g_hobject", "Krohn1") -- WINMAN.scr:456
    do return ctx:exit("") end -- WINMAN.scr:457
end

script.labels["OnKrohn2"] = function(ctx)
    -- WINMAN.scr:460
    ctx:command("getobjecthandle", "WG_Scene7Cam5 g_hobject") -- WINMAN.scr:464
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:465
    ctx:command("getobjecthandle", "WG_Scene7Cam6 g_hobject") -- WINMAN.scr:466
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:467
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:468
    ctx:trigger("g_hobject", "Krohn2") -- WINMAN.scr:469
    do return ctx:exit("") end -- WINMAN.scr:470
end

script.labels["OnKrohn3"] = function(ctx)
    -- WINMAN.scr:473
    ctx:command("getobjecthandle", "WG_Scene7Cam4 g_hobject") -- WINMAN.scr:476
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:477
    ctx:command("getobjecthandle", "WG_Scene7Cam7 g_hobject") -- WINMAN.scr:478
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:479
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:480
    ctx:trigger("g_hobject", "Krohn3") -- WINMAN.scr:481
    do return ctx:exit("") end -- WINMAN.scr:482
end

script.labels["OnKrohn4"] = function(ctx)
    -- WINMAN.scr:485
    ctx:command("getobjecthandle", "WG_Scene7Cam9 g_hobject") -- WINMAN.scr:488
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:489
    ctx:command("getobjecthandle", "WG_Scene7Cam6 g_hobject") -- WINMAN.scr:490
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:491
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:492
    ctx:trigger("g_hobject", "Krohn4") -- WINMAN.scr:493
    do return ctx:exit("") end -- WINMAN.scr:494
end

script.labels["OnKrohn5"] = function(ctx)
    -- WINMAN.scr:497
    ctx:command("getobjecthandle", "WG_Scene7Cam5 g_hobject") -- WINMAN.scr:500
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:501
    ctx:command("getobjecthandle", "WG_Scene7Cam6 g_hobject") -- WINMAN.scr:502
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:503
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:504
    ctx:trigger("g_hobject", "Krohn5") -- WINMAN.scr:505
    do return ctx:exit("") end -- WINMAN.scr:506
end

script.labels["OnKrohn6"] = function(ctx)
    -- WINMAN.scr:509
    ctx:command("getobjecthandle", "WG_Scene7Cam10 g_hobject") -- WINMAN.scr:512
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:513
    ctx:command("getobjecthandle", "WG_Scene7Cam11 g_hobject") -- WINMAN.scr:514
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:515
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:516
    ctx:trigger("g_hobject", "Krohn6") -- WINMAN.scr:517
    do return ctx:exit("") end -- WINMAN.scr:518
end

script.labels["OnKrohn7"] = function(ctx)
    -- WINMAN.scr:521
    ctx:command("getobjecthandle", "WG_Scene7Cam5 g_hobject") -- WINMAN.scr:524
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:525
    ctx:command("getobjecthandle", "WG_Scene7Cam6 g_hobject") -- WINMAN.scr:526
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:527
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:528
    ctx:trigger("g_hobject", "Krohn7") -- WINMAN.scr:529
    do return ctx:exit("") end -- WINMAN.scr:530
end

script.labels["OnKrohnClose"] = function(ctx)
    -- WINMAN.scr:533
    ctx:command("getobjecthandle", "WG_Scene7Cam8 g_hobject") -- WINMAN.scr:536
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:537
    ctx:command("getobjecthandle", "WG_Scene7Cam7 g_hobject") -- WINMAN.scr:538
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:539
    do return ctx:exit("") end -- WINMAN.scr:540
end

script.labels["OnEver"] = function(ctx)
    -- WINMAN.scr:543
    ctx:command("getobjecthandle", "WG_Scene7Cam7 g_hobject") -- WINMAN.scr:546
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:547
    ctx:command("getobjecthandle", "WG_Scene7Cam11 g_hobject") -- WINMAN.scr:548
    ctx:trigger("g_hobject", "On") -- WINMAN.scr:549
    do return ctx:exit("") end -- WINMAN.scr:550
end

script.labels["End"] = function(ctx)
    -- WINMAN.scr:553
    ctx:command("screenfadeout", "1") -- WINMAN.scr:556
    ctx:giveItem(394) -- WINMAN.scr:559
    ctx:command("wait", "1 3 Release") -- WINMAN.scr:560
    do return ctx:exit("") end -- WINMAN.scr:561
end

script.labels["Release"] = function(ctx)
    -- WINMAN.scr:564
    -- load Arslegard here
    ctx:command("getobjecthandle", "WG_Scene7Cam11 g_hobject") -- WINMAN.scr:568
    ctx:trigger("g_hobject", "Off") -- WINMAN.scr:569
    ctx:command("getobjecthandle", "Skraelos0 g_hobject") -- WINMAN.scr:570
    ctx:trigger("g_hobject", "stop") -- WINMAN.scr:571
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WINMAN.scr:572
    ctx:trigger("g_hobject", "stop") -- WINMAN.scr:573
    ctx:command("getobjecthandle", "Hanndl g_hobject") -- WINMAN.scr:574
    ctx:trigger("g_hobject", "stop") -- WINMAN.scr:575
    ctx:command("getobjecthandle", "Krohn0 g_hobject") -- WINMAN.scr:576
    ctx:trigger("g_hobject", "start") -- WINMAN.scr:577
    ctx:command("letterbox", "False") -- WINMAN.scr:578
    ctx:command("screenfadein", "1") -- WINMAN.scr:579
    ctx:command("dohighscore", "") -- WINMAN.scr:580
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
    ctx:command("wait", "1 .1 OnKrohn") -- WINMAN.scr:601
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
    ctx:command("onpoststartworld", "Init") -- WINMAN.scr:648
    ctx:command("onpostminisaveload", "Init") -- WINMAN.scr:649
    ctx:command("onpostsaveload", "Init") -- WINMAN.scr:650
    ctx:command("wait", "1 .4 Init") -- WINMAN.scr:651
    do return ctx:exit("") end -- WINMAN.scr:654
end

script.labels["Init"] = function(ctx)
    -- WINMAN.scr:658
    -- overloaded -- Bones
    ctx:hasKey(108, "g_bTemp") -- WINMAN.scr:662
    if ctx:condition("g_bTemp == FALSE") then -- WINMAN.scr:663
        ctx:command("getobjecthandle", "FoyerDoorSouth1 g_hobject") -- WINMAN.scr:664
        ctx:trigger("g_hobject", "close") -- WINMAN.scr:665
        ctx:trigger("g_hobject", "lock") -- WINMAN.scr:666
        ctx:command("getobjecthandle", "FoyerDoorSouth2 g_hobject") -- WINMAN.scr:667
        ctx:trigger("g_hobject", "close") -- WINMAN.scr:668
        ctx:trigger("g_hobject", "lock") -- WINMAN.scr:669
        do return ctx:exit("") end -- WINMAN.scr:670
    else -- WINMAN.scr:671
        ctx:command("getobjecthandle", "FoyerDoorSouth1 g_hobject") -- WINMAN.scr:672
        ctx:trigger("g_hobject", "unlock") -- WINMAN.scr:673
        ctx:command("getobjecthandle", "FoyerDoorSouth2 g_hobject") -- WINMAN.scr:674
        ctx:trigger("g_hobject", "unlock") -- WINMAN.scr:675
        do return mm9.gotoLabel(script, ctx, "Init") end -- WINMAN.scr:676
    end -- WINMAN.scr:677
end

return script
