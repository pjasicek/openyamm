-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "KNUTSPEECH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- knutspeech.scr
-- By Timmy
-- handles knut fastmouth's political rant.
-- parameters
-- p0 Dedit object name for Ake
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
script.labels["Onblabber"] = function(ctx)
    -- KNUTSPEECH.scr:22
    -- knuts blabber
    ctx:wait(1, 1, "Speak") -- KNUTSPEECH.scr:26
    mm9.gosub(script, ctx, "Conv") -- KNUTSPEECH.scr:27
    do return ctx:exit("") end -- KNUTSPEECH.scr:29
end

script.labels["Speak"] = function(ctx)
    -- KNUTSPEECH.scr:31
    if ctx:condition("sound==0") then -- KNUTSPEECH.scr:34
        ctx:state().sound = 1 -- KNUTSPEECH.scr:35
        ctx:giveKey(114) -- KNUTSPEECH.scr:36
        ctx:playSoundHandle("voices\\cinema\\socialism\\KnutFAstmouth01.wav", "soundhandle", 768, "FALSE", 100) -- KNUTSPEECH.scr:37
        ctx:getSoundDuration("", "soundhandle", "sounddur") -- KNUTSPEECH.scr:38
        -- trigger ake's script to start heckles
        ctx:object("params"):trigger("blabber") -- KNUTSPEECH.scr:41-42
        ctx:state().sounddur = (tonumber(ctx:state().sounddur) or 0) - 5 -- KNUTSPEECH.scr:43
        ctx:wait(1, "sounddur", "shutup") -- KNUTSPEECH.scr:44
    end -- KNUTSPEECH.scr:45
    do return ctx:exit("") end -- KNUTSPEECH.scr:47
end

script.labels["Conv"] = function(ctx)
    -- KNUTSPEECH.scr:50
    if ctx:condition("nShutup==TRUE") then -- KNUTSPEECH.scr:52
        do return ctx:exit("") end -- KNUTSPEECH.scr:53
    end -- KNUTSPEECH.scr:54
    ctx:self():converse(-1, "conv") -- KNUTSPEECH.scr:56
    do return ctx:exit("") end -- KNUTSPEECH.scr:57
end

script.labels["OnUse"] = function(ctx)
    -- KNUTSPEECH.scr:59
    -- if sound is playing, kill it
    if ctx:condition("sound==1") then -- KNUTSPEECH.scr:64
        ctx:killSound("soundhandle") -- KNUTSPEECH.scr:65
        ctx:state().sound = 0 -- KNUTSPEECH.scr:67
        ctx:state().g_ntemp = 0 -- KNUTSPEECH.scr:68
    end -- KNUTSPEECH.scr:69
    -- start rude dialog
    -- DoRude 261
    do return ctx:exit("") end -- KNUTSPEECH.scr:72
end

script.labels["shutup"] = function(ctx)
    -- KNUTSPEECH.scr:75
    ctx:state().nShutup = true -- KNUTSPEECH.scr:78
    ctx:trigger("g_hobject", "shutup") -- KNUTSPEECH.scr:79
    ctx:wait(1, 6, "onexit") -- KNUTSPEECH.scr:80
    do return ctx:exit("") end -- KNUTSPEECH.scr:81
end

script.labels["Onexit"] = function(ctx)
    -- KNUTSPEECH.scr:84
    -- kill the sound if it's done
    ctx:isSoundDone("soundhandle", "sounddone") -- KNUTSPEECH.scr:89
    if ctx:condition("sounddone==1") then -- KNUTSPEECH.scr:90
        ctx:killSound("soundhandle") -- KNUTSPEECH.scr:91
    end -- KNUTSPEECH.scr:92
    -- goto ondrink
    do return ctx:exit("") end -- KNUTSPEECH.scr:94
end

script.labels["GoPosition1"] = function(ctx)
    -- KNUTSPEECH.scr:97
    ctx:self():setPos(3424.0, 1344.0, -672.0) -- KNUTSPEECH.scr:99
    ctx:self():faceDir(0, 0, 0, 0) -- KNUTSPEECH.scr:100
    do return ctx:exit("") end -- KNUTSPEECH.scr:102
end

script.labels["GoPosition2"] = function(ctx)
    -- KNUTSPEECH.scr:105
    ctx:self():setPos(3494, 1254, 3166) -- KNUTSPEECH.scr:107
    ctx:self():faceDir(0.78, 0, 0.63, 0) -- KNUTSPEECH.scr:108
    do return ctx:exit("") end -- KNUTSPEECH.scr:110
end

script.labels["GoPosition3"] = function(ctx)
    -- KNUTSPEECH.scr:113
    ctx:self():setPos(-933, 1254, 2036) -- KNUTSPEECH.scr:116
    ctx:self():faceDir(0.7, 0, 0.72, 0) -- KNUTSPEECH.scr:117
    do return ctx:exit("") end -- KNUTSPEECH.scr:119
end

script.labels["GoPosition4"] = function(ctx)
    -- KNUTSPEECH.scr:122
    ctx:self():setPos(-2324, 1254, 4559) -- KNUTSPEECH.scr:125
    ctx:self():faceDir(0.75, 0, 0.67, 0) -- KNUTSPEECH.scr:126
    do return ctx:exit("") end -- KNUTSPEECH.scr:128
end

script.labels["SetupPosition"] = function(ctx)
    -- KNUTSPEECH.scr:131
    ctx:state().nPosition = (tonumber(ctx:state().nPosition) or 0) + 1 -- KNUTSPEECH.scr:136
    if ctx:condition("nPosition>4") then -- KNUTSPEECH.scr:138
        ctx:state().nPosition = 1 -- KNUTSPEECH.scr:139
    end -- KNUTSPEECH.scr:140
    if ctx:condition("nPosition==1") then -- KNUTSPEECH.scr:142
        do return mm9.gotoLabel(script, ctx, "GoPosition1") end -- KNUTSPEECH.scr:143
    end -- KNUTSPEECH.scr:144
    if ctx:condition("nPosition==2") then -- KNUTSPEECH.scr:146
        do return mm9.gotoLabel(script, ctx, "GoPosition2") end -- KNUTSPEECH.scr:147
    end -- KNUTSPEECH.scr:148
    if ctx:condition("nPosition==3") then -- KNUTSPEECH.scr:150
        do return mm9.gotoLabel(script, ctx, "GoPosition3") end -- KNUTSPEECH.scr:151
    end -- KNUTSPEECH.scr:152
    if ctx:condition("nPosition==4") then -- KNUTSPEECH.scr:154
        do return mm9.gotoLabel(script, ctx, "GoPosition4") end -- KNUTSPEECH.scr:155
    end -- KNUTSPEECH.scr:156
    do return ctx:exit("") end -- KNUTSPEECH.scr:158
end

script.labels["PostMiniSaveLoad"] = function(ctx)
    -- KNUTSPEECH.scr:161
    mm9.gosub(script, ctx, "SetupPosition") -- KNUTSPEECH.scr:164
    do return ctx:exit("") end -- KNUTSPEECH.scr:165
end

script.labels["Main"] = function(ctx)
    -- KNUTSPEECH.scr:168
    -- TraceOn ;delete me!!
    ctx:addTrigger("blabber", "Onblabber") -- KNUTSPEECH.scr:172
    -- ADD THIS BACK IN WHEN PROPS CAN REACT TO WAIT COMMAND
    ctx:addTrigger("Use", "OnUse") -- KNUTSPEECH.scr:173
    ctx:onEvent("OnFoundPlayer", "OnBlabber") -- KNUTSPEECH.scr:174
    ctx:getParam(0, "Params") -- KNUTSPEECH.scr:175
    ctx:state().sound = 0 -- KNUTSPEECH.scr:176
    ctx:state().g_ntemp = 0 -- KNUTSPEECH.scr:177
    if ctx:hasKey(114) then -- KNUTSPEECH.scr:178-179
        ctx:state().sound = 1 -- KNUTSPEECH.scr:180
    end -- KNUTSPEECH.scr:181
    mm9.gosub(script, ctx, "SetupPosition") -- KNUTSPEECH.scr:183
    ctx:onEvent("OnPostMiniSaveLoad", "PostMiniSaveLoad") -- KNUTSPEECH.scr:185
    ctx:addTrigger("GoPosition1", "GoPosition1") -- KNUTSPEECH.scr:186
    ctx:addTrigger("GoPosition2", "GoPosition2") -- KNUTSPEECH.scr:187
    ctx:addTrigger("GoPosition3", "GoPosition3") -- KNUTSPEECH.scr:188
    ctx:addTrigger("GoPosition4", "GoPosition4") -- KNUTSPEECH.scr:189
    do return ctx:exit("") end -- KNUTSPEECH.scr:192
end

return script
