-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MM_ARSLEGARD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "Globals.inc" }

-- MM_Arslegard.scr
-- Jim Craig
-- Mundane Task List for Arslegard
script.labels["OnArrived"] = function(ctx)
    -- MM_ARSLEGARD.scr:39
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:42
end

script.labels["WarpOn"] = function(ctx)
    -- MM_ARSLEGARD.scr:45
    ctx:state().bWarp = true -- MM_ARSLEGARD.scr:48
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:50
end

script.labels["WarpOff"] = function(ctx)
    -- MM_ARSLEGARD.scr:53
    ctx:state().bWarp = false -- MM_ARSLEGARD.scr:56
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:58
end

script.labels["CreateMarker"] = function(ctx)
    -- MM_ARSLEGARD.scr:61
    if ctx:condition("goto_location == Work") then -- MM_ARSLEGARD.scr:64
        ctx:set("goto_marker", "marker_work + npc_id") -- MM_ARSLEGARD.scr:65
    end -- MM_ARSLEGARD.scr:66
    if ctx:condition("goto_location == Home") then -- MM_ARSLEGARD.scr:68
        ctx:set("goto_marker", "marker_home + npc_id") -- MM_ARSLEGARD.scr:69
    end -- MM_ARSLEGARD.scr:70
    if ctx:condition("goto_location == Misc") then -- MM_ARSLEGARD.scr:72
        ctx:set("goto_marker", "marker_misc + npc_id") -- MM_ARSLEGARD.scr:73
    end -- MM_ARSLEGARD.scr:74
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:76
end

script.labels["GoToLocation"] = function(ctx)
    -- MM_ARSLEGARD.scr:79
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_ARSLEGARD.scr:82
    ctx:object("npc_object"):setStat("PARAM", "goto_marker") -- MM_ARSLEGARD.scr:84
    if ctx:condition("bWarp == FALSE") then -- MM_ARSLEGARD.scr:86
        ctx:trigger("npc_object", "GoToLoc") -- MM_ARSLEGARD.scr:87
    end -- MM_ARSLEGARD.scr:88
    if ctx:condition("bWarp == TRUE") then -- MM_ARSLEGARD.scr:90
        ctx:trigger("npc_object", "WarpToLoc") -- MM_ARSLEGARD.scr:91
    end -- MM_ARSLEGARD.scr:92
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:94
end

script.labels["LaunchGroup"] = function(ctx)
    -- MM_ARSLEGARD.scr:97
    ctx:state().index = 0 -- MM_ARSLEGARD.scr:100
    while ctx:condition("index < 10") do -- MM_ARSLEGARD.scr:102
        ctx:state().npc_id = 0 -- MM_ARSLEGARD.scr:104
        if ctx:condition("current_group == Group1") then -- MM_ARSLEGARD.scr:106
            ctx:arrayGet("aGroup1", "index", "npc_id") -- MM_ARSLEGARD.scr:107
        end -- MM_ARSLEGARD.scr:108
        if ctx:condition("current_group == Group2") then -- MM_ARSLEGARD.scr:110
            ctx:arrayGet("aGroup2", "index", "npc_id") -- MM_ARSLEGARD.scr:111
        end -- MM_ARSLEGARD.scr:112
        if ctx:condition("current_group == Group3") then -- MM_ARSLEGARD.scr:114
            ctx:arrayGet("aGroup3", "index", "npc_id") -- MM_ARSLEGARD.scr:115
        end -- MM_ARSLEGARD.scr:116
        if ctx:condition("current_group == Group4") then -- MM_ARSLEGARD.scr:118
            ctx:arrayGet("aGroup4", "index", "npc_id") -- MM_ARSLEGARD.scr:119
        end -- MM_ARSLEGARD.scr:120
        if ctx:condition("npc_id != 0") then -- MM_ARSLEGARD.scr:122
            mm9.gosub(script, ctx, "CreateMarker") -- MM_ARSLEGARD.scr:123
            mm9.gosub(script, ctx, "GoToLocation") -- MM_ARSLEGARD.scr:124
        end -- MM_ARSLEGARD.scr:125
        ctx:set("index", "index + 1") -- MM_ARSLEGARD.scr:127
    end -- MM_ARSLEGARD.scr:128
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:130
end

script.labels["Group1_GoWork"] = function(ctx)
    -- MM_ARSLEGARD.scr:137
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:140
    ctx:set("current_group", "Group1") -- MM_ARSLEGARD.scr:141
    ctx:set("goto_location", "Work") -- MM_ARSLEGARD.scr:142
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:143
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:145
end

script.labels["Group1_WarpWork"] = function(ctx)
    -- MM_ARSLEGARD.scr:148
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:151
    ctx:set("current_group", "Group1") -- MM_ARSLEGARD.scr:152
    ctx:set("goto_location", "Work") -- MM_ARSLEGARD.scr:153
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:154
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:156
end

script.labels["Group1_GoHome"] = function(ctx)
    -- MM_ARSLEGARD.scr:159
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:162
    ctx:set("current_group", "Group1") -- MM_ARSLEGARD.scr:163
    ctx:set("goto_location", "Home") -- MM_ARSLEGARD.scr:164
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:165
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:167
end

script.labels["Group1_WarpHome"] = function(ctx)
    -- MM_ARSLEGARD.scr:170
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:173
    ctx:set("current_group", "Group1") -- MM_ARSLEGARD.scr:174
    ctx:set("goto_location", "Home") -- MM_ARSLEGARD.scr:175
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:176
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:178
end

script.labels["Group1_GoMisc"] = function(ctx)
    -- MM_ARSLEGARD.scr:181
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:184
    ctx:set("current_group", "Group1") -- MM_ARSLEGARD.scr:185
    ctx:set("goto_location", "Misc") -- MM_ARSLEGARD.scr:186
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:187
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:189
end

script.labels["Group1_WarpMisc"] = function(ctx)
    -- MM_ARSLEGARD.scr:192
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:195
    ctx:set("current_group", "Group1") -- MM_ARSLEGARD.scr:196
    ctx:set("goto_location", "Misc") -- MM_ARSLEGARD.scr:197
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:198
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:200
end

script.labels["Group2_GoWork"] = function(ctx)
    -- MM_ARSLEGARD.scr:204
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:207
    ctx:set("current_group", "Group2") -- MM_ARSLEGARD.scr:208
    ctx:set("goto_location", "Work") -- MM_ARSLEGARD.scr:209
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:210
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:212
end

script.labels["Group2_WarpWork"] = function(ctx)
    -- MM_ARSLEGARD.scr:215
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:218
    ctx:set("current_group", "Group2") -- MM_ARSLEGARD.scr:219
    ctx:set("goto_location", "Work") -- MM_ARSLEGARD.scr:220
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:221
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:223
end

script.labels["Group2_GoHome"] = function(ctx)
    -- MM_ARSLEGARD.scr:226
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:229
    ctx:set("current_group", "Group2") -- MM_ARSLEGARD.scr:230
    ctx:set("goto_location", "Home") -- MM_ARSLEGARD.scr:231
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:232
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:234
end

script.labels["Group2_WarpHome"] = function(ctx)
    -- MM_ARSLEGARD.scr:237
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:240
    ctx:set("current_group", "Group2") -- MM_ARSLEGARD.scr:241
    ctx:set("goto_location", "Home") -- MM_ARSLEGARD.scr:242
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:243
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:245
end

script.labels["Group2_GoMisc"] = function(ctx)
    -- MM_ARSLEGARD.scr:248
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:251
    ctx:set("current_group", "Group2") -- MM_ARSLEGARD.scr:252
    ctx:set("goto_location", "Misc") -- MM_ARSLEGARD.scr:253
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:254
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:256
end

script.labels["Group2_WarpMisc"] = function(ctx)
    -- MM_ARSLEGARD.scr:259
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:262
    ctx:set("current_group", "Group2") -- MM_ARSLEGARD.scr:263
    ctx:set("goto_location", "Misc") -- MM_ARSLEGARD.scr:264
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:265
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:267
end

script.labels["Group3_GoWork"] = function(ctx)
    -- MM_ARSLEGARD.scr:270
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:273
    ctx:set("current_group", "Group3") -- MM_ARSLEGARD.scr:274
    ctx:set("goto_location", "Work") -- MM_ARSLEGARD.scr:275
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:276
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:278
end

script.labels["Group3_WarpWork"] = function(ctx)
    -- MM_ARSLEGARD.scr:281
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:284
    ctx:set("current_group", "Group3") -- MM_ARSLEGARD.scr:285
    ctx:set("goto_location", "Work") -- MM_ARSLEGARD.scr:286
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:287
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:289
end

script.labels["Group3_GoHome"] = function(ctx)
    -- MM_ARSLEGARD.scr:292
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:295
    ctx:set("current_group", "Group3") -- MM_ARSLEGARD.scr:296
    ctx:set("goto_location", "Home") -- MM_ARSLEGARD.scr:297
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:298
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:300
end

script.labels["Group3_WarpHome"] = function(ctx)
    -- MM_ARSLEGARD.scr:303
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:306
    ctx:set("current_group", "Group3") -- MM_ARSLEGARD.scr:307
    ctx:set("goto_location", "Home") -- MM_ARSLEGARD.scr:308
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:309
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:311
end

script.labels["Group3_GoMisc"] = function(ctx)
    -- MM_ARSLEGARD.scr:314
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:317
    ctx:set("current_group", "Group3") -- MM_ARSLEGARD.scr:318
    ctx:set("goto_location", "Misc") -- MM_ARSLEGARD.scr:319
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:320
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:322
end

script.labels["Group3_WarpMisc"] = function(ctx)
    -- MM_ARSLEGARD.scr:325
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:328
    ctx:set("current_group", "Group3") -- MM_ARSLEGARD.scr:329
    ctx:set("goto_location", "Misc") -- MM_ARSLEGARD.scr:330
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:331
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:333
end

script.labels["Group4_GoWork"] = function(ctx)
    -- MM_ARSLEGARD.scr:336
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:339
    ctx:set("current_group", "Group4") -- MM_ARSLEGARD.scr:340
    ctx:set("goto_location", "Work") -- MM_ARSLEGARD.scr:341
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:342
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:344
end

script.labels["Group4_WarpWork"] = function(ctx)
    -- MM_ARSLEGARD.scr:347
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:350
    ctx:set("current_group", "Group4") -- MM_ARSLEGARD.scr:351
    ctx:set("goto_location", "Work") -- MM_ARSLEGARD.scr:352
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:353
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:355
end

script.labels["Group4_GoHome"] = function(ctx)
    -- MM_ARSLEGARD.scr:359
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:362
    ctx:set("current_group", "Group4") -- MM_ARSLEGARD.scr:363
    ctx:set("goto_location", "Home") -- MM_ARSLEGARD.scr:364
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:365
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:367
end

script.labels["Group4_WarpHome"] = function(ctx)
    -- MM_ARSLEGARD.scr:370
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:373
    ctx:set("current_group", "Group4") -- MM_ARSLEGARD.scr:374
    ctx:set("goto_location", "Home") -- MM_ARSLEGARD.scr:375
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:376
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:378
end

script.labels["Group4_GoMisc"] = function(ctx)
    -- MM_ARSLEGARD.scr:381
    mm9.gosub(script, ctx, "WarpOff") -- MM_ARSLEGARD.scr:384
    ctx:set("current_group", "Group4") -- MM_ARSLEGARD.scr:385
    ctx:set("goto_location", "Misc") -- MM_ARSLEGARD.scr:386
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:387
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:389
end

script.labels["Group4_WarpMisc"] = function(ctx)
    -- MM_ARSLEGARD.scr:392
    mm9.gosub(script, ctx, "WarpOn") -- MM_ARSLEGARD.scr:395
    ctx:set("current_group", "Group4") -- MM_ARSLEGARD.scr:396
    ctx:set("goto_location", "Misc") -- MM_ARSLEGARD.scr:397
    mm9.gosub(script, ctx, "LaunchGroup") -- MM_ARSLEGARD.scr:398
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:400
end

script.labels["InitWorkSchedule"] = function(ctx)
    -- MM_ARSLEGARD.scr:408
    ctx:atTime(6, 15, "Group1_GoWork", "Group1_WarpWork") -- MM_ARSLEGARD.scr:411
    ctx:atTime(6, 30, "Group2_GoWork", "Group2_WarpWork") -- MM_ARSLEGARD.scr:412
    ctx:atTime(6, 45, "Group3_GoWork", "Group3_WarpWork") -- MM_ARSLEGARD.scr:413
    ctx:atTime(7, 0, "Group4_GoWork", "Group4_WarpWork") -- MM_ARSLEGARD.scr:414
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:416
end

script.labels["InitHomeSchedule"] = function(ctx)
    -- MM_ARSLEGARD.scr:420
    ctx:atTime(18, 0, "Group1_GoHome", "Group1_WarpHome") -- MM_ARSLEGARD.scr:423
    ctx:atTime(18, 15, "Group2_GoHome", "Group2_WarpHome") -- MM_ARSLEGARD.scr:424
    ctx:atTime(18, 30, "Group3_GoHome", "Group3_WarpHome") -- MM_ARSLEGARD.scr:425
    ctx:atTime(18, 45, "Group4_GoHome", "Group4_WarpHome") -- MM_ARSLEGARD.scr:426
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:428
end

script.labels["InitMiscSchedule"] = function(ctx)
    -- MM_ARSLEGARD.scr:431
    -- Go Wander off to somewhere
    ctx:atTime(13, 0, "Group1_GoMisc", "Group1_WarpMisc") -- MM_ARSLEGARD.scr:435
    ctx:atTime(13, 15, "Group2_GoMisc", "Group2_WarpMisc") -- MM_ARSLEGARD.scr:436
    ctx:atTime(13, 30, "Group3_GoMisc", "Group3_WarpMisc") -- MM_ARSLEGARD.scr:437
    ctx:atTime(13, 45, "Group4_GoMisc", "Group4_WarpMisc") -- MM_ARSLEGARD.scr:438
    -- Go Back to work
    ctx:atTime(15, 0, "Group1_GoWork", "Group1_WarpWork") -- MM_ARSLEGARD.scr:441
    ctx:atTime(15, 15, "Group2_GoWork", "Group2_WarpWork") -- MM_ARSLEGARD.scr:442
    ctx:atTime(15, 30, "Group3_GoWork", "Group3_WarpWork") -- MM_ARSLEGARD.scr:443
    ctx:atTime(15, 45, "Group4_GoWork", "Group4_WarpWork") -- MM_ARSLEGARD.scr:444
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:446
end

script.labels["InitArrays"] = function(ctx)
    -- MM_ARSLEGARD.scr:454
    ctx:state().index = 0 -- MM_ARSLEGARD.scr:457
    while ctx:condition("index < 10") do -- MM_ARSLEGARD.scr:458
        ctx:arrayPut("aGroup1", "index", 0) -- MM_ARSLEGARD.scr:459
        ctx:arrayPut("aGroup2", "index", 0) -- MM_ARSLEGARD.scr:460
        ctx:arrayPut("aGroup3", "index", 0) -- MM_ARSLEGARD.scr:461
        ctx:arrayPut("aGroup4", "index", 0) -- MM_ARSLEGARD.scr:462
        ctx:set("index", "index + 1") -- MM_ARSLEGARD.scr:463
    end -- MM_ARSLEGARD.scr:464
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:466
end

script.labels["LoadGroup1"] = function(ctx)
    -- MM_ARSLEGARD.scr:470
    -- ArrayPut aGroup1,0,53
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:475
end

script.labels["LoadGroup2"] = function(ctx)
    -- MM_ARSLEGARD.scr:478
    -- ArrayPut aGroup2,0,54
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:483
end

script.labels["LoadGroup3"] = function(ctx)
    -- MM_ARSLEGARD.scr:486
    -- ArrayPut aGroup3,0,55
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:489
end

script.labels["LoadGroup4"] = function(ctx)
    -- MM_ARSLEGARD.scr:492
    -- ArrayPut aGroup4,0,56
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:495
end

script.labels["Init"] = function(ctx)
    -- MM_ARSLEGARD.scr:500
    mm9.gosub(script, ctx, "InitArrays") -- MM_ARSLEGARD.scr:502
    mm9.gosub(script, ctx, "LoadGroup1") -- MM_ARSLEGARD.scr:504
    mm9.gosub(script, ctx, "LoadGroup2") -- MM_ARSLEGARD.scr:505
    mm9.gosub(script, ctx, "LoadGroup3") -- MM_ARSLEGARD.scr:506
    mm9.gosub(script, ctx, "LoadGroup4") -- MM_ARSLEGARD.scr:507
    mm9.gosub(script, ctx, "InitWorkSchedule") -- MM_ARSLEGARD.scr:509
    mm9.gosub(script, ctx, "InitHomeSchedule") -- MM_ARSLEGARD.scr:510
    mm9.gosub(script, ctx, "InitMiscSchedule") -- MM_ARSLEGARD.scr:511
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:513
end

script.labels["Main"] = function(ctx)
    -- MM_ARSLEGARD.scr:516
    mm9.gosub(script, ctx, "Init") -- MM_ARSLEGARD.scr:518
    ctx:addTrigger("HasArrived", "OnArrived") -- MM_ARSLEGARD.scr:519
    do return ctx:exit("") end -- MM_ARSLEGARD.scr:521
end

return script
