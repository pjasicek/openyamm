-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "E3DUNGEONCAMERA0.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "followpath.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Camera0.scr
-- John Machin
-- This script will move a camera down a designated marker
-- path.
script.labels["OnTurnOn"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:12
    mm9.gosub(script, ctx, "OnStartPendulum") -- E3DUNGEONCAMERA0.scr:14
    do return ctx:exit("FALSE") end -- E3DUNGEONCAMERA0.scr:16
end

script.labels["OnStartPendulum"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:19
    ctx:command("setcallback", "0, OnPendulumDone") -- E3DUNGEONCAMERA0.scr:21
    ctx:command("set", "g_sFollowPathName\t\t\tPendulumPath") -- E3DUNGEONCAMERA0.scr:23
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:24
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:25
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:26
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:27
    -- AddTrigger StartPendulum, DoNothing
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:31
end

script.labels["OnStartThrone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:34
    ctx:command("setcallback", "0, OnThroneDone") -- E3DUNGEONCAMERA0.scr:36
    ctx:command("set", "g_sFollowPathName\t\t\tThronePath") -- E3DUNGEONCAMERA0.scr:38
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:39
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:40
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:41
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:42
    ctx:addTrigger("StartThrone", "DoNothing") -- E3DUNGEONCAMERA0.scr:44
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:46
end

script.labels["OnStartScythe"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:49
    ctx:command("setcallback", "0, OnScytheDone") -- E3DUNGEONCAMERA0.scr:51
    ctx:command("set", "g_sFollowPathName\t\t\tScythePath") -- E3DUNGEONCAMERA0.scr:53
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:54
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:55
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:56
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:57
    ctx:addTrigger("StartScythe", "DoNothing") -- E3DUNGEONCAMERA0.scr:59
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:61
end

script.labels["OnStartSaw"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:64
    ctx:command("setcallback", "0, OnSawDone") -- E3DUNGEONCAMERA0.scr:66
    ctx:command("set", "g_sFollowPathName\t\t\tSawPath") -- E3DUNGEONCAMERA0.scr:68
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:69
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:70
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:71
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:72
    ctx:addTrigger("StartSaw", "DoNothing") -- E3DUNGEONCAMERA0.scr:74
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:76
end

script.labels["OnStartWardrobe"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:79
    ctx:command("setcallback", "0, OnWardrobeDone") -- E3DUNGEONCAMERA0.scr:81
    ctx:command("set", "g_sFollowPathName\t\t\tWardrobePath") -- E3DUNGEONCAMERA0.scr:83
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:84
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:85
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:86
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:87
    ctx:addTrigger("StartWardrobe", "DoNothing") -- E3DUNGEONCAMERA0.scr:89
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:91
end

script.labels["OnStartWardrobe2"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:94
    ctx:command("setcallback", "0, OnWardrobe2Done") -- E3DUNGEONCAMERA0.scr:96
    ctx:command("set", "g_sFollowPathName\t\t\tWardrobe2Path") -- E3DUNGEONCAMERA0.scr:98
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:99
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:100
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:101
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:102
    ctx:addTrigger("StartWardrobe2", "DoNothing") -- E3DUNGEONCAMERA0.scr:104
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:106
end

script.labels["OnStartSconce"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:109
    ctx:command("setcallback", "0, OnSconceDone") -- E3DUNGEONCAMERA0.scr:111
    ctx:command("set", "g_sFollowPathName\t\t\tSconcePath") -- E3DUNGEONCAMERA0.scr:113
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:114
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:115
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:116
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:117
    ctx:addTrigger("StartSconce", "DoNothing") -- E3DUNGEONCAMERA0.scr:119
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:121
end

script.labels["OnStartTreasure"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:124
    ctx:command("setcallback", "0, OnTreasureDone") -- E3DUNGEONCAMERA0.scr:126
    ctx:command("set", "g_sFollowPathName\t\t\tTreasurePath") -- E3DUNGEONCAMERA0.scr:128
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:129
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:130
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:131
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:132
    ctx:addTrigger("StartTreasure", "DoNothing") -- E3DUNGEONCAMERA0.scr:134
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:136
end

script.labels["OnStartPit"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:139
    ctx:command("setcallback", "0, OnPitDone") -- E3DUNGEONCAMERA0.scr:141
    ctx:command("set", "g_sFollowPathName\t\t\tPitPath") -- E3DUNGEONCAMERA0.scr:143
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:144
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:145
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:146
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:147
    ctx:addTrigger("StartPit", "DoNothing") -- E3DUNGEONCAMERA0.scr:149
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:151
end

script.labels["OnStartPit2"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:154
    ctx:command("setcallback", "0, OnPit2Done") -- E3DUNGEONCAMERA0.scr:156
    ctx:command("set", "g_sFollowPathName\t\t\tPit2Path") -- E3DUNGEONCAMERA0.scr:158
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:159
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:160
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:161
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:162
    ctx:addTrigger("StartPit2", "DoNothing") -- E3DUNGEONCAMERA0.scr:164
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:166
end

script.labels["OnStartTrapDoor"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:169
    ctx:command("setcallback", "0, OnTrapDoorDone") -- E3DUNGEONCAMERA0.scr:171
    ctx:command("set", "g_sFollowPathName\t\t\tTrapDoorPath") -- E3DUNGEONCAMERA0.scr:173
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:174
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:175
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:176
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:177
    ctx:addTrigger("StartTrapDoor", "DoNothing") -- E3DUNGEONCAMERA0.scr:179
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:181
end

script.labels["OnStartChasm"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:184
    ctx:command("setcallback", "0, OnChasmDone") -- E3DUNGEONCAMERA0.scr:186
    ctx:command("set", "g_sFollowPathName\t\t\tChasmPath") -- E3DUNGEONCAMERA0.scr:188
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:189
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:190
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:191
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:192
    ctx:addTrigger("StartChasm", "DoNothing") -- E3DUNGEONCAMERA0.scr:194
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:196
end

script.labels["OnStartLich"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:199
    ctx:command("setcallback", "0, OnLichDone") -- E3DUNGEONCAMERA0.scr:201
    ctx:command("set", "g_sFollowPathName\t\t\tLichPath") -- E3DUNGEONCAMERA0.scr:203
    ctx:command("set", "g_nFollowPathSpeed\t\t\t175") -- E3DUNGEONCAMERA0.scr:204
    ctx:command("set", "g_nFollowPathDoneCallback\t0") -- E3DUNGEONCAMERA0.scr:205
    ctx:command("set", "g_nFollowPathLoops\t\t\t1") -- E3DUNGEONCAMERA0.scr:206
    mm9.gosub(script, ctx, "FollowPath") -- E3DUNGEONCAMERA0.scr:207
    ctx:addTrigger("StartLich", "DoNothing") -- E3DUNGEONCAMERA0.scr:209
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:211
end

script.labels["OnPendulumDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:215
    -- do whatever here then continue
    ctx:command("debugout", "In OnPendulum Done") -- E3DUNGEONCAMERA0.scr:218
    mm9.gosub(script, ctx, "OnStartThrone") -- E3DUNGEONCAMERA0.scr:219
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:221
end

script.labels["OnThroneDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:224
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartScythe") -- E3DUNGEONCAMERA0.scr:227
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:229
end

script.labels["OnScytheDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:232
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartSaw") -- E3DUNGEONCAMERA0.scr:235
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:237
end

script.labels["OnSawDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:240
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartWardrobe") -- E3DUNGEONCAMERA0.scr:243
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:245
end

script.labels["OnWardrobeDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:248
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartWardrobe2") -- E3DUNGEONCAMERA0.scr:251
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:253
end

script.labels["OnWardrobe2Done"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:256
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartSconce") -- E3DUNGEONCAMERA0.scr:259
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:261
end

script.labels["OnSconceDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:264
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartTreasure") -- E3DUNGEONCAMERA0.scr:267
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:269
end

script.labels["OnTreasureDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:272
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartPit") -- E3DUNGEONCAMERA0.scr:275
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:277
end

script.labels["OnPitDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:280
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartPit2") -- E3DUNGEONCAMERA0.scr:283
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:285
end

script.labels["OnPit2Done"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:288
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartTrapDoor") -- E3DUNGEONCAMERA0.scr:291
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:293
end

script.labels["OnTrapDoorDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:296
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartChasm") -- E3DUNGEONCAMERA0.scr:299
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:301
end

script.labels["OnChasmDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:304
    -- do whatever here then continue
    mm9.gosub(script, ctx, "OnStartLich") -- E3DUNGEONCAMERA0.scr:307
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:309
end

script.labels["OnLichDone"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:313
    -- do whatever here then continue
    ctx:trigger("g_hMyObject", "OFF") -- E3DUNGEONCAMERA0.scr:316
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:318
end

script.labels["DoNothing"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:321
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:323
end

script.labels["Main"] = function(ctx)
    -- E3DUNGEONCAMERA0.scr:326
    -- This routine is automatically run
    -- at script startup...
    -- TraceOn
    mm9.gosub(script, ctx, "FollowPathInit") -- E3DUNGEONCAMERA0.scr:333
    ctx:command("getmyhandle", "g_hMyObject") -- E3DUNGEONCAMERA0.scr:335
    ctx:addTrigger("StartPendulum", "OnStartPendulum") -- E3DUNGEONCAMERA0.scr:337
    ctx:addTrigger("StartThrone", "OnStartThrone") -- E3DUNGEONCAMERA0.scr:338
    ctx:addTrigger("StartScythe", "OnStartScythe") -- E3DUNGEONCAMERA0.scr:339
    ctx:addTrigger("StartSaw", "OnStartSaw") -- E3DUNGEONCAMERA0.scr:340
    ctx:addTrigger("StartWardrobe", "OnStartWardrobe") -- E3DUNGEONCAMERA0.scr:341
    ctx:addTrigger("StartWardrobe2", "OnStartWardrobe2") -- E3DUNGEONCAMERA0.scr:342
    ctx:addTrigger("StartSconce", "OnStartSconce") -- E3DUNGEONCAMERA0.scr:343
    ctx:addTrigger("StartTreasure", "OnStartTreasure") -- E3DUNGEONCAMERA0.scr:344
    ctx:addTrigger("StartPit", "OnStartPit") -- E3DUNGEONCAMERA0.scr:345
    ctx:addTrigger("StartPit2", "OnStartPit2") -- E3DUNGEONCAMERA0.scr:346
    ctx:addTrigger("StartTrapDoor", "OnStartTrapDoor") -- E3DUNGEONCAMERA0.scr:347
    ctx:addTrigger("StartChasm", "OnStartChasm") -- E3DUNGEONCAMERA0.scr:348
    ctx:addTrigger("StartLich", "OnStartLich") -- E3DUNGEONCAMERA0.scr:349
    ctx:addTrigger("On", "OnTurnOn") -- E3DUNGEONCAMERA0.scr:351
    -- AddTrigger FollowPathDone OnFollowPathDone
    do return ctx:exit("") end -- E3DUNGEONCAMERA0.scr:355
end

return script
