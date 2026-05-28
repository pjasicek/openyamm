-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOBANDDOUG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- bobanddoug.scr
-- By Timmy
-- handles robert and douglas's argument
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
script.labels["Onblabber"] = function(ctx)
    -- BOBANDDOUG.scr:18
    -- starts with doug's speech
    if ctx:condition("sound==0") then -- BOBANDDOUG.scr:23
        ctx:command("set", "sound, 1") -- BOBANDDOUG.scr:24
        ctx:giveKey(111) -- BOBANDDOUG.scr:25
        ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\01.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:26
        ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:27
        ctx:command("wait", "1 sounddur, Bob02") -- BOBANDDOUG.scr:28
    end -- BOBANDDOUG.scr:29
    do return ctx:exit("") end -- BOBANDDOUG.scr:31
end

script.labels["Bob02"] = function(ctx)
    -- BOBANDDOUG.scr:35
    ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:38
    ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\02.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:39
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:40
    ctx:command("wait", "1 sounddur, doug03") -- BOBANDDOUG.scr:41
    do return ctx:exit("") end -- BOBANDDOUG.scr:42
end

script.labels["Doug03"] = function(ctx)
    -- BOBANDDOUG.scr:46
    ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:50
    ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\03.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:51
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:52
    ctx:command("wait", "1 sounddur, Bob04") -- BOBANDDOUG.scr:53
    do return ctx:exit("") end -- BOBANDDOUG.scr:54
end

script.labels["Bob04"] = function(ctx)
    -- BOBANDDOUG.scr:58
    ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:62
    ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\04.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:63
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:64
    ctx:command("wait", "1 sounddur, doug05") -- BOBANDDOUG.scr:65
    do return ctx:exit("") end -- BOBANDDOUG.scr:66
end

script.labels["Doug05"] = function(ctx)
    -- BOBANDDOUG.scr:70
    ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:73
    ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\05.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:74
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:75
    ctx:command("wait", "1 sounddur, Bob06") -- BOBANDDOUG.scr:76
    do return ctx:exit("") end -- BOBANDDOUG.scr:77
end

script.labels["Bob06"] = function(ctx)
    -- BOBANDDOUG.scr:81
    ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:84
    ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\06.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:85
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:86
    ctx:command("wait", "1 sounddur, doug07") -- BOBANDDOUG.scr:87
    do return ctx:exit("") end -- BOBANDDOUG.scr:88
end

script.labels["Doug07"] = function(ctx)
    -- BOBANDDOUG.scr:92
    ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:95
    ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\07.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:96
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:97
    ctx:command("wait", "1 sounddur, Bob08") -- BOBANDDOUG.scr:98
    do return ctx:exit("") end -- BOBANDDOUG.scr:99
end

script.labels["Bob08"] = function(ctx)
    -- BOBANDDOUG.scr:103
    ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:106
    ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\08.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:107
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:108
    ctx:command("wait", "1 sounddur, doug09") -- BOBANDDOUG.scr:109
    do return ctx:exit("") end -- BOBANDDOUG.scr:110
end

script.labels["Doug09"] = function(ctx)
    -- BOBANDDOUG.scr:114
    ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:117
    ctx:command("playsoundhandle", "voices\\cinema\\bobanddoug\\09.wav, soundhandle, 240, FALSE, 100") -- BOBANDDOUG.scr:118
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- BOBANDDOUG.scr:119
    ctx:command("add", "sounddur, 3") -- BOBANDDOUG.scr:120
    ctx:command("wait", "1 sounddur, Onexit") -- BOBANDDOUG.scr:121
    do return ctx:exit("") end -- BOBANDDOUG.scr:122
end

script.labels["OnUse"] = function(ctx)
    -- BOBANDDOUG.scr:126
    -- if sound is playing, kill it
    if ctx:condition("sound==1") then -- BOBANDDOUG.scr:131
        ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:132
        ctx:command("set", "sound, 0") -- BOBANDDOUG.scr:133
        ctx:command("set", "g_ntemp, 0") -- BOBANDDOUG.scr:134
    end -- BOBANDDOUG.scr:135
    -- start rude dialog
    ctx:doRude(214) -- BOBANDDOUG.scr:137
    do return ctx:exit("") end -- BOBANDDOUG.scr:138
end

script.labels["Onexit"] = function(ctx)
    -- BOBANDDOUG.scr:142
    -- kill the sound if it's done
    ctx:command("issounddone", "soundhandle, sounddone") -- BOBANDDOUG.scr:147
    if ctx:condition("sounddone==1") then -- BOBANDDOUG.scr:148
        ctx:command("killsound", "soundhandle") -- BOBANDDOUG.scr:149
        do return ctx:exit("") end -- BOBANDDOUG.scr:150
    end -- BOBANDDOUG.scr:151
    -- goto ondrink
    do return ctx:exit("") end -- BOBANDDOUG.scr:153
end

script.labels["Main"] = function(ctx)
    -- BOBANDDOUG.scr:155
    -- TraceOn ;delete me!!
    ctx:addTrigger("blabber", "Onblabber") -- BOBANDDOUG.scr:159
    -- AddTrigger Use, OnUse ; ADD THIS BACK IN WHEN PROPS CAN REACT TO WAIT COMMAND
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\01.wav") -- BOBANDDOUG.scr:161
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\02.wav") -- BOBANDDOUG.scr:162
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\03.wav") -- BOBANDDOUG.scr:163
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\04.wav") -- BOBANDDOUG.scr:164
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\05.wav") -- BOBANDDOUG.scr:165
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\06.wav") -- BOBANDDOUG.scr:166
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\07.wav") -- BOBANDDOUG.scr:167
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\08.wav") -- BOBANDDOUG.scr:168
    ctx:command("cachesound", "voices\\cinema\\bobanddoug\\09.wav") -- BOBANDDOUG.scr:169
    ctx:command("set", "sound, 0") -- BOBANDDOUG.scr:170
    ctx:command("set", "g_ntemp, 0") -- BOBANDDOUG.scr:171
    if ctx:hasKey(111) then -- BOBANDDOUG.scr:172-173
        ctx:command("set", "sound, 1") -- BOBANDDOUG.scr:174
    end -- BOBANDDOUG.scr:175
    do return ctx:exit("") end -- BOBANDDOUG.scr:176
end

return script
