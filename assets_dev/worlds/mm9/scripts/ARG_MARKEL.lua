-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_MARKEL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ARG_Kira.scr
-- By Timmy
-- handles Kira's Argument Cutscene stuff
script.labels["OnApplause"] = function(ctx)
    -- ARG_MARKEL.scr:15
    ctx:command("playanim", "Applause Init") -- ARG_MARKEL.scr:18
    do return ctx:exit("") end -- ARG_MARKEL.scr:19
end

script.labels["OnScene2"] = function(ctx)
    -- ARG_MARKEL.scr:21
    ctx:command("playanim", "Sc2_MARKEL02 OnIdle") -- ARG_MARKEL.scr:24
    ctx:command("wait", "1 1.5 Book") -- ARG_MARKEL.scr:25
    do return ctx:exit("") end -- ARG_MARKEL.scr:27
end

script.labels["Book"] = function(ctx)
    -- ARG_MARKEL.scr:30
    ctx:command("playsound", "\\sounds\\events\\bookopen.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:32
    ctx:command("getobjecthandle", "Prop8 g_hobject") -- ARG_MARKEL.scr:33
    ctx:trigger("g_hobject", "use") -- ARG_MARKEL.scr:34
    do return ctx:exit("") end -- ARG_MARKEL.scr:35
end

script.labels["OnVoice1"] = function(ctx)
    -- ARG_MARKEL.scr:37
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\01.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:40
    do return ctx:exit("") end -- ARG_MARKEL.scr:41
end

script.labels["OnSpeak4"] = function(ctx)
    -- ARG_MARKEL.scr:44
    ctx:command("playanim", "Sc2_MARKEL04 OnIdle") -- ARG_MARKEL.scr:47
    do return ctx:exit("") end -- ARG_MARKEL.scr:48
end

script.labels["OnVoice4"] = function(ctx)
    -- ARG_MARKEL.scr:51
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\04.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:54
    do return ctx:exit("") end -- ARG_MARKEL.scr:55
end

script.labels["OnSpeak8"] = function(ctx)
    -- ARG_MARKEL.scr:58
    ctx:command("playanim", "Sc2_MARKEL08 OnIdle") -- ARG_MARKEL.scr:61
    do return ctx:exit("") end -- ARG_MARKEL.scr:62
end

script.labels["OnVoice8"] = function(ctx)
    -- ARG_MARKEL.scr:65
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\08.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:68
    do return ctx:exit("") end -- ARG_MARKEL.scr:69
end

script.labels["OnSpeak11"] = function(ctx)
    -- ARG_MARKEL.scr:72
    ctx:command("playanim", "Sc2_MARKEL10 OnIdle") -- ARG_MARKEL.scr:75
    do return ctx:exit("") end -- ARG_MARKEL.scr:76
end

script.labels["OnVoice11"] = function(ctx)
    -- ARG_MARKEL.scr:79
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\11.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:82
    do return ctx:exit("") end -- ARG_MARKEL.scr:83
end

script.labels["OnSpeak13"] = function(ctx)
    -- ARG_MARKEL.scr:86
    ctx:command("playanim", "Sc2_MARKEL13 OnIdle") -- ARG_MARKEL.scr:89
    do return ctx:exit("") end -- ARG_MARKEL.scr:90
end

script.labels["OnVoice13"] = function(ctx)
    -- ARG_MARKEL.scr:93
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\13.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:96
    do return ctx:exit("") end -- ARG_MARKEL.scr:97
end

script.labels["OnSpeak15"] = function(ctx)
    -- ARG_MARKEL.scr:100
    ctx:command("playanim", "Sc2_MARKEL15 OnIdle") -- ARG_MARKEL.scr:103
    do return ctx:exit("") end -- ARG_MARKEL.scr:104
end

script.labels["OnVoice15"] = function(ctx)
    -- ARG_MARKEL.scr:107
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\15.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:110
    do return ctx:exit("") end -- ARG_MARKEL.scr:111
end

script.labels["OnDone"] = function(ctx)
    -- ARG_MARKEL.scr:114
    ctx:command("getobjecthandle", "Argueman g_hobject") -- ARG_MARKEL.scr:117
    ctx:trigger("g_hobject", "Done") -- ARG_MARKEL.scr:118
end

script.labels["OnIdle"] = function(ctx)
    -- ARG_MARKEL.scr:122
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_MARKEL.scr:125
    do return ctx:exit("") end -- ARG_MARKEL.scr:126
end

script.labels["OnMove"] = function(ctx)
    -- ARG_MARKEL.scr:129
    ctx:command("getobjecthandle", "prop7 g_hobject") -- ARG_MARKEL.scr:131
    ctx:command("clearflag", "g_hobject, solid") -- ARG_MARKEL.scr:132
    ctx:command("clearflag", "g_hobject, gravity") -- ARG_MARKEL.scr:133
    ctx:trigger("g_hobject", "Play") -- ARG_MARKEL.scr:134
    ctx:command("playsound", "Sounds\\events\\Chairslide.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:136
    ctx:command("getobjecthandle", "KiraMarker1 g_hobject") -- ARG_MARKEL.scr:137
    ctx:command("walkto", "g_hobject 8 Target") -- ARG_MARKEL.scr:138
    do return ctx:exit("") end -- ARG_MARKEL.scr:139
end

script.labels["OnAgree"] = function(ctx)
    -- ARG_MARKEL.scr:142
    ctx:command("playanim", "Agree DoNothing") -- ARG_MARKEL.scr:144
    do return ctx:exit("") end -- ARG_MARKEL.scr:145
end

script.labels["Target"] = function(ctx)
    -- ARG_MARKEL.scr:148
    ctx:command("getobjecthandle", "Kira g_hobject") -- ARG_MARKEL.scr:151
    ctx:command("target", "g_hobject") -- ARG_MARKEL.scr:152
    do return ctx:exit("") end -- ARG_MARKEL.scr:153
end

script.labels["Init"] = function(ctx)
    -- ARG_MARKEL.scr:156
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_MARKEL.scr:159
    do return ctx:exit("") end -- ARG_MARKEL.scr:160
end

script.labels["OnKill"] = function(ctx)
    -- ARG_MARKEL.scr:164
    ctx:command("playanim", "Sc2_markel21 Dead") -- ARG_MARKEL.scr:167
    do return ctx:exit("") end -- ARG_MARKEL.scr:168
end

script.labels["OnDie"] = function(ctx)
    -- ARG_MARKEL.scr:171
    ctx:command("playsound", "\\sounds\\Weapons\\cflesh.wav, DoNothing, 100, 24000, FALSE, 25") -- ARG_MARKEL.scr:175
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\16a.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:176
    do return ctx:exit("") end -- ARG_MARKEL.scr:177
end

script.labels["Dead"] = function(ctx)
    -- ARG_MARKEL.scr:180
    ctx:command("loopanim", "static_die2 0 DoNothing") -- ARG_MARKEL.scr:184
    do return ctx:exit("") end -- ARG_MARKEL.scr:185
end

script.labels["Onclap"] = function(ctx)
    -- ARG_MARKEL.scr:188
    ctx:command("getrandomint", "1, 7 g_ntemp") -- ARG_MARKEL.scr:190
    if ctx:condition("g_ntemp==1") then -- ARG_MARKEL.scr:192
        ctx:command("playsound", "\\sounds\\events\\clap01.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:193
        do return ctx:exit("") end -- ARG_MARKEL.scr:194
    end -- ARG_MARKEL.scr:195
    if ctx:condition("g_ntemp==2") then -- ARG_MARKEL.scr:197
        ctx:command("playsound", "\\sounds\\events\\clap02.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:198
        do return ctx:exit("") end -- ARG_MARKEL.scr:199
    end -- ARG_MARKEL.scr:200
    if ctx:condition("g_ntemp==3") then -- ARG_MARKEL.scr:202
        ctx:command("playsound", "\\sounds\\events\\clap03.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:203
        do return ctx:exit("") end -- ARG_MARKEL.scr:204
    end -- ARG_MARKEL.scr:205
    if ctx:condition("g_ntemp==4") then -- ARG_MARKEL.scr:207
        ctx:command("playsound", "\\sounds\\events\\clap04.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:208
        do return ctx:exit("") end -- ARG_MARKEL.scr:209
    end -- ARG_MARKEL.scr:210
    if ctx:condition("g_ntemp==5") then -- ARG_MARKEL.scr:212
        ctx:command("playsound", "\\sounds\\events\\clap05.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:213
        do return ctx:exit("") end -- ARG_MARKEL.scr:214
    end -- ARG_MARKEL.scr:215
    if ctx:condition("g_ntemp==6") then -- ARG_MARKEL.scr:217
        ctx:command("playsound", "\\sounds\\events\\clap06.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:218
        do return ctx:exit("") end -- ARG_MARKEL.scr:219
    end -- ARG_MARKEL.scr:220
    if ctx:condition("g_ntemp==7") then -- ARG_MARKEL.scr:222
        ctx:command("playsound", "\\sounds\\events\\clap07.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_MARKEL.scr:223
        do return ctx:exit("") end -- ARG_MARKEL.scr:224
    end -- ARG_MARKEL.scr:225
    do return ctx:exit("") end -- ARG_MARKEL.scr:227
end

script.labels["Main"] = function(ctx)
    -- ARG_MARKEL.scr:229
    -- TraceOn ;delete me!!
    ctx:command("onpoststartworld", "Init") -- ARG_MARKEL.scr:233
    ctx:command("onpostminisaveload", "Init") -- ARG_MARKEL.scr:234
    ctx:command("onpostsaveload", "Init") -- ARG_MARKEL.scr:235
    ctx:command("wait", "1 .1 Init") -- ARG_MARKEL.scr:236
    ctx:addTrigger("Scene2", "OnScene2") -- ARG_MARKEL.scr:237
    ctx:command("addmodelkey", "Voice1 OnVoice1") -- ARG_MARKEL.scr:238
    ctx:addTrigger("Speak4", "OnSpeak4") -- ARG_MARKEL.scr:239
    ctx:command("addmodelkey", "Voice4 OnVoice4") -- ARG_MARKEL.scr:240
    ctx:addTrigger("Speak8", "OnSpeak8") -- ARG_MARKEL.scr:241
    ctx:command("addmodelkey", "Voice8 OnVoice8") -- ARG_MARKEL.scr:242
    ctx:addTrigger("Speak11", "OnSpeak11") -- ARG_MARKEL.scr:243
    ctx:command("addmodelkey", "Voice11 OnVoice11") -- ARG_MARKEL.scr:244
    ctx:addTrigger("Speak13", "OnSpeak13") -- ARG_MARKEL.scr:245
    ctx:command("addmodelkey", "Voice13 OnVoice13") -- ARG_MARKEL.scr:246
    ctx:addTrigger("Speak15", "OnSpeak15") -- ARG_MARKEL.scr:247
    ctx:command("addmodelkey", "Voice15 OnVoice15") -- ARG_MARKEL.scr:248
    ctx:addTrigger("Move", "OnMove") -- ARG_MARKEL.scr:249
    ctx:command("addmodelkey", "Done OnDone") -- ARG_MARKEL.scr:250
    ctx:addTrigger("Kill", "OnKill") -- ARG_MARKEL.scr:251
    ctx:command("addmodelkey", "Die OnDie") -- ARG_MARKEL.scr:252
    ctx:addTrigger("Clap", "OnApplause") -- ARG_MARKEL.scr:253
    ctx:command("addmodelkey", "Clap OnClap") -- ARG_MARKEL.scr:254
    ctx:addTrigger("Agree", "OnAgree") -- ARG_MARKEL.scr:255
    ctx:command("wait", "1 .1 Init") -- ARG_MARKEL.scr:256
    do return ctx:exit("") end -- ARG_MARKEL.scr:257
end

return script
