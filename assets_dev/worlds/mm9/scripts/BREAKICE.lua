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
    ctx:command("wait", "1 2 Start") -- BREAKICE.scr:17
    do return ctx:exit("") end -- BREAKICE.scr:18
end

script.labels["Start"] = function(ctx)
    -- BREAKICE.scr:21
    ctx:command("screenfadeout", "1") -- BREAKICE.scr:24
    ctx:command("wait", "1 1 FadeIn") -- BREAKICE.scr:25
    do return ctx:exit("") end -- BREAKICE.scr:26
end

script.labels["FadeIn"] = function(ctx)
    -- BREAKICE.scr:30
    ctx:command("letterbox", "true") -- BREAKICE.scr:33
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- BREAKICE.scr:34
    ctx:trigger("g_hobject", "On") -- BREAKICE.scr:35
    ctx:command("screenfadein", "1") -- BREAKICE.scr:36
    ctx:command("getobjecthandle", "DestructableBrush27 g_hobject") -- BREAKICE.scr:39
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:40
    ctx:command("wait", "1 1 ShootOn") -- BREAKICE.scr:42
    do return ctx:exit("") end -- BREAKICE.scr:43
end

script.labels["ShootOn"] = function(ctx)
    -- BREAKICE.scr:46
    ctx:command("getobjecthandle", "Shooter1 g_hobject") -- BREAKICE.scr:49
    ctx:trigger("g_hobject", "On") -- BREAKICE.scr:50
    ctx:command("wait", "1 .5 LetterboxOff") -- BREAKICE.scr:52
    do return ctx:exit("") end -- BREAKICE.scr:53
end

script.labels["LetterboxOff"] = function(ctx)
    -- BREAKICE.scr:56
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- BREAKICE.scr:58
    ctx:trigger("g_hobject", "Start") -- BREAKICE.scr:59
    ctx:command("wait", "1 1.5 Shooter2") -- BREAKICE.scr:60
    ctx:command("wait", "2 1.7 Shooter3") -- BREAKICE.scr:61
    ctx:command("wait", "3 1.8 Shooter4") -- BREAKICE.scr:62
    ctx:command("wait", "4 2.5 UnderCam") -- BREAKICE.scr:63
    do return ctx:exit("") end -- BREAKICE.scr:64
end

script.labels["Shooter2"] = function(ctx)
    -- BREAKICE.scr:67
    ctx:command("getobjecthandle", "DestructableBrush6 g_hobject") -- BREAKICE.scr:70
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:71
    ctx:command("getobjecthandle", "DestructableBrush17 g_hobject") -- BREAKICE.scr:72
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:73
    ctx:command("getobjecthandle", "DestructableBrush18 g_hobject") -- BREAKICE.scr:74
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:75
    ctx:command("getobjecthandle", "DestructableBrush16 g_hobject") -- BREAKICE.scr:76
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:77
    ctx:command("getobjecthandle", "Shooter2 g_hobject") -- BREAKICE.scr:79
    ctx:trigger("g_hobject", "On") -- BREAKICE.scr:80
    do return ctx:exit("") end -- BREAKICE.scr:81
end

script.labels["Shooter3"] = function(ctx)
    -- BREAKICE.scr:84
    ctx:command("getobjecthandle", "Shooter3 g_hobject") -- BREAKICE.scr:87
    ctx:trigger("g_hobject", "On") -- BREAKICE.scr:88
    do return ctx:exit("") end -- BREAKICE.scr:89
end

script.labels["Shooter4"] = function(ctx)
    -- BREAKICE.scr:92
    ctx:command("getobjecthandle", "Shooter4 g_hobject") -- BREAKICE.scr:95
    ctx:trigger("g_hobject", "On") -- BREAKICE.scr:96
    do return ctx:exit("") end -- BREAKICE.scr:97
end

script.labels["UnderCam"] = function(ctx)
    -- BREAKICE.scr:101
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- BREAKICE.scr:104
    ctx:trigger("g_hobject", "Off") -- BREAKICE.scr:105
    ctx:command("getobjecthandle", "Camera1 g_hobject") -- BREAKICE.scr:106
    ctx:trigger("g_hobject", "On") -- BREAKICE.scr:107
    ctx:trigger("g_hobject", "Move") -- BREAKICE.scr:108
    ctx:command("wait", "1 .7 Destroy15") -- BREAKICE.scr:109
    ctx:command("wait", "2 1.5 Destroy16") -- BREAKICE.scr:110
    ctx:command("wait", "3 2 Destroy25") -- BREAKICE.scr:111
    do return ctx:exit("") end -- BREAKICE.scr:112
end

script.labels["Destroy15"] = function(ctx)
    -- BREAKICE.scr:116
    ctx:command("getobjecthandle", "DestructableBrush15 g_hobject") -- BREAKICE.scr:119
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:120
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:121
    ctx:command("playsound", "Sounds\\Events\\iceimpact.wav, DoNothing, 100, 9000, FALSE, 100") -- BREAKICE.scr:122
    do return ctx:exit("") end -- BREAKICE.scr:123
end

script.labels["Destroy16"] = function(ctx)
    -- BREAKICE.scr:126
    ctx:command("getobjecthandle", "DestructableBrush26 g_hobject") -- BREAKICE.scr:129
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:130
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:131
    ctx:command("playsound", "Sounds\\Events\\iceimpact.wav, DoNothing, 100, 9000, FALSE, 100") -- BREAKICE.scr:132
    do return ctx:exit("") end -- BREAKICE.scr:133
end

script.labels["Destroy25"] = function(ctx)
    -- BREAKICE.scr:136
    ctx:command("getobjecthandle", "DestructableBrush25 g_hobject") -- BREAKICE.scr:139
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:140
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:141
    ctx:command("playsound", "Sounds\\Events\\iceimpact.wav, DoNothing, 100, 9000, FALSE, 100") -- BREAKICE.scr:142
    do return ctx:exit("") end -- BREAKICE.scr:143
end

script.labels["OnCam3"] = function(ctx)
    -- BREAKICE.scr:146
    ctx:command("getobjecthandle", "Camera1 g_hobject") -- BREAKICE.scr:149
    ctx:trigger("g_hobject", "Off") -- BREAKICE.scr:150
    ctx:command("getobjecthandle", "Camera2 g_hobject") -- BREAKICE.scr:151
    ctx:trigger("g_hobject", "On") -- BREAKICE.scr:152
    ctx:command("wait", "1 1.1 Group1") -- BREAKICE.scr:153
    ctx:command("wait", "2 1.11 Group2") -- BREAKICE.scr:154
    ctx:command("wait", "3 1.12 Group3") -- BREAKICE.scr:155
    ctx:command("wait", "4 3 OnDone") -- BREAKICE.scr:156
    do return ctx:exit("") end -- BREAKICE.scr:157
end

script.labels["Group1"] = function(ctx)
    -- BREAKICE.scr:160
    ctx:command("playsound", "Sounds\\Events\\iceimpact.wav, DoNothing, 100, 9000, FALSE, 100") -- BREAKICE.scr:163
    ctx:command("getobjecthandle", "DestructableBrush17 g_hobject") -- BREAKICE.scr:164
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:165
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:166
    ctx:command("getobjecthandle", "DestructableBrush18 g_hobject") -- BREAKICE.scr:167
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:168
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:169
    ctx:command("getobjecthandle", "DestructableBrush27 g_hobject") -- BREAKICE.scr:170
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:171
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:172
    ctx:command("getobjecthandle", "DestructableBrush16 g_hobject") -- BREAKICE.scr:173
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:174
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:175
    ctx:command("getobjecthandle", "DestructableBrush14 g_hobject") -- BREAKICE.scr:177
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:178
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:179
    ctx:command("getobjecthandle", "DestructableBrush21 g_hobject") -- BREAKICE.scr:180
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:181
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:182
    ctx:command("getobjecthandle", "DestructableBrush24 g_hobject") -- BREAKICE.scr:183
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:184
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:185
    ctx:command("getobjecthandle", "DestructableBrush30 g_hobject") -- BREAKICE.scr:186
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:187
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:188
    ctx:command("getobjecthandle", "DestructableBrush33 g_hobject") -- BREAKICE.scr:189
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:190
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:191
    ctx:command("getobjecthandle", "DestructableBrush36 g_hobject") -- BREAKICE.scr:192
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:193
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:194
    ctx:command("getobjecthandle", "DestructableBrush39 g_hobject") -- BREAKICE.scr:195
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:196
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:197
    ctx:command("getobjecthandle", "DestructableBrush42 g_hobject") -- BREAKICE.scr:198
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:199
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:200
    ctx:command("getobjecthandle", "DestructableBrush45 g_hobject") -- BREAKICE.scr:201
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:202
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:203
    ctx:command("getobjecthandle", "DestructableBrush9 g_hobject") -- BREAKICE.scr:204
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:205
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:206
    do return ctx:exit("") end -- BREAKICE.scr:207
end

script.labels["Group2"] = function(ctx)
    -- BREAKICE.scr:210
    ctx:command("playsound", "Sounds\\Events\\iceimpact.wav, DoNothing, 100, 9000, FALSE, 100") -- BREAKICE.scr:213
    ctx:command("getobjecthandle", "DestructableBrush19 g_hobject") -- BREAKICE.scr:214
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:215
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:216
    ctx:command("getobjecthandle", "DestructableBrush22 g_hobject") -- BREAKICE.scr:217
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:218
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:219
    ctx:command("getobjecthandle", "DestructableBrush28 g_hobject") -- BREAKICE.scr:220
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:221
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:222
    ctx:command("getobjecthandle", "DestructableBrush31 g_hobject") -- BREAKICE.scr:223
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:224
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:225
    ctx:command("getobjecthandle", "DestructableBrush34 g_hobject") -- BREAKICE.scr:226
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:227
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:228
    ctx:command("getobjecthandle", "DestructableBrush37 g_hobject") -- BREAKICE.scr:229
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:230
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:231
    ctx:command("getobjecthandle", "DestructableBrush40 g_hobject") -- BREAKICE.scr:232
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:233
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:234
    ctx:command("getobjecthandle", "DestructableBrush43 g_hobject") -- BREAKICE.scr:235
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:236
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:237
    ctx:command("getobjecthandle", "DestructableBrush7 g_hobject") -- BREAKICE.scr:238
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:239
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:240
    do return ctx:exit("") end -- BREAKICE.scr:241
end

script.labels["Group3"] = function(ctx)
    -- BREAKICE.scr:244
    ctx:command("playsound", "Sounds\\Events\\iceimpact.wav, DoNothing, 100, 9000, FALSE, 100") -- BREAKICE.scr:247
    ctx:command("getobjecthandle", "DestructableBrush20 g_hobject") -- BREAKICE.scr:248
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:249
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:250
    ctx:command("getobjecthandle", "DestructableBrush23 g_hobject") -- BREAKICE.scr:251
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:252
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:253
    ctx:command("getobjecthandle", "DestructableBrush29 g_hobject") -- BREAKICE.scr:254
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:255
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:256
    ctx:command("getobjecthandle", "DestructableBrush32 g_hobject") -- BREAKICE.scr:257
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:258
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:259
    ctx:command("getobjecthandle", "DestructableBrush35 g_hobject") -- BREAKICE.scr:260
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:261
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:262
    ctx:command("getobjecthandle", "DestructableBrush38 g_hobject") -- BREAKICE.scr:263
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:264
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:265
    ctx:command("getobjecthandle", "DestructableBrush41 g_hobject") -- BREAKICE.scr:266
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:267
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:268
    ctx:command("getobjecthandle", "DestructableBrush44 g_hobject") -- BREAKICE.scr:269
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:270
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:271
    ctx:command("getobjecthandle", "DestructableBrush8 g_hobject") -- BREAKICE.scr:272
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:273
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:274
    do return ctx:exit("") end -- BREAKICE.scr:275
end

script.labels["OnDone"] = function(ctx)
    -- BREAKICE.scr:278
    ctx:command("screenfadeout", "1") -- BREAKICE.scr:281
    mm9.gosub(script, ctx, "GivePoints") -- BREAKICE.scr:282
    ctx:command("wait", "1 1.5 Done") -- BREAKICE.scr:283
    do return ctx:exit("") end -- BREAKICE.scr:284
end

script.labels["Done"] = function(ctx)
    -- BREAKICE.scr:287
    ctx:command("letterbox", "false") -- BREAKICE.scr:290
    ctx:command("getobjecthandle", "Camera2 g_hobject") -- BREAKICE.scr:291
    ctx:trigger("g_hobject", "Off") -- BREAKICE.scr:292
    ctx:command("screenfadein", "1") -- BREAKICE.scr:293
    do return ctx:exit("") end -- BREAKICE.scr:294
end

script.labels["Init"] = function(ctx)
    -- BREAKICE.scr:297
    if not ctx:hasKey(72) then -- BREAKICE.scr:300-301
        do return ctx:exit("") end -- BREAKICE.scr:302
    end -- BREAKICE.scr:303
    ctx:command("getobjecthandle", "DestructableBrush20 g_hobject") -- BREAKICE.scr:306
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:307
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:308
    ctx:command("getobjecthandle", "DestructableBrush23 g_hobject") -- BREAKICE.scr:309
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:310
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:311
    ctx:command("getobjecthandle", "DestructableBrush29 g_hobject") -- BREAKICE.scr:312
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:313
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:314
    ctx:command("getobjecthandle", "DestructableBrush32 g_hobject") -- BREAKICE.scr:315
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:316
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:317
    ctx:command("getobjecthandle", "DestructableBrush35 g_hobject") -- BREAKICE.scr:318
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:319
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:320
    ctx:command("getobjecthandle", "DestructableBrush38 g_hobject") -- BREAKICE.scr:321
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:322
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:323
    ctx:command("getobjecthandle", "DestructableBrush41 g_hobject") -- BREAKICE.scr:324
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:325
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:326
    ctx:command("getobjecthandle", "DestructableBrush44 g_hobject") -- BREAKICE.scr:327
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:328
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:329
    ctx:command("getobjecthandle", "DestructableBrush8 g_hobject") -- BREAKICE.scr:330
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:331
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:332
    ctx:command("getobjecthandle", "DestructableBrush19 g_hobject") -- BREAKICE.scr:333
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:334
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:335
    ctx:command("getobjecthandle", "DestructableBrush22 g_hobject") -- BREAKICE.scr:336
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:337
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:338
    ctx:command("getobjecthandle", "DestructableBrush28 g_hobject") -- BREAKICE.scr:339
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:340
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:341
    ctx:command("getobjecthandle", "DestructableBrush31 g_hobject") -- BREAKICE.scr:342
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:343
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:344
    ctx:command("getobjecthandle", "DestructableBrush34 g_hobject") -- BREAKICE.scr:345
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:346
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:347
    ctx:command("getobjecthandle", "DestructableBrush37 g_hobject") -- BREAKICE.scr:348
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:349
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:350
    ctx:command("getobjecthandle", "DestructableBrush40 g_hobject") -- BREAKICE.scr:351
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:352
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:353
    ctx:command("getobjecthandle", "DestructableBrush43 g_hobject") -- BREAKICE.scr:354
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:355
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:356
    ctx:command("getobjecthandle", "DestructableBrush7 g_hobject") -- BREAKICE.scr:357
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:358
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:359
    ctx:command("getobjecthandle", "DestructableBrush14 g_hobject") -- BREAKICE.scr:360
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:361
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:362
    ctx:command("getobjecthandle", "DestructableBrush21 g_hobject") -- BREAKICE.scr:363
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:364
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:365
    ctx:command("getobjecthandle", "DestructableBrush24 g_hobject") -- BREAKICE.scr:366
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:367
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:368
    ctx:command("getobjecthandle", "DestructableBrush30 g_hobject") -- BREAKICE.scr:369
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:370
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:371
    ctx:command("getobjecthandle", "DestructableBrush33 g_hobject") -- BREAKICE.scr:372
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:373
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:374
    ctx:command("getobjecthandle", "DestructableBrush36 g_hobject") -- BREAKICE.scr:375
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:376
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:377
    ctx:command("getobjecthandle", "DestructableBrush39 g_hobject") -- BREAKICE.scr:378
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:379
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:380
    ctx:command("getobjecthandle", "DestructableBrush42 g_hobject") -- BREAKICE.scr:381
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:382
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:383
    ctx:command("getobjecthandle", "DestructableBrush45 g_hobject") -- BREAKICE.scr:384
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:385
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:386
    ctx:command("getobjecthandle", "DestructableBrush9 g_hobject") -- BREAKICE.scr:387
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:388
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:389
    ctx:command("getobjecthandle", "DestructableBrush25 g_hobject") -- BREAKICE.scr:390
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:391
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:392
    ctx:command("getobjecthandle", "DestructableBrush26 g_hobject") -- BREAKICE.scr:393
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:394
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:395
    ctx:command("getobjecthandle", "DestructableBrush15 g_hobject") -- BREAKICE.scr:396
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:397
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:398
    ctx:command("getobjecthandle", "DestructableBrush6 g_hobject") -- BREAKICE.scr:399
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:400
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:401
    ctx:command("getobjecthandle", "DestructableBrush17 g_hobject") -- BREAKICE.scr:402
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:403
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:404
    ctx:command("getobjecthandle", "DestructableBrush18 g_hobject") -- BREAKICE.scr:405
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:406
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:407
    ctx:command("getobjecthandle", "DestructableBrush16 g_hobject") -- BREAKICE.scr:408
    ctx:trigger("g_hobject", "DamageOn") -- BREAKICE.scr:409
    ctx:trigger("g_hobject", "destroy") -- BREAKICE.scr:410
    ctx:command("getobjecthandle", "DestructableProp0 g_hobject") -- BREAKICE.scr:411
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:412
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
    ctx:command("onpoststartworld", "Init") -- BREAKICE.scr:453
    ctx:command("onpostminisaveload", "Init") -- BREAKICE.scr:454
    ctx:command("onpostsaveload", "Init") -- BREAKICE.scr:455
    ctx:command("wait", "1 .1 Init") -- BREAKICE.scr:456
    do return ctx:exit("") end -- BREAKICE.scr:457
end

script.labels["Init"] = function(ctx)
    -- BREAKICE.scr:461
    -- overloaded -- Bones
    -- kills competing waits
    ctx:command("wait", "1 0 DoNothing") -- BREAKICE.scr:466
    if not ctx:hasKey(72) then -- BREAKICE.scr:468-469
        if not ctx:hasKey(174) then -- BREAKICE.scr:470-471
            do return ctx:exit("") end -- BREAKICE.scr:472
        end -- BREAKICE.scr:473
    end -- BREAKICE.scr:474
    ctx:command("set", "g_nPad2 1") -- BREAKICE.scr:476
    -- timer overloaded intentionally
    ctx:command("wait", "1 1 OnStart") -- BREAKICE.scr:478
    do return ctx:exit("") end -- BREAKICE.scr:479
end

script.labels["OnStart"] = function(ctx)
    -- BREAKICE.scr:482
    -- overloaded -- Bones
    if ctx:condition("g_nPad2 == 0") then -- BREAKICE.scr:486
        ctx:command("wait", "1 2 Start") -- BREAKICE.scr:487
        do return ctx:exit("") end -- BREAKICE.scr:488
    end -- BREAKICE.scr:489
    ctx:command("set", "g_nPad2 0") -- BREAKICE.scr:491
    ctx:command("getobjecthandle", "DestructableBrush20 g_hobject") -- BREAKICE.scr:493
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:494
    ctx:command("getobjecthandle", "DestructableBrush23 g_hobject") -- BREAKICE.scr:496
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:497
    ctx:command("getobjecthandle", "DestructableBrush29 g_hobject") -- BREAKICE.scr:499
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:500
    ctx:command("getobjecthandle", "DestructableBrush32 g_hobject") -- BREAKICE.scr:502
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:503
    ctx:command("getobjecthandle", "DestructableBrush35 g_hobject") -- BREAKICE.scr:505
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:506
    ctx:command("getobjecthandle", "DestructableBrush38 g_hobject") -- BREAKICE.scr:508
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:509
    ctx:command("getobjecthandle", "DestructableBrush41 g_hobject") -- BREAKICE.scr:511
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:512
    ctx:command("getobjecthandle", "DestructableBrush44 g_hobject") -- BREAKICE.scr:514
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:515
    ctx:command("getobjecthandle", "DestructableBrush8 g_hobject") -- BREAKICE.scr:517
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:518
    ctx:command("getobjecthandle", "DestructableBrush19 g_hobject") -- BREAKICE.scr:520
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:521
    ctx:command("getobjecthandle", "DestructableBrush22 g_hobject") -- BREAKICE.scr:523
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:524
    ctx:command("getobjecthandle", "DestructableBrush28 g_hobject") -- BREAKICE.scr:526
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:527
    ctx:command("getobjecthandle", "DestructableBrush31 g_hobject") -- BREAKICE.scr:529
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:530
    ctx:command("getobjecthandle", "DestructableBrush34 g_hobject") -- BREAKICE.scr:532
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:533
    ctx:command("getobjecthandle", "DestructableBrush37 g_hobject") -- BREAKICE.scr:535
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:536
    ctx:command("getobjecthandle", "DestructableBrush40 g_hobject") -- BREAKICE.scr:538
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:539
    ctx:command("getobjecthandle", "DestructableBrush43 g_hobject") -- BREAKICE.scr:541
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:542
    ctx:command("getobjecthandle", "DestructableBrush7 g_hobject") -- BREAKICE.scr:544
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:545
    ctx:command("getobjecthandle", "DestructableBrush14 g_hobject") -- BREAKICE.scr:547
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:548
    ctx:command("getobjecthandle", "DestructableBrush21 g_hobject") -- BREAKICE.scr:550
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:551
    ctx:command("getobjecthandle", "DestructableBrush24 g_hobject") -- BREAKICE.scr:553
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:554
    ctx:command("getobjecthandle", "DestructableBrush30 g_hobject") -- BREAKICE.scr:556
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:557
    ctx:command("getobjecthandle", "DestructableBrush33 g_hobject") -- BREAKICE.scr:559
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:560
    ctx:command("getobjecthandle", "DestructableBrush36 g_hobject") -- BREAKICE.scr:562
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:563
    ctx:command("getobjecthandle", "DestructableBrush39 g_hobject") -- BREAKICE.scr:565
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:566
    ctx:command("getobjecthandle", "DestructableBrush42 g_hobject") -- BREAKICE.scr:568
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:569
    ctx:command("getobjecthandle", "DestructableBrush45 g_hobject") -- BREAKICE.scr:571
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:572
    ctx:command("getobjecthandle", "DestructableBrush9 g_hobject") -- BREAKICE.scr:574
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:575
    ctx:command("getobjecthandle", "DestructableBrush25 g_hobject") -- BREAKICE.scr:577
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:578
    ctx:command("getobjecthandle", "DestructableBrush26 g_hobject") -- BREAKICE.scr:580
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:581
    ctx:command("getobjecthandle", "DestructableBrush15 g_hobject") -- BREAKICE.scr:583
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:584
    ctx:command("getobjecthandle", "DestructableBrush6 g_hobject") -- BREAKICE.scr:586
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:587
    ctx:command("getobjecthandle", "DestructableBrush17 g_hobject") -- BREAKICE.scr:589
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:590
    ctx:command("getobjecthandle", "DestructableBrush18 g_hobject") -- BREAKICE.scr:592
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:593
    ctx:command("getobjecthandle", "DestructableBrush16 g_hobject") -- BREAKICE.scr:595
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:596
    ctx:command("getobjecthandle", "DestructableProp0 g_hobject") -- BREAKICE.scr:598
    ctx:command("removeobject", "g_hobject") -- BREAKICE.scr:599
    do return ctx:exit("") end -- BREAKICE.scr:601
end

return script
