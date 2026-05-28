-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RONDO.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- rondo.scr
-- timmy
-- Plays the intro to Rondo ala turk
script.labels["OnPlay"] = function(ctx)
    -- RONDO.scr:12
    ctx:command("getobjecthandle", "Bell1, g_hobject") -- RONDO.scr:15
    ctx:trigger("g_hobject", "use") -- RONDO.scr:16
    ctx:command("wait", "1 .5, 1") -- RONDO.scr:17
    do return ctx:exit("") end -- RONDO.scr:18
end

script.labels["1"] = function(ctx)
    -- RONDO.scr:21
    ctx:command("getobjecthandle", "Bell2, g_hobject") -- RONDO.scr:24
    ctx:trigger("g_hobject", "use") -- RONDO.scr:25
    ctx:command("wait", "1 .5, 2") -- RONDO.scr:26
    do return ctx:exit("") end -- RONDO.scr:28
end

script.labels["2"] = function(ctx)
    -- RONDO.scr:31
    ctx:command("getobjecthandle", "Bell3, g_hobject") -- RONDO.scr:34
    ctx:trigger("g_hobject", "use") -- RONDO.scr:35
    ctx:command("wait", "1 .25, 3") -- RONDO.scr:36
    do return ctx:exit("") end -- RONDO.scr:38
end

script.labels["3"] = function(ctx)
    -- RONDO.scr:43
    ctx:command("getobjecthandle", "Bell4, g_hobject") -- RONDO.scr:46
    ctx:trigger("g_hobject", "use") -- RONDO.scr:47
    ctx:command("wait", "1 .25, 4") -- RONDO.scr:48
    do return ctx:exit("") end -- RONDO.scr:50
end

script.labels["4"] = function(ctx)
    -- RONDO.scr:53
    ctx:command("getobjecthandle", "Bell5, g_hobject") -- RONDO.scr:56
    ctx:trigger("g_hobject", "use") -- RONDO.scr:57
    ctx:command("wait", "1 .5, partII") -- RONDO.scr:58
    do return ctx:exit("") end -- RONDO.scr:60
end

-- Part II
-- exit
script.labels["partII"] = function(ctx)
    -- RONDO.scr:68
    ctx:command("getobjecthandle", "Bell4, g_hobject") -- RONDO.scr:71
    ctx:trigger("g_hobject", "use") -- RONDO.scr:72
    ctx:command("wait", "1 .25, 1-2") -- RONDO.scr:73
    do return ctx:exit("") end -- RONDO.scr:74
end

script.labels["1-2"] = function(ctx)
    -- RONDO.scr:77
    ctx:command("getobjecthandle", "Bell3, g_hobject") -- RONDO.scr:80
    ctx:trigger("g_hobject", "use") -- RONDO.scr:81
    ctx:command("wait", "1 .25, 2-2") -- RONDO.scr:82
    do return ctx:exit("") end -- RONDO.scr:84
end

script.labels["2-2"] = function(ctx)
    -- RONDO.scr:87
    ctx:command("getobjecthandle", "Bell2, g_hobject") -- RONDO.scr:90
    ctx:trigger("g_hobject", "use") -- RONDO.scr:91
    ctx:command("wait", "1 .5, 3-2") -- RONDO.scr:92
    do return ctx:exit("") end -- RONDO.scr:94
end

script.labels["3-2"] = function(ctx)
    -- RONDO.scr:99
    ctx:command("getobjecthandle", "Bell3, g_hobject") -- RONDO.scr:102
    ctx:trigger("g_hobject", "use") -- RONDO.scr:103
    ctx:command("wait", "1 .25, 4-2") -- RONDO.scr:104
    do return ctx:exit("") end -- RONDO.scr:106
end

script.labels["4-2"] = function(ctx)
    -- RONDO.scr:109
    ctx:command("getobjecthandle", "Bell4, g_hobject") -- RONDO.scr:112
    ctx:trigger("g_hobject", "use") -- RONDO.scr:113
    ctx:command("wait", "1 .25, PartIII") -- RONDO.scr:114
    -- Part III
    do return ctx:exit("") end -- RONDO.scr:119
end

script.labels["partIII"] = function(ctx)
    -- RONDO.scr:122
    ctx:command("getobjecthandle", "Bell5, g_hobject") -- RONDO.scr:125
    ctx:trigger("g_hobject", "use") -- RONDO.scr:126
    ctx:command("wait", "1 .5, 1-3") -- RONDO.scr:127
    do return ctx:exit("") end -- RONDO.scr:128
end

script.labels["1-3"] = function(ctx)
    -- RONDO.scr:131
    ctx:command("getobjecthandle", "Bell4, g_hobject") -- RONDO.scr:134
    ctx:trigger("g_hobject", "use") -- RONDO.scr:135
    ctx:command("wait", "1 .25, 2-3") -- RONDO.scr:136
    do return ctx:exit("") end -- RONDO.scr:138
end

script.labels["2-3"] = function(ctx)
    -- RONDO.scr:141
    ctx:command("getobjecthandle", "Bell3, g_hobject") -- RONDO.scr:144
    ctx:trigger("g_hobject", "use") -- RONDO.scr:145
    ctx:command("wait", "1 .25, 3-3") -- RONDO.scr:146
    do return ctx:exit("") end -- RONDO.scr:148
end

script.labels["3-3"] = function(ctx)
    -- RONDO.scr:153
    ctx:command("getobjecthandle", "Bell2, g_hobject") -- RONDO.scr:156
    ctx:trigger("g_hobject", "use") -- RONDO.scr:157
    ctx:command("wait", "1 .5, DoNothing") -- RONDO.scr:158
    do return ctx:exit("") end -- RONDO.scr:160
end

-- PartIV
script.labels["partIV"] = function(ctx)
    -- RONDO.scr:167
    ctx:command("getobjecthandle", "B2, g_hobject") -- RONDO.scr:170
    ctx:trigger("g_hobject", "use") -- RONDO.scr:171
    ctx:command("wait", "1 .25, 1-4") -- RONDO.scr:172
    do return ctx:exit("") end -- RONDO.scr:173
end

script.labels["1-4"] = function(ctx)
    -- RONDO.scr:176
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:179
    ctx:trigger("g_hobject", "use") -- RONDO.scr:180
    ctx:command("wait", "1 .25, 2-4") -- RONDO.scr:181
    do return ctx:exit("") end -- RONDO.scr:183
end

script.labels["2-4"] = function(ctx)
    -- RONDO.scr:186
    ctx:command("getobjecthandle", "G#2, g_hobject") -- RONDO.scr:189
    ctx:trigger("g_hobject", "use") -- RONDO.scr:190
    ctx:command("wait", "1 .25, 3-4") -- RONDO.scr:191
    do return ctx:exit("") end -- RONDO.scr:193
end

script.labels["3-4"] = function(ctx)
    -- RONDO.scr:198
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:201
    ctx:trigger("g_hobject", "use") -- RONDO.scr:202
    ctx:command("wait", "1 .25, 4-4") -- RONDO.scr:203
    do return ctx:exit("") end -- RONDO.scr:204
end

script.labels["4-4"] = function(ctx)
    -- RONDO.scr:208
    ctx:command("getobjecthandle", "B2, g_hobject") -- RONDO.scr:211
    ctx:trigger("g_hobject", "use") -- RONDO.scr:212
    ctx:command("wait", "1 .25, 5-4") -- RONDO.scr:213
    do return ctx:exit("") end -- RONDO.scr:214
end

script.labels["5-4"] = function(ctx)
    -- RONDO.scr:217
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:220
    ctx:trigger("g_hobject", "use") -- RONDO.scr:221
    ctx:command("wait", "1 .25, 6-4") -- RONDO.scr:222
    do return ctx:exit("") end -- RONDO.scr:224
end

script.labels["6-4"] = function(ctx)
    -- RONDO.scr:227
    ctx:command("getobjecthandle", "G#2, g_hobject") -- RONDO.scr:230
    ctx:trigger("g_hobject", "use") -- RONDO.scr:231
    ctx:command("wait", "1 .25, 7-4") -- RONDO.scr:232
    do return ctx:exit("") end -- RONDO.scr:234
end

script.labels["7-4"] = function(ctx)
    -- RONDO.scr:239
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:242
    ctx:trigger("g_hobject", "use") -- RONDO.scr:243
    ctx:command("wait", "1 .25, 8-4") -- RONDO.scr:244
    do return ctx:exit("") end -- RONDO.scr:246
end

script.labels["8-4"] = function(ctx)
    -- RONDO.scr:249
    ctx:command("getobjecthandle", "C2, g_hobject") -- RONDO.scr:252
    ctx:trigger("g_hobject", "use") -- RONDO.scr:253
    ctx:command("wait", "1 .75, partV") -- RONDO.scr:254
    do return ctx:exit("") end -- RONDO.scr:256
end

-- PartV
script.labels["partV"] = function(ctx)
    -- RONDO.scr:265
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:268
    ctx:trigger("g_hobject", "use") -- RONDO.scr:269
    ctx:command("wait", "1 .5, 1-5") -- RONDO.scr:270
    do return ctx:exit("") end -- RONDO.scr:271
end

script.labels["1-5"] = function(ctx)
    -- RONDO.scr:274
    ctx:command("getobjecthandle", "C2, g_hobject") -- RONDO.scr:277
    ctx:trigger("g_hobject", "use") -- RONDO.scr:278
    ctx:command("wait", "1 .5, 2-5") -- RONDO.scr:279
    do return ctx:exit("") end -- RONDO.scr:281
end

script.labels["2-5"] = function(ctx)
    -- RONDO.scr:284
    ctx:command("getobjecthandle", "G2, g_hobject") -- RONDO.scr:287
    ctx:trigger("g_hobject", "use") -- RONDO.scr:288
    ctx:command("getobjecthandle", "B2, g_hobject") -- RONDO.scr:289
    ctx:trigger("g_hobject", "use") -- RONDO.scr:290
    ctx:command("wait", "1 .5, 3-5") -- RONDO.scr:291
    do return ctx:exit("") end -- RONDO.scr:293
end

script.labels["3-5"] = function(ctx)
    -- RONDO.scr:298
    ctx:command("getobjecthandle", "F#2, g_hobject") -- RONDO.scr:301
    ctx:trigger("g_hobject", "use") -- RONDO.scr:302
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:303
    ctx:trigger("g_hobject", "use") -- RONDO.scr:304
    ctx:command("wait", "1 .5, 4-5") -- RONDO.scr:305
    do return ctx:exit("") end -- RONDO.scr:306
end

script.labels["4-5"] = function(ctx)
    -- RONDO.scr:310
    ctx:command("getobjecthandle", "E1, g_hobject") -- RONDO.scr:313
    ctx:trigger("g_hobject", "use") -- RONDO.scr:314
    ctx:command("getobjecthandle", "G2, g_hobject") -- RONDO.scr:315
    ctx:trigger("g_hobject", "use") -- RONDO.scr:316
    ctx:command("wait", "1 .5, 5-5") -- RONDO.scr:317
    do return ctx:exit("") end -- RONDO.scr:318
end

script.labels["5-5"] = function(ctx)
    -- RONDO.scr:321
    ctx:command("getobjecthandle", "F#2, g_hobject") -- RONDO.scr:324
    ctx:trigger("g_hobject", "use") -- RONDO.scr:325
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:326
    ctx:trigger("g_hobject", "use") -- RONDO.scr:327
    ctx:command("wait", "1 .5, 6-5") -- RONDO.scr:328
    do return ctx:exit("") end -- RONDO.scr:330
end

script.labels["6-5"] = function(ctx)
    -- RONDO.scr:333
    ctx:command("getobjecthandle", "G2, g_hobject") -- RONDO.scr:336
    ctx:trigger("g_hobject", "use") -- RONDO.scr:337
    ctx:command("getobjecthandle", "B2, g_hobject") -- RONDO.scr:338
    ctx:trigger("g_hobject", "use") -- RONDO.scr:339
    ctx:command("wait", "1 .5, 7-5") -- RONDO.scr:340
    do return ctx:exit("") end -- RONDO.scr:342
end

script.labels["7-5"] = function(ctx)
    -- RONDO.scr:347
    ctx:command("getobjecthandle", "F#2, g_hobject") -- RONDO.scr:350
    ctx:trigger("g_hobject", "use") -- RONDO.scr:351
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:352
    ctx:trigger("g_hobject", "use") -- RONDO.scr:353
    ctx:command("wait", "1 .5, 8-5") -- RONDO.scr:354
    do return ctx:exit("") end -- RONDO.scr:356
end

script.labels["8-5"] = function(ctx)
    -- RONDO.scr:359
    ctx:command("getobjecthandle", "E1, g_hobject") -- RONDO.scr:362
    ctx:trigger("g_hobject", "use") -- RONDO.scr:363
    ctx:command("getobjecthandle", "G2, g_hobject") -- RONDO.scr:364
    ctx:trigger("g_hobject", "use") -- RONDO.scr:365
    ctx:command("wait", "1 .5, 9-5") -- RONDO.scr:366
    do return ctx:exit("") end -- RONDO.scr:368
end

script.labels["9-5"] = function(ctx)
    -- RONDO.scr:373
    ctx:command("getobjecthandle", "F#2, g_hobject") -- RONDO.scr:376
    ctx:trigger("g_hobject", "use") -- RONDO.scr:377
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:378
    ctx:trigger("g_hobject", "use") -- RONDO.scr:379
    ctx:command("wait", "1 .5, 10-5") -- RONDO.scr:380
    do return ctx:exit("") end -- RONDO.scr:381
end

script.labels["10-5"] = function(ctx)
    -- RONDO.scr:385
    ctx:command("getobjecthandle", "G2, g_hobject") -- RONDO.scr:388
    ctx:trigger("g_hobject", "use") -- RONDO.scr:389
    ctx:command("getobjecthandle", "B2, g_hobject") -- RONDO.scr:390
    ctx:trigger("g_hobject", "use") -- RONDO.scr:391
    ctx:command("wait", "1 .5, 11-5") -- RONDO.scr:392
    do return ctx:exit("") end -- RONDO.scr:393
end

script.labels["11-5"] = function(ctx)
    -- RONDO.scr:396
    ctx:command("getobjecthandle", "F#2, g_hobject") -- RONDO.scr:399
    ctx:trigger("g_hobject", "use") -- RONDO.scr:400
    ctx:command("getobjecthandle", "A2, g_hobject") -- RONDO.scr:401
    ctx:trigger("g_hobject", "use") -- RONDO.scr:402
    ctx:command("wait", "1 .5, 12-5") -- RONDO.scr:403
    do return ctx:exit("") end -- RONDO.scr:405
end

script.labels["12-5"] = function(ctx)
    -- RONDO.scr:408
    ctx:command("getobjecthandle", "E1, g_hobject") -- RONDO.scr:411
    ctx:trigger("g_hobject", "use") -- RONDO.scr:412
    ctx:command("getobjecthandle", "G2, g_hobject") -- RONDO.scr:413
    ctx:trigger("g_hobject", "use") -- RONDO.scr:414
    ctx:command("wait", "1 .5, 13-5") -- RONDO.scr:415
    do return ctx:exit("") end -- RONDO.scr:417
end

script.labels["13-5"] = function(ctx)
    -- RONDO.scr:422
    ctx:command("getobjecthandle", "D#2, g_hobject") -- RONDO.scr:425
    ctx:trigger("g_hobject", "use") -- RONDO.scr:426
    ctx:command("getobjecthandle", "F#2, g_hobject") -- RONDO.scr:427
    ctx:trigger("g_hobject", "use") -- RONDO.scr:428
    ctx:command("wait", "1 .5, 14-5") -- RONDO.scr:429
    do return ctx:exit("") end -- RONDO.scr:431
end

script.labels["14-5"] = function(ctx)
    -- RONDO.scr:434
    ctx:command("getobjecthandle", "E1, g_hobject") -- RONDO.scr:437
    ctx:trigger("g_hobject", "use") -- RONDO.scr:438
    -- wait 1 .5, 8-5
    do return ctx:exit("") end -- RONDO.scr:441
end

script.labels["Main"] = function(ctx)
    -- RONDO.scr:445
    -- TRACEON
    ctx:command("set", "counter, 0") -- RONDO.scr:450
    ctx:addTrigger("Use", "OnPlay") -- RONDO.scr:451
    do return ctx:exit("") end -- RONDO.scr:452
end

return script
