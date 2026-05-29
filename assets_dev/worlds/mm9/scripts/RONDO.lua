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
    ctx:object("Bell1"):trigger("use") -- RONDO.scr:15-16
    ctx:wait(1, .5, "1") -- RONDO.scr:17
    do return ctx:exit("") end -- RONDO.scr:18
end

script.labels["1"] = function(ctx)
    -- RONDO.scr:21
    ctx:object("Bell2"):trigger("use") -- RONDO.scr:24-25
    ctx:wait(1, .5, "2") -- RONDO.scr:26
    do return ctx:exit("") end -- RONDO.scr:28
end

script.labels["2"] = function(ctx)
    -- RONDO.scr:31
    ctx:object("Bell3"):trigger("use") -- RONDO.scr:34-35
    ctx:wait(1, .25, "3") -- RONDO.scr:36
    do return ctx:exit("") end -- RONDO.scr:38
end

script.labels["3"] = function(ctx)
    -- RONDO.scr:43
    ctx:object("Bell4"):trigger("use") -- RONDO.scr:46-47
    ctx:wait(1, .25, "4") -- RONDO.scr:48
    do return ctx:exit("") end -- RONDO.scr:50
end

script.labels["4"] = function(ctx)
    -- RONDO.scr:53
    ctx:object("Bell5"):trigger("use") -- RONDO.scr:56-57
    ctx:wait(1, .5, "partII") -- RONDO.scr:58
    do return ctx:exit("") end -- RONDO.scr:60
end

-- Part II
-- exit
script.labels["partII"] = function(ctx)
    -- RONDO.scr:68
    ctx:object("Bell4"):trigger("use") -- RONDO.scr:71-72
    ctx:wait(1, .25, "1-2") -- RONDO.scr:73
    do return ctx:exit("") end -- RONDO.scr:74
end

script.labels["1-2"] = function(ctx)
    -- RONDO.scr:77
    ctx:object("Bell3"):trigger("use") -- RONDO.scr:80-81
    ctx:wait(1, .25, "2-2") -- RONDO.scr:82
    do return ctx:exit("") end -- RONDO.scr:84
end

script.labels["2-2"] = function(ctx)
    -- RONDO.scr:87
    ctx:object("Bell2"):trigger("use") -- RONDO.scr:90-91
    ctx:wait(1, .5, "3-2") -- RONDO.scr:92
    do return ctx:exit("") end -- RONDO.scr:94
end

script.labels["3-2"] = function(ctx)
    -- RONDO.scr:99
    ctx:object("Bell3"):trigger("use") -- RONDO.scr:102-103
    ctx:wait(1, .25, "4-2") -- RONDO.scr:104
    do return ctx:exit("") end -- RONDO.scr:106
end

script.labels["4-2"] = function(ctx)
    -- RONDO.scr:109
    ctx:object("Bell4"):trigger("use") -- RONDO.scr:112-113
    ctx:wait(1, .25, "PartIII") -- RONDO.scr:114
    -- Part III
    do return ctx:exit("") end -- RONDO.scr:119
end

script.labels["partIII"] = function(ctx)
    -- RONDO.scr:122
    ctx:object("Bell5"):trigger("use") -- RONDO.scr:125-126
    ctx:wait(1, .5, "1-3") -- RONDO.scr:127
    do return ctx:exit("") end -- RONDO.scr:128
end

script.labels["1-3"] = function(ctx)
    -- RONDO.scr:131
    ctx:object("Bell4"):trigger("use") -- RONDO.scr:134-135
    ctx:wait(1, .25, "2-3") -- RONDO.scr:136
    do return ctx:exit("") end -- RONDO.scr:138
end

script.labels["2-3"] = function(ctx)
    -- RONDO.scr:141
    ctx:object("Bell3"):trigger("use") -- RONDO.scr:144-145
    ctx:wait(1, .25, "3-3") -- RONDO.scr:146
    do return ctx:exit("") end -- RONDO.scr:148
end

script.labels["3-3"] = function(ctx)
    -- RONDO.scr:153
    ctx:object("Bell2"):trigger("use") -- RONDO.scr:156-157
    ctx:wait(1, .5, "DoNothing") -- RONDO.scr:158
    do return ctx:exit("") end -- RONDO.scr:160
end

-- PartIV
script.labels["partIV"] = function(ctx)
    -- RONDO.scr:167
    ctx:object("B2"):trigger("use") -- RONDO.scr:170-171
    ctx:wait(1, .25, "1-4") -- RONDO.scr:172
    do return ctx:exit("") end -- RONDO.scr:173
end

script.labels["1-4"] = function(ctx)
    -- RONDO.scr:176
    ctx:object("A2"):trigger("use") -- RONDO.scr:179-180
    ctx:wait(1, .25, "2-4") -- RONDO.scr:181
    do return ctx:exit("") end -- RONDO.scr:183
end

script.labels["2-4"] = function(ctx)
    -- RONDO.scr:186
    ctx:object("G#2"):trigger("use") -- RONDO.scr:189-190
    ctx:wait(1, .25, "3-4") -- RONDO.scr:191
    do return ctx:exit("") end -- RONDO.scr:193
end

script.labels["3-4"] = function(ctx)
    -- RONDO.scr:198
    ctx:object("A2"):trigger("use") -- RONDO.scr:201-202
    ctx:wait(1, .25, "4-4") -- RONDO.scr:203
    do return ctx:exit("") end -- RONDO.scr:204
end

script.labels["4-4"] = function(ctx)
    -- RONDO.scr:208
    ctx:object("B2"):trigger("use") -- RONDO.scr:211-212
    ctx:wait(1, .25, "5-4") -- RONDO.scr:213
    do return ctx:exit("") end -- RONDO.scr:214
end

script.labels["5-4"] = function(ctx)
    -- RONDO.scr:217
    ctx:object("A2"):trigger("use") -- RONDO.scr:220-221
    ctx:wait(1, .25, "6-4") -- RONDO.scr:222
    do return ctx:exit("") end -- RONDO.scr:224
end

script.labels["6-4"] = function(ctx)
    -- RONDO.scr:227
    ctx:object("G#2"):trigger("use") -- RONDO.scr:230-231
    ctx:wait(1, .25, "7-4") -- RONDO.scr:232
    do return ctx:exit("") end -- RONDO.scr:234
end

script.labels["7-4"] = function(ctx)
    -- RONDO.scr:239
    ctx:object("A2"):trigger("use") -- RONDO.scr:242-243
    ctx:wait(1, .25, "8-4") -- RONDO.scr:244
    do return ctx:exit("") end -- RONDO.scr:246
end

script.labels["8-4"] = function(ctx)
    -- RONDO.scr:249
    ctx:object("C2"):trigger("use") -- RONDO.scr:252-253
    ctx:wait(1, .75, "partV") -- RONDO.scr:254
    do return ctx:exit("") end -- RONDO.scr:256
end

-- PartV
script.labels["partV"] = function(ctx)
    -- RONDO.scr:265
    ctx:object("A2"):trigger("use") -- RONDO.scr:268-269
    ctx:wait(1, .5, "1-5") -- RONDO.scr:270
    do return ctx:exit("") end -- RONDO.scr:271
end

script.labels["1-5"] = function(ctx)
    -- RONDO.scr:274
    ctx:object("C2"):trigger("use") -- RONDO.scr:277-278
    ctx:wait(1, .5, "2-5") -- RONDO.scr:279
    do return ctx:exit("") end -- RONDO.scr:281
end

script.labels["2-5"] = function(ctx)
    -- RONDO.scr:284
    ctx:object("G2"):trigger("use") -- RONDO.scr:287-288
    ctx:object("B2"):trigger("use") -- RONDO.scr:289-290
    ctx:wait(1, .5, "3-5") -- RONDO.scr:291
    do return ctx:exit("") end -- RONDO.scr:293
end

script.labels["3-5"] = function(ctx)
    -- RONDO.scr:298
    ctx:object("F#2"):trigger("use") -- RONDO.scr:301-302
    ctx:object("A2"):trigger("use") -- RONDO.scr:303-304
    ctx:wait(1, .5, "4-5") -- RONDO.scr:305
    do return ctx:exit("") end -- RONDO.scr:306
end

script.labels["4-5"] = function(ctx)
    -- RONDO.scr:310
    ctx:object("E1"):trigger("use") -- RONDO.scr:313-314
    ctx:object("G2"):trigger("use") -- RONDO.scr:315-316
    ctx:wait(1, .5, "5-5") -- RONDO.scr:317
    do return ctx:exit("") end -- RONDO.scr:318
end

script.labels["5-5"] = function(ctx)
    -- RONDO.scr:321
    ctx:object("F#2"):trigger("use") -- RONDO.scr:324-325
    ctx:object("A2"):trigger("use") -- RONDO.scr:326-327
    ctx:wait(1, .5, "6-5") -- RONDO.scr:328
    do return ctx:exit("") end -- RONDO.scr:330
end

script.labels["6-5"] = function(ctx)
    -- RONDO.scr:333
    ctx:object("G2"):trigger("use") -- RONDO.scr:336-337
    ctx:object("B2"):trigger("use") -- RONDO.scr:338-339
    ctx:wait(1, .5, "7-5") -- RONDO.scr:340
    do return ctx:exit("") end -- RONDO.scr:342
end

script.labels["7-5"] = function(ctx)
    -- RONDO.scr:347
    ctx:object("F#2"):trigger("use") -- RONDO.scr:350-351
    ctx:object("A2"):trigger("use") -- RONDO.scr:352-353
    ctx:wait(1, .5, "8-5") -- RONDO.scr:354
    do return ctx:exit("") end -- RONDO.scr:356
end

script.labels["8-5"] = function(ctx)
    -- RONDO.scr:359
    ctx:object("E1"):trigger("use") -- RONDO.scr:362-363
    ctx:object("G2"):trigger("use") -- RONDO.scr:364-365
    ctx:wait(1, .5, "9-5") -- RONDO.scr:366
    do return ctx:exit("") end -- RONDO.scr:368
end

script.labels["9-5"] = function(ctx)
    -- RONDO.scr:373
    ctx:object("F#2"):trigger("use") -- RONDO.scr:376-377
    ctx:object("A2"):trigger("use") -- RONDO.scr:378-379
    ctx:wait(1, .5, "10-5") -- RONDO.scr:380
    do return ctx:exit("") end -- RONDO.scr:381
end

script.labels["10-5"] = function(ctx)
    -- RONDO.scr:385
    ctx:object("G2"):trigger("use") -- RONDO.scr:388-389
    ctx:object("B2"):trigger("use") -- RONDO.scr:390-391
    ctx:wait(1, .5, "11-5") -- RONDO.scr:392
    do return ctx:exit("") end -- RONDO.scr:393
end

script.labels["11-5"] = function(ctx)
    -- RONDO.scr:396
    ctx:object("F#2"):trigger("use") -- RONDO.scr:399-400
    ctx:object("A2"):trigger("use") -- RONDO.scr:401-402
    ctx:wait(1, .5, "12-5") -- RONDO.scr:403
    do return ctx:exit("") end -- RONDO.scr:405
end

script.labels["12-5"] = function(ctx)
    -- RONDO.scr:408
    ctx:object("E1"):trigger("use") -- RONDO.scr:411-412
    ctx:object("G2"):trigger("use") -- RONDO.scr:413-414
    ctx:wait(1, .5, "13-5") -- RONDO.scr:415
    do return ctx:exit("") end -- RONDO.scr:417
end

script.labels["13-5"] = function(ctx)
    -- RONDO.scr:422
    ctx:object("D#2"):trigger("use") -- RONDO.scr:425-426
    ctx:object("F#2"):trigger("use") -- RONDO.scr:427-428
    ctx:wait(1, .5, "14-5") -- RONDO.scr:429
    do return ctx:exit("") end -- RONDO.scr:431
end

script.labels["14-5"] = function(ctx)
    -- RONDO.scr:434
    ctx:object("E1"):trigger("use") -- RONDO.scr:437-438
    -- wait 1 .5, 8-5
    do return ctx:exit("") end -- RONDO.scr:441
end

script.labels["Main"] = function(ctx)
    -- RONDO.scr:445
    -- TRACEON
    ctx:state().counter = 0 -- RONDO.scr:450
    ctx:addTrigger("Use", "OnPlay") -- RONDO.scr:451
    do return ctx:exit("") end -- RONDO.scr:452
end

return script
