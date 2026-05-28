-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_DRANGHEIMCITY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 35, path = "Globals.inc" }

-- MM_DrangheimCity.scr
-- Jim Craig
-- Mundane Task List for Drangheim City
-- Current NPCs
-- Gossip NPCs
-- Alfrigg Hafnarssen  ( 109 ) <<< REMOVED >>>
-- Hrolf Anfarssen		( 110 ) <<< REMOVED >>>
-- Ambient NPCs
-- Iosobail A'Norta a'leipshi	( 113 )
-- Fisk Goldenhand				( 116 )
-- Anneka Herjolfdotir			( 117 )
-- Freja Goodears				( 118 )
-- Talco Tonlan				( 121 )
-- Korina Martla				( 122 )
-- Ejnar Bluetooth				( 120 )
-- Teacher NPCs
-- Cermak Atlor				( 123 )
-- Hagar the Horrible			( 119 )
-- Aefentid A'Feslo			( 114 )
-- Thorhalla the Short			( 394 )
-- Krej Matlal					( 124 )
-- Galvin A'mor				( 115 )
-- Fasolt Hredmarssen			( 395 )
-- Rannveig Hargrimdotir		( 396 )
-- Cassidy A'Dorad				( 397 )
script.labels["OnArrived"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:66
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:69
end

script.labels["WarpOn"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:72
    ctx:command("bwarp", "= TRUE") -- MM_DRANGHEIMCITY.scr:75
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:77
end

script.labels["WarpOff"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:80
    ctx:command("bwarp", "= FALSE") -- MM_DRANGHEIMCITY.scr:83
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:85
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:88
    if ctx:condition("goto_location == Work") then -- MM_DRANGHEIMCITY.scr:91
        ctx:command("goto_marker", "= marker_work + npc_id") -- MM_DRANGHEIMCITY.scr:92
    end -- MM_DRANGHEIMCITY.scr:93
    if ctx:condition("goto_location == Home") then -- MM_DRANGHEIMCITY.scr:95
        ctx:command("goto_marker", "= marker_home + npc_id") -- MM_DRANGHEIMCITY.scr:96
    end -- MM_DRANGHEIMCITY.scr:97
    if ctx:condition("goto_location == Misc") then -- MM_DRANGHEIMCITY.scr:99
        ctx:command("goto_marker", "= marker_misc + npc_id") -- MM_DRANGHEIMCITY.scr:100
    end -- MM_DRANGHEIMCITY.scr:101
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:103
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:106
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_DRANGHEIMCITY.scr:109
    ctx:command("setstat", "npc_object, PARAM, goto_marker") -- MM_DRANGHEIMCITY.scr:111
    if ctx:condition("bWarp == FALSE") then -- MM_DRANGHEIMCITY.scr:113
        ctx:trigger("npc_object", "GoToLoc") -- MM_DRANGHEIMCITY.scr:114
    end -- MM_DRANGHEIMCITY.scr:115
    if ctx:condition("bWarp == TRUE") then -- MM_DRANGHEIMCITY.scr:117
        ctx:trigger("npc_object", "WarpToLoc") -- MM_DRANGHEIMCITY.scr:118
    end -- MM_DRANGHEIMCITY.scr:119
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:121
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:124
    ctx:command("index", "= 0") -- MM_DRANGHEIMCITY.scr:127
    while ctx:condition("index < 10") do -- MM_DRANGHEIMCITY.scr:129
        ctx:command("npc_id", "= 0") -- MM_DRANGHEIMCITY.scr:131
        if ctx:condition("current_group == Group1") then -- MM_DRANGHEIMCITY.scr:133
            ctx:command("arrayget", "aGroup1,index,npc_id") -- MM_DRANGHEIMCITY.scr:134
        end -- MM_DRANGHEIMCITY.scr:135
        if ctx:condition("current_group == Group2") then -- MM_DRANGHEIMCITY.scr:137
            ctx:command("arrayget", "aGroup2,index,npc_id") -- MM_DRANGHEIMCITY.scr:138
        end -- MM_DRANGHEIMCITY.scr:139
        if ctx:condition("current_group == Group3") then -- MM_DRANGHEIMCITY.scr:141
            ctx:command("arrayget", "aGroup3,index,npc_id") -- MM_DRANGHEIMCITY.scr:142
        end -- MM_DRANGHEIMCITY.scr:143
        if ctx:condition("current_group == Group4") then -- MM_DRANGHEIMCITY.scr:145
            ctx:command("arrayget", "aGroup4,index,npc_id") -- MM_DRANGHEIMCITY.scr:146
        end -- MM_DRANGHEIMCITY.scr:147
        if ctx:condition("npc_id != 0") then -- MM_DRANGHEIMCITY.scr:149
            mm9.gosub(script, ctx, "CreateMarker") -- MM_DRANGHEIMCITY.scr:150
            mm9.gosub(script, ctx, "GoToLocation") -- MM_DRANGHEIMCITY.scr:151
        end -- MM_DRANGHEIMCITY.scr:152
        ctx:command("index", "= index + 1") -- MM_DRANGHEIMCITY.scr:154
    end -- MM_DRANGHEIMCITY.scr:155
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:157
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:164
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:167
    ctx:command("current_group", "= Group1") -- MM_DRANGHEIMCITY.scr:168
    ctx:command("goto_location", "= Work") -- MM_DRANGHEIMCITY.scr:169
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:170
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:172
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:175
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:178
    ctx:command("current_group", "= Group1") -- MM_DRANGHEIMCITY.scr:179
    ctx:command("goto_location", "= Work") -- MM_DRANGHEIMCITY.scr:180
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:181
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:183
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:186
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:189
    ctx:command("current_group", "= Group1") -- MM_DRANGHEIMCITY.scr:190
    ctx:command("goto_location", "= Home") -- MM_DRANGHEIMCITY.scr:191
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:192
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:194
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:197
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:200
    ctx:command("current_group", "= Group1") -- MM_DRANGHEIMCITY.scr:201
    ctx:command("goto_location", "= Home") -- MM_DRANGHEIMCITY.scr:202
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:203
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:205
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:208
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:211
    ctx:command("current_group", "= Group1") -- MM_DRANGHEIMCITY.scr:212
    ctx:command("goto_location", "= Misc") -- MM_DRANGHEIMCITY.scr:213
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:214
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:216
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:219
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:222
    ctx:command("current_group", "= Group1") -- MM_DRANGHEIMCITY.scr:223
    ctx:command("goto_location", "= Misc") -- MM_DRANGHEIMCITY.scr:224
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:225
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:227
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:231
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:234
    ctx:command("current_group", "= Group2") -- MM_DRANGHEIMCITY.scr:235
    ctx:command("goto_location", "= Work") -- MM_DRANGHEIMCITY.scr:236
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:237
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:239
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:242
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:245
    ctx:command("current_group", "= Group2") -- MM_DRANGHEIMCITY.scr:246
    ctx:command("goto_location", "= Work") -- MM_DRANGHEIMCITY.scr:247
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:248
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:250
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:253
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:256
    ctx:command("current_group", "= Group2") -- MM_DRANGHEIMCITY.scr:257
    ctx:command("goto_location", "= Home") -- MM_DRANGHEIMCITY.scr:258
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:259
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:261
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:264
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:267
    ctx:command("current_group", "= Group2") -- MM_DRANGHEIMCITY.scr:268
    ctx:command("goto_location", "= Home") -- MM_DRANGHEIMCITY.scr:269
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:270
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:272
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:275
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:278
    ctx:command("current_group", "= Group2") -- MM_DRANGHEIMCITY.scr:279
    ctx:command("goto_location", "= Misc") -- MM_DRANGHEIMCITY.scr:280
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:281
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:283
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:286
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:289
    ctx:command("current_group", "= Group2") -- MM_DRANGHEIMCITY.scr:290
    ctx:command("goto_location", "= Misc") -- MM_DRANGHEIMCITY.scr:291
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:292
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:294
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:297
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:300
    ctx:command("current_group", "= Group3") -- MM_DRANGHEIMCITY.scr:301
    ctx:command("goto_location", "= Work") -- MM_DRANGHEIMCITY.scr:302
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:303
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:305
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:308
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:311
    ctx:command("current_group", "= Group3") -- MM_DRANGHEIMCITY.scr:312
    ctx:command("goto_location", "= Work") -- MM_DRANGHEIMCITY.scr:313
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:314
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:316
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:319
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:322
    ctx:command("current_group", "= Group3") -- MM_DRANGHEIMCITY.scr:323
    ctx:command("goto_location", "= Home") -- MM_DRANGHEIMCITY.scr:324
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:325
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:327
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:330
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:333
    ctx:command("current_group", "= Group3") -- MM_DRANGHEIMCITY.scr:334
    ctx:command("goto_location", "= Home") -- MM_DRANGHEIMCITY.scr:335
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:336
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:338
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:341
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:344
    ctx:command("current_group", "= Group3") -- MM_DRANGHEIMCITY.scr:345
    ctx:command("goto_location", "= Misc") -- MM_DRANGHEIMCITY.scr:346
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:347
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:349
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:352
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:355
    ctx:command("current_group", "= Group3") -- MM_DRANGHEIMCITY.scr:356
    ctx:command("goto_location", "= Misc") -- MM_DRANGHEIMCITY.scr:357
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:358
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:360
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:363
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:366
    ctx:command("current_group", "= Group4") -- MM_DRANGHEIMCITY.scr:367
    ctx:command("goto_location", "= Work") -- MM_DRANGHEIMCITY.scr:368
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:369
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:371
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:374
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:377
    ctx:command("current_group", "= Group4") -- MM_DRANGHEIMCITY.scr:378
    ctx:command("goto_location", "= Work") -- MM_DRANGHEIMCITY.scr:379
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:380
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:382
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:386
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:389
    ctx:command("current_group", "= Group4") -- MM_DRANGHEIMCITY.scr:390
    ctx:command("goto_location", "= Home") -- MM_DRANGHEIMCITY.scr:391
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:392
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:394
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:397
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:400
    ctx:command("current_group", "= Group4") -- MM_DRANGHEIMCITY.scr:401
    ctx:command("goto_location", "= Home") -- MM_DRANGHEIMCITY.scr:402
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:403
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:405
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:408
    mm9.gosub(script, ctx, "WarpOff") -- MM_DRANGHEIMCITY.scr:411
    ctx:command("current_group", "= Group4") -- MM_DRANGHEIMCITY.scr:412
    ctx:command("goto_location", "= Misc") -- MM_DRANGHEIMCITY.scr:413
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:414
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:416
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:419
    mm9.gosub(script, ctx, "WarpOn") -- MM_DRANGHEIMCITY.scr:422
    ctx:command("current_group", "= Group4") -- MM_DRANGHEIMCITY.scr:423
    ctx:command("goto_location", "= Misc") -- MM_DRANGHEIMCITY.scr:424
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_DRANGHEIMCITY.scr:425
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:427
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:435
    ctx:command("@m", "6 : 15 Group1_GoWork Group1_WarpWork") -- MM_DRANGHEIMCITY.scr:438
    ctx:command("@m", "6 : 30 Group2_GoWork Group2_WarpWork") -- MM_DRANGHEIMCITY.scr:439
    ctx:command("@m", "6 : 45 Group3_GoWork Group3_WarpWork") -- MM_DRANGHEIMCITY.scr:440
    ctx:command("@m", "7 : 00 Group4_GoWork Group4_WarpWork") -- MM_DRANGHEIMCITY.scr:441
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:443
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:447
    ctx:command("@m", "18 : 00 Group1_GoHome Group1_WarpHome") -- MM_DRANGHEIMCITY.scr:450
    ctx:command("@m", "18 : 15 Group2_GoHome Group2_WarpHome") -- MM_DRANGHEIMCITY.scr:451
    ctx:command("@m", "18 : 30 Group3_GoHome Group3_WarpHome") -- MM_DRANGHEIMCITY.scr:452
    ctx:command("@m", "18 : 45 Group4_GoHome Group4_WarpHome") -- MM_DRANGHEIMCITY.scr:453
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:455
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:458
    -- Go Wander off to somewhere
    ctx:command("@m", "13 : 00 Group1_GoMisc Group1_WarpMisc") -- MM_DRANGHEIMCITY.scr:462
    ctx:command("@m", "13 : 15 Group2_GoMisc Group2_WarpMisc") -- MM_DRANGHEIMCITY.scr:463
    ctx:command("@m", "13 : 30 Group3_GoMisc Group3_WarpMisc") -- MM_DRANGHEIMCITY.scr:464
    ctx:command("@m", "13 : 45 Group4_GoMisc Group4_WarpMisc") -- MM_DRANGHEIMCITY.scr:465
    -- Go Back to work
    ctx:command("@m", "15 : 00 Group1_GoWork Group1_WarpWork") -- MM_DRANGHEIMCITY.scr:468
    ctx:command("@m", "15 : 15 Group2_GoWork Group2_WarpWork") -- MM_DRANGHEIMCITY.scr:469
    ctx:command("@m", "15 : 30 Group3_GoWork Group3_WarpWork") -- MM_DRANGHEIMCITY.scr:470
    ctx:command("@m", "15 : 45 Group4_GoWork Group4_WarpWork") -- MM_DRANGHEIMCITY.scr:471
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:473
end

script.labels["InitArrays"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:481
    ctx:command("index", "= 0") -- MM_DRANGHEIMCITY.scr:484
    while ctx:condition("index < 10") do -- MM_DRANGHEIMCITY.scr:485
        ctx:command("arrayput", "aGroup1, index , 0") -- MM_DRANGHEIMCITY.scr:486
        ctx:command("arrayput", "aGroup2, index , 0") -- MM_DRANGHEIMCITY.scr:487
        ctx:command("arrayput", "aGroup3, index , 0") -- MM_DRANGHEIMCITY.scr:488
        ctx:command("arrayput", "aGroup4, index , 0") -- MM_DRANGHEIMCITY.scr:489
        ctx:command("index", "= index + 1") -- MM_DRANGHEIMCITY.scr:490
    end -- MM_DRANGHEIMCITY.scr:491
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:493
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:497
    -- Anneka Herjolfdotir			( 117 )
    ctx:command("arrayput", "aGroup1,0,117") -- MM_DRANGHEIMCITY.scr:501
    -- Ejnar Bluetooth				( 120 )
    ctx:command("arrayput", "aGroup1,1,120") -- MM_DRANGHEIMCITY.scr:504
    -- Thorhalla the Short			( 394 )
    ctx:command("arrayput", "aGroup1,2,394") -- MM_DRANGHEIMCITY.scr:507
    -- Rannveig Hargrimdotir		( 396 )
    ctx:command("arrayput", "aGroup1,3,396") -- MM_DRANGHEIMCITY.scr:510
    -- Alfrigg Hafnarssen			( 109 ) <<< REMOVED >>>
    -- ArrayPut aGroup1,4,109
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:515
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:518
    -- Freja Goodears				( 118 )
    ctx:command("arrayput", "aGroup2,0,118") -- MM_DRANGHEIMCITY.scr:522
    -- Cermak Atlor				( 123 )
    ctx:command("arrayput", "aGroup2,1,123") -- MM_DRANGHEIMCITY.scr:525
    -- Krej Matlal					( 124 )
    ctx:command("arrayput", "aGroup2,2,124") -- MM_DRANGHEIMCITY.scr:528
    -- Cassidy A'Dorad				( 397 )
    ctx:command("arrayput", "aGroup2,3,397") -- MM_DRANGHEIMCITY.scr:531
    -- Hrolf Anfarssen				( 110 ) <<< REMOVED >>>
    -- ArrayPut aGroup2,4,110
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:537
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:540
    -- Iosobail A'Norta a'leipshi	( 113 )
    ctx:command("arrayput", "aGroup3,0,113") -- MM_DRANGHEIMCITY.scr:544
    -- Talco Tonlan				( 121 )
    ctx:command("arrayput", "aGroup3,1,121") -- MM_DRANGHEIMCITY.scr:547
    -- Hagar the Horrible			( 119 )
    ctx:command("arrayput", "aGroup3,2,119") -- MM_DRANGHEIMCITY.scr:550
    -- Galvin A'mor				( 115 )
    ctx:command("arrayput", "aGroup3,3, 115") -- MM_DRANGHEIMCITY.scr:553
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:555
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:558
    -- Fisk Goldenhand				( 116 )
    ctx:command("arrayput", "aGroup4,0,116") -- MM_DRANGHEIMCITY.scr:562
    -- Korina Martla				( 122 )
    ctx:command("arrayput", "aGroup4,1,122") -- MM_DRANGHEIMCITY.scr:565
    -- Aefentid A'Feslo			( 114 )
    ctx:command("arrayput", "aGroup4,2,114") -- MM_DRANGHEIMCITY.scr:568
    -- Fasolt Hredmarssen			( 395 )
    ctx:command("arrayput", "aGroup4,3,395") -- MM_DRANGHEIMCITY.scr:571
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:573
end

script.labels["Init"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:577
    mm9.gosub(script, ctx, "InitArrays") -- MM_DRANGHEIMCITY.scr:579
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_DRANGHEIMCITY.scr:581
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_DRANGHEIMCITY.scr:582
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_DRANGHEIMCITY.scr:583
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_DRANGHEIMCITY.scr:584
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_DRANGHEIMCITY.scr:586
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_DRANGHEIMCITY.scr:587
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_DRANGHEIMCITY.scr:588
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:590
end

script.labels["Main"] = function(ctx)
    -- MM_DRANGHEIMCITY.scr:593
    mm9.gosub(script, ctx, "Init") -- MM_DRANGHEIMCITY.scr:595
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_DRANGHEIMCITY.scr:596
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:598
end

return script
