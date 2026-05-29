-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARENAFIGHT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "Pickmon.inc" }

-- Arena.scr
-- By Timmy
-- gives the player the key for killing 5 monsters in arena
-- 11/29/01
script.labels["OnPage"] = function(ctx)
    -- ARENAFIGHT.scr:43
    ctx:setConsoleNumVar("WaitingForPlayer", "TRUE") -- ARENAFIGHT.scr:46
    ctx:set("nMinLevel", "nPlayerLevel * .8") -- ARENAFIGHT.scr:48
    ctx:set("nMaxLevel", "nPlayerLevel * 1.3") -- ARENAFIGHT.scr:49
    if ctx:condition("nPlayerLevel>89") then -- ARENAFIGHT.scr:50
        ctx:state().nMaxLevel = 89 -- ARENAFIGHT.scr:51
    end -- ARENAFIGHT.scr:52
    if ctx:condition("nPlayerlevel<4") then -- ARENAFIGHT.scr:54
        ctx:state().nMaxLevel = 4 -- ARENAFIGHT.scr:55
    end -- ARENAFIGHT.scr:56
    mm9.gosub(script, ctx, "Clearmon") -- ARENAFIGHT.scr:58
    ctx:randomInt(1, 2, "nNumberMonsters") -- ARENAFIGHT.scr:60
    ctx:set("nArenaReward", "nNumberMonsters * nPlayerLevel") -- ARENAFIGHT.scr:61
    ctx:set("nArenaReward", "nArenaReward * 20") -- ARENAFIGHT.scr:62
    ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:65
    mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:66
    if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:68
        do return mm9.gotoLabel(script, ctx, "OnPage") end -- ARENAFIGHT.scr:69
        do return ctx:exit("") end -- ARENAFIGHT.scr:70
    end -- ARENAFIGHT.scr:71
    if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:73
        do return mm9.gotoLabel(script, ctx, "OnPage") end -- ARENAFIGHT.scr:74
        do return ctx:exit("") end -- ARENAFIGHT.scr:75
    end -- ARENAFIGHT.scr:76
    ctx:set("sMonsterA", "sMonster_Temp + Script") -- ARENAFIGHT.scr:78
    ctx:state().g_hobject = ctx:objectOrNil("marker0") -- ARENAFIGHT.scr:79
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:80
    ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ARENAFIGHT.scr:81
    if ctx:condition("nMonsterNumber>1") then -- ARENAFIGHT.scr:84
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:85
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:86
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:88
            do return mm9.gotoLabel(script, ctx, "OnPage") end -- ARENAFIGHT.scr:89
            do return ctx:exit("") end -- ARENAFIGHT.scr:90
        end -- ARENAFIGHT.scr:91
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:93
            do return mm9.gotoLabel(script, ctx, "OnPage") end -- ARENAFIGHT.scr:94
            do return ctx:exit("") end -- ARENAFIGHT.scr:95
        end -- ARENAFIGHT.scr:96
        ctx:set("sMonsterB", "sMonster_Temp + Script") -- ARENAFIGHT.scr:98
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:99
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:100
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ARENAFIGHT.scr:101
    end -- ARENAFIGHT.scr:102
    ctx:object("RotatingDoor3"):trigger("use") -- ARENAFIGHT.scr:104-105
    ctx:object("RotatingDoor4"):trigger("use") -- ARENAFIGHT.scr:107-108
    do return ctx:exit("") end -- ARENAFIGHT.scr:110
end

script.labels["OnSquire"] = function(ctx)
    -- ARENAFIGHT.scr:113
    ctx:setConsoleNumVar("WaitingForPlayer", "TRUE") -- ARENAFIGHT.scr:116
    ctx:set("nMinLevel", "nPlayerLevel * .8") -- ARENAFIGHT.scr:118
    ctx:set("nMaxLevel", "nPlayerLevel * 1.5") -- ARENAFIGHT.scr:119
    if ctx:condition("nPlayerLevel>89") then -- ARENAFIGHT.scr:120
        ctx:state().nMaxLevel = 89 -- ARENAFIGHT.scr:121
    end -- ARENAFIGHT.scr:122
    if ctx:condition("nPlayerlevel<4") then -- ARENAFIGHT.scr:124
        ctx:state().nMaxLevel = 4 -- ARENAFIGHT.scr:125
    end -- ARENAFIGHT.scr:126
    mm9.gosub(script, ctx, "Clearmon") -- ARENAFIGHT.scr:128
    ctx:randomInt(1, 3, "nNumberMonsters") -- ARENAFIGHT.scr:130
    ctx:set("nArenaReward", "nNumberMonsters * nPlayerLevel") -- ARENAFIGHT.scr:131
    ctx:set("nArenaReward", "nArenaReward * 30") -- ARENAFIGHT.scr:132
    ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:135
    mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:136
    if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:138
        do return mm9.gotoLabel(script, ctx, "OnSquire") end -- ARENAFIGHT.scr:139
        do return ctx:exit("") end -- ARENAFIGHT.scr:140
    end -- ARENAFIGHT.scr:141
    if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:143
        do return mm9.gotoLabel(script, ctx, "OnSquire") end -- ARENAFIGHT.scr:144
        do return ctx:exit("") end -- ARENAFIGHT.scr:145
    end -- ARENAFIGHT.scr:146
    ctx:set("sMonsterA", "sMonster_Temp + Script") -- ARENAFIGHT.scr:148
    ctx:state().g_hobject = ctx:objectOrNil("marker0") -- ARENAFIGHT.scr:149
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:150
    ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ARENAFIGHT.scr:151
    if ctx:condition("nMonsterNumber>1") then -- ARENAFIGHT.scr:154
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:155
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:156
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:158
            do return mm9.gotoLabel(script, ctx, "OnSquire") end -- ARENAFIGHT.scr:159
            do return ctx:exit("") end -- ARENAFIGHT.scr:160
        end -- ARENAFIGHT.scr:161
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:163
            do return mm9.gotoLabel(script, ctx, "OnSquire") end -- ARENAFIGHT.scr:164
            do return ctx:exit("") end -- ARENAFIGHT.scr:165
        end -- ARENAFIGHT.scr:166
        ctx:set("sMonsterB", "sMonster_Temp + Script") -- ARENAFIGHT.scr:168
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:169
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:170
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ARENAFIGHT.scr:171
    end -- ARENAFIGHT.scr:172
    if ctx:condition("nMonsterNumber>2") then -- ARENAFIGHT.scr:174
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:175
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:176
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:178
            do return mm9.gotoLabel(script, ctx, "OnSquire") end -- ARENAFIGHT.scr:179
            do return ctx:exit("") end -- ARENAFIGHT.scr:180
        end -- ARENAFIGHT.scr:181
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:183
            do return mm9.gotoLabel(script, ctx, "OnSquire") end -- ARENAFIGHT.scr:184
            do return ctx:exit("") end -- ARENAFIGHT.scr:185
        end -- ARENAFIGHT.scr:186
        ctx:set("sMonsterB", "sMonster_Temp + Script") -- ARENAFIGHT.scr:188
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:189
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:190
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ARENAFIGHT.scr:191
    end -- ARENAFIGHT.scr:192
    ctx:object("RotatingDoor3"):trigger("use") -- ARENAFIGHT.scr:194-195
    ctx:object("RotatingDoor4"):trigger("use") -- ARENAFIGHT.scr:197-198
    do return ctx:exit("") end -- ARENAFIGHT.scr:200
end

script.labels["OnKnight"] = function(ctx)
    -- ARENAFIGHT.scr:203
    ctx:setConsoleNumVar("WaitingForPlayer", "TRUE") -- ARENAFIGHT.scr:206
    ctx:set("nMinLevel", "nPlayerLevel") -- ARENAFIGHT.scr:208
    ctx:set("nMaxLevel", "nPlayerLevel * 1.7") -- ARENAFIGHT.scr:209
    if ctx:condition("nPlayerLevel>89") then -- ARENAFIGHT.scr:210
        ctx:state().nMaxLevel = 89 -- ARENAFIGHT.scr:211
    end -- ARENAFIGHT.scr:212
    if ctx:condition("nPlayerlevel<4") then -- ARENAFIGHT.scr:214
        ctx:state().nMaxLevel = 4 -- ARENAFIGHT.scr:215
    end -- ARENAFIGHT.scr:216
    mm9.gosub(script, ctx, "Clearmon") -- ARENAFIGHT.scr:218
    ctx:randomInt(1, 4, "nNumberMonsters") -- ARENAFIGHT.scr:220
    ctx:set("nArenaReward", "nNumberMonsters * nPlayerLevel") -- ARENAFIGHT.scr:221
    ctx:set("nArenaReward", "nArenaReward * 50") -- ARENAFIGHT.scr:222
    ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:225
    mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:226
    if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:228
        do return mm9.gotoLabel(script, ctx, "OnKnight") end -- ARENAFIGHT.scr:229
        do return ctx:exit("") end -- ARENAFIGHT.scr:230
    end -- ARENAFIGHT.scr:231
    if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:233
        do return mm9.gotoLabel(script, ctx, "OnKnight") end -- ARENAFIGHT.scr:234
        do return ctx:exit("") end -- ARENAFIGHT.scr:235
    end -- ARENAFIGHT.scr:236
    ctx:set("sMonsterA", "sMonster_Temp + Script") -- ARENAFIGHT.scr:238
    ctx:state().g_hobject = ctx:objectOrNil("marker0") -- ARENAFIGHT.scr:239
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:240
    ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ARENAFIGHT.scr:241
    if ctx:condition("nMonsterNumber>1") then -- ARENAFIGHT.scr:244
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:245
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:246
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:248
            do return mm9.gotoLabel(script, ctx, "OnKnight") end -- ARENAFIGHT.scr:249
            do return ctx:exit("") end -- ARENAFIGHT.scr:250
        end -- ARENAFIGHT.scr:251
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:253
            do return mm9.gotoLabel(script, ctx, "OnKnight") end -- ARENAFIGHT.scr:254
            do return ctx:exit("") end -- ARENAFIGHT.scr:255
        end -- ARENAFIGHT.scr:256
        ctx:set("sMonsterB", "sMonster_Temp + Script") -- ARENAFIGHT.scr:258
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:259
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:260
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ARENAFIGHT.scr:261
    end -- ARENAFIGHT.scr:262
    if ctx:condition("nMonsterNumber>2") then -- ARENAFIGHT.scr:264
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:265
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:266
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:268
            do return mm9.gotoLabel(script, ctx, "OnKnight") end -- ARENAFIGHT.scr:269
            do return ctx:exit("") end -- ARENAFIGHT.scr:270
        end -- ARENAFIGHT.scr:271
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:273
            do return mm9.gotoLabel(script, ctx, "OnKnight") end -- ARENAFIGHT.scr:274
            do return ctx:exit("") end -- ARENAFIGHT.scr:275
        end -- ARENAFIGHT.scr:276
        ctx:set("sMonsterB", "sMonster_Temp + Script") -- ARENAFIGHT.scr:278
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:279
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:280
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ARENAFIGHT.scr:281
    end -- ARENAFIGHT.scr:282
    if ctx:condition("nMonsterNumber>3") then -- ARENAFIGHT.scr:284
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:285
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:286
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:288
            do return mm9.gotoLabel(script, ctx, "OnKnight") end -- ARENAFIGHT.scr:289
            do return ctx:exit("") end -- ARENAFIGHT.scr:290
        end -- ARENAFIGHT.scr:291
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:293
            do return mm9.gotoLabel(script, ctx, "OnKnight") end -- ARENAFIGHT.scr:294
            do return ctx:exit("") end -- ARENAFIGHT.scr:295
        end -- ARENAFIGHT.scr:296
        ctx:set("sMonsterA", "sMonster_Temp + Script") -- ARENAFIGHT.scr:298
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:299
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:300
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ARENAFIGHT.scr:301
    end -- ARENAFIGHT.scr:302
    ctx:object("RotatingDoor3"):trigger("use") -- ARENAFIGHT.scr:304-305
    ctx:object("RotatingDoor4"):trigger("use") -- ARENAFIGHT.scr:307-308
    do return ctx:exit("") end -- ARENAFIGHT.scr:310
end

script.labels["OnLord"] = function(ctx)
    -- ARENAFIGHT.scr:312
    ctx:setConsoleNumVar("WaitingForPlayer", "TRUE") -- ARENAFIGHT.scr:315
    ctx:object("ShopkeeperElfMaleB0"):trigger("Lord") -- ARENAFIGHT.scr:317-318
    ctx:set("nMinLevel", "nPlayerLevel") -- ARENAFIGHT.scr:320
    ctx:set("nMaxLevel", "nPlayerLevel * 2.5") -- ARENAFIGHT.scr:323
    if ctx:condition("nPlayerLevel>89") then -- ARENAFIGHT.scr:324
        ctx:state().nMaxLevel = 89 -- ARENAFIGHT.scr:325
    end -- ARENAFIGHT.scr:326
    if ctx:condition("nPlayerlevel<4") then -- ARENAFIGHT.scr:328
        ctx:state().nMaxLevel = 4 -- ARENAFIGHT.scr:329
    end -- ARENAFIGHT.scr:330
    mm9.gosub(script, ctx, "Clearmon") -- ARENAFIGHT.scr:332
    ctx:randomInt(1, 5, "nNumberMonsters") -- ARENAFIGHT.scr:334
    ctx:set("nArenaReward", "nNumberMonsters * nPlayerLevel") -- ARENAFIGHT.scr:335
    ctx:set("nArenaReward", "nArenaReward * 100") -- ARENAFIGHT.scr:336
    ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:339
    mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:340
    if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:343
        do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:344
        do return ctx:exit("") end -- ARENAFIGHT.scr:345
    end -- ARENAFIGHT.scr:346
    if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:348
        do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:349
        do return ctx:exit("") end -- ARENAFIGHT.scr:350
    end -- ARENAFIGHT.scr:351
    ctx:set("sMonsterA", "sMonster_Temp + Script") -- ARENAFIGHT.scr:353
    ctx:state().g_hobject = ctx:objectOrNil("marker0") -- ARENAFIGHT.scr:354
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:355
    ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ARENAFIGHT.scr:356
    if ctx:condition("nMonsterNumber>1") then -- ARENAFIGHT.scr:359
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:360
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:361
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:363
            do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:364
            do return ctx:exit("") end -- ARENAFIGHT.scr:365
        end -- ARENAFIGHT.scr:366
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:368
            do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:369
            do return ctx:exit("") end -- ARENAFIGHT.scr:370
        end -- ARENAFIGHT.scr:371
        ctx:set("sMonsterB", "sMonster_Temp + Script") -- ARENAFIGHT.scr:373
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:374
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:375
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ARENAFIGHT.scr:376
    end -- ARENAFIGHT.scr:377
    if ctx:condition("nMonsterNumber>2") then -- ARENAFIGHT.scr:379
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:380
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:381
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:383
            do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:384
            do return ctx:exit("") end -- ARENAFIGHT.scr:385
        end -- ARENAFIGHT.scr:386
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:388
            do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:389
            do return ctx:exit("") end -- ARENAFIGHT.scr:390
        end -- ARENAFIGHT.scr:391
        ctx:set("sMonsterB", "sMonster_Temp + Script") -- ARENAFIGHT.scr:393
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:394
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:395
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ARENAFIGHT.scr:396
    end -- ARENAFIGHT.scr:397
    if ctx:condition("nMonsterNumber>3") then -- ARENAFIGHT.scr:399
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:400
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:401
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:402
            do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:403
            do return ctx:exit("") end -- ARENAFIGHT.scr:404
        end -- ARENAFIGHT.scr:405
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:407
            do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:408
            do return ctx:exit("") end -- ARENAFIGHT.scr:409
        end -- ARENAFIGHT.scr:410
        ctx:set("sMonsterA", "sMonster_Temp + Script") -- ARENAFIGHT.scr:412
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:413
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:414
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ARENAFIGHT.scr:415
    end -- ARENAFIGHT.scr:416
    if ctx:condition("nMonsterNumber>4") then -- ARENAFIGHT.scr:419
        ctx:randomInt("nMinLevel", "nMaxLevel", "g_ntemp") -- ARENAFIGHT.scr:420
        mm9.gosub(script, ctx, "pickmonster") -- ARENAFIGHT.scr:421
        if ctx:condition("nMonster_Level<nMinLevel") then -- ARENAFIGHT.scr:423
            do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:424
            do return ctx:exit("") end -- ARENAFIGHT.scr:425
        end -- ARENAFIGHT.scr:426
        if ctx:condition("nMonster_Level>nMaxLevel") then -- ARENAFIGHT.scr:428
            do return mm9.gotoLabel(script, ctx, "OnLord") end -- ARENAFIGHT.scr:429
            do return ctx:exit("") end -- ARENAFIGHT.scr:430
        end -- ARENAFIGHT.scr:431
        ctx:set("sMonsterA", "sMonster_Temp + Script") -- ARENAFIGHT.scr:433
        ctx:state().g_hobject = ctx:objectOrNil("marker1") -- ARENAFIGHT.scr:434
        ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("g_hobject"):pos() -- ARENAFIGHT.scr:435
        ctx:state().g_hobject = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ARENAFIGHT.scr:436
    end -- ARENAFIGHT.scr:437
    ctx:object("RotatingDoor3"):trigger("use") -- ARENAFIGHT.scr:439-440
    ctx:object("RotatingDoor4"):trigger("use") -- ARENAFIGHT.scr:442-443
    do return ctx:exit("") end -- ARENAFIGHT.scr:445
end

script.labels["ClearMon"] = function(ctx)
    -- ARENAFIGHT.scr:448
    ctx:state().nMonstersDead = 0 -- ARENAFIGHT.scr:451
    ctx:object("hMonsterA"):remove() -- ARENAFIGHT.scr:452
    ctx:object("hMonsterB"):remove() -- ARENAFIGHT.scr:453
    do return ctx:exit("") end -- ARENAFIGHT.scr:454
end

script.labels["OnHello"] = function(ctx)
    -- ARENAFIGHT.scr:457
    if ctx:condition("g_nCounter==1") then -- ARENAFIGHT.scr:460
        ctx:getParam(0, "hMonsterB") -- ARENAFIGHT.scr:461
        ctx:state().g_ncounter = 0 -- ARENAFIGHT.scr:462
        do return ctx:exit("") end -- ARENAFIGHT.scr:463
    else -- ARENAFIGHT.scr:464
        ctx:getParam(0, "hMonsterA") -- ARENAFIGHT.scr:465
        ctx:state().g_nCounter = (tonumber(ctx:state().g_nCounter) or 0) + 1 -- ARENAFIGHT.scr:466
        do return ctx:exit("") end -- ARENAFIGHT.scr:467
    end -- ARENAFIGHT.scr:468
    do return ctx:exit("") end -- ARENAFIGHT.scr:469
end

script.labels["Reset"] = function(ctx)
    -- ARENAFIGHT.scr:472
    ctx:state().nMonstersDead = 0 -- ARENAFIGHT.scr:475
    ctx:takeKey(1004) -- ARENAFIGHT.scr:476
    ctx:takeKey(1005) -- ARENAFIGHT.scr:477
    ctx:takeKey(1006) -- ARENAFIGHT.scr:478
    ctx:takeKey(1007) -- ARENAFIGHT.scr:479
    ctx:takeKey(1008) -- ARENAFIGHT.scr:480
    ctx:takeKey(1010) -- ARENAFIGHT.scr:481
    ctx:takeKey(1011) -- ARENAFIGHT.scr:482
    ctx:takeKey(1012) -- ARENAFIGHT.scr:483
    ctx:takeKey(1013) -- ARENAFIGHT.scr:484
    ctx:takeKey(1014) -- ARENAFIGHT.scr:485
    ctx:takeKey(1015) -- ARENAFIGHT.scr:486
    ctx:takeKey(1016) -- ARENAFIGHT.scr:487
    ctx:takeKey(1017) -- ARENAFIGHT.scr:488
    ctx:takeKey(1018) -- ARENAFIGHT.scr:489
    ctx:takeKey(1019) -- ARENAFIGHT.scr:490
    do return ctx:exit("") end -- ARENAFIGHT.scr:492
end

script.labels["GetCharLevel"] = function(ctx)
    -- ARENAFIGHT.scr:495
    ctx:getPcLevel(0, "g_ntemp") -- ARENAFIGHT.scr:498
    ctx:set("nPlayerLevel", "NPlayerLevel + g_ntemp") -- ARENAFIGHT.scr:500
    ctx:getPcLevel(1, "g_ntemp") -- ARENAFIGHT.scr:503
    ctx:set("nPlayerLevel", "NPlayerLevel + g_ntemp") -- ARENAFIGHT.scr:504
    ctx:getPcLevel(2, "g_ntemp") -- ARENAFIGHT.scr:506
    ctx:set("nPlayerLevel", "NPlayerLevel + g_ntemp") -- ARENAFIGHT.scr:507
    ctx:getPcLevel(3, "g_ntemp") -- ARENAFIGHT.scr:509
    ctx:set("nPlayerLevel", "NPlayerLevel + g_ntemp") -- ARENAFIGHT.scr:510
    ctx:set("nPlayerLevel", "nPlayerLevel / 4") -- ARENAFIGHT.scr:513
    ctx:debugOut("nPlayerLevel") -- ARENAFIGHT.scr:515
    do return ctx:exit("") end -- ARENAFIGHT.scr:517
end

script.labels["OnDead"] = function(ctx)
    -- ARENAFIGHT.scr:520
    ctx:state().nMonstersDead = (tonumber(ctx:state().nMonstersDead) or 0) + 1 -- ARENAFIGHT.scr:523
    if ctx:condition("nMonstersDead==nNumberMonsters") then -- ARENAFIGHT.scr:524
        ctx:giveKey(1020) -- ARENAFIGHT.scr:525
        ctx:setConsoleNumVar("nWinAmount", "nArenaReward") -- ARENAFIGHT.scr:526
        ctx:object("RotatingDoor0"):trigger("UnLock") -- ARENAFIGHT.scr:527-528
        do return ctx:exit("") end -- ARENAFIGHT.scr:529
    end -- ARENAFIGHT.scr:530
    do return ctx:exit("") end -- ARENAFIGHT.scr:531
end

script.labels["OnPlayerInTheHouse"] = function(ctx)
    -- ARENAFIGHT.scr:534
    ctx:getConsoleNumVar("WaitingForPlayer", "bWaitingForPlayer") -- ARENAFIGHT.scr:536
    if ctx:condition("bWaitingForPlayer==FALSE") then -- ARENAFIGHT.scr:538
        do return ctx:exit("") end -- ARENAFIGHT.scr:539
    end -- ARENAFIGHT.scr:540
    ctx:setConsoleNumVar("WaitingForPlayer", "FALSE") -- ARENAFIGHT.scr:542
    local object = ctx:object("RotatingDoor1") -- ARENAFIGHT.scr:544
    object:trigger("close") -- ARENAFIGHT.scr:545
    object:trigger("Lock") -- ARENAFIGHT.scr:546
    do return ctx:exit("") end -- ARENAFIGHT.scr:548
end

script.labels["Main"] = function(ctx)
    -- ARENAFIGHT.scr:551
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Dead", "OnDead") -- ARENAFIGHT.scr:556
    ctx:addTrigger("Hello", "OnHello") -- ARENAFIGHT.scr:557
    ctx:addTrigger("Page", "OnPage") -- ARENAFIGHT.scr:558
    ctx:addTrigger("Squire", "OnSquire") -- ARENAFIGHT.scr:559
    ctx:addTrigger("Knight", "OnKnight") -- ARENAFIGHT.scr:560
    ctx:addTrigger("Lord", "OnLord") -- ARENAFIGHT.scr:561
    ctx:addTrigger("PlayerInTheHouse", "OnPlayerInTheHouse") -- ARENAFIGHT.scr:562
    ctx:setConsoleNumVar("WaitingForPlayer", "FALSE") -- ARENAFIGHT.scr:564
    ctx:wait(1, 1, "GetCharLevel") -- ARENAFIGHT.scr:566
    do return ctx:exit("") end -- ARENAFIGHT.scr:568
end

return script
