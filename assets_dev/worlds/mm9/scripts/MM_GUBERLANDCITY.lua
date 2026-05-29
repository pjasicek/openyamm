-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_GUBERLANDCITY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 42, path = "Globals.inc" }

-- MM_GuberLandCity.scr
-- Jim Craig
-- Mundane Task List for GuberLand City
-- Current NPCs
-- Gossip NPCs
-- Mata Abyomi					( 148 )
-- Bragi the Toothloose		( 149 )
-- Scandian the Long-tongued	( 150 )	<<< REMOVED >>>
-- Broccan A'Norta a'bre		( 151 ) <<< REMOVED >>>
-- Mirek Mazatle				( 152 )
-- Gudny the Nose				( 153 )
-- Aso Stinkshirt				( 154 )
-- Darby Etzelessen			( 155 ) <<< REMOVED >>>
-- Eyjolf Bjolfssen			( 156 ) <<< REMOVED >>>
-- Aki the King				( 157 ) <<< REMOVED >>>
-- Cassidy A'Dorad				( 158 ) <<< REMOVED >>>
-- Elvis						( 159 ) <<< REMOVED >>>
-- Arni Brokkssen				( 160 ) <<< REMOVED >>>
-- Ambient NPCs
-- Fyrie the Forgettable		( 162 )
-- Gabriel Dullard				( 163 )
-- Ryan the Simpleton			( 164 )
-- Davin the Ample				( 165 )
-- Denby Badbreath				( 166 )
-- Lina Friggdotir				( 167 )
-- Gregusk Mazo				( 168 )
-- Teacher NPCs
-- Peterk Olin					( 170 )
-- Treshi Yatol				( 171 )
-- Bohus Kinar					( 172 )
-- Rya Fremi					( 173 )
-- Hrapp Tjorvissen			( 174 )
script.labels["OnArrived"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:73
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:76
end

script.labels["WarpOn"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:79
    ctx:state().bWarp = true -- MM_GUBERLANDCITY.scr:82
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:84
end

script.labels["WarpOff"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:87
    ctx:state().bWarp = false -- MM_GUBERLANDCITY.scr:90
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:92
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:95
    if ctx:condition("goto_location == Work") then -- MM_GUBERLANDCITY.scr:98
        ctx:set("goto_marker", "marker_work + npc_id") -- MM_GUBERLANDCITY.scr:99
    end -- MM_GUBERLANDCITY.scr:100
    if ctx:condition("goto_location == Home") then -- MM_GUBERLANDCITY.scr:102
        ctx:set("goto_marker", "marker_home + npc_id") -- MM_GUBERLANDCITY.scr:103
    end -- MM_GUBERLANDCITY.scr:104
    if ctx:condition("goto_location == Misc") then -- MM_GUBERLANDCITY.scr:106
        ctx:set("goto_marker", "marker_misc + npc_id") -- MM_GUBERLANDCITY.scr:107
    end -- MM_GUBERLANDCITY.scr:108
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:110
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:113
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_GUBERLANDCITY.scr:116
    ctx:object("npc_object"):setStat("PARAM", "goto_marker") -- MM_GUBERLANDCITY.scr:118
    if ctx:condition("bWarp == FALSE") then -- MM_GUBERLANDCITY.scr:120
        ctx:trigger("npc_object", "GoToLoc") -- MM_GUBERLANDCITY.scr:121
    end -- MM_GUBERLANDCITY.scr:122
    if ctx:condition("bWarp == TRUE") then -- MM_GUBERLANDCITY.scr:124
        ctx:trigger("npc_object", "WarpToLoc") -- MM_GUBERLANDCITY.scr:125
    end -- MM_GUBERLANDCITY.scr:126
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:128
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:131
    ctx:state().index = 0 -- MM_GUBERLANDCITY.scr:134
    while ctx:condition("index < 10") do -- MM_GUBERLANDCITY.scr:136
        ctx:state().npc_id = 0 -- MM_GUBERLANDCITY.scr:138
        if ctx:condition("current_group == Group1") then -- MM_GUBERLANDCITY.scr:140
            ctx:arrayGet("aGroup1", "index", "npc_id") -- MM_GUBERLANDCITY.scr:141
        end -- MM_GUBERLANDCITY.scr:142
        if ctx:condition("current_group == Group2") then -- MM_GUBERLANDCITY.scr:144
            ctx:arrayGet("aGroup2", "index", "npc_id") -- MM_GUBERLANDCITY.scr:145
        end -- MM_GUBERLANDCITY.scr:146
        if ctx:condition("current_group == Group3") then -- MM_GUBERLANDCITY.scr:148
            ctx:arrayGet("aGroup3", "index", "npc_id") -- MM_GUBERLANDCITY.scr:149
        end -- MM_GUBERLANDCITY.scr:150
        if ctx:condition("current_group == Group4") then -- MM_GUBERLANDCITY.scr:152
            ctx:arrayGet("aGroup4", "index", "npc_id") -- MM_GUBERLANDCITY.scr:153
        end -- MM_GUBERLANDCITY.scr:154
        if ctx:condition("npc_id != 0") then -- MM_GUBERLANDCITY.scr:156
            mm9.gosub(script, ctx, "CreateMarker") -- MM_GUBERLANDCITY.scr:157
            mm9.gosub(script, ctx, "GoToLocation") -- MM_GUBERLANDCITY.scr:158
        end -- MM_GUBERLANDCITY.scr:159
        ctx:set("index", "index + 1") -- MM_GUBERLANDCITY.scr:161
    end -- MM_GUBERLANDCITY.scr:162
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:164
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:171
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:174
    ctx:set("current_group", "Group1") -- MM_GUBERLANDCITY.scr:175
    ctx:set("goto_location", "Work") -- MM_GUBERLANDCITY.scr:176
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:177
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:179
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:182
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:185
    ctx:set("current_group", "Group1") -- MM_GUBERLANDCITY.scr:186
    ctx:set("goto_location", "Work") -- MM_GUBERLANDCITY.scr:187
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:188
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:190
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:193
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:196
    ctx:set("current_group", "Group1") -- MM_GUBERLANDCITY.scr:197
    ctx:set("goto_location", "Home") -- MM_GUBERLANDCITY.scr:198
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:199
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:201
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:204
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:207
    ctx:set("current_group", "Group1") -- MM_GUBERLANDCITY.scr:208
    ctx:set("goto_location", "Home") -- MM_GUBERLANDCITY.scr:209
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:210
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:212
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:215
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:218
    ctx:set("current_group", "Group1") -- MM_GUBERLANDCITY.scr:219
    ctx:set("goto_location", "Misc") -- MM_GUBERLANDCITY.scr:220
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:221
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:223
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:226
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:229
    ctx:set("current_group", "Group1") -- MM_GUBERLANDCITY.scr:230
    ctx:set("goto_location", "Misc") -- MM_GUBERLANDCITY.scr:231
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:232
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:234
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:238
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:241
    ctx:set("current_group", "Group2") -- MM_GUBERLANDCITY.scr:242
    ctx:set("goto_location", "Work") -- MM_GUBERLANDCITY.scr:243
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:244
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:246
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:249
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:252
    ctx:set("current_group", "Group2") -- MM_GUBERLANDCITY.scr:253
    ctx:set("goto_location", "Work") -- MM_GUBERLANDCITY.scr:254
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:255
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:257
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:260
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:263
    ctx:set("current_group", "Group2") -- MM_GUBERLANDCITY.scr:264
    ctx:set("goto_location", "Home") -- MM_GUBERLANDCITY.scr:265
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:266
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:268
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:271
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:274
    ctx:set("current_group", "Group2") -- MM_GUBERLANDCITY.scr:275
    ctx:set("goto_location", "Home") -- MM_GUBERLANDCITY.scr:276
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:277
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:279
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:282
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:285
    ctx:set("current_group", "Group2") -- MM_GUBERLANDCITY.scr:286
    ctx:set("goto_location", "Misc") -- MM_GUBERLANDCITY.scr:287
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:288
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:290
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:293
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:296
    ctx:set("current_group", "Group2") -- MM_GUBERLANDCITY.scr:297
    ctx:set("goto_location", "Misc") -- MM_GUBERLANDCITY.scr:298
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:299
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:301
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:304
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:307
    ctx:set("current_group", "Group3") -- MM_GUBERLANDCITY.scr:308
    ctx:set("goto_location", "Work") -- MM_GUBERLANDCITY.scr:309
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:310
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:312
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:315
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:318
    ctx:set("current_group", "Group3") -- MM_GUBERLANDCITY.scr:319
    ctx:set("goto_location", "Work") -- MM_GUBERLANDCITY.scr:320
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:321
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:323
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:326
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:329
    ctx:set("current_group", "Group3") -- MM_GUBERLANDCITY.scr:330
    ctx:set("goto_location", "Home") -- MM_GUBERLANDCITY.scr:331
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:332
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:334
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:337
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:340
    ctx:set("current_group", "Group3") -- MM_GUBERLANDCITY.scr:341
    ctx:set("goto_location", "Home") -- MM_GUBERLANDCITY.scr:342
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:343
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:345
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:348
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:351
    ctx:set("current_group", "Group3") -- MM_GUBERLANDCITY.scr:352
    ctx:set("goto_location", "Misc") -- MM_GUBERLANDCITY.scr:353
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:354
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:356
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:359
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:362
    ctx:set("current_group", "Group3") -- MM_GUBERLANDCITY.scr:363
    ctx:set("goto_location", "Misc") -- MM_GUBERLANDCITY.scr:364
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:365
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:367
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:370
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:373
    ctx:set("current_group", "Group4") -- MM_GUBERLANDCITY.scr:374
    ctx:set("goto_location", "Work") -- MM_GUBERLANDCITY.scr:375
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:376
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:378
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:381
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:384
    ctx:set("current_group", "Group4") -- MM_GUBERLANDCITY.scr:385
    ctx:set("goto_location", "Work") -- MM_GUBERLANDCITY.scr:386
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:387
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:389
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:393
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:396
    ctx:set("current_group", "Group4") -- MM_GUBERLANDCITY.scr:397
    ctx:set("goto_location", "Home") -- MM_GUBERLANDCITY.scr:398
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:399
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:401
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:404
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:407
    ctx:set("current_group", "Group4") -- MM_GUBERLANDCITY.scr:408
    ctx:set("goto_location", "Home") -- MM_GUBERLANDCITY.scr:409
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:410
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:412
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:415
    mm9.gosub(script, ctx, "WarpOff") -- MM_GUBERLANDCITY.scr:418
    ctx:set("current_group", "Group4") -- MM_GUBERLANDCITY.scr:419
    ctx:set("goto_location", "Misc") -- MM_GUBERLANDCITY.scr:420
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:421
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:423
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:426
    mm9.gosub(script, ctx, "WarpOn") -- MM_GUBERLANDCITY.scr:429
    ctx:set("current_group", "Group4") -- MM_GUBERLANDCITY.scr:430
    ctx:set("goto_location", "Misc") -- MM_GUBERLANDCITY.scr:431
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_GUBERLANDCITY.scr:432
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:434
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:442
    ctx:atTime(6, 15, "Group1_GoWork", "Group1_WarpWork") -- MM_GUBERLANDCITY.scr:445
    ctx:atTime(6, 30, "Group2_GoWork", "Group2_WarpWork") -- MM_GUBERLANDCITY.scr:446
    ctx:atTime(6, 45, "Group3_GoWork", "Group3_WarpWork") -- MM_GUBERLANDCITY.scr:447
    ctx:atTime(7, 0, "Group4_GoWork", "Group4_WarpWork") -- MM_GUBERLANDCITY.scr:448
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:450
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:454
    ctx:atTime(18, 0, "Group1_GoHome", "Group1_WarpHome") -- MM_GUBERLANDCITY.scr:457
    ctx:atTime(18, 15, "Group2_GoHome", "Group2_WarpHome") -- MM_GUBERLANDCITY.scr:458
    ctx:atTime(18, 30, "Group3_GoHome", "Group3_WarpHome") -- MM_GUBERLANDCITY.scr:459
    ctx:atTime(18, 45, "Group4_GoHome", "Group4_WarpHome") -- MM_GUBERLANDCITY.scr:460
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:462
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:465
    -- Go Wander off to somewhere
    ctx:atTime(13, 0, "Group1_GoMisc", "Group1_WarpMisc") -- MM_GUBERLANDCITY.scr:469
    ctx:atTime(13, 15, "Group2_GoMisc", "Group2_WarpMisc") -- MM_GUBERLANDCITY.scr:470
    ctx:atTime(13, 30, "Group3_GoMisc", "Group3_WarpMisc") -- MM_GUBERLANDCITY.scr:471
    ctx:atTime(13, 45, "Group4_GoMisc", "Group4_WarpMisc") -- MM_GUBERLANDCITY.scr:472
    -- Go Back to work
    ctx:atTime(15, 0, "Group1_GoWork", "Group1_WarpWork") -- MM_GUBERLANDCITY.scr:475
    ctx:atTime(15, 15, "Group2_GoWork", "Group2_WarpWork") -- MM_GUBERLANDCITY.scr:476
    ctx:atTime(15, 30, "Group3_GoWork", "Group3_WarpWork") -- MM_GUBERLANDCITY.scr:477
    ctx:atTime(15, 45, "Group4_GoWork", "Group4_WarpWork") -- MM_GUBERLANDCITY.scr:478
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:480
end

script.labels["InitArrays"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:488
    ctx:state().index = 0 -- MM_GUBERLANDCITY.scr:491
    while ctx:condition("index < 10") do -- MM_GUBERLANDCITY.scr:492
        ctx:arrayPut("aGroup1", "index", 0) -- MM_GUBERLANDCITY.scr:493
        ctx:arrayPut("aGroup2", "index", 0) -- MM_GUBERLANDCITY.scr:494
        ctx:arrayPut("aGroup3", "index", 0) -- MM_GUBERLANDCITY.scr:495
        ctx:arrayPut("aGroup4", "index", 0) -- MM_GUBERLANDCITY.scr:496
        ctx:set("index", "index + 1") -- MM_GUBERLANDCITY.scr:497
    end -- MM_GUBERLANDCITY.scr:498
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:500
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:504
    -- Mata Abyomi					( 148 )
    ctx:arrayPut("aGroup1", 0, 148) -- MM_GUBERLANDCITY.scr:508
    -- Mirek Mazatle				( 152 )
    ctx:arrayPut("aGroup1", 1, 152) -- MM_GUBERLANDCITY.scr:511
    -- Davin the Ample				( 165 )
    ctx:arrayPut("aGroup1", 2, 165) -- MM_GUBERLANDCITY.scr:514
    -- Gregusk Mazo				( 168 )
    ctx:arrayPut("aGroup1", 3, 168) -- MM_GUBERLANDCITY.scr:517
    -- Rya Fremi					( 173 )
    ctx:arrayPut("aGroup1", 4, 173) -- MM_GUBERLANDCITY.scr:520
    -- Eyjolf Bjolfssen			( 156 ) <<< REMOVED >>>
    -- ArrayPut aGroup1,2,156
    -- Arni Brokkssen				( 160 ) <<< REMOVED >>>
    -- ArrayPut aGroup1,3,160
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:528
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:531
    -- Bragi the Toothloose		( 149 )
    ctx:arrayPut("aGroup2", 0, 149) -- MM_GUBERLANDCITY.scr:535
    -- Gudny the Nose				( 153 )
    ctx:arrayPut("aGroup2", 1, 153) -- MM_GUBERLANDCITY.scr:538
    -- Fyrie the Forgettable		( 162 )
    ctx:arrayPut("aGroup2", 2, 162) -- MM_GUBERLANDCITY.scr:541
    -- Denby Badbreath				( 166 )
    ctx:arrayPut("aGroup2", 3, 166) -- MM_GUBERLANDCITY.scr:544
    -- Peterk Olin					( 170 )
    ctx:arrayPut("aGroup2", 4, 170) -- MM_GUBERLANDCITY.scr:547
    -- Hrapp Tjorvissen			( 174 )
    ctx:arrayPut("aGroup2", 5, 174) -- MM_GUBERLANDCITY.scr:550
    -- Aki the King				( 157 ) <<< REMOVED >>>
    -- ArrayPut aGroup2,2,157
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:556
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:559
    -- Aso Stinkshirt				( 154 )
    ctx:arrayPut("aGroup3", 0, 154) -- MM_GUBERLANDCITY.scr:563
    -- Gabriel Dullard				( 163 )
    ctx:arrayPut("aGroup3", 1, 163) -- MM_GUBERLANDCITY.scr:567
    -- Treshi Yatol				( 171 )
    ctx:arrayPut("aGroup3", 2, 171) -- MM_GUBERLANDCITY.scr:570
    -- Scandian the Long-tongued	( 150 ) <<< REMOVED >>>
    -- ArrayPut aGroup3,0,150
    -- Cassidy A'Dorad				( 158 ) <<< REMOVED >>>
    -- ArrayPut aGroup3,2,158
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:579
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:582
    -- Ryan the Simpleton			( 164 )
    ctx:arrayPut("aGroup4", 0, 164) -- MM_GUBERLANDCITY.scr:586
    -- Lina Friggdotir				( 167 )
    ctx:arrayPut("aGroup4", 1, 167) -- MM_GUBERLANDCITY.scr:589
    -- Bohus Kinar					( 172 )
    ctx:arrayPut("aGroup4", 2, 172) -- MM_GUBERLANDCITY.scr:592
    -- Broccan A'Norta a'bre		( 151 ) <<< REMOVED >>>
    -- ArrayPut aGroup4,3, 151
    -- Darby Etzelessen			( 155 ) <<< REMOVED >>>
    -- ArrayPut aGroup4,4, 155
    -- Elvis						( 159 ) <<< REMOVED >>>
    -- ArrayPut aGroup4,5, 159
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:605
end

script.labels["Init"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:608
    mm9.gosub(script, ctx, "InitArrays") -- MM_GUBERLANDCITY.scr:610
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_GUBERLANDCITY.scr:612
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_GUBERLANDCITY.scr:613
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_GUBERLANDCITY.scr:614
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_GUBERLANDCITY.scr:615
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_GUBERLANDCITY.scr:617
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_GUBERLANDCITY.scr:618
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_GUBERLANDCITY.scr:619
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:621
end

script.labels["Main"] = function(ctx)
    -- MM_GUBERLANDCITY.scr:624
    mm9.gosub(script, ctx, "Init") -- MM_GUBERLANDCITY.scr:626
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_GUBERLANDCITY.scr:627
    do return ctx:exit("") end -- MM_GUBERLANDCITY.scr:629
end

return script
