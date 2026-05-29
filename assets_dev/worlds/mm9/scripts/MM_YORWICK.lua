-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_YORWICK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 32, path = "Globals.inc" }

-- MM_Yorwick.scr
-- Jim Craig
-- Mundane Task List for Yorwick
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
    -- MM_YORWICK.scr:63
    do return ctx:exit("") end -- MM_YORWICK.scr:66
end

script.labels["WarpOn"] = function(ctx)
    -- MM_YORWICK.scr:69
    ctx:state().bWarp = true -- MM_YORWICK.scr:72
    do return ctx:exit("") end -- MM_YORWICK.scr:74
end

script.labels["WarpOff"] = function(ctx)
    -- MM_YORWICK.scr:77
    ctx:state().bWarp = false -- MM_YORWICK.scr:80
    do return ctx:exit("") end -- MM_YORWICK.scr:82
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_YORWICK.scr:85
    if ctx:condition("goto_location == Work") then -- MM_YORWICK.scr:88
        ctx:set("goto_marker", "marker_work + npc_id") -- MM_YORWICK.scr:89
    end -- MM_YORWICK.scr:90
    if ctx:condition("goto_location == Home") then -- MM_YORWICK.scr:92
        ctx:set("goto_marker", "marker_home + npc_id") -- MM_YORWICK.scr:93
    end -- MM_YORWICK.scr:94
    if ctx:condition("goto_location == Misc") then -- MM_YORWICK.scr:96
        ctx:set("goto_marker", "marker_misc + npc_id") -- MM_YORWICK.scr:97
    end -- MM_YORWICK.scr:98
    do return ctx:exit("") end -- MM_YORWICK.scr:100
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_YORWICK.scr:103
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_YORWICK.scr:106
    ctx:object("npc_object"):setStat("PARAM", "goto_marker") -- MM_YORWICK.scr:108
    if ctx:condition("bWarp == FALSE") then -- MM_YORWICK.scr:110
        ctx:trigger("npc_object", "GoToLoc") -- MM_YORWICK.scr:111
    end -- MM_YORWICK.scr:112
    if ctx:condition("bWarp == TRUE") then -- MM_YORWICK.scr:114
        ctx:trigger("npc_object", "WarpToLoc") -- MM_YORWICK.scr:115
    end -- MM_YORWICK.scr:116
    do return ctx:exit("") end -- MM_YORWICK.scr:118
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_YORWICK.scr:121
    ctx:state().index = 0 -- MM_YORWICK.scr:124
    while ctx:condition("index < 10") do -- MM_YORWICK.scr:126
        ctx:state().npc_id = 0 -- MM_YORWICK.scr:128
        if ctx:condition("current_group == Group1") then -- MM_YORWICK.scr:130
            ctx:arrayGet("aGroup1", "index", "npc_id") -- MM_YORWICK.scr:131
        end -- MM_YORWICK.scr:132
        if ctx:condition("current_group == Group2") then -- MM_YORWICK.scr:134
            ctx:arrayGet("aGroup2", "index", "npc_id") -- MM_YORWICK.scr:135
        end -- MM_YORWICK.scr:136
        if ctx:condition("current_group == Group3") then -- MM_YORWICK.scr:138
            ctx:arrayGet("aGroup3", "index", "npc_id") -- MM_YORWICK.scr:139
        end -- MM_YORWICK.scr:140
        if ctx:condition("current_group == Group4") then -- MM_YORWICK.scr:142
            ctx:arrayGet("aGroup4", "index", "npc_id") -- MM_YORWICK.scr:143
        end -- MM_YORWICK.scr:144
        if ctx:condition("npc_id != 0") then -- MM_YORWICK.scr:146
            mm9.gosub(script, ctx, "CreateMarker") -- MM_YORWICK.scr:147
            mm9.gosub(script, ctx, "GoToLocation") -- MM_YORWICK.scr:148
        end -- MM_YORWICK.scr:149
        ctx:set("index", "index + 1") -- MM_YORWICK.scr:151
    end -- MM_YORWICK.scr:152
    do return ctx:exit("") end -- MM_YORWICK.scr:154
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_YORWICK.scr:161
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:164
    ctx:set("current_group", "Group1") -- MM_YORWICK.scr:165
    ctx:set("goto_location", "Work") -- MM_YORWICK.scr:166
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:167
    do return ctx:exit("") end -- MM_YORWICK.scr:169
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_YORWICK.scr:172
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:175
    ctx:set("current_group", "Group1") -- MM_YORWICK.scr:176
    ctx:set("goto_location", "Work") -- MM_YORWICK.scr:177
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:178
    do return ctx:exit("") end -- MM_YORWICK.scr:180
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_YORWICK.scr:183
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:186
    ctx:set("current_group", "Group1") -- MM_YORWICK.scr:187
    ctx:set("goto_location", "Home") -- MM_YORWICK.scr:188
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:189
    do return ctx:exit("") end -- MM_YORWICK.scr:191
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_YORWICK.scr:194
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:197
    ctx:set("current_group", "Group1") -- MM_YORWICK.scr:198
    ctx:set("goto_location", "Home") -- MM_YORWICK.scr:199
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:200
    do return ctx:exit("") end -- MM_YORWICK.scr:202
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_YORWICK.scr:205
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:208
    ctx:set("current_group", "Group1") -- MM_YORWICK.scr:209
    ctx:set("goto_location", "Misc") -- MM_YORWICK.scr:210
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:211
    do return ctx:exit("") end -- MM_YORWICK.scr:213
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_YORWICK.scr:216
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:219
    ctx:set("current_group", "Group1") -- MM_YORWICK.scr:220
    ctx:set("goto_location", "Misc") -- MM_YORWICK.scr:221
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:222
    do return ctx:exit("") end -- MM_YORWICK.scr:224
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_YORWICK.scr:228
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:231
    ctx:set("current_group", "Group2") -- MM_YORWICK.scr:232
    ctx:set("goto_location", "Work") -- MM_YORWICK.scr:233
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:234
    do return ctx:exit("") end -- MM_YORWICK.scr:236
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_YORWICK.scr:239
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:242
    ctx:set("current_group", "Group2") -- MM_YORWICK.scr:243
    ctx:set("goto_location", "Work") -- MM_YORWICK.scr:244
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:245
    do return ctx:exit("") end -- MM_YORWICK.scr:247
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_YORWICK.scr:250
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:253
    ctx:set("current_group", "Group2") -- MM_YORWICK.scr:254
    ctx:set("goto_location", "Home") -- MM_YORWICK.scr:255
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:256
    do return ctx:exit("") end -- MM_YORWICK.scr:258
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_YORWICK.scr:261
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:264
    ctx:set("current_group", "Group2") -- MM_YORWICK.scr:265
    ctx:set("goto_location", "Home") -- MM_YORWICK.scr:266
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:267
    do return ctx:exit("") end -- MM_YORWICK.scr:269
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_YORWICK.scr:272
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:275
    ctx:set("current_group", "Group2") -- MM_YORWICK.scr:276
    ctx:set("goto_location", "Misc") -- MM_YORWICK.scr:277
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:278
    do return ctx:exit("") end -- MM_YORWICK.scr:280
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_YORWICK.scr:283
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:286
    ctx:set("current_group", "Group2") -- MM_YORWICK.scr:287
    ctx:set("goto_location", "Misc") -- MM_YORWICK.scr:288
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:289
    do return ctx:exit("") end -- MM_YORWICK.scr:291
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_YORWICK.scr:294
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:297
    ctx:set("current_group", "Group3") -- MM_YORWICK.scr:298
    ctx:set("goto_location", "Work") -- MM_YORWICK.scr:299
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:300
    do return ctx:exit("") end -- MM_YORWICK.scr:302
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_YORWICK.scr:305
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:308
    ctx:set("current_group", "Group3") -- MM_YORWICK.scr:309
    ctx:set("goto_location", "Work") -- MM_YORWICK.scr:310
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:311
    do return ctx:exit("") end -- MM_YORWICK.scr:313
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_YORWICK.scr:316
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:319
    ctx:set("current_group", "Group3") -- MM_YORWICK.scr:320
    ctx:set("goto_location", "Home") -- MM_YORWICK.scr:321
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:322
    do return ctx:exit("") end -- MM_YORWICK.scr:324
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_YORWICK.scr:327
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:330
    ctx:set("current_group", "Group3") -- MM_YORWICK.scr:331
    ctx:set("goto_location", "Home") -- MM_YORWICK.scr:332
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:333
    do return ctx:exit("") end -- MM_YORWICK.scr:335
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_YORWICK.scr:338
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:341
    ctx:set("current_group", "Group3") -- MM_YORWICK.scr:342
    ctx:set("goto_location", "Misc") -- MM_YORWICK.scr:343
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:344
    do return ctx:exit("") end -- MM_YORWICK.scr:346
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_YORWICK.scr:349
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:352
    ctx:set("current_group", "Group3") -- MM_YORWICK.scr:353
    ctx:set("goto_location", "Misc") -- MM_YORWICK.scr:354
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:355
    do return ctx:exit("") end -- MM_YORWICK.scr:357
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_YORWICK.scr:360
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:363
    ctx:set("current_group", "Group4") -- MM_YORWICK.scr:364
    ctx:set("goto_location", "Work") -- MM_YORWICK.scr:365
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:366
    do return ctx:exit("") end -- MM_YORWICK.scr:368
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_YORWICK.scr:371
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:374
    ctx:set("current_group", "Group4") -- MM_YORWICK.scr:375
    ctx:set("goto_location", "Work") -- MM_YORWICK.scr:376
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:377
    do return ctx:exit("") end -- MM_YORWICK.scr:379
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_YORWICK.scr:383
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:386
    ctx:set("current_group", "Group4") -- MM_YORWICK.scr:387
    ctx:set("goto_location", "Home") -- MM_YORWICK.scr:388
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:389
    do return ctx:exit("") end -- MM_YORWICK.scr:391
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_YORWICK.scr:394
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:397
    ctx:set("current_group", "Group4") -- MM_YORWICK.scr:398
    ctx:set("goto_location", "Home") -- MM_YORWICK.scr:399
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:400
    do return ctx:exit("") end -- MM_YORWICK.scr:402
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_YORWICK.scr:405
    mm9.gosub(script, ctx, "WarpOff") -- MM_YORWICK.scr:408
    ctx:set("current_group", "Group4") -- MM_YORWICK.scr:409
    ctx:set("goto_location", "Misc") -- MM_YORWICK.scr:410
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:411
    do return ctx:exit("") end -- MM_YORWICK.scr:413
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_YORWICK.scr:416
    mm9.gosub(script, ctx, "WarpOn") -- MM_YORWICK.scr:419
    ctx:set("current_group", "Group4") -- MM_YORWICK.scr:420
    ctx:set("goto_location", "Misc") -- MM_YORWICK.scr:421
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_YORWICK.scr:422
    do return ctx:exit("") end -- MM_YORWICK.scr:424
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_YORWICK.scr:432
    ctx:atTime(6, 15, "Group1_GoWork", "Group1_WarpWork") -- MM_YORWICK.scr:435
    ctx:atTime(6, 30, "Group2_GoWork", "Group2_WarpWork") -- MM_YORWICK.scr:436
    ctx:atTime(6, 45, "Group3_GoWork", "Group3_WarpWork") -- MM_YORWICK.scr:437
    ctx:atTime(7, 0, "Group4_GoWork", "Group4_WarpWork") -- MM_YORWICK.scr:438
    do return ctx:exit("") end -- MM_YORWICK.scr:440
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_YORWICK.scr:444
    ctx:atTime(18, 0, "Group1_GoHome", "Group1_WarpHome") -- MM_YORWICK.scr:447
    ctx:atTime(18, 15, "Group2_GoHome", "Group2_WarpHome") -- MM_YORWICK.scr:448
    ctx:atTime(18, 30, "Group3_GoHome", "Group3_WarpHome") -- MM_YORWICK.scr:449
    ctx:atTime(18, 45, "Group4_GoHome", "Group4_WarpHome") -- MM_YORWICK.scr:450
    do return ctx:exit("") end -- MM_YORWICK.scr:452
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_YORWICK.scr:455
    -- Go Wander off to somewhere
    ctx:atTime(13, 0, "Group1_GoMisc", "Group1_WarpMisc") -- MM_YORWICK.scr:459
    ctx:atTime(13, 15, "Group2_GoMisc", "Group2_WarpMisc") -- MM_YORWICK.scr:460
    ctx:atTime(13, 30, "Group3_GoMisc", "Group3_WarpMisc") -- MM_YORWICK.scr:461
    ctx:atTime(13, 45, "Group4_GoMisc", "Group4_WarpMisc") -- MM_YORWICK.scr:462
    -- Go Back to work
    ctx:atTime(15, 0, "Group1_GoWork", "Group1_WarpWork") -- MM_YORWICK.scr:465
    ctx:atTime(15, 15, "Group2_GoWork", "Group2_WarpWork") -- MM_YORWICK.scr:466
    ctx:atTime(15, 30, "Group3_GoWork", "Group3_WarpWork") -- MM_YORWICK.scr:467
    ctx:atTime(15, 45, "Group4_GoWork", "Group4_WarpWork") -- MM_YORWICK.scr:468
    do return ctx:exit("") end -- MM_YORWICK.scr:470
end

script.labels["InitArrays"] = function(ctx)
    -- MM_YORWICK.scr:478
    ctx:state().index = 0 -- MM_YORWICK.scr:481
    while ctx:condition("index < 10") do -- MM_YORWICK.scr:482
        ctx:arrayPut("aGroup1", "index", 0) -- MM_YORWICK.scr:483
        ctx:arrayPut("aGroup2", "index", 0) -- MM_YORWICK.scr:484
        ctx:arrayPut("aGroup3", "index", 0) -- MM_YORWICK.scr:485
        ctx:arrayPut("aGroup4", "index", 0) -- MM_YORWICK.scr:486
        ctx:set("index", "index + 1") -- MM_YORWICK.scr:487
    end -- MM_YORWICK.scr:488
    do return ctx:exit("") end -- MM_YORWICK.scr:490
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_YORWICK.scr:494
    -- Bran A'Norta a'leipshi	( 322 )
    ctx:arrayPut("aGroup1", 0, 322) -- MM_YORWICK.scr:498
    -- Asvald Hrrappssen		( 328 )
    ctx:arrayPut("aGroup1", 1, 328) -- MM_YORWICK.scr:501
    -- Marshall Hanford		( 333 )
    ctx:arrayPut("aGroup1", 2, 333) -- MM_YORWICK.scr:504
    -- Laina Wilan				( 409 )
    ctx:arrayPut("aGroup1", 3, 409) -- MM_YORWICK.scr:507
    -- Brighde A'Endlar		( 413 )
    ctx:arrayPut("aGroup1", 4, 413) -- MM_YORWICK.scr:510
    do return ctx:exit("") end -- MM_YORWICK.scr:512
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_YORWICK.scr:515
    -- Caitir A'Klindor		( 324 )
    ctx:arrayPut("aGroup2", 0, 324) -- MM_YORWICK.scr:519
    -- Snora Hreidrardotir		( 330 )
    ctx:arrayPut("aGroup2", 1, 330) -- MM_YORWICK.scr:522
    -- Bren Haukdotir			( 329 )
    ctx:arrayPut("aGroup2", 2, 329) -- MM_YORWICK.scr:525
    -- Ragfreid Manslayer		( 410 )
    ctx:arrayPut("aGroup2", 3, 410) -- MM_YORWICK.scr:528
    do return ctx:exit("") end -- MM_YORWICK.scr:530
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_YORWICK.scr:533
    -- Searlaid A'Endlar		( 325 )
    ctx:arrayPut("aGroup3", 0, 325) -- MM_YORWICK.scr:537
    -- Kenward Mason			( 331 )
    ctx:arrayPut("aGroup3", 1, 331) -- MM_YORWICK.scr:540
    -- Broccan A'Ghrie			( 323 )
    ctx:arrayPut("aGroup3", 2, 323) -- MM_YORWICK.scr:543
    -- Jenn Harrise			( 411 )
    ctx:arrayPut("aGroup3", 3, 411) -- MM_YORWICK.scr:546
    do return ctx:exit("") end -- MM_YORWICK.scr:548
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_YORWICK.scr:551
    -- Eskil Bodilssen			( 326 )
    ctx:arrayPut("aGroup4", 0, 326) -- MM_YORWICK.scr:555
    -- Lane the Framish		( 332 )
    ctx:arrayPut("aGroup4", 1, 332) -- MM_YORWICK.scr:558
    -- Halvar Davinssen		( 327 )
    ctx:arrayPut("aGroup4", 2, 327) -- MM_YORWICK.scr:561
    -- Stev Palac				( 412 )
    ctx:arrayPut("aGroup4", 3, 412) -- MM_YORWICK.scr:564
    do return ctx:exit("") end -- MM_YORWICK.scr:566
end

script.labels["Init"] = function(ctx)
    -- MM_YORWICK.scr:572
    mm9.gosub(script, ctx, "InitArrays") -- MM_YORWICK.scr:574
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_YORWICK.scr:576
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_YORWICK.scr:577
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_YORWICK.scr:578
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_YORWICK.scr:579
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_YORWICK.scr:581
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_YORWICK.scr:582
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_YORWICK.scr:583
    do return ctx:exit("") end -- MM_YORWICK.scr:585
end

script.labels["Main"] = function(ctx)
    -- MM_YORWICK.scr:588
    mm9.gosub(script, ctx, "Init") -- MM_YORWICK.scr:590
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_YORWICK.scr:591
    do return ctx:exit("") end -- MM_YORWICK.scr:593
end

return script
