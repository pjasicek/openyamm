-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_STURMFORDCITY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 39, path = "Globals.inc" }

-- MM_SturmfordCity.scr
-- Jim Craig
-- Mundane Task List for Sturmford City
-- Current NPCs
-- Gossip NPCs
-- Gormla A'Feslo				( 68 )
-- Annabel A'Lyrae				( 69 )
-- Eimhir A'Mor				( 70 )
-- Cinaed A'Velsi				( 71 )
-- Thorfinn Tjorvissen			( 72 )
-- Ambient NPCs
-- Yoltzin Oord				( 73 ) <<< REMOVED >>>
-- Cetzpal Oord				( 74 ) <<< REMOVED >>>
-- Mazat Oord					( 75 ) <<< REMOVED >>>
-- Halfdan Doorsbane			( 76 )
-- Fearghus A'Feslo			( 81 )
-- Tynan A'Lyrae				( 82 )
-- Tearlach A'Lyrae			( 83 )
-- Teacher NPCs
-- Katrina Vianni				( 80 )
-- Hafgrim Shorthands			( 78 )
-- Mirjam Thjordotir			( 77 )
-- Lili A'Ghrie				( 84 )
-- Eskil Tryygvassen			( 389 )
-- Adotette Haji				( 390 )
-- Hildr Fjalldotir			( 391 )
-- Devlin A'Norta a'meich		( 392 )
-- Olrun Fjalldotir			( 393 )
-- Leppa the Shy				( 79 )
script.labels["OnArrived"] = function(ctx)
    -- MM_STURMFORDCITY.scr:70
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:73
end

script.labels["WarpOn"] = function(ctx)
    -- MM_STURMFORDCITY.scr:76
    ctx:state().bWarp = true -- MM_STURMFORDCITY.scr:79
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:81
end

script.labels["WarpOff"] = function(ctx)
    -- MM_STURMFORDCITY.scr:84
    ctx:state().bWarp = false -- MM_STURMFORDCITY.scr:87
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:89
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_STURMFORDCITY.scr:92
    if ctx:condition("goto_location == Work") then -- MM_STURMFORDCITY.scr:95
        ctx:set("goto_marker", "marker_work + npc_id") -- MM_STURMFORDCITY.scr:96
    end -- MM_STURMFORDCITY.scr:97
    if ctx:condition("goto_location == Home") then -- MM_STURMFORDCITY.scr:99
        ctx:set("goto_marker", "marker_home + npc_id") -- MM_STURMFORDCITY.scr:100
    end -- MM_STURMFORDCITY.scr:101
    if ctx:condition("goto_location == Misc") then -- MM_STURMFORDCITY.scr:103
        ctx:set("goto_marker", "marker_misc + npc_id") -- MM_STURMFORDCITY.scr:104
    end -- MM_STURMFORDCITY.scr:105
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:107
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_STURMFORDCITY.scr:110
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_STURMFORDCITY.scr:113
    ctx:object("npc_object"):setStat("PARAM", "goto_marker") -- MM_STURMFORDCITY.scr:115
    if ctx:condition("bWarp == FALSE") then -- MM_STURMFORDCITY.scr:117
        ctx:trigger("npc_object", "GoToLoc") -- MM_STURMFORDCITY.scr:118
    end -- MM_STURMFORDCITY.scr:119
    if ctx:condition("bWarp == TRUE") then -- MM_STURMFORDCITY.scr:121
        ctx:trigger("npc_object", "WarpToLoc") -- MM_STURMFORDCITY.scr:122
    end -- MM_STURMFORDCITY.scr:123
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:125
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_STURMFORDCITY.scr:128
    ctx:state().index = 0 -- MM_STURMFORDCITY.scr:131
    while ctx:condition("index < 10") do -- MM_STURMFORDCITY.scr:133
        ctx:state().npc_id = 0 -- MM_STURMFORDCITY.scr:135
        if ctx:condition("current_group == Group1") then -- MM_STURMFORDCITY.scr:137
            ctx:arrayGet("aGroup1", "index", "npc_id") -- MM_STURMFORDCITY.scr:138
        end -- MM_STURMFORDCITY.scr:139
        if ctx:condition("current_group == Group2") then -- MM_STURMFORDCITY.scr:141
            ctx:arrayGet("aGroup2", "index", "npc_id") -- MM_STURMFORDCITY.scr:142
        end -- MM_STURMFORDCITY.scr:143
        if ctx:condition("current_group == Group3") then -- MM_STURMFORDCITY.scr:145
            ctx:arrayGet("aGroup3", "index", "npc_id") -- MM_STURMFORDCITY.scr:146
        end -- MM_STURMFORDCITY.scr:147
        if ctx:condition("current_group == Group4") then -- MM_STURMFORDCITY.scr:149
            ctx:arrayGet("aGroup4", "index", "npc_id") -- MM_STURMFORDCITY.scr:150
        end -- MM_STURMFORDCITY.scr:151
        if ctx:condition("npc_id != 0") then -- MM_STURMFORDCITY.scr:153
            mm9.gosub(script, ctx, "CreateMarker") -- MM_STURMFORDCITY.scr:154
            mm9.gosub(script, ctx, "GoToLocation") -- MM_STURMFORDCITY.scr:155
        end -- MM_STURMFORDCITY.scr:156
        ctx:set("index", "index + 1") -- MM_STURMFORDCITY.scr:158
    end -- MM_STURMFORDCITY.scr:159
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:161
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_STURMFORDCITY.scr:168
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:171
    ctx:set("current_group", "Group1") -- MM_STURMFORDCITY.scr:172
    ctx:set("goto_location", "Work") -- MM_STURMFORDCITY.scr:173
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:174
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:176
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_STURMFORDCITY.scr:179
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:182
    ctx:set("current_group", "Group1") -- MM_STURMFORDCITY.scr:183
    ctx:set("goto_location", "Work") -- MM_STURMFORDCITY.scr:184
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:185
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:187
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_STURMFORDCITY.scr:190
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:193
    ctx:set("current_group", "Group1") -- MM_STURMFORDCITY.scr:194
    ctx:set("goto_location", "Home") -- MM_STURMFORDCITY.scr:195
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:196
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:198
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_STURMFORDCITY.scr:201
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:204
    ctx:set("current_group", "Group1") -- MM_STURMFORDCITY.scr:205
    ctx:set("goto_location", "Home") -- MM_STURMFORDCITY.scr:206
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:207
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:209
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_STURMFORDCITY.scr:212
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:215
    ctx:set("current_group", "Group1") -- MM_STURMFORDCITY.scr:216
    ctx:set("goto_location", "Misc") -- MM_STURMFORDCITY.scr:217
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:218
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:220
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_STURMFORDCITY.scr:223
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:226
    ctx:set("current_group", "Group1") -- MM_STURMFORDCITY.scr:227
    ctx:set("goto_location", "Misc") -- MM_STURMFORDCITY.scr:228
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:229
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:231
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_STURMFORDCITY.scr:235
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:238
    ctx:set("current_group", "Group2") -- MM_STURMFORDCITY.scr:239
    ctx:set("goto_location", "Work") -- MM_STURMFORDCITY.scr:240
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:241
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:243
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_STURMFORDCITY.scr:246
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:249
    ctx:set("current_group", "Group2") -- MM_STURMFORDCITY.scr:250
    ctx:set("goto_location", "Work") -- MM_STURMFORDCITY.scr:251
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:252
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:254
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_STURMFORDCITY.scr:257
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:260
    ctx:set("current_group", "Group2") -- MM_STURMFORDCITY.scr:261
    ctx:set("goto_location", "Home") -- MM_STURMFORDCITY.scr:262
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:263
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:265
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_STURMFORDCITY.scr:268
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:271
    ctx:set("current_group", "Group2") -- MM_STURMFORDCITY.scr:272
    ctx:set("goto_location", "Home") -- MM_STURMFORDCITY.scr:273
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:274
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:276
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_STURMFORDCITY.scr:279
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:282
    ctx:set("current_group", "Group2") -- MM_STURMFORDCITY.scr:283
    ctx:set("goto_location", "Misc") -- MM_STURMFORDCITY.scr:284
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:285
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:287
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_STURMFORDCITY.scr:290
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:293
    ctx:set("current_group", "Group2") -- MM_STURMFORDCITY.scr:294
    ctx:set("goto_location", "Misc") -- MM_STURMFORDCITY.scr:295
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:296
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:298
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_STURMFORDCITY.scr:301
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:304
    ctx:set("current_group", "Group3") -- MM_STURMFORDCITY.scr:305
    ctx:set("goto_location", "Work") -- MM_STURMFORDCITY.scr:306
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:307
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:309
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_STURMFORDCITY.scr:312
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:315
    ctx:set("current_group", "Group3") -- MM_STURMFORDCITY.scr:316
    ctx:set("goto_location", "Work") -- MM_STURMFORDCITY.scr:317
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:318
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:320
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_STURMFORDCITY.scr:323
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:326
    ctx:set("current_group", "Group3") -- MM_STURMFORDCITY.scr:327
    ctx:set("goto_location", "Home") -- MM_STURMFORDCITY.scr:328
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:329
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:331
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_STURMFORDCITY.scr:334
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:337
    ctx:set("current_group", "Group3") -- MM_STURMFORDCITY.scr:338
    ctx:set("goto_location", "Home") -- MM_STURMFORDCITY.scr:339
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:340
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:342
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_STURMFORDCITY.scr:345
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:348
    ctx:set("current_group", "Group3") -- MM_STURMFORDCITY.scr:349
    ctx:set("goto_location", "Misc") -- MM_STURMFORDCITY.scr:350
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:351
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:353
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_STURMFORDCITY.scr:356
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:359
    ctx:set("current_group", "Group3") -- MM_STURMFORDCITY.scr:360
    ctx:set("goto_location", "Misc") -- MM_STURMFORDCITY.scr:361
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:362
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:364
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_STURMFORDCITY.scr:367
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:370
    ctx:set("current_group", "Group4") -- MM_STURMFORDCITY.scr:371
    ctx:set("goto_location", "Work") -- MM_STURMFORDCITY.scr:372
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:373
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:375
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_STURMFORDCITY.scr:378
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:381
    ctx:set("current_group", "Group4") -- MM_STURMFORDCITY.scr:382
    ctx:set("goto_location", "Work") -- MM_STURMFORDCITY.scr:383
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:384
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:386
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_STURMFORDCITY.scr:390
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:393
    ctx:set("current_group", "Group4") -- MM_STURMFORDCITY.scr:394
    ctx:set("goto_location", "Home") -- MM_STURMFORDCITY.scr:395
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:396
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:398
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_STURMFORDCITY.scr:401
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:404
    ctx:set("current_group", "Group4") -- MM_STURMFORDCITY.scr:405
    ctx:set("goto_location", "Home") -- MM_STURMFORDCITY.scr:406
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:407
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:409
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_STURMFORDCITY.scr:412
    mm9.gosub(script, ctx, "WarpOff") -- MM_STURMFORDCITY.scr:415
    ctx:set("current_group", "Group4") -- MM_STURMFORDCITY.scr:416
    ctx:set("goto_location", "Misc") -- MM_STURMFORDCITY.scr:417
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:418
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:420
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_STURMFORDCITY.scr:423
    mm9.gosub(script, ctx, "WarpOn") -- MM_STURMFORDCITY.scr:426
    ctx:set("current_group", "Group4") -- MM_STURMFORDCITY.scr:427
    ctx:set("goto_location", "Misc") -- MM_STURMFORDCITY.scr:428
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_STURMFORDCITY.scr:429
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:431
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_STURMFORDCITY.scr:439
    ctx:atTime(6, 15, "Group1_GoWork", "Group1_WarpWork") -- MM_STURMFORDCITY.scr:442
    ctx:atTime(6, 30, "Group2_GoWork", "Group2_WarpWork") -- MM_STURMFORDCITY.scr:443
    ctx:atTime(6, 45, "Group3_GoWork", "Group3_WarpWork") -- MM_STURMFORDCITY.scr:444
    ctx:atTime(7, 0, "Group4_GoWork", "Group4_WarpWork") -- MM_STURMFORDCITY.scr:445
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:447
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_STURMFORDCITY.scr:451
    ctx:atTime(18, 0, "Group1_GoHome", "Group1_WarpHome") -- MM_STURMFORDCITY.scr:454
    ctx:atTime(18, 15, "Group2_GoHome", "Group2_WarpHome") -- MM_STURMFORDCITY.scr:455
    ctx:atTime(18, 30, "Group3_GoHome", "Group3_WarpHome") -- MM_STURMFORDCITY.scr:456
    ctx:atTime(18, 45, "Group4_GoHome", "Group4_WarpHome") -- MM_STURMFORDCITY.scr:457
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:459
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_STURMFORDCITY.scr:462
    -- Go Wander off to somewhere
    ctx:atTime(13, 0, "Group1_GoMisc", "Group1_WarpMisc") -- MM_STURMFORDCITY.scr:466
    ctx:atTime(13, 15, "Group2_GoMisc", "Group2_WarpMisc") -- MM_STURMFORDCITY.scr:467
    ctx:atTime(13, 30, "Group3_GoMisc", "Group3_WarpMisc") -- MM_STURMFORDCITY.scr:468
    ctx:atTime(13, 45, "Group4_GoMisc", "Group4_WarpMisc") -- MM_STURMFORDCITY.scr:469
    -- Go Back to work
    ctx:atTime(15, 0, "Group1_GoWork", "Group1_WarpWork") -- MM_STURMFORDCITY.scr:472
    ctx:atTime(15, 15, "Group2_GoWork", "Group2_WarpWork") -- MM_STURMFORDCITY.scr:473
    ctx:atTime(15, 30, "Group3_GoWork", "Group3_WarpWork") -- MM_STURMFORDCITY.scr:474
    ctx:atTime(15, 45, "Group4_GoWork", "Group4_WarpWork") -- MM_STURMFORDCITY.scr:475
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:477
end

script.labels["InitArrays"] = function(ctx)
    -- MM_STURMFORDCITY.scr:485
    ctx:state().index = 0 -- MM_STURMFORDCITY.scr:488
    while ctx:condition("index < 10") do -- MM_STURMFORDCITY.scr:489
        ctx:arrayPut("aGroup1", "index", 0) -- MM_STURMFORDCITY.scr:490
        ctx:arrayPut("aGroup2", "index", 0) -- MM_STURMFORDCITY.scr:491
        ctx:arrayPut("aGroup3", "index", 0) -- MM_STURMFORDCITY.scr:492
        ctx:arrayPut("aGroup4", "index", 0) -- MM_STURMFORDCITY.scr:493
        ctx:set("index", "index + 1") -- MM_STURMFORDCITY.scr:494
    end -- MM_STURMFORDCITY.scr:495
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:497
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_STURMFORDCITY.scr:501
    -- Gormla A'Feslo				( 68 )
    ctx:arrayPut("aGroup1", 0, 68) -- MM_STURMFORDCITY.scr:505
    -- Thorfinn Tjorvissen			( 72 )
    ctx:arrayPut("aGroup1", 1, 72) -- MM_STURMFORDCITY.scr:508
    -- Katrina Vianni				( 80 )
    ctx:arrayPut("aGroup1", 2, 80) -- MM_STURMFORDCITY.scr:511
    -- Eskil Tryygvassen			( 389 )
    ctx:arrayPut("aGroup1", 3, 389) -- MM_STURMFORDCITY.scr:514
    -- Olrun Fjalldotir			( 393 )
    ctx:arrayPut("aGroup1", 4, 393) -- MM_STURMFORDCITY.scr:517
    -- Yoltzin Oord				( 73 ) <<< REMOVED >>>
    -- ArrayPut aGroup1,5,73
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:523
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_STURMFORDCITY.scr:526
    -- Annabel A'Lyrae				( 69 )
    ctx:arrayPut("aGroup2", 0, 69) -- MM_STURMFORDCITY.scr:530
    -- Fearghus A'Feslo			( 81 )
    ctx:arrayPut("aGroup2", 1, 81) -- MM_STURMFORDCITY.scr:533
    -- Hafgrim Shorthands			( 78 )
    ctx:arrayPut("aGroup2", 2, 78) -- MM_STURMFORDCITY.scr:536
    -- Adotette Haji				( 390 )
    ctx:arrayPut("aGroup2", 3, 390) -- MM_STURMFORDCITY.scr:539
    -- Leppa the Shy				( 79 )
    ctx:arrayPut("aGroup2", 4, 79) -- MM_STURMFORDCITY.scr:542
    -- Yoltzin Oord				( 73 ) <<< REMOVED >>>
    -- ArrayPut aGroup1,5,73
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:548
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_STURMFORDCITY.scr:551
    -- Eimhir A'Mor				( 70 )
    ctx:arrayPut("aGroup3", 0, 70) -- MM_STURMFORDCITY.scr:555
    -- Tynan A'Lyrae				( 82 )
    ctx:arrayPut("aGroup3", 1, 82) -- MM_STURMFORDCITY.scr:558
    -- Mirjam Thjordotir			( 77 )
    ctx:arrayPut("aGroup3", 2, 77) -- MM_STURMFORDCITY.scr:561
    -- Hildr Fjalldotir			( 391 )
    ctx:arrayPut("aGroup3", 3, 391) -- MM_STURMFORDCITY.scr:564
    -- Mazat Oord					( 75 ) <<< REMOVED >>>
    -- ArrayPut aGroup3,4,75
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:569
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_STURMFORDCITY.scr:572
    -- Cinaed A'Velsi				( 71 )
    ctx:arrayPut("aGroup4", 0, 71) -- MM_STURMFORDCITY.scr:576
    -- Halfdan Doorsbane			( 76 )
    ctx:arrayPut("aGroup4", 1, 76) -- MM_STURMFORDCITY.scr:579
    -- Tearlach A'Lyrae			( 83 )
    ctx:arrayPut("aGroup4", 2, 83) -- MM_STURMFORDCITY.scr:582
    -- Lili A'Ghrie				( 84 )
    ctx:arrayPut("aGroup4", 3, 84) -- MM_STURMFORDCITY.scr:585
    -- Devlin A'Norta a'meich		( 392 )
    ctx:arrayPut("aGroup4", 4, 392) -- MM_STURMFORDCITY.scr:588
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:590
end

script.labels["Init"] = function(ctx)
    -- MM_STURMFORDCITY.scr:593
    mm9.gosub(script, ctx, "InitArrays") -- MM_STURMFORDCITY.scr:595
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_STURMFORDCITY.scr:597
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_STURMFORDCITY.scr:598
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_STURMFORDCITY.scr:599
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_STURMFORDCITY.scr:600
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_STURMFORDCITY.scr:602
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_STURMFORDCITY.scr:603
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_STURMFORDCITY.scr:604
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:606
end

script.labels["Main"] = function(ctx)
    -- MM_STURMFORDCITY.scr:609
    mm9.gosub(script, ctx, "Init") -- MM_STURMFORDCITY.scr:611
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_STURMFORDCITY.scr:612
    do return ctx:exit("") end -- MM_STURMFORDCITY.scr:614
end

return script
