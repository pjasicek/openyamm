-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ALFRIGGFIGHT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Alfriggfight.scr
-- By Timmy
-- handles robert and douglas's argument
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
-- handler for second actor
script.labels["Onblabber"] = function(ctx)
    -- ALFRIGGFIGHT.scr:18
    -- starts with Hrolf speech
    if ctx:condition("sound==0") then -- ALFRIGGFIGHT.scr:23
        ctx:command("set", "sound, 1") -- ALFRIGGFIGHT.scr:24
        ctx:giveKey(115) -- ALFRIGGFIGHT.scr:25
        ctx:command("playsoundhandle", "voices\\cinema\\dwarvesandhumans\\01.wav, soundhandle, 240, FALSE, 100") -- ALFRIGGFIGHT.scr:26
        ctx:command("getsoundduration", ", soundhandle, sounddur") -- ALFRIGGFIGHT.scr:27
        ctx:command("wait", "1 sounddur, Alfrigg02") -- ALFRIGGFIGHT.scr:28
    end -- ALFRIGGFIGHT.scr:29
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:31
end

script.labels["Alfrigg02"] = function(ctx)
    -- ALFRIGGFIGHT.scr:35
    ctx:command("killsound", "soundhandle2") -- ALFRIGGFIGHT.scr:38
    ctx:command("playsoundhandle", "voices\\cinema\\dwarvesandhumans\\02.wav, soundhandle2, 240, FALSE, 100") -- ALFRIGGFIGHT.scr:39
    ctx:command("getsoundduration", ", soundhandle2, sounddur") -- ALFRIGGFIGHT.scr:40
    ctx:command("wait", "1 sounddur, Hrolf03") -- ALFRIGGFIGHT.scr:41
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:42
end

script.labels["Hrolf03"] = function(ctx)
    -- ALFRIGGFIGHT.scr:46
    ctx:command("killsound", "soundhandle") -- ALFRIGGFIGHT.scr:50
    ctx:command("playsoundhandle", "voices\\cinema\\dwarvesandhumans\\03.wav, soundhandle, 240, FALSE, 100") -- ALFRIGGFIGHT.scr:51
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- ALFRIGGFIGHT.scr:52
    ctx:command("subtract", "sounddur, .6") -- ALFRIGGFIGHT.scr:53
    ctx:command("wait", "1 sounddur, Alfrigg04") -- ALFRIGGFIGHT.scr:54
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:55
end

script.labels["Alfrigg04"] = function(ctx)
    -- ALFRIGGFIGHT.scr:59
    ctx:command("killsound", "soundhandle2") -- ALFRIGGFIGHT.scr:63
    ctx:command("playsoundhandle", "voices\\cinema\\dwarvesandhumans\\04c.wav, soundhandle2, 240, FALSE, 100") -- ALFRIGGFIGHT.scr:65
    ctx:command("getsoundduration", ", soundhandle2, sounddur") -- ALFRIGGFIGHT.scr:66
    ctx:command("subtract", "sounddur, .5") -- ALFRIGGFIGHT.scr:67
    ctx:command("wait", "1 sounddur, Hrolf05") -- ALFRIGGFIGHT.scr:68
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:69
end

script.labels["Hrolf05"] = function(ctx)
    -- ALFRIGGFIGHT.scr:73
    ctx:command("killsound", "soundhandle") -- ALFRIGGFIGHT.scr:76
    ctx:command("playsoundhandle", "voices\\cinema\\dwarvesandhumans\\05.wav, soundhandle, 240, FALSE, 100") -- ALFRIGGFIGHT.scr:77
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- ALFRIGGFIGHT.scr:78
    ctx:command("subtract", "sounddur, .5") -- ALFRIGGFIGHT.scr:79
    ctx:command("wait", "1 sounddur, Alfrigg06") -- ALFRIGGFIGHT.scr:80
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:81
end

script.labels["Alfrigg06"] = function(ctx)
    -- ALFRIGGFIGHT.scr:85
    ctx:command("killsound", "soundhandle2") -- ALFRIGGFIGHT.scr:88
    ctx:command("playsoundhandle", "voices\\cinema\\dwarvesandhumans\\06.wav, soundhandle2, 240, FALSE, 100") -- ALFRIGGFIGHT.scr:89
    ctx:command("getsoundduration", ", soundhandle2, sounddur") -- ALFRIGGFIGHT.scr:90
    ctx:command("wait", "1 sounddur, Hrolf07") -- ALFRIGGFIGHT.scr:91
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:92
end

script.labels["Hrolf07"] = function(ctx)
    -- ALFRIGGFIGHT.scr:97
    ctx:command("killsound", "soundhandle") -- ALFRIGGFIGHT.scr:100
    ctx:command("playsoundhandle", "voices\\cinema\\dwarvesandhumans\\07.wav, soundhandle, 240, FALSE, 100") -- ALFRIGGFIGHT.scr:101
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- ALFRIGGFIGHT.scr:102
    ctx:command("add", "sounddur, 3") -- ALFRIGGFIGHT.scr:103
    ctx:command("wait", "1 sounddur, Onexit") -- ALFRIGGFIGHT.scr:104
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:105
end

script.labels["OnUse"] = function(ctx)
    -- ALFRIGGFIGHT.scr:109
    -- if sound is playing, kill it
    if ctx:condition("sound==1") then -- ALFRIGGFIGHT.scr:114
        ctx:command("killsound", "soundhandle") -- ALFRIGGFIGHT.scr:115
        ctx:command("killsound", "soundhandle2") -- ALFRIGGFIGHT.scr:116
        ctx:command("set", "sound, 0") -- ALFRIGGFIGHT.scr:117
        ctx:command("set", "g_ntemp, 0") -- ALFRIGGFIGHT.scr:118
    end -- ALFRIGGFIGHT.scr:119
    -- start rude dialog
    ctx:doRude(110) -- ALFRIGGFIGHT.scr:121
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:122
end

script.labels["Onexit"] = function(ctx)
    -- ALFRIGGFIGHT.scr:126
    -- kill the sound if it's done
    ctx:command("issounddone", "soundhandle, sounddone") -- ALFRIGGFIGHT.scr:131
    if ctx:condition("sounddone==1") then -- ALFRIGGFIGHT.scr:132
        ctx:command("killsound", "soundhandle") -- ALFRIGGFIGHT.scr:133
        ctx:command("killsound", "soundhandle2") -- ALFRIGGFIGHT.scr:134
        -- commence with the fight!
        do return ctx:exit("") end -- ALFRIGGFIGHT.scr:137
    end -- ALFRIGGFIGHT.scr:138
    -- goto ondrink
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:140
end

script.labels["Main"] = function(ctx)
    -- ALFRIGGFIGHT.scr:144
    -- TraceOn ;delete me!!
    ctx:addTrigger("blabber", "Onblabber") -- ALFRIGGFIGHT.scr:148
    -- AddTrigger Use, OnUse ; ADD THIS BACK IN WHEN PROPS CAN REACT TO WAIT COMMAND
    ctx:command("set", "sound, 0") -- ALFRIGGFIGHT.scr:151
    ctx:command("set", "g_ntemp, 0") -- ALFRIGGFIGHT.scr:152
    if ctx:hasKey(115) then -- ALFRIGGFIGHT.scr:153-154
        ctx:command("set", "sound, 1") -- ALFRIGGFIGHT.scr:155
    end -- ALFRIGGFIGHT.scr:156
    do return ctx:exit("") end -- ALFRIGGFIGHT.scr:157
end

return script
