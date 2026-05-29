-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WRITMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- LoseMan.scr
-- By Timmy
-- 12/20
-- handles losegame cutscene
script.labels["OnLose"] = function(ctx)
    -- WRITMAN.scr:14
    if not ctx:hasKey(100) then -- WRITMAN.scr:18-19
        do return ctx:exit("") end -- WRITMAN.scr:20
    end -- WRITMAN.scr:21
    if ctx:hasKey(9515) then -- WRITMAN.scr:23-24
        mm9.gosub(script, ctx, "DeleteHanndl") -- WRITMAN.scr:25
        do return ctx:exit("") end -- WRITMAN.scr:26
    end -- WRITMAN.scr:27
    ctx:giveKey(9515) -- WRITMAN.scr:29
    ctx:screenFadeOut(1) -- WRITMAN.scr:30
    ctx:wait(1, 2, "OnStart") -- WRITMAN.scr:31
    do return ctx:exit("") end -- WRITMAN.scr:32
end

script.labels["OnStart"] = function(ctx)
    -- WRITMAN.scr:35
    ctx:state().g_hobject = ctx:objectOrNil("Losecam1") -- WRITMAN.scr:38
    -- trigger g_hobject On
    ctx:trigger("g_hobject", "Play") -- WRITMAN.scr:40
    do return ctx:exit("") end -- WRITMAN.scr:42
end

script.labels["OnCam2"] = function(ctx)
    -- WRITMAN.scr:45
    ctx:screenFadeOut(.5) -- WRITMAN.scr:49
    ctx:object("losecam1"):trigger("off") -- WRITMAN.scr:50-51
    ctx:object("losecam2"):trigger("Play") -- WRITMAN.scr:53-54
    do return ctx:exit("") end -- WRITMAN.scr:55
end

script.labels["OnCam3"] = function(ctx)
    -- WRITMAN.scr:58
    ctx:screenFadeOut(.5) -- WRITMAN.scr:62
    ctx:object("losecam2"):trigger("off") -- WRITMAN.scr:63-64
    ctx:object("losecam3"):trigger("on") -- WRITMAN.scr:66-67
    ctx:screenFadeIn(.5) -- WRITMAN.scr:68
    ctx:wait(1, 1, "Scene3") -- WRITMAN.scr:69
    do return ctx:exit("") end -- WRITMAN.scr:70
end

script.labels["Scene3"] = function(ctx)
    -- WRITMAN.scr:73
    ctx:object("Door0"):trigger("use") -- WRITMAN.scr:76-77
    ctx:playSound("\\Sounds\\events\\draweropenwood.wav", "DoNothing", 100, 24000, "FALSE", 100) -- WRITMAN.scr:78
    ctx:wait(1, 1.5, "Speak1") -- WRITMAN.scr:79
    do return ctx:exit("") end -- WRITMAN.scr:80
end

script.labels["Speak1"] = function(ctx)
    -- WRITMAN.scr:83
    ctx:object("hanndl"):trigger("speak16") -- WRITMAN.scr:86-87
    do return ctx:exit("") end -- WRITMAN.scr:89
end

script.labels["Close"] = function(ctx)
    -- WRITMAN.scr:93
    ctx:object("Door0"):trigger("use") -- WRITMAN.scr:96-97
    ctx:playSound("\\Sounds\\events\\drawerclosewood.wav", "DoNothing", 100, 24000, "FALSE", 100) -- WRITMAN.scr:98
    ctx:wait(1, 1, "FadeOut") -- WRITMAN.scr:99
    do return ctx:exit("") end -- WRITMAN.scr:100
end

script.labels["DeleteHanndl"] = function(ctx)
    -- WRITMAN.scr:103
    ctx:state().g_hobject = ctx:objectOrNil("hanndl") -- WRITMAN.scr:106
    ctx:object("g_hobject"):remove() -- WRITMAN.scr:107
    do return ctx:exit("") end -- WRITMAN.scr:108
end

script.labels["FadeOut"] = function(ctx)
    -- WRITMAN.scr:111
    ctx:giveExp(170000) -- WRITMAN.scr:114
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 24000, "FALSE", 100) -- WRITMAN.scr:115
    ctx:object("losecam3"):trigger("off") -- WRITMAN.scr:116-117
    ctx:object("losecam5"):trigger("on") -- WRITMAN.scr:118-119
    ctx:screenFadeIn(1) -- WRITMAN.scr:120
    ctx:wait(1, 1, "FadeOut2") -- WRITMAN.scr:121
    do return ctx:exit("") end -- WRITMAN.scr:122
end

script.labels["FadeOut2"] = function(ctx)
    -- WRITMAN.scr:125
    mm9.gosub(script, ctx, "DeleteHanndl") -- WRITMAN.scr:128
    ctx:object("RotatingDoor1"):trigger("Unlock") -- WRITMAN.scr:129-130
    local object = ctx:object("RotatingDoor0") -- WRITMAN.scr:131
    object:trigger("Unlock") -- WRITMAN.scr:132
    object:trigger("use") -- WRITMAN.scr:133
    ctx:object("losecam5"):trigger("play") -- WRITMAN.scr:134-135
    ctx:wait(1, 4, "FadeOutReal") -- WRITMAN.scr:136
    do return ctx:exit("") end -- WRITMAN.scr:137
end

script.labels["FadeOutReal"] = function(ctx)
    -- WRITMAN.scr:141
    ctx:screenFadeOut(1) -- WRITMAN.scr:144
    ctx:wait(1, 2, "fadein") -- WRITMAN.scr:147
    do return ctx:exit("") end -- WRITMAN.scr:148
end

script.labels["FadeIn"] = function(ctx)
    -- WRITMAN.scr:151
    ctx:letterBox("False") -- WRITMAN.scr:154
    ctx:object("losecam5"):trigger("off") -- WRITMAN.scr:155-156
    ctx:screenFadeIn(1) -- WRITMAN.scr:157
    do return ctx:exit("") end -- WRITMAN.scr:158
end

script.labels["Init"] = function(ctx)
    -- WRITMAN.scr:161
    ctx:getPcVoice("g_ntemp") -- WRITMAN.scr:166
    if ctx:condition("g_ntemp==0") then -- WRITMAN.scr:169
        ctx:set("sVoice1", "voices\\cinema\\AngryFemale\\AngryFText01a.wav") -- WRITMAN.scr:170
        do return ctx:exit("") end -- WRITMAN.scr:171
    end -- WRITMAN.scr:172
    if ctx:condition("g_ntemp==1") then -- WRITMAN.scr:174
        ctx:set("sVoice1", "voices\\cinema\\ArrogantFemale\\ArrogantFText01a.wav") -- WRITMAN.scr:175
        do return ctx:exit("") end -- WRITMAN.scr:176
    end -- WRITMAN.scr:177
    if ctx:condition("g_ntemp==2") then -- WRITMAN.scr:179
        ctx:set("sVoice1", "voices\\cinema\\AssertiveFemale\\AssertiveFText01.wav") -- WRITMAN.scr:180
        do return ctx:exit("") end -- WRITMAN.scr:181
    end -- WRITMAN.scr:182
    if ctx:condition("g_ntemp==3") then -- WRITMAN.scr:184
        ctx:set("sVoice1", "voices\\cinema\\CowardlyFemale\\CowardlyFText01b.wav") -- WRITMAN.scr:185
        do return ctx:exit("") end -- WRITMAN.scr:186
    end -- WRITMAN.scr:187
    if ctx:condition("g_ntemp==4") then -- WRITMAN.scr:189
        ctx:set("sVoice1", "voices\\cinema\\DimFemale\\DimFText01.wav") -- WRITMAN.scr:190
        do return ctx:exit("") end -- WRITMAN.scr:191
    end -- WRITMAN.scr:192
    if ctx:condition("g_ntemp==5") then -- WRITMAN.scr:194
        ctx:set("sVoice1", "voices\\cinema\\HappyFemale\\HappyFText01.wav") -- WRITMAN.scr:195
        do return ctx:exit("") end -- WRITMAN.scr:196
    end -- WRITMAN.scr:197
    if ctx:condition("g_ntemp==6") then -- WRITMAN.scr:199
        ctx:set("sVoice1", "voices\\cinema\\SarcasticFemale\\SarcasticFText01.wav") -- WRITMAN.scr:200
        do return ctx:exit("") end -- WRITMAN.scr:201
    end -- WRITMAN.scr:202
    if ctx:condition("g_ntemp==7") then -- WRITMAN.scr:204
        ctx:set("sVoice1", "voices\\cinema\\LichFemale\\LichFText01.wav") -- WRITMAN.scr:205
        do return ctx:exit("") end -- WRITMAN.scr:206
    end -- WRITMAN.scr:207
    if ctx:condition("g_ntemp==8") then -- WRITMAN.scr:209
        ctx:set("sVoice1", "voices\\cinema\\HalfOrcLichFemale\\HalfOrcLichFText01.wav") -- WRITMAN.scr:210
        do return ctx:exit("") end -- WRITMAN.scr:211
    end -- WRITMAN.scr:212
    if ctx:condition("g_ntemp==9") then -- WRITMAN.scr:214
        ctx:set("sVoice1", "voices\\cinema\\Angrymale\\AngryText01a.wav") -- WRITMAN.scr:215
        do return ctx:exit("") end -- WRITMAN.scr:216
    end -- WRITMAN.scr:217
    if ctx:condition("g_ntemp==10") then -- WRITMAN.scr:219
        ctx:set("sVoice1", "voices\\cinema\\ArrogantMale\\ArrogantMText01.wav") -- WRITMAN.scr:220
        do return ctx:exit("") end -- WRITMAN.scr:221
    end -- WRITMAN.scr:222
    if ctx:condition("g_ntemp==11") then -- WRITMAN.scr:224
        ctx:set("sVoice1", "voices\\cinema\\AssertiveMale\\AssertiveMText01.wav") -- WRITMAN.scr:225
        do return ctx:exit("") end -- WRITMAN.scr:226
    end -- WRITMAN.scr:227
    if ctx:condition("g_ntemp==12") then -- WRITMAN.scr:229
        ctx:set("sVoice1", "voices\\cinema\\CowardlyMale\\CowardlyMText01.wav") -- WRITMAN.scr:230
        do return ctx:exit("") end -- WRITMAN.scr:231
    end -- WRITMAN.scr:232
    if ctx:condition("g_ntemp==13") then -- WRITMAN.scr:234
        ctx:set("sVoice1", "voices\\cinema\\DimMale\\DimMText01.wav") -- WRITMAN.scr:235
        do return ctx:exit("") end -- WRITMAN.scr:236
    end -- WRITMAN.scr:237
    if ctx:condition("g_ntemp==14") then -- WRITMAN.scr:239
        ctx:set("sVoice1", "voices\\cinema\\HappyMale\\HappyMText01.wav") -- WRITMAN.scr:240
        do return ctx:exit("") end -- WRITMAN.scr:241
    end -- WRITMAN.scr:242
    if ctx:condition("g_ntemp==15") then -- WRITMAN.scr:244
        ctx:set("sVoice1", "voices\\cinema\\SarcasticMale\\SarcasticMText01.wav") -- WRITMAN.scr:245
        do return ctx:exit("") end -- WRITMAN.scr:246
    end -- WRITMAN.scr:247
    if ctx:condition("g_ntemp==16") then -- WRITMAN.scr:249
        ctx:set("sVoice1", "voices\\cinema\\LichMale\\LichMText01.wav") -- WRITMAN.scr:250
        do return ctx:exit("") end -- WRITMAN.scr:251
    end -- WRITMAN.scr:252
    if ctx:condition("g_ntemp==17") then -- WRITMAN.scr:254
        ctx:set("sVoice1", "voices\\cinema\\HalfOrcLichMale\\HalfOrcLichMText01.wav") -- WRITMAN.scr:255
        do return ctx:exit("") end -- WRITMAN.scr:256
    end -- WRITMAN.scr:257
    do return ctx:exit("") end -- WRITMAN.scr:259
end

script.labels["OnDone"] = function(ctx)
    -- WRITMAN.scr:263
    ctx:playSound("sVoice1", "Trigger10", 100, 16000, "FALSE", 100) -- WRITMAN.scr:266
    do return ctx:exit("") end -- WRITMAN.scr:268
end

script.labels["Trigger10"] = function(ctx)
    -- WRITMAN.scr:271
    ctx:object("Hanndl"):trigger("Speak17") -- WRITMAN.scr:274-275
    do return ctx:exit("") end -- WRITMAN.scr:276
end

script.labels["Main"] = function(ctx)
    -- WRITMAN.scr:279
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Lose", "OnLose") -- WRITMAN.scr:284
    ctx:addTrigger("Cam2", "OnCam2") -- WRITMAN.scr:285
    ctx:addTrigger("cam3", "OnCam3") -- WRITMAN.scr:286
    ctx:addTrigger("FadeOut", "Close") -- WRITMAN.scr:287
    mm9.gosub(script, ctx, "Init") -- WRITMAN.scr:288
    ctx:onEvent("OnPostStartWorld", "OnLose") -- WRITMAN.scr:289
    ctx:onEvent("OnPostMiniSaveLoad", "OnLose") -- WRITMAN.scr:290
    ctx:onEvent("OnPostSaveLoad", "OnLose") -- WRITMAN.scr:291
    ctx:addTrigger("Done", "OnDone") -- WRITMAN.scr:292
    ctx:wait(1, .1, "OnLose") -- WRITMAN.scr:293
    do return ctx:exit("") end -- WRITMAN.scr:294
end

return script
