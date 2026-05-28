-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LUDWIGSMANUSCRIPT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Ludwigsmanuscript.scr
-- By Timmy
-- gives the player ludwig's manuscript
-- and the related key
-- Ludwig's RudeID is 47
script.labels["Onuse"] = function(ctx)
    -- LUDWIGSMANUSCRIPT.scr:15
    -- checks to see if player talked to Ludwig first
    ctx:hasKey(14, "g_ntemp") -- LUDWIGSMANUSCRIPT.scr:19
    if ctx:condition("g_ntemp==1") then -- LUDWIGSMANUSCRIPT.scr:21
        -- checks to see if player has picked up the mauscript already
        ctx:hasKey(16, "keycheck") -- LUDWIGSMANUSCRIPT.scr:23
        if ctx:condition("keycheck==0") then -- LUDWIGSMANUSCRIPT.scr:24
            -- gives player finished quest key
            ctx:giveKey("", 16) -- LUDWIGSMANUSCRIPT.scr:26
            ctx:command("set", "keydata, 16") -- LUDWIGSMANUSCRIPT.scr:27
            ctx:giveItem(248) -- LUDWIGSMANUSCRIPT.scr:28
            ctx:command("getmyhandle", "g_hmyobject") -- LUDWIGSMANUSCRIPT.scr:29
            ctx:command("removeobject", "g_hmyobject") -- LUDWIGSMANUSCRIPT.scr:30
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- LUDWIGSMANUSCRIPT.scr:31
            do return ctx:exit("") end -- LUDWIGSMANUSCRIPT.scr:32
        end -- LUDWIGSMANUSCRIPT.scr:33
    end -- LUDWIGSMANUSCRIPT.scr:34
    ctx:hasKey(110, "keycheck") -- LUDWIGSMANUSCRIPT.scr:35
    if ctx:condition("keycheck==0") then -- LUDWIGSMANUSCRIPT.scr:36
        ctx:giveKey("", 110) -- LUDWIGSMANUSCRIPT.scr:38
        ctx:command("set", "keydata, 110") -- LUDWIGSMANUSCRIPT.scr:39
        ctx:giveItem(248) -- LUDWIGSMANUSCRIPT.scr:40
        ctx:command("getmyhandle", "g_hmyobject") -- LUDWIGSMANUSCRIPT.scr:41
        ctx:command("removeobject", "g_hmyobject") -- LUDWIGSMANUSCRIPT.scr:42
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- LUDWIGSMANUSCRIPT.scr:43
    end -- LUDWIGSMANUSCRIPT.scr:44
    do return ctx:exit("") end -- LUDWIGSMANUSCRIPT.scr:45
end

script.labels["Init"] = function(ctx)
    -- LUDWIGSMANUSCRIPT.scr:49
    if ctx:hasKey(16) then -- LUDWIGSMANUSCRIPT.scr:52-53
        mm9.gosub(script, ctx, "delete") -- LUDWIGSMANUSCRIPT.scr:54
    end -- LUDWIGSMANUSCRIPT.scr:55
    if ctx:hasKey(110) then -- LUDWIGSMANUSCRIPT.scr:57-58
        mm9.gosub(script, ctx, "delete") -- LUDWIGSMANUSCRIPT.scr:59
    end -- LUDWIGSMANUSCRIPT.scr:60
    do return ctx:exit("") end -- LUDWIGSMANUSCRIPT.scr:62
end

script.labels["Delete"] = function(ctx)
    -- LUDWIGSMANUSCRIPT.scr:66
    ctx:command("getmyhandle", "g_hmyobject") -- LUDWIGSMANUSCRIPT.scr:69
    ctx:command("removeobject", "g_hmyobject") -- LUDWIGSMANUSCRIPT.scr:70
    do return ctx:exit("") end -- LUDWIGSMANUSCRIPT.scr:71
end

script.labels["Main"] = function(ctx)
    -- LUDWIGSMANUSCRIPT.scr:74
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- LUDWIGSMANUSCRIPT.scr:78
    ctx:command("onpoststartworld", "Init") -- LUDWIGSMANUSCRIPT.scr:79
    ctx:command("onpostminisaveload", "Init") -- LUDWIGSMANUSCRIPT.scr:80
    ctx:command("onpostsaveload", "Init") -- LUDWIGSMANUSCRIPT.scr:81
    ctx:command("wait", "1 .1 Init") -- LUDWIGSMANUSCRIPT.scr:82
    do return ctx:exit("") end -- LUDWIGSMANUSCRIPT.scr:83
end

return script
