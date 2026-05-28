-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARENA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "Pickmon.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "nogold.inc" }

-- Arena.scr
-- By Timmy
-- gives the player the key for killing 5 monsters in arena
-- 11/29/01
script.labels["OnRude"] = function(ctx)
    -- ARENA.scr:49
    ctx:command("ndeadcounter", "= 0") -- ARENA.scr:52
    ctx:hasKey(231, "g_hobject") -- ARENA.scr:54
    if ctx:condition("g_hobject==FALSE") then -- ARENA.scr:55
        if ctx:hasKey(230) then -- ARENA.scr:56-57
            mm9.gosub(script, ctx, "Reset") -- ARENA.scr:58
            do return ctx:exit("") end -- ARENA.scr:59
        end -- ARENA.scr:60
    end -- ARENA.scr:61
    if ctx:hasKey(1018) then -- ARENA.scr:63-64
        mm9.gosub(script, ctx, "GiveWin") -- ARENA.scr:65
        do return ctx:exit("") end -- ARENA.scr:66
    end -- ARENA.scr:67
    if ctx:hasKey(1009) then -- ARENA.scr:69-70
        do return ctx:exit("") end -- ARENA.scr:71
    end -- ARENA.scr:72
    if ctx:hasKey(1011) then -- ARENA.scr:75-76
        if ctx:hasKey(1020) then -- ARENA.scr:77-78
            mm9.gosub(script, ctx, "FightWin") -- ARENA.scr:79
            do return ctx:exit("") end -- ARENA.scr:80
        end -- ARENA.scr:81
        do return ctx:exit("") end -- ARENA.scr:82
    end -- ARENA.scr:83
    if ctx:hasKey(1010) then -- ARENA.scr:85-86
        mm9.gosub(script, ctx, "OnWatch") -- ARENA.scr:87
        do return ctx:exit("") end -- ARENA.scr:88
    end -- ARENA.scr:89
    if ctx:hasKey(1017) then -- ARENA.scr:91-92
        mm9.gosub(script, ctx, "OnBet") -- ARENA.scr:93
        do return ctx:exit("") end -- ARENA.scr:94
    end -- ARENA.scr:95
    mm9.gosub(script, ctx, "fightcheck") -- ARENA.scr:99
    do return ctx:exit("") end -- ARENA.scr:100
end

script.labels["FightCheck"] = function(ctx)
    -- ARENA.scr:103
    if ctx:hasKey(1004) then -- ARENA.scr:107-108
        ctx:command("getobjecthandle", "ArenaFight g_hobject") -- ARENA.scr:109
        ctx:trigger("g_hobject", "Page") -- ARENA.scr:110
        mm9.gosub(script, ctx, "UnLockDoors") -- ARENA.scr:111
        do return ctx:exit("") end -- ARENA.scr:112
    end -- ARENA.scr:113
    if ctx:hasKey(1005) then -- ARENA.scr:115-116
        ctx:command("getobjecthandle", "ArenaFight g_hobject") -- ARENA.scr:117
        ctx:trigger("g_hobject", "Squire") -- ARENA.scr:118
        mm9.gosub(script, ctx, "UnLockDoors") -- ARENA.scr:119
        do return ctx:exit("") end -- ARENA.scr:120
    end -- ARENA.scr:121
    if ctx:hasKey(1006) then -- ARENA.scr:123-124
        ctx:command("getobjecthandle", "ArenaFight g_hobject") -- ARENA.scr:125
        ctx:trigger("g_hobject", "Knight") -- ARENA.scr:126
        mm9.gosub(script, ctx, "UnLockDoors") -- ARENA.scr:127
        do return ctx:exit("") end -- ARENA.scr:128
    end -- ARENA.scr:129
    if ctx:hasKey(1007) then -- ARENA.scr:132-133
        ctx:command("getobjecthandle", "ArenaFight g_hobject") -- ARENA.scr:134
        ctx:trigger("g_hobject", "Lord") -- ARENA.scr:135
        mm9.gosub(script, ctx, "UnLockDoors") -- ARENA.scr:136
        do return ctx:exit("") end -- ARENA.scr:137
    end -- ARENA.scr:138
    do return ctx:exit("") end -- ARENA.scr:140
end

script.labels["OnWatch"] = function(ctx)
    -- ARENA.scr:145
    ctx:command("set", "SCRIPT \" ScriptName ArenaCreature.scr\"") -- ARENA.scr:148
    ctx:command("removeobject", "hMonsterA") -- ARENA.scr:150
    ctx:command("smonstera", "= sMonsterA + Script") -- ARENA.scr:151
    ctx:command("getobjecthandle", "marker0 g_hobject") -- ARENA.scr:152
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- ARENA.scr:153
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- ARENA.scr:154
    -- ScriptParams WinMonsterB"
    ctx:command("set", "SCRIPT \" ScriptName ArenaCreature.scr") -- ARENA.scr:156
    ctx:command("removeobject", "hMonsterB") -- ARENA.scr:158
    ctx:command("smonsterb", "= sMonsterB + Script") -- ARENA.scr:159
    ctx:command("getobjecthandle", "marker1 g_hobject") -- ARENA.scr:160
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- ARENA.scr:161
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- ARENA.scr:162
    -- getobjecthandle RotatingDoor3 g_hobject
    -- trigger g_hobject use
    -- getobjecthandle RotatingDoor4 g_hobject
    -- trigger g_hobject use
    mm9.gosub(script, ctx, "LockDoors") -- ARENA.scr:170
    ctx:command("playsound", "sounds\\Events\\Cheer.wav, DoNothing, 100, 2400, FALSE, 100") -- ARENA.scr:172
    do return ctx:exit("") end -- ARENA.scr:174
end

script.labels["pick"] = function(ctx)
    -- ARENA.scr:178
    ctx:command("getrandomint", "nMinLevel, nMaxLevel mon1") -- ARENA.scr:184
    ctx:command("g_ntemp", "= mon1") -- ARENA.scr:185
    mm9.gosub(script, ctx, "PickMonster") -- ARENA.scr:186
    ctx:command("smonstera", "= sMonster_Temp") -- ARENA.scr:187
    ctx:command("nmonstera_level", "= nMonster_Level") -- ARENA.scr:188
    ctx:command("nmin2", "= mon1 - 4") -- ARENA.scr:190
    if ctx:condition("nMin2 < nMinLevel") then -- ARENA.scr:192
        ctx:command("nmin2", "= nMinLevel") -- ARENA.scr:193
    end -- ARENA.scr:194
    ctx:command("nmax2", "= nMin2 + 8") -- ARENA.scr:196
    if ctx:condition("nMax2 > nMaxLevel") then -- ARENA.scr:198
        ctx:command("nmax2", "= nMaxLevel") -- ARENA.scr:199
        ctx:command("nmin2", "= nMax2 - 8") -- ARENA.scr:200
    end -- ARENA.scr:201
    ctx:command("getrandomint", "nMin2, nMax2, mon2") -- ARENA.scr:203
    -- don't want same monster
    if ctx:condition("mon2==mon1") then -- ARENA.scr:207
        ctx:command("mon2", "= mon1 - 1") -- ARENA.scr:208
        if ctx:condition("mon2<nMinLevel") then -- ARENA.scr:209
            ctx:command("mon2", "= mon1 + 1") -- ARENA.scr:210
        end -- ARENA.scr:211
    end -- ARENA.scr:212
    ctx:command("g_ntemp", "= mon2") -- ARENA.scr:213
    mm9.gosub(script, ctx, "PickMonster") -- ARENA.scr:214
    ctx:command("smonsterb", "= sMonster_Temp") -- ARENA.scr:215
    ctx:command("nmonsterb_level", "= nMonster_Level") -- ARENA.scr:216
    -- cprint sMonsterA
    -- cprint vs
    -- cprint sMonsterB
    do return ctx:exit("") end -- ARENA.scr:220
end

script.labels["Init"] = function(ctx)
    -- ARENA.scr:223
    if ctx:condition("g_nCounter==3") then -- ARENA.scr:227
        ctx:giveKey(1009) -- ARENA.scr:228
        do return ctx:exit("") end -- ARENA.scr:229
    end -- ARENA.scr:230
    ctx:command("add", "g_nCounter, 1") -- ARENA.scr:231
    mm9.gosub(script, ctx, "pick") -- ARENA.scr:233
    -- Scale .30;ScriptParams MonsterA"
    ctx:command("set", "Script \" ScriptName ArenaMini.scr") -- ARENA.scr:235
    ctx:command("sminimonstera", "= sMonsterA + Script") -- ARENA.scr:237
    ctx:command("getobjecthandle", "marker3 g_hobject") -- ARENA.scr:238
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- ARENA.scr:239
    ctx:command("spawn2", "hMonsterA Xpos YPos ZPos 1 0 0 sMiniMonsterA") -- ARENA.scr:240
    -- Scale .30;ScriptParams MonsterB"
    ctx:command("set", "Script \" ScriptName ArenaMini.scr") -- ARENA.scr:243
    ctx:command("sminimonsterb", "= sMonsterB + Script") -- ARENA.scr:245
    ctx:command("getobjecthandle", "marker4 g_hobject") -- ARENA.scr:246
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- ARENA.scr:247
    ctx:command("spawn2", "hMonsterB Xpos YPos ZPos 1 0 0 sMiniMonsterB") -- ARENA.scr:248
    do return ctx:exit("") end -- ARENA.scr:250
end

script.labels["OnArrive"] = function(ctx)
    -- ARENA.scr:256
    ctx:getParam(0, "g_hobject") -- ARENA.scr:259
    if ctx:condition("g_hObject==hMonsterA") then -- ARENA.scr:261
        ctx:command("bmonathere", "= TRUE") -- ARENA.scr:262
        if ctx:condition("bMonBThere==FALSE") then -- ARENA.scr:264
            do return ctx:exit("") end -- ARENA.scr:265
        end -- ARENA.scr:266
    end -- ARENA.scr:268
    if ctx:condition("g_hObject==hMonsterB") then -- ARENA.scr:270
        ctx:command("bmonbthere", "= TRUE") -- ARENA.scr:271
        if ctx:condition("bMonAThere==FALSE") then -- ARENA.scr:272
            do return ctx:exit("") end -- ARENA.scr:273
        end -- ARENA.scr:274
    end -- ARENA.scr:275
    ctx:trigger("hMonsterA", "HateAll") -- ARENA.scr:277
    ctx:trigger("hMonsterB", "HateAll") -- ARENA.scr:278
    do return ctx:exit("") end -- ARENA.scr:280
end

script.labels["Onuse"] = function(ctx)
    -- ARENA.scr:286
    do return ctx:exit("") end -- ARENA.scr:288
    if not ctx:hasKey(217) then -- ARENA.scr:289-290
        if ctx:hasKey(214) then -- ARENA.scr:291-292
            ctx:giveKey(217) -- ARENA.scr:293
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- ARENA.scr:294
            do return ctx:exit("") end -- ARENA.scr:295
        end -- ARENA.scr:296
    end -- ARENA.scr:297
    do return ctx:exit("") end -- ARENA.scr:298
end

script.labels["OnMonsterA"] = function(ctx)
    -- ARENA.scr:304
    ctx:command("set", "sBetOn MonsterA") -- ARENA.scr:307
    ctx:command("g_ntemp", "= nMonsterB_Level - nMonsterA_Level") -- ARENA.scr:308
    if ctx:condition("g_ntemp<0") then -- ARENA.scr:309
        ctx:command("nbetamount", "= nBetAmount * 1.5") -- ARENA.scr:310
        do return ctx:exit("") end -- ARENA.scr:311
    end -- ARENA.scr:312
    if ctx:condition("g_ntemp>5") then -- ARENA.scr:314
        ctx:command("nbetamount", "= nBetAmount * 2") -- ARENA.scr:315
        do return ctx:exit("") end -- ARENA.scr:316
    end -- ARENA.scr:317
    if ctx:condition("g_ntemp>10") then -- ARENA.scr:319
        ctx:command("nbetamount", "= nBetAmount * 3") -- ARENA.scr:320
        do return ctx:exit("") end -- ARENA.scr:321
    end -- ARENA.scr:322
    if ctx:condition("g_ntemp>15") then -- ARENA.scr:324
        ctx:command("nbetamount", "= nBetAmount * 4") -- ARENA.scr:325
        do return ctx:exit("") end -- ARENA.scr:326
    end -- ARENA.scr:327
    do return ctx:exit("") end -- ARENA.scr:328
end

script.labels["OnMonsterB"] = function(ctx)
    -- ARENA.scr:332
    ctx:command("set", "sBetOn MonsterB") -- ARENA.scr:335
    ctx:command("g_ntemp", "= nMonsterA_Level - nMonsterB_Level") -- ARENA.scr:336
    if ctx:condition("g_ntemp<0") then -- ARENA.scr:337
        ctx:command("nbetamount", "= nBetAmount * 1.5") -- ARENA.scr:338
        do return ctx:exit("") end -- ARENA.scr:339
    end -- ARENA.scr:340
    if ctx:condition("g_ntemp>5") then -- ARENA.scr:342
        ctx:command("nbetamount", "= nBetAmount * 2") -- ARENA.scr:343
        do return ctx:exit("") end -- ARENA.scr:344
    end -- ARENA.scr:345
    if ctx:condition("g_ntemp>10") then -- ARENA.scr:347
        ctx:command("nbetamount", "= nBetAmount * 3") -- ARENA.scr:348
        do return ctx:exit("") end -- ARENA.scr:349
    end -- ARENA.scr:350
    if ctx:condition("g_ntemp>15") then -- ARENA.scr:352
        ctx:command("nbetamount", "= nBetAmount * 4") -- ARENA.scr:353
        do return ctx:exit("") end -- ARENA.scr:354
    end -- ARENA.scr:355
    do return ctx:exit("") end -- ARENA.scr:356
end

script.labels["OnMonsterAWin"] = function(ctx)
    -- ARENA.scr:359
    if ctx:condition("sBetOn==MonsterA") then -- ARENA.scr:362
        ctx:giveKey(1018) -- ARENA.scr:363
        ctx:command("rollovertext", "6, 0") -- ARENA.scr:364
    else -- ARENA.scr:365
        ctx:command("rollovertext", "7, 0") -- ARENA.scr:366
        do return ctx:exit("") end -- ARENA.scr:367
    end -- ARENA.scr:368
    do return ctx:exit("") end -- ARENA.scr:369
end

script.labels["OnMonsterBWin"] = function(ctx)
    -- ARENA.scr:372
    if ctx:condition("sBetOn==MonsterB") then -- ARENA.scr:375
        ctx:giveKey(1018) -- ARENA.scr:376
        ctx:command("rollovertext", "6, 0") -- ARENA.scr:377
    else -- ARENA.scr:378
        ctx:command("rollovertext", "7, 0") -- ARENA.scr:379
        do return ctx:exit("") end -- ARENA.scr:380
    end -- ARENA.scr:381
    do return ctx:exit("") end -- ARENA.scr:382
end

script.labels["FightWin"] = function(ctx)
    -- ARENA.scr:385
    if ctx:condition("nLord==TRUE") then -- ARENA.scr:387
        ctx:giveKey(217) -- ARENA.scr:388
        do return ctx:exit("") end -- ARENA.scr:389
    end -- ARENA.scr:390
    ctx:giveKey(1009) -- ARENA.scr:391
    ctx:takeKey(1020) -- ARENA.scr:392
    ctx:getConsoleNumVar("nWinAmount", "nBetAmount") -- ARENA.scr:393
    ctx:giveGold("nBetAmount") -- ARENA.scr:394
    do return ctx:exit("") end -- ARENA.scr:395
end

script.labels["Givewin"] = function(ctx)
    -- ARENA.scr:398
    ctx:takeKey(1018) -- ARENA.scr:401
    ctx:takeKey(1019) -- ARENA.scr:402
    mm9.gosub(script, ctx, "Reset") -- ARENA.scr:403
    ctx:giveGold("nBetAmount") -- ARENA.scr:404
    ctx:command("debugout", "nBetAmount") -- ARENA.scr:405
    do return ctx:exit("") end -- ARENA.scr:406
end

script.labels["LockDoors"] = function(ctx)
    -- ARENA.scr:409
    ctx:command("getobjecthandle", "RotatingDoor0 g_hobject") -- ARENA.scr:411
    ctx:trigger("g_hobject", "close") -- ARENA.scr:412
    ctx:trigger("g_hobject", "lock") -- ARENA.scr:413
    ctx:command("getobjecthandle", "RotatingDoor1 g_hobject") -- ARENA.scr:415
    ctx:trigger("g_hobject", "close") -- ARENA.scr:416
    ctx:trigger("g_hobject", "lock") -- ARENA.scr:417
    do return ctx:exit("") end -- ARENA.scr:419
end

script.labels["UnLockDoors"] = function(ctx)
    -- ARENA.scr:422
    ctx:command("getobjecthandle", "RotatingDoor0 g_hobject") -- ARENA.scr:424
    ctx:trigger("g_hobject", "unlock") -- ARENA.scr:425
    ctx:command("getobjecthandle", "RotatingDoor1 g_hobject") -- ARENA.scr:427
    ctx:trigger("g_hobject", "unlock") -- ARENA.scr:428
    do return ctx:exit("") end -- ARENA.scr:429
end

script.labels["OnBet"] = function(ctx)
    -- ARENA.scr:431
    -- traceON
    mm9.gosub(script, ctx, "OnBet2") -- ARENA.scr:433
end

-- traceOFF
script.labels["OnBet2"] = function(ctx)
    -- ARENA.scr:437
    mm9.gosub(script, ctx, "LockDoors") -- ARENA.scr:440
    if ctx:hasKey(1012) then -- ARENA.scr:442-443
        ctx:command("hasgold", "50 g_ntemp") -- ARENA.scr:444
        if ctx:condition("g_ntemp==FALSE") then -- ARENA.scr:445
            mm9.gosub(script, ctx, "NoGold") -- ARENA.scr:446
            mm9.gosub(script, ctx, "Reset") -- ARENA.scr:447
            do return ctx:exit("") end -- ARENA.scr:448
        else -- ARENA.scr:449
            ctx:takeKey(1012) -- ARENA.scr:450
            ctx:command("takegold", "50") -- ARENA.scr:451
            ctx:command("set", "nBetAmount 50") -- ARENA.scr:452
        end -- ARENA.scr:453
        do return ctx:exit("") end -- ARENA.scr:454
    end -- ARENA.scr:455
    if ctx:hasKey(1013) then -- ARENA.scr:457-458
        ctx:command("hasgold", "100 g_ntemp") -- ARENA.scr:459
        if ctx:condition("g_ntemp==FALSE") then -- ARENA.scr:460
            mm9.gosub(script, ctx, "NoGold") -- ARENA.scr:461
            mm9.gosub(script, ctx, "Reset") -- ARENA.scr:462
            do return ctx:exit("") end -- ARENA.scr:463
        else -- ARENA.scr:464
            ctx:takeKey(1013) -- ARENA.scr:465
            ctx:command("takegold", "100") -- ARENA.scr:466
            ctx:command("set", "nBetAmount 100") -- ARENA.scr:467
        end -- ARENA.scr:468
        do return ctx:exit("") end -- ARENA.scr:469
    end -- ARENA.scr:470
    if ctx:hasKey(1014) then -- ARENA.scr:472-473
        ctx:command("hasgold", "250 g_ntemp") -- ARENA.scr:474
        if ctx:condition("g_ntemp==FALSE") then -- ARENA.scr:475
            mm9.gosub(script, ctx, "NoGold") -- ARENA.scr:476
            mm9.gosub(script, ctx, "Reset") -- ARENA.scr:477
            do return ctx:exit("") end -- ARENA.scr:478
        else -- ARENA.scr:479
            ctx:takeKey(1014) -- ARENA.scr:480
            ctx:command("takegold", "250") -- ARENA.scr:481
            ctx:command("set", "nBetAmount 250") -- ARENA.scr:482
        end -- ARENA.scr:483
        do return ctx:exit("") end -- ARENA.scr:484
    end -- ARENA.scr:485
    if ctx:hasKey(1015) then -- ARENA.scr:487-488
        ctx:command("hasgold", "500 g_ntemp") -- ARENA.scr:489
        if ctx:condition("g_ntemp==FALSE") then -- ARENA.scr:490
            mm9.gosub(script, ctx, "NoGold") -- ARENA.scr:491
            mm9.gosub(script, ctx, "Reset") -- ARENA.scr:492
            do return ctx:exit("") end -- ARENA.scr:493
        else -- ARENA.scr:494
            ctx:takeKey(1015) -- ARENA.scr:495
            ctx:command("takegold", "500") -- ARENA.scr:496
            ctx:command("set", "nBetAmount 500") -- ARENA.scr:497
        end -- ARENA.scr:498
        do return ctx:exit("") end -- ARENA.scr:499
    end -- ARENA.scr:500
    if ctx:hasKey(1016) then -- ARENA.scr:502-503
        ctx:command("hasgold", "1000 g_ntemp") -- ARENA.scr:504
        if ctx:condition("g_ntemp==FALSE") then -- ARENA.scr:505
            mm9.gosub(script, ctx, "NoGold") -- ARENA.scr:506
            mm9.gosub(script, ctx, "Reset") -- ARENA.scr:507
            do return ctx:exit("") end -- ARENA.scr:508
        else -- ARENA.scr:509
            ctx:takeKey(1016) -- ARENA.scr:510
            ctx:command("takegold", "1000") -- ARENA.scr:511
            ctx:command("set", "nBetAmount 1000") -- ARENA.scr:512
        end -- ARENA.scr:513
        do return ctx:exit("") end -- ARENA.scr:514
    end -- ARENA.scr:515
    do return ctx:exit("") end -- ARENA.scr:516
end

script.labels["OnLord"] = function(ctx)
    -- ARENA.scr:519
    if ctx:hasKey(214) then -- ARENA.scr:522-523
        ctx:command("set", "nLord TRUE") -- ARENA.scr:524
        do return ctx:exit("") end -- ARENA.scr:525
    end -- ARENA.scr:526
    do return ctx:exit("") end -- ARENA.scr:527
end

script.labels["Reset"] = function(ctx)
    -- ARENA.scr:530
    ctx:takeKey(1004) -- ARENA.scr:533
    ctx:takeKey(1005) -- ARENA.scr:534
    ctx:takeKey(1006) -- ARENA.scr:535
    ctx:takeKey(1007) -- ARENA.scr:536
    ctx:takeKey(1008) -- ARENA.scr:537
    ctx:takeKey(1010) -- ARENA.scr:538
    ctx:takeKey(1011) -- ARENA.scr:539
    ctx:takeKey(1012) -- ARENA.scr:540
    ctx:takeKey(1013) -- ARENA.scr:541
    ctx:takeKey(1014) -- ARENA.scr:542
    ctx:takeKey(1015) -- ARENA.scr:543
    ctx:takeKey(1016) -- ARENA.scr:544
    ctx:takeKey(1017) -- ARENA.scr:545
    ctx:takeKey(1018) -- ARENA.scr:546
    ctx:takeKey(1019) -- ARENA.scr:547
    do return ctx:exit("") end -- ARENA.scr:549
end

script.labels["BeVictorious"] = function(ctx)
    -- ARENA.scr:553
    ctx:takeKey(1010) -- ARENA.scr:556
    ctx:trigger("hWinner", "RunScript ArenaVictory.scr") -- ARENA.scr:557
    do return ctx:exit("") end -- ARENA.scr:559
end

script.labels["OnMonsterDead"] = function(ctx)
    -- ARENA.scr:562
    -- Find out who this is, and trigger
    -- the opposite one..
    -- in case both of them die...
    ctx:command("ndeadcounter", "= nDeadCounter + 1") -- ARENA.scr:570
    if ctx:condition("nDeadCounter==2") then -- ARENA.scr:572
        mm9.gosub(script, ctx, "Reset") -- ARENA.scr:573
        mm9.gosub(script, ctx, "Init") -- ARENA.scr:574
        mm9.gosub(script, ctx, "UnLockDoors") -- ARENA.scr:575
        do return ctx:exit("") end -- ARENA.scr:576
    end -- ARENA.scr:577
    ctx:takeKey(1019) -- ARENA.scr:580
    ctx:hasKey(1017, "bHasKey") -- ARENA.scr:583
    ctx:getParam(0, "hMonster") -- ARENA.scr:585
    if ctx:condition("hMonster==hMonsterA") then -- ARENA.scr:586
        -- cprint MonsterB won!
        ctx:command("hwinner", "= hMonsterB") -- ARENA.scr:588
        if ctx:condition("bHasKey==1") then -- ARENA.scr:589
            mm9.gosub(script, ctx, "OnMonsterBWin") -- ARENA.scr:590
        end -- ARENA.scr:591
    else -- ARENA.scr:592
        -- cprint MonsterA won!
        ctx:command("hwinner", "= hMonsterA") -- ARENA.scr:594
        if ctx:condition("bHasKey==1") then -- ARENA.scr:595
            mm9.gosub(script, ctx, "OnMonsterAWin") -- ARENA.scr:596
        end -- ARENA.scr:597
    end -- ARENA.scr:598
    ctx:command("wait", "20,1,BeVictorious") -- ARENA.scr:600
    do return ctx:exit("") end -- ARENA.scr:602
end

script.labels["OnPostStartWorld"] = function(ctx)
    -- ARENA.scr:606
    mm9.gosub(script, ctx, "Init") -- ARENA.scr:608
    do return ctx:exit("") end -- ARENA.scr:610
end

script.labels["Main"] = function(ctx)
    -- ARENA.scr:613
    -- TraceOn ;DELETE ME!!
    ctx:takeKey(1009) -- ARENA.scr:618
    mm9.gosub(script, ctx, "reset") -- ARENA.scr:619
    -- AddTrigger Use, Onuse
    ctx:addTrigger("Arrive", "OnArrive") -- ARENA.scr:621
    ctx:addTrigger("Pick", "Init") -- ARENA.scr:622
    ctx:addTrigger("MonsterA", "OnMonsterA") -- ARENA.scr:623
    ctx:addTrigger("MonsterB", "OnMonsterB") -- ARENA.scr:624
    ctx:addTrigger("WinMonsterA", "OnMonsterAWin") -- ARENA.scr:625
    ctx:addTrigger("WinMonsterB", "OnMonsterBWin") -- ARENA.scr:626
    ctx:addTrigger("Fight", "OnWatch") -- ARENA.scr:627
    ctx:addTrigger("Lord", "OnLord") -- ARENA.scr:628
    ctx:addTrigger("IDied", "OnMonsterDead") -- ARENA.scr:629
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- ARENA.scr:630
    mm9.gosub(script, ctx, "voiceinit") -- ARENA.scr:631
    ctx:command("onpoststartworld", "OnPostStartWorld") -- ARENA.scr:633
    do return ctx:exit("") end -- ARENA.scr:636
end

return script
