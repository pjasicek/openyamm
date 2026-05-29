-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THEPLAY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- ThePlay.scr
-- By Timmy
-- handles robert and douglas's argument
-- sound stuff
-- checks to see if a sound is currently playing
-- duration of sound
-- if sound is done this is true
-- actor voice handlers
-- handler for Narrator
-- handler for Trislan
-- Handle for Abriel
-- Handle for Ralof
-- Handle for Wilam
-- Handle for Leffery
-- ACT I
script.labels["Onblabber"] = function(ctx)
    -- THEPLAY.scr:31
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\01.wav", "Narratorhandle", 240, "FALSE", 100) -- THEPLAY.scr:37
    ctx:getSoundDuration("", "Narratorhandle", "sounddur") -- THEPLAY.scr:38
    ctx:state().sounddur = (tonumber(ctx:state().sounddur) or 0) + 1 -- THEPLAY.scr:39
    ctx:wait(1, "sounddur", "Narrator02") -- THEPLAY.scr:40
    do return ctx:exit("") end -- THEPLAY.scr:43
end

script.labels["Narrator02"] = function(ctx)
    -- THEPLAY.scr:47
    ctx:killSound("Narratorhandle") -- THEPLAY.scr:50
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\02.wav", "Narratorhandle", 240, "FALSE", 100) -- THEPLAY.scr:51
    ctx:getSoundDuration("", "Narratorhandle", "sounddur") -- THEPLAY.scr:52
    ctx:wait(1, "sounddur", "Trislan03") -- THEPLAY.scr:53
    do return ctx:exit("") end -- THEPLAY.scr:54
end

script.labels["Trislan03"] = function(ctx)
    -- THEPLAY.scr:58
    ctx:killSound("TrislanHandle") -- THEPLAY.scr:62
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\03.wav", "TrislanHandle", 240, "FALSE", 100) -- THEPLAY.scr:63
    ctx:getSoundDuration("", "TrislanHandle", "sounddur") -- THEPLAY.scr:64
    ctx:wait(1, "sounddur", "Abriel04") -- THEPLAY.scr:66
    do return ctx:exit("") end -- THEPLAY.scr:67
end

script.labels["Abriel04"] = function(ctx)
    -- THEPLAY.scr:71
    ctx:killSound("AbrielHandle") -- THEPLAY.scr:75
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\04.wav", "AbrielHandle", 240, "FALSE", 100) -- THEPLAY.scr:77
    ctx:getSoundDuration("", "AbrielHandle", "sounddur") -- THEPLAY.scr:78
    ctx:wait(1, "sounddur", "Trislan05") -- THEPLAY.scr:80
    do return ctx:exit("") end -- THEPLAY.scr:81
end

script.labels["Trislan05"] = function(ctx)
    -- THEPLAY.scr:85
    ctx:killSound("TrislanHandle") -- THEPLAY.scr:88
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\05.wav", "TrislanHandle", 240, "FALSE", 100) -- THEPLAY.scr:89
    ctx:getSoundDuration("", "TrislanHandle", "sounddur") -- THEPLAY.scr:90
    ctx:sub("Sounddur", .4) -- THEPLAY.scr:91
    ctx:wait(1, "sounddur", "Abriel06") -- THEPLAY.scr:92
    do return ctx:exit("") end -- THEPLAY.scr:93
end

script.labels["Abriel06"] = function(ctx)
    -- THEPLAY.scr:97
    ctx:killSound("AbrielHandle") -- THEPLAY.scr:100
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\06.wav", "AbrielHandle", 240, "FALSE", 100) -- THEPLAY.scr:101
    ctx:getSoundDuration("", "AbrielHandle", "sounddur") -- THEPLAY.scr:102
    ctx:wait(1, "sounddur", "Trislan07") -- THEPLAY.scr:103
    do return ctx:exit("") end -- THEPLAY.scr:104
end

script.labels["Trislan07"] = function(ctx)
    -- THEPLAY.scr:109
    ctx:killSound("TrislanHandle") -- THEPLAY.scr:112
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\07.wav", "TrislanHandle", 240, "FALSE", 100) -- THEPLAY.scr:113
    ctx:getSoundDuration("", "TrislanHandle", "sounddur") -- THEPLAY.scr:114
    ctx:wait(1, "sounddur", "Abriel08") -- THEPLAY.scr:116
    do return ctx:exit("") end -- THEPLAY.scr:117
end

script.labels["Abriel08"] = function(ctx)
    -- THEPLAY.scr:120
    ctx:killSound("AbrielHandle") -- THEPLAY.scr:123
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\08.wav", "AbrielHandle", 240, "FALSE", 100) -- THEPLAY.scr:124
    ctx:getSoundDuration("", "AbrielHandle", "sounddur") -- THEPLAY.scr:125
    ctx:state().sounddur = (tonumber(ctx:state().sounddur) or 0) + 1 -- THEPLAY.scr:126
    ctx:wait(1, "sounddur", "Narrator09") -- THEPLAY.scr:127
    do return ctx:exit("") end -- THEPLAY.scr:128
end

-- ACT II
script.labels["Narrator09"] = function(ctx)
    -- THEPLAY.scr:135
    ctx:killSound("Narratorhandle") -- THEPLAY.scr:138
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\09.wav", "Narratorhandle", 240, "FALSE", 100) -- THEPLAY.scr:139
    ctx:getSoundDuration("", "Narratorhandle", "sounddur") -- THEPLAY.scr:140
    ctx:wait(1, "sounddur", "Wilam10") -- THEPLAY.scr:142
    do return ctx:exit("") end -- THEPLAY.scr:143
end

script.labels["Wilam10"] = function(ctx)
    -- THEPLAY.scr:146
    ctx:killSound("WilamHandle") -- THEPLAY.scr:149
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\10.wav", "WilamHandle", 240, "FALSE", 100) -- THEPLAY.scr:150
    ctx:getSoundDuration("", "WilamHandle", "sounddur") -- THEPLAY.scr:151
    ctx:wait(1, "sounddur", "Ralof11") -- THEPLAY.scr:153
    do return ctx:exit("") end -- THEPLAY.scr:154
end

script.labels["Ralof11"] = function(ctx)
    -- THEPLAY.scr:157
    ctx:killSound("RalofHandle") -- THEPLAY.scr:160
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\11.wav", "RalofHandle", 240, "FALSE", 100) -- THEPLAY.scr:161
    ctx:getSoundDuration("", "RalofHandle", "sounddur") -- THEPLAY.scr:162
    ctx:sub("sounddur", .4) -- THEPLAY.scr:163
    ctx:wait(1, "sounddur", "Leffery12") -- THEPLAY.scr:164
    do return ctx:exit("") end -- THEPLAY.scr:165
end

script.labels["Leffery12"] = function(ctx)
    -- THEPLAY.scr:168
    ctx:killSound("LefferyHandle") -- THEPLAY.scr:171
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\12.wav", "LefferyHandle", 240, "FALSE", 100) -- THEPLAY.scr:172
    ctx:getSoundDuration("", "LefferyHandle", "sounddur") -- THEPLAY.scr:173
    ctx:wait(1, "sounddur", "Ralof13") -- THEPLAY.scr:175
    do return ctx:exit("") end -- THEPLAY.scr:176
end

script.labels["Ralof13"] = function(ctx)
    -- THEPLAY.scr:179
    ctx:killSound("RalofHandle") -- THEPLAY.scr:182
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\13b.wav", "RalofHandle", 240, "FALSE", 100) -- THEPLAY.scr:183
    ctx:getSoundDuration("", "RalofHandle", "sounddur") -- THEPLAY.scr:184
    ctx:sub("sounddur", .4) -- THEPLAY.scr:185
    ctx:wait(1, "sounddur", "Leffery14") -- THEPLAY.scr:186
    do return ctx:exit("") end -- THEPLAY.scr:187
end

script.labels["Leffery14"] = function(ctx)
    -- THEPLAY.scr:190
    ctx:killSound("LefferyHandle") -- THEPLAY.scr:193
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\14.wav", "LefferyHandle", 240, "FALSE", 100) -- THEPLAY.scr:194
    ctx:getSoundDuration("", "LefferyHandle", "sounddur") -- THEPLAY.scr:195
    ctx:wait(1, "sounddur", "Abriel15") -- THEPLAY.scr:197
    do return ctx:exit("") end -- THEPLAY.scr:198
end

script.labels["Abriel15"] = function(ctx)
    -- THEPLAY.scr:201
    ctx:killSound("AbrielHandle") -- THEPLAY.scr:204
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\15.wav", "AbrielHandle", 240, "FALSE", 100) -- THEPLAY.scr:205
    ctx:getSoundDuration("", "AbrielHandle", "sounddur") -- THEPLAY.scr:206
    ctx:wait(1, "sounddur", "Ralof16") -- THEPLAY.scr:208
    do return ctx:exit("") end -- THEPLAY.scr:209
end

script.labels["Ralof16"] = function(ctx)
    -- THEPLAY.scr:212
    ctx:killSound("RalofHandle") -- THEPLAY.scr:215
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\16.wav", "RalofHandle", 240, "FALSE", 100) -- THEPLAY.scr:216
    ctx:getSoundDuration("", "RalofHandle", "sounddur") -- THEPLAY.scr:217
    ctx:wait(1, "sounddur", "Abriel17") -- THEPLAY.scr:219
    do return ctx:exit("") end -- THEPLAY.scr:220
end

script.labels["Abriel17"] = function(ctx)
    -- THEPLAY.scr:223
    ctx:killSound("AbrielHandle") -- THEPLAY.scr:226
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\17.wav", "AbrielHandle", 240, "FALSE", 100) -- THEPLAY.scr:227
    ctx:getSoundDuration("", "AbrielHandle", "sounddur") -- THEPLAY.scr:228
    ctx:wait(1, "sounddur", "Ralof18") -- THEPLAY.scr:230
    do return ctx:exit("") end -- THEPLAY.scr:231
end

script.labels["Ralof18"] = function(ctx)
    -- THEPLAY.scr:234
    ctx:killSound("RalofHandle") -- THEPLAY.scr:237
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\18.wav", "RalofHandle", 240, "FALSE", 100) -- THEPLAY.scr:238
    ctx:getSoundDuration("", "RalofHandle", "sounddur") -- THEPLAY.scr:239
    ctx:wait(1, "sounddur", "Abriel19") -- THEPLAY.scr:241
    do return ctx:exit("") end -- THEPLAY.scr:242
end

script.labels["Abriel19"] = function(ctx)
    -- THEPLAY.scr:245
    ctx:killSound("AbrielHandle") -- THEPLAY.scr:248
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\19.wav", "AbrielHandle", 240, "FALSE", 100) -- THEPLAY.scr:249
    ctx:getSoundDuration("", "AbrielHandle", "sounddur") -- THEPLAY.scr:250
    ctx:wait(1, "sounddur", "Ralof20") -- THEPLAY.scr:252
    do return ctx:exit("") end -- THEPLAY.scr:253
end

script.labels["Ralof20"] = function(ctx)
    -- THEPLAY.scr:256
    ctx:killSound("RalofHandle") -- THEPLAY.scr:259
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\20.wav", "RalofHandle", 240, "FALSE", 100) -- THEPLAY.scr:260
    ctx:getSoundDuration("", "RalofHandle", "sounddur") -- THEPLAY.scr:261
    ctx:state().sounddur = (tonumber(ctx:state().sounddur) or 0) + 1 -- THEPLAY.scr:262
    ctx:wait(1, "sounddur", "Narrator21") -- THEPLAY.scr:263
    do return ctx:exit("") end -- THEPLAY.scr:264
end

script.labels["Narrator21"] = function(ctx)
    -- THEPLAY.scr:267
    ctx:killSound("Narratorhandle") -- THEPLAY.scr:270
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\21.wav", "Narratorhandle", 240, "FALSE", 100) -- THEPLAY.scr:271
    ctx:getSoundDuration("", "Narratorhandle", "sounddur") -- THEPLAY.scr:272
    ctx:state().sounddur = (tonumber(ctx:state().sounddur) or 0) + 1 -- THEPLAY.scr:273
    ctx:wait(1, "sounddur", "Narrator22") -- THEPLAY.scr:274
    do return ctx:exit("") end -- THEPLAY.scr:275
end

-- ACT III
script.labels["Narrator22"] = function(ctx)
    -- THEPLAY.scr:281
    ctx:killSound("Narratorhandle") -- THEPLAY.scr:284
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\22.wav", "Narratorhandle", 240, "FALSE", 100) -- THEPLAY.scr:285
    ctx:getSoundDuration("", "Narratorhandle", "sounddur") -- THEPLAY.scr:286
    ctx:wait(1, "sounddur", "Trislan23") -- THEPLAY.scr:288
    do return ctx:exit("") end -- THEPLAY.scr:289
end

script.labels["Trislan23"] = function(ctx)
    -- THEPLAY.scr:292
    ctx:killSound("TrislanHandle") -- THEPLAY.scr:295
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\23.wav", "TrislanHandle", 240, "FALSE", 100) -- THEPLAY.scr:296
    ctx:getSoundDuration("", "TrislanHandle", "sounddur") -- THEPLAY.scr:297
    ctx:wait(1, "sounddur", "Ralof24") -- THEPLAY.scr:299
    do return ctx:exit("") end -- THEPLAY.scr:300
end

script.labels["Ralof24"] = function(ctx)
    -- THEPLAY.scr:303
    ctx:killSound("RalofHandle") -- THEPLAY.scr:306
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\24.wav", "RalofHandle", 240, "FALSE", 100) -- THEPLAY.scr:307
    ctx:getSoundDuration("", "RalofHandle", "sounddur") -- THEPLAY.scr:308
    ctx:wait(1, "sounddur", "Trislan25") -- THEPLAY.scr:310
    do return ctx:exit("") end -- THEPLAY.scr:311
end

script.labels["Trislan25"] = function(ctx)
    -- THEPLAY.scr:314
    ctx:killSound("TrislanHandle") -- THEPLAY.scr:317
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\25.wav", "TrislanHandle", 240, "FALSE", 100) -- THEPLAY.scr:318
    ctx:getSoundDuration("", "TrislanHandle", "sounddur") -- THEPLAY.scr:319
    ctx:wait(1, "sounddur", "Ralof26") -- THEPLAY.scr:321
    do return ctx:exit("") end -- THEPLAY.scr:322
end

script.labels["Ralof26"] = function(ctx)
    -- THEPLAY.scr:325
    ctx:killSound("RalofHandle") -- THEPLAY.scr:328
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\26.wav", "RalofHandle", 240, "FALSE", 100) -- THEPLAY.scr:329
    ctx:getSoundDuration("", "RalofHandle", "sounddur") -- THEPLAY.scr:330
    ctx:wait(1, "sounddur", "Trislan27a") -- THEPLAY.scr:332
    do return ctx:exit("") end -- THEPLAY.scr:333
end

script.labels["Trislan27a"] = function(ctx)
    -- THEPLAY.scr:338
    ctx:killSound("TrislanHandle") -- THEPLAY.scr:341
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\27a.wav", "TrislanHandle", 240, "FALSE", 100) -- THEPLAY.scr:342
    ctx:getSoundDuration("", "TrislanHandle", "sounddur") -- THEPLAY.scr:343
    ctx:sub("sounddur", .6) -- THEPLAY.scr:344
    ctx:wait(1, "sounddur", "Narrator27") -- THEPLAY.scr:345
    do return ctx:exit("") end -- THEPLAY.scr:346
end

script.labels["Narrator27"] = function(ctx)
    -- THEPLAY.scr:349
    ctx:killSound("Narratorhandle") -- THEPLAY.scr:352
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\27.wav", "Narratorhandle", 240, "FALSE", 100) -- THEPLAY.scr:353
    ctx:getSoundDuration("", "Narratorhandle", "sounddur") -- THEPLAY.scr:354
    ctx:state().sounddur = (tonumber(ctx:state().sounddur) or 0) + 1 -- THEPLAY.scr:355
    ctx:wait(1, "sounddur", "Narrator28") -- THEPLAY.scr:356
    do return ctx:exit("") end -- THEPLAY.scr:357
end

script.labels["Narrator28"] = function(ctx)
    -- THEPLAY.scr:360
    ctx:killSound("Narratorhandle") -- THEPLAY.scr:363
    ctx:playSoundHandle("voices\\cinema\\guberlandplay\\28.wav", "Narratorhandle", 240, "FALSE", 100) -- THEPLAY.scr:364
    ctx:getSoundDuration("", "Narratorhandle", "sounddur") -- THEPLAY.scr:365
    ctx:state().sounddur = (tonumber(ctx:state().sounddur) or 0) + 3 -- THEPLAY.scr:366
    ctx:wait(1, "sounddur", "Onexit") -- THEPLAY.scr:367
    do return ctx:exit("") end -- THEPLAY.scr:368
end

script.labels["OnUse"] = function(ctx)
    -- THEPLAY.scr:371
    -- if sound is playing, kill it
    ctx:killSound("Narratorhandle") -- THEPLAY.scr:376
    ctx:killSound("TrislanHandle") -- THEPLAY.scr:377
    ctx:killSound("AbrielHandle") -- THEPLAY.scr:378
    ctx:killSound("RalofHandle") -- THEPLAY.scr:379
    ctx:killSound("WilamHandle") -- THEPLAY.scr:380
    ctx:killSound("LefferyHandle") -- THEPLAY.scr:381
    ctx:state().sound = 0 -- THEPLAY.scr:383
    ctx:state().g_ntemp = 0 -- THEPLAY.scr:384
    -- start rude dialog
    ctx:doRude(110) -- THEPLAY.scr:387
    do return ctx:exit("") end -- THEPLAY.scr:388
end

script.labels["Onexit"] = function(ctx)
    -- THEPLAY.scr:392
    -- kill the sound if it's done
    ctx:killSound("Narratorhandle") -- THEPLAY.scr:399
    ctx:killSound("TrislanHandle") -- THEPLAY.scr:400
    ctx:killSound("AbrielHandle") -- THEPLAY.scr:401
    ctx:killSound("RalofHandle") -- THEPLAY.scr:402
    ctx:killSound("WilamHandle") -- THEPLAY.scr:403
    ctx:killSound("LefferyHandle") -- THEPLAY.scr:404
    do return ctx:exit("") end -- THEPLAY.scr:406
end

script.labels["Main"] = function(ctx)
    -- THEPLAY.scr:410
    -- TraceOn ;delete me!!
    ctx:addTrigger("blabber", "Onblabber") -- THEPLAY.scr:414
    -- AddTrigger Use, OnUse ; ADD THIS BACK IN WHEN PROPS CAN REACT TO WAIT COMMAND
    ctx:cacheSound("voices\\cinema\\guberlandplay\\01.wav") -- THEPLAY.scr:416
    ctx:cacheSound("voices\\cinema\\guberlandplay\\02.wav") -- THEPLAY.scr:417
    ctx:cacheSound("voices\\cinema\\guberlandplay\\03.wav") -- THEPLAY.scr:418
    ctx:cacheSound("voices\\cinema\\guberlandplay\\04.wav") -- THEPLAY.scr:419
    ctx:cacheSound("voices\\cinema\\guberlandplay\\05.wav") -- THEPLAY.scr:420
    ctx:cacheSound("voices\\cinema\\guberlandplay\\06.wav") -- THEPLAY.scr:421
    ctx:cacheSound("voices\\cinema\\guberlandplay\\07.wav") -- THEPLAY.scr:422
    ctx:cacheSound("voices\\cinema\\guberlandplay\\08.wav") -- THEPLAY.scr:423
    ctx:cacheSound("voices\\cinema\\guberlandplay\\09.wav") -- THEPLAY.scr:424
    ctx:cacheSound("voices\\cinema\\guberlandplay\\10.wav") -- THEPLAY.scr:425
    ctx:cacheSound("voices\\cinema\\guberlandplay\\11.wav") -- THEPLAY.scr:426
    ctx:cacheSound("voices\\cinema\\guberlandplay\\12.wav") -- THEPLAY.scr:427
    ctx:cacheSound("voices\\cinema\\guberlandplay\\13.wav") -- THEPLAY.scr:428
    ctx:cacheSound("voices\\cinema\\guberlandplay\\14.wav") -- THEPLAY.scr:429
    ctx:cacheSound("voices\\cinema\\guberlandplay\\15.wav") -- THEPLAY.scr:430
    ctx:cacheSound("voices\\cinema\\guberlandplay\\16.wav") -- THEPLAY.scr:431
    ctx:cacheSound("voices\\cinema\\guberlandplay\\17.wav") -- THEPLAY.scr:432
    ctx:cacheSound("voices\\cinema\\guberlandplay\\18.wav") -- THEPLAY.scr:433
    ctx:cacheSound("voices\\cinema\\guberlandplay\\19.wav") -- THEPLAY.scr:434
    ctx:cacheSound("voices\\cinema\\guberlandplay\\20.wav") -- THEPLAY.scr:435
    ctx:cacheSound("voices\\cinema\\guberlandplay\\21.wav") -- THEPLAY.scr:436
    ctx:cacheSound("voices\\cinema\\guberlandplay\\22.wav") -- THEPLAY.scr:437
    ctx:cacheSound("voices\\cinema\\guberlandplay\\23.wav") -- THEPLAY.scr:438
    ctx:cacheSound("voices\\cinema\\guberlandplay\\24.wav") -- THEPLAY.scr:439
    ctx:cacheSound("voices\\cinema\\guberlandplay\\25.wav") -- THEPLAY.scr:440
    ctx:cacheSound("voices\\cinema\\guberlandplay\\26.wav") -- THEPLAY.scr:441
    ctx:cacheSound("voices\\cinema\\guberlandplay\\27.wav") -- THEPLAY.scr:442
    ctx:cacheSound("voices\\cinema\\guberlandplay\\28.wav") -- THEPLAY.scr:443
    ctx:state().sound = 0 -- THEPLAY.scr:444
    ctx:state().g_ntemp = 0 -- THEPLAY.scr:445
    do return ctx:exit("") end -- THEPLAY.scr:448
end

return script
