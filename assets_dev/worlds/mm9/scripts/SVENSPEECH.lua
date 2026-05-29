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
    ctx:playSound("\\voices\\cinema\\Battlefield\\sven01.wav", "DoNothing", 100, 50000, "FALSE", 100) -- SVENSPEECH.scr:35
    do return ctx:exit("") end -- SVENSPEECH.scr:36
end

script.labels["OnSven02"] = function(ctx)
    -- SVENSPEECH.scr:40
    ctx:playSound("\\voices\\cinema\\Battlefield\\sven02.wav", "DoNothing", 100, 50000, "FALSE", 100) -- SVENSPEECH.scr:43
    do return ctx:exit("") end -- SVENSPEECH.scr:44
end

script.labels["OnSven03"] = function(ctx)
    -- SVENSPEECH.scr:48
    ctx:playSound("\\voices\\cinema\\Battlefield\\sven03.wav", "DoNothing", 100, 50000, "FALSE", 100) -- SVENSPEECH.scr:51
    do return ctx:exit("") end -- SVENSPEECH.scr:52
end

script.labels["OnSven04"] = function(ctx)
    -- SVENSPEECH.scr:56
    ctx:playSound("\\voices\\cinema\\Battlefield\\sven04.wav", "DoNothing", 100, 50000, "FALSE", 100) -- SVENSPEECH.scr:59
    mm9.gosub(script, ctx, "Award") -- SVENSPEECH.scr:60
    do return ctx:exit("") end -- SVENSPEECH.scr:61
end

script.labels["PlaySpeech"] = function(ctx)
    -- SVENSPEECH.scr:65
    ctx:self():playAnimation("Sven_scene06", "ONDead") -- SVENSPEECH.scr:68
    do return ctx:exit("") end -- SVENSPEECH.scr:69
end

script.labels["OnStart"] = function(ctx)
    -- SVENSPEECH.scr:72
    ctx:object("AmbientSound0"):trigger("off") -- SVENSPEECH.scr:75-76
    ctx:object("AmbientSound1"):trigger("off") -- SVENSPEECH.scr:77-78
    ctx:object("AmbientSound2"):trigger("off") -- SVENSPEECH.scr:79-80
    ctx:object("AmbientSound3"):trigger("off") -- SVENSPEECH.scr:81-82
    ctx:object("AmbientSound4"):trigger("off") -- SVENSPEECH.scr:83-84
    ctx:object("AmbientSound5"):trigger("off") -- SVENSPEECH.scr:85-86
    ctx:object("AmbientSound6"):trigger("off") -- SVENSPEECH.scr:87-88
    ctx:object("AmbientSound7"):trigger("off") -- SVENSPEECH.scr:89-90
    ctx:state().ShowAll = true -- SVENSPEECH.scr:92
    mm9.gosub(script, ctx, "RemoveAll") -- SVENSPEECH.scr:93
    ctx:screenFadeOut(1) -- SVENSPEECH.scr:94
    ctx:wait(1, 1, "FadeIn") -- SVENSPEECH.scr:95
    do return ctx:exit("") end -- SVENSPEECH.scr:96
end

script.labels["FadeIn"] = function(ctx)
    -- SVENSPEECH.scr:100
    ctx:letterBox("true") -- SVENSPEECH.scr:104
    local object = ctx:object("Camera0") -- SVENSPEECH.scr:105
    object:trigger("On") -- SVENSPEECH.scr:106
    object:trigger("Play") -- SVENSPEECH.scr:107
    ctx:screenFadeIn(1) -- SVENSPEECH.scr:108
    -- wait 1 1 ShootOn
    do return ctx:exit("") end -- SVENSPEECH.scr:110
end

script.labels["Cam2"] = function(ctx)
    -- SVENSPEECH.scr:113
    ctx:screenFadeIn(1) -- SVENSPEECH.scr:115
    ctx:object("Camera0"):trigger("Off") -- SVENSPEECH.scr:116-117
    local object = ctx:object("Camera1") -- SVENSPEECH.scr:119
    object:trigger("On") -- SVENSPEECH.scr:120
    object:trigger("Play") -- SVENSPEECH.scr:121
    do return ctx:exit("") end -- SVENSPEECH.scr:122
end

script.labels["Cam3"] = function(ctx)
    -- SVENSPEECH.scr:125
    ctx:screenFadeIn(1) -- SVENSPEECH.scr:127
    ctx:object("Camera1"):trigger("Off") -- SVENSPEECH.scr:128-129
    local object = ctx:object("Camera3") -- SVENSPEECH.scr:131
    object:trigger("On") -- SVENSPEECH.scr:132
    object:trigger("Play") -- SVENSPEECH.scr:133
    do return ctx:exit("") end -- SVENSPEECH.scr:134
end

script.labels["Cam5"] = function(ctx)
    -- SVENSPEECH.scr:137
    ctx:screenFadeIn(.5) -- SVENSPEECH.scr:139
    ctx:object("Camera3"):trigger("Off") -- SVENSPEECH.scr:140-141
    ctx:object("Camera5"):trigger("On") -- SVENSPEECH.scr:143-144
    mm9.gosub(script, ctx, "Playspeech") -- SVENSPEECH.scr:145
    do return ctx:exit("") end -- SVENSPEECH.scr:146
end

script.labels["OnCam6"] = function(ctx)
    -- SVENSPEECH.scr:150
    ctx:object("Camera5"):trigger("Off") -- SVENSPEECH.scr:153-154
    ctx:object("Camera6"):trigger("On") -- SVENSPEECH.scr:156-157
    do return ctx:exit("") end -- SVENSPEECH.scr:159
end

script.labels["OnCam7"] = function(ctx)
    -- SVENSPEECH.scr:163
    ctx:object("Camera6"):trigger("Off") -- SVENSPEECH.scr:166-167
    ctx:object("Camera7"):trigger("On") -- SVENSPEECH.scr:169-170
    do return ctx:exit("") end -- SVENSPEECH.scr:172
end

script.labels["OnCam8"] = function(ctx)
    -- SVENSPEECH.scr:175
    ctx:object("Camera7"):trigger("Off") -- SVENSPEECH.scr:178-179
    ctx:object("Camera8"):trigger("On") -- SVENSPEECH.scr:181-182
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
        ctx:state().ShowAll = false -- SVENSPEECH.scr:212
        mm9.gosub(script, ctx, "RemoveAll") -- SVENSPEECH.scr:213
        do return ctx:exit("") end -- SVENSPEECH.scr:215
    end -- SVENSPEECH.scr:216
    if ctx:hasKey(97) then -- SVENSPEECH.scr:218-219
        ctx:state().ShowAll = false -- SVENSPEECH.scr:220
        mm9.gosub(script, ctx, "RemoveAll") -- SVENSPEECH.scr:221
        do return ctx:exit("") end -- SVENSPEECH.scr:223
    end -- SVENSPEECH.scr:224
    ctx:state().ShowAll = true -- SVENSPEECH.scr:226
    mm9.gosub(script, ctx, "RemoveAll") -- SVENSPEECH.scr:227
    ctx:self():loopAnimation("static_model", 0, "DoNothing") -- SVENSPEECH.scr:228
    ctx:wait(1, .3, "OnStart") -- SVENSPEECH.scr:229
    do return ctx:exit("") end -- SVENSPEECH.scr:231
end

script.labels["OnDead"] = function(ctx)
    -- SVENSPEECH.scr:236
    ctx:self():loopAnimation("static_model", 0, "DoNothing") -- SVENSPEECH.scr:239
    do return ctx:exit("") end -- SVENSPEECH.scr:240
end

script.labels["OnDone"] = function(ctx)
    -- SVENSPEECH.scr:243
    ctx:set("nCamCount", "nCamCount + 1") -- SVENSPEECH.scr:246
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
    ctx:wait(1, 1, "FadeOut") -- SVENSPEECH.scr:268
    do return ctx:exit("") end -- SVENSPEECH.scr:269
end

script.labels["FadeOut"] = function(ctx)
    -- SVENSPEECH.scr:272
    ctx:screenFadeOut(1) -- SVENSPEECH.scr:274
    ctx:wait(1, 1, "FadeOut2") -- SVENSPEECH.scr:275
    do return ctx:exit("") end -- SVENSPEECH.scr:276
end

script.labels["FadeOut2"] = function(ctx)
    -- SVENSPEECH.scr:279
    ctx:object("AmbientSound0"):trigger("On") -- SVENSPEECH.scr:281-282
    ctx:object("AmbientSound1"):trigger("On") -- SVENSPEECH.scr:283-284
    ctx:object("AmbientSound2"):trigger("On") -- SVENSPEECH.scr:285-286
    ctx:object("AmbientSound3"):trigger("On") -- SVENSPEECH.scr:287-288
    ctx:object("AmbientSound4"):trigger("On") -- SVENSPEECH.scr:289-290
    ctx:object("AmbientSound5"):trigger("On") -- SVENSPEECH.scr:291-292
    ctx:object("AmbientSound6"):trigger("On") -- SVENSPEECH.scr:293-294
    ctx:object("AmbientSound7"):trigger("On") -- SVENSPEECH.scr:295-296
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 50000, "FALSE", 100) -- SVENSPEECH.scr:297
    ctx:letterBox("false") -- SVENSPEECH.scr:298
    ctx:object("Camera8"):trigger("Off") -- SVENSPEECH.scr:299-300
    ctx:screenFadeIn(1) -- SVENSPEECH.scr:301
    do return ctx:exit("") end -- SVENSPEECH.scr:302
end

script.labels["Main"] = function(ctx)
    -- SVENSPEECH.scr:305
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Done", "OnDone") -- SVENSPEECH.scr:312
    ctx:addTrigger("Start", "OnStart") -- SVENSPEECH.scr:313
    ctx:addModelKey("Sven01", "OnSven01") -- SVENSPEECH.scr:314
    ctx:addModelKey("Sven02", "OnSven02") -- SVENSPEECH.scr:315
    ctx:addModelKey("Sven03", "OnSven03") -- SVENSPEECH.scr:316
    ctx:addModelKey("Sven04", "OnSven04") -- SVENSPEECH.scr:317
    ctx:addModelKey("Camera6", "OnCam6") -- SVENSPEECH.scr:318
    ctx:addModelKey("Camera7", "OnCam7") -- SVENSPEECH.scr:319
    ctx:addModelKey("Camera8", "OnCam8") -- SVENSPEECH.scr:320
    ctx:addModelKey("FadeOut", "OnFadeOut") -- SVENSPEECH.scr:321
    ctx:onEvent("OnPostStartWorld", "Init") -- SVENSPEECH.scr:322
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- SVENSPEECH.scr:323
    ctx:onEvent("OnPostSaveLoad", "Init") -- SVENSPEECH.scr:324
    ctx:wait(1, .1, "Init") -- SVENSPEECH.scr:325
    do return ctx:exit("") end -- SVENSPEECH.scr:326
end

return script
