-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AKE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- ake.scr
-- By Timmy
-- handles ake's heckles of knut fastmouth
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
-- time to wait between heckles in seconds
-- knut has finally shut up
script.labels["Onblabber"] = function(ctx)
    -- AKE.scr:22
    -- ake's heckles
    ctx:getParam(0, "g_hobject") -- AKE.scr:26
    ctx:self():setTarget(ctx:object("g_hobject")) -- AKE.scr:27
    if ctx:condition("shutup==1") then -- AKE.scr:29
        do return mm9.gotoLabel(script, ctx, "Onexit") end -- AKE.scr:30
    end -- AKE.scr:31
    ctx:killSound("soundhandle") -- AKE.scr:32
    ctx:randomInt(5, 10, "knutwait") -- AKE.scr:33
    ctx:wait(1, "knutwait", "blabber") -- AKE.scr:34
    do return ctx:exit("") end -- AKE.scr:35
    do return ctx:exit("") end -- AKE.scr:38
end

script.labels["blabber"] = function(ctx)
    -- AKE.scr:42
    -- plays random heckle
    ctx:state().sound = 1 -- AKE.scr:48
    if ctx:condition("g_ntemp==1") then -- AKE.scr:49
        ctx:self():converse(-1, "DoNothing") -- AKE.scr:50
        ctx:playSoundHandle("voices\\cinema\\socialism\\ake01.wav", "soundhandle", 768, "FALSE", 100) -- AKE.scr:51
        ctx:getSoundDuration("", "soundhandle", "sounddur") -- AKE.scr:52
        ctx:state().g_ntemp = 2 -- AKE.scr:53
        ctx:wait(1, "sounddur", "Onblabber") -- AKE.scr:54
        do return ctx:exit("") end -- AKE.scr:55
    end -- AKE.scr:56
    if ctx:condition("g_ntemp==2") then -- AKE.scr:58
        ctx:self():converse(-1, "DoNothing") -- AKE.scr:59
        ctx:playSoundHandle("voices\\cinema\\socialism\\ake02.wav", "soundhandle", 768, "FALSE", 100) -- AKE.scr:60
        ctx:getSoundDuration("", "soundhandle", "sounddur") -- AKE.scr:61
        ctx:state().g_ntemp = 3 -- AKE.scr:62
        ctx:wait(1, "sounddur", "Onblabber") -- AKE.scr:63
        do return ctx:exit("") end -- AKE.scr:64
    end -- AKE.scr:65
    if ctx:condition("g_ntemp==3") then -- AKE.scr:67
        ctx:self():converse(-1, "DoNothing") -- AKE.scr:68
        ctx:playSoundHandle("voices\\cinema\\socialism\\ake03.wav", "soundhandle", 768, "FALSE", 100) -- AKE.scr:69
        ctx:getSoundDuration("", "soundhandle", "sounddur") -- AKE.scr:70
        ctx:state().g_ntemp = 4 -- AKE.scr:71
        ctx:wait(1, "sounddur", "Onblabber") -- AKE.scr:72
        do return ctx:exit("") end -- AKE.scr:73
    end -- AKE.scr:74
    if ctx:condition("g_ntemp==4") then -- AKE.scr:76
        ctx:self():converse(-1, "DoNothing") -- AKE.scr:77
        ctx:playSoundHandle("voices\\cinema\\socialism\\ake04.wav", "soundhandle", 768, "FALSE", 100) -- AKE.scr:78
        ctx:getSoundDuration("", "soundhandle", "sounddur") -- AKE.scr:79
        ctx:state().g_ntemp = 5 -- AKE.scr:80
        ctx:wait(1, "sounddur", "Onblabber") -- AKE.scr:81
        do return ctx:exit("") end -- AKE.scr:82
    end -- AKE.scr:83
    if ctx:condition("g_ntemp==5") then -- AKE.scr:84
        ctx:self():converse(-1, "DoNothing") -- AKE.scr:85
        ctx:playSoundHandle("voices\\cinema\\socialism\\ake05.wav", "soundhandle", 768, "FALSE", 100) -- AKE.scr:86
        ctx:getSoundDuration("", "soundhandle", "sounddur") -- AKE.scr:87
        ctx:state().g_ntemp = 1 -- AKE.scr:88
        ctx:wait(1, "sounddur", "Onblabber") -- AKE.scr:89
        do return ctx:exit("") end -- AKE.scr:90
    end -- AKE.scr:91
    do return ctx:exit("") end -- AKE.scr:93
end

script.labels["OnUse"] = function(ctx)
    -- AKE.scr:100
    -- if sound is playing, kill it
    if ctx:condition("sound==1") then -- AKE.scr:105
        ctx:killSound("soundhandle") -- AKE.scr:106
        ctx:state().sound = 0 -- AKE.scr:108
        ctx:state().g_ntemp = 0 -- AKE.scr:109
    end -- AKE.scr:110
    -- start rude dialog
    -- DoRude 261
    do return ctx:exit("") end -- AKE.scr:113
end

script.labels["Onexit"] = function(ctx)
    -- AKE.scr:117
    -- kill the sound if it's done
    ctx:state().shutup = 1 -- AKE.scr:122
    ctx:isSoundDone("soundhandle", "sounddone") -- AKE.scr:123
    if ctx:condition("sounddone==1") then -- AKE.scr:124
        ctx:killSound("soundhandle") -- AKE.scr:125
    end -- AKE.scr:126
    do return ctx:exit("") end -- AKE.scr:128
end

script.labels["GoPosition1"] = function(ctx)
    -- AKE.scr:132
    ctx:self():setPos(3328.0, 1344.0, -480.0) -- AKE.scr:134
    ctx:self():faceDir(0, 0, 0, 0) -- AKE.scr:135
    do return ctx:exit("") end -- AKE.scr:137
end

script.labels["GoPosition2"] = function(ctx)
    -- AKE.scr:140
    ctx:self():setPos(3557, 1254, 3331) -- AKE.scr:142
    ctx:self():faceDir(-0.62, 0, -0.79, 0) -- AKE.scr:143
    do return ctx:exit("") end -- AKE.scr:145
end

script.labels["GoPosition3"] = function(ctx)
    -- AKE.scr:148
    ctx:self():setPos(-720, 1246, 2166) -- AKE.scr:151
    ctx:self():faceDir(-0.7, 0, -0.7, 0) -- AKE.scr:152
    do return ctx:exit("") end -- AKE.scr:154
end

script.labels["GoPosition4"] = function(ctx)
    -- AKE.scr:157
    ctx:self():setPos(-2176, 1246, 4711) -- AKE.scr:160
    ctx:self():faceDir(-0.54, 0, -0.84, 0) -- AKE.scr:161
    do return ctx:exit("") end -- AKE.scr:163
end

script.labels["SetupPosition"] = function(ctx)
    -- AKE.scr:167
    ctx:state().nPosition = (tonumber(ctx:state().nPosition) or 0) + 1 -- AKE.scr:172
    if ctx:condition("nPosition>4") then -- AKE.scr:174
        ctx:state().nPosition = 1 -- AKE.scr:175
    end -- AKE.scr:176
    if ctx:condition("nPosition==1") then -- AKE.scr:178
        do return mm9.gotoLabel(script, ctx, "GoPosition1") end -- AKE.scr:179
    end -- AKE.scr:180
    if ctx:condition("nPosition==2") then -- AKE.scr:182
        do return mm9.gotoLabel(script, ctx, "GoPosition2") end -- AKE.scr:183
    end -- AKE.scr:184
    if ctx:condition("nPosition==3") then -- AKE.scr:186
        do return mm9.gotoLabel(script, ctx, "GoPosition3") end -- AKE.scr:187
    end -- AKE.scr:188
    if ctx:condition("nPosition==4") then -- AKE.scr:190
        do return mm9.gotoLabel(script, ctx, "GoPosition4") end -- AKE.scr:191
    end -- AKE.scr:192
    do return ctx:exit("") end -- AKE.scr:194
end

script.labels["PostMiniSaveLoad"] = function(ctx)
    -- AKE.scr:197
    mm9.gosub(script, ctx, "SetupPosition") -- AKE.scr:200
    do return ctx:exit("") end -- AKE.scr:201
end

script.labels["Main"] = function(ctx)
    -- AKE.scr:204
    -- TraceOn ;delete me!!
    ctx:addTrigger("blabber", "Onblabber") -- AKE.scr:208
    ctx:addTrigger("Use", "OnUse") -- AKE.scr:209
    ctx:addTrigger("shutup", "onexit") -- AKE.scr:210
    -- CacheSound voices\cinema\socialism\Ake01.wav
    -- CacheSound voices\cinema\socialism\Ake02.wav
    -- CacheSound voices\cinema\socialism\Ake03.wav
    -- CacheSound voices\cinema\socialism\Ake04.wav
    -- CacheSound voices\cinema\socialism\Ake05.wav
    ctx:state().shutup = 0 -- AKE.scr:217
    ctx:state().sound = 0 -- AKE.scr:218
    ctx:state().g_ntemp = 1 -- AKE.scr:219
    if ctx:hasKey(114) then -- AKE.scr:220-221
        ctx:state().sound = 1 -- AKE.scr:222
    end -- AKE.scr:223
    mm9.gosub(script, ctx, "SetupPosition") -- AKE.scr:225
    ctx:onEvent("OnPostMiniSaveLoad", "PostMiniSaveLoad") -- AKE.scr:226
    ctx:addTrigger("GoPosition1", "GoPosition1") -- AKE.scr:227
    ctx:addTrigger("GoPosition2", "GoPosition2") -- AKE.scr:228
    ctx:addTrigger("GoPosition3", "GoPosition3") -- AKE.scr:229
    ctx:addTrigger("GoPosition4", "GoPosition4") -- AKE.scr:230
    do return ctx:exit("") end -- AKE.scr:232
end

return script
