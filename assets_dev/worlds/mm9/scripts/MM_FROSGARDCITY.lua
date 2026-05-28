-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_FROSGARDCITY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 42, path = "Globals.inc" }

-- MM_FrosgardCity.scr
-- Jim Craig
-- Mundane Task List for Frosgard City
-- Current NPCs
-- Gossip NPCs
-- Flosi Stickpoker	( 217 )
-- Pules Haji			( 218 )
-- Tjorvi Duartrssen	( 219 )
-- Halfdan Hagenessen	( 220 )
-- Ambient NPCs
-- Heikkinen Bloodhands	( 222 )
-- Thorkel Cortssen		( 223 )
-- Canute Gardrarssen		( 224 )
-- Brand Borssen			( 225 )
-- Eitri Haukssen			( 226 )
-- Asdis Brunidotir		( 227 )
-- Sigrid Tryygvadotir		( 228 )
-- Eyjolf Knutssen			( 229 )
-- Hroald Etzelssen		( 230 )
-- Tadita Akin				( 231 )
-- Hanta Fenku				( 232 )
-- Fionnaghal A'Lanth		( 236 )
-- Teacher NPCs
-- Eachann A'Mor			( 237 )
-- Fogartach A'Velsi		( 234 )
-- Derbforgaill A'Norta a'meich	( 235 )
-- Hervor Etzeldotir		( 398 )
-- Frode Herjolfssen		( 399 )
-- Hagen Hrrappssen		( 401 )
-- Lansa Akin				( 233 )
-- Dymphna A'Klindor		( 402 )
-- Erin A'Feslo			( 403 )
script.labels["OnArrived"] = function(ctx)
    -- MM_FROSGARDCITY.scr:73
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:76
end

script.labels["WarpOn"] = function(ctx)
    -- MM_FROSGARDCITY.scr:79
    ctx:command("bwarp", "= TRUE") -- MM_FROSGARDCITY.scr:82
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:84
end

script.labels["WarpOff"] = function(ctx)
    -- MM_FROSGARDCITY.scr:87
    ctx:command("bwarp", "= FALSE") -- MM_FROSGARDCITY.scr:90
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:92
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_FROSGARDCITY.scr:95
    if ctx:condition("goto_location == Work") then -- MM_FROSGARDCITY.scr:98
        ctx:command("goto_marker", "= marker_work + npc_id") -- MM_FROSGARDCITY.scr:99
    end -- MM_FROSGARDCITY.scr:100
    if ctx:condition("goto_location == Home") then -- MM_FROSGARDCITY.scr:102
        ctx:command("goto_marker", "= marker_home + npc_id") -- MM_FROSGARDCITY.scr:103
    end -- MM_FROSGARDCITY.scr:104
    if ctx:condition("goto_location == Misc") then -- MM_FROSGARDCITY.scr:106
        ctx:command("goto_marker", "= marker_misc + npc_id") -- MM_FROSGARDCITY.scr:107
    end -- MM_FROSGARDCITY.scr:108
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:110
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_FROSGARDCITY.scr:113
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_FROSGARDCITY.scr:116
    ctx:command("setstat", "npc_object, PARAM, goto_marker") -- MM_FROSGARDCITY.scr:118
    if ctx:condition("bWarp == FALSE") then -- MM_FROSGARDCITY.scr:120
        ctx:trigger("npc_object", "GoToLoc") -- MM_FROSGARDCITY.scr:121
    end -- MM_FROSGARDCITY.scr:122
    if ctx:condition("bWarp == TRUE") then -- MM_FROSGARDCITY.scr:124
        ctx:trigger("npc_object", "WarpToLoc") -- MM_FROSGARDCITY.scr:125
    end -- MM_FROSGARDCITY.scr:126
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:128
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_FROSGARDCITY.scr:131
    ctx:command("index", "= 0") -- MM_FROSGARDCITY.scr:134
    while ctx:condition("index < 10") do -- MM_FROSGARDCITY.scr:136
        ctx:command("npc_id", "= 0") -- MM_FROSGARDCITY.scr:138
        if ctx:condition("current_group == Group1") then -- MM_FROSGARDCITY.scr:140
            ctx:command("arrayget", "aGroup1,index,npc_id") -- MM_FROSGARDCITY.scr:141
        end -- MM_FROSGARDCITY.scr:142
        if ctx:condition("current_group == Group2") then -- MM_FROSGARDCITY.scr:144
            ctx:command("arrayget", "aGroup2,index,npc_id") -- MM_FROSGARDCITY.scr:145
        end -- MM_FROSGARDCITY.scr:146
        if ctx:condition("current_group == Group3") then -- MM_FROSGARDCITY.scr:148
            ctx:command("arrayget", "aGroup3,index,npc_id") -- MM_FROSGARDCITY.scr:149
        end -- MM_FROSGARDCITY.scr:150
        if ctx:condition("current_group == Group4") then -- MM_FROSGARDCITY.scr:152
            ctx:command("arrayget", "aGroup4,index,npc_id") -- MM_FROSGARDCITY.scr:153
        end -- MM_FROSGARDCITY.scr:154
        if ctx:condition("npc_id != 0") then -- MM_FROSGARDCITY.scr:156
            mm9.gosub(script, ctx, "CreateMarker") -- MM_FROSGARDCITY.scr:157
            mm9.gosub(script, ctx, "GoToLocation") -- MM_FROSGARDCITY.scr:158
        end -- MM_FROSGARDCITY.scr:159
        ctx:command("index", "= index + 1") -- MM_FROSGARDCITY.scr:161
    end -- MM_FROSGARDCITY.scr:162
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:164
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_FROSGARDCITY.scr:171
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:174
    ctx:command("current_group", "= Group1") -- MM_FROSGARDCITY.scr:175
    ctx:command("goto_location", "= Work") -- MM_FROSGARDCITY.scr:176
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:177
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:179
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_FROSGARDCITY.scr:182
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:185
    ctx:command("current_group", "= Group1") -- MM_FROSGARDCITY.scr:186
    ctx:command("goto_location", "= Work") -- MM_FROSGARDCITY.scr:187
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:188
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:190
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_FROSGARDCITY.scr:193
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:196
    ctx:command("current_group", "= Group1") -- MM_FROSGARDCITY.scr:197
    ctx:command("goto_location", "= Home") -- MM_FROSGARDCITY.scr:198
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:199
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:201
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_FROSGARDCITY.scr:204
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:207
    ctx:command("current_group", "= Group1") -- MM_FROSGARDCITY.scr:208
    ctx:command("goto_location", "= Home") -- MM_FROSGARDCITY.scr:209
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:210
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:212
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_FROSGARDCITY.scr:215
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:218
    ctx:command("current_group", "= Group1") -- MM_FROSGARDCITY.scr:219
    ctx:command("goto_location", "= Misc") -- MM_FROSGARDCITY.scr:220
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:221
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:223
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_FROSGARDCITY.scr:226
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:229
    ctx:command("current_group", "= Group1") -- MM_FROSGARDCITY.scr:230
    ctx:command("goto_location", "= Misc") -- MM_FROSGARDCITY.scr:231
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:232
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:234
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_FROSGARDCITY.scr:238
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:241
    ctx:command("current_group", "= Group2") -- MM_FROSGARDCITY.scr:242
    ctx:command("goto_location", "= Work") -- MM_FROSGARDCITY.scr:243
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:244
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:246
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_FROSGARDCITY.scr:249
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:252
    ctx:command("current_group", "= Group2") -- MM_FROSGARDCITY.scr:253
    ctx:command("goto_location", "= Work") -- MM_FROSGARDCITY.scr:254
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:255
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:257
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_FROSGARDCITY.scr:260
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:263
    ctx:command("current_group", "= Group2") -- MM_FROSGARDCITY.scr:264
    ctx:command("goto_location", "= Home") -- MM_FROSGARDCITY.scr:265
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:266
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:268
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_FROSGARDCITY.scr:271
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:274
    ctx:command("current_group", "= Group2") -- MM_FROSGARDCITY.scr:275
    ctx:command("goto_location", "= Home") -- MM_FROSGARDCITY.scr:276
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:277
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:279
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_FROSGARDCITY.scr:282
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:285
    ctx:command("current_group", "= Group2") -- MM_FROSGARDCITY.scr:286
    ctx:command("goto_location", "= Misc") -- MM_FROSGARDCITY.scr:287
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:288
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:290
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_FROSGARDCITY.scr:293
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:296
    ctx:command("current_group", "= Group2") -- MM_FROSGARDCITY.scr:297
    ctx:command("goto_location", "= Misc") -- MM_FROSGARDCITY.scr:298
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:299
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:301
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_FROSGARDCITY.scr:304
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:307
    ctx:command("current_group", "= Group3") -- MM_FROSGARDCITY.scr:308
    ctx:command("goto_location", "= Work") -- MM_FROSGARDCITY.scr:309
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:310
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:312
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_FROSGARDCITY.scr:315
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:318
    ctx:command("current_group", "= Group3") -- MM_FROSGARDCITY.scr:319
    ctx:command("goto_location", "= Work") -- MM_FROSGARDCITY.scr:320
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:321
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:323
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_FROSGARDCITY.scr:326
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:329
    ctx:command("current_group", "= Group3") -- MM_FROSGARDCITY.scr:330
    ctx:command("goto_location", "= Home") -- MM_FROSGARDCITY.scr:331
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:332
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:334
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_FROSGARDCITY.scr:337
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:340
    ctx:command("current_group", "= Group3") -- MM_FROSGARDCITY.scr:341
    ctx:command("goto_location", "= Home") -- MM_FROSGARDCITY.scr:342
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:343
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:345
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_FROSGARDCITY.scr:348
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:351
    ctx:command("current_group", "= Group3") -- MM_FROSGARDCITY.scr:352
    ctx:command("goto_location", "= Misc") -- MM_FROSGARDCITY.scr:353
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:354
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:356
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_FROSGARDCITY.scr:359
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:362
    ctx:command("current_group", "= Group3") -- MM_FROSGARDCITY.scr:363
    ctx:command("goto_location", "= Misc") -- MM_FROSGARDCITY.scr:364
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:365
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:367
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_FROSGARDCITY.scr:370
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:373
    ctx:command("current_group", "= Group4") -- MM_FROSGARDCITY.scr:374
    ctx:command("goto_location", "= Work") -- MM_FROSGARDCITY.scr:375
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:376
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:378
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_FROSGARDCITY.scr:381
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:384
    ctx:command("current_group", "= Group4") -- MM_FROSGARDCITY.scr:385
    ctx:command("goto_location", "= Work") -- MM_FROSGARDCITY.scr:386
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:387
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:389
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_FROSGARDCITY.scr:393
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:396
    ctx:command("current_group", "= Group4") -- MM_FROSGARDCITY.scr:397
    ctx:command("goto_location", "= Home") -- MM_FROSGARDCITY.scr:398
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:399
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:401
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_FROSGARDCITY.scr:404
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:407
    ctx:command("current_group", "= Group4") -- MM_FROSGARDCITY.scr:408
    ctx:command("goto_location", "= Home") -- MM_FROSGARDCITY.scr:409
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:410
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:412
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_FROSGARDCITY.scr:415
    mm9.gosub(script, ctx, "WarpOff") -- MM_FROSGARDCITY.scr:418
    ctx:command("current_group", "= Group4") -- MM_FROSGARDCITY.scr:419
    ctx:command("goto_location", "= Misc") -- MM_FROSGARDCITY.scr:420
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:421
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:423
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_FROSGARDCITY.scr:426
    mm9.gosub(script, ctx, "WarpOn") -- MM_FROSGARDCITY.scr:429
    ctx:command("current_group", "= Group4") -- MM_FROSGARDCITY.scr:430
    ctx:command("goto_location", "= Misc") -- MM_FROSGARDCITY.scr:431
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_FROSGARDCITY.scr:432
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:434
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_FROSGARDCITY.scr:442
    ctx:command("@m", "6 : 15 Group1_GoWork Group1_WarpWork") -- MM_FROSGARDCITY.scr:445
    ctx:command("@m", "6 : 30 Group2_GoWork Group2_WarpWork") -- MM_FROSGARDCITY.scr:446
    ctx:command("@m", "6 : 45 Group3_GoWork Group3_WarpWork") -- MM_FROSGARDCITY.scr:447
    ctx:command("@m", "7 : 00 Group4_GoWork Group4_WarpWork") -- MM_FROSGARDCITY.scr:448
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:450
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_FROSGARDCITY.scr:454
    ctx:command("@m", "18 : 00 Group1_GoHome Group1_WarpHome") -- MM_FROSGARDCITY.scr:457
    ctx:command("@m", "18 : 15 Group2_GoHome Group2_WarpHome") -- MM_FROSGARDCITY.scr:458
    ctx:command("@m", "18 : 30 Group3_GoHome Group3_WarpHome") -- MM_FROSGARDCITY.scr:459
    ctx:command("@m", "18 : 45 Group4_GoHome Group4_WarpHome") -- MM_FROSGARDCITY.scr:460
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:462
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_FROSGARDCITY.scr:465
    -- Go Wander off to somewhere
    ctx:command("@m", "13 : 00 Group1_GoMisc Group1_WarpMisc") -- MM_FROSGARDCITY.scr:469
    ctx:command("@m", "13 : 15 Group2_GoMisc Group2_WarpMisc") -- MM_FROSGARDCITY.scr:470
    ctx:command("@m", "13 : 30 Group3_GoMisc Group3_WarpMisc") -- MM_FROSGARDCITY.scr:471
    ctx:command("@m", "13 : 45 Group4_GoMisc Group4_WarpMisc") -- MM_FROSGARDCITY.scr:472
    -- Go Back to work
    ctx:command("@m", "15 : 00 Group1_GoWork Group1_WarpWork") -- MM_FROSGARDCITY.scr:475
    ctx:command("@m", "15 : 15 Group2_GoWork Group2_WarpWork") -- MM_FROSGARDCITY.scr:476
    ctx:command("@m", "15 : 30 Group3_GoWork Group3_WarpWork") -- MM_FROSGARDCITY.scr:477
    ctx:command("@m", "15 : 45 Group4_GoWork Group4_WarpWork") -- MM_FROSGARDCITY.scr:478
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:480
end

script.labels["InitArrays"] = function(ctx)
    -- MM_FROSGARDCITY.scr:488
    ctx:command("index", "= 0") -- MM_FROSGARDCITY.scr:491
    while ctx:condition("index < 10") do -- MM_FROSGARDCITY.scr:492
        ctx:command("arrayput", "aGroup1, index , 0") -- MM_FROSGARDCITY.scr:493
        ctx:command("arrayput", "aGroup2, index , 0") -- MM_FROSGARDCITY.scr:494
        ctx:command("arrayput", "aGroup3, index , 0") -- MM_FROSGARDCITY.scr:495
        ctx:command("arrayput", "aGroup4, index , 0") -- MM_FROSGARDCITY.scr:496
        ctx:command("index", "= index + 1") -- MM_FROSGARDCITY.scr:497
    end -- MM_FROSGARDCITY.scr:498
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:500
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_FROSGARDCITY.scr:504
    -- Flosi Stickpoker	( 217 )
    ctx:command("arrayput", "aGroup1,0,217") -- MM_FROSGARDCITY.scr:508
    -- Heikkinen Bloodhands	( 222 )
    ctx:command("arrayput", "aGroup1,1,222") -- MM_FROSGARDCITY.scr:511
    -- Brand Borssen			( 225 )
    ctx:command("arrayput", "aGroup1,2,225") -- MM_FROSGARDCITY.scr:514
    -- Eyjolf Knutssen			( 229 )
    ctx:command("arrayput", "aGroup1,3,229") -- MM_FROSGARDCITY.scr:517
    -- Hanta Fenku				( 232 )
    ctx:command("arrayput", "aGroup1,4,232") -- MM_FROSGARDCITY.scr:520
    -- Fogartach A'Velsi		( 234 )
    ctx:command("arrayput", "aGroup1,5,234") -- MM_FROSGARDCITY.scr:523
    -- Frode Herjolfssen		( 399 )
    ctx:command("arrayput", "aGroup1,6,399") -- MM_FROSGARDCITY.scr:526
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:528
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_FROSGARDCITY.scr:531
    -- Pules Haji			( 218 )
    ctx:command("arrayput", "aGroup2,0,218") -- MM_FROSGARDCITY.scr:535
    -- Heikkinen Bloodhands	( 222 )
    ctx:command("arrayput", "aGroup2,1,222") -- MM_FROSGARDCITY.scr:538
    -- Eitri Haukssen			( 226 )
    ctx:command("arrayput", "aGroup2,2,226") -- MM_FROSGARDCITY.scr:541
    -- Hroald Etzelssen		( 230 )
    ctx:command("arrayput", "aGroup2,3,230") -- MM_FROSGARDCITY.scr:544
    -- Fionnaghal A'Lanth		( 236 )
    ctx:command("arrayput", "aGroup2,4,236") -- MM_FROSGARDCITY.scr:547
    -- Derbforgaill A'Norta a'meich	( 235 )
    ctx:command("arrayput", "aGroup2,5,235") -- MM_FROSGARDCITY.scr:550
    -- Hagen Hrrappssen		( 401 )
    ctx:command("arrayput", "aGroup2,6,401") -- MM_FROSGARDCITY.scr:553
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:556
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_FROSGARDCITY.scr:559
    -- Tjorvi Duartrssen	( 219 )
    ctx:command("arrayput", "aGroup3,0,219") -- MM_FROSGARDCITY.scr:563
    -- Thorkel Cortssen		( 223 )
    ctx:command("arrayput", "aGroup3,1,223") -- MM_FROSGARDCITY.scr:566
    -- Asdis Brunidotir		( 227 )
    ctx:command("arrayput", "aGroup3,2,227") -- MM_FROSGARDCITY.scr:569
    -- Lansa Akin				( 233 )
    ctx:command("arrayput", "aGroup3,3,233") -- MM_FROSGARDCITY.scr:572
    -- Erin A'Feslo			( 403 )
    ctx:command("arrayput", "aGroup3,4,403") -- MM_FROSGARDCITY.scr:575
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:578
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_FROSGARDCITY.scr:581
    -- Halfdan Hagenessen	( 220 )
    ctx:command("arrayput", "aGroup4,0,220") -- MM_FROSGARDCITY.scr:585
    -- Canute Gardrarssen		( 224 )
    ctx:command("arrayput", "aGroup4,1,224") -- MM_FROSGARDCITY.scr:588
    -- Sigrid Tryygvadotir		( 228 )
    ctx:command("arrayput", "aGroup4,2,228") -- MM_FROSGARDCITY.scr:591
    -- Tadita Akin				( 231 )
    ctx:command("arrayput", "aGroup4,3,231") -- MM_FROSGARDCITY.scr:594
    -- Eachann A'Mor			( 237 )
    ctx:command("arrayput", "aGroup4,4,237") -- MM_FROSGARDCITY.scr:597
    -- Hervor Etzeldotir		( 398 )
    ctx:command("arrayput", "aGroup4,5,398") -- MM_FROSGARDCITY.scr:600
    -- Dymphna A'Klindor		( 402 )
    ctx:command("arrayput", "aGroup4,6,402") -- MM_FROSGARDCITY.scr:603
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:606
end

script.labels["Init"] = function(ctx)
    -- MM_FROSGARDCITY.scr:610
    mm9.gosub(script, ctx, "InitArrays") -- MM_FROSGARDCITY.scr:612
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_FROSGARDCITY.scr:614
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_FROSGARDCITY.scr:615
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_FROSGARDCITY.scr:616
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_FROSGARDCITY.scr:617
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_FROSGARDCITY.scr:619
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_FROSGARDCITY.scr:620
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_FROSGARDCITY.scr:621
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:623
end

script.labels["Main"] = function(ctx)
    -- MM_FROSGARDCITY.scr:626
    mm9.gosub(script, ctx, "Init") -- MM_FROSGARDCITY.scr:628
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_FROSGARDCITY.scr:629
    do return ctx:exit("") end -- MM_FROSGARDCITY.scr:631
end

return script
