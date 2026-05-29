-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_FORAD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ARG_Kira.scr
-- By Timmy
-- handles Kira's Argument Cutscene stuff
script.labels["OnAgree"] = function(ctx)
    -- ARG_FORAD.scr:12
    ctx:self():playAnimation("Agree", "Init") -- ARG_FORAD.scr:14
    do return ctx:exit("") end -- ARG_FORAD.scr:15
end

script.labels["OnApplause"] = function(ctx)
    -- ARG_FORAD.scr:17
    ctx:self():playAnimation("Applause", "Init") -- ARG_FORAD.scr:20
    do return ctx:exit("") end -- ARG_FORAD.scr:21
end

script.labels["OnDone"] = function(ctx)
    -- ARG_FORAD.scr:23
    -- loopanim Sc2_Bjarni2 0 DoNothing
    ctx:object("Argueman"):trigger("Done") -- ARG_FORAD.scr:27-28
    do return ctx:exit("") end -- ARG_FORAD.scr:29
end

script.labels["OnSpeak6"] = function(ctx)
    -- ARG_FORAD.scr:32
    ctx:self():playAnimation("Sc2_Forad6", "OnIdle") -- ARG_FORAD.scr:35
    do return ctx:exit("") end -- ARG_FORAD.scr:37
end

script.labels["OnVoice6"] = function(ctx)
    -- ARG_FORAD.scr:40
    ctx:playSound("\\voices\\cinema\\TheArgument\\06.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:44
    do return ctx:exit("") end -- ARG_FORAD.scr:45
end

script.labels["OnSpeak20"] = function(ctx)
    -- ARG_FORAD.scr:48
    ctx:self():playAnimation("Sc2_Forad26", "OnIdle") -- ARG_FORAD.scr:51
    do return ctx:exit("") end -- ARG_FORAD.scr:53
end

script.labels["OnVoice20"] = function(ctx)
    -- ARG_FORAD.scr:56
    ctx:playSound("\\voices\\cinema\\TheArgument\\20.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:60
    do return ctx:exit("") end -- ARG_FORAD.scr:61
end

script.labels["OnIdle"] = function(ctx)
    -- ARG_FORAD.scr:65
    ctx:self():loopAnimation("Sit", 0, "DoNothing") -- ARG_FORAD.scr:68
    do return ctx:exit("") end -- ARG_FORAD.scr:69
end

script.labels["Init"] = function(ctx)
    -- ARG_FORAD.scr:72
    ctx:self():loopAnimation("Sit", 0, "DoNothing") -- ARG_FORAD.scr:75
    do return ctx:exit("") end -- ARG_FORAD.scr:76
end

script.labels["Onclap"] = function(ctx)
    -- ARG_FORAD.scr:79
    ctx:randomInt(1, 7, "g_ntemp") -- ARG_FORAD.scr:81
    if ctx:condition("g_ntemp==1") then -- ARG_FORAD.scr:83
        ctx:playSound("\\sounds\\events\\clap01.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:84
        do return ctx:exit("") end -- ARG_FORAD.scr:85
    end -- ARG_FORAD.scr:86
    if ctx:condition("g_ntemp==2") then -- ARG_FORAD.scr:88
        ctx:playSound("\\sounds\\events\\clap02.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:89
        do return ctx:exit("") end -- ARG_FORAD.scr:90
    end -- ARG_FORAD.scr:91
    if ctx:condition("g_ntemp==3") then -- ARG_FORAD.scr:93
        ctx:playSound("\\sounds\\events\\clap03.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:94
        do return ctx:exit("") end -- ARG_FORAD.scr:95
    end -- ARG_FORAD.scr:96
    if ctx:condition("g_ntemp==4") then -- ARG_FORAD.scr:98
        ctx:playSound("\\sounds\\events\\clap04.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:99
        do return ctx:exit("") end -- ARG_FORAD.scr:100
    end -- ARG_FORAD.scr:101
    if ctx:condition("g_ntemp==5") then -- ARG_FORAD.scr:103
        ctx:playSound("\\sounds\\events\\clap05.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:104
        do return ctx:exit("") end -- ARG_FORAD.scr:105
    end -- ARG_FORAD.scr:106
    if ctx:condition("g_ntemp==6") then -- ARG_FORAD.scr:108
        ctx:playSound("\\sounds\\events\\clap06.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:109
        do return ctx:exit("") end -- ARG_FORAD.scr:110
    end -- ARG_FORAD.scr:111
    if ctx:condition("g_ntemp==7") then -- ARG_FORAD.scr:113
        ctx:playSound("\\sounds\\events\\clap07.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_FORAD.scr:114
        do return ctx:exit("") end -- ARG_FORAD.scr:115
    end -- ARG_FORAD.scr:116
    do return ctx:exit("") end -- ARG_FORAD.scr:118
end

script.labels["Main"] = function(ctx)
    -- ARG_FORAD.scr:121
    -- TraceOn ;delete me!!
    ctx:onEvent("OnPostStartWorld", "Init") -- ARG_FORAD.scr:125
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- ARG_FORAD.scr:126
    ctx:onEvent("OnPostSaveLoad", "Init") -- ARG_FORAD.scr:127
    ctx:wait(1, .1, "Init") -- ARG_FORAD.scr:128
    ctx:addTrigger("Speak6", "OnSpeak6") -- ARG_FORAD.scr:129
    ctx:addModelKey("Voice6", "OnVoice6") -- ARG_FORAD.scr:130
    ctx:addTrigger("Speak20", "OnSpeak20") -- ARG_FORAD.scr:131
    ctx:addModelKey("Voice20", "OnVoice20") -- ARG_FORAD.scr:132
    ctx:addModelKey("Done", "OnDone") -- ARG_FORAD.scr:133
    ctx:addTrigger("Clap", "OnApplause") -- ARG_FORAD.scr:134
    ctx:addModelKey("Clap", "OnCLap") -- ARG_FORAD.scr:135
    ctx:addTrigger("Agree", "OnAgree") -- ARG_FORAD.scr:136
    do return ctx:exit("") end -- ARG_FORAD.scr:137
end

return script
