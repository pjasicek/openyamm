-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_ARSLEGARDCITY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 38, path = "Globals.inc" }

-- MM_ArslegardCity.scr
-- Jim Craig
-- Mundane Task List for Arslegard City
-- Current NPCs :
-- Gossip NPCs
-- Eirik Thorvaldssen	( 352 )
-- Falki Bergfinnssen  ( 353 )
-- Beowulf Ingssen		( 354 )
-- Gote Tjorvidotir	( 355 )
-- Rurik Moyol			( 358 ) <<< REMOVED >>>
-- Onund Thordssen		( 359 ) <<< REMOVED >>>
-- Kolskegg Skulissen	( 360 )
-- Ambient NPCs
-- Gymir Afissen		( 363 )
-- Aso Darbyssen		( 364 )
-- Dain Kolskeggssen	( 365 )
-- Dagny Daindotir		( 366 )
-- Osk Thorgrimdotir	( 367 )
-- Tepil Ahura			( 368 )
-- Val Tonlan			( 369 )
-- Ateed Haji			( 370 )
-- Sechnassach A'Washadi	( 371 )
-- Angus A'Mor				( 372 )
-- Orabilia A'Dlinn		( 373 )
-- Eilinoir A'Endlar		( 374 )
-- Bjarni Eirikssen		( 375 )
-- Unn Canutedotir			( 376 )
-- Phili, The Great Honk	( 377 ) <<< REMOVED >>>
script.labels["OnArrived"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:69
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:72
end

script.labels["WarpOn"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:75
    ctx:command("bwarp", "= TRUE") -- MM_ARSLEGARDCITY.scr:78
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:80
end

script.labels["WarpOff"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:83
    ctx:command("bwarp", "= FALSE") -- MM_ARSLEGARDCITY.scr:86
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:88
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:91
    if ctx:condition("goto_location == Work") then -- MM_ARSLEGARDCITY.scr:94
        ctx:command("goto_marker", "= marker_work + npc_id") -- MM_ARSLEGARDCITY.scr:95
    end -- MM_ARSLEGARDCITY.scr:96
    if ctx:condition("goto_location == Home") then -- MM_ARSLEGARDCITY.scr:98
        ctx:command("goto_marker", "= marker_home + npc_id") -- MM_ARSLEGARDCITY.scr:99
    end -- MM_ARSLEGARDCITY.scr:100
    if ctx:condition("goto_location == Misc") then -- MM_ARSLEGARDCITY.scr:102
        ctx:command("goto_marker", "= marker_misc + npc_id") -- MM_ARSLEGARDCITY.scr:103
    end -- MM_ARSLEGARDCITY.scr:104
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:106
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:109
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_ARSLEGARDCITY.scr:112
    ctx:command("setstat", "npc_object, PARAM, goto_marker") -- MM_ARSLEGARDCITY.scr:114
    if ctx:condition("bWarp == FALSE") then -- MM_ARSLEGARDCITY.scr:116
        ctx:trigger("npc_object", "GoToLoc") -- MM_ARSLEGARDCITY.scr:117
    end -- MM_ARSLEGARDCITY.scr:118
    if ctx:condition("bWarp == TRUE") then -- MM_ARSLEGARDCITY.scr:120
        ctx:trigger("npc_object", "WarpToLoc") -- MM_ARSLEGARDCITY.scr:121
    end -- MM_ARSLEGARDCITY.scr:122
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:124
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:127
    ctx:command("index", "= 0") -- MM_ARSLEGARDCITY.scr:130
    while ctx:condition("index < 10") do -- MM_ARSLEGARDCITY.scr:132
        ctx:command("npc_id", "= 0") -- MM_ARSLEGARDCITY.scr:134
        if ctx:condition("current_group == Group1") then -- MM_ARSLEGARDCITY.scr:136
            ctx:command("arrayget", "aGroup1,index,npc_id") -- MM_ARSLEGARDCITY.scr:137
        end -- MM_ARSLEGARDCITY.scr:138
        if ctx:condition("current_group == Group2") then -- MM_ARSLEGARDCITY.scr:140
            ctx:command("arrayget", "aGroup2,index,npc_id") -- MM_ARSLEGARDCITY.scr:141
        end -- MM_ARSLEGARDCITY.scr:142
        if ctx:condition("current_group == Group3") then -- MM_ARSLEGARDCITY.scr:144
            ctx:command("arrayget", "aGroup3,index,npc_id") -- MM_ARSLEGARDCITY.scr:145
        end -- MM_ARSLEGARDCITY.scr:146
        if ctx:condition("current_group == Group4") then -- MM_ARSLEGARDCITY.scr:148
            ctx:command("arrayget", "aGroup4,index,npc_id") -- MM_ARSLEGARDCITY.scr:149
        end -- MM_ARSLEGARDCITY.scr:150
        if ctx:condition("npc_id != 0") then -- MM_ARSLEGARDCITY.scr:152
            mm9.gosub(script, ctx, "CreateMarker") -- MM_ARSLEGARDCITY.scr:153
            mm9.gosub(script, ctx, "GoToLocation") -- MM_ARSLEGARDCITY.scr:154
        end -- MM_ARSLEGARDCITY.scr:155
        ctx:command("index", "= index + 1") -- MM_ARSLEGARDCITY.scr:157
    end -- MM_ARSLEGARDCITY.scr:158
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:160
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:167
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:170
    ctx:command("current_group", "= Group1") -- MM_ARSLEGARDCITY.scr:171
    ctx:command("goto_location", "= Work") -- MM_ARSLEGARDCITY.scr:172
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:173
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:175
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:178
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:181
    ctx:command("current_group", "= Group1") -- MM_ARSLEGARDCITY.scr:182
    ctx:command("goto_location", "= Work") -- MM_ARSLEGARDCITY.scr:183
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:184
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:186
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:189
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:192
    ctx:command("current_group", "= Group1") -- MM_ARSLEGARDCITY.scr:193
    ctx:command("goto_location", "= Home") -- MM_ARSLEGARDCITY.scr:194
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:195
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:197
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:200
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:203
    ctx:command("current_group", "= Group1") -- MM_ARSLEGARDCITY.scr:204
    ctx:command("goto_location", "= Home") -- MM_ARSLEGARDCITY.scr:205
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:206
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:208
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:211
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:214
    ctx:command("current_group", "= Group1") -- MM_ARSLEGARDCITY.scr:215
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGARDCITY.scr:216
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:217
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:219
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:222
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:225
    ctx:command("current_group", "= Group1") -- MM_ARSLEGARDCITY.scr:226
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGARDCITY.scr:227
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:228
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:230
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:234
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:237
    ctx:command("current_group", "= Group2") -- MM_ARSLEGARDCITY.scr:238
    ctx:command("goto_location", "= Work") -- MM_ARSLEGARDCITY.scr:239
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:240
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:242
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:245
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:248
    ctx:command("current_group", "= Group2") -- MM_ARSLEGARDCITY.scr:249
    ctx:command("goto_location", "= Work") -- MM_ARSLEGARDCITY.scr:250
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:251
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:253
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:256
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:259
    ctx:command("current_group", "= Group2") -- MM_ARSLEGARDCITY.scr:260
    ctx:command("goto_location", "= Home") -- MM_ARSLEGARDCITY.scr:261
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:262
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:264
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:267
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:270
    ctx:command("current_group", "= Group2") -- MM_ARSLEGARDCITY.scr:271
    ctx:command("goto_location", "= Home") -- MM_ARSLEGARDCITY.scr:272
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:273
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:275
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:278
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:281
    ctx:command("current_group", "= Group2") -- MM_ARSLEGARDCITY.scr:282
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGARDCITY.scr:283
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:284
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:286
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:289
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:292
    ctx:command("current_group", "= Group2") -- MM_ARSLEGARDCITY.scr:293
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGARDCITY.scr:294
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:295
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:297
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:300
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:303
    ctx:command("current_group", "= Group3") -- MM_ARSLEGARDCITY.scr:304
    ctx:command("goto_location", "= Work") -- MM_ARSLEGARDCITY.scr:305
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:306
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:308
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:311
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:314
    ctx:command("current_group", "= Group3") -- MM_ARSLEGARDCITY.scr:315
    ctx:command("goto_location", "= Work") -- MM_ARSLEGARDCITY.scr:316
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:317
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:319
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:322
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:325
    ctx:command("current_group", "= Group3") -- MM_ARSLEGARDCITY.scr:326
    ctx:command("goto_location", "= Home") -- MM_ARSLEGARDCITY.scr:327
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:328
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:330
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:333
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:336
    ctx:command("current_group", "= Group3") -- MM_ARSLEGARDCITY.scr:337
    ctx:command("goto_location", "= Home") -- MM_ARSLEGARDCITY.scr:338
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:339
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:341
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:344
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:347
    ctx:command("current_group", "= Group3") -- MM_ARSLEGARDCITY.scr:348
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGARDCITY.scr:349
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:350
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:352
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:355
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:358
    ctx:command("current_group", "= Group3") -- MM_ARSLEGARDCITY.scr:359
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGARDCITY.scr:360
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:361
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:363
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:366
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:369
    ctx:command("current_group", "= Group4") -- MM_ARSLEGARDCITY.scr:370
    ctx:command("goto_location", "= Work") -- MM_ARSLEGARDCITY.scr:371
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:372
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:374
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:377
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:380
    ctx:command("current_group", "= Group4") -- MM_ARSLEGARDCITY.scr:381
    ctx:command("goto_location", "= Work") -- MM_ARSLEGARDCITY.scr:382
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:383
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:385
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:389
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:392
    ctx:command("current_group", "= Group4") -- MM_ARSLEGARDCITY.scr:393
    ctx:command("goto_location", "= Home") -- MM_ARSLEGARDCITY.scr:394
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:395
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:397
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:400
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:403
    ctx:command("current_group", "= Group4") -- MM_ARSLEGARDCITY.scr:404
    ctx:command("goto_location", "= Home") -- MM_ARSLEGARDCITY.scr:405
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:406
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:408
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:411
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARDCITY.scr:414
    ctx:command("current_group", "= Group4") -- MM_ARSLEGARDCITY.scr:415
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGARDCITY.scr:416
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:417
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:419
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:422
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARDCITY.scr:425
    ctx:command("current_group", "= Group4") -- MM_ARSLEGARDCITY.scr:426
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGARDCITY.scr:427
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARDCITY.scr:428
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:430
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:438
    ctx:command("@m", "6 : 15 Group1_GoWork Group1_WarpWork") -- MM_ARSLEGARDCITY.scr:441
    ctx:command("@m", "6 : 30 Group2_GoWork Group2_WarpWork") -- MM_ARSLEGARDCITY.scr:442
    ctx:command("@m", "6 : 45 Group3_GoWork Group3_WarpWork") -- MM_ARSLEGARDCITY.scr:443
    ctx:command("@m", "7 : 00 Group4_GoWork Group4_WarpWork") -- MM_ARSLEGARDCITY.scr:444
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:446
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:450
    ctx:command("@m", "18 : 00 Group1_GoHome Group1_WarpHome") -- MM_ARSLEGARDCITY.scr:453
    ctx:command("@m", "18 : 15 Group2_GoHome Group2_WarpHome") -- MM_ARSLEGARDCITY.scr:454
    ctx:command("@m", "18 : 30 Group3_GoHome Group3_WarpHome") -- MM_ARSLEGARDCITY.scr:455
    ctx:command("@m", "18 : 45 Group4_GoHome Group4_WarpHome") -- MM_ARSLEGARDCITY.scr:456
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:458
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:461
    -- Go Wander off to somewhere
    ctx:command("@m", "13 : 00 Group1_GoMisc Group1_WarpMisc") -- MM_ARSLEGARDCITY.scr:465
    ctx:command("@m", "13 : 15 Group2_GoMisc Group2_WarpMisc") -- MM_ARSLEGARDCITY.scr:466
    ctx:command("@m", "13 : 30 Group3_GoMisc Group3_WarpMisc") -- MM_ARSLEGARDCITY.scr:467
    ctx:command("@m", "13 : 45 Group4_GoMisc Group4_WarpMisc") -- MM_ARSLEGARDCITY.scr:468
    -- Go Back to work
    ctx:command("@m", "15 : 00 Group1_GoWork Group1_WarpWork") -- MM_ARSLEGARDCITY.scr:471
    ctx:command("@m", "15 : 15 Group2_GoWork Group2_WarpWork") -- MM_ARSLEGARDCITY.scr:472
    ctx:command("@m", "15 : 30 Group3_GoWork Group3_WarpWork") -- MM_ARSLEGARDCITY.scr:473
    ctx:command("@m", "15 : 45 Group4_GoWork Group4_WarpWork") -- MM_ARSLEGARDCITY.scr:474
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:476
end

script.labels["InitArrays"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:484
    ctx:command("index", "= 0") -- MM_ARSLEGARDCITY.scr:487
    while ctx:condition("index < 10") do -- MM_ARSLEGARDCITY.scr:488
        ctx:command("arrayput", "aGroup1, index , 0") -- MM_ARSLEGARDCITY.scr:489
        ctx:command("arrayput", "aGroup2, index , 0") -- MM_ARSLEGARDCITY.scr:490
        ctx:command("arrayput", "aGroup3, index , 0") -- MM_ARSLEGARDCITY.scr:491
        ctx:command("arrayput", "aGroup4, index , 0") -- MM_ARSLEGARDCITY.scr:492
        ctx:command("index", "= index + 1") -- MM_ARSLEGARDCITY.scr:493
    end -- MM_ARSLEGARDCITY.scr:494
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:496
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:500
    -- Eirik Thorvaldssen	( 352 )
    ctx:command("arrayput", "aGroup1,0,352") -- MM_ARSLEGARDCITY.scr:504
    -- Aso Darbyssen		( 364 )
    ctx:command("arrayput", "aGroup1,1,364") -- MM_ARSLEGARDCITY.scr:507
    -- Val Tonlan			( 369 )
    ctx:command("arrayput", "aGroup1,2,369") -- MM_ARSLEGARDCITY.scr:510
    -- Orabilia A'Dlinn		( 373 )
    ctx:command("arrayput", "aGroup1,3,373") -- MM_ARSLEGARDCITY.scr:513
    -- Rurik Moyol			( 358 )	<<< REMOVED >>>
    -- ArrayPut aGroup1,4,358
    -- Phili, The Great Honk	( 377 ) <<< REMOVED >>>
    -- ArrayPut aGroup1,5,377
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:521
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:524
    -- Falki Bergfinnssen  ( 353 )
    ctx:command("arrayput", "aGroup2,0,353") -- MM_ARSLEGARDCITY.scr:528
    -- Dain Kolskeggssen	( 365 )
    ctx:command("arrayput", "aGroup2,1,365") -- MM_ARSLEGARDCITY.scr:531
    -- Ateed Haji			( 370 )
    ctx:command("arrayput", "aGroup2,2,370") -- MM_ARSLEGARDCITY.scr:534
    -- Eilinoir A'Endlar		( 374 )
    ctx:command("arrayput", "aGroup2,3,374") -- MM_ARSLEGARDCITY.scr:537
    -- Onund Thordssen		( 359 ) <<< REMOVED >>>
    -- ArrayPut aGroup2,4,359
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:542
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:545
    -- Beowulf Ingssen		( 354 )
    ctx:command("arrayput", "aGroup3,0,354") -- MM_ARSLEGARDCITY.scr:549
    -- Kolskegg Skulissen	( 360 )
    ctx:command("arrayput", "aGroup3,1,360") -- MM_ARSLEGARDCITY.scr:552
    -- Dagny Daindotir		( 366 )
    ctx:command("arrayput", "aGroup3,2,366") -- MM_ARSLEGARDCITY.scr:555
    -- Sechnassach A'Washadi	( 371 )
    ctx:command("arrayput", "aGroup3,3,371") -- MM_ARSLEGARDCITY.scr:558
    -- Bjarni Eirikssen		( 375 )
    ctx:command("arrayput", "aGroup3,4,375") -- MM_ARSLEGARDCITY.scr:561
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:563
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:566
    -- Gote Tjorvidotir	( 355 )
    ctx:command("arrayput", "aGroup4,0,355") -- MM_ARSLEGARDCITY.scr:570
    -- Gymir Afissen		( 363 )
    ctx:command("arrayput", "aGroup4,1,363") -- MM_ARSLEGARDCITY.scr:573
    -- Osk Thorgrimdotir	( 367 )
    ctx:command("arrayput", "aGroup4,2,367") -- MM_ARSLEGARDCITY.scr:576
    -- Tepil Ahura			( 368 )
    ctx:command("arrayput", "aGroup4,3,368") -- MM_ARSLEGARDCITY.scr:579
    -- Angus A'Mor				( 372 )
    ctx:command("arrayput", "aGroup4,4,372") -- MM_ARSLEGARDCITY.scr:582
    -- Unn Canutedotir			( 376 )
    ctx:command("arrayput", "aGroup4,5,376") -- MM_ARSLEGARDCITY.scr:585
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:588
end

script.labels["Init"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:591
    mm9.gosub(script, ctx, "InitArrays") -- MM_ARSLEGARDCITY.scr:593
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_ARSLEGARDCITY.scr:595
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_ARSLEGARDCITY.scr:596
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_ARSLEGARDCITY.scr:597
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_ARSLEGARDCITY.scr:598
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_ARSLEGARDCITY.scr:600
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_ARSLEGARDCITY.scr:601
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_ARSLEGARDCITY.scr:602
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:604
end

script.labels["Main"] = function(ctx)
    -- MM_ARSLEGARDCITY.scr:607
    mm9.gosub(script, ctx, "Init") -- MM_ARSLEGARDCITY.scr:609
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_ARSLEGARDCITY.scr:610
    do return ctx:exit("") end -- MM_ARSLEGARDCITY.scr:612
end

return script
