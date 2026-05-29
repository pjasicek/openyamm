-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BREAKICE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- BreakIce.scr
-- By Timmy
-- handles break the ice quest
-- edited by Bones -- 6/12/03
-- TELP Patch 1.3 -- prevents accessing objects before they are loaded
script.labels["OnStart"] = function(ctx)
    -- BREAKICE.scr:15
    ctx:wait(1, 2, "Start") -- BREAKICE.scr:17
    do return ctx:exit("") end -- BREAKICE.scr:18
end

script.labels["Start"] = function(ctx)
    -- BREAKICE.scr:21
    ctx:screenFadeOut(1) -- BREAKICE.scr:24
    ctx:wait(1, 1, "FadeIn") -- BREAKICE.scr:25
    do return ctx:exit("") end -- BREAKICE.scr:26
end

script.labels["FadeIn"] = function(ctx)
    -- BREAKICE.scr:30
    ctx:letterBox("true") -- BREAKICE.scr:33
    ctx:object("Camera0"):trigger("On") -- BREAKICE.scr:34-35
    ctx:screenFadeIn(1) -- BREAKICE.scr:36
    ctx:object("DestructableBrush27"):trigger("DamageOn") -- BREAKICE.scr:39-40
    ctx:wait(1, 1, "ShootOn") -- BREAKICE.scr:42
    do return ctx:exit("") end -- BREAKICE.scr:43
end

script.labels["ShootOn"] = function(ctx)
    -- BREAKICE.scr:46
    ctx:object("Shooter1"):trigger("On") -- BREAKICE.scr:49-50
    ctx:wait(1, .5, "LetterboxOff") -- BREAKICE.scr:52
    do return ctx:exit("") end -- BREAKICE.scr:53
end

script.labels["LetterboxOff"] = function(ctx)
    -- BREAKICE.scr:56
    ctx:object("Camera0"):trigger("Start") -- BREAKICE.scr:58-59
    ctx:wait(1, 1.5, "Shooter2") -- BREAKICE.scr:60
    ctx:wait(2, 1.7, "Shooter3") -- BREAKICE.scr:61
    ctx:wait(3, 1.8, "Shooter4") -- BREAKICE.scr:62
    ctx:wait(4, 2.5, "UnderCam") -- BREAKICE.scr:63
    do return ctx:exit("") end -- BREAKICE.scr:64
end

script.labels["Shooter2"] = function(ctx)
    -- BREAKICE.scr:67
    ctx:object("DestructableBrush6"):trigger("DamageOn") -- BREAKICE.scr:70-71
    ctx:object("DestructableBrush17"):trigger("DamageOn") -- BREAKICE.scr:72-73
    ctx:object("DestructableBrush18"):trigger("DamageOn") -- BREAKICE.scr:74-75
    ctx:object("DestructableBrush16"):trigger("DamageOn") -- BREAKICE.scr:76-77
    ctx:object("Shooter2"):trigger("On") -- BREAKICE.scr:79-80
    do return ctx:exit("") end -- BREAKICE.scr:81
end

script.labels["Shooter3"] = function(ctx)
    -- BREAKICE.scr:84
    ctx:object("Shooter3"):trigger("On") -- BREAKICE.scr:87-88
    do return ctx:exit("") end -- BREAKICE.scr:89
end

script.labels["Shooter4"] = function(ctx)
    -- BREAKICE.scr:92
    ctx:object("Shooter4"):trigger("On") -- BREAKICE.scr:95-96
    do return ctx:exit("") end -- BREAKICE.scr:97
end

script.labels["UnderCam"] = function(ctx)
    -- BREAKICE.scr:101
    ctx:object("Camera0"):trigger("Off") -- BREAKICE.scr:104-105
    local object = ctx:object("Camera1") -- BREAKICE.scr:106
    object:trigger("On") -- BREAKICE.scr:107
    object:trigger("Move") -- BREAKICE.scr:108
    ctx:wait(1, .7, "Destroy15") -- BREAKICE.scr:109
    ctx:wait(2, 1.5, "Destroy16") -- BREAKICE.scr:110
    ctx:wait(3, 2, "Destroy25") -- BREAKICE.scr:111
    do return ctx:exit("") end -- BREAKICE.scr:112
end

script.labels["Destroy15"] = function(ctx)
    -- BREAKICE.scr:116
    local object = ctx:object("DestructableBrush15") -- BREAKICE.scr:119
    object:trigger("DamageOn") -- BREAKICE.scr:120
    object:trigger("destroy") -- BREAKICE.scr:121
    ctx:playSound("Sounds\\Events\\iceimpact.wav", "DoNothing", 100, 9000, "FALSE", 100) -- BREAKICE.scr:122
    do return ctx:exit("") end -- BREAKICE.scr:123
end

script.labels["Destroy16"] = function(ctx)
    -- BREAKICE.scr:126
    local object = ctx:object("DestructableBrush26") -- BREAKICE.scr:129
    object:trigger("DamageOn") -- BREAKICE.scr:130
    object:trigger("destroy") -- BREAKICE.scr:131
    ctx:playSound("Sounds\\Events\\iceimpact.wav", "DoNothing", 100, 9000, "FALSE", 100) -- BREAKICE.scr:132
    do return ctx:exit("") end -- BREAKICE.scr:133
end

script.labels["Destroy25"] = function(ctx)
    -- BREAKICE.scr:136
    local object = ctx:object("DestructableBrush25") -- BREAKICE.scr:139
    object:trigger("DamageOn") -- BREAKICE.scr:140
    object:trigger("destroy") -- BREAKICE.scr:141
    ctx:playSound("Sounds\\Events\\iceimpact.wav", "DoNothing", 100, 9000, "FALSE", 100) -- BREAKICE.scr:142
    do return ctx:exit("") end -- BREAKICE.scr:143
end

script.labels["OnCam3"] = function(ctx)
    -- BREAKICE.scr:146
    ctx:object("Camera1"):trigger("Off") -- BREAKICE.scr:149-150
    ctx:object("Camera2"):trigger("On") -- BREAKICE.scr:151-152
    ctx:wait(1, 1.1, "Group1") -- BREAKICE.scr:153
    ctx:wait(2, 1.11, "Group2") -- BREAKICE.scr:154
    ctx:wait(3, 1.12, "Group3") -- BREAKICE.scr:155
    ctx:wait(4, 3, "OnDone") -- BREAKICE.scr:156
    do return ctx:exit("") end -- BREAKICE.scr:157
end

script.labels["Group1"] = function(ctx)
    -- BREAKICE.scr:160
    ctx:playSound("Sounds\\Events\\iceimpact.wav", "DoNothing", 100, 9000, "FALSE", 100) -- BREAKICE.scr:163
    local object = ctx:object("DestructableBrush17") -- BREAKICE.scr:164
    object:trigger("DamageOn") -- BREAKICE.scr:165
    object:trigger("destroy") -- BREAKICE.scr:166
    local object = ctx:object("DestructableBrush18") -- BREAKICE.scr:167
    object:trigger("DamageOn") -- BREAKICE.scr:168
    object:trigger("destroy") -- BREAKICE.scr:169
    local object = ctx:object("DestructableBrush27") -- BREAKICE.scr:170
    object:trigger("DamageOn") -- BREAKICE.scr:171
    object:trigger("destroy") -- BREAKICE.scr:172
    local object = ctx:object("DestructableBrush16") -- BREAKICE.scr:173
    object:trigger("DamageOn") -- BREAKICE.scr:174
    object:trigger("destroy") -- BREAKICE.scr:175
    local object = ctx:object("DestructableBrush14") -- BREAKICE.scr:177
    object:trigger("DamageOn") -- BREAKICE.scr:178
    object:trigger("destroy") -- BREAKICE.scr:179
    local object = ctx:object("DestructableBrush21") -- BREAKICE.scr:180
    object:trigger("DamageOn") -- BREAKICE.scr:181
    object:trigger("destroy") -- BREAKICE.scr:182
    local object = ctx:object("DestructableBrush24") -- BREAKICE.scr:183
    object:trigger("DamageOn") -- BREAKICE.scr:184
    object:trigger("destroy") -- BREAKICE.scr:185
    local object = ctx:object("DestructableBrush30") -- BREAKICE.scr:186
    object:trigger("DamageOn") -- BREAKICE.scr:187
    object:trigger("destroy") -- BREAKICE.scr:188
    local object = ctx:object("DestructableBrush33") -- BREAKICE.scr:189
    object:trigger("DamageOn") -- BREAKICE.scr:190
    object:trigger("destroy") -- BREAKICE.scr:191
    local object = ctx:object("DestructableBrush36") -- BREAKICE.scr:192
    object:trigger("DamageOn") -- BREAKICE.scr:193
    object:trigger("destroy") -- BREAKICE.scr:194
    local object = ctx:object("DestructableBrush39") -- BREAKICE.scr:195
    object:trigger("DamageOn") -- BREAKICE.scr:196
    object:trigger("destroy") -- BREAKICE.scr:197
    local object = ctx:object("DestructableBrush42") -- BREAKICE.scr:198
    object:trigger("DamageOn") -- BREAKICE.scr:199
    object:trigger("destroy") -- BREAKICE.scr:200
    local object = ctx:object("DestructableBrush45") -- BREAKICE.scr:201
    object:trigger("DamageOn") -- BREAKICE.scr:202
    object:trigger("destroy") -- BREAKICE.scr:203
    local object = ctx:object("DestructableBrush9") -- BREAKICE.scr:204
    object:trigger("DamageOn") -- BREAKICE.scr:205
    object:trigger("destroy") -- BREAKICE.scr:206
    do return ctx:exit("") end -- BREAKICE.scr:207
end

script.labels["Group2"] = function(ctx)
    -- BREAKICE.scr:210
    ctx:playSound("Sounds\\Events\\iceimpact.wav", "DoNothing", 100, 9000, "FALSE", 100) -- BREAKICE.scr:213
    local object = ctx:object("DestructableBrush19") -- BREAKICE.scr:214
    object:trigger("DamageOn") -- BREAKICE.scr:215
    object:trigger("destroy") -- BREAKICE.scr:216
    local object = ctx:object("DestructableBrush22") -- BREAKICE.scr:217
    object:trigger("DamageOn") -- BREAKICE.scr:218
    object:trigger("destroy") -- BREAKICE.scr:219
    local object = ctx:object("DestructableBrush28") -- BREAKICE.scr:220
    object:trigger("DamageOn") -- BREAKICE.scr:221
    object:trigger("destroy") -- BREAKICE.scr:222
    local object = ctx:object("DestructableBrush31") -- BREAKICE.scr:223
    object:trigger("DamageOn") -- BREAKICE.scr:224
    object:trigger("destroy") -- BREAKICE.scr:225
    local object = ctx:object("DestructableBrush34") -- BREAKICE.scr:226
    object:trigger("DamageOn") -- BREAKICE.scr:227
    object:trigger("destroy") -- BREAKICE.scr:228
    local object = ctx:object("DestructableBrush37") -- BREAKICE.scr:229
    object:trigger("DamageOn") -- BREAKICE.scr:230
    object:trigger("destroy") -- BREAKICE.scr:231
    local object = ctx:object("DestructableBrush40") -- BREAKICE.scr:232
    object:trigger("DamageOn") -- BREAKICE.scr:233
    object:trigger("destroy") -- BREAKICE.scr:234
    local object = ctx:object("DestructableBrush43") -- BREAKICE.scr:235
    object:trigger("DamageOn") -- BREAKICE.scr:236
    object:trigger("destroy") -- BREAKICE.scr:237
    local object = ctx:object("DestructableBrush7") -- BREAKICE.scr:238
    object:trigger("DamageOn") -- BREAKICE.scr:239
    object:trigger("destroy") -- BREAKICE.scr:240
    do return ctx:exit("") end -- BREAKICE.scr:241
end

script.labels["Group3"] = function(ctx)
    -- BREAKICE.scr:244
    ctx:playSound("Sounds\\Events\\iceimpact.wav", "DoNothing", 100, 9000, "FALSE", 100) -- BREAKICE.scr:247
    local object = ctx:object("DestructableBrush20") -- BREAKICE.scr:248
    object:trigger("DamageOn") -- BREAKICE.scr:249
    object:trigger("destroy") -- BREAKICE.scr:250
    local object = ctx:object("DestructableBrush23") -- BREAKICE.scr:251
    object:trigger("DamageOn") -- BREAKICE.scr:252
    object:trigger("destroy") -- BREAKICE.scr:253
    local object = ctx:object("DestructableBrush29") -- BREAKICE.scr:254
    object:trigger("DamageOn") -- BREAKICE.scr:255
    object:trigger("destroy") -- BREAKICE.scr:256
    local object = ctx:object("DestructableBrush32") -- BREAKICE.scr:257
    object:trigger("DamageOn") -- BREAKICE.scr:258
    object:trigger("destroy") -- BREAKICE.scr:259
    local object = ctx:object("DestructableBrush35") -- BREAKICE.scr:260
    object:trigger("DamageOn") -- BREAKICE.scr:261
    object:trigger("destroy") -- BREAKICE.scr:262
    local object = ctx:object("DestructableBrush38") -- BREAKICE.scr:263
    object:trigger("DamageOn") -- BREAKICE.scr:264
    object:trigger("destroy") -- BREAKICE.scr:265
    local object = ctx:object("DestructableBrush41") -- BREAKICE.scr:266
    object:trigger("DamageOn") -- BREAKICE.scr:267
    object:trigger("destroy") -- BREAKICE.scr:268
    local object = ctx:object("DestructableBrush44") -- BREAKICE.scr:269
    object:trigger("DamageOn") -- BREAKICE.scr:270
    object:trigger("destroy") -- BREAKICE.scr:271
    local object = ctx:object("DestructableBrush8") -- BREAKICE.scr:272
    object:trigger("DamageOn") -- BREAKICE.scr:273
    object:trigger("destroy") -- BREAKICE.scr:274
    do return ctx:exit("") end -- BREAKICE.scr:275
end

script.labels["OnDone"] = function(ctx)
    -- BREAKICE.scr:278
    ctx:screenFadeOut(1) -- BREAKICE.scr:281
    mm9.gosub(script, ctx, "GivePoints") -- BREAKICE.scr:282
    ctx:wait(1, 1.5, "Done") -- BREAKICE.scr:283
    do return ctx:exit("") end -- BREAKICE.scr:284
end

script.labels["Done"] = function(ctx)
    -- BREAKICE.scr:287
    ctx:letterBox("false") -- BREAKICE.scr:290
    ctx:object("Camera2"):trigger("Off") -- BREAKICE.scr:291-292
    ctx:screenFadeIn(1) -- BREAKICE.scr:293
    do return ctx:exit("") end -- BREAKICE.scr:294
end

script.labels["Init"] = function(ctx)
    -- BREAKICE.scr:297
    if not ctx:hasKey(72) then -- BREAKICE.scr:300-301
        do return ctx:exit("") end -- BREAKICE.scr:302
    end -- BREAKICE.scr:303
    local object = ctx:object("DestructableBrush20") -- BREAKICE.scr:306
    object:trigger("DamageOn") -- BREAKICE.scr:307
    object:trigger("destroy") -- BREAKICE.scr:308
    local object = ctx:object("DestructableBrush23") -- BREAKICE.scr:309
    object:trigger("DamageOn") -- BREAKICE.scr:310
    object:trigger("destroy") -- BREAKICE.scr:311
    local object = ctx:object("DestructableBrush29") -- BREAKICE.scr:312
    object:trigger("DamageOn") -- BREAKICE.scr:313
    object:trigger("destroy") -- BREAKICE.scr:314
    local object = ctx:object("DestructableBrush32") -- BREAKICE.scr:315
    object:trigger("DamageOn") -- BREAKICE.scr:316
    object:trigger("destroy") -- BREAKICE.scr:317
    local object = ctx:object("DestructableBrush35") -- BREAKICE.scr:318
    object:trigger("DamageOn") -- BREAKICE.scr:319
    object:trigger("destroy") -- BREAKICE.scr:320
    local object = ctx:object("DestructableBrush38") -- BREAKICE.scr:321
    object:trigger("DamageOn") -- BREAKICE.scr:322
    object:trigger("destroy") -- BREAKICE.scr:323
    local object = ctx:object("DestructableBrush41") -- BREAKICE.scr:324
    object:trigger("DamageOn") -- BREAKICE.scr:325
    object:trigger("destroy") -- BREAKICE.scr:326
    local object = ctx:object("DestructableBrush44") -- BREAKICE.scr:327
    object:trigger("DamageOn") -- BREAKICE.scr:328
    object:trigger("destroy") -- BREAKICE.scr:329
    local object = ctx:object("DestructableBrush8") -- BREAKICE.scr:330
    object:trigger("DamageOn") -- BREAKICE.scr:331
    object:trigger("destroy") -- BREAKICE.scr:332
    local object = ctx:object("DestructableBrush19") -- BREAKICE.scr:333
    object:trigger("DamageOn") -- BREAKICE.scr:334
    object:trigger("destroy") -- BREAKICE.scr:335
    local object = ctx:object("DestructableBrush22") -- BREAKICE.scr:336
    object:trigger("DamageOn") -- BREAKICE.scr:337
    object:trigger("destroy") -- BREAKICE.scr:338
    local object = ctx:object("DestructableBrush28") -- BREAKICE.scr:339
    object:trigger("DamageOn") -- BREAKICE.scr:340
    object:trigger("destroy") -- BREAKICE.scr:341
    local object = ctx:object("DestructableBrush31") -- BREAKICE.scr:342
    object:trigger("DamageOn") -- BREAKICE.scr:343
    object:trigger("destroy") -- BREAKICE.scr:344
    local object = ctx:object("DestructableBrush34") -- BREAKICE.scr:345
    object:trigger("DamageOn") -- BREAKICE.scr:346
    object:trigger("destroy") -- BREAKICE.scr:347
    local object = ctx:object("DestructableBrush37") -- BREAKICE.scr:348
    object:trigger("DamageOn") -- BREAKICE.scr:349
    object:trigger("destroy") -- BREAKICE.scr:350
    local object = ctx:object("DestructableBrush40") -- BREAKICE.scr:351
    object:trigger("DamageOn") -- BREAKICE.scr:352
    object:trigger("destroy") -- BREAKICE.scr:353
    local object = ctx:object("DestructableBrush43") -- BREAKICE.scr:354
    object:trigger("DamageOn") -- BREAKICE.scr:355
    object:trigger("destroy") -- BREAKICE.scr:356
    local object = ctx:object("DestructableBrush7") -- BREAKICE.scr:357
    object:trigger("DamageOn") -- BREAKICE.scr:358
    object:trigger("destroy") -- BREAKICE.scr:359
    local object = ctx:object("DestructableBrush14") -- BREAKICE.scr:360
    object:trigger("DamageOn") -- BREAKICE.scr:361
    object:trigger("destroy") -- BREAKICE.scr:362
    local object = ctx:object("DestructableBrush21") -- BREAKICE.scr:363
    object:trigger("DamageOn") -- BREAKICE.scr:364
    object:trigger("destroy") -- BREAKICE.scr:365
    local object = ctx:object("DestructableBrush24") -- BREAKICE.scr:366
    object:trigger("DamageOn") -- BREAKICE.scr:367
    object:trigger("destroy") -- BREAKICE.scr:368
    local object = ctx:object("DestructableBrush30") -- BREAKICE.scr:369
    object:trigger("DamageOn") -- BREAKICE.scr:370
    object:trigger("destroy") -- BREAKICE.scr:371
    local object = ctx:object("DestructableBrush33") -- BREAKICE.scr:372
    object:trigger("DamageOn") -- BREAKICE.scr:373
    object:trigger("destroy") -- BREAKICE.scr:374
    local object = ctx:object("DestructableBrush36") -- BREAKICE.scr:375
    object:trigger("DamageOn") -- BREAKICE.scr:376
    object:trigger("destroy") -- BREAKICE.scr:377
    local object = ctx:object("DestructableBrush39") -- BREAKICE.scr:378
    object:trigger("DamageOn") -- BREAKICE.scr:379
    object:trigger("destroy") -- BREAKICE.scr:380
    local object = ctx:object("DestructableBrush42") -- BREAKICE.scr:381
    object:trigger("DamageOn") -- BREAKICE.scr:382
    object:trigger("destroy") -- BREAKICE.scr:383
    local object = ctx:object("DestructableBrush45") -- BREAKICE.scr:384
    object:trigger("DamageOn") -- BREAKICE.scr:385
    object:trigger("destroy") -- BREAKICE.scr:386
    local object = ctx:object("DestructableBrush9") -- BREAKICE.scr:387
    object:trigger("DamageOn") -- BREAKICE.scr:388
    object:trigger("destroy") -- BREAKICE.scr:389
    local object = ctx:object("DestructableBrush25") -- BREAKICE.scr:390
    object:trigger("DamageOn") -- BREAKICE.scr:391
    object:trigger("destroy") -- BREAKICE.scr:392
    local object = ctx:object("DestructableBrush26") -- BREAKICE.scr:393
    object:trigger("DamageOn") -- BREAKICE.scr:394
    object:trigger("destroy") -- BREAKICE.scr:395
    local object = ctx:object("DestructableBrush15") -- BREAKICE.scr:396
    object:trigger("DamageOn") -- BREAKICE.scr:397
    object:trigger("destroy") -- BREAKICE.scr:398
    local object = ctx:object("DestructableBrush6") -- BREAKICE.scr:399
    object:trigger("DamageOn") -- BREAKICE.scr:400
    object:trigger("destroy") -- BREAKICE.scr:401
    local object = ctx:object("DestructableBrush17") -- BREAKICE.scr:402
    object:trigger("DamageOn") -- BREAKICE.scr:403
    object:trigger("destroy") -- BREAKICE.scr:404
    local object = ctx:object("DestructableBrush18") -- BREAKICE.scr:405
    object:trigger("DamageOn") -- BREAKICE.scr:406
    object:trigger("destroy") -- BREAKICE.scr:407
    local object = ctx:object("DestructableBrush16") -- BREAKICE.scr:408
    object:trigger("DamageOn") -- BREAKICE.scr:409
    object:trigger("destroy") -- BREAKICE.scr:410
    ctx:state().g_hobject = ctx:objectOrNil("DestructableProp0") -- BREAKICE.scr:411
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:412
    do return ctx:exit("") end -- BREAKICE.scr:413
end

script.labels["GivePoints"] = function(ctx)
    -- BREAKICE.scr:417
    -- NOTE this script just completes the quest right now.
    -- this is the routine where additional functionality should go
    -- checks to see if player has done this yet
    ctx:hasKey(72, "g_ntemp") -- BREAKICE.scr:421
    if ctx:condition("g_ntemp==0") then -- BREAKICE.scr:423
        -- checks to see if player is on kill anskram keep Quest
        ctx:hasKey(71, "keycheck") -- BREAKICE.scr:425
        if ctx:condition("keycheck==1") then -- BREAKICE.scr:426
            -- gives player finished quest key
            ctx:giveKey("", 72) -- BREAKICE.scr:428
            ctx:giveExp(8000) -- BREAKICE.scr:429
            do return ctx:exit("") end -- BREAKICE.scr:430
        end -- BREAKICE.scr:431
    end -- BREAKICE.scr:432
    -- checks to see if player is on kill anskram keep Quest
    ctx:hasKey(174, "keycheck") -- BREAKICE.scr:434
    if ctx:condition("keycheck==0") then -- BREAKICE.scr:435
        -- gives player finished quest key
        ctx:giveKey("", 174) -- BREAKICE.scr:437
        ctx:giveExp(8000) -- BREAKICE.scr:438
        do return ctx:exit("") end -- BREAKICE.scr:439
    end -- BREAKICE.scr:440
    do return ctx:exit("") end -- BREAKICE.scr:441
end

script.labels["Main"] = function(ctx)
    -- BREAKICE.scr:447
    -- TraceOn ;delete me!!
    ctx:addTrigger("Start", "OnStart") -- BREAKICE.scr:451
    ctx:addTrigger("Cam3", "OnCam3") -- BREAKICE.scr:452
    ctx:onEvent("OnPostStartWorld", "Init") -- BREAKICE.scr:453
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- BREAKICE.scr:454
    ctx:onEvent("OnPostSaveLoad", "Init") -- BREAKICE.scr:455
    ctx:wait(1, .1, "Init") -- BREAKICE.scr:456
    do return ctx:exit("") end -- BREAKICE.scr:457
end

script.labels["Init"] = function(ctx)
    -- BREAKICE.scr:461
    -- overloaded -- Bones
    -- kills competing waits
    ctx:wait(1, 0, "DoNothing") -- BREAKICE.scr:466
    if not ctx:hasKey(72) then -- BREAKICE.scr:468-469
        if not ctx:hasKey(174) then -- BREAKICE.scr:470-471
            do return ctx:exit("") end -- BREAKICE.scr:472
        end -- BREAKICE.scr:473
    end -- BREAKICE.scr:474
    ctx:state().g_nPad2 = 1 -- BREAKICE.scr:476
    -- timer overloaded intentionally
    ctx:wait(1, 1, "OnStart") -- BREAKICE.scr:478
    do return ctx:exit("") end -- BREAKICE.scr:479
end

script.labels["OnStart"] = function(ctx)
    -- BREAKICE.scr:482
    -- overloaded -- Bones
    if ctx:condition("g_nPad2 == 0") then -- BREAKICE.scr:486
        ctx:wait(1, 2, "Start") -- BREAKICE.scr:487
        do return ctx:exit("") end -- BREAKICE.scr:488
    end -- BREAKICE.scr:489
    ctx:state().g_nPad2 = 0 -- BREAKICE.scr:491
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush20") -- BREAKICE.scr:493
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:494
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush23") -- BREAKICE.scr:496
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:497
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush29") -- BREAKICE.scr:499
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:500
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush32") -- BREAKICE.scr:502
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:503
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush35") -- BREAKICE.scr:505
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:506
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush38") -- BREAKICE.scr:508
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:509
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush41") -- BREAKICE.scr:511
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:512
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush44") -- BREAKICE.scr:514
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:515
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush8") -- BREAKICE.scr:517
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:518
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush19") -- BREAKICE.scr:520
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:521
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush22") -- BREAKICE.scr:523
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:524
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush28") -- BREAKICE.scr:526
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:527
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush31") -- BREAKICE.scr:529
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:530
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush34") -- BREAKICE.scr:532
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:533
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush37") -- BREAKICE.scr:535
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:536
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush40") -- BREAKICE.scr:538
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:539
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush43") -- BREAKICE.scr:541
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:542
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush7") -- BREAKICE.scr:544
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:545
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush14") -- BREAKICE.scr:547
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:548
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush21") -- BREAKICE.scr:550
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:551
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush24") -- BREAKICE.scr:553
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:554
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush30") -- BREAKICE.scr:556
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:557
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush33") -- BREAKICE.scr:559
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:560
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush36") -- BREAKICE.scr:562
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:563
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush39") -- BREAKICE.scr:565
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:566
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush42") -- BREAKICE.scr:568
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:569
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush45") -- BREAKICE.scr:571
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:572
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush9") -- BREAKICE.scr:574
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:575
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush25") -- BREAKICE.scr:577
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:578
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush26") -- BREAKICE.scr:580
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:581
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush15") -- BREAKICE.scr:583
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:584
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush6") -- BREAKICE.scr:586
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:587
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush17") -- BREAKICE.scr:589
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:590
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush18") -- BREAKICE.scr:592
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:593
    ctx:state().g_hobject = ctx:objectOrNil("DestructableBrush16") -- BREAKICE.scr:595
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:596
    ctx:state().g_hobject = ctx:objectOrNil("DestructableProp0") -- BREAKICE.scr:598
    ctx:object("g_hobject"):remove() -- BREAKICE.scr:599
    do return ctx:exit("") end -- BREAKICE.scr:601
end

return script
