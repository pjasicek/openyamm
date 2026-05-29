-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_JYRKAVIK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 32, path = "Globals.inc" }

-- MM_Jyrkavik.scr
-- Jim Craig
-- Mundane Task List for Jyrkavik
-- Current NPCs
-- Ambient NPCs
-- Bran A'Norta a'leipshi	( 322 )
-- Caitir A'Klindor		( 324 )
-- Searlaid A'Endlar		( 325 )
-- Eskil Bodilssen			( 326 )
-- Asvald Hrrappssen		( 328 )
-- Snora Hreidrardotir		( 330 )
-- Kenward Mason			( 331 )
-- Lane the Framish		( 332 )
-- Teacher NPCs
-- Marshall Hanford		( 333 )
-- Bren Haukdotir			( 329 )
-- Broccan A'Ghrie			( 323 )
-- Halvar Davinssen		( 327 )
-- Laina Wilan				( 409 )
-- Ragfreid Manslayer		( 410 )
-- Jenn Harrise			( 411 )
-- Stev Palac				( 412 )
-- Brighde A'Endlar		( 413 )
script.labels["OnArrived"] = function(ctx)
    -- MM_JYRKAVIK.scr:63
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:66
end

script.labels["WarpOn"] = function(ctx)
    -- MM_JYRKAVIK.scr:69
    ctx:state().bWarp = true -- MM_JYRKAVIK.scr:72
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:74
end

script.labels["WarpOff"] = function(ctx)
    -- MM_JYRKAVIK.scr:77
    ctx:state().bWarp = false -- MM_JYRKAVIK.scr:80
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:82
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_JYRKAVIK.scr:85
    if ctx:condition("goto_location == Work") then -- MM_JYRKAVIK.scr:88
        ctx:set("goto_marker", "marker_work + npc_id") -- MM_JYRKAVIK.scr:89
    end -- MM_JYRKAVIK.scr:90
    if ctx:condition("goto_location == Home") then -- MM_JYRKAVIK.scr:92
        ctx:set("goto_marker", "marker_home + npc_id") -- MM_JYRKAVIK.scr:93
    end -- MM_JYRKAVIK.scr:94
    if ctx:condition("goto_location == Misc") then -- MM_JYRKAVIK.scr:96
        ctx:set("goto_marker", "marker_misc + npc_id") -- MM_JYRKAVIK.scr:97
    end -- MM_JYRKAVIK.scr:98
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:100
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_JYRKAVIK.scr:103
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_JYRKAVIK.scr:106
    ctx:object("npc_object"):setStat("PARAM", "goto_marker") -- MM_JYRKAVIK.scr:108
    if ctx:condition("bWarp == FALSE") then -- MM_JYRKAVIK.scr:110
        ctx:trigger("npc_object", "GoToLoc") -- MM_JYRKAVIK.scr:111
    end -- MM_JYRKAVIK.scr:112
    if ctx:condition("bWarp == TRUE") then -- MM_JYRKAVIK.scr:114
        ctx:trigger("npc_object", "WarpToLoc") -- MM_JYRKAVIK.scr:115
    end -- MM_JYRKAVIK.scr:116
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:118
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_JYRKAVIK.scr:121
    ctx:state().index = 0 -- MM_JYRKAVIK.scr:124
    while ctx:condition("index < 10") do -- MM_JYRKAVIK.scr:126
        ctx:state().npc_id = 0 -- MM_JYRKAVIK.scr:128
        if ctx:condition("current_group == Group1") then -- MM_JYRKAVIK.scr:130
            ctx:arrayGet("aGroup1", "index", "npc_id") -- MM_JYRKAVIK.scr:131
        end -- MM_JYRKAVIK.scr:132
        if ctx:condition("current_group == Group2") then -- MM_JYRKAVIK.scr:134
            ctx:arrayGet("aGroup2", "index", "npc_id") -- MM_JYRKAVIK.scr:135
        end -- MM_JYRKAVIK.scr:136
        if ctx:condition("current_group == Group3") then -- MM_JYRKAVIK.scr:138
            ctx:arrayGet("aGroup3", "index", "npc_id") -- MM_JYRKAVIK.scr:139
        end -- MM_JYRKAVIK.scr:140
        if ctx:condition("current_group == Group4") then -- MM_JYRKAVIK.scr:142
            ctx:arrayGet("aGroup4", "index", "npc_id") -- MM_JYRKAVIK.scr:143
        end -- MM_JYRKAVIK.scr:144
        if ctx:condition("npc_id != 0") then -- MM_JYRKAVIK.scr:146
            mm9.gosub(script, ctx, "CreateMarker") -- MM_JYRKAVIK.scr:147
            mm9.gosub(script, ctx, "GoToLocation") -- MM_JYRKAVIK.scr:148
        end -- MM_JYRKAVIK.scr:149
        ctx:set("index", "index + 1") -- MM_JYRKAVIK.scr:151
    end -- MM_JYRKAVIK.scr:152
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:154
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_JYRKAVIK.scr:161
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:164
    ctx:set("current_group", "Group1") -- MM_JYRKAVIK.scr:165
    ctx:set("goto_location", "Work") -- MM_JYRKAVIK.scr:166
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:167
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:169
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_JYRKAVIK.scr:172
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:175
    ctx:set("current_group", "Group1") -- MM_JYRKAVIK.scr:176
    ctx:set("goto_location", "Work") -- MM_JYRKAVIK.scr:177
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:178
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:180
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_JYRKAVIK.scr:183
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:186
    ctx:set("current_group", "Group1") -- MM_JYRKAVIK.scr:187
    ctx:set("goto_location", "Home") -- MM_JYRKAVIK.scr:188
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:189
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:191
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_JYRKAVIK.scr:194
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:197
    ctx:set("current_group", "Group1") -- MM_JYRKAVIK.scr:198
    ctx:set("goto_location", "Home") -- MM_JYRKAVIK.scr:199
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:200
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:202
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_JYRKAVIK.scr:205
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:208
    ctx:set("current_group", "Group1") -- MM_JYRKAVIK.scr:209
    ctx:set("goto_location", "Misc") -- MM_JYRKAVIK.scr:210
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:211
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:213
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_JYRKAVIK.scr:216
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:219
    ctx:set("current_group", "Group1") -- MM_JYRKAVIK.scr:220
    ctx:set("goto_location", "Misc") -- MM_JYRKAVIK.scr:221
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:222
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:224
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_JYRKAVIK.scr:228
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:231
    ctx:set("current_group", "Group2") -- MM_JYRKAVIK.scr:232
    ctx:set("goto_location", "Work") -- MM_JYRKAVIK.scr:233
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:234
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:236
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_JYRKAVIK.scr:239
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:242
    ctx:set("current_group", "Group2") -- MM_JYRKAVIK.scr:243
    ctx:set("goto_location", "Work") -- MM_JYRKAVIK.scr:244
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:245
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:247
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_JYRKAVIK.scr:250
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:253
    ctx:set("current_group", "Group2") -- MM_JYRKAVIK.scr:254
    ctx:set("goto_location", "Home") -- MM_JYRKAVIK.scr:255
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:256
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:258
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_JYRKAVIK.scr:261
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:264
    ctx:set("current_group", "Group2") -- MM_JYRKAVIK.scr:265
    ctx:set("goto_location", "Home") -- MM_JYRKAVIK.scr:266
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:267
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:269
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_JYRKAVIK.scr:272
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:275
    ctx:set("current_group", "Group2") -- MM_JYRKAVIK.scr:276
    ctx:set("goto_location", "Misc") -- MM_JYRKAVIK.scr:277
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:278
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:280
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_JYRKAVIK.scr:283
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:286
    ctx:set("current_group", "Group2") -- MM_JYRKAVIK.scr:287
    ctx:set("goto_location", "Misc") -- MM_JYRKAVIK.scr:288
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:289
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:291
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_JYRKAVIK.scr:294
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:297
    ctx:set("current_group", "Group3") -- MM_JYRKAVIK.scr:298
    ctx:set("goto_location", "Work") -- MM_JYRKAVIK.scr:299
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:300
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:302
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_JYRKAVIK.scr:305
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:308
    ctx:set("current_group", "Group3") -- MM_JYRKAVIK.scr:309
    ctx:set("goto_location", "Work") -- MM_JYRKAVIK.scr:310
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:311
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:313
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_JYRKAVIK.scr:316
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:319
    ctx:set("current_group", "Group3") -- MM_JYRKAVIK.scr:320
    ctx:set("goto_location", "Home") -- MM_JYRKAVIK.scr:321
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:322
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:324
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_JYRKAVIK.scr:327
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:330
    ctx:set("current_group", "Group3") -- MM_JYRKAVIK.scr:331
    ctx:set("goto_location", "Home") -- MM_JYRKAVIK.scr:332
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:333
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:335
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_JYRKAVIK.scr:338
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:341
    ctx:set("current_group", "Group3") -- MM_JYRKAVIK.scr:342
    ctx:set("goto_location", "Misc") -- MM_JYRKAVIK.scr:343
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:344
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:346
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_JYRKAVIK.scr:349
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:352
    ctx:set("current_group", "Group3") -- MM_JYRKAVIK.scr:353
    ctx:set("goto_location", "Misc") -- MM_JYRKAVIK.scr:354
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:355
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:357
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_JYRKAVIK.scr:360
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:363
    ctx:set("current_group", "Group4") -- MM_JYRKAVIK.scr:364
    ctx:set("goto_location", "Work") -- MM_JYRKAVIK.scr:365
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:366
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:368
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_JYRKAVIK.scr:371
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:374
    ctx:set("current_group", "Group4") -- MM_JYRKAVIK.scr:375
    ctx:set("goto_location", "Work") -- MM_JYRKAVIK.scr:376
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:377
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:379
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_JYRKAVIK.scr:383
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:386
    ctx:set("current_group", "Group4") -- MM_JYRKAVIK.scr:387
    ctx:set("goto_location", "Home") -- MM_JYRKAVIK.scr:388
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:389
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:391
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_JYRKAVIK.scr:394
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:397
    ctx:set("current_group", "Group4") -- MM_JYRKAVIK.scr:398
    ctx:set("goto_location", "Home") -- MM_JYRKAVIK.scr:399
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:400
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:402
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_JYRKAVIK.scr:405
    mm9.gosub(script, ctx, "WarpOff") -- MM_JYRKAVIK.scr:408
    ctx:set("current_group", "Group4") -- MM_JYRKAVIK.scr:409
    ctx:set("goto_location", "Misc") -- MM_JYRKAVIK.scr:410
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:411
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:413
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_JYRKAVIK.scr:416
    mm9.gosub(script, ctx, "WarpOn") -- MM_JYRKAVIK.scr:419
    ctx:set("current_group", "Group4") -- MM_JYRKAVIK.scr:420
    ctx:set("goto_location", "Misc") -- MM_JYRKAVIK.scr:421
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_JYRKAVIK.scr:422
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:424
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_JYRKAVIK.scr:432
    ctx:atTime(6, 15, "Group1_GoWork", "Group1_WarpWork") -- MM_JYRKAVIK.scr:435
    ctx:atTime(6, 30, "Group2_GoWork", "Group2_WarpWork") -- MM_JYRKAVIK.scr:436
    ctx:atTime(6, 45, "Group3_GoWork", "Group3_WarpWork") -- MM_JYRKAVIK.scr:437
    ctx:atTime(7, 0, "Group4_GoWork", "Group4_WarpWork") -- MM_JYRKAVIK.scr:438
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:440
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_JYRKAVIK.scr:444
    ctx:atTime(18, 0, "Group1_GoHome", "Group1_WarpHome") -- MM_JYRKAVIK.scr:447
    ctx:atTime(18, 15, "Group2_GoHome", "Group2_WarpHome") -- MM_JYRKAVIK.scr:448
    ctx:atTime(18, 30, "Group3_GoHome", "Group3_WarpHome") -- MM_JYRKAVIK.scr:449
    ctx:atTime(18, 45, "Group4_GoHome", "Group4_WarpHome") -- MM_JYRKAVIK.scr:450
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:452
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_JYRKAVIK.scr:455
    -- Go Wander off to somewhere
    ctx:atTime(13, 0, "Group1_GoMisc", "Group1_WarpMisc") -- MM_JYRKAVIK.scr:459
    ctx:atTime(13, 15, "Group2_GoMisc", "Group2_WarpMisc") -- MM_JYRKAVIK.scr:460
    ctx:atTime(13, 30, "Group3_GoMisc", "Group3_WarpMisc") -- MM_JYRKAVIK.scr:461
    ctx:atTime(13, 45, "Group4_GoMisc", "Group4_WarpMisc") -- MM_JYRKAVIK.scr:462
    -- Go Back to work
    ctx:atTime(15, 0, "Group1_GoWork", "Group1_WarpWork") -- MM_JYRKAVIK.scr:465
    ctx:atTime(15, 15, "Group2_GoWork", "Group2_WarpWork") -- MM_JYRKAVIK.scr:466
    ctx:atTime(15, 30, "Group3_GoWork", "Group3_WarpWork") -- MM_JYRKAVIK.scr:467
    ctx:atTime(15, 45, "Group4_GoWork", "Group4_WarpWork") -- MM_JYRKAVIK.scr:468
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:470
end

script.labels["InitArrays"] = function(ctx)
    -- MM_JYRKAVIK.scr:478
    ctx:state().index = 0 -- MM_JYRKAVIK.scr:481
    while ctx:condition("index < 10") do -- MM_JYRKAVIK.scr:482
        ctx:arrayPut("aGroup1", "index", 0) -- MM_JYRKAVIK.scr:483
        ctx:arrayPut("aGroup2", "index", 0) -- MM_JYRKAVIK.scr:484
        ctx:arrayPut("aGroup3", "index", 0) -- MM_JYRKAVIK.scr:485
        ctx:arrayPut("aGroup4", "index", 0) -- MM_JYRKAVIK.scr:486
        ctx:set("index", "index + 1") -- MM_JYRKAVIK.scr:487
    end -- MM_JYRKAVIK.scr:488
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:490
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_JYRKAVIK.scr:494
    -- Bran A'Norta a'leipshi	( 322 )
    ctx:arrayPut("aGroup1", 0, 322) -- MM_JYRKAVIK.scr:498
    -- Asvald Hrrappssen		( 328 )
    ctx:arrayPut("aGroup1", 1, 328) -- MM_JYRKAVIK.scr:501
    -- Marshall Hanford		( 333 )
    ctx:arrayPut("aGroup1", 2, 333) -- MM_JYRKAVIK.scr:504
    -- Laina Wilan				( 409 )
    ctx:arrayPut("aGroup1", 3, 409) -- MM_JYRKAVIK.scr:507
    -- Brighde A'Endlar		( 413 )
    ctx:arrayPut("aGroup1", 4, 413) -- MM_JYRKAVIK.scr:510
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:512
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_JYRKAVIK.scr:515
    -- Caitir A'Klindor		( 324 )
    ctx:arrayPut("aGroup2", 0, 324) -- MM_JYRKAVIK.scr:519
    -- Snora Hreidrardotir		( 330 )
    ctx:arrayPut("aGroup2", 1, 330) -- MM_JYRKAVIK.scr:522
    -- Bren Haukdotir			( 329 )
    ctx:arrayPut("aGroup2", 2, 329) -- MM_JYRKAVIK.scr:525
    -- Ragfreid Manslayer		( 410 )
    ctx:arrayPut("aGroup2", 3, 410) -- MM_JYRKAVIK.scr:528
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:530
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_JYRKAVIK.scr:533
    -- Searlaid A'Endlar		( 325 )
    ctx:arrayPut("aGroup3", 0, 325) -- MM_JYRKAVIK.scr:537
    -- Kenward Mason			( 331 )
    ctx:arrayPut("aGroup3", 1, 331) -- MM_JYRKAVIK.scr:540
    -- Broccan A'Ghrie			( 323 )
    ctx:arrayPut("aGroup3", 2, 323) -- MM_JYRKAVIK.scr:543
    -- Jenn Harrise			( 411 )
    ctx:arrayPut("aGroup3", 3, 411) -- MM_JYRKAVIK.scr:546
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:548
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_JYRKAVIK.scr:551
    -- Eskil Bodilssen			( 326 )
    ctx:arrayPut("aGroup4", 0, 326) -- MM_JYRKAVIK.scr:555
    -- Lane the Framish		( 332 )
    ctx:arrayPut("aGroup4", 1, 332) -- MM_JYRKAVIK.scr:558
    -- Halvar Davinssen		( 327 )
    ctx:arrayPut("aGroup4", 2, 327) -- MM_JYRKAVIK.scr:561
    -- Stev Palac				( 412 )
    ctx:arrayPut("aGroup4", 3, 412) -- MM_JYRKAVIK.scr:564
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:566
end

script.labels["Init"] = function(ctx)
    -- MM_JYRKAVIK.scr:569
    mm9.gosub(script, ctx, "InitArrays") -- MM_JYRKAVIK.scr:571
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_JYRKAVIK.scr:573
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_JYRKAVIK.scr:574
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_JYRKAVIK.scr:575
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_JYRKAVIK.scr:576
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_JYRKAVIK.scr:578
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_JYRKAVIK.scr:579
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_JYRKAVIK.scr:580
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:582
end

script.labels["Main"] = function(ctx)
    -- MM_JYRKAVIK.scr:585
    mm9.gosub(script, ctx, "Init") -- MM_JYRKAVIK.scr:587
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_JYRKAVIK.scr:588
    do return ctx:exit("") end -- MM_JYRKAVIK.scr:590
end

return script
