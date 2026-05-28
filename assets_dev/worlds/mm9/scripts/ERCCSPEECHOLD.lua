-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ERCCSPEECHOLD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- erccspeech.scr
-- By Timmy
-- handles ercc's rant.
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
-- handler for second actor
-- is he out cold
script.labels["Onblabber"] = function(ctx)
    -- ERCCSPEECHOLD.scr:19
    -- erccs blabber
    ctx:command("set", "unconscious, 1") -- ERCCSPEECHOLD.scr:23
    if ctx:condition("sound==0") then -- ERCCSPEECHOLD.scr:24
        ctx:command("loopanim", "Conv2, 0 Donothing") -- ERCCSPEECHOLD.scr:25
        ctx:command("set", "sound, 1") -- ERCCSPEECHOLD.scr:26
        ctx:giveKey(113) -- ERCCSPEECHOLD.scr:27
        ctx:command("playsoundhandle", "voices\\cinema\\ercc01.wav, soundhandle, 240, FALSE, 100") -- ERCCSPEECHOLD.scr:28
        ctx:command("getsoundduration", ", soundhandle, sounddur") -- ERCCSPEECHOLD.scr:29
        ctx:command("wait", "1 sounddur, Ercc2") -- ERCCSPEECHOLD.scr:30
    end -- ERCCSPEECHOLD.scr:31
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:33
end

script.labels["ercc2"] = function(ctx)
    -- ERCCSPEECHOLD.scr:38
    ctx:command("killsound", "soundhandle") -- ERCCSPEECHOLD.scr:41
    ctx:command("playanim", "Fidget4, Passout") -- ERCCSPEECHOLD.scr:42
    ctx:command("playsoundhandle", "voices\\cinema\\ercc02.wav, soundhandle, 240, FALSE, 100") -- ERCCSPEECHOLD.scr:43
    ctx:command("getsoundduration", ", soundhandle, sounddur") -- ERCCSPEECHOLD.scr:44
    ctx:command("wait", "1 sounddur, Onexit") -- ERCCSPEECHOLD.scr:45
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:46
end

script.labels["Passout"] = function(ctx)
    -- ERCCSPEECHOLD.scr:49
    ctx:command("loopanim", "listen 0, Donothing") -- ERCCSPEECHOLD.scr:52
    ctx:command("wait", "1 3, passout2") -- ERCCSPEECHOLD.scr:53
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:54
end

script.labels["Passout2"] = function(ctx)
    -- ERCCSPEECHOLD.scr:56
    ctx:command("playanim", "Passout, Donothing2") -- ERCCSPEECHOLD.scr:59
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:61
end

script.labels["OnUse"] = function(ctx)
    -- ERCCSPEECHOLD.scr:64
    -- if sound is playing, kill it
    if ctx:condition("unconscious==1") then -- ERCCSPEECHOLD.scr:69
        do return ctx:exit("") end -- ERCCSPEECHOLD.scr:70
    end -- ERCCSPEECHOLD.scr:71
    -- start rude dialog
    ctx:doRude(106) -- ERCCSPEECHOLD.scr:73
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:74
end

script.labels["Donothing2"] = function(ctx)
    -- ERCCSPEECHOLD.scr:77
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:81
end

script.labels["Donothing"] = function(ctx)
    -- ERCCSPEECHOLD.scr:84
    ctx:command("loopanim", "conv2 0, Donothing") -- ERCCSPEECHOLD.scr:87
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:88
end

script.labels["Init"] = function(ctx)
    -- ERCCSPEECHOLD.scr:91
    ctx:command("loopanim", "sitting 0, donothing2") -- ERCCSPEECHOLD.scr:94
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:95
end

script.labels["Onexit"] = function(ctx)
    -- ERCCSPEECHOLD.scr:100
    -- kill the sound if it's done
    ctx:command("issounddone", "soundhandle, sounddone") -- ERCCSPEECHOLD.scr:105
    if ctx:condition("sounddone==1") then -- ERCCSPEECHOLD.scr:106
        ctx:command("killsound", "soundhandle") -- ERCCSPEECHOLD.scr:107
        ctx:command("playanim", "Passout, Donothing") -- ERCCSPEECHOLD.scr:108
    end -- ERCCSPEECHOLD.scr:109
    -- goto ondrink
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:111
end

script.labels["Main"] = function(ctx)
    -- ERCCSPEECHOLD.scr:113
    -- TraceOn ;delete me!!
    ctx:command("addmodelkey", "start OnStart") -- ERCCSPEECHOLD.scr:117
    ctx:command("addmodelkey", "Passout ONPassOut") -- ERCCSPEECHOLD.scr:118
    ctx:command("addmodelkey", "Done OnDone") -- ERCCSPEECHOLD.scr:119
    ctx:command("set", "sound, 0") -- ERCCSPEECHOLD.scr:120
    ctx:command("set", "g_ntemp, 0") -- ERCCSPEECHOLD.scr:121
    if ctx:hasKey(113) then -- ERCCSPEECHOLD.scr:122-123
        ctx:command("set", "sound, 1") -- ERCCSPEECHOLD.scr:124
    end -- ERCCSPEECHOLD.scr:125
    ctx:command("onpoststartworld", "Init") -- ERCCSPEECHOLD.scr:126
    ctx:command("onpostminisaveload", "Init") -- ERCCSPEECHOLD.scr:127
    do return ctx:exit("") end -- ERCCSPEECHOLD.scr:128
end

return script
