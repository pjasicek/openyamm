-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AKERETAINER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Akeretainer.scr
-- By Timmy
-- handles ake the righteous's stuff
-- flag variables
script.labels["Onblabber"] = function(ctx)
    -- AKERETAINER.scr:17
    ctx:command("playsound", "voices\\NPC\\NPC_086.wav, DoNothing, 100, 24000, FALSE, 100") -- AKERETAINER.scr:20
    do return ctx:exit("") end -- AKERETAINER.scr:21
end

script.labels["Init"] = function(ctx)
    -- AKERETAINER.scr:25
    ctx:hasKey(454, "g_ntemp") -- AKERETAINER.scr:27
    ctx:command("getmyhandle", "g_hobject") -- AKERETAINER.scr:29
    if ctx:condition("g_ntemp==FALSE") then -- AKERETAINER.scr:32
        ctx:command("setflag", "g_hobject, visible") -- AKERETAINER.scr:33
        ctx:command("setflag", "g_hobject, solid") -- AKERETAINER.scr:34
        ctx:command("setflag", "g_hobject, gravity") -- AKERETAINER.scr:35
        ctx:command("loopanim", "sitting 0, DoNothing") -- AKERETAINER.scr:36
    else -- AKERETAINER.scr:37
        ctx:command("clearflag", "g_hobject, visible") -- AKERETAINER.scr:38
        ctx:command("clearflag", "g_hobject, solid") -- AKERETAINER.scr:39
        ctx:command("clearflag", "g_hobject, gravity") -- AKERETAINER.scr:40
        do return ctx:exit("") end -- AKERETAINER.scr:41
    end -- AKERETAINER.scr:42
    do return ctx:exit("") end -- AKERETAINER.scr:44
end

script.labels["Main"] = function(ctx)
    -- AKERETAINER.scr:48
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onblabber") -- AKERETAINER.scr:52
    ctx:command("onpoststartworld", "Init") -- AKERETAINER.scr:53
    ctx:command("onpostminisaveload", "Init") -- AKERETAINER.scr:54
    ctx:command("onpostsaveload", "Init") -- AKERETAINER.scr:55
    ctx:command("wait", "1 .1 Init") -- AKERETAINER.scr:56
    do return ctx:exit("") end -- AKERETAINER.scr:57
end

return script
