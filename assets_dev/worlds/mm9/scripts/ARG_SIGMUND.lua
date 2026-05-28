-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_SIGMUND.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ARG_Kira.scr
-- By Timmy
-- handles Kira's Argument Cutscene stuff
script.labels["OnAgree"] = function(ctx)
    -- ARG_SIGMUND.scr:15
    ctx:command("playanim", "Agree Init") -- ARG_SIGMUND.scr:17
    do return ctx:exit("") end -- ARG_SIGMUND.scr:18
end

script.labels["OnApplause"] = function(ctx)
    -- ARG_SIGMUND.scr:20
    ctx:command("playanim", "Applause Init") -- ARG_SIGMUND.scr:23
    do return ctx:exit("") end -- ARG_SIGMUND.scr:24
end

script.labels["OnShake"] = function(ctx)
    -- ARG_SIGMUND.scr:26
    ctx:command("playanim", "Sc2_Sigmund1c OnIdle") -- ARG_SIGMUND.scr:29
    do return ctx:exit("") end -- ARG_SIGMUND.scr:30
end

script.labels["OnSign"] = function(ctx)
    -- ARG_SIGMUND.scr:34
    ctx:command("playsound", "sSign, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:37
    do return ctx:exit("") end -- ARG_SIGMUND.scr:38
end

script.labels["OnShot1A"] = function(ctx)
    -- ARG_SIGMUND.scr:41
    ctx:command("getobjecthandle", "Prop9 g_hobject") -- ARG_SIGMUND.scr:44
    ctx:trigger("g_hobject", "play") -- ARG_SIGMUND.scr:45
    ctx:command("playsound", "\\sounds\\Events\\bookpgturn01.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:46
    ctx:command("playanim", "Sc2_Sigmund1b OnIdle") -- ARG_SIGMUND.scr:47
    do return ctx:exit("") end -- ARG_SIGMUND.scr:48
end

script.labels["OnDone"] = function(ctx)
    -- ARG_SIGMUND.scr:51
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_SIGMUND.scr:54
    ctx:command("getobjecthandle", "Argueman g_hobject") -- ARG_SIGMUND.scr:55
    ctx:trigger("g_hobject", "Done") -- ARG_SIGMUND.scr:56
    do return ctx:exit("") end -- ARG_SIGMUND.scr:57
end

script.labels["OnSpeak3"] = function(ctx)
    -- ARG_SIGMUND.scr:60
    ctx:command("playanim", "Sc2_Sigmund3b OnIdle") -- ARG_SIGMUND.scr:63
    do return ctx:exit("") end -- ARG_SIGMUND.scr:65
end

script.labels["OnVoice3"] = function(ctx)
    -- ARG_SIGMUND.scr:68
    ctx:command("playsound", "\\voices\\cinema\\TheArgument\\03.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:72
    do return ctx:exit("") end -- ARG_SIGMUND.scr:73
end

script.labels["OnIdle"] = function(ctx)
    -- ARG_SIGMUND.scr:76
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_SIGMUND.scr:79
    do return ctx:exit("") end -- ARG_SIGMUND.scr:80
end

script.labels["Onclap"] = function(ctx)
    -- ARG_SIGMUND.scr:83
    ctx:command("getrandomint", "1, 7 g_ntemp") -- ARG_SIGMUND.scr:85
    if ctx:condition("g_ntemp==1") then -- ARG_SIGMUND.scr:87
        ctx:command("playsound", "\\sounds\\events\\clap01.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:88
        do return ctx:exit("") end -- ARG_SIGMUND.scr:89
    end -- ARG_SIGMUND.scr:90
    if ctx:condition("g_ntemp==2") then -- ARG_SIGMUND.scr:92
        ctx:command("playsound", "\\sounds\\events\\clap02.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:93
        do return ctx:exit("") end -- ARG_SIGMUND.scr:94
    end -- ARG_SIGMUND.scr:95
    if ctx:condition("g_ntemp==3") then -- ARG_SIGMUND.scr:97
        ctx:command("playsound", "\\sounds\\events\\clap03.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:98
        do return ctx:exit("") end -- ARG_SIGMUND.scr:99
    end -- ARG_SIGMUND.scr:100
    if ctx:condition("g_ntemp==4") then -- ARG_SIGMUND.scr:102
        ctx:command("playsound", "\\sounds\\events\\clap04.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:103
        do return ctx:exit("") end -- ARG_SIGMUND.scr:104
    end -- ARG_SIGMUND.scr:105
    if ctx:condition("g_ntemp==5") then -- ARG_SIGMUND.scr:107
        ctx:command("playsound", "\\sounds\\events\\clap05.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:108
        do return ctx:exit("") end -- ARG_SIGMUND.scr:109
    end -- ARG_SIGMUND.scr:110
    if ctx:condition("g_ntemp==6") then -- ARG_SIGMUND.scr:112
        ctx:command("playsound", "\\sounds\\events\\clap06.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:113
        do return ctx:exit("") end -- ARG_SIGMUND.scr:114
    end -- ARG_SIGMUND.scr:115
    if ctx:condition("g_ntemp==7") then -- ARG_SIGMUND.scr:117
        ctx:command("playsound", "\\sounds\\events\\clap07.wav, DoNothing, 100, 24000, FALSE, 100") -- ARG_SIGMUND.scr:118
        do return ctx:exit("") end -- ARG_SIGMUND.scr:119
    end -- ARG_SIGMUND.scr:120
    do return ctx:exit("") end -- ARG_SIGMUND.scr:122
end

script.labels["Init"] = function(ctx)
    -- ARG_SIGMUND.scr:124
    ctx:command("loopanim", "Sit 0 DoNothing") -- ARG_SIGMUND.scr:127
    do return ctx:exit("") end -- ARG_SIGMUND.scr:128
end

script.labels["Main"] = function(ctx)
    -- ARG_SIGMUND.scr:131
    -- TraceOn ;delete me!!
    ctx:addTrigger("Shot1A", "OnShot1A") -- ARG_SIGMUND.scr:135
    ctx:command("onpoststartworld", "Init") -- ARG_SIGMUND.scr:136
    ctx:command("onpostminisaveload", "Init") -- ARG_SIGMUND.scr:137
    ctx:command("onpostsaveload", "Init") -- ARG_SIGMUND.scr:138
    ctx:command("wait", "1 .1 Init") -- ARG_SIGMUND.scr:139
    ctx:command("addmodelkey", "Voice3 ONVoice3") -- ARG_SIGMUND.scr:140
    ctx:addTrigger("Speak3", "ONSpeak3") -- ARG_SIGMUND.scr:141
    ctx:command("addmodelkey", "Done OnDone") -- ARG_SIGMUND.scr:142
    ctx:addTrigger("Shake", "OnShake") -- ARG_SIGMUND.scr:143
    ctx:addTrigger("Clap", "OnApplause") -- ARG_SIGMUND.scr:144
    ctx:command("addmodelkey", "Clap OnClap") -- ARG_SIGMUND.scr:145
    ctx:addTrigger("Agree", "OnAgree") -- ARG_SIGMUND.scr:146
    ctx:command("addmodelkey", "Sign OnSign") -- ARG_SIGMUND.scr:147
    do return ctx:exit("") end -- ARG_SIGMUND.scr:148
end

return script
