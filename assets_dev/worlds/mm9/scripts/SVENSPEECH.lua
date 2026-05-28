-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SVENSPEECH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "SvenShowtake.inc" }

-- NPC7.scr
-- timmy
-- handles Hjarrrand Fixer voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnSven01"] = function(ctx)
    -- SVENSPEECH.scr:31
    ctx:command("playsound", "\\voices\\cinema\\Battlefield\\sven01.wav, DoNothing, 100, 50000, FALSE, 100") -- SVENSPEECH.scr:35
    do return ctx:exit("") end -- SVENSPEECH.scr:36
end

script.labels["OnSven02"] = function(ctx)
    -- SVENSPEECH.scr:40
    ctx:command("playsound", "\\voices\\cinema\\Battlefield\\sven02.wav, DoNothing, 100, 50000, FALSE, 100") -- SVENSPEECH.scr:43
    do return ctx:exit("") end -- SVENSPEECH.scr:44
end

script.labels["OnSven03"] = function(ctx)
    -- SVENSPEECH.scr:48
    ctx:command("playsound", "\\voices\\cinema\\Battlefield\\sven03.wav, DoNothing, 100, 50000, FALSE, 100") -- SVENSPEECH.scr:51
    do return ctx:exit("") end -- SVENSPEECH.scr:52
end

script.labels["OnSven04"] = function(ctx)
    -- SVENSPEECH.scr:56
    ctx:command("playsound", "\\voices\\cinema\\Battlefield\\sven04.wav, DoNothing, 100, 50000, FALSE, 100") -- SVENSPEECH.scr:59
    mm9.gosub(script, ctx, "Award") -- SVENSPEECH.scr:60
    do return ctx:exit("") end -- SVENSPEECH.scr:61
end

script.labels["PlaySpeech"] = function(ctx)
    -- SVENSPEECH.scr:65
    ctx:command("playanim", "Sven_scene06 ONDead") -- SVENSPEECH.scr:68
    do return ctx:exit("") end -- SVENSPEECH.scr:69
end

script.labels["OnStart"] = function(ctx)
    -- SVENSPEECH.scr:72
    ctx:command("getobjecthandle", "AmbientSound0 g_hobject") -- SVENSPEECH.scr:75
    ctx:trigger("g_hobject", "off") -- SVENSPEECH.scr:76
    ctx:command("getobjecthandle", "AmbientSound1 g_hobject") -- SVENSPEECH.scr:77
    ctx:trigger("g_hobject", "off") -- SVENSPEECH.scr:78
    ctx:command("getobjecthandle", "AmbientSound2 g_hobject") -- SVENSPEECH.scr:79
    ctx:trigger("g_hobject", "off") -- SVENSPEECH.scr:80
    ctx:command("getobjecthandle", "AmbientSound3 g_hobject") -- SVENSPEECH.scr:81
    ctx:trigger("g_hobject", "off") -- SVENSPEECH.scr:82
    ctx:command("getobjecthandle", "AmbientSound4 g_hobject") -- SVENSPEECH.scr:83
    ctx:trigger("g_hobject", "off") -- SVENSPEECH.scr:84
    ctx:command("getobjecthandle", "AmbientSound5 g_hobject") -- SVENSPEECH.scr:85
    ctx:trigger("g_hobject", "off") -- SVENSPEECH.scr:86
    ctx:command("getobjecthandle", "AmbientSound6 g_hobject") -- SVENSPEECH.scr:87
    ctx:trigger("g_hobject", "off") -- SVENSPEECH.scr:88
    ctx:command("getobjecthandle", "AmbientSound7 g_hobject") -- SVENSPEECH.scr:89
    ctx:trigger("g_hobject", "off") -- SVENSPEECH.scr:90
    ctx:command("set", "ShowAll, TRUE") -- SVENSPEECH.scr:92
    mm9.gosub(script, ctx, "RemoveAll") -- SVENSPEECH.scr:93
    ctx:command("screenfadeout", "1") -- SVENSPEECH.scr:94
    ctx:command("wait", "1 1 FadeIn") -- SVENSPEECH.scr:95
    do return ctx:exit("") end -- SVENSPEECH.scr:96
end

script.labels["FadeIn"] = function(ctx)
    -- SVENSPEECH.scr:100
    ctx:command("letterbox", "true") -- SVENSPEECH.scr:104
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- SVENSPEECH.scr:105
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:106
    ctx:trigger("g_hobject", "Play") -- SVENSPEECH.scr:107
    ctx:command("screenfadein", "1") -- SVENSPEECH.scr:108
    -- wait 1 1 ShootOn
    do return ctx:exit("") end -- SVENSPEECH.scr:110
end

script.labels["Cam2"] = function(ctx)
    -- SVENSPEECH.scr:113
    ctx:command("screenfadein", "1") -- SVENSPEECH.scr:115
    ctx:command("getobjecthandle", "Camera0 g_hobject") -- SVENSPEECH.scr:116
    ctx:trigger("g_hobject", "Off") -- SVENSPEECH.scr:117
    ctx:command("getobjecthandle", "Camera1 g_hobject") -- SVENSPEECH.scr:119
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:120
    ctx:trigger("g_hobject", "Play") -- SVENSPEECH.scr:121
    do return ctx:exit("") end -- SVENSPEECH.scr:122
end

script.labels["Cam3"] = function(ctx)
    -- SVENSPEECH.scr:125
    ctx:command("screenfadein", "1") -- SVENSPEECH.scr:127
    ctx:command("getobjecthandle", "Camera1 g_hobject") -- SVENSPEECH.scr:128
    ctx:trigger("g_hobject", "Off") -- SVENSPEECH.scr:129
    ctx:command("getobjecthandle", "Camera3 g_hobject") -- SVENSPEECH.scr:131
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:132
    ctx:trigger("g_hobject", "Play") -- SVENSPEECH.scr:133
    do return ctx:exit("") end -- SVENSPEECH.scr:134
end

script.labels["Cam5"] = function(ctx)
    -- SVENSPEECH.scr:137
    ctx:command("screenfadein", ".5") -- SVENSPEECH.scr:139
    ctx:command("getobjecthandle", "Camera3 g_hobject") -- SVENSPEECH.scr:140
    ctx:trigger("g_hobject", "Off") -- SVENSPEECH.scr:141
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- SVENSPEECH.scr:143
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:144
    mm9.gosub(script, ctx, "Playspeech") -- SVENSPEECH.scr:145
    do return ctx:exit("") end -- SVENSPEECH.scr:146
end

script.labels["OnCam6"] = function(ctx)
    -- SVENSPEECH.scr:150
    ctx:command("getobjecthandle", "Camera5 g_hobject") -- SVENSPEECH.scr:153
    ctx:trigger("g_hobject", "Off") -- SVENSPEECH.scr:154
    ctx:command("getobjecthandle", "Camera6 g_hobject") -- SVENSPEECH.scr:156
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:157
    do return ctx:exit("") end -- SVENSPEECH.scr:159
end

script.labels["OnCam7"] = function(ctx)
    -- SVENSPEECH.scr:163
    ctx:command("getobjecthandle", "Camera6 g_hobject") -- SVENSPEECH.scr:166
    ctx:trigger("g_hobject", "Off") -- SVENSPEECH.scr:167
    ctx:command("getobjecthandle", "Camera7 g_hobject") -- SVENSPEECH.scr:169
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:170
    do return ctx:exit("") end -- SVENSPEECH.scr:172
end

script.labels["OnCam8"] = function(ctx)
    -- SVENSPEECH.scr:175
    ctx:command("getobjecthandle", "Camera7 g_hobject") -- SVENSPEECH.scr:178
    ctx:trigger("g_hobject", "Off") -- SVENSPEECH.scr:179
    ctx:command("getobjecthandle", "Camera8 g_hobject") -- SVENSPEECH.scr:181
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:182
    do return ctx:exit("") end -- SVENSPEECH.scr:184
end

script.labels["Award"] = function(ctx)
    -- SVENSPEECH.scr:187
    if not ctx:hasKey(97) then -- SVENSPEECH.scr:192-193
        if ctx:hasKey(95) then -- SVENSPEECH.scr:194-195
            ctx:giveKey(97) -- SVENSPEECH.scr:197
            ctx:giveExp(114000) -- SVENSPEECH.scr:198
            do return ctx:exit("") end -- SVENSPEECH.scr:199
        end -- SVENSPEECH.scr:200
    end -- SVENSPEECH.scr:201
    do return ctx:exit("") end -- SVENSPEECH.scr:202
end

script.labels["Init"] = function(ctx)
    -- SVENSPEECH.scr:205
    if not ctx:hasKey(95) then -- SVENSPEECH.scr:210-211
        ctx:command("set", "ShowAll, FALSE") -- SVENSPEECH.scr:212
        mm9.gosub(script, ctx, "RemoveAll") -- SVENSPEECH.scr:213
        do return ctx:exit("") end -- SVENSPEECH.scr:215
    end -- SVENSPEECH.scr:216
    if ctx:hasKey(97) then -- SVENSPEECH.scr:218-219
        ctx:command("set", "ShowAll, FALSE") -- SVENSPEECH.scr:220
        mm9.gosub(script, ctx, "RemoveAll") -- SVENSPEECH.scr:221
        do return ctx:exit("") end -- SVENSPEECH.scr:223
    end -- SVENSPEECH.scr:224
    ctx:command("set", "ShowAll, True") -- SVENSPEECH.scr:226
    mm9.gosub(script, ctx, "RemoveAll") -- SVENSPEECH.scr:227
    ctx:command("loopanim", "static_model 0 DoNothing") -- SVENSPEECH.scr:228
    ctx:command("wait", "1 .3 OnStart") -- SVENSPEECH.scr:229
    do return ctx:exit("") end -- SVENSPEECH.scr:231
end

script.labels["OnDead"] = function(ctx)
    -- SVENSPEECH.scr:236
    ctx:command("loopanim", "static_model 0 DoNothing") -- SVENSPEECH.scr:239
    do return ctx:exit("") end -- SVENSPEECH.scr:240
end

script.labels["OnDone"] = function(ctx)
    -- SVENSPEECH.scr:243
    ctx:command("ncamcount", "= nCamCount + 1") -- SVENSPEECH.scr:246
    if ctx:condition("nCamCount==1") then -- SVENSPEECH.scr:248
        mm9.gosub(script, ctx, "Cam2") -- SVENSPEECH.scr:249
        do return ctx:exit("") end -- SVENSPEECH.scr:250
    end -- SVENSPEECH.scr:251
    if ctx:condition("nCamCount==2") then -- SVENSPEECH.scr:253
        mm9.gosub(script, ctx, "Cam3") -- SVENSPEECH.scr:254
        do return ctx:exit("") end -- SVENSPEECH.scr:255
    end -- SVENSPEECH.scr:256
    if ctx:condition("nCamCount==3") then -- SVENSPEECH.scr:258
        mm9.gosub(script, ctx, "Cam5") -- SVENSPEECH.scr:259
        do return ctx:exit("") end -- SVENSPEECH.scr:260
    end -- SVENSPEECH.scr:261
    do return ctx:exit("") end -- SVENSPEECH.scr:262
end

script.labels["OnFadeOut"] = function(ctx)
    -- SVENSPEECH.scr:265
    ctx:command("wait", "1 1 FadeOut") -- SVENSPEECH.scr:268
    do return ctx:exit("") end -- SVENSPEECH.scr:269
end

script.labels["FadeOut"] = function(ctx)
    -- SVENSPEECH.scr:272
    ctx:command("screenfadeout", "1") -- SVENSPEECH.scr:274
    ctx:command("wait", "1 1 FadeOut2") -- SVENSPEECH.scr:275
    do return ctx:exit("") end -- SVENSPEECH.scr:276
end

script.labels["FadeOut2"] = function(ctx)
    -- SVENSPEECH.scr:279
    ctx:command("getobjecthandle", "AmbientSound0 g_hobject") -- SVENSPEECH.scr:281
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:282
    ctx:command("getobjecthandle", "AmbientSound1 g_hobject") -- SVENSPEECH.scr:283
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:284
    ctx:command("getobjecthandle", "AmbientSound2 g_hobject") -- SVENSPEECH.scr:285
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:286
    ctx:command("getobjecthandle", "AmbientSound3 g_hobject") -- SVENSPEECH.scr:287
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:288
    ctx:command("getobjecthandle", "AmbientSound4 g_hobject") -- SVENSPEECH.scr:289
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:290
    ctx:command("getobjecthandle", "AmbientSound5 g_hobject") -- SVENSPEECH.scr:291
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:292
    ctx:command("getobjecthandle", "AmbientSound6 g_hobject") -- SVENSPEECH.scr:293
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:294
    ctx:command("getobjecthandle", "AmbientSound7 g_hobject") -- SVENSPEECH.scr:295
    ctx:trigger("g_hobject", "On") -- SVENSPEECH.scr:296
    ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 50000, FALSE, 100") -- SVENSPEECH.scr:297
    ctx:command("letterbox", "false") -- SVENSPEECH.scr:298
    ctx:command("getobjecthandle", "Camera8 g_hobject") -- SVENSPEECH.scr:299
    ctx:trigger("g_hobject", "Off") -- SVENSPEECH.scr:300
    ctx:command("screenfadein", "1") -- SVENSPEECH.scr:301
    do return ctx:exit("") end -- SVENSPEECH.scr:302
end

script.labels["Main"] = function(ctx)
    -- SVENSPEECH.scr:305
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Done", "OnDone") -- SVENSPEECH.scr:312
    ctx:addTrigger("Start", "OnStart") -- SVENSPEECH.scr:313
    ctx:command("addmodelkey", "Sven01 OnSven01") -- SVENSPEECH.scr:314
    ctx:command("addmodelkey", "Sven02 OnSven02") -- SVENSPEECH.scr:315
    ctx:command("addmodelkey", "Sven03 OnSven03") -- SVENSPEECH.scr:316
    ctx:command("addmodelkey", "Sven04 OnSven04") -- SVENSPEECH.scr:317
    ctx:command("addmodelkey", "Camera6 OnCam6") -- SVENSPEECH.scr:318
    ctx:command("addmodelkey", "Camera7 OnCam7") -- SVENSPEECH.scr:319
    ctx:command("addmodelkey", "Camera8 OnCam8") -- SVENSPEECH.scr:320
    ctx:command("addmodelkey", "FadeOut OnFadeOut") -- SVENSPEECH.scr:321
    ctx:command("onpoststartworld", "Init") -- SVENSPEECH.scr:322
    ctx:command("onpostminisaveload", "Init") -- SVENSPEECH.scr:323
    ctx:command("onpostsaveload", "Init") -- SVENSPEECH.scr:324
    ctx:command("wait", "1 .1 Init") -- SVENSPEECH.scr:325
    do return ctx:exit("") end -- SVENSPEECH.scr:326
end

return script
