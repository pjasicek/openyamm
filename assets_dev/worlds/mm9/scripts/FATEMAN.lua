-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FATEMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- LoseMan.scr
-- By Timmy
-- 12/20
-- handles losegame cutscene
script.labels["OnLose"] = function(ctx)
    -- FATEMAN.scr:23
    if ctx:hasKey(98) then -- FATEMAN.scr:28-29
        do return ctx:exit("") end -- FATEMAN.scr:30
    end -- FATEMAN.scr:31
    ctx:giveKey(98) -- FATEMAN.scr:33
    ctx:screenFadeOut(1) -- FATEMAN.scr:35
    ctx:wait(1, 2, "OnStart") -- FATEMAN.scr:36
    do return ctx:exit("") end -- FATEMAN.scr:37
end

script.labels["OnStart"] = function(ctx)
    -- FATEMAN.scr:40
    ctx:state().g_hobject = ctx:objectOrNil("Losecam4") -- FATEMAN.scr:43
    -- trigger g_hobject On
    ctx:trigger("g_hobject", "Play") -- FATEMAN.scr:45
    do return ctx:exit("") end -- FATEMAN.scr:47
end

script.labels["OnCam2"] = function(ctx)
    -- FATEMAN.scr:50
    ctx:screenFadeOut(.5) -- FATEMAN.scr:54
    ctx:object("losecam4"):trigger("off") -- FATEMAN.scr:55-56
    ctx:object("losecam2"):trigger("Play") -- FATEMAN.scr:58-59
    do return ctx:exit("") end -- FATEMAN.scr:60
end

script.labels["OnCam3"] = function(ctx)
    -- FATEMAN.scr:63
    ctx:screenFadeOut(.5) -- FATEMAN.scr:67
    ctx:object("losecam2"):trigger("off") -- FATEMAN.scr:68-69
    ctx:object("losecam3"):trigger("on") -- FATEMAN.scr:71-72
    ctx:screenFadeIn(.5) -- FATEMAN.scr:73
    ctx:wait(1, 1, "Scene4") -- FATEMAN.scr:74
    do return ctx:exit("") end -- FATEMAN.scr:75
end

script.labels["Scene4"] = function(ctx)
    -- FATEMAN.scr:78
    ctx:object("Door0"):trigger("use") -- FATEMAN.scr:81-82
    ctx:playSound("\\Sounds\\events\\draweropenwood.wav", "DoNothing", 100, 24000, "FALSE", 100) -- FATEMAN.scr:83
    ctx:wait(1, 1.5, "Speak9") -- FATEMAN.scr:84
    do return ctx:exit("") end -- FATEMAN.scr:85
end

script.labels["Speak9"] = function(ctx)
    -- FATEMAN.scr:88
    ctx:object("hanndl"):trigger("speak9") -- FATEMAN.scr:91-92
    do return ctx:exit("") end -- FATEMAN.scr:94
end

script.labels["Close"] = function(ctx)
    -- FATEMAN.scr:97
    ctx:object("Door0"):trigger("use") -- FATEMAN.scr:100-101
    ctx:playSound("\\Sounds\\events\\draweropenwood.wav", "DoNothing", 100, 24000, "FALSE", 100) -- FATEMAN.scr:102
    ctx:wait(1, 1, "FadeOut") -- FATEMAN.scr:103
    do return ctx:exit("") end -- FATEMAN.scr:104
end

script.labels["FadeOut"] = function(ctx)
    -- FATEMAN.scr:107
    ctx:screenFadeOut(1) -- FATEMAN.scr:110
    ctx:letterBox("False") -- FATEMAN.scr:111
    ctx:wait(1, 1, "ExitIN") -- FATEMAN.scr:112
    do return ctx:exit("") end -- FATEMAN.scr:113
end

script.labels["ExitIN"] = function(ctx)
    -- FATEMAN.scr:117
    ctx:screenFadeIn(2) -- FATEMAN.scr:120
    ctx:object("ExitTrigger2"):trigger("trigger") -- FATEMAN.scr:121-122
    ctx:giveExp(46000) -- FATEMAN.scr:123
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 24000, "FALSE", 100) -- FATEMAN.scr:124
    do return ctx:exit("") end -- FATEMAN.scr:125
end

script.labels["OnPC1"] = function(ctx)
    -- FATEMAN.scr:128
    ctx:playSound("sVoice1", "Trigger10", 100, 24000, "FALSE", 100) -- FATEMAN.scr:131
    -- wait 1 2.5 Trigger10
    do return ctx:exit("") end -- FATEMAN.scr:133
end

script.labels["Trigger10"] = function(ctx)
    -- FATEMAN.scr:136
    ctx:object("Hanndl"):trigger("Speak10") -- FATEMAN.scr:139-140
    do return ctx:exit("") end -- FATEMAN.scr:141
end

script.labels["OnPC2"] = function(ctx)
    -- FATEMAN.scr:145
    ctx:playSound("sVoice2", "Trigger11", 100, 24000, "FALSE", 100) -- FATEMAN.scr:148
    -- wait 1 3 Trigger11
    do return ctx:exit("") end -- FATEMAN.scr:150
end

script.labels["Trigger11"] = function(ctx)
    -- FATEMAN.scr:153
    ctx:object("Hanndl"):trigger("Speak11") -- FATEMAN.scr:156-157
    do return ctx:exit("") end -- FATEMAN.scr:158
end

script.labels["OnPC3"] = function(ctx)
    -- FATEMAN.scr:161
    ctx:playSound("sVoice3", "Trigger12", 100, 24000, "FALSE", 100) -- FATEMAN.scr:164
    -- wait 1 3.5 Trigger12
    do return ctx:exit("") end -- FATEMAN.scr:166
end

script.labels["Trigger12"] = function(ctx)
    -- FATEMAN.scr:169
    ctx:object("Hanndl"):trigger("Speak12") -- FATEMAN.scr:172-173
    do return ctx:exit("") end -- FATEMAN.scr:174
end

script.labels["OnPC4"] = function(ctx)
    -- FATEMAN.scr:177
    ctx:playSound("sVoice4", "Trigger13", 100, 24000, "FALSE", 100) -- FATEMAN.scr:180
    -- wait 1 3.5 OnPC5
    do return ctx:exit("") end -- FATEMAN.scr:182
end

script.labels["Trigger13"] = function(ctx)
    -- FATEMAN.scr:185
    ctx:object("Hanndl"):trigger("Speak13") -- FATEMAN.scr:188-189
    do return ctx:exit("") end -- FATEMAN.scr:190
end

script.labels["OnPC5"] = function(ctx)
    -- FATEMAN.scr:193
    ctx:playSound("sVoice5", "Trigger13", 100, 24000, "FALSE", 100) -- FATEMAN.scr:196
    -- wait 1 3.5 Trigger13
    do return ctx:exit("") end -- FATEMAN.scr:198
end

script.labels["OnPC6"] = function(ctx)
    -- FATEMAN.scr:203
    ctx:playSound("sVoice6", "Trigger15", 100, 24000, "FALSE", 100) -- FATEMAN.scr:206
    -- wait 1 2.5 Trigger15
    do return ctx:exit("") end -- FATEMAN.scr:208
end

script.labels["Trigger15"] = function(ctx)
    -- FATEMAN.scr:211
    ctx:object("Hanndl"):trigger("Speak15") -- FATEMAN.scr:214-215
    do return ctx:exit("") end -- FATEMAN.scr:216
end

script.labels["OnDone"] = function(ctx)
    -- FATEMAN.scr:219
    ctx:set("nCounter", "nCounter + 1") -- FATEMAN.scr:222
    if ctx:condition("nCounter==1") then -- FATEMAN.scr:224
        do return mm9.gotoLabel(script, ctx, "OnPC1") end -- FATEMAN.scr:225
        do return ctx:exit("") end -- FATEMAN.scr:226
    end -- FATEMAN.scr:227
    if ctx:condition("nCounter==2") then -- FATEMAN.scr:229
        do return mm9.gotoLabel(script, ctx, "OnPC2") end -- FATEMAN.scr:230
        do return ctx:exit("") end -- FATEMAN.scr:231
    end -- FATEMAN.scr:232
    if ctx:condition("nCounter==3") then -- FATEMAN.scr:234
        do return mm9.gotoLabel(script, ctx, "OnPC3") end -- FATEMAN.scr:235
        do return ctx:exit("") end -- FATEMAN.scr:236
    end -- FATEMAN.scr:237
    if ctx:condition("nCounter==4") then -- FATEMAN.scr:239
        do return mm9.gotoLabel(script, ctx, "OnPC4") end -- FATEMAN.scr:240
        do return ctx:exit("") end -- FATEMAN.scr:241
    end -- FATEMAN.scr:242
    if ctx:condition("nCounter==5") then -- FATEMAN.scr:244
        do return mm9.gotoLabel(script, ctx, "OnPC6") end -- FATEMAN.scr:245
        do return ctx:exit("") end -- FATEMAN.scr:246
    end -- FATEMAN.scr:247
    if ctx:condition("nCounter==6") then -- FATEMAN.scr:249
        do return mm9.gotoLabel(script, ctx, "OnPC6") end -- FATEMAN.scr:250
        do return ctx:exit("") end -- FATEMAN.scr:251
    end -- FATEMAN.scr:252
    do return ctx:exit("") end -- FATEMAN.scr:253
end

script.labels["Init"] = function(ctx)
    -- FATEMAN.scr:256
    ctx:getPcVoice("g_ntemp") -- FATEMAN.scr:261
    if ctx:condition("g_ntemp==0") then -- FATEMAN.scr:264
        ctx:set("sVoice1", "voices\\cinema\\AngryFemale\\AngryFText01a.wav") -- FATEMAN.scr:265
        ctx:set("sVoice2", "voices\\cinema\\AngryFemale\\AngryFText02a.wav") -- FATEMAN.scr:266
        ctx:set("sVoice3", "voices\\cinema\\AngryFemale\\AngryFText03a.wav") -- FATEMAN.scr:267
        ctx:set("sVoice4", "voices\\cinema\\AngryFemale\\AngryFText04a.wav") -- FATEMAN.scr:268
        ctx:set("sVoice5", "voices\\cinema\\AngryFemale\\AngryFText05a.wav") -- FATEMAN.scr:269
        ctx:set("sVoice6", "voices\\cinema\\AngryFemale\\AngryFText06a.wav") -- FATEMAN.scr:270
        do return ctx:exit("") end -- FATEMAN.scr:271
    end -- FATEMAN.scr:272
    if ctx:condition("g_ntemp==1") then -- FATEMAN.scr:274
        ctx:set("sVoice1", "voices\\cinema\\ArrogantFemale\\ArrogantFText01a.wav") -- FATEMAN.scr:275
        ctx:set("sVoice2", "voices\\cinema\\ArrogantFemale\\ArrogantFText02b.wav") -- FATEMAN.scr:276
        ctx:set("sVoice3", "voices\\cinema\\ArrogantFemale\\ArrogantFText03a.wav") -- FATEMAN.scr:277
        ctx:set("sVoice4", "voices\\cinema\\ArrogantFemale\\ArrogantFText04a.wav") -- FATEMAN.scr:278
        ctx:set("sVoice5", "voices\\cinema\\ArrogantFemale\\ArrogantFText05a.wav") -- FATEMAN.scr:279
        ctx:set("sVoice6", "voices\\cinema\\ArrogantFemale\\ArrogantFText06a.wav") -- FATEMAN.scr:280
        do return ctx:exit("") end -- FATEMAN.scr:281
    end -- FATEMAN.scr:282
    if ctx:condition("g_ntemp==2") then -- FATEMAN.scr:284
        ctx:set("sVoice1", "voices\\cinema\\AssertiveFemale\\AssertiveFText01.wav") -- FATEMAN.scr:285
        ctx:set("sVoice2", "voices\\cinema\\AssertiveFemale\\AssertiveFText02.wav") -- FATEMAN.scr:286
        ctx:set("sVoice3", "voices\\cinema\\AssertiveFemale\\AssertiveFText03.wav") -- FATEMAN.scr:287
        ctx:set("sVoice4", "voices\\cinema\\AssertiveFemale\\AssertiveFText04.wav") -- FATEMAN.scr:288
        ctx:set("sVoice5", "voices\\cinema\\AssertiveFemale\\AssertiveFText05.wav") -- FATEMAN.scr:289
        ctx:set("sVoice6", "voices\\cinema\\AssertiveFemale\\AssertiveFText06.wav") -- FATEMAN.scr:290
        do return ctx:exit("") end -- FATEMAN.scr:291
    end -- FATEMAN.scr:292
    if ctx:condition("g_ntemp==3") then -- FATEMAN.scr:294
        ctx:set("sVoice1", "voices\\cinema\\CowardlyFemale\\CowardlyFText01b.wav") -- FATEMAN.scr:295
        ctx:set("sVoice2", "voices\\cinema\\CowardlyFemale\\CowardlyFText02.wav") -- FATEMAN.scr:296
        ctx:set("sVoice3", "voices\\cinema\\CowardlyFemale\\CowardlyFText03.wav") -- FATEMAN.scr:297
        ctx:set("sVoice4", "voices\\cinema\\CowardlyFemale\\CowardlyFText04b.wav") -- FATEMAN.scr:298
        ctx:set("sVoice5", "voices\\cinema\\CowardlyFemale\\CowardlyFText05.wav") -- FATEMAN.scr:299
        ctx:set("sVoice6", "voices\\cinema\\CowardlyFemale\\CowardlyFText06.wav") -- FATEMAN.scr:300
        do return ctx:exit("") end -- FATEMAN.scr:301
    end -- FATEMAN.scr:302
    if ctx:condition("g_ntemp==4") then -- FATEMAN.scr:304
        ctx:set("sVoice1", "voices\\cinema\\DimFemale\\DimFText01.wav") -- FATEMAN.scr:305
        ctx:set("sVoice2", "voices\\cinema\\DimFemale\\DimFText02.wav") -- FATEMAN.scr:306
        ctx:set("sVoice3", "voices\\cinema\\DimFemale\\DimFText03.wav") -- FATEMAN.scr:307
        ctx:set("sVoice4", "voices\\cinema\\DimFemale\\DimFText04.wav") -- FATEMAN.scr:308
        ctx:set("sVoice5", "voices\\cinema\\DimFemale\\DimFText05.wav") -- FATEMAN.scr:309
        ctx:set("sVoice6", "voices\\cinema\\DimFemale\\DimFText06.wav") -- FATEMAN.scr:310
        do return ctx:exit("") end -- FATEMAN.scr:311
    end -- FATEMAN.scr:312
    if ctx:condition("g_ntemp==5") then -- FATEMAN.scr:314
        ctx:set("sVoice1", "voices\\cinema\\HappyFemale\\HappyFText01.wav") -- FATEMAN.scr:315
        ctx:set("sVoice2", "voices\\cinema\\HappyFemale\\HappyFText02.wav") -- FATEMAN.scr:316
        ctx:set("sVoice3", "voices\\cinema\\HappyFemale\\HappyFText03.wav") -- FATEMAN.scr:317
        ctx:set("sVoice4", "voices\\cinema\\HappyFemale\\HappyFText04.wav") -- FATEMAN.scr:318
        ctx:set("sVoice5", "voices\\cinema\\HappyFemale\\HappyFText05.wav") -- FATEMAN.scr:319
        ctx:set("sVoice6", "voices\\cinema\\HappyFemale\\HappyFText06.wav") -- FATEMAN.scr:320
        do return ctx:exit("") end -- FATEMAN.scr:321
    end -- FATEMAN.scr:322
    if ctx:condition("g_ntemp==6") then -- FATEMAN.scr:324
        ctx:set("sVoice1", "voices\\cinema\\SarcasticFemale\\SarcasticFText01.wav") -- FATEMAN.scr:325
        ctx:set("sVoice2", "voices\\cinema\\SarcasticFemale\\SarcasticFText02.wav") -- FATEMAN.scr:326
        ctx:set("sVoice3", "voices\\cinema\\SarcasticFemale\\SarcasticFText03.wav") -- FATEMAN.scr:327
        ctx:set("sVoice4", "voices\\cinema\\SarcasticFemale\\SarcasticFText04.wav") -- FATEMAN.scr:328
        ctx:set("sVoice5", "voices\\cinema\\SarcasticFemale\\SarcasticFText05.wav") -- FATEMAN.scr:329
        ctx:set("sVoice6", "voices\\cinema\\SarcasticFemale\\SarcasticFText06.wav") -- FATEMAN.scr:330
        do return ctx:exit("") end -- FATEMAN.scr:331
    end -- FATEMAN.scr:332
    if ctx:condition("g_ntemp==7") then -- FATEMAN.scr:334
        ctx:set("sVoice1", "voices\\cinema\\LichFemale\\LichFText01.wav") -- FATEMAN.scr:335
        ctx:set("sVoice2", "voices\\cinema\\LichFemale\\LichFText02.wav") -- FATEMAN.scr:336
        ctx:set("sVoice3", "voices\\cinema\\LichFemale\\LichFText03.wav") -- FATEMAN.scr:337
        ctx:set("sVoice4", "voices\\cinema\\LichFemale\\LichFText04.wav") -- FATEMAN.scr:338
        ctx:set("sVoice5", "voices\\cinema\\LichFemale\\LichFText05.wav") -- FATEMAN.scr:339
        ctx:set("sVoice6", "voices\\cinema\\LichFemale\\LichFText06.wav") -- FATEMAN.scr:340
        do return ctx:exit("") end -- FATEMAN.scr:341
    end -- FATEMAN.scr:342
    if ctx:condition("g_ntemp==8") then -- FATEMAN.scr:344
        ctx:set("sVoice1", "voices\\cinema\\HalfOrcLichFemale\\HalfOrcLichFText01.wav") -- FATEMAN.scr:345
        ctx:set("sVoice2", "voices\\cinema\\HalfOrcLichFemale\\HalfOrcLichFText02.wav") -- FATEMAN.scr:346
        ctx:set("sVoice3", "voices\\cinema\\HalfOrcLichFemale\\HalfOrcLichFText03.wav") -- FATEMAN.scr:347
        ctx:set("sVoice4", "voices\\cinema\\HalfOrcLichFemale\\HalfOrcLichFText04.wav") -- FATEMAN.scr:348
        ctx:set("sVoice5", "voices\\cinema\\HalfOrcLichFemale\\HalfOrcLichFText05.wav") -- FATEMAN.scr:349
        ctx:set("sVoice6", "voices\\cinema\\HalfOrcLichFemale\\HalfOrcLichFText06.wav") -- FATEMAN.scr:350
        do return ctx:exit("") end -- FATEMAN.scr:351
    end -- FATEMAN.scr:352
    if ctx:condition("g_ntemp==9") then -- FATEMAN.scr:354
        ctx:set("sVoice1", "voices\\cinema\\Angrymale\\AngryText01a.wav") -- FATEMAN.scr:355
        ctx:set("sVoice2", "voices\\cinema\\Angrymale\\AngryText02.wav") -- FATEMAN.scr:356
        ctx:set("sVoice3", "voices\\cinema\\Angrymale\\AngryText03.wav") -- FATEMAN.scr:357
        ctx:set("sVoice4", "voices\\cinema\\Angrymale\\AngryText04.wav") -- FATEMAN.scr:358
        ctx:set("sVoice5", "voices\\cinema\\Angrymale\\AngryText05.wav") -- FATEMAN.scr:359
        ctx:set("sVoice6", "voices\\cinema\\Angrymale\\AngryText06a.wav") -- FATEMAN.scr:360
        do return ctx:exit("") end -- FATEMAN.scr:361
    end -- FATEMAN.scr:362
    if ctx:condition("g_ntemp==10") then -- FATEMAN.scr:364
        ctx:set("sVoice1", "voices\\cinema\\ArrogantMale\\ArrogantMText01.wav") -- FATEMAN.scr:365
        ctx:set("sVoice2", "voices\\cinema\\ArrogantMale\\ArrogantMText02.wav") -- FATEMAN.scr:366
        ctx:set("sVoice3", "voices\\cinema\\ArrogantMale\\ArrogantMText03.wav") -- FATEMAN.scr:367
        ctx:set("sVoice4", "voices\\cinema\\ArrogantMale\\ArrogantMText04.wav") -- FATEMAN.scr:368
        ctx:set("sVoice5", "voices\\cinema\\ArrogantMale\\ArrogantMText05.wav") -- FATEMAN.scr:369
        ctx:set("sVoice6", "voices\\cinema\\ArrogantMale\\ArrogantMText06.wav") -- FATEMAN.scr:370
        do return ctx:exit("") end -- FATEMAN.scr:371
    end -- FATEMAN.scr:372
    if ctx:condition("g_ntemp==11") then -- FATEMAN.scr:374
        ctx:set("sVoice1", "voices\\cinema\\AssertiveMale\\AssertiveMText01.wav") -- FATEMAN.scr:375
        ctx:set("sVoice2", "voices\\cinema\\AssertiveMale\\AssertiveMText02a.wav") -- FATEMAN.scr:376
        ctx:set("sVoice3", "voices\\cinema\\AssertiveMale\\AssertiveMText03.wav") -- FATEMAN.scr:377
        ctx:set("sVoice4", "voices\\cinema\\AssertiveMale\\AssertiveMText04.wav") -- FATEMAN.scr:378
        ctx:set("sVoice5", "voices\\cinema\\AssertiveMale\\AssertiveMText05.wav") -- FATEMAN.scr:379
        ctx:set("sVoice6", "voices\\cinema\\AssertiveMale\\AssertiveMText06.wav") -- FATEMAN.scr:380
        do return ctx:exit("") end -- FATEMAN.scr:381
    end -- FATEMAN.scr:382
    if ctx:condition("g_ntemp==12") then -- FATEMAN.scr:384
        ctx:set("sVoice1", "voices\\cinema\\CowardlyMale\\CowardlyMText01.wav") -- FATEMAN.scr:385
        ctx:set("sVoice2", "voices\\cinema\\CowardlyMale\\CowardlyMText02.wav") -- FATEMAN.scr:386
        ctx:set("sVoice3", "voices\\cinema\\CowardlyMale\\CowardlyMText03.wav") -- FATEMAN.scr:387
        ctx:set("sVoice4", "voices\\cinema\\CowardlyMale\\CowardlyMText04.wav") -- FATEMAN.scr:388
        ctx:set("sVoice5", "voices\\cinema\\CowardlyMale\\CowardlyMText05.wav") -- FATEMAN.scr:389
        ctx:set("sVoice6", "voices\\cinema\\CowardlyMale\\CowardlyMText06.wav") -- FATEMAN.scr:390
        do return ctx:exit("") end -- FATEMAN.scr:391
    end -- FATEMAN.scr:392
    if ctx:condition("g_ntemp==13") then -- FATEMAN.scr:394
        ctx:set("sVoice1", "voices\\cinema\\DimMale\\DimMText01.wav") -- FATEMAN.scr:395
        ctx:set("sVoice2", "voices\\cinema\\DimMale\\DimMText02.wav") -- FATEMAN.scr:396
        ctx:set("sVoice3", "voices\\cinema\\DimMale\\DimMText03.wav") -- FATEMAN.scr:397
        ctx:set("sVoice4", "voices\\cinema\\DimMale\\DimMText04.wav") -- FATEMAN.scr:398
        ctx:set("sVoice5", "voices\\cinema\\DimMale\\DimMText05.wav") -- FATEMAN.scr:399
        ctx:set("sVoice6", "voices\\cinema\\DimMale\\DimMText06.wav") -- FATEMAN.scr:400
        do return ctx:exit("") end -- FATEMAN.scr:401
    end -- FATEMAN.scr:402
    if ctx:condition("g_ntemp==14") then -- FATEMAN.scr:404
        ctx:set("sVoice1", "voices\\cinema\\HappyMale\\HappyMText01.wav") -- FATEMAN.scr:405
        ctx:set("sVoice2", "voices\\cinema\\HappyMale\\HappyMText02.wav") -- FATEMAN.scr:406
        ctx:set("sVoice3", "voices\\cinema\\HappyMale\\HappyMText03.wav") -- FATEMAN.scr:407
        ctx:set("sVoice4", "voices\\cinema\\HappyMale\\HappyMText04.wav") -- FATEMAN.scr:408
        ctx:set("sVoice5", "voices\\cinema\\HappyMale\\HappyMText05.wav") -- FATEMAN.scr:409
        ctx:set("sVoice6", "voices\\cinema\\HappyMale\\HappyMText06.wav") -- FATEMAN.scr:410
        do return ctx:exit("") end -- FATEMAN.scr:411
    end -- FATEMAN.scr:412
    if ctx:condition("g_ntemp==15") then -- FATEMAN.scr:414
        ctx:set("sVoice1", "voices\\cinema\\SarcasticMale\\SarcasticMText01.wav") -- FATEMAN.scr:415
        ctx:set("sVoice2", "voices\\cinema\\SarcasticMale\\SarcasticMText02.wav") -- FATEMAN.scr:416
        ctx:set("sVoice3", "voices\\cinema\\SarcasticMale\\SarcasticMText03.wav") -- FATEMAN.scr:417
        ctx:set("sVoice4", "voices\\cinema\\SarcasticMale\\SarcasticMText04.wav") -- FATEMAN.scr:418
        ctx:set("sVoice5", "voices\\cinema\\SarcasticMale\\SarcasticMText05.wav") -- FATEMAN.scr:419
        ctx:set("sVoice6", "voices\\cinema\\SarcasticMale\\SarcasticMText06.wav") -- FATEMAN.scr:420
        do return ctx:exit("") end -- FATEMAN.scr:421
    end -- FATEMAN.scr:422
    if ctx:condition("g_ntemp==16") then -- FATEMAN.scr:424
        ctx:set("sVoice1", "voices\\cinema\\LichMale\\LichMText01.wav") -- FATEMAN.scr:425
        ctx:set("sVoice2", "voices\\cinema\\LichMale\\LichMText02.wav") -- FATEMAN.scr:426
        ctx:set("sVoice3", "voices\\cinema\\LichMale\\LichMText03.wav") -- FATEMAN.scr:427
        ctx:set("sVoice4", "voices\\cinema\\LichMale\\LichMText04.wav") -- FATEMAN.scr:428
        ctx:set("sVoice5", "voices\\cinema\\LichMale\\LichMText05.wav") -- FATEMAN.scr:429
        ctx:set("sVoice6", "voices\\cinema\\LichMale\\LichMText06.wav") -- FATEMAN.scr:430
        do return ctx:exit("") end -- FATEMAN.scr:431
    end -- FATEMAN.scr:432
    if ctx:condition("g_ntemp==17") then -- FATEMAN.scr:434
        ctx:set("sVoice1", "voices\\cinema\\HalfOrcLichMale\\HalfOrcLichMText01.wav") -- FATEMAN.scr:435
        ctx:set("sVoice2", "voices\\cinema\\HalfOrcLichMale\\HalfOrcLichMText02.wav") -- FATEMAN.scr:436
        ctx:set("sVoice3", "voices\\cinema\\HalfOrcLichMale\\HalfOrcLichMText03.wav") -- FATEMAN.scr:437
        ctx:set("sVoice4", "voices\\cinema\\HalfOrcLichMale\\HalfOrcLichMText04.wav") -- FATEMAN.scr:438
        ctx:set("sVoice5", "voices\\cinema\\HalfOrcLichMale\\HalfOrcLichMText05.wav") -- FATEMAN.scr:439
        ctx:set("sVoice6", "voices\\cinema\\HalfOrcLichMale\\HalfOrcLichMText06.wav") -- FATEMAN.scr:440
        do return ctx:exit("") end -- FATEMAN.scr:441
    end -- FATEMAN.scr:442
    do return ctx:exit("") end -- FATEMAN.scr:444
end

script.labels["Main"] = function(ctx)
    -- FATEMAN.scr:447
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Lose", "OnLose") -- FATEMAN.scr:452
    ctx:addTrigger("Cam2", "OnCam2") -- FATEMAN.scr:453
    ctx:addTrigger("cam3", "OnCam3") -- FATEMAN.scr:454
    ctx:addTrigger("FadeOut", "Close") -- FATEMAN.scr:455
    ctx:addTrigger("Done", "OnDone") -- FATEMAN.scr:456
    -- wait 1 1 Init
    ctx:wait(1, .1, "OnLose") -- FATEMAN.scr:458
    ctx:onEvent("OnPostStartWorld", "OnLose") -- FATEMAN.scr:459
    ctx:onEvent("OnPostMiniSaveLoad", "OnLose") -- FATEMAN.scr:460
    ctx:onEvent("OnPostSaveLoad", "OnLose") -- FATEMAN.scr:461
    mm9.gosub(script, ctx, "Init") -- FATEMAN.scr:462
    do return ctx:exit("") end -- FATEMAN.scr:463
end

return script
