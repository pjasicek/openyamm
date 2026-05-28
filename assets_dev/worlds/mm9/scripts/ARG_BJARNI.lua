-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_BJARNI.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ARG_Kira.scr
-- By Timmy
-- handles Kira's Argument Cutscene stuff
script.labels["OnAgree"] = function(ctx)
    -- ARG_BJARNI.scr:16
    ctx:command("playsound", "sAgree, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:20
    ctx:command("playanim", "Agree OnIdle") -- ARG_BJARNI.scr:21
    do return ctx:exit("") end -- ARG_BJARNI.scr:22
end

script.labels["OnSign"] = function(ctx)
    -- ARG_BJARNI.scr:25
    ctx:command("playsound", "sSign, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:28
    do return ctx:exit("") end -- ARG_BJARNI.scr:29
end

script.labels["OnShake"] = function(ctx)
    -- ARG_BJARNI.scr:32
    ctx:command("playanim", "Sc2_Bjarni1c OnIdle") -- ARG_BJARNI.scr:35
    do return ctx:exit("") end -- ARG_BJARNI.scr:36
end

script.labels["Init"] = function(ctx)
    -- ARG_BJARNI.scr:40
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_BJARNI.scr:43
    do return ctx:exit("") end -- ARG_BJARNI.scr:44
end

script.labels["OnIdle"] = function(ctx)
    -- ARG_BJARNI.scr:47
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_BJARNI.scr:50
    do return ctx:exit("") end -- ARG_BJARNI.scr:51
end

script.labels["On1A"] = function(ctx)
    -- ARG_BJARNI.scr:54
    ctx:command("playanim", "Sc2_Bjarni1a Init") -- ARG_BJARNI.scr:57
    do return ctx:exit("") end -- ARG_BJARNI.scr:58
end

script.labels["Cam3"] = function(ctx)
    -- ARG_BJARNI.scr:61
    -- loopanim Sc2_Bjarni2 0 DoNothing
    ctx:command("getobjecthandle", "Argueman g_hobject") -- ARG_BJARNI.scr:65
    ctx:trigger("g_hobject", "Done") -- ARG_BJARNI.scr:66
    do return ctx:exit("") end -- ARG_BJARNI.scr:67
end

script.labels["OnDone"] = function(ctx)
    -- ARG_BJARNI.scr:70
    -- loopanim Sc2_Bjarni2 0 DoNothing
    ctx:command("getobjecthandle", "Argueman g_hobject") -- ARG_BJARNI.scr:74
    ctx:trigger("g_hobject", "Done") -- ARG_BJARNI.scr:75
    do return ctx:exit("") end -- ARG_BJARNI.scr:76
end

script.labels["OnSpeak2"] = function(ctx)
    -- ARG_BJARNI.scr:79
    ctx:command("playanim", "Sc2_Bjarni2 OnIdle") -- ARG_BJARNI.scr:82
    do return ctx:exit("") end -- ARG_BJARNI.scr:84
end

script.labels["OnVoice2"] = function(ctx)
    -- ARG_BJARNI.scr:87
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\02.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:91
    do return ctx:exit("") end -- ARG_BJARNI.scr:92
end

script.labels["OnSpeak9"] = function(ctx)
    -- ARG_BJARNI.scr:95
    ctx:command("playanim", "Sc2_Bjarni9 OnIdle") -- ARG_BJARNI.scr:98
    do return ctx:exit("") end -- ARG_BJARNI.scr:100
end

script.labels["OnVoice9"] = function(ctx)
    -- ARG_BJARNI.scr:103
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\09.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:107
    do return ctx:exit("") end -- ARG_BJARNI.scr:108
end

script.labels["OnSpeak16"] = function(ctx)
    -- ARG_BJARNI.scr:111
    ctx:command("playanim", "Sc2_bjarni15 OnIdle") -- ARG_BJARNI.scr:114
    ctx:command("getobjecthandle", "Markel g_hobject") -- ARG_BJARNI.scr:116
    ctx:trigger("g_hobject", "Move") -- ARG_BJARNI.scr:117
    -- gosub OnVoice16
    -- wait 1 2 OnDone
    do return ctx:exit("") end -- ARG_BJARNI.scr:120
end

script.labels["OnVoice16"] = function(ctx)
    -- ARG_BJARNI.scr:123
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\16.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:127
    do return ctx:exit("") end -- ARG_BJARNI.scr:128
end

script.labels["OnApplause"] = function(ctx)
    -- ARG_BJARNI.scr:130
    ctx:command("playanim", "Applause OnIdle") -- ARG_BJARNI.scr:133
    do return ctx:exit("") end -- ARG_BJARNI.scr:134
end

script.labels["Onclap"] = function(ctx)
    -- ARG_BJARNI.scr:137
    ctx:command("getrandomint", "1, 7 g_ntemp") -- ARG_BJARNI.scr:139
    if ctx:condition("g_ntemp==1") then -- ARG_BJARNI.scr:141
        ctx:command("playsound", "\\sounds\\events\\clap01.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:142
        do return ctx:exit("") end -- ARG_BJARNI.scr:143
    end -- ARG_BJARNI.scr:144
    if ctx:condition("g_ntemp==2") then -- ARG_BJARNI.scr:146
        ctx:command("playsound", "\\sounds\\events\\clap02.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:147
        do return ctx:exit("") end -- ARG_BJARNI.scr:148
    end -- ARG_BJARNI.scr:149
    if ctx:condition("g_ntemp==3") then -- ARG_BJARNI.scr:151
        ctx:command("playsound", "\\sounds\\events\\clap03.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:152
        do return ctx:exit("") end -- ARG_BJARNI.scr:153
    end -- ARG_BJARNI.scr:154
    if ctx:condition("g_ntemp==4") then -- ARG_BJARNI.scr:156
        ctx:command("playsound", "\\sounds\\events\\clap04.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:157
        do return ctx:exit("") end -- ARG_BJARNI.scr:158
    end -- ARG_BJARNI.scr:159
    if ctx:condition("g_ntemp==5") then -- ARG_BJARNI.scr:161
        ctx:command("playsound", "\\sounds\\events\\clap05.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:162
        do return ctx:exit("") end -- ARG_BJARNI.scr:163
    end -- ARG_BJARNI.scr:164
    if ctx:condition("g_ntemp==6") then -- ARG_BJARNI.scr:166
        ctx:command("playsound", "\\sounds\\events\\clap06.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:167
        do return ctx:exit("") end -- ARG_BJARNI.scr:168
    end -- ARG_BJARNI.scr:169
    if ctx:condition("g_ntemp==7") then -- ARG_BJARNI.scr:171
        ctx:command("playsound", "\\sounds\\events\\clap07.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_BJARNI.scr:172
        do return ctx:exit("") end -- ARG_BJARNI.scr:173
    end -- ARG_BJARNI.scr:174
    do return ctx:exit("") end -- ARG_BJARNI.scr:176
end

script.labels["Main"] = function(ctx)
    -- ARG_BJARNI.scr:179
    -- TraceOn ;delete me!!
    ctx:addTrigger("Shot1A", "On1A") -- ARG_BJARNI.scr:183
    ctx:command("onpoststartworld", "Init") -- ARG_BJARNI.scr:186
    ctx:command("onpostminisaveload", "Init") -- ARG_BJARNI.scr:187
    ctx:command("onpostsaveload", "Init") -- ARG_BJARNI.scr:188
    ctx:command("wait", "1 .1 Init") -- ARG_BJARNI.scr:189
    ctx:addTrigger("Speak2", "OnSpeak2") -- ARG_BJARNI.scr:190
    ctx:command("addmodelkey", "Cam3 Cam3") -- ARG_BJARNI.scr:191
    ctx:command("addmodelkey", "Voice2 OnVoice2") -- ARG_BJARNI.scr:192
    ctx:addTrigger("Speak9", "OnSpeak9") -- ARG_BJARNI.scr:193
    ctx:command("addmodelkey", "Voice9 OnVoice9") -- ARG_BJARNI.scr:194
    ctx:addTrigger("Speak16", "OnSpeak16") -- ARG_BJARNI.scr:195
    ctx:command("addmodelkey", "Voice16 OnVoice16") -- ARG_BJARNI.scr:196
    ctx:command("addmodelkey", "Done OnDone") -- ARG_BJARNI.scr:197
    ctx:addTrigger("Shake", "OnShake") -- ARG_BJARNI.scr:198
    ctx:addTrigger("Clap", "OnApplause") -- ARG_BJARNI.scr:199
    ctx:command("addmodelkey", "Clap OnClap") -- ARG_BJARNI.scr:200
    ctx:addTrigger("Agree", "OnAgree") -- ARG_BJARNI.scr:201
    ctx:command("addmodelkey", "Sign OnSign") -- ARG_BJARNI.scr:202
    do return ctx:exit("") end -- ARG_BJARNI.scr:203
end

return script
