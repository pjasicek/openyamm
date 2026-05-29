-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PICKMON.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- PickiMon.inc
-- By Timmy
-- Picks a random monster from the list
-- 11/29/01
script.labels["PickMonster"] = function(ctx)
    -- PICKMON.inc:25
    if ctx:condition("g_ntemp>=1") then -- PICKMON.inc:28
        if ctx:condition("g_ntemp<=4)") then -- PICKMON.inc:29
            mm9.gosub(script, ctx, "Group1") -- PICKMON.inc:30
            do return ctx:exit("") end -- PICKMON.inc:31
        end -- PICKMON.inc:32
    end -- PICKMON.inc:33
    if ctx:condition("g_ntemp>=5") then -- PICKMON.inc:35
        if ctx:condition("g_ntemp<=8") then -- PICKMON.inc:36
            mm9.gosub(script, ctx, "Group2") -- PICKMON.inc:37
            do return ctx:exit("") end -- PICKMON.inc:38
        end -- PICKMON.inc:39
    end -- PICKMON.inc:40
    if ctx:condition("g_ntemp>=9") then -- PICKMON.inc:42
        if ctx:condition("g_ntemp<=11") then -- PICKMON.inc:43
            mm9.gosub(script, ctx, "Group3") -- PICKMON.inc:44
            do return ctx:exit("") end -- PICKMON.inc:45
        end -- PICKMON.inc:46
    end -- PICKMON.inc:47
    if ctx:condition("g_ntemp>=12") then -- PICKMON.inc:49
        if ctx:condition("g_ntemp<=14") then -- PICKMON.inc:50
            mm9.gosub(script, ctx, "Group4") -- PICKMON.inc:51
            do return ctx:exit("") end -- PICKMON.inc:52
        end -- PICKMON.inc:53
    end -- PICKMON.inc:54
    if ctx:condition("g_ntemp>=15") then -- PICKMON.inc:56
        if ctx:condition("g_ntemp<=16") then -- PICKMON.inc:57
            mm9.gosub(script, ctx, "Group5") -- PICKMON.inc:58
            do return ctx:exit("") end -- PICKMON.inc:59
        end -- PICKMON.inc:60
    end -- PICKMON.inc:61
    if ctx:condition("g_ntemp>=17") then -- PICKMON.inc:63
        if ctx:condition("g_ntemp<=19") then -- PICKMON.inc:64
            mm9.gosub(script, ctx, "Group6") -- PICKMON.inc:65
            do return ctx:exit("") end -- PICKMON.inc:66
        end -- PICKMON.inc:67
    end -- PICKMON.inc:68
    if ctx:condition("g_ntemp>=20") then -- PICKMON.inc:70
        if ctx:condition("g_ntemp<=21") then -- PICKMON.inc:71
            mm9.gosub(script, ctx, "Group7") -- PICKMON.inc:72
            do return ctx:exit("") end -- PICKMON.inc:73
        end -- PICKMON.inc:74
    end -- PICKMON.inc:75
    if ctx:condition("g_ntemp>=22") then -- PICKMON.inc:77
        if ctx:condition("g_ntemp<=23") then -- PICKMON.inc:78
            mm9.gosub(script, ctx, "Group8") -- PICKMON.inc:79
            do return ctx:exit("") end -- PICKMON.inc:80
        end -- PICKMON.inc:81
    end -- PICKMON.inc:82
    if ctx:condition("g_ntemp>=24") then -- PICKMON.inc:84
        if ctx:condition("g_ntemp<=26") then -- PICKMON.inc:85
            mm9.gosub(script, ctx, "Group9") -- PICKMON.inc:86
            do return ctx:exit("") end -- PICKMON.inc:87
        end -- PICKMON.inc:88
    end -- PICKMON.inc:89
    if ctx:condition("g_ntemp>=27") then -- PICKMON.inc:91
        if ctx:condition("g_ntemp<=29") then -- PICKMON.inc:92
            mm9.gosub(script, ctx, "Group10") -- PICKMON.inc:93
            do return ctx:exit("") end -- PICKMON.inc:94
        end -- PICKMON.inc:95
    end -- PICKMON.inc:96
    if ctx:condition("g_ntemp>=30") then -- PICKMON.inc:98
        if ctx:condition("g_ntemp<=32") then -- PICKMON.inc:99
            mm9.gosub(script, ctx, "Group11") -- PICKMON.inc:100
            do return ctx:exit("") end -- PICKMON.inc:101
        end -- PICKMON.inc:102
    end -- PICKMON.inc:103
    if ctx:condition("g_ntemp==33") then -- PICKMON.inc:105
        mm9.gosub(script, ctx, "Group12") -- PICKMON.inc:106
        do return ctx:exit("") end -- PICKMON.inc:107
    end -- PICKMON.inc:108
    if ctx:condition("g_ntemp>=34") then -- PICKMON.inc:110
        if ctx:condition("g_ntemp<=37") then -- PICKMON.inc:111
            mm9.gosub(script, ctx, "Group13") -- PICKMON.inc:112
            do return ctx:exit("") end -- PICKMON.inc:113
        end -- PICKMON.inc:114
    end -- PICKMON.inc:115
    if ctx:condition("g_ntemp>=38") then -- PICKMON.inc:117
        if ctx:condition("g_ntemp<=39") then -- PICKMON.inc:118
            mm9.gosub(script, ctx, "Group14") -- PICKMON.inc:119
            do return ctx:exit("") end -- PICKMON.inc:120
        end -- PICKMON.inc:121
    end -- PICKMON.inc:122
    if ctx:condition("g_ntemp>=40") then -- PICKMON.inc:124
        if ctx:condition("g_ntemp<=43") then -- PICKMON.inc:125
            mm9.gosub(script, ctx, "Group15") -- PICKMON.inc:126
            do return ctx:exit("") end -- PICKMON.inc:127
        end -- PICKMON.inc:128
    end -- PICKMON.inc:129
    if ctx:condition("g_ntemp>=44") then -- PICKMON.inc:131
        if ctx:condition("g_ntemp<=47") then -- PICKMON.inc:132
            mm9.gosub(script, ctx, "Group16") -- PICKMON.inc:133
            do return ctx:exit("") end -- PICKMON.inc:134
        end -- PICKMON.inc:135
    end -- PICKMON.inc:136
    if ctx:condition("g_ntemp>=48") then -- PICKMON.inc:138
        if ctx:condition("g_ntemp<=53") then -- PICKMON.inc:139
            mm9.gosub(script, ctx, "Group17") -- PICKMON.inc:140
            do return ctx:exit("") end -- PICKMON.inc:141
        end -- PICKMON.inc:142
    end -- PICKMON.inc:143
    if ctx:condition("g_ntemp>=54") then -- PICKMON.inc:145
        if ctx:condition("g_ntemp<=58") then -- PICKMON.inc:146
            mm9.gosub(script, ctx, "Group18") -- PICKMON.inc:147
            do return ctx:exit("") end -- PICKMON.inc:148
        end -- PICKMON.inc:149
    end -- PICKMON.inc:150
    if ctx:condition("g_ntemp>=59") then -- PICKMON.inc:151
        if ctx:condition("g_ntemp<=64") then -- PICKMON.inc:152
            mm9.gosub(script, ctx, "Group19") -- PICKMON.inc:153
            do return ctx:exit("") end -- PICKMON.inc:154
        end -- PICKMON.inc:155
    end -- PICKMON.inc:156
    if ctx:condition("g_ntemp>=65") then -- PICKMON.inc:158
        if ctx:condition("g_ntemp<=74") then -- PICKMON.inc:159
            mm9.gosub(script, ctx, "Group20") -- PICKMON.inc:160
            do return ctx:exit("") end -- PICKMON.inc:161
        end -- PICKMON.inc:162
    end -- PICKMON.inc:163
    if ctx:condition("g_ntemp>75") then -- PICKMON.inc:165
        mm9.gosub(script, ctx, "Group21") -- PICKMON.inc:166
        do return ctx:exit("") end -- PICKMON.inc:167
    end -- PICKMON.inc:169
    do return ctx:exit("") end -- PICKMON.inc:173
end

script.labels["Group1"] = function(ctx)
    -- PICKMON.inc:176
    -- levels 1 - 4
    ctx:randomInt(1, 4, "nMonTemp") -- PICKMON.inc:180
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:182
        ctx:set("sMonster_Temp", "DragonFlyMite") -- PICKMON.inc:183
        ctx:state().nMonster_Level = 2 -- PICKMON.inc:184
        do return ctx:exit("") end -- PICKMON.inc:185
    end -- PICKMON.inc:186
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:188
        ctx:set("sMonster_Temp", "DragonFly") -- PICKMON.inc:189
        ctx:state().nMonster_Level = 3 -- PICKMON.inc:190
        do return ctx:exit("") end -- PICKMON.inc:191
    end -- PICKMON.inc:192
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:194
        ctx:set("sMonster_Temp", "Imply") -- PICKMON.inc:195
        ctx:state().nMonster_Level = 4 -- PICKMON.inc:196
        do return ctx:exit("") end -- PICKMON.inc:197
    end -- PICKMON.inc:198
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:202
        ctx:set("sMonster_Temp", "Skeletoid") -- PICKMON.inc:203
        ctx:state().nMonster_Level = 4 -- PICKMON.inc:204
        do return ctx:exit("") end -- PICKMON.inc:205
    end -- PICKMON.inc:206
    do return ctx:exit("") end -- PICKMON.inc:207
end

script.labels["Group2"] = function(ctx)
    -- PICKMON.inc:210
    -- levels 5 - 8
    ctx:randomInt(1, 6, "nMonTemp") -- PICKMON.inc:214
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:216
        ctx:set("sMonster_Temp", "FireDragonFly") -- PICKMON.inc:217
        ctx:state().nMonster_Level = 5 -- PICKMON.inc:218
        do return ctx:exit("") end -- PICKMON.inc:219
    end -- PICKMON.inc:220
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:222
        ctx:set("sMonster_Temp", "NagateHatchling") -- PICKMON.inc:223
        ctx:state().nMonster_Level = 6 -- PICKMON.inc:224
        do return ctx:exit("") end -- PICKMON.inc:225
    end -- PICKMON.inc:226
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:228
        ctx:set("sMonster_Temp", "Imp") -- PICKMON.inc:229
        ctx:state().nMonster_Level = 6 -- PICKMON.inc:230
        do return ctx:exit("") end -- PICKMON.inc:231
    end -- PICKMON.inc:232
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:234
        ctx:set("sMonster_Temp", "BoneThrasher") -- PICKMON.inc:235
        ctx:state().nMonster_Level = 8 -- PICKMON.inc:236
        do return ctx:exit("") end -- PICKMON.inc:237
    end -- PICKMON.inc:238
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:240
        ctx:set("sMonster_Temp", "FieldThrall") -- PICKMON.inc:241
        ctx:state().nMonster_Level = 8 -- PICKMON.inc:242
        do return ctx:exit("") end -- PICKMON.inc:243
    end -- PICKMON.inc:244
    if ctx:condition("nMonTemp==6") then -- PICKMON.inc:246
        ctx:set("sMonster_Temp", "Cutpurse") -- PICKMON.inc:247
        ctx:state().nMonster_Level = 8 -- PICKMON.inc:248
        do return ctx:exit("") end -- PICKMON.inc:249
    end -- PICKMON.inc:250
    do return ctx:exit("") end -- PICKMON.inc:251
end

script.labels["Group3"] = function(ctx)
    -- PICKMON.inc:255
    -- levels 9 - 11
    ctx:randomInt(1, 5, "nMonTemp") -- PICKMON.inc:259
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:261
        ctx:set("sMonster_Temp", "Rotter") -- PICKMON.inc:262
        ctx:state().nMonster_Level = 9 -- PICKMON.inc:263
        do return ctx:exit("") end -- PICKMON.inc:264
    end -- PICKMON.inc:265
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:267
        ctx:set("sMonster_Temp", "Nagate") -- PICKMON.inc:268
        ctx:state().nMonster_Level = 10 -- PICKMON.inc:269
        do return ctx:exit("") end -- PICKMON.inc:270
    end -- PICKMON.inc:271
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:274
        ctx:set("sMonster_Temp", "ImpElder") -- PICKMON.inc:275
        ctx:state().nMonster_Level = 10 -- PICKMON.inc:276
        do return ctx:exit("") end -- PICKMON.inc:277
    end -- PICKMON.inc:278
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:282
        ctx:set("sMonster_Temp", "Troglodyte") -- PICKMON.inc:283
        ctx:state().nMonster_Level = 10 -- PICKMON.inc:284
        do return ctx:exit("") end -- PICKMON.inc:285
    end -- PICKMON.inc:286
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:288
        ctx:set("sMonster_Temp", "DwarvenGuard") -- PICKMON.inc:289
        ctx:state().nMonster_Level = 10 -- PICKMON.inc:290
        do return ctx:exit("") end -- PICKMON.inc:291
    end -- PICKMON.inc:292
    do return ctx:exit("") end -- PICKMON.inc:293
end

script.labels["Group4"] = function(ctx)
    -- PICKMON.inc:296
    -- levels 12 - 14
    ctx:randomInt(1, 5, "nMonTemp") -- PICKMON.inc:300
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:302
        ctx:set("sMonster_Temp", "Troglodyte") -- PICKMON.inc:303
        ctx:state().nMonster_Level = 12 -- PICKMON.inc:305
        do return ctx:exit("") end -- PICKMON.inc:306
    end -- PICKMON.inc:307
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:309
        ctx:set("sMonster_Temp", "Thrall") -- PICKMON.inc:310
        ctx:state().nMonster_Level = 12 -- PICKMON.inc:311
        do return ctx:exit("") end -- PICKMON.inc:312
    end -- PICKMON.inc:313
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:315
        ctx:set("sMonster_Temp", "Dripper") -- PICKMON.inc:316
        ctx:state().nMonster_Level = 13 -- PICKMON.inc:317
        do return ctx:exit("") end -- PICKMON.inc:318
    end -- PICKMON.inc:319
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:323
        ctx:set("sMonster_Temp", "HalfOrcRecruit") -- PICKMON.inc:324
        ctx:state().nMonster_Level = 14 -- PICKMON.inc:325
        do return ctx:exit("") end -- PICKMON.inc:326
    end -- PICKMON.inc:327
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:330
        ctx:set("sMonster_Temp", "Burgler") -- PICKMON.inc:331
        ctx:state().nMonster_Level = 14 -- PICKMON.inc:332
        do return ctx:exit("") end -- PICKMON.inc:333
    end -- PICKMON.inc:334
    do return ctx:exit("") end -- PICKMON.inc:335
end

script.labels["Group5"] = function(ctx)
    -- PICKMON.inc:338
    -- levels 15 - 16
    ctx:randomInt(1, 4, "nMonTemp") -- PICKMON.inc:342
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:344
        ctx:set("sMonster_Temp", "Gezzamptling") -- PICKMON.inc:345
        ctx:state().nMonster_Level = 15 -- PICKMON.inc:346
        do return ctx:exit("") end -- PICKMON.inc:347
    end -- PICKMON.inc:348
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:349
        ctx:set("sMonster_Temp", "Basilisk") -- PICKMON.inc:350
        ctx:state().nMonster_Level = 15 -- PICKMON.inc:351
        do return ctx:exit("") end -- PICKMON.inc:352
    end -- PICKMON.inc:353
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:356
        ctx:set("sMonster_Temp", "Skeleton") -- PICKMON.inc:357
        ctx:state().nMonster_Level = 16 -- PICKMON.inc:358
        do return ctx:exit("") end -- PICKMON.inc:359
    end -- PICKMON.inc:360
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:362
        ctx:set("sMonster_Temp", "Skeleton") -- PICKMON.inc:363
        ctx:state().nMonster_Level = 16 -- PICKMON.inc:364
        do return ctx:exit("") end -- PICKMON.inc:365
    end -- PICKMON.inc:366
    do return ctx:exit("") end -- PICKMON.inc:367
end

script.labels["Group6"] = function(ctx)
    -- PICKMON.inc:371
    -- levels 17 - 19
    ctx:randomInt(1, 4, "nMonTemp") -- PICKMON.inc:375
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:377
        ctx:set("sMonster_Temp", "TroglodyteWren") -- PICKMON.inc:378
        ctx:state().nMonster_Level = 17 -- PICKMON.inc:379
        do return ctx:exit("") end -- PICKMON.inc:380
    end -- PICKMON.inc:381
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:383
        ctx:set("sMonster_Temp", "Zombie") -- PICKMON.inc:384
        ctx:state().nMonster_Level = 17 -- PICKMON.inc:385
        do return ctx:exit("") end -- PICKMON.inc:386
    end -- PICKMON.inc:387
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:389
        ctx:set("sMonster_Temp", "ThrallMaster") -- PICKMON.inc:390
        ctx:state().nMonster_Level = 18 -- PICKMON.inc:391
        do return ctx:exit("") end -- PICKMON.inc:392
    end -- PICKMON.inc:393
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:395
        ctx:set("sMonster_Temp", "Bigfoot") -- PICKMON.inc:396
        ctx:state().nMonster_Level = 18 -- PICKMON.inc:397
        do return ctx:exit("") end -- PICKMON.inc:398
    end -- PICKMON.inc:399
    do return ctx:exit("") end -- PICKMON.inc:400
end

script.labels["Group7"] = function(ctx)
    -- PICKMON.inc:404
    -- levels 20 -21
    ctx:randomInt(1, 9, "nMonTemp") -- PICKMON.inc:408
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:410
        ctx:set("sMonster_Temp", "PoorTownGuard2") -- PICKMON.inc:411
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:412
        do return ctx:exit("") end -- PICKMON.inc:413
    end -- PICKMON.inc:414
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:416
        ctx:set("sMonster_Temp", "Gezzampt") -- PICKMON.inc:417
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:418
        do return ctx:exit("") end -- PICKMON.inc:419
    end -- PICKMON.inc:420
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:422
        ctx:set("sMonster_Temp", "PoorTownGuard1") -- PICKMON.inc:423
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:424
        do return ctx:exit("") end -- PICKMON.inc:425
    end -- PICKMON.inc:426
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:428
        ctx:set("sMonster_Temp", "Guard") -- PICKMON.inc:429
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:430
        do return ctx:exit("") end -- PICKMON.inc:431
    end -- PICKMON.inc:432
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:434
        ctx:set("sMonster_Temp", "GreyWolf") -- PICKMON.inc:435
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:436
        do return ctx:exit("") end -- PICKMON.inc:437
    end -- PICKMON.inc:438
    if ctx:condition("nMonTemp==6") then -- PICKMON.inc:440
        ctx:set("sMonster_Temp", "DwarvenSoldier") -- PICKMON.inc:441
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:442
        do return ctx:exit("") end -- PICKMON.inc:443
    end -- PICKMON.inc:444
    if ctx:condition("nMonTemp==7") then -- PICKMON.inc:446
        ctx:set("sMonster_Temp", "CanopicMummy") -- PICKMON.inc:447
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:448
        do return ctx:exit("") end -- PICKMON.inc:449
    end -- PICKMON.inc:450
    if ctx:condition("nMonTemp==8") then -- PICKMON.inc:451
        ctx:set("sMonster_Temp", "Ghast") -- PICKMON.inc:452
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:453
        do return ctx:exit("") end -- PICKMON.inc:454
    end -- PICKMON.inc:455
    if ctx:condition("nMonTemp==9") then -- PICKMON.inc:457
        ctx:set("sMonster_Temp", "Bloodsucker") -- PICKMON.inc:458
        ctx:state().nMonster_Level = 20 -- PICKMON.inc:459
        do return ctx:exit("") end -- PICKMON.inc:460
    end -- PICKMON.inc:461
    do return ctx:exit("") end -- PICKMON.inc:462
end

script.labels["Group8"] = function(ctx)
    -- PICKMON.inc:465
    -- levels 22 - 23
    ctx:randomInt(1, 5, "nMonTemp") -- PICKMON.inc:469
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:471
        ctx:set("sMonster_Temp", "Trellborg") -- PICKMON.inc:472
        ctx:state().nMonster_Level = 22 -- PICKMON.inc:473
        do return ctx:exit("") end -- PICKMON.inc:474
    end -- PICKMON.inc:475
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:476
        ctx:set("sMonster_Temp", "Bandit") -- PICKMON.inc:477
        ctx:state().nMonster_Level = 22 -- PICKMON.inc:478
        do return ctx:exit("") end -- PICKMON.inc:479
    end -- PICKMON.inc:480
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:482
        ctx:set("sMonster_Temp", "Magreeb") -- PICKMON.inc:483
        ctx:state().nMonster_Level = 22 -- PICKMON.inc:484
        do return ctx:exit("") end -- PICKMON.inc:485
    end -- PICKMON.inc:486
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:489
        ctx:set("sMonster_Temp", "SkeletonWarrior") -- PICKMON.inc:490
        ctx:state().nMonster_Level = 22 -- PICKMON.inc:491
        do return ctx:exit("") end -- PICKMON.inc:492
    end -- PICKMON.inc:493
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:495
        ctx:set("sMonster_Temp", "FibraseBasilisk") -- PICKMON.inc:496
        ctx:state().nMonster_Level = 23 -- PICKMON.inc:497
        do return ctx:exit("") end -- PICKMON.inc:498
    end -- PICKMON.inc:499
    do return ctx:exit("") end -- PICKMON.inc:500
end

script.labels["Group9"] = function(ctx)
    -- PICKMON.inc:503
    -- levels 24 - 26
    ctx:randomInt(1, 3, "nMonTemp") -- PICKMON.inc:507
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:509
        ctx:set("sMonster_Temp", "TroglodyteGnoll") -- PICKMON.inc:510
        ctx:state().nMonster_Level = 24 -- PICKMON.inc:511
        do return ctx:exit("") end -- PICKMON.inc:512
    end -- PICKMON.inc:513
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:516
        ctx:set("sMonster_Temp", "HalfOrcSoldier") -- PICKMON.inc:517
        ctx:state().nMonster_Level = 24 -- PICKMON.inc:518
        do return ctx:exit("") end -- PICKMON.inc:519
    end -- PICKMON.inc:520
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:522
        ctx:set("sMonster_Temp", "TroglodyteGnoll") -- PICKMON.inc:523
        ctx:state().nMonster_Level = 24 -- PICKMON.inc:524
        do return ctx:exit("") end -- PICKMON.inc:525
    end -- PICKMON.inc:526
    do return ctx:exit("") end -- PICKMON.inc:527
end

script.labels["Group10"] = function(ctx)
    -- PICKMON.inc:530
    -- levels 27 -29
    ctx:randomInt(1, 6, "nMonTemp") -- PICKMON.inc:534
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:536
        ctx:set("sMonster_Temp", "WingedOddity") -- PICKMON.inc:537
        ctx:state().nMonster_Level = 27 -- PICKMON.inc:538
        do return ctx:exit("") end -- PICKMON.inc:539
    end -- PICKMON.inc:540
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:543
        ctx:set("sMonster_Temp", "Ghoul") -- PICKMON.inc:544
        ctx:state().nMonster_Level = 27 -- PICKMON.inc:545
        do return ctx:exit("") end -- PICKMON.inc:546
    end -- PICKMON.inc:547
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:549
        ctx:set("sMonster_Temp", "GuardSegeant") -- PICKMON.inc:550
        ctx:state().nMonster_Level = 28 -- PICKMON.inc:551
        do return ctx:exit("") end -- PICKMON.inc:552
    end -- PICKMON.inc:553
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:555
        ctx:set("sMonster_Temp", "Sasquatch") -- PICKMON.inc:556
        ctx:state().nMonster_Level = 28 -- PICKMON.inc:557
        do return ctx:exit("") end -- PICKMON.inc:558
    end -- PICKMON.inc:559
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:561
        ctx:set("sMonster_Temp", "Sasquatch") -- PICKMON.inc:562
        ctx:state().nMonster_Level = 28 -- PICKMON.inc:563
        do return ctx:exit("") end -- PICKMON.inc:564
    end -- PICKMON.inc:565
    if ctx:condition("nMonTemp==6") then -- PICKMON.inc:568
        ctx:set("sMonster_Temp", "GezzamptElder") -- PICKMON.inc:569
        ctx:state().nMonster_Level = 28 -- PICKMON.inc:570
        do return ctx:exit("") end -- PICKMON.inc:571
    end -- PICKMON.inc:572
    do return ctx:exit("") end -- PICKMON.inc:573
end

script.labels["Group11"] = function(ctx)
    -- PICKMON.inc:576
    -- levels 30 - 32
    ctx:randomInt(1, 5, "nMonTemp") -- PICKMON.inc:580
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:582
        ctx:set("sMonster_Temp", "RedWolf") -- PICKMON.inc:583
        ctx:state().nMonster_Level = 30 -- PICKMON.inc:584
        do return ctx:exit("") end -- PICKMON.inc:585
    end -- PICKMON.inc:586
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:587
        ctx:set("sMonster_Temp", "EmbalmedMummy") -- PICKMON.inc:588
        ctx:state().nMonster_Level = 30 -- PICKMON.inc:589
        do return ctx:exit("") end -- PICKMON.inc:590
    end -- PICKMON.inc:591
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:593
        ctx:set("sMonster_Temp", "DwarvenCommander") -- PICKMON.inc:594
        ctx:state().nMonster_Level = 30 -- PICKMON.inc:595
        do return ctx:exit("") end -- PICKMON.inc:596
    end -- PICKMON.inc:597
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:599
        ctx:set("sMonster_Temp", "KingBasilisk") -- PICKMON.inc:600
        ctx:state().nMonster_Level = 30 -- PICKMON.inc:601
        do return ctx:exit("") end -- PICKMON.inc:602
    end -- PICKMON.inc:603
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:605
        ctx:set("sMonster_Temp", "KingBasilisk") -- PICKMON.inc:606
        ctx:state().nMonster_Level = 30 -- PICKMON.inc:607
        do return ctx:exit("") end -- PICKMON.inc:608
    end -- PICKMON.inc:609
    do return ctx:exit("") end -- PICKMON.inc:610
end

script.labels["Group12"] = function(ctx)
    -- PICKMON.inc:613
    -- levels 33-33
    ctx:randomInt(1, 6, "nMonTemp") -- PICKMON.inc:617
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:619
        ctx:set("sMonster_Temp", "SkeletonMaster") -- PICKMON.inc:620
        ctx:state().nMonster_Level = 33 -- PICKMON.inc:621
        do return ctx:exit("") end -- PICKMON.inc:622
    end -- PICKMON.inc:623
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:625
        ctx:set("sMonster_Temp", "Magreeb2") -- PICKMON.inc:626
        ctx:state().nMonster_Level = 33 -- PICKMON.inc:627
        do return ctx:exit("") end -- PICKMON.inc:628
    end -- PICKMON.inc:629
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:632
        ctx:set("sMonster_Temp", "Annelid") -- PICKMON.inc:633
        ctx:state().nMonster_Level = 33 -- PICKMON.inc:634
        do return ctx:exit("") end -- PICKMON.inc:635
    end -- PICKMON.inc:636
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:638
        ctx:set("sMonster_Temp", "GuardCaptain") -- PICKMON.inc:639
        ctx:state().nMonster_Level = 33 -- PICKMON.inc:640
        do return ctx:exit("") end -- PICKMON.inc:641
    end -- PICKMON.inc:642
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:645
        ctx:set("sMonster_Temp", "GuardCaptain") -- PICKMON.inc:646
        ctx:state().nMonster_Level = 33 -- PICKMON.inc:647
        do return ctx:exit("") end -- PICKMON.inc:648
    end -- PICKMON.inc:649
    if ctx:condition("nMonTemp==6") then -- PICKMON.inc:651
        ctx:set("sMonster_Temp", "Magreeb2") -- PICKMON.inc:652
        ctx:state().nMonster_Level = 33 -- PICKMON.inc:653
        do return ctx:exit("") end -- PICKMON.inc:654
    end -- PICKMON.inc:655
    do return ctx:exit("") end -- PICKMON.inc:656
end

script.labels["Group13"] = function(ctx)
    -- PICKMON.inc:659
    -- levels 34-37
    ctx:randomInt(1, 5, "nMonTemp") -- PICKMON.inc:663
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:665
        ctx:set("sMonster_Temp", "ClanSoldier") -- PICKMON.inc:666
        ctx:state().nMonster_Level = 34 -- PICKMON.inc:667
        do return ctx:exit("") end -- PICKMON.inc:668
    end -- PICKMON.inc:669
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:671
        ctx:set("sMonster_Temp", "Fright") -- PICKMON.inc:672
        ctx:state().nMonster_Level = 35 -- PICKMON.inc:673
        do return ctx:exit("") end -- PICKMON.inc:674
    end -- PICKMON.inc:675
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:677
        ctx:set("sMonster_Temp", "HalfOrcCaptain") -- PICKMON.inc:678
        ctx:state().nMonster_Level = 35 -- PICKMON.inc:679
        do return ctx:exit("") end -- PICKMON.inc:680
    end -- PICKMON.inc:681
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:683
        ctx:set("sMonster_Temp", "HalfOrcCaptain") -- PICKMON.inc:684
        ctx:state().nMonster_Level = 35 -- PICKMON.inc:685
        do return ctx:exit("") end -- PICKMON.inc:686
    end -- PICKMON.inc:687
    if ctx:condition("nMonTemp==5") then -- PICKMON.inc:689
        ctx:set("sMonster_Temp", "KinTrellborg") -- PICKMON.inc:690
        ctx:state().nMonster_Level = 35 -- PICKMON.inc:691
        do return ctx:exit("") end -- PICKMON.inc:692
    end -- PICKMON.inc:693
    do return ctx:exit("") end -- PICKMON.inc:694
end

script.labels["Group14"] = function(ctx)
    -- PICKMON.inc:697
    -- levels 38-39
    ctx:randomInt(1, 4, "nMonTemp") -- PICKMON.inc:701
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:703
        ctx:set("sMonster_Temp", "Revenant") -- PICKMON.inc:704
        ctx:state().nMonster_Level = 38 -- PICKMON.inc:705
        do return ctx:exit("") end -- PICKMON.inc:706
    end -- PICKMON.inc:707
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:709
        ctx:set("sMonster_Temp", "Yeti") -- PICKMON.inc:710
        ctx:state().nMonster_Level = 38 -- PICKMON.inc:711
        do return ctx:exit("") end -- PICKMON.inc:712
    end -- PICKMON.inc:713
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:716
        ctx:set("sMonster_Temp", "Dagrell") -- PICKMON.inc:717
        ctx:state().nMonster_Level = 39 -- PICKMON.inc:718
        do return ctx:exit("") end -- PICKMON.inc:719
    end -- PICKMON.inc:720
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:722
        ctx:set("sMonster_Temp", "WingedMutant") -- PICKMON.inc:723
        ctx:state().nMonster_Level = 39 -- PICKMON.inc:724
        do return ctx:exit("") end -- PICKMON.inc:725
    end -- PICKMON.inc:726
    do return ctx:exit("") end -- PICKMON.inc:727
end

script.labels["Group15"] = function(ctx)
    -- PICKMON.inc:730
    -- levels 40 - 43
    ctx:randomInt(1, 4, "nMonTemp") -- PICKMON.inc:734
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:736
        ctx:set("sMonster_Temp", "LizardOrc") -- PICKMON.inc:737
        ctx:state().nMonster_Level = 40 -- PICKMON.inc:738
        do return ctx:exit("") end -- PICKMON.inc:739
    end -- PICKMON.inc:740
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:743
        ctx:set("sMonster_Temp", "BlackWolf") -- PICKMON.inc:744
        ctx:state().nMonster_Level = 40 -- PICKMON.inc:745
        do return ctx:exit("") end -- PICKMON.inc:746
    end -- PICKMON.inc:747
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:749
        ctx:set("sMonster_Temp", "PetrifiedMummy") -- PICKMON.inc:750
        ctx:state().nMonster_Level = 40 -- PICKMON.inc:751
        do return ctx:exit("") end -- PICKMON.inc:752
    end -- PICKMON.inc:753
    if ctx:condition("nMonTemp==4") then -- PICKMON.inc:755
        ctx:set("sMonster_Temp", "LizardOrc") -- PICKMON.inc:756
        ctx:state().nMonster_Level = 40 -- PICKMON.inc:757
        do return ctx:exit("") end -- PICKMON.inc:758
    end -- PICKMON.inc:759
    do return ctx:exit("") end -- PICKMON.inc:760
end

script.labels["Group16"] = function(ctx)
    -- PICKMON.inc:763
    -- levels 44-47
    ctx:randomInt(1, 2, "nMonTemp") -- PICKMON.inc:767
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:769
        ctx:set("sMonster_Temp", "ClanCorporal") -- PICKMON.inc:770
        ctx:state().nMonster_Level = 44 -- PICKMON.inc:771
        do return ctx:exit("") end -- PICKMON.inc:772
    end -- PICKMON.inc:773
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:775
        ctx:set("sMonster_Temp", "Lich") -- PICKMON.inc:776
        ctx:state().nMonster_Level = 45 -- PICKMON.inc:777
        do return ctx:exit("") end -- PICKMON.inc:778
    end -- PICKMON.inc:779
    do return ctx:exit("") end -- PICKMON.inc:780
end

script.labels["Group17"] = function(ctx)
    -- PICKMON.inc:783
    -- levels 48-53
    ctx:randomInt(1, 3, "nMonTemp") -- PICKMON.inc:787
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:789
        ctx:set("sMonster_Temp", "Vampir") -- PICKMON.inc:790
        ctx:state().nMonster_Level = 48 -- PICKMON.inc:791
        do return ctx:exit("") end -- PICKMON.inc:792
    end -- PICKMON.inc:793
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:796
        ctx:set("sMonster_Temp", "AncientTrellborg") -- PICKMON.inc:797
        ctx:state().nMonster_Level = 50 -- PICKMON.inc:798
        do return ctx:exit("") end -- PICKMON.inc:799
    end -- PICKMON.inc:800
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:802
        ctx:set("sMonster_Temp", "WingedAberration") -- PICKMON.inc:803
        ctx:state().nMonster_Level = 51 -- PICKMON.inc:804
        do return ctx:exit("") end -- PICKMON.inc:805
    end -- PICKMON.inc:806
    do return ctx:exit("") end -- PICKMON.inc:807
end

script.labels["Group18"] = function(ctx)
    -- PICKMON.inc:811
    -- levels 54 - 58
    ctx:randomInt(1, 3, "nMonTemp") -- PICKMON.inc:815
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:817
        ctx:set("sMonster_Temp", "ClanSergeant") -- PICKMON.inc:818
        ctx:state().nMonster_Level = 54 -- PICKMON.inc:819
        do return ctx:exit("") end -- PICKMON.inc:820
    end -- PICKMON.inc:821
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:823
        ctx:set("sMonster_Temp", "Dread") -- PICKMON.inc:824
        ctx:state().nMonster_Level = 55 -- PICKMON.inc:825
        do return ctx:exit("") end -- PICKMON.inc:826
    end -- PICKMON.inc:827
    if ctx:condition("nMonTemp==3") then -- PICKMON.inc:829
        ctx:set("sMonster_Temp", "PowerLich") -- PICKMON.inc:830
        ctx:state().nMonster_Level = 55 -- PICKMON.inc:831
        do return ctx:exit("") end -- PICKMON.inc:832
    end -- PICKMON.inc:833
    do return ctx:exit("") end -- PICKMON.inc:834
end

script.labels["Group19"] = function(ctx)
    -- PICKMON.inc:837
    -- levels 59 - 64
    ctx:randomInt(1, 2, "nMonTemp") -- PICKMON.inc:841
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:843
        ctx:set("sMonster_Temp", "VenomousDagrell") -- PICKMON.inc:844
        ctx:state().nMonster_Level = 59 -- PICKMON.inc:845
        do return ctx:exit("") end -- PICKMON.inc:846
    end -- PICKMON.inc:847
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:850
        ctx:set("sMonster_Temp", "LizardOrcWarrior") -- PICKMON.inc:851
        ctx:state().nMonster_Level = 60 -- PICKMON.inc:852
        do return ctx:exit("") end -- PICKMON.inc:853
    end -- PICKMON.inc:854
    do return ctx:exit("") end -- PICKMON.inc:855
end

script.labels["Group20"] = function(ctx)
    -- PICKMON.inc:858
    -- levels 65-74
    ctx:randomInt(1, 2, "nMonTemp") -- PICKMON.inc:862
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:864
        ctx:set("sMonster_Temp", "Terror") -- PICKMON.inc:865
        ctx:state().nMonster_Level = 65 -- PICKMON.inc:866
        do return ctx:exit("") end -- PICKMON.inc:867
    end -- PICKMON.inc:868
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:870
        ctx:set("sMonster_Temp", "LichKing") -- PICKMON.inc:871
        ctx:state().nMonster_Level = 65 -- PICKMON.inc:872
        do return ctx:exit("") end -- PICKMON.inc:873
    end -- PICKMON.inc:874
    do return ctx:exit("") end -- PICKMON.inc:875
end

script.labels["Group21"] = function(ctx)
    -- PICKMON.inc:878
    -- levels 75 - 89
    ctx:randomInt(1, 2, "nMonTemp") -- PICKMON.inc:882
    if ctx:condition("nMonTemp==1") then -- PICKMON.inc:884
        ctx:set("sMonster_Temp", "SpectreDagrell") -- PICKMON.inc:885
        ctx:state().nMonster_Level = 79 -- PICKMON.inc:886
        do return ctx:exit("") end -- PICKMON.inc:887
    end -- PICKMON.inc:888
    if ctx:condition("nMonTemp==2") then -- PICKMON.inc:891
        ctx:set("sMonster_Temp", "LizardOrcMage") -- PICKMON.inc:892
        ctx:state().nMonster_Level = 80 -- PICKMON.inc:893
        do return ctx:exit("") end -- PICKMON.inc:894
    end -- PICKMON.inc:895
    do return ctx:exit("") end -- PICKMON.inc:897
end

return script
