-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RANDVERRETAINER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- forad.scr
-- By Timmy
-- handles forad's stuff
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
-- handler for second actor
-- flag variables
script.labels["Onblabber"] = function(ctx)
    -- RANDVERRETAINER.scr:22
    -- erccs blabber
    ctx:command("playsound", "voices\\NPC\\NPC_085.wav, Onexit, 100, 240, FALSE, 100") -- RANDVERRETAINER.scr:29
    do return ctx:exit("") end -- RANDVERRETAINER.scr:34
end

script.labels["Init"] = function(ctx)
    -- RANDVERRETAINER.scr:37
    -- LoopAnim Sitting 0 DoNothing
    ctx:command("getmyhandle", "g_hobject") -- RANDVERRETAINER.scr:41
    if not ctx:hasKey(453) then -- RANDVERRETAINER.scr:44-45
        ctx:command("setflag", "g_hobject, visible") -- RANDVERRETAINER.scr:48
        ctx:command("setflag", "g_hobject, solid") -- RANDVERRETAINER.scr:49
        ctx:command("setflag", "g_hobject, gravity") -- RANDVERRETAINER.scr:50
        ctx:command("loopanim", "sitting, 0 DoNothing") -- RANDVERRETAINER.scr:51
        do return ctx:exit("") end -- RANDVERRETAINER.scr:52
    else -- RANDVERRETAINER.scr:53
        ctx:command("clearflag", "g_hobject, visible") -- RANDVERRETAINER.scr:54
        ctx:command("clearflag", "g_hobject, solid") -- RANDVERRETAINER.scr:55
        ctx:command("clearflag", "g_hobject, gravity") -- RANDVERRETAINER.scr:56
        do return ctx:exit("") end -- RANDVERRETAINER.scr:57
    end -- RANDVERRETAINER.scr:58
    do return ctx:exit("") end -- RANDVERRETAINER.scr:60
end

script.labels["Onexit"] = function(ctx)
    -- RANDVERRETAINER.scr:65
    do return ctx:exit("") end -- RANDVERRETAINER.scr:68
end

script.labels["Main"] = function(ctx)
    -- RANDVERRETAINER.scr:71
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onblabber") -- RANDVERRETAINER.scr:75
    ctx:command("onpoststartworld", "Init") -- RANDVERRETAINER.scr:76
    ctx:command("onpostminisaveload", "Init") -- RANDVERRETAINER.scr:77
    ctx:command("onpostsaveload", "Init") -- RANDVERRETAINER.scr:78
    ctx:command("wait", "1 .1 Init") -- RANDVERRETAINER.scr:79
    do return ctx:exit("") end -- RANDVERRETAINER.scr:80
end

return script
