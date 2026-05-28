-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARGUMENT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }

-- Argument.scr
-- By Timmy
-- handles XP for stopping the war
-- edited by Bones 7/16/02, 5/29/03
-- TELP Patch 1.3 -- Ensures Yrsa's errand is given.
-- Prevents proceeding to cutscene in TB mode.
script.labels["OnUse"] = function(ctx)
    -- ARGUMENT.scr:28
    if ctx:hasKey(184) then -- ARGUMENT.scr:30-31
        ctx:doRude(1) -- ARGUMENT.scr:32
        ctx:command("playsound", "voices\\NPC\\NPC_001.wav, DoNothing, 100, 24000, FALSE, 100") -- ARGUMENT.scr:33
        do return ctx:exit("") end -- ARGUMENT.scr:34
    end -- ARGUMENT.scr:35
    mm9.gosub(script, ctx, "War") -- ARGUMENT.scr:36
    do return ctx:exit("") end -- ARGUMENT.scr:38
end

script.labels["War"] = function(ctx)
    -- ARGUMENT.scr:42
    -- gives reward for viewing cutscene
    if not ctx:hasKey(184) then -- ARGUMENT.scr:47-48
        ctx:giveKey(184) -- ARGUMENT.scr:49
        ctx:giveKey(40) -- ARGUMENT.scr:50
        ctx:giveKey(85) -- ARGUMENT.scr:51
        ctx:giveExp(26500) -- ARGUMENT.scr:52
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- ARGUMENT.scr:53
        ctx:takeItem(401) -- ARGUMENT.scr:54
        -- gives reward
        ctx:giveKey(93) -- ARGUMENT.scr:57
        -- Yrsa's errand
        do return ctx:exit("") end -- ARGUMENT.scr:60
    end -- ARGUMENT.scr:61
    do return ctx:exit("") end -- ARGUMENT.scr:62
end

script.labels["OnRude"] = function(ctx)
    -- ARGUMENT.scr:66
    -- this is for Yrsa after the arguement
    if not ctx:hasKey(185) then -- ARGUMENT.scr:70-71
        if ctx:hasKey(93) then -- ARGUMENT.scr:72-73
            -- this is where Forad is removed from the party
            -- GiveExp 16000
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- ARGUMENT.scr:76
            ctx:giveKey(185) -- ARGUMENT.scr:77
            do return ctx:exit("") end -- ARGUMENT.scr:79
        end -- ARGUMENT.scr:80
    end -- ARGUMENT.scr:81
    do return ctx:exit("") end -- ARGUMENT.scr:82
end

script.labels["ForceStart"] = function(ctx)
    -- ARGUMENT.scr:86
    if ctx:condition("nStarted==TRUE") then -- ARGUMENT.scr:89
        do return ctx:exit("") end -- ARGUMENT.scr:90
    end -- ARGUMENT.scr:91
    ctx:command("getobjecthandle", "Sven hSven") -- ARGUMENT.scr:93
    ctx:command("getobjecthandle", "Bjarni hBjarni") -- ARGUMENT.scr:94
    ctx:command("getobjecthandle", "Sigmund hSigmund") -- ARGUMENT.scr:95
    ctx:command("getobjecthandle", "Markel hMarkel") -- ARGUMENT.scr:96
    ctx:command("getobjecthandle", "Tryygva hTryygva") -- ARGUMENT.scr:97
    ctx:command("getobjecthandle", "Kira hKira") -- ARGUMENT.scr:98
    ctx:command("getobjecthandle", "Forad hForad") -- ARGUMENT.scr:99
    -- letterbox true
    -- set ncamcount 18
    -- gosub Bjarni16
    mm9.gosub(script, ctx, "OnStart") -- ARGUMENT.scr:103
    do return ctx:exit("") end -- ARGUMENT.scr:104
end

script.labels["Init"] = function(ctx)
    -- ARGUMENT.scr:107
    if ctx:hasKey(40) then -- ARGUMENT.scr:110-111
        do return ctx:exit("") end -- ARGUMENT.scr:112
    end -- ARGUMENT.scr:113
    ctx:command("set", "g_ncounter, 0") -- ARGUMENT.scr:116
    if ctx:hasKey(90) then -- ARGUMENT.scr:120-121
        ctx:command("add", "g_ncounter, 1") -- ARGUMENT.scr:122
    end -- ARGUMENT.scr:123
    if ctx:hasKey(91) then -- ARGUMENT.scr:125-126
        ctx:command("add", "g_nCounter, 1") -- ARGUMENT.scr:127
    end -- ARGUMENT.scr:128
    if ctx:condition("g_nCounter==2") then -- ARGUMENT.scr:130
        if ctx:condition("nStarted==TRUE") then -- ARGUMENT.scr:132
            do return ctx:exit("") end -- ARGUMENT.scr:133
        end -- ARGUMENT.scr:134
        ctx:command("getobjecthandle", "Sven hSven") -- ARGUMENT.scr:136
        ctx:command("getobjecthandle", "Bjarni hBjarni") -- ARGUMENT.scr:137
        ctx:command("getobjecthandle", "Sigmund hSigmund") -- ARGUMENT.scr:138
        ctx:command("getobjecthandle", "Markel hMarkel") -- ARGUMENT.scr:139
        ctx:command("getobjecthandle", "Tryygva hTryygva") -- ARGUMENT.scr:140
        ctx:command("getobjecthandle", "Kira hKira") -- ARGUMENT.scr:141
        ctx:command("getobjecthandle", "Forad hForad") -- ARGUMENT.scr:142
        mm9.gosub(script, ctx, "OnStart") -- ARGUMENT.scr:144
        do return ctx:exit("") end -- ARGUMENT.scr:145
    end -- ARGUMENT.scr:146
    do return ctx:exit("") end -- ARGUMENT.scr:148
end

script.labels["OnStart"] = function(ctx)
    -- ARGUMENT.scr:152
    ctx:command("isturnbased", "g_nTemp") -- ARGUMENT.scr:155
    if ctx:condition("g_nTemp == TRUE") then -- ARGUMENT.scr:156
        ctx:command("screenfadeout", "1") -- ARGUMENT.scr:157
        ctx:command("rollovertext", "18 0") -- ARGUMENT.scr:158
        ctx:command("wait", "0 1 OnStart") -- ARGUMENT.scr:159
        do return ctx:exit("") end -- ARGUMENT.scr:160
    end -- ARGUMENT.scr:161
    ctx:command("set", "nStarted, TRUE") -- ARGUMENT.scr:163
    ctx:command("removetrigger", "start") -- ARGUMENT.scr:164
    ctx:command("set", "nCamCount, 0") -- ARGUMENT.scr:165
    ctx:command("screenfadeout", "1") -- ARGUMENT.scr:166
    ctx:command("wait", "1 1 FadeIn") -- ARGUMENT.scr:167
    do return ctx:exit("") end -- ARGUMENT.scr:168
end

script.labels["FadeIn"] = function(ctx)
    -- ARGUMENT.scr:171
    ctx:command("letterbox", "true") -- ARGUMENT.scr:174
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- ARGUMENT.scr:175
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:176
    ctx:trigger("g_hobject", "Play") -- ARGUMENT.scr:177
    ctx:command("screenfadein", "1") -- ARGUMENT.scr:178
    -- wait 1 1 ShootOn
    do return ctx:exit("") end -- ARGUMENT.scr:180
end

script.labels["Cam1"] = function(ctx)
    -- ARGUMENT.scr:183
    ctx:command("screenfadeout", ".5") -- ARGUMENT.scr:186
    ctx:command("wait", "1 .5 Cam2B") -- ARGUMENT.scr:187
    do return ctx:exit("") end -- ARGUMENT.scr:188
end

script.labels["Cam2b"] = function(ctx)
    -- ARGUMENT.scr:191
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- ARGUMENT.scr:194
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:195
    ctx:command("getobjecthandle", "Camera1 g_hobject") -- ARGUMENT.scr:196
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:197
    ctx:command("screenfadein", ".5") -- ARGUMENT.scr:198
    ctx:command("getobjecthandle", "KiraCold g_hobject") -- ARGUMENT.scr:200
    ctx:trigger("g_hobject", "KillMarkel") -- ARGUMENT.scr:201
    ctx:command("removenpc", "2 g_hobject") -- ARGUMENT.scr:202
    ctx:trigger("hBjarni", "Shot1A") -- ARGUMENT.scr:204
    do return ctx:exit("") end -- ARGUMENT.scr:206
end

script.labels["Cam2"] = function(ctx)
    -- ARGUMENT.scr:209
    ctx:command("getobjecthandle", "Camera1 g_hobject") -- ARGUMENT.scr:212
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:213
    ctx:command("getobjecthandle", "Camera11 g_hobject") -- ARGUMENT.scr:214
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:215
    ctx:trigger("hSigmund", "Shot1A") -- ARGUMENT.scr:217
    ctx:command("wait", "1 4 Cam2c") -- ARGUMENT.scr:218
    do return ctx:exit("") end -- ARGUMENT.scr:219
end

script.labels["Cam2c"] = function(ctx)
    -- ARGUMENT.scr:222
    ctx:command("getobjecthandle", "Camera11 g_hobject") -- ARGUMENT.scr:225
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:226
    ctx:command("getobjecthandle", "Camera2 g_hobject") -- ARGUMENT.scr:227
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:228
    -- itrigger hSigmund Shot1A
    -- wait 1 2 Cam2b
    do return ctx:exit("") end -- ARGUMENT.scr:232
end

script.labels["Cam3"] = function(ctx)
    -- ARGUMENT.scr:237
    ctx:command("getobjecthandle", "Camera2 g_hobject") -- ARGUMENT.scr:240
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:241
    ctx:command("getobjecthandle", "Camera3 g_hobject") -- ARGUMENT.scr:242
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:243
    -- trigger Bjarni and Sigmund to Shake hands
    ctx:trigger("hBjarni", "Shake") -- ARGUMENT.scr:247
    ctx:trigger("hSigmund", "Shake") -- ARGUMENT.scr:248
    ctx:trigger("hKira", "Clap") -- ARGUMENT.scr:249
    ctx:trigger("hMarkel", "Clap") -- ARGUMENT.scr:250
    ctx:trigger("hSven", "Clap") -- ARGUMENT.scr:251
    ctx:trigger("hForad", "Clap") -- ARGUMENT.scr:252
    ctx:trigger("htryygva", "clap") -- ARGUMENT.scr:253
    mm9.gosub(script, ctx, "war") -- ARGUMENT.scr:254
    ctx:command("wait", "1 4 OnMarkel") -- ARGUMENT.scr:255
    do return ctx:exit("") end -- ARGUMENT.scr:257
end

script.labels["Cam4"] = function(ctx)
    -- ARGUMENT.scr:260
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:263
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:264
    ctx:command("getobjecthandle", "Camera1 g_hobject") -- ARGUMENT.scr:265
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:266
    -- trigger Bjarni and Sigmund to Shake hands
    ctx:trigger("hBjarni", "Speak2") -- ARGUMENT.scr:270
    do return ctx:exit("") end -- ARGUMENT.scr:272
end

script.labels["OnMarkel"] = function(ctx)
    -- ARGUMENT.scr:275
    ctx:command("getobjecthandle", "Camera3 g_hobject") -- ARGUMENT.scr:279
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:280
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:281
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:282
    ctx:trigger("hMarkel", "Scene2") -- ARGUMENT.scr:283
    do return ctx:exit("") end -- ARGUMENT.scr:285
end

script.labels["Sigmund3"] = function(ctx)
    -- ARGUMENT.scr:288
    ctx:command("getobjecthandle", "Camera1 g_hobject") -- ARGUMENT.scr:291
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:292
    ctx:command("getobjecthandle", "Camera2 g_hobject") -- ARGUMENT.scr:293
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:294
    ctx:trigger("hSigmund", "Speak3") -- ARGUMENT.scr:296
    do return ctx:exit("") end -- ARGUMENT.scr:297
end

script.labels["Markel4"] = function(ctx)
    -- ARGUMENT.scr:300
    ctx:command("getobjecthandle", "Camera2 g_hobject") -- ARGUMENT.scr:304
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:305
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:306
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:307
    ctx:trigger("hMarkel", "Speak4") -- ARGUMENT.scr:308
    do return ctx:exit("") end -- ARGUMENT.scr:310
end

script.labels["Kira5"] = function(ctx)
    -- ARGUMENT.scr:313
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:317
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:318
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- ARGUMENT.scr:319
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:320
    ctx:trigger("hKira", "Speak5") -- ARGUMENT.scr:321
    do return ctx:exit("") end -- ARGUMENT.scr:323
end

script.labels["Forad6"] = function(ctx)
    -- ARGUMENT.scr:328
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- ARGUMENT.scr:332
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:333
    ctx:command("getobjecthandle", "Camera6 g_hobject") -- ARGUMENT.scr:334
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:335
    ctx:trigger("hForad", "Speak6") -- ARGUMENT.scr:336
    do return ctx:exit("") end -- ARGUMENT.scr:338
end

script.labels["Kira7"] = function(ctx)
    -- ARGUMENT.scr:342
    ctx:command("getobjecthandle", "Camera6 g_hobject") -- ARGUMENT.scr:346
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:347
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- ARGUMENT.scr:348
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:349
    ctx:trigger("hKira", "Speak7") -- ARGUMENT.scr:350
    do return ctx:exit("") end -- ARGUMENT.scr:351
end

script.labels["Markel8"] = function(ctx)
    -- ARGUMENT.scr:355
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- ARGUMENT.scr:359
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:360
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:361
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:362
    ctx:trigger("hMarkel", "Speak8") -- ARGUMENT.scr:363
    do return ctx:exit("") end -- ARGUMENT.scr:365
end

script.labels["Bjarni9"] = function(ctx)
    -- ARGUMENT.scr:369
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:373
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:374
    ctx:command("getobjecthandle", "Camera7 g_hobject") -- ARGUMENT.scr:375
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:376
    ctx:trigger("hBjarni", "Speak9") -- ARGUMENT.scr:377
    do return ctx:exit("") end -- ARGUMENT.scr:379
end

script.labels["Kira10"] = function(ctx)
    -- ARGUMENT.scr:383
    -- getobjecthandle Camera1 g_hobject
    -- trigger g_hobject Off
    -- getobjecthandle Camera5 g_hobject
    -- trigger g_hobject On
    ctx:trigger("hKira", "Speak10") -- ARGUMENT.scr:391
    do return ctx:exit("") end -- ARGUMENT.scr:393
end

script.labels["Markel11"] = function(ctx)
    -- ARGUMENT.scr:397
    ctx:command("getobjecthandle", "Camera7 g_hobject") -- ARGUMENT.scr:401
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:402
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:403
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:404
    ctx:trigger("hMarkel", "Speak11") -- ARGUMENT.scr:405
    do return ctx:exit("") end -- ARGUMENT.scr:407
end

script.labels["Kira12"] = function(ctx)
    -- ARGUMENT.scr:412
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:416
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:417
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- ARGUMENT.scr:418
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:419
    ctx:trigger("hKira", "Speak12") -- ARGUMENT.scr:420
    do return ctx:exit("") end -- ARGUMENT.scr:422
end

script.labels["Markel13"] = function(ctx)
    -- ARGUMENT.scr:427
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- ARGUMENT.scr:431
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:432
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:433
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:434
    ctx:trigger("hMarkel", "Speak13") -- ARGUMENT.scr:435
    do return ctx:exit("") end -- ARGUMENT.scr:437
end

script.labels["Kira14"] = function(ctx)
    -- ARGUMENT.scr:440
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:444
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:445
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- ARGUMENT.scr:446
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:447
    ctx:trigger("hKira", "Speak14") -- ARGUMENT.scr:448
    do return ctx:exit("") end -- ARGUMENT.scr:450
end

script.labels["Markel15"] = function(ctx)
    -- ARGUMENT.scr:453
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- ARGUMENT.scr:457
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:458
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:459
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:460
    ctx:trigger("hMarkel", "Speak15") -- ARGUMENT.scr:461
    do return ctx:exit("") end -- ARGUMENT.scr:463
end

script.labels["Bjarni16"] = function(ctx)
    -- ARGUMENT.scr:466
    ctx:command("getobjecthandle", "Camera4 g_hobject") -- ARGUMENT.scr:470
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:471
    ctx:command("getobjecthandle", "Camera7 g_hobject") -- ARGUMENT.scr:472
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:473
    ctx:trigger("hBjarni", "Speak16") -- ARGUMENT.scr:474
    -- wait 1 2 KiraStand
    do return ctx:exit("") end -- ARGUMENT.scr:476
end

script.labels["KiraStand"] = function(ctx)
    -- ARGUMENT.scr:479
    ctx:trigger("hKira", "Stand") -- ARGUMENT.scr:482
    do return ctx:exit("") end -- ARGUMENT.scr:483
end

script.labels["OnKiraStand"] = function(ctx)
    -- ARGUMENT.scr:486
    ctx:command("getobjecthandle", "Camera7 g_hobject") -- ARGUMENT.scr:489
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:490
    ctx:command("getobjecthandle", "Camera8 g_hobject") -- ARGUMENT.scr:491
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:492
    do return ctx:exit("") end -- ARGUMENT.scr:493
end

script.labels["OnKiraStand2"] = function(ctx)
    -- ARGUMENT.scr:497
    ctx:command("getobjecthandle", "Camera9 g_hobject") -- ARGUMENT.scr:500
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:501
    ctx:command("getobjecthandle", "Camera8 g_hobject") -- ARGUMENT.scr:502
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:503
    -- trigger g_hobject play
    do return ctx:exit("") end -- ARGUMENT.scr:505
end

script.labels["Agree"] = function(ctx)
    -- ARGUMENT.scr:508
    ctx:command("getobjecthandle", "Camera10 g_hobject") -- ARGUMENT.scr:511
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:512
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- ARGUMENT.scr:513
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:514
    ctx:trigger("hsven", "Agree") -- ARGUMENT.scr:516
    ctx:trigger("hBjarni", "Agree") -- ARGUMENT.scr:517
    ctx:trigger("hsigmund", "Agree") -- ARGUMENT.scr:518
    ctx:trigger("hForad", "Agree") -- ARGUMENT.scr:519
    ctx:trigger("hTryygva", "Agree") -- ARGUMENT.scr:520
    ctx:command("wait", "1 2 Kira19") -- ARGUMENT.scr:521
    do return ctx:exit("") end -- ARGUMENT.scr:522
end

script.labels["KiraCam"] = function(ctx)
    -- ARGUMENT.scr:525
    ctx:command("getobjecthandle", "Camera8 g_hobject") -- ARGUMENT.scr:528
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:529
    ctx:command("getobjecthandle", "Camera9 g_hobject") -- ARGUMENT.scr:530
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:531
    do return ctx:exit("") end -- ARGUMENT.scr:532
end

script.labels["KiraCam2"] = function(ctx)
    -- ARGUMENT.scr:535
    ctx:command("getobjecthandle", "Camera9 g_hobject") -- ARGUMENT.scr:538
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:539
    ctx:command("getobjecthandle", "Camera10 g_hobject") -- ARGUMENT.scr:540
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:541
    ctx:trigger("hKira", "Speak18") -- ARGUMENT.scr:542
    do return ctx:exit("") end -- ARGUMENT.scr:543
end

script.labels["Kira19"] = function(ctx)
    -- ARGUMENT.scr:546
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- ARGUMENT.scr:549
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:550
    ctx:command("getobjecthandle", "Camera10 g_hobject") -- ARGUMENT.scr:551
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:552
    ctx:trigger("hKira", "Speak19") -- ARGUMENT.scr:553
    do return ctx:exit("") end -- ARGUMENT.scr:554
end

script.labels["Forad20"] = function(ctx)
    -- ARGUMENT.scr:557
    ctx:command("getobjecthandle", "Camera10 g_hobject") -- ARGUMENT.scr:560
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:561
    ctx:command("getobjecthandle", "Camera6 g_hobject") -- ARGUMENT.scr:562
    ctx:trigger("g_hobject", "On") -- ARGUMENT.scr:563
    ctx:trigger("hForad", "Speak20") -- ARGUMENT.scr:564
    do return ctx:exit("") end -- ARGUMENT.scr:565
end

script.labels["OnDone"] = function(ctx)
    -- ARGUMENT.scr:569
    ctx:command("ncamcount", "= nCamCount + 1") -- ARGUMENT.scr:572
    if ctx:condition("nCamCount==1") then -- ARGUMENT.scr:574
        -- Bjarni signs
        mm9.gosub(script, ctx, "Cam1") -- ARGUMENT.scr:576
        do return ctx:exit("") end -- ARGUMENT.scr:577
    end -- ARGUMENT.scr:578
    if ctx:condition("nCamCount==2") then -- ARGUMENT.scr:581
        -- sigmund signs
        mm9.gosub(script, ctx, "Cam2") -- ARGUMENT.scr:583
        do return ctx:exit("") end -- ARGUMENT.scr:584
    end -- ARGUMENT.scr:585
    if ctx:condition("nCamCount==3") then -- ARGUMENT.scr:588
        -- shake hands and clap
        mm9.gosub(script, ctx, "Cam3") -- ARGUMENT.scr:590
        do return ctx:exit("") end -- ARGUMENT.scr:591
    end -- ARGUMENT.scr:592
    if ctx:condition("nCamCount==4") then -- ARGUMENT.scr:594
        mm9.gosub(script, ctx, "Cam4") -- ARGUMENT.scr:595
        -- Bjarni "Who gives a damn..."
        do return ctx:exit("") end -- ARGUMENT.scr:597
    end -- ARGUMENT.scr:598
    if ctx:condition("nCamCount==5") then -- ARGUMENT.scr:600
        mm9.gosub(script, ctx, "Sigmund3") -- ARGUMENT.scr:601
        -- "...I Agree with you..."
        do return ctx:exit("") end -- ARGUMENT.scr:603
    end -- ARGUMENT.scr:604
    if ctx:condition("nCamCount==6") then -- ARGUMENT.scr:606
        mm9.gosub(script, ctx, "Markel4") -- ARGUMENT.scr:607
        -- "What do you know about fighting..."
        do return ctx:exit("") end -- ARGUMENT.scr:609
    end -- ARGUMENT.scr:610
    if ctx:condition("nCamCount==7") then -- ARGUMENT.scr:613
        mm9.gosub(script, ctx, "Kira5") -- ARGUMENT.scr:614
        -- "...please go..."
        do return ctx:exit("") end -- ARGUMENT.scr:616
    end -- ARGUMENT.scr:617
    if ctx:condition("nCamCount==8") then -- ARGUMENT.scr:619
        mm9.gosub(script, ctx, "Forad6") -- ARGUMENT.scr:620
        -- "Don't go, we need you to stay"
        do return ctx:exit("") end -- ARGUMENT.scr:622
    end -- ARGUMENT.scr:623
    if ctx:condition("nCamCount==9") then -- ARGUMENT.scr:625
        mm9.gosub(script, ctx, "Kira7") -- ARGUMENT.scr:626
        -- "If he would shut up about that book of his..."
        do return ctx:exit("") end -- ARGUMENT.scr:628
    end -- ARGUMENT.scr:629
    if ctx:condition("nCamCount==10") then -- ARGUMENT.scr:631
        mm9.gosub(script, ctx, "Markel8") -- ARGUMENT.scr:632
        -- "Maybe it's not me.."
        do return ctx:exit("") end -- ARGUMENT.scr:634
    end -- ARGUMENT.scr:635
    if ctx:condition("nCamCount==11") then -- ARGUMENT.scr:637
        mm9.gosub(script, ctx, "Bjarni9") -- ARGUMENT.scr:638
        -- "watch your mouth, boy"
        do return ctx:exit("") end -- ARGUMENT.scr:640
    end -- ARGUMENT.scr:641
    if ctx:condition("nCamCount==12") then -- ARGUMENT.scr:643
        mm9.gosub(script, ctx, "Kira10") -- ARGUMENT.scr:644
        -- "Bjarni please,...Yesterday's beef"
        do return ctx:exit("") end -- ARGUMENT.scr:646
    end -- ARGUMENT.scr:647
    if ctx:condition("nCamCount==13") then -- ARGUMENT.scr:649
        mm9.gosub(script, ctx, "Markel11") -- ARGUMENT.scr:650
        -- "Is that what you think...what do you do..."
        do return ctx:exit("") end -- ARGUMENT.scr:652
    end -- ARGUMENT.scr:653
    if ctx:condition("nCamCount==14") then -- ARGUMENT.scr:655
        mm9.gosub(script, ctx, "Kira12") -- ARGUMENT.scr:656
        -- "I will not play this game with you..."
        do return ctx:exit("") end -- ARGUMENT.scr:658
    end -- ARGUMENT.scr:659
    if ctx:condition("nCamCount==15") then -- ARGUMENT.scr:661
        mm9.gosub(script, ctx, "Markel13") -- ARGUMENT.scr:662
        -- "Of course you won't...Don't know the answer..."
        do return ctx:exit("") end -- ARGUMENT.scr:664
    end -- ARGUMENT.scr:665
    if ctx:condition("nCamCount==16") then -- ARGUMENT.scr:667
        mm9.gosub(script, ctx, "Kira14") -- ARGUMENT.scr:668
        -- "Why don't I put my sword in your belly?"
        do return ctx:exit("") end -- ARGUMENT.scr:670
    end -- ARGUMENT.scr:671
    if ctx:condition("nCamCount==17") then -- ARGUMENT.scr:673
        mm9.gosub(script, ctx, "Markel15") -- ARGUMENT.scr:674
        -- "always the violence...rotten brains"
        do return ctx:exit("") end -- ARGUMENT.scr:676
    end -- ARGUMENT.scr:677
    if ctx:condition("nCamCount==18") then -- ARGUMENT.scr:679
        mm9.gosub(script, ctx, "Bjarni16") -- ARGUMENT.scr:680
        -- "You've done it now..."
        do return ctx:exit("") end -- ARGUMENT.scr:682
    end -- ARGUMENT.scr:683
    if ctx:condition("nCamCount==19") then -- ARGUMENT.scr:685
        mm9.gosub(script, ctx, "KiraStand") -- ARGUMENT.scr:686
        -- wave off Bjarni and stand
        do return ctx:exit("") end -- ARGUMENT.scr:688
    end -- ARGUMENT.scr:689
    if ctx:condition("nCamCount==20") then -- ARGUMENT.scr:691
        mm9.gosub(script, ctx, "OnKiraStand") -- ARGUMENT.scr:692
        -- switch to behind Kira cam wide
        do return ctx:exit("") end -- ARGUMENT.scr:694
    end -- ARGUMENT.scr:695
    if ctx:condition("nCamCount==21") then -- ARGUMENT.scr:697
        mm9.gosub(script, ctx, "KiraCam") -- ARGUMENT.scr:698
        -- switch to behind Markel Cam
        do return ctx:exit("") end -- ARGUMENT.scr:700
    end -- ARGUMENT.scr:701
    if ctx:condition("nCamCount==22") then -- ARGUMENT.scr:703
        mm9.gosub(script, ctx, "KiraCam2") -- ARGUMENT.scr:704
        -- "now may we get down to business?"
        do return ctx:exit("") end -- ARGUMENT.scr:706
    end -- ARGUMENT.scr:707
    if ctx:condition("nCamCount==23") then -- ARGUMENT.scr:709
        mm9.gosub(script, ctx, "Agree") -- ARGUMENT.scr:710
        -- The Jarls Agree
        do return ctx:exit("") end -- ARGUMENT.scr:712
    end -- ARGUMENT.scr:713
    if ctx:condition("nCamCount==24") then -- ARGUMENT.scr:715
        -- Gosub Forad20
        mm9.gosub(script, ctx, "end") -- ARGUMENT.scr:717
        -- "very well...a week's time"
        do return ctx:exit("") end -- ARGUMENT.scr:719
    end -- ARGUMENT.scr:720
    if ctx:condition("nCamCount==25") then -- ARGUMENT.scr:723
        mm9.gosub(script, ctx, "End") -- ARGUMENT.scr:724
        -- thank you for playing, and good night!
        do return ctx:exit("") end -- ARGUMENT.scr:726
    end -- ARGUMENT.scr:727
    do return ctx:exit("") end -- ARGUMENT.scr:729
end

script.labels["End"] = function(ctx)
    -- ARGUMENT.scr:731
    mm9.gosub(script, ctx, "war") -- ARGUMENT.scr:734
    ctx:command("screenfadeout", "1") -- ARGUMENT.scr:735
    ctx:command("wait", "1 1 End2") -- ARGUMENT.scr:736
    do return ctx:exit("") end -- ARGUMENT.scr:737
end

script.labels["End2"] = function(ctx)
    -- ARGUMENT.scr:741
    ctx:command("getobjecthandle", "Camera10 g_hobject") -- ARGUMENT.scr:745
    ctx:trigger("g_hobject", "Off") -- ARGUMENT.scr:746
    ctx:command("getobjecthandle", "YrsatheTroll0 g_hobject") -- ARGUMENT.scr:747
    ctx:trigger("g_hobject", "appear") -- ARGUMENT.scr:748
    ctx:command("letterbox", "false") -- ARGUMENT.scr:749
    ctx:command("screenfadein", "1") -- ARGUMENT.scr:750
    do return ctx:exit("") end -- ARGUMENT.scr:751
end

script.labels["Main"] = function(ctx)
    -- ARGUMENT.scr:754
    -- TraceOn ;delete me!!
    ctx:addTrigger("Done", "OnDone") -- ARGUMENT.scr:759
    ctx:addTrigger("ForceStart", "ForceStart") -- ARGUMENT.scr:760
    ctx:addTrigger("Start", "Init") -- ARGUMENT.scr:761
    do return ctx:exit("") end -- ARGUMENT.scr:763
end

return script
