-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_THRONHEIM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 33, path = "Globals.inc" }

-- MM_Thronheim.scr
-- Jim Craig
-- Mundane Task List for Thronheim
-- Current NPCs
-- Gossip NPCs
-- Olaf Frodessen			( 262 )
-- Neda Haki				( 263 )
-- Caitir A'Feslo			( 264 )
-- Gudlaug Ragnarssen		( 265 )
-- Ambient NPCs
-- Allasan A'Washadi		( 268 )
-- Eimhir A'Mor			( 269 )
-- Fland A'Tryht			( 270 )
-- Muiredach A'Lanth		( 271 )
-- Comgghan A'Feslo		( 272 )
-- Dain Swordstrong		( 278 )
-- Yoltzin Tor				( 279 )
-- Ateed Bakari			( 280 )
-- Teacher NPCs
-- Bryan Hrutssen			( 273 )
-- Dagny Borkdotir			( 274 )
-- Ran Tryygvadotir		( 275 )
-- Fjall Bodilssen			( 276 )
-- Andvari Egilssen		( 277 )
script.labels["OnArrived"] = function(ctx)
    -- MM_THRONHEIM.scr:64
    do return ctx:exit("") end -- MM_THRONHEIM.scr:67
end

script.labels["WarpOn"] = function(ctx)
    -- MM_THRONHEIM.scr:70
    ctx:state().bWarp = true -- MM_THRONHEIM.scr:73
    do return ctx:exit("") end -- MM_THRONHEIM.scr:75
end

script.labels["WarpOff"] = function(ctx)
    -- MM_THRONHEIM.scr:78
    ctx:state().bWarp = false -- MM_THRONHEIM.scr:81
    do return ctx:exit("") end -- MM_THRONHEIM.scr:83
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_THRONHEIM.scr:86
    if ctx:condition("goto_location == Work") then -- MM_THRONHEIM.scr:89
        ctx:set("goto_marker", "marker_work + npc_id") -- MM_THRONHEIM.scr:90
    end -- MM_THRONHEIM.scr:91
    if ctx:condition("goto_location == Home") then -- MM_THRONHEIM.scr:93
        ctx:set("goto_marker", "marker_home + npc_id") -- MM_THRONHEIM.scr:94
    end -- MM_THRONHEIM.scr:95
    if ctx:condition("goto_location == Misc") then -- MM_THRONHEIM.scr:97
        ctx:set("goto_marker", "marker_misc + npc_id") -- MM_THRONHEIM.scr:98
    end -- MM_THRONHEIM.scr:99
    do return ctx:exit("") end -- MM_THRONHEIM.scr:101
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_THRONHEIM.scr:104
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_THRONHEIM.scr:107
    ctx:object("npc_object"):setStat("PARAM", "goto_marker") -- MM_THRONHEIM.scr:109
    if ctx:condition("bWarp == FALSE") then -- MM_THRONHEIM.scr:111
        ctx:trigger("npc_object", "GoToLoc") -- MM_THRONHEIM.scr:112
    end -- MM_THRONHEIM.scr:113
    if ctx:condition("bWarp == TRUE") then -- MM_THRONHEIM.scr:115
        ctx:trigger("npc_object", "WarpToLoc") -- MM_THRONHEIM.scr:116
    end -- MM_THRONHEIM.scr:117
    do return ctx:exit("") end -- MM_THRONHEIM.scr:119
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_THRONHEIM.scr:122
    ctx:state().index = 0 -- MM_THRONHEIM.scr:125
    while ctx:condition("index < 10") do -- MM_THRONHEIM.scr:127
        ctx:state().npc_id = 0 -- MM_THRONHEIM.scr:129
        if ctx:condition("current_group == Group1") then -- MM_THRONHEIM.scr:131
            ctx:arrayGet("aGroup1", "index", "npc_id") -- MM_THRONHEIM.scr:132
        end -- MM_THRONHEIM.scr:133
        if ctx:condition("current_group == Group2") then -- MM_THRONHEIM.scr:135
            ctx:arrayGet("aGroup2", "index", "npc_id") -- MM_THRONHEIM.scr:136
        end -- MM_THRONHEIM.scr:137
        if ctx:condition("current_group == Group3") then -- MM_THRONHEIM.scr:139
            ctx:arrayGet("aGroup3", "index", "npc_id") -- MM_THRONHEIM.scr:140
        end -- MM_THRONHEIM.scr:141
        if ctx:condition("current_group == Group4") then -- MM_THRONHEIM.scr:143
            ctx:arrayGet("aGroup4", "index", "npc_id") -- MM_THRONHEIM.scr:144
        end -- MM_THRONHEIM.scr:145
        if ctx:condition("npc_id != 0") then -- MM_THRONHEIM.scr:147
            mm9.gosub(script, ctx, "CreateMarker") -- MM_THRONHEIM.scr:148
            mm9.gosub(script, ctx, "GoToLocation") -- MM_THRONHEIM.scr:149
        end -- MM_THRONHEIM.scr:150
        ctx:set("index", "index + 1") -- MM_THRONHEIM.scr:152
    end -- MM_THRONHEIM.scr:153
    do return ctx:exit("") end -- MM_THRONHEIM.scr:155
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_THRONHEIM.scr:162
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:165
    ctx:set("current_group", "Group1") -- MM_THRONHEIM.scr:166
    ctx:set("goto_location", "Work") -- MM_THRONHEIM.scr:167
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:168
    do return ctx:exit("") end -- MM_THRONHEIM.scr:170
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_THRONHEIM.scr:173
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:176
    ctx:set("current_group", "Group1") -- MM_THRONHEIM.scr:177
    ctx:set("goto_location", "Work") -- MM_THRONHEIM.scr:178
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:179
    do return ctx:exit("") end -- MM_THRONHEIM.scr:181
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_THRONHEIM.scr:184
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:187
    ctx:set("current_group", "Group1") -- MM_THRONHEIM.scr:188
    ctx:set("goto_location", "Home") -- MM_THRONHEIM.scr:189
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:190
    do return ctx:exit("") end -- MM_THRONHEIM.scr:192
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_THRONHEIM.scr:195
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:198
    ctx:set("current_group", "Group1") -- MM_THRONHEIM.scr:199
    ctx:set("goto_location", "Home") -- MM_THRONHEIM.scr:200
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:201
    do return ctx:exit("") end -- MM_THRONHEIM.scr:203
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_THRONHEIM.scr:206
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:209
    ctx:set("current_group", "Group1") -- MM_THRONHEIM.scr:210
    ctx:set("goto_location", "Misc") -- MM_THRONHEIM.scr:211
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:212
    do return ctx:exit("") end -- MM_THRONHEIM.scr:214
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_THRONHEIM.scr:217
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:220
    ctx:set("current_group", "Group1") -- MM_THRONHEIM.scr:221
    ctx:set("goto_location", "Misc") -- MM_THRONHEIM.scr:222
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:223
    do return ctx:exit("") end -- MM_THRONHEIM.scr:225
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_THRONHEIM.scr:229
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:232
    ctx:set("current_group", "Group2") -- MM_THRONHEIM.scr:233
    ctx:set("goto_location", "Work") -- MM_THRONHEIM.scr:234
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:235
    do return ctx:exit("") end -- MM_THRONHEIM.scr:237
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_THRONHEIM.scr:240
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:243
    ctx:set("current_group", "Group2") -- MM_THRONHEIM.scr:244
    ctx:set("goto_location", "Work") -- MM_THRONHEIM.scr:245
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:246
    do return ctx:exit("") end -- MM_THRONHEIM.scr:248
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_THRONHEIM.scr:251
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:254
    ctx:set("current_group", "Group2") -- MM_THRONHEIM.scr:255
    ctx:set("goto_location", "Home") -- MM_THRONHEIM.scr:256
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:257
    do return ctx:exit("") end -- MM_THRONHEIM.scr:259
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_THRONHEIM.scr:262
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:265
    ctx:set("current_group", "Group2") -- MM_THRONHEIM.scr:266
    ctx:set("goto_location", "Home") -- MM_THRONHEIM.scr:267
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:268
    do return ctx:exit("") end -- MM_THRONHEIM.scr:270
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_THRONHEIM.scr:273
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:276
    ctx:set("current_group", "Group2") -- MM_THRONHEIM.scr:277
    ctx:set("goto_location", "Misc") -- MM_THRONHEIM.scr:278
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:279
    do return ctx:exit("") end -- MM_THRONHEIM.scr:281
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_THRONHEIM.scr:284
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:287
    ctx:set("current_group", "Group2") -- MM_THRONHEIM.scr:288
    ctx:set("goto_location", "Misc") -- MM_THRONHEIM.scr:289
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:290
    do return ctx:exit("") end -- MM_THRONHEIM.scr:292
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_THRONHEIM.scr:295
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:298
    ctx:set("current_group", "Group3") -- MM_THRONHEIM.scr:299
    ctx:set("goto_location", "Work") -- MM_THRONHEIM.scr:300
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:301
    do return ctx:exit("") end -- MM_THRONHEIM.scr:303
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_THRONHEIM.scr:306
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:309
    ctx:set("current_group", "Group3") -- MM_THRONHEIM.scr:310
    ctx:set("goto_location", "Work") -- MM_THRONHEIM.scr:311
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:312
    do return ctx:exit("") end -- MM_THRONHEIM.scr:314
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_THRONHEIM.scr:317
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:320
    ctx:set("current_group", "Group3") -- MM_THRONHEIM.scr:321
    ctx:set("goto_location", "Home") -- MM_THRONHEIM.scr:322
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:323
    do return ctx:exit("") end -- MM_THRONHEIM.scr:325
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_THRONHEIM.scr:328
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:331
    ctx:set("current_group", "Group3") -- MM_THRONHEIM.scr:332
    ctx:set("goto_location", "Home") -- MM_THRONHEIM.scr:333
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:334
    do return ctx:exit("") end -- MM_THRONHEIM.scr:336
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_THRONHEIM.scr:339
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:342
    ctx:set("current_group", "Group3") -- MM_THRONHEIM.scr:343
    ctx:set("goto_location", "Misc") -- MM_THRONHEIM.scr:344
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:345
    do return ctx:exit("") end -- MM_THRONHEIM.scr:347
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_THRONHEIM.scr:350
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:353
    ctx:set("current_group", "Group3") -- MM_THRONHEIM.scr:354
    ctx:set("goto_location", "Misc") -- MM_THRONHEIM.scr:355
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:356
    do return ctx:exit("") end -- MM_THRONHEIM.scr:358
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_THRONHEIM.scr:361
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:364
    ctx:set("current_group", "Group4") -- MM_THRONHEIM.scr:365
    ctx:set("goto_location", "Work") -- MM_THRONHEIM.scr:366
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:367
    do return ctx:exit("") end -- MM_THRONHEIM.scr:369
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_THRONHEIM.scr:372
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:375
    ctx:set("current_group", "Group4") -- MM_THRONHEIM.scr:376
    ctx:set("goto_location", "Work") -- MM_THRONHEIM.scr:377
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:378
    do return ctx:exit("") end -- MM_THRONHEIM.scr:380
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_THRONHEIM.scr:384
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:387
    ctx:set("current_group", "Group4") -- MM_THRONHEIM.scr:388
    ctx:set("goto_location", "Home") -- MM_THRONHEIM.scr:389
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:390
    do return ctx:exit("") end -- MM_THRONHEIM.scr:392
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_THRONHEIM.scr:395
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:398
    ctx:set("current_group", "Group4") -- MM_THRONHEIM.scr:399
    ctx:set("goto_location", "Home") -- MM_THRONHEIM.scr:400
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:401
    do return ctx:exit("") end -- MM_THRONHEIM.scr:403
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_THRONHEIM.scr:406
    mm9.gosub(script, ctx, "WarpOff") -- MM_THRONHEIM.scr:409
    ctx:set("current_group", "Group4") -- MM_THRONHEIM.scr:410
    ctx:set("goto_location", "Misc") -- MM_THRONHEIM.scr:411
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:412
    do return ctx:exit("") end -- MM_THRONHEIM.scr:414
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_THRONHEIM.scr:417
    mm9.gosub(script, ctx, "WarpOn") -- MM_THRONHEIM.scr:420
    ctx:set("current_group", "Group4") -- MM_THRONHEIM.scr:421
    ctx:set("goto_location", "Misc") -- MM_THRONHEIM.scr:422
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_THRONHEIM.scr:423
    do return ctx:exit("") end -- MM_THRONHEIM.scr:425
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_THRONHEIM.scr:433
    ctx:atTime(6, 15, "Group1_GoWork", "Group1_WarpWork") -- MM_THRONHEIM.scr:436
    ctx:atTime(6, 30, "Group2_GoWork", "Group2_WarpWork") -- MM_THRONHEIM.scr:437
    ctx:atTime(6, 45, "Group3_GoWork", "Group3_WarpWork") -- MM_THRONHEIM.scr:438
    ctx:atTime(7, 0, "Group4_GoWork", "Group4_WarpWork") -- MM_THRONHEIM.scr:439
    do return ctx:exit("") end -- MM_THRONHEIM.scr:441
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_THRONHEIM.scr:445
    ctx:atTime(18, 0, "Group1_GoHome", "Group1_WarpHome") -- MM_THRONHEIM.scr:448
    ctx:atTime(18, 15, "Group2_GoHome", "Group2_WarpHome") -- MM_THRONHEIM.scr:449
    ctx:atTime(18, 30, "Group3_GoHome", "Group3_WarpHome") -- MM_THRONHEIM.scr:450
    ctx:atTime(18, 45, "Group4_GoHome", "Group4_WarpHome") -- MM_THRONHEIM.scr:451
    do return ctx:exit("") end -- MM_THRONHEIM.scr:453
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_THRONHEIM.scr:456
    -- Go Wander off to somewhere
    ctx:atTime(13, 0, "Group1_GoMisc", "Group1_WarpMisc") -- MM_THRONHEIM.scr:460
    ctx:atTime(13, 15, "Group2_GoMisc", "Group2_WarpMisc") -- MM_THRONHEIM.scr:461
    ctx:atTime(13, 30, "Group3_GoMisc", "Group3_WarpMisc") -- MM_THRONHEIM.scr:462
    ctx:atTime(13, 45, "Group4_GoMisc", "Group4_WarpMisc") -- MM_THRONHEIM.scr:463
    -- Go Back to work
    ctx:atTime(15, 0, "Group1_GoWork", "Group1_WarpWork") -- MM_THRONHEIM.scr:466
    ctx:atTime(15, 15, "Group2_GoWork", "Group2_WarpWork") -- MM_THRONHEIM.scr:467
    ctx:atTime(15, 30, "Group3_GoWork", "Group3_WarpWork") -- MM_THRONHEIM.scr:468
    ctx:atTime(15, 45, "Group4_GoWork", "Group4_WarpWork") -- MM_THRONHEIM.scr:469
    do return ctx:exit("") end -- MM_THRONHEIM.scr:471
end

script.labels["InitArrays"] = function(ctx)
    -- MM_THRONHEIM.scr:479
    ctx:state().index = 0 -- MM_THRONHEIM.scr:482
    while ctx:condition("index < 10") do -- MM_THRONHEIM.scr:483
        ctx:arrayPut("aGroup1", "index", 0) -- MM_THRONHEIM.scr:484
        ctx:arrayPut("aGroup2", "index", 0) -- MM_THRONHEIM.scr:485
        ctx:arrayPut("aGroup3", "index", 0) -- MM_THRONHEIM.scr:486
        ctx:arrayPut("aGroup4", "index", 0) -- MM_THRONHEIM.scr:487
        ctx:set("index", "index + 1") -- MM_THRONHEIM.scr:488
    end -- MM_THRONHEIM.scr:489
    do return ctx:exit("") end -- MM_THRONHEIM.scr:491
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_THRONHEIM.scr:495
    -- Olaf Frodessen			( 262 )
    ctx:arrayPut("aGroup1", 0, 262) -- MM_THRONHEIM.scr:499
    -- Allasan A'Washadi		( 268 )
    ctx:arrayPut("aGroup1", 1, 268) -- MM_THRONHEIM.scr:502
    -- Comgghan A'Feslo		( 272 )
    ctx:arrayPut("aGroup1", 3, 272) -- MM_THRONHEIM.scr:505
    -- Bryan Hrutssen			( 273 )
    ctx:arrayPut("aGroup1", 4, 273) -- MM_THRONHEIM.scr:508
    -- Andvari Egilssen		( 277 )
    ctx:arrayPut("aGroup1", 5, 277) -- MM_THRONHEIM.scr:511
    do return ctx:exit("") end -- MM_THRONHEIM.scr:513
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_THRONHEIM.scr:516
    -- Neda Haki				( 263 )
    ctx:arrayPut("aGroup2", 0, 263) -- MM_THRONHEIM.scr:520
    -- Eimhir A'Mor			( 269 )
    ctx:arrayPut("aGroup2", 1, 269) -- MM_THRONHEIM.scr:523
    -- Dain Swordstrong		( 278 )
    ctx:arrayPut("aGroup2", 2, 278) -- MM_THRONHEIM.scr:526
    -- Dagny Borkdotir			( 274 )
    ctx:arrayPut("aGroup2", 3, 274) -- MM_THRONHEIM.scr:529
    do return ctx:exit("") end -- MM_THRONHEIM.scr:531
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_THRONHEIM.scr:534
    -- Caitir A'Feslo			( 264 )
    ctx:arrayPut("aGroup3", 0, 264) -- MM_THRONHEIM.scr:538
    -- Fland A'Tryht			( 270 )
    ctx:arrayPut("aGroup3", 1, 270) -- MM_THRONHEIM.scr:541
    -- Yoltzin Tor				( 279 )
    ctx:arrayPut("aGroup3", 2, 279) -- MM_THRONHEIM.scr:544
    -- Ran Tryygvadotir		( 275 )
    ctx:arrayPut("aGroup3", 3, 275) -- MM_THRONHEIM.scr:547
    do return ctx:exit("") end -- MM_THRONHEIM.scr:549
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_THRONHEIM.scr:552
    -- Gudlaug Ragnarssen		( 265 )
    ctx:arrayPut("aGroup4", 0, 265) -- MM_THRONHEIM.scr:556
    -- Muiredach A'Lanth		( 271 )
    ctx:arrayPut("aGroup4", 1, 271) -- MM_THRONHEIM.scr:559
    -- Ateed Bakari			( 280 )
    ctx:arrayPut("aGroup4", 2, 280) -- MM_THRONHEIM.scr:562
    -- Fjall Bodilssen			( 276 )
    ctx:arrayPut("aGroup4", 3, 276) -- MM_THRONHEIM.scr:565
    do return ctx:exit("") end -- MM_THRONHEIM.scr:567
end

script.labels["Init"] = function(ctx)
    -- MM_THRONHEIM.scr:570
    mm9.gosub(script, ctx, "InitArrays") -- MM_THRONHEIM.scr:572
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_THRONHEIM.scr:574
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_THRONHEIM.scr:575
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_THRONHEIM.scr:576
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_THRONHEIM.scr:577
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_THRONHEIM.scr:579
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_THRONHEIM.scr:580
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_THRONHEIM.scr:581
    do return ctx:exit("") end -- MM_THRONHEIM.scr:583
end

script.labels["Main"] = function(ctx)
    -- MM_THRONHEIM.scr:586
    mm9.gosub(script, ctx, "Init") -- MM_THRONHEIM.scr:588
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_THRONHEIM.scr:589
    do return ctx:exit("") end -- MM_THRONHEIM.scr:591
end

return script
