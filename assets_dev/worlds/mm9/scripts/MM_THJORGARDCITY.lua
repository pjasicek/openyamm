-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_THJORGARDCITY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 46, path = "Globals.inc" }

-- MM_ThjorgardCity.scr
-- Jim Craig
-- Mundane Task List for Thjordard City
-- Current NPCs
-- Gossip NPCs
-- Gunnar Thorlakssen			( 22 )
-- Donnachac A'Washadi			( 23 )
-- Raghnailt A'Ghrie			( 24 )
-- Fiachu A'Dlinn				( 25 )
-- Ambient NPCs
-- Bodil the Brawny			( 31 )
-- Frode Fafnirssen			( 32 )
-- Annelise Baldundotir		( 33 )
-- Karl Knutssen				( 34 )
-- Britta Stonewasher			( 35 )
-- Einar Thorfinssen			( 36 )
-- Teacher NPCs
-- Barabell A'Dorad			( 267 )
-- Cator Fiskdal				( 295 )
-- Eilinoir A'Mor				( 310 )
-- Bysen A'Klindor				( 40 )
-- Darby Davinssen				( 311 )
-- Tove Halvardotir			( 320 )
-- Toman Yatol					( 38 )
-- Giorsal A'Velsi				( 321 )
-- Comhgan A'Dorad				( 41 )
-- Cinnfhail A'Mor				( 347 )
-- Gjerta Headstrong			( 37 )
-- Hrrapp Spearhands			( 361 )
-- Muadhnait A'Tryht			( 362 )
-- Thorfinn Quickeye			( 384 )
-- Chera Papan					( 39 )
-- Sigre Bjarnidotir			( 385 )
-- Fjarkskafinn the Still-alive	( 386 )
-- Halfdan the Hidden			( 387 )
-- Hildigunna the Quick		( 388 )
script.labels["OnArrived"] = function(ctx)
    -- MM_THJORGARDCITY.scr:77
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:80
end

script.labels["WarpOn"] = function(ctx)
    -- MM_THJORGARDCITY.scr:83
    ctx:command("bwarp", "= TRUE") -- MM_THJORGARDCITY.scr:86
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:88
end

script.labels["WarpOff"] = function(ctx)
    -- MM_THJORGARDCITY.scr:91
    ctx:command("bwarp", "= FALSE") -- MM_THJORGARDCITY.scr:94
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:96
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_THJORGARDCITY.scr:99
    if ctx:condition("goto_location == Work") then -- MM_THJORGARDCITY.scr:102
        ctx:command("goto_marker", "= marker_work + npc_id") -- MM_THJORGARDCITY.scr:103
    end -- MM_THJORGARDCITY.scr:104
    if ctx:condition("goto_location == Home") then -- MM_THJORGARDCITY.scr:106
        ctx:command("goto_marker", "= marker_home + npc_id") -- MM_THJORGARDCITY.scr:107
    end -- MM_THJORGARDCITY.scr:108
    if ctx:condition("goto_location == Misc") then -- MM_THJORGARDCITY.scr:110
        ctx:command("goto_marker", "= marker_misc + npc_id") -- MM_THJORGARDCITY.scr:111
    end -- MM_THJORGARDCITY.scr:112
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:114
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_THJORGARDCITY.scr:117
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_THJORGARDCITY.scr:120
    ctx:command("setstat", "npc_object, PARAM, goto_marker") -- MM_THJORGARDCITY.scr:122
    if ctx:condition("bWarp == FALSE") then -- MM_THJORGARDCITY.scr:124
        ctx:trigger("npc_object", "GoToLoc") -- MM_THJORGARDCITY.scr:125
    end -- MM_THJORGARDCITY.scr:126
    if ctx:condition("bWarp == TRUE") then -- MM_THJORGARDCITY.scr:128
        ctx:trigger("npc_object", "WarpToLoc") -- MM_THJORGARDCITY.scr:129
    end -- MM_THJORGARDCITY.scr:130
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:132
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_THJORGARDCITY.scr:135
    ctx:command("index", "= 0") -- MM_THJORGARDCITY.scr:138
    while ctx:condition("index < 10") do -- MM_THJORGARDCITY.scr:140
        ctx:command("npc_id", "= 0") -- MM_THJORGARDCITY.scr:142
        if ctx:condition("current_group == Group1") then -- MM_THJORGARDCITY.scr:144
            ctx:command("arrayget", "aGroup1,index,npc_id") -- MM_THJORGARDCITY.scr:145
        end -- MM_THJORGARDCITY.scr:146
        if ctx:condition("current_group == Group2") then -- MM_THJORGARDCITY.scr:148
            ctx:command("arrayget", "aGroup2,index,npc_id") -- MM_THJORGARDCITY.scr:149
        end -- MM_THJORGARDCITY.scr:150
        if ctx:condition("current_group == Group3") then -- MM_THJORGARDCITY.scr:152
            ctx:command("arrayget", "aGroup3,index,npc_id") -- MM_THJORGARDCITY.scr:153
        end -- MM_THJORGARDCITY.scr:154
        if ctx:condition("current_group == Group4") then -- MM_THJORGARDCITY.scr:156
            ctx:command("arrayget", "aGroup4,index,npc_id") -- MM_THJORGARDCITY.scr:157
        end -- MM_THJORGARDCITY.scr:158
        if ctx:condition("npc_id != 0") then -- MM_THJORGARDCITY.scr:160
            mm9.gosub(script, ctx, "CreateMarker") -- MM_THJORGARDCITY.scr:161
            mm9.gosub(script, ctx, "GoToLocation") -- MM_THJORGARDCITY.scr:162
        end -- MM_THJORGARDCITY.scr:163
        ctx:command("index", "= index + 1") -- MM_THJORGARDCITY.scr:165
    end -- MM_THJORGARDCITY.scr:166
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:168
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_THJORGARDCITY.scr:175
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:178
    ctx:command("current_group", "= Group1") -- MM_THJORGARDCITY.scr:179
    ctx:command("goto_location", "= Work") -- MM_THJORGARDCITY.scr:180
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:181
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:183
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_THJORGARDCITY.scr:186
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:189
    ctx:command("current_group", "= Group1") -- MM_THJORGARDCITY.scr:190
    ctx:command("goto_location", "= Work") -- MM_THJORGARDCITY.scr:191
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:192
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:194
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_THJORGARDCITY.scr:197
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:200
    ctx:command("current_group", "= Group1") -- MM_THJORGARDCITY.scr:201
    ctx:command("goto_location", "= Home") -- MM_THJORGARDCITY.scr:202
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:203
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:205
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_THJORGARDCITY.scr:208
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:211
    ctx:command("current_group", "= Group1") -- MM_THJORGARDCITY.scr:212
    ctx:command("goto_location", "= Home") -- MM_THJORGARDCITY.scr:213
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:214
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:216
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_THJORGARDCITY.scr:219
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:222
    ctx:command("current_group", "= Group1") -- MM_THJORGARDCITY.scr:223
    ctx:command("goto_location", "= Misc") -- MM_THJORGARDCITY.scr:224
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:225
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:227
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_THJORGARDCITY.scr:230
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:233
    ctx:command("current_group", "= Group1") -- MM_THJORGARDCITY.scr:234
    ctx:command("goto_location", "= Misc") -- MM_THJORGARDCITY.scr:235
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:236
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:238
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_THJORGARDCITY.scr:242
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:245
    ctx:command("current_group", "= Group2") -- MM_THJORGARDCITY.scr:246
    ctx:command("goto_location", "= Work") -- MM_THJORGARDCITY.scr:247
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:248
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:250
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_THJORGARDCITY.scr:253
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:256
    ctx:command("current_group", "= Group2") -- MM_THJORGARDCITY.scr:257
    ctx:command("goto_location", "= Work") -- MM_THJORGARDCITY.scr:258
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:259
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:261
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_THJORGARDCITY.scr:264
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:267
    ctx:command("current_group", "= Group2") -- MM_THJORGARDCITY.scr:268
    ctx:command("goto_location", "= Home") -- MM_THJORGARDCITY.scr:269
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:270
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:272
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_THJORGARDCITY.scr:275
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:278
    ctx:command("current_group", "= Group2") -- MM_THJORGARDCITY.scr:279
    ctx:command("goto_location", "= Home") -- MM_THJORGARDCITY.scr:280
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:281
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:283
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_THJORGARDCITY.scr:286
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:289
    ctx:command("current_group", "= Group2") -- MM_THJORGARDCITY.scr:290
    ctx:command("goto_location", "= Misc") -- MM_THJORGARDCITY.scr:291
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:292
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:294
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_THJORGARDCITY.scr:297
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:300
    ctx:command("current_group", "= Group2") -- MM_THJORGARDCITY.scr:301
    ctx:command("goto_location", "= Misc") -- MM_THJORGARDCITY.scr:302
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:303
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:305
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_THJORGARDCITY.scr:308
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:311
    ctx:command("current_group", "= Group3") -- MM_THJORGARDCITY.scr:312
    ctx:command("goto_location", "= Work") -- MM_THJORGARDCITY.scr:313
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:314
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:316
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_THJORGARDCITY.scr:319
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:322
    ctx:command("current_group", "= Group3") -- MM_THJORGARDCITY.scr:323
    ctx:command("goto_location", "= Work") -- MM_THJORGARDCITY.scr:324
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:325
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:327
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_THJORGARDCITY.scr:330
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:333
    ctx:command("current_group", "= Group3") -- MM_THJORGARDCITY.scr:334
    ctx:command("goto_location", "= Home") -- MM_THJORGARDCITY.scr:335
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:336
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:338
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_THJORGARDCITY.scr:341
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:344
    ctx:command("current_group", "= Group3") -- MM_THJORGARDCITY.scr:345
    ctx:command("goto_location", "= Home") -- MM_THJORGARDCITY.scr:346
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:347
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:349
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_THJORGARDCITY.scr:352
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:355
    ctx:command("current_group", "= Group3") -- MM_THJORGARDCITY.scr:356
    ctx:command("goto_location", "= Misc") -- MM_THJORGARDCITY.scr:357
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:358
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:360
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_THJORGARDCITY.scr:363
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:366
    ctx:command("current_group", "= Group3") -- MM_THJORGARDCITY.scr:367
    ctx:command("goto_location", "= Misc") -- MM_THJORGARDCITY.scr:368
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:369
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:371
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_THJORGARDCITY.scr:374
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:377
    ctx:command("current_group", "= Group4") -- MM_THJORGARDCITY.scr:378
    ctx:command("goto_location", "= Work") -- MM_THJORGARDCITY.scr:379
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:380
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:382
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_THJORGARDCITY.scr:385
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:388
    ctx:command("current_group", "= Group4") -- MM_THJORGARDCITY.scr:389
    ctx:command("goto_location", "= Work") -- MM_THJORGARDCITY.scr:390
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:391
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:393
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_THJORGARDCITY.scr:397
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:400
    ctx:command("current_group", "= Group4") -- MM_THJORGARDCITY.scr:401
    ctx:command("goto_location", "= Home") -- MM_THJORGARDCITY.scr:402
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:403
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:405
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_THJORGARDCITY.scr:408
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:411
    ctx:command("current_group", "= Group4") -- MM_THJORGARDCITY.scr:412
    ctx:command("goto_location", "= Home") -- MM_THJORGARDCITY.scr:413
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:414
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:416
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_THJORGARDCITY.scr:419
    mm9.gosub(script, ctx, "WarpOff") -- MM_THJORGARDCITY.scr:422
    ctx:command("current_group", "= Group4") -- MM_THJORGARDCITY.scr:423
    ctx:command("goto_location", "= Misc") -- MM_THJORGARDCITY.scr:424
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:425
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:427
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_THJORGARDCITY.scr:430
    mm9.gosub(script, ctx, "WarpOn") -- MM_THJORGARDCITY.scr:433
    ctx:command("current_group", "= Group4") -- MM_THJORGARDCITY.scr:434
    ctx:command("goto_location", "= Misc") -- MM_THJORGARDCITY.scr:435
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THJORGARDCITY.scr:436
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:438
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_THJORGARDCITY.scr:446
    ctx:command("@m", "6 : 15 Group1_GoWork Group1_WarpWork") -- MM_THJORGARDCITY.scr:449
    ctx:command("@m", "6 : 30 Group2_GoWork Group2_WarpWork") -- MM_THJORGARDCITY.scr:450
    ctx:command("@m", "6 : 45 Group3_GoWork Group3_WarpWork") -- MM_THJORGARDCITY.scr:451
    ctx:command("@m", "7 : 00 Group4_GoWork Group4_WarpWork") -- MM_THJORGARDCITY.scr:452
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:454
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_THJORGARDCITY.scr:458
    ctx:command("@m", "18 : 00 Group1_GoHome Group1_WarpHome") -- MM_THJORGARDCITY.scr:461
    ctx:command("@m", "18 : 15 Group2_GoHome Group2_WarpHome") -- MM_THJORGARDCITY.scr:462
    ctx:command("@m", "18 : 30 Group3_GoHome Group3_WarpHome") -- MM_THJORGARDCITY.scr:463
    ctx:command("@m", "18 : 45 Group4_GoHome Group4_WarpHome") -- MM_THJORGARDCITY.scr:464
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:466
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_THJORGARDCITY.scr:469
    -- Go Wander off to somewhere
    ctx:command("@m", "13 : 00 Group1_GoMisc Group1_WarpMisc") -- MM_THJORGARDCITY.scr:473
    ctx:command("@m", "13 : 15 Group2_GoMisc Group2_WarpMisc") -- MM_THJORGARDCITY.scr:474
    ctx:command("@m", "13 : 30 Group3_GoMisc Group3_WarpMisc") -- MM_THJORGARDCITY.scr:475
    ctx:command("@m", "13 : 45 Group4_GoMisc Group4_WarpMisc") -- MM_THJORGARDCITY.scr:476
    -- Go Back to work
    ctx:command("@m", "15 : 00 Group1_GoWork Group1_WarpWork") -- MM_THJORGARDCITY.scr:479
    ctx:command("@m", "15 : 15 Group2_GoWork Group2_WarpWork") -- MM_THJORGARDCITY.scr:480
    ctx:command("@m", "15 : 30 Group3_GoWork Group3_WarpWork") -- MM_THJORGARDCITY.scr:481
    ctx:command("@m", "15 : 45 Group4_GoWork Group4_WarpWork") -- MM_THJORGARDCITY.scr:482
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:484
end

script.labels["InitArrays"] = function(ctx)
    -- MM_THJORGARDCITY.scr:492
    ctx:command("index", "= 0") -- MM_THJORGARDCITY.scr:495
    while ctx:condition("index < 10") do -- MM_THJORGARDCITY.scr:496
        ctx:command("arrayput", "aGroup1, index , 0") -- MM_THJORGARDCITY.scr:497
        ctx:command("arrayput", "aGroup2, index , 0") -- MM_THJORGARDCITY.scr:498
        ctx:command("arrayput", "aGroup3, index , 0") -- MM_THJORGARDCITY.scr:499
        ctx:command("arrayput", "aGroup4, index , 0") -- MM_THJORGARDCITY.scr:500
        ctx:command("index", "= index + 1") -- MM_THJORGARDCITY.scr:501
    end -- MM_THJORGARDCITY.scr:502
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:504
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_THJORGARDCITY.scr:508
    -- Gunnar Thorlakssen			( 22 )
    ctx:command("arrayput", "aGroup1,0,22") -- MM_THJORGARDCITY.scr:512
    -- Bodil the Brawny			( 31 )
    ctx:command("arrayput", "aGroup1,1,31") -- MM_THJORGARDCITY.scr:515
    -- Britta Stonewasher			( 35 )
    ctx:command("arrayput", "aGroup1,2,35") -- MM_THJORGARDCITY.scr:518
    -- Eilinoir A'Mor				( 310 )
    ctx:command("arrayput", "aGroup1,3,310") -- MM_THJORGARDCITY.scr:521
    -- Toman Yatol					( 38 )
    ctx:command("arrayput", "aGroup1,4,38") -- MM_THJORGARDCITY.scr:524
    -- Gjerta Headstrong			( 37 )
    ctx:command("arrayput", "aGroup1,5,37") -- MM_THJORGARDCITY.scr:527
    -- Chera Papan					( 39 )
    ctx:command("arrayput", "aGroup1,6,39") -- MM_THJORGARDCITY.scr:530
    -- Hildigunna the Quick		( 388 )
    ctx:command("arrayput", "aGroup1,7,388") -- MM_THJORGARDCITY.scr:533
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:535
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_THJORGARDCITY.scr:538
    -- Donnachac A'Washadi			( 23 )
    ctx:command("arrayput", "aGroup2,0,23") -- MM_THJORGARDCITY.scr:542
    -- Frode Fafnirssen			( 32 )
    ctx:command("arrayput", "aGroup2,1,32") -- MM_THJORGARDCITY.scr:545
    -- Einar Thorfinssen			( 36 )
    ctx:command("arrayput", "aGroup2,2,36") -- MM_THJORGARDCITY.scr:548
    -- Bysen A'Klindor				( 40 )
    ctx:command("arrayput", "aGroup2,3,40") -- MM_THJORGARDCITY.scr:551
    -- Giorsal A'Velsi				( 321 )
    ctx:command("arrayput", "aGroup2,4,321") -- MM_THJORGARDCITY.scr:554
    -- Hrrapp Spearhands			( 361 )
    ctx:command("arrayput", "aGroup2,5,361") -- MM_THJORGARDCITY.scr:557
    -- Sigre Bjarnidotir			( 385 )
    ctx:command("arrayput", "aGroup2,6,385") -- MM_THJORGARDCITY.scr:560
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:562
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_THJORGARDCITY.scr:565
    -- Raghnailt A'Ghrie			( 24 )
    ctx:command("arrayput", "aGroup3,0,24") -- MM_THJORGARDCITY.scr:569
    -- Annelise Baldundotir		( 33 )
    ctx:command("arrayput", "aGroup3,1,33") -- MM_THJORGARDCITY.scr:572
    -- Barabell A'Dorad			( 267 )
    ctx:command("arrayput", "aGroup3,2,267") -- MM_THJORGARDCITY.scr:575
    -- Darby Davinssen				( 311 )
    ctx:command("arrayput", "aGroup3,3,311") -- MM_THJORGARDCITY.scr:578
    -- Comhgan A'Dorad				( 41 )
    ctx:command("arrayput", "aGroup3,4,41") -- MM_THJORGARDCITY.scr:581
    -- Muadhnait A'Tryht			( 362 )
    ctx:command("arrayput", "aGroup3,5,362") -- MM_THJORGARDCITY.scr:584
    -- Fjarkskafinn the Still-alive	( 386 )
    ctx:command("arrayput", "aGroup3,6,386") -- MM_THJORGARDCITY.scr:587
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:589
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_THJORGARDCITY.scr:592
    -- Fiachu A'Dlinn				( 25 )
    ctx:command("arrayput", "aGroup4,0,25") -- MM_THJORGARDCITY.scr:596
    -- Karl Knutssen				( 34 )
    ctx:command("arrayput", "aGroup4,1,34") -- MM_THJORGARDCITY.scr:599
    -- Cator Fiskdal				( 295 )
    ctx:command("arrayput", "aGroup4,2,295") -- MM_THJORGARDCITY.scr:602
    -- Tove Halvardotir			( 320 )
    ctx:command("arrayput", "aGroup4,3,320") -- MM_THJORGARDCITY.scr:605
    -- Cinnfhail A'Mor				( 347 )
    ctx:command("arrayput", "aGroup4,4,347") -- MM_THJORGARDCITY.scr:608
    -- Thorfinn Quickeye			( 384 )
    ctx:command("arrayput", "aGroup4,5,384") -- MM_THJORGARDCITY.scr:611
    -- Halfdan the Hidden			( 387 )
    ctx:command("arrayput", "aGroup4,6,387") -- MM_THJORGARDCITY.scr:614
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:616
end

script.labels["Init"] = function(ctx)
    -- MM_THJORGARDCITY.scr:619
    mm9.gosub(script, ctx, "InitArrays") -- MM_THJORGARDCITY.scr:621
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_THJORGARDCITY.scr:623
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_THJORGARDCITY.scr:624
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_THJORGARDCITY.scr:625
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_THJORGARDCITY.scr:626
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_THJORGARDCITY.scr:628
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_THJORGARDCITY.scr:629
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_THJORGARDCITY.scr:630
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:632
end

script.labels["Main"] = function(ctx)
    -- MM_THJORGARDCITY.scr:635
    mm9.gosub(script, ctx, "Init") -- MM_THJORGARDCITY.scr:637
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_THJORGARDCITY.scr:638
    do return ctx:exit("") end -- MM_THJORGARDCITY.scr:640
end

return script
