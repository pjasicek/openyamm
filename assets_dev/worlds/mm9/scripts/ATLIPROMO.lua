-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ATLIPROMO.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

-- Atlipromo.scr
-- By Timmy
-- handles the guard behavior!
-- Thorfinn's RudeID is 240
-- Atli's RudeID is 186
-- key 125 = player has got Atli
-- Key 126 = player has taken atli where he belongs
-- key 127 = player has completed the quest
script.labels["OnLeave"] = function(ctx)
    -- ATLIPROMO.scr:22
    if ctx:hasKey(376) then -- ATLIPROMO.scr:25-26
        if ctx:hasKey(125) then -- ATLIPROMO.scr:27-28
            ctx:giveKey(197) -- ATLIPROMO.scr:29
            ctx:command("getobjecthandle", "AtliMarker g_hobject") -- ATLIPROMO.scr:30
            ctx:command("walkto", "g_hobject 64 DoNothing") -- ATLIPROMO.scr:31
            do return ctx:exit("") end -- ATLIPROMO.scr:32
        end -- ATLIPROMO.scr:33
    end -- ATLIPROMO.scr:35
    do return ctx:exit("") end -- ATLIPROMO.scr:36
end

script.labels["Init"] = function(ctx)
    -- ATLIPROMO.scr:39
    ctx:command("onfoundplayer", "OnLeave") -- ATLIPROMO.scr:42
    if ctx:hasKey(197) then -- ATLIPROMO.scr:44-45
        ctx:command("getmyhandle", "G_hmyobject") -- ATLIPROMO.scr:46
        ctx:command("removeobject", "g_hmyobject") -- ATLIPROMO.scr:47
        do return ctx:exit("") end -- ATLIPROMO.scr:48
    end -- ATLIPROMO.scr:49
    do return ctx:exit("") end -- ATLIPROMO.scr:50
end

script.labels["Givekey"] = function(ctx)
    -- ATLIPROMO.scr:53
    ctx:giveKey(376) -- ATLIPROMO.scr:56
    do return ctx:exit("") end -- ATLIPROMO.scr:57
end

script.labels["TakeKey"] = function(ctx)
    -- ATLIPROMO.scr:60
    ctx:takeKey(376) -- ATLIPROMO.scr:63
    do return ctx:exit("") end -- ATLIPROMO.scr:64
end

script.labels["OnReturn"] = function(ctx)
    -- ATLIPROMO.scr:66
    ctx:command("getobjecthandle", "Atlimarker0 g_hobject") -- ATLIPROMO.scr:69
    ctx:command("walkto", "g_hobject 256 DoNothing") -- ATLIPROMO.scr:70
    do return ctx:exit("") end -- ATLIPROMO.scr:71
end

script.labels["Main"] = function(ctx)
    -- ATLIPROMO.scr:75
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Return", "OnReturn") -- ATLIPROMO.scr:81
    ctx:command("onpoststartworld", "Init") -- ATLIPROMO.scr:82
    ctx:command("onpostminisaveload", "Init") -- ATLIPROMO.scr:83
    ctx:command("onpostsaveload", "Init") -- ATLIPROMO.scr:84
    ctx:command("wait", "1 .5 Init") -- ATLIPROMO.scr:85
    ctx:command("@m", "2 : 45 givekey givekey") -- ATLIPROMO.scr:86
    ctx:command("@m", "3 : 15 takekey takekey") -- ATLIPROMO.scr:87
    do return ctx:exit("") end -- ATLIPROMO.scr:88
end

return script
