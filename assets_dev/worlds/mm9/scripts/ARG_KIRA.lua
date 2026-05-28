-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_KIRA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ARG_Kira.scr
-- By Timmy
-- handles Kira's Argument Cutscene stuff
script.labels["OnApplause"] = function(ctx)
    -- ARG_KIRA.scr:23
    ctx:command("playanim", "Applause Init") -- ARG_KIRA.scr:26
    do return ctx:exit("") end -- ARG_KIRA.scr:27
end

script.labels["OnDone"] = function(ctx)
    -- ARG_KIRA.scr:29
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_KIRA.scr:32
    ctx:command("getobjecthandle", "Argueman g_hobject") -- ARG_KIRA.scr:33
    ctx:trigger("g_hobject", "Done") -- ARG_KIRA.scr:34
    do return ctx:exit("") end -- ARG_KIRA.scr:35
end

script.labels["OnDone2"] = function(ctx)
    -- ARG_KIRA.scr:38
    ctx:command("getobjecthandle", "Argueman g_hobject") -- ARG_KIRA.scr:42
    ctx:trigger("g_hobject", "Done") -- ARG_KIRA.scr:43
    do return ctx:exit("") end -- ARG_KIRA.scr:44
end

script.labels["OnSpeak5"] = function(ctx)
    -- ARG_KIRA.scr:47
    ctx:command("playanim", "Sc2_KIRA5 OnIdle") -- ARG_KIRA.scr:50
    do return ctx:exit("") end -- ARG_KIRA.scr:51
end

script.labels["Onclap"] = function(ctx)
    -- ARG_KIRA.scr:54
    ctx:command("getrandomint", "1, 7 g_ntemp") -- ARG_KIRA.scr:56
    if ctx:condition("g_ntemp==1") then -- ARG_KIRA.scr:58
        ctx:command("playsound", "\\sounds\\events\\clap01.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:59
        do return ctx:exit("") end -- ARG_KIRA.scr:60
    end -- ARG_KIRA.scr:61
    if ctx:condition("g_ntemp==2") then -- ARG_KIRA.scr:63
        ctx:command("playsound", "\\sounds\\events\\clap02.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:64
        do return ctx:exit("") end -- ARG_KIRA.scr:65
    end -- ARG_KIRA.scr:66
    if ctx:condition("g_ntemp==3") then -- ARG_KIRA.scr:68
        ctx:command("playsound", "\\sounds\\events\\clap03.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:69
        do return ctx:exit("") end -- ARG_KIRA.scr:70
    end -- ARG_KIRA.scr:71
    if ctx:condition("g_ntemp==4") then -- ARG_KIRA.scr:73
        ctx:command("playsound", "\\sounds\\events\\clap04.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:74
        do return ctx:exit("") end -- ARG_KIRA.scr:75
    end -- ARG_KIRA.scr:76
    if ctx:condition("g_ntemp==5") then -- ARG_KIRA.scr:78
        ctx:command("playsound", "\\sounds\\events\\clap05.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:79
        do return ctx:exit("") end -- ARG_KIRA.scr:80
    end -- ARG_KIRA.scr:81
    if ctx:condition("g_ntemp==6") then -- ARG_KIRA.scr:83
        ctx:command("playsound", "\\sounds\\events\\clap06.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:84
        do return ctx:exit("") end -- ARG_KIRA.scr:85
    end -- ARG_KIRA.scr:86
    if ctx:condition("g_ntemp==7") then -- ARG_KIRA.scr:88
        ctx:command("playsound", "\\sounds\\events\\clap07.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:89
        do return ctx:exit("") end -- ARG_KIRA.scr:90
    end -- ARG_KIRA.scr:91
    do return ctx:exit("") end -- ARG_KIRA.scr:93
end

script.labels["OnVoice5"] = function(ctx)
    -- ARG_KIRA.scr:96
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\05.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:99
    do return ctx:exit("") end -- ARG_KIRA.scr:100
end

script.labels["OnSpeak7"] = function(ctx)
    -- ARG_KIRA.scr:103
    ctx:command("playanim", "Sc2_Kira7 OnIdle") -- ARG_KIRA.scr:106
    do return ctx:exit("") end -- ARG_KIRA.scr:107
end

script.labels["OnVoice7"] = function(ctx)
    -- ARG_KIRA.scr:110
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\07.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:113
    do return ctx:exit("") end -- ARG_KIRA.scr:114
end

script.labels["OnSpeak10"] = function(ctx)
    -- ARG_KIRA.scr:117
    ctx:command("playanim", "Sc2_Kira9b OnIdle") -- ARG_KIRA.scr:120
    do return ctx:exit("") end -- ARG_KIRA.scr:121
end

script.labels["OnVoice10"] = function(ctx)
    -- ARG_KIRA.scr:124
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\10.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:127
    do return ctx:exit("") end -- ARG_KIRA.scr:128
end

script.labels["OnSpeak12"] = function(ctx)
    -- ARG_KIRA.scr:131
    ctx:command("playanim", "Sc2_KIRA12 OnIdle") -- ARG_KIRA.scr:134
    do return ctx:exit("") end -- ARG_KIRA.scr:135
end

script.labels["OnVoice12"] = function(ctx)
    -- ARG_KIRA.scr:138
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\12.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:141
    do return ctx:exit("") end -- ARG_KIRA.scr:142
end

script.labels["OnSpeak14"] = function(ctx)
    -- ARG_KIRA.scr:145
    ctx:command("playanim", "Sc2_KIRA14 OnIdle") -- ARG_KIRA.scr:148
    do return ctx:exit("") end -- ARG_KIRA.scr:149
end

script.labels["OnVoice14"] = function(ctx)
    -- ARG_KIRA.scr:152
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\14.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:155
    do return ctx:exit("") end -- ARG_KIRA.scr:156
end

script.labels["OnSpeak17"] = function(ctx)
    -- ARG_KIRA.scr:159
    -- gosub OnDone2
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\17.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:163
    do return ctx:exit("") end -- ARG_KIRA.scr:164
end

script.labels["OnVoice19"] = function(ctx)
    -- ARG_KIRA.scr:167
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\19.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:170
    do return ctx:exit("") end -- ARG_KIRA.scr:171
end

script.labels["OnSpeak18"] = function(ctx)
    -- ARG_KIRA.scr:174
    -- gosub OnDone2
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\18.wav, OnDone2, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:178
    do return ctx:exit("") end -- ARG_KIRA.scr:179
end

script.labels["OnAgree"] = function(ctx)
    -- ARG_KIRA.scr:182
    ctx:command("playanim", "Agree DoNothing") -- ARG_KIRA.scr:184
    do return ctx:exit("") end -- ARG_KIRA.scr:185
end

script.labels["OnSpeak19"] = function(ctx)
    -- ARG_KIRA.scr:188
    ctx:command("playanim", "Sc2_Kira19 DoNothing") -- ARG_KIRA.scr:192
    do return ctx:exit("") end -- ARG_KIRA.scr:193
end

script.labels["OnStand"] = function(ctx)
    -- ARG_KIRA.scr:197
    ctx:command("attachprop", "kirasword.ABC KiraSword.dtx Sheath g_hobject2") -- ARG_KIRA.scr:201
    ctx:command("playanim", "Sc2_KIRA16b Walk") -- ARG_KIRA.scr:202
    do return ctx:exit("") end -- ARG_KIRA.scr:203
end

script.labels["Walk"] = function(ctx)
    -- ARG_KIRA.scr:207
    -- Gosub OnDone2
    ctx:command("getobjecthandle", "Markel g_hobject") -- ARG_KIRA.scr:211
    ctx:command("target", "g_hobject") -- ARG_KIRA.scr:212
    ctx:command("getobjecthandle", "KiraMarker1 g_hobject") -- ARG_KIRA.scr:213
    ctx:command("walkto", "g_hobject 8 DrawSword") -- ARG_KIRA.scr:214
    do return ctx:exit("") end -- ARG_KIRA.scr:215
end

script.labels["DrawSword"] = function(ctx)
    -- ARG_KIRA.scr:218
    -- switch to behind Markel Cam
    -- Gosub OnDone2
    ctx:command("playanim", "Sc2_Kira17 Attack") -- ARG_KIRA.scr:224
    do return ctx:exit("") end -- ARG_KIRA.scr:225
end

script.labels["Attack"] = function(ctx)
    -- ARG_KIRA.scr:228
    ctx:command("playanim", "Sc2_Kira20-23 DoNothing") -- ARG_KIRA.scr:231
    do return ctx:exit("") end -- ARG_KIRA.scr:232
end

script.labels["WittyRetort"] = function(ctx)
    -- ARG_KIRA.scr:235
    ctx:command("playanim", "Sc2_Kira22 DoNothing") -- ARG_KIRA.scr:238
    ctx:command("wait", "2 .5 ClapTrigger") -- ARG_KIRA.scr:239
    do return ctx:exit("") end -- ARG_KIRA.scr:240
end

script.labels["ClapTrigger"] = function(ctx)
    -- ARG_KIRA.scr:244
    ctx:command("getobjecthandle", "Sven hSven") -- ARG_KIRA.scr:246
    ctx:command("getobjecthandle", "Bjarni hBjarni") -- ARG_KIRA.scr:247
    ctx:command("getobjecthandle", "Sigmund hSigmund") -- ARG_KIRA.scr:248
    ctx:command("getobjecthandle", "Tryygva hTryygva") -- ARG_KIRA.scr:249
    ctx:command("getobjecthandle", "Forad hForad") -- ARG_KIRA.scr:250
    ctx:trigger("hBjarni", "Clap") -- ARG_KIRA.scr:252
    ctx:trigger("hSigmund", "Clap") -- ARG_KIRA.scr:253
    ctx:trigger("hSven", "Clap") -- ARG_KIRA.scr:254
    ctx:trigger("hForad", "Clap") -- ARG_KIRA.scr:255
    ctx:trigger("htryygva", "clap") -- ARG_KIRA.scr:256
    do return ctx:exit("") end -- ARG_KIRA.scr:257
end

script.labels["OnIdle"] = function(ctx)
    -- ARG_KIRA.scr:260
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_KIRA.scr:263
    do return ctx:exit("") end -- ARG_KIRA.scr:264
end

script.labels["Init"] = function(ctx)
    -- ARG_KIRA.scr:266
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_KIRA.scr:269
    do return ctx:exit("") end -- ARG_KIRA.scr:270
end

script.labels["OnAttach"] = function(ctx)
    -- ARG_KIRA.scr:273
    ctx:command("detachprop", "g_hobject2, false") -- ARG_KIRA.scr:276
    ctx:command("removeobject", "g_hobject2") -- ARG_KIRA.scr:277
    ctx:command("attachprop", "kirasword.ABC KiraSword.dtx RHand1 g_hobject3") -- ARG_KIRA.scr:278
    ctx:command("playsound", "\\sounds\\events\\DrawSword.wav, OnDone2, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:279
    do return ctx:exit("") end -- ARG_KIRA.scr:281
end

script.labels["OnKillMarkel"] = function(ctx)
    -- ARG_KIRA.scr:284
    ctx:command("getobjecthandle", "Markel g_hobject") -- ARG_KIRA.scr:287
    ctx:trigger("g_hobject", "Kill") -- ARG_KIRA.scr:288
    do return ctx:exit("") end -- ARG_KIRA.scr:289
end

script.labels["OnFootstep"] = function(ctx)
    -- ARG_KIRA.scr:292
    ctx:command("playsound", "\\Sounds\\AnimSounds\\Footsteps\\Dirt1.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_KIRA.scr:295
    do return ctx:exit("") end -- ARG_KIRA.scr:296
end

script.labels["Main"] = function(ctx)
    -- ARG_KIRA.scr:299
    -- TraceOn ;delete me!!
    ctx:command("onpoststartworld", "Init") -- ARG_KIRA.scr:303
    ctx:command("onpostminisaveload", "Init") -- ARG_KIRA.scr:304
    ctx:command("onpostsaveload", "Init") -- ARG_KIRA.scr:305
    ctx:command("wait", "1 .1 Init") -- ARG_KIRA.scr:306
    ctx:addTrigger("Clap", "OnApplause") -- ARG_KIRA.scr:307
    ctx:addTrigger("Speak5", "OnSpeak5") -- ARG_KIRA.scr:308
    ctx:command("addmodelkey", "Voice5 OnVoice5") -- ARG_KIRA.scr:309
    ctx:addTrigger("Speak7", "OnSpeak7") -- ARG_KIRA.scr:310
    ctx:command("addmodelkey", "Voice7 OnVoice7") -- ARG_KIRA.scr:311
    ctx:addTrigger("Speak10", "OnSpeak10") -- ARG_KIRA.scr:312
    ctx:command("addmodelkey", "Voice10 OnVoice10") -- ARG_KIRA.scr:313
    ctx:addTrigger("Speak12", "OnSpeak12") -- ARG_KIRA.scr:314
    ctx:command("addmodelkey", "Voice12 OnVoice12") -- ARG_KIRA.scr:315
    ctx:addTrigger("Speak14", "OnSpeak14") -- ARG_KIRA.scr:316
    ctx:command("addmodelkey", "Voice14 OnVoice14") -- ARG_KIRA.scr:317
    ctx:command("addmodelkey", "Done OnDone") -- ARG_KIRA.scr:318
    ctx:command("addmodelkey", "Done2 OnDone2") -- ARG_KIRA.scr:319
    ctx:command("addmodelkey", "Speak17 OnSpeak17") -- ARG_KIRA.scr:320
    ctx:addTrigger("Stand", "OnStand") -- ARG_KIRA.scr:321
    ctx:command("addmodelkey", "Attach OnAttach") -- ARG_KIRA.scr:322
    ctx:addTrigger("Speak18", "OnSpeak18") -- ARG_KIRA.scr:323
    ctx:addTrigger("Speak19", "OnSpeak19") -- ARG_KIRA.scr:324
    ctx:command("addmodelkey", "voice19 OnVoice19") -- ARG_KIRA.scr:325
    ctx:command("addmodelkey", "Done2 OnDone2") -- ARG_KIRA.scr:326
    ctx:command("addmodelkey", "KillMarkel OnKillMarkel") -- ARG_KIRA.scr:327
    ctx:command("addmodelkey", "Clap OnClap") -- ARG_KIRA.scr:328
    ctx:command("addmodelkey", "Witty WittyRetort") -- ARG_KIRA.scr:329
    ctx:addTrigger("Agree", "OnAgree") -- ARG_KIRA.scr:330
    ctx:command("addmodelkey", "Footsteps OnFootstep") -- ARG_KIRA.scr:331
    do return ctx:exit("") end -- ARG_KIRA.scr:332
end

return script
