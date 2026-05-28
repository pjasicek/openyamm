-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_ARSLEGAARD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "Globals.inc" }

-- MM_Arslegaard.scr
-- Jim Craig
-- Mundane Task List for Arslegaard
script.labels["OnArrived"] = function(ctx)
    -- MM_ARSLEGAARD.scr:39
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:42
end

script.labels["WarpOn"] = function(ctx)
    -- MM_ARSLEGAARD.scr:45
    ctx:command("bwarp", "= TRUE") -- MM_ARSLEGAARD.scr:48
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:50
end

script.labels["WarpOff"] = function(ctx)
    -- MM_ARSLEGAARD.scr:53
    ctx:command("bwarp", "= FALSE") -- MM_ARSLEGAARD.scr:56
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:58
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_ARSLEGAARD.scr:61
    if ctx:condition("goto_location == Work") then -- MM_ARSLEGAARD.scr:64
        ctx:command("goto_marker", "= marker_work + npc_id") -- MM_ARSLEGAARD.scr:65
    end -- MM_ARSLEGAARD.scr:66
    if ctx:condition("goto_location == Home") then -- MM_ARSLEGAARD.scr:68
        ctx:command("goto_marker", "= marker_home + npc_id") -- MM_ARSLEGAARD.scr:69
    end -- MM_ARSLEGAARD.scr:70
    if ctx:condition("goto_location == Misc") then -- MM_ARSLEGAARD.scr:72
        ctx:command("goto_marker", "= marker_misc + npc_id") -- MM_ARSLEGAARD.scr:73
    end -- MM_ARSLEGAARD.scr:74
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:76
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_ARSLEGAARD.scr:79
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_ARSLEGAARD.scr:82
    ctx:command("setstat", "npc_object, PARAM, goto_marker") -- MM_ARSLEGAARD.scr:84
    if ctx:condition("bWarp == FALSE") then -- MM_ARSLEGAARD.scr:86
        ctx:trigger("npc_object", "GoToLoc") -- MM_ARSLEGAARD.scr:87
    end -- MM_ARSLEGAARD.scr:88
    if ctx:condition("bWarp == TRUE") then -- MM_ARSLEGAARD.scr:90
        ctx:trigger("npc_object", "WarpToLoc") -- MM_ARSLEGAARD.scr:91
    end -- MM_ARSLEGAARD.scr:92
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:94
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_ARSLEGAARD.scr:97
    ctx:command("index", "= 0") -- MM_ARSLEGAARD.scr:100
    while ctx:condition("index < 10") do -- MM_ARSLEGAARD.scr:102
        ctx:command("npc_id", "= 0") -- MM_ARSLEGAARD.scr:104
        if ctx:condition("current_group == Group1") then -- MM_ARSLEGAARD.scr:106
            ctx:command("arrayget", "aGroup1,index,npc_id") -- MM_ARSLEGAARD.scr:107
        end -- MM_ARSLEGAARD.scr:108
        if ctx:condition("current_group == Group2") then -- MM_ARSLEGAARD.scr:110
            ctx:command("arrayget", "aGroup2,index,npc_id") -- MM_ARSLEGAARD.scr:111
        end -- MM_ARSLEGAARD.scr:112
        if ctx:condition("current_group == Group3") then -- MM_ARSLEGAARD.scr:114
            ctx:command("arrayget", "aGroup3,index,npc_id") -- MM_ARSLEGAARD.scr:115
        end -- MM_ARSLEGAARD.scr:116
        if ctx:condition("current_group == Group4") then -- MM_ARSLEGAARD.scr:118
            ctx:command("arrayget", "aGroup4,index,npc_id") -- MM_ARSLEGAARD.scr:119
        end -- MM_ARSLEGAARD.scr:120
        if ctx:condition("npc_id != 0") then -- MM_ARSLEGAARD.scr:122
            mm9.gosub(script, ctx, "CreateMarker") -- MM_ARSLEGAARD.scr:123
            mm9.gosub(script, ctx, "GoToLocation") -- MM_ARSLEGAARD.scr:124
        end -- MM_ARSLEGAARD.scr:125
        ctx:command("index", "= index + 1") -- MM_ARSLEGAARD.scr:127
    end -- MM_ARSLEGAARD.scr:128
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:130
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_ARSLEGAARD.scr:137
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:140
    ctx:command("current_group", "= Group1") -- MM_ARSLEGAARD.scr:141
    ctx:command("goto_location", "= Work") -- MM_ARSLEGAARD.scr:142
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:143
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:145
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_ARSLEGAARD.scr:148
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:151
    ctx:command("current_group", "= Group1") -- MM_ARSLEGAARD.scr:152
    ctx:command("goto_location", "= Work") -- MM_ARSLEGAARD.scr:153
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:154
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:156
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_ARSLEGAARD.scr:159
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:162
    ctx:command("current_group", "= Group1") -- MM_ARSLEGAARD.scr:163
    ctx:command("goto_location", "= Home") -- MM_ARSLEGAARD.scr:164
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:165
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:167
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_ARSLEGAARD.scr:170
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:173
    ctx:command("current_group", "= Group1") -- MM_ARSLEGAARD.scr:174
    ctx:command("goto_location", "= Home") -- MM_ARSLEGAARD.scr:175
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:176
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:178
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_ARSLEGAARD.scr:181
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:184
    ctx:command("current_group", "= Group1") -- MM_ARSLEGAARD.scr:185
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGAARD.scr:186
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:187
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:189
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_ARSLEGAARD.scr:192
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:195
    ctx:command("current_group", "= Group1") -- MM_ARSLEGAARD.scr:196
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGAARD.scr:197
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:198
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:200
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_ARSLEGAARD.scr:204
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:207
    ctx:command("current_group", "= Group2") -- MM_ARSLEGAARD.scr:208
    ctx:command("goto_location", "= Work") -- MM_ARSLEGAARD.scr:209
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:210
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:212
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_ARSLEGAARD.scr:215
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:218
    ctx:command("current_group", "= Group2") -- MM_ARSLEGAARD.scr:219
    ctx:command("goto_location", "= Work") -- MM_ARSLEGAARD.scr:220
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:221
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:223
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_ARSLEGAARD.scr:226
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:229
    ctx:command("current_group", "= Group2") -- MM_ARSLEGAARD.scr:230
    ctx:command("goto_location", "= Home") -- MM_ARSLEGAARD.scr:231
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:232
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:234
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_ARSLEGAARD.scr:237
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:240
    ctx:command("current_group", "= Group2") -- MM_ARSLEGAARD.scr:241
    ctx:command("goto_location", "= Home") -- MM_ARSLEGAARD.scr:242
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:243
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:245
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_ARSLEGAARD.scr:248
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:251
    ctx:command("current_group", "= Group2") -- MM_ARSLEGAARD.scr:252
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGAARD.scr:253
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:254
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:256
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_ARSLEGAARD.scr:259
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:262
    ctx:command("current_group", "= Group2") -- MM_ARSLEGAARD.scr:263
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGAARD.scr:264
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:265
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:267
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_ARSLEGAARD.scr:270
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:273
    ctx:command("current_group", "= Group3") -- MM_ARSLEGAARD.scr:274
    ctx:command("goto_location", "= Work") -- MM_ARSLEGAARD.scr:275
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:276
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:278
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_ARSLEGAARD.scr:281
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:284
    ctx:command("current_group", "= Group3") -- MM_ARSLEGAARD.scr:285
    ctx:command("goto_location", "= Work") -- MM_ARSLEGAARD.scr:286
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:287
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:289
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_ARSLEGAARD.scr:292
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:295
    ctx:command("current_group", "= Group3") -- MM_ARSLEGAARD.scr:296
    ctx:command("goto_location", "= Home") -- MM_ARSLEGAARD.scr:297
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:298
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:300
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_ARSLEGAARD.scr:303
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:306
    ctx:command("current_group", "= Group3") -- MM_ARSLEGAARD.scr:307
    ctx:command("goto_location", "= Home") -- MM_ARSLEGAARD.scr:308
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:309
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:311
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_ARSLEGAARD.scr:314
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:317
    ctx:command("current_group", "= Group3") -- MM_ARSLEGAARD.scr:318
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGAARD.scr:319
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:320
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:322
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_ARSLEGAARD.scr:325
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:328
    ctx:command("current_group", "= Group3") -- MM_ARSLEGAARD.scr:329
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGAARD.scr:330
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:331
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:333
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_ARSLEGAARD.scr:336
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:339
    ctx:command("current_group", "= Group4") -- MM_ARSLEGAARD.scr:340
    ctx:command("goto_location", "= Work") -- MM_ARSLEGAARD.scr:341
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:342
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:344
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_ARSLEGAARD.scr:347
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:350
    ctx:command("current_group", "= Group4") -- MM_ARSLEGAARD.scr:351
    ctx:command("goto_location", "= Work") -- MM_ARSLEGAARD.scr:352
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:353
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:355
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_ARSLEGAARD.scr:359
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:362
    ctx:command("current_group", "= Group4") -- MM_ARSLEGAARD.scr:363
    ctx:command("goto_location", "= Home") -- MM_ARSLEGAARD.scr:364
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:365
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:367
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_ARSLEGAARD.scr:370
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:373
    ctx:command("current_group", "= Group4") -- MM_ARSLEGAARD.scr:374
    ctx:command("goto_location", "= Home") -- MM_ARSLEGAARD.scr:375
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:376
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:378
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_ARSLEGAARD.scr:381
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGAARD.scr:384
    ctx:command("current_group", "= Group4") -- MM_ARSLEGAARD.scr:385
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGAARD.scr:386
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:387
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:389
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_ARSLEGAARD.scr:392
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGAARD.scr:395
    ctx:command("current_group", "= Group4") -- MM_ARSLEGAARD.scr:396
    ctx:command("goto_location", "= Misc") -- MM_ARSLEGAARD.scr:397
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGAARD.scr:398
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:400
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_ARSLEGAARD.scr:408
    ctx:command("@m", "6 : 15 Group1_GoWork Group1_WarpWork") -- MM_ARSLEGAARD.scr:411
    ctx:command("@m", "6 : 30 Group2_GoWork Group2_WarpWork") -- MM_ARSLEGAARD.scr:412
    ctx:command("@m", "6 : 45 Group3_GoWork Group3_WarpWork") -- MM_ARSLEGAARD.scr:413
    ctx:command("@m", "7 : 00 Group4_GoWork Group4_WarpWork") -- MM_ARSLEGAARD.scr:414
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:416
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_ARSLEGAARD.scr:420
    ctx:command("@m", "18 : 00 Group1_GoHome Group1_WarpHome") -- MM_ARSLEGAARD.scr:423
    ctx:command("@m", "18 : 15 Group2_GoHome Group2_WarpHome") -- MM_ARSLEGAARD.scr:424
    ctx:command("@m", "18 : 30 Group3_GoHome Group3_WarpHome") -- MM_ARSLEGAARD.scr:425
    ctx:command("@m", "18 : 45 Group4_GoHome Group4_WarpHome") -- MM_ARSLEGAARD.scr:426
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:428
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_ARSLEGAARD.scr:431
    -- Go Wander off to somewhere
    ctx:command("@m", "13 : 00 Group1_GoMisc Group1_WarpMisc") -- MM_ARSLEGAARD.scr:435
    ctx:command("@m", "13 : 15 Group2_GoMisc Group2_WarpMisc") -- MM_ARSLEGAARD.scr:436
    ctx:command("@m", "13 : 30 Group3_GoMisc Group3_WarpMisc") -- MM_ARSLEGAARD.scr:437
    ctx:command("@m", "13 : 45 Group4_GoMisc Group4_WarpMisc") -- MM_ARSLEGAARD.scr:438
    -- Go Back to work
    ctx:command("@m", "15 : 00 Group1_GoWork Group1_WarpWork") -- MM_ARSLEGAARD.scr:441
    ctx:command("@m", "15 : 15 Group2_GoWork Group2_WarpWork") -- MM_ARSLEGAARD.scr:442
    ctx:command("@m", "15 : 30 Group3_GoWork Group3_WarpWork") -- MM_ARSLEGAARD.scr:443
    ctx:command("@m", "15 : 45 Group4_GoWork Group4_WarpWork") -- MM_ARSLEGAARD.scr:444
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:446
end

script.labels["InitArrays"] = function(ctx)
    -- MM_ARSLEGAARD.scr:454
    ctx:command("index", "= 0") -- MM_ARSLEGAARD.scr:457
    while ctx:condition("index < 10") do -- MM_ARSLEGAARD.scr:458
        ctx:command("arrayput", "aGroup1, index , 0") -- MM_ARSLEGAARD.scr:459
        ctx:command("arrayput", "aGroup2, index , 0") -- MM_ARSLEGAARD.scr:460
        ctx:command("arrayput", "aGroup3, index , 0") -- MM_ARSLEGAARD.scr:461
        ctx:command("arrayput", "aGroup4, index , 0") -- MM_ARSLEGAARD.scr:462
        ctx:command("index", "= index + 1") -- MM_ARSLEGAARD.scr:463
    end -- MM_ARSLEGAARD.scr:464
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:466
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_ARSLEGAARD.scr:470
    -- ArrayPut aGroup1,0,53
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:475
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_ARSLEGAARD.scr:478
    -- ArrayPut aGroup2,0,54
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:483
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_ARSLEGAARD.scr:486
    -- ArrayPut aGroup3,0,55
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:489
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_ARSLEGAARD.scr:492
    -- ArrayPut aGroup4,0,56
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:495
end

script.labels["Init"] = function(ctx)
    -- MM_ARSLEGAARD.scr:500
    mm9.gosub(script, ctx, "InitArrays") -- MM_ARSLEGAARD.scr:502
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_ARSLEGAARD.scr:504
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_ARSLEGAARD.scr:505
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_ARSLEGAARD.scr:506
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_ARSLEGAARD.scr:507
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_ARSLEGAARD.scr:509
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_ARSLEGAARD.scr:510
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_ARSLEGAARD.scr:511
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:513
end

script.labels["Main"] = function(ctx)
    -- MM_ARSLEGAARD.scr:516
    mm9.gosub(script, ctx, "Init") -- MM_ARSLEGAARD.scr:518
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_ARSLEGAARD.scr:519
    do return ctx:exit("") end -- MM_ARSLEGAARD.scr:521
end

return script
