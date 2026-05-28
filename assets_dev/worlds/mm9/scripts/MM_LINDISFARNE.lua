-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_LINDISFARNE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 37, path = "Globals.inc" }

-- MM_Lindisfarne.scr
-- Jim Craig
-- Mundane Task List for Lindisfarne
-- Current NPCs
-- Ambient NPCs
-- Addis Auger				( 296 ) <<< REMOVED >>>
-- Aikin Smit				( 297 ) <<< REMOVED >>>
-- Horton Heland			( 298 ) <<< REMOVED >>>
-- Isham Forten			( 299 ) <<< REMOVED >>>
-- Jagr Wilaims			( 300 ) <<< REMOVED >>>
-- Bragi Gramson			( 301 ) <<< REMOVED >>>
-- Etzel Thakkradson		( 302 ) <<< REMOVED >>>
-- Bred Gagii				( 303 ) <<< REMOVED >>>
-- Ezno Skullpusher		( 304 ) <<< REMOVED >>>
-- Aod A'Norta a'leipshi	( 305 )
-- Blathmac A'Endlar		( 306 ) <<< REMOVED >>>
-- Tuathal A'Klindor		( 307 ) <<< REMOVED >>>
-- Pilgrim Robet			( 379 )
-- Pilgrim Mikal			( 380 )
-- Pilgrim Jermay			( 381 )
-- Pilgrim Jann			( 382 )
-- Pilgrim Stephe			( 383 )
-- Teacher NPCs
-- Gudlaug Eitrissen		( 404 )
-- Annabel A'Tryht			( 405 )
-- Alanna Etzeldotir		( 406 )
-- Gymir Lokissen			( 407 )
-- Delano A'Lanth			( 408 )
script.labels["OnArrived"] = function(ctx)
    -- MM_LINDISFARNE.scr:68
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:71
end

script.labels["WarpOn"] = function(ctx)
    -- MM_LINDISFARNE.scr:74
    ctx:command("bwarp", "= TRUE") -- MM_LINDISFARNE.scr:77
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:79
end

script.labels["WarpOff"] = function(ctx)
    -- MM_LINDISFARNE.scr:82
    ctx:command("bwarp", "= FALSE") -- MM_LINDISFARNE.scr:85
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:87
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_LINDISFARNE.scr:90
    if ctx:condition("goto_location == Work") then -- MM_LINDISFARNE.scr:93
        ctx:command("goto_marker", "= marker_work + npc_id") -- MM_LINDISFARNE.scr:94
    end -- MM_LINDISFARNE.scr:95
    if ctx:condition("goto_location == Home") then -- MM_LINDISFARNE.scr:97
        ctx:command("goto_marker", "= marker_home + npc_id") -- MM_LINDISFARNE.scr:98
    end -- MM_LINDISFARNE.scr:99
    if ctx:condition("goto_location == Misc") then -- MM_LINDISFARNE.scr:101
        ctx:command("goto_marker", "= marker_misc + npc_id") -- MM_LINDISFARNE.scr:102
    end -- MM_LINDISFARNE.scr:103
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:105
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_LINDISFARNE.scr:108
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_LINDISFARNE.scr:111
    ctx:command("setstat", "npc_object, PARAM, goto_marker") -- MM_LINDISFARNE.scr:113
    if ctx:condition("bWarp == FALSE") then -- MM_LINDISFARNE.scr:115
        ctx:trigger("npc_object", "GoToLoc") -- MM_LINDISFARNE.scr:116
    end -- MM_LINDISFARNE.scr:117
    if ctx:condition("bWarp == TRUE") then -- MM_LINDISFARNE.scr:119
        ctx:trigger("npc_object", "WarpToLoc") -- MM_LINDISFARNE.scr:120
    end -- MM_LINDISFARNE.scr:121
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:123
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_LINDISFARNE.scr:126
    ctx:command("index", "= 0") -- MM_LINDISFARNE.scr:129
    while ctx:condition("index < 10") do -- MM_LINDISFARNE.scr:131
        ctx:command("npc_id", "= 0") -- MM_LINDISFARNE.scr:133
        if ctx:condition("current_group == Group1") then -- MM_LINDISFARNE.scr:135
            ctx:command("arrayget", "aGroup1,index,npc_id") -- MM_LINDISFARNE.scr:136
        end -- MM_LINDISFARNE.scr:137
        if ctx:condition("current_group == Group2") then -- MM_LINDISFARNE.scr:139
            ctx:command("arrayget", "aGroup2,index,npc_id") -- MM_LINDISFARNE.scr:140
        end -- MM_LINDISFARNE.scr:141
        if ctx:condition("current_group == Group3") then -- MM_LINDISFARNE.scr:143
            ctx:command("arrayget", "aGroup3,index,npc_id") -- MM_LINDISFARNE.scr:144
        end -- MM_LINDISFARNE.scr:145
        if ctx:condition("current_group == Group4") then -- MM_LINDISFARNE.scr:147
            ctx:command("arrayget", "aGroup4,index,npc_id") -- MM_LINDISFARNE.scr:148
        end -- MM_LINDISFARNE.scr:149
        if ctx:condition("npc_id != 0") then -- MM_LINDISFARNE.scr:151
            mm9.gosub(script, ctx, "CreateMarker") -- MM_LINDISFARNE.scr:152
            mm9.gosub(script, ctx, "GoToLocation") -- MM_LINDISFARNE.scr:153
        end -- MM_LINDISFARNE.scr:154
        ctx:command("index", "= index + 1") -- MM_LINDISFARNE.scr:156
    end -- MM_LINDISFARNE.scr:157
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:159
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_LINDISFARNE.scr:166
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:169
    ctx:command("current_group", "= Group1") -- MM_LINDISFARNE.scr:170
    ctx:command("goto_location", "= Work") -- MM_LINDISFARNE.scr:171
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:172
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:174
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_LINDISFARNE.scr:177
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:180
    ctx:command("current_group", "= Group1") -- MM_LINDISFARNE.scr:181
    ctx:command("goto_location", "= Work") -- MM_LINDISFARNE.scr:182
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:183
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:185
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_LINDISFARNE.scr:188
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:191
    ctx:command("current_group", "= Group1") -- MM_LINDISFARNE.scr:192
    ctx:command("goto_location", "= Home") -- MM_LINDISFARNE.scr:193
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:194
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:196
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_LINDISFARNE.scr:199
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:202
    ctx:command("current_group", "= Group1") -- MM_LINDISFARNE.scr:203
    ctx:command("goto_location", "= Home") -- MM_LINDISFARNE.scr:204
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:205
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:207
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_LINDISFARNE.scr:210
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:213
    ctx:command("current_group", "= Group1") -- MM_LINDISFARNE.scr:214
    ctx:command("goto_location", "= Misc") -- MM_LINDISFARNE.scr:215
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:216
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:218
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_LINDISFARNE.scr:221
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:224
    ctx:command("current_group", "= Group1") -- MM_LINDISFARNE.scr:225
    ctx:command("goto_location", "= Misc") -- MM_LINDISFARNE.scr:226
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:227
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:229
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_LINDISFARNE.scr:233
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:236
    ctx:command("current_group", "= Group2") -- MM_LINDISFARNE.scr:237
    ctx:command("goto_location", "= Work") -- MM_LINDISFARNE.scr:238
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:239
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:241
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_LINDISFARNE.scr:244
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:247
    ctx:command("current_group", "= Group2") -- MM_LINDISFARNE.scr:248
    ctx:command("goto_location", "= Work") -- MM_LINDISFARNE.scr:249
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:250
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:252
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_LINDISFARNE.scr:255
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:258
    ctx:command("current_group", "= Group2") -- MM_LINDISFARNE.scr:259
    ctx:command("goto_location", "= Home") -- MM_LINDISFARNE.scr:260
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:261
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:263
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_LINDISFARNE.scr:266
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:269
    ctx:command("current_group", "= Group2") -- MM_LINDISFARNE.scr:270
    ctx:command("goto_location", "= Home") -- MM_LINDISFARNE.scr:271
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:272
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:274
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_LINDISFARNE.scr:277
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:280
    ctx:command("current_group", "= Group2") -- MM_LINDISFARNE.scr:281
    ctx:command("goto_location", "= Misc") -- MM_LINDISFARNE.scr:282
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:283
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:285
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_LINDISFARNE.scr:288
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:291
    ctx:command("current_group", "= Group2") -- MM_LINDISFARNE.scr:292
    ctx:command("goto_location", "= Misc") -- MM_LINDISFARNE.scr:293
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:294
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:296
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_LINDISFARNE.scr:299
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:302
    ctx:command("current_group", "= Group3") -- MM_LINDISFARNE.scr:303
    ctx:command("goto_location", "= Work") -- MM_LINDISFARNE.scr:304
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:305
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:307
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_LINDISFARNE.scr:310
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:313
    ctx:command("current_group", "= Group3") -- MM_LINDISFARNE.scr:314
    ctx:command("goto_location", "= Work") -- MM_LINDISFARNE.scr:315
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:316
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:318
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_LINDISFARNE.scr:321
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:324
    ctx:command("current_group", "= Group3") -- MM_LINDISFARNE.scr:325
    ctx:command("goto_location", "= Home") -- MM_LINDISFARNE.scr:326
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:327
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:329
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_LINDISFARNE.scr:332
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:335
    ctx:command("current_group", "= Group3") -- MM_LINDISFARNE.scr:336
    ctx:command("goto_location", "= Home") -- MM_LINDISFARNE.scr:337
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:338
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:340
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_LINDISFARNE.scr:343
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:346
    ctx:command("current_group", "= Group3") -- MM_LINDISFARNE.scr:347
    ctx:command("goto_location", "= Misc") -- MM_LINDISFARNE.scr:348
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:349
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:351
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_LINDISFARNE.scr:354
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:357
    ctx:command("current_group", "= Group3") -- MM_LINDISFARNE.scr:358
    ctx:command("goto_location", "= Misc") -- MM_LINDISFARNE.scr:359
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:360
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:362
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_LINDISFARNE.scr:365
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:368
    ctx:command("current_group", "= Group4") -- MM_LINDISFARNE.scr:369
    ctx:command("goto_location", "= Work") -- MM_LINDISFARNE.scr:370
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:371
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:373
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_LINDISFARNE.scr:376
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:379
    ctx:command("current_group", "= Group4") -- MM_LINDISFARNE.scr:380
    ctx:command("goto_location", "= Work") -- MM_LINDISFARNE.scr:381
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:382
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:384
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_LINDISFARNE.scr:388
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:391
    ctx:command("current_group", "= Group4") -- MM_LINDISFARNE.scr:392
    ctx:command("goto_location", "= Home") -- MM_LINDISFARNE.scr:393
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:394
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:396
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_LINDISFARNE.scr:399
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:402
    ctx:command("current_group", "= Group4") -- MM_LINDISFARNE.scr:403
    ctx:command("goto_location", "= Home") -- MM_LINDISFARNE.scr:404
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:405
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:407
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_LINDISFARNE.scr:410
    mm9.gosub(script, ctx, "WarpOff") -- MM_LINDISFARNE.scr:413
    ctx:command("current_group", "= Group4") -- MM_LINDISFARNE.scr:414
    ctx:command("goto_location", "= Misc") -- MM_LINDISFARNE.scr:415
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:416
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:418
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_LINDISFARNE.scr:421
    mm9.gosub(script, ctx, "WarpOn") -- MM_LINDISFARNE.scr:424
    ctx:command("current_group", "= Group4") -- MM_LINDISFARNE.scr:425
    ctx:command("goto_location", "= Misc") -- MM_LINDISFARNE.scr:426
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_LINDISFARNE.scr:427
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:429
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_LINDISFARNE.scr:437
    ctx:command("@m", "6 : 15 Group1_GoWork Group1_WarpWork") -- MM_LINDISFARNE.scr:440
    ctx:command("@m", "6 : 30 Group2_GoWork Group2_WarpWork") -- MM_LINDISFARNE.scr:441
    ctx:command("@m", "6 : 45 Group3_GoWork Group3_WarpWork") -- MM_LINDISFARNE.scr:442
    ctx:command("@m", "7 : 00 Group4_GoWork Group4_WarpWork") -- MM_LINDISFARNE.scr:443
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:445
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_LINDISFARNE.scr:449
    ctx:command("@m", "18 : 00 Group1_GoHome Group1_WarpHome") -- MM_LINDISFARNE.scr:452
    ctx:command("@m", "18 : 15 Group2_GoHome Group2_WarpHome") -- MM_LINDISFARNE.scr:453
    ctx:command("@m", "18 : 30 Group3_GoHome Group3_WarpHome") -- MM_LINDISFARNE.scr:454
    ctx:command("@m", "18 : 45 Group4_GoHome Group4_WarpHome") -- MM_LINDISFARNE.scr:455
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:457
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_LINDISFARNE.scr:460
    -- Go Wander off to somewhere
    ctx:command("@m", "13 : 00 Group1_GoMisc Group1_WarpMisc") -- MM_LINDISFARNE.scr:464
    ctx:command("@m", "13 : 15 Group2_GoMisc Group2_WarpMisc") -- MM_LINDISFARNE.scr:465
    ctx:command("@m", "13 : 30 Group3_GoMisc Group3_WarpMisc") -- MM_LINDISFARNE.scr:466
    ctx:command("@m", "13 : 45 Group4_GoMisc Group4_WarpMisc") -- MM_LINDISFARNE.scr:467
    -- Go Back to work
    ctx:command("@m", "15 : 00 Group1_GoWork Group1_WarpWork") -- MM_LINDISFARNE.scr:470
    ctx:command("@m", "15 : 15 Group2_GoWork Group2_WarpWork") -- MM_LINDISFARNE.scr:471
    ctx:command("@m", "15 : 30 Group3_GoWork Group3_WarpWork") -- MM_LINDISFARNE.scr:472
    ctx:command("@m", "15 : 45 Group4_GoWork Group4_WarpWork") -- MM_LINDISFARNE.scr:473
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:475
end

script.labels["InitArrays"] = function(ctx)
    -- MM_LINDISFARNE.scr:483
    ctx:command("index", "= 0") -- MM_LINDISFARNE.scr:486
    while ctx:condition("index < 10") do -- MM_LINDISFARNE.scr:487
        ctx:command("arrayput", "aGroup1, index , 0") -- MM_LINDISFARNE.scr:488
        ctx:command("arrayput", "aGroup2, index , 0") -- MM_LINDISFARNE.scr:489
        ctx:command("arrayput", "aGroup3, index , 0") -- MM_LINDISFARNE.scr:490
        ctx:command("arrayput", "aGroup4, index , 0") -- MM_LINDISFARNE.scr:491
        ctx:command("index", "= index + 1") -- MM_LINDISFARNE.scr:492
    end -- MM_LINDISFARNE.scr:493
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:495
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_LINDISFARNE.scr:499
    -- Pilgrim Robet			( 379 )
    ctx:command("arrayput", "aGroup1,0,379") -- MM_LINDISFARNE.scr:503
    -- Pilgrim Stephe			( 383 )
    ctx:command("arrayput", "aGroup1,1,383") -- MM_LINDISFARNE.scr:506
    -- Gymir Lokissen			( 407 )
    ctx:command("arrayput", "aGroup1,2,407") -- MM_LINDISFARNE.scr:509
    -- Addis Auger				( 296 )	<<< REMOVED >>>
    -- ArrayPut aGroup1,3,296
    -- Jagr Wilaims			( 300 ) <<< REMOVED >>>
    -- ArrayPut aGroup1,4,300
    -- Ezno Skullpusher		( 304 ) <<< REMOVED >>>
    -- ArrayPut aGroup1,5,304
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:520
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_LINDISFARNE.scr:523
    -- Aod A'Norta a'leipshi	( 305 )
    ctx:command("arrayput", "aGroup2,0,305") -- MM_LINDISFARNE.scr:527
    -- Pilgrim Mikal			( 380 )
    ctx:command("arrayput", "aGroup2,1,380") -- MM_LINDISFARNE.scr:530
    -- Gudlaug Eitrissen		( 404 )
    ctx:command("arrayput", "aGroup2,2,404") -- MM_LINDISFARNE.scr:533
    -- Delano A'Lanth			( 408 )
    ctx:command("arrayput", "aGroup2,3,408") -- MM_LINDISFARNE.scr:536
    -- Aikin Smit				( 297 ) <<< REMOVED >>>
    -- ArrayPut aGroup2,4,297
    -- Bragi Gramson			( 301 ) <<< REMOVED >>>
    -- ArrayPut aGroup2,5,301
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:544
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_LINDISFARNE.scr:547
    -- Pilgrim Jermay			( 381 )
    ctx:command("arrayput", "aGroup3,0,381") -- MM_LINDISFARNE.scr:551
    -- Annabel A'Tryht			( 405 )
    ctx:command("arrayput", "aGroup3,1,405") -- MM_LINDISFARNE.scr:554
    -- Horton Heland			( 298 ) <<< REMOVED >>>
    -- ArrayPut aGroup3,2,298
    -- Etzel Thakkradson		( 302 ) <<< REMOVED >>>
    -- ArrayPut aGroup3,3,302
    -- Blathmac A'Endlar		( 306 ) <<< REMOVED >>>
    -- ArrayPut aGroup3,4,306
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:566
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_LINDISFARNE.scr:569
    -- Pilgrim Jann			( 382 )
    ctx:command("arrayput", "aGroup4,0,382") -- MM_LINDISFARNE.scr:573
    -- Alanna Etzeldotir		( 406 )
    ctx:command("arrayput", "aGroup4,1,406") -- MM_LINDISFARNE.scr:576
end

script.labels["Isham Forten\t\t\t( 299 ) <<< REMOVED >>>"] = function(ctx)
    -- MM_LINDISFARNE.scr:578
    -- ArrayPut aGroup4,2,299
    -- Bred Gagii				( 303 ) <<< REMOVED >>>
    -- ArrayPut aGroup4,3,303
    -- Tuathal A'Klindor		( 307 ) <<< REMOVED >>>
    -- ArrayPut aGroup4,4,307
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:587
end

script.labels["Init"] = function(ctx)
    -- MM_LINDISFARNE.scr:590
    mm9.gosub(script, ctx, "InitArrays") -- MM_LINDISFARNE.scr:592
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_LINDISFARNE.scr:594
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_LINDISFARNE.scr:595
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_LINDISFARNE.scr:596
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_LINDISFARNE.scr:597
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_LINDISFARNE.scr:599
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_LINDISFARNE.scr:600
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_LINDISFARNE.scr:601
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:603
end

script.labels["Main"] = function(ctx)
    -- MM_LINDISFARNE.scr:606
    mm9.gosub(script, ctx, "Init") -- MM_LINDISFARNE.scr:608
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_LINDISFARNE.scr:609
    do return ctx:exit("") end -- MM_LINDISFARNE.scr:611
end

return script
