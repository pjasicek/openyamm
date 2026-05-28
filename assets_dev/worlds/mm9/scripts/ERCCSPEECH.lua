-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ERCCSPEECH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- erccspeech.scr
-- By Timmy
-- handles ercc's rant.
-- is he out cold
script.labels["OnBlabber"] = function(ctx)
    -- ERCCSPEECH.scr:17
    if ctx:hasKey(113) then -- ERCCSPEECH.scr:19-20
        do return ctx:exit("") end -- ERCCSPEECH.scr:21
    end -- ERCCSPEECH.scr:22
    ctx:command("set", "unconscious, 1") -- ERCCSPEECH.scr:24
    ctx:giveKey(113) -- ERCCSPEECH.scr:25
    ctx:command("playanim", "ercc01a Anim2") -- ERCCSPEECH.scr:26
    -- gosub OnStart
    do return ctx:exit("") end -- ERCCSPEECH.scr:28
end

script.labels["Anim2"] = function(ctx)
    -- ERCCSPEECH.scr:31
    ctx:command("playanim", "ercc01b Anim3") -- ERCCSPEECH.scr:34
    do return ctx:exit("") end -- ERCCSPEECH.scr:35
end

script.labels["Anim3"] = function(ctx)
    -- ERCCSPEECH.scr:38
    ctx:command("playanim", "ercc01c Passout") -- ERCCSPEECH.scr:41
    do return ctx:exit("") end -- ERCCSPEECH.scr:42
end

script.labels["Passout"] = function(ctx)
    -- ERCCSPEECH.scr:45
    -- gosub OnPassOut
    ctx:command("playanim", "ercc02 DoNothing") -- ERCCSPEECH.scr:48
    do return ctx:exit("") end -- ERCCSPEECH.scr:49
end

script.labels["OnStart"] = function(ctx)
    -- ERCCSPEECH.scr:52
    ctx:command("playsound", "\\voices\\cinema\\ercc01.wav, DoNothing, 100, 512, FALSE, 100") -- ERCCSPEECH.scr:55
    do return ctx:exit("") end -- ERCCSPEECH.scr:56
end

script.labels["OnPassOut"] = function(ctx)
    -- ERCCSPEECH.scr:59
    ctx:command("playsound", "\\voices\\cinema\\ercc02.wav, DoNothing, 100, 512, FALSE, 100") -- ERCCSPEECH.scr:62
    do return ctx:exit("") end -- ERCCSPEECH.scr:63
end

script.labels["OnDone"] = function(ctx)
    -- ERCCSPEECH.scr:66
    do return ctx:exit("") end -- ERCCSPEECH.scr:69
end

script.labels["Init"] = function(ctx)
    -- ERCCSPEECH.scr:72
    ctx:command("loopanim", "sitting 0, donothing") -- ERCCSPEECH.scr:76
    do return ctx:exit("") end -- ERCCSPEECH.scr:77
end

script.labels["Main"] = function(ctx)
    -- ERCCSPEECH.scr:81
    -- TraceOn ;delete me!!
    ctx:addTrigger("Blabber", "OnBlabber") -- ERCCSPEECH.scr:85
    ctx:command("addmodelkey", "start OnStart") -- ERCCSPEECH.scr:86
    ctx:command("addmodelkey", "Passout OnPassOut") -- ERCCSPEECH.scr:87
    ctx:command("addmodelkey", "Done OnDone") -- ERCCSPEECH.scr:88
    ctx:command("wait", "1 .1 Init") -- ERCCSPEECH.scr:89
    ctx:command("onpoststartworld", "Init") -- ERCCSPEECH.scr:90
    ctx:command("onpostminisaveload", "Init") -- ERCCSPEECH.scr:91
    ctx:command("onpostsaveload", "Init") -- ERCCSPEECH.scr:92
    do return ctx:exit("") end -- ERCCSPEECH.scr:93
end

return script
