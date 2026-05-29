-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NEWGAME.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Newgame.scr
-- By Timmy
-- handles scandlan's rant about his new game.
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
-- handler for second actor
script.labels["Onblabber"] = function(ctx)
    -- NEWGAME.scr:19
    -- starts with scandlan's speech
    if ctx:condition("sound==0") then -- NEWGAME.scr:24
        ctx:state().sound = 1 -- NEWGAME.scr:25
        ctx:giveKey(112) -- NEWGAME.scr:26
        ctx:playSoundHandle("voices\\cinema\\newgame\\01.wav", "soundhandle", 240, "FALSE", 100) -- NEWGAME.scr:27
        ctx:getSoundDuration("", "soundhandle", "sounddur") -- NEWGAME.scr:28
        ctx:sub("sounddur", .13) -- NEWGAME.scr:29
        ctx:wait(1, "sounddur", "Broccan02") -- NEWGAME.scr:30
    end -- NEWGAME.scr:31
    do return ctx:exit("") end -- NEWGAME.scr:33
end

script.labels["Broccan02"] = function(ctx)
    -- NEWGAME.scr:37
    -- KillSound soundhandle
    ctx:playSoundHandle("voices\\cinema\\newgame\\02.wav", "soundhandle2", 240, "FALSE", 100) -- NEWGAME.scr:41
    ctx:getSoundDuration("", "soundhandle2", "sounddur") -- NEWGAME.scr:42
    ctx:sub("sounddur", .3) -- NEWGAME.scr:43
    ctx:wait(1, "sounddur", "Scandlan03") -- NEWGAME.scr:44
    do return ctx:exit("") end -- NEWGAME.scr:45
end

script.labels["Scandlan03"] = function(ctx)
    -- NEWGAME.scr:49
    ctx:killSound("soundhandle") -- NEWGAME.scr:53
    ctx:playSoundHandle("voices\\cinema\\newgame\\03.wav", "soundhandle", 240, "FALSE", 100) -- NEWGAME.scr:54
    ctx:getSoundDuration("", "soundhandle", "sounddur") -- NEWGAME.scr:55
    ctx:sub("sounddur", .12) -- NEWGAME.scr:56
    ctx:wait(1, "sounddur", "Broccan04") -- NEWGAME.scr:57
    do return ctx:exit("") end -- NEWGAME.scr:58
end

script.labels["Broccan04"] = function(ctx)
    -- NEWGAME.scr:62
    ctx:killSound("soundhandle2") -- NEWGAME.scr:66
    ctx:playSoundHandle("voices\\cinema\\newgame\\04.wav", "soundhandle2", 240, "FALSE", 100) -- NEWGAME.scr:67
    ctx:getSoundDuration("", "soundhandle2", "sounddur") -- NEWGAME.scr:68
    ctx:sub("sounddur", .6) -- NEWGAME.scr:69
    ctx:wait(1, "sounddur", "Scandlan05") -- NEWGAME.scr:70
    do return ctx:exit("") end -- NEWGAME.scr:71
end

script.labels["Scandlan05"] = function(ctx)
    -- NEWGAME.scr:75
    ctx:killSound("soundhandle") -- NEWGAME.scr:78
    ctx:playSoundHandle("voices\\cinema\\newgame\\05.wav", "soundhandle", 240, "FALSE", 100) -- NEWGAME.scr:79
    ctx:getSoundDuration("", "soundhandle", "sounddur") -- NEWGAME.scr:80
    ctx:sub("sounddur", .7) -- NEWGAME.scr:81
    ctx:wait(1, "sounddur", "Broccan06") -- NEWGAME.scr:82
    do return ctx:exit("") end -- NEWGAME.scr:83
end

script.labels["Broccan06"] = function(ctx)
    -- NEWGAME.scr:87
    ctx:killSound("soundhandle2") -- NEWGAME.scr:90
    ctx:playSoundHandle("voices\\cinema\\newgame\\06.wav", "soundhandle2", 240, "FALSE", 100) -- NEWGAME.scr:91
    ctx:getSoundDuration("", "soundhandle2", "sounddur") -- NEWGAME.scr:92
    ctx:sub("sounddur", .13) -- NEWGAME.scr:93
    ctx:wait(1, "sounddur", "Scandlan07") -- NEWGAME.scr:94
    do return ctx:exit("") end -- NEWGAME.scr:95
end

script.labels["Scandlan07"] = function(ctx)
    -- NEWGAME.scr:99
    ctx:killSound("soundhandle") -- NEWGAME.scr:102
    ctx:playSoundHandle("voices\\cinema\\newgame\\07.wav", "soundhandle", 240, "FALSE", 100) -- NEWGAME.scr:103
    ctx:getSoundDuration("", "soundhandle", "sounddur") -- NEWGAME.scr:104
    ctx:wait(1, "sounddur", "Broccan08") -- NEWGAME.scr:105
    do return ctx:exit("") end -- NEWGAME.scr:106
end

script.labels["Broccan08"] = function(ctx)
    -- NEWGAME.scr:110
    ctx:killSound("soundhandle2") -- NEWGAME.scr:113
    ctx:playSoundHandle("voices\\cinema\\newgame\\08.wav", "soundhandle2", 240, "FALSE", 100) -- NEWGAME.scr:114
    ctx:getSoundDuration("", "soundhandle2", "sounddur") -- NEWGAME.scr:115
    ctx:sub("sounddur", .6) -- NEWGAME.scr:116
    ctx:wait(1, "sounddur", "Scandlan09") -- NEWGAME.scr:117
    do return ctx:exit("") end -- NEWGAME.scr:118
end

script.labels["Scandlan09"] = function(ctx)
    -- NEWGAME.scr:122
    ctx:killSound("soundhandle") -- NEWGAME.scr:125
    ctx:playSoundHandle("voices\\cinema\\newgame\\09.wav", "soundhandle", 240, "FALSE", 100) -- NEWGAME.scr:126
    ctx:getSoundDuration("", "soundhandle", "sounddur") -- NEWGAME.scr:127
    ctx:wait(1, "sounddur", "Broccan10") -- NEWGAME.scr:129
    do return ctx:exit("") end -- NEWGAME.scr:130
end

script.labels["Broccan10"] = function(ctx)
    -- NEWGAME.scr:133
    ctx:killSound("soundhandle2") -- NEWGAME.scr:136
    ctx:playSoundHandle("voices\\cinema\\newgame\\10.wav", "soundhandle2", 240, "FALSE", 100) -- NEWGAME.scr:137
    ctx:getSoundDuration("", "soundhandle2", "sounddur") -- NEWGAME.scr:138
    ctx:sub("sounddur", .7) -- NEWGAME.scr:139
    ctx:wait(1, "sounddur", "Scandlan11") -- NEWGAME.scr:140
    do return ctx:exit("") end -- NEWGAME.scr:141
end

script.labels["Scandlan11"] = function(ctx)
    -- NEWGAME.scr:144
    ctx:killSound("soundhandle") -- NEWGAME.scr:147
    ctx:playSoundHandle("voices\\cinema\\newgame\\11.wav", "soundhandle", 240, "FALSE", 100) -- NEWGAME.scr:148
    ctx:getSoundDuration("", "soundhandle", "sounddur") -- NEWGAME.scr:149
    ctx:wait(1, "sounddur", "Scandlan12") -- NEWGAME.scr:150
    do return ctx:exit("") end -- NEWGAME.scr:151
end

script.labels["Scandlan12"] = function(ctx)
    -- NEWGAME.scr:154
    ctx:killSound("soundhandle") -- NEWGAME.scr:157
    ctx:playSoundHandle("voices\\cinema\\newgame\\12.wav", "soundhandle", 240, "FALSE", 100) -- NEWGAME.scr:158
    ctx:getSoundDuration("", "soundhandle", "sounddur") -- NEWGAME.scr:159
    ctx:state().sounddur = (tonumber(ctx:state().sounddur) or 0) + 3 -- NEWGAME.scr:160
    ctx:wait(1, "sounddur", "Onexit") -- NEWGAME.scr:161
    do return ctx:exit("") end -- NEWGAME.scr:162
end

script.labels["OnUse"] = function(ctx)
    -- NEWGAME.scr:165
    -- if sound is playing, kill it
    if ctx:condition("sound==1") then -- NEWGAME.scr:170
        ctx:killSound("soundhandle") -- NEWGAME.scr:171
        ctx:killSound("soundhandle2") -- NEWGAME.scr:172
        ctx:state().sound = 0 -- NEWGAME.scr:173
        ctx:state().g_ntemp = 0 -- NEWGAME.scr:174
    end -- NEWGAME.scr:175
    -- start rude dialog
    ctx:doRude(214) -- NEWGAME.scr:177
    do return ctx:exit("") end -- NEWGAME.scr:178
end

script.labels["Onexit"] = function(ctx)
    -- NEWGAME.scr:182
    -- kill the sound if it's done
    ctx:isSoundDone("soundhandle", "sounddone") -- NEWGAME.scr:187
    if ctx:condition("sounddone==1") then -- NEWGAME.scr:188
        ctx:killSound("soundhandle") -- NEWGAME.scr:189
    end -- NEWGAME.scr:190
    ctx:isSoundDone("soundhandle2", "sounddone") -- NEWGAME.scr:191
    if ctx:condition("sounddone==1") then -- NEWGAME.scr:192
        ctx:killSound("soundhandle2") -- NEWGAME.scr:193
        do return ctx:exit("") end -- NEWGAME.scr:194
    end -- NEWGAME.scr:195
    -- goto ondrink
    do return ctx:exit("") end -- NEWGAME.scr:197
end

script.labels["Main"] = function(ctx)
    -- NEWGAME.scr:199
    -- TraceOn ;delete me!!
    ctx:addTrigger("blabber", "Onblabber") -- NEWGAME.scr:203
    -- AddTrigger Use, OnUse ; ADD THIS BACK IN WHEN PROPS CAN REACT TO WAIT COMMAND
    ctx:cacheSound("voices\\cinema\\newgame\\01.wav") -- NEWGAME.scr:205
    ctx:cacheSound("voices\\cinema\\newgame\\02.wav") -- NEWGAME.scr:206
    ctx:cacheSound("voices\\cinema\\newgame\\03.wav") -- NEWGAME.scr:207
    ctx:cacheSound("voices\\cinema\\newgame\\04.wav") -- NEWGAME.scr:208
    ctx:cacheSound("voices\\cinema\\newgame\\05.wav") -- NEWGAME.scr:209
    ctx:cacheSound("voices\\cinema\\newgame\\06.wav") -- NEWGAME.scr:210
    ctx:cacheSound("voices\\cinema\\newgame\\07.wav") -- NEWGAME.scr:211
    ctx:cacheSound("voices\\cinema\\newgame\\08.wav") -- NEWGAME.scr:212
    ctx:cacheSound("voices\\cinema\\newgame\\09.wav") -- NEWGAME.scr:213
    ctx:cacheSound("voices\\cinema\\newgame\\10.wav") -- NEWGAME.scr:214
    ctx:cacheSound("voices\\cinema\\newgame\\11.wav") -- NEWGAME.scr:215
    ctx:cacheSound("voices\\cinema\\newgame\\12.wav") -- NEWGAME.scr:216
    ctx:state().sound = 0 -- NEWGAME.scr:217
    ctx:state().g_ntemp = 0 -- NEWGAME.scr:218
    if ctx:hasKey(112) then -- NEWGAME.scr:219-220
        ctx:state().sound = 1 -- NEWGAME.scr:221
    end -- NEWGAME.scr:222
    do return ctx:exit("") end -- NEWGAME.scr:223
end

return script
