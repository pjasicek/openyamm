-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THJORAD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Thjorad.scr
-- By Timmy
-- gives the player Thjorad item 197
-- and the related key
-- Sven's RudeID is 3
script.labels["Onuse"] = function(ctx)
    -- THJORAD.scr:18
    if ctx:condition("On==False") then -- THJORAD.scr:21
        do return ctx:exit("") end -- THJORAD.scr:22
    end -- THJORAD.scr:23
    ctx:hasKey(2, "g_ntemp") -- THJORAD.scr:25
    if ctx:condition("g_ntemp==1") then -- THJORAD.scr:27
        ctx:hasKey(31, "keycheck") -- THJORAD.scr:28
        if ctx:condition("keycheck==0") then -- THJORAD.scr:29
            ctx:giveKey("", 31) -- THJORAD.scr:30
            ctx:giveItem(197) -- THJORAD.scr:31
            ctx:giveExp(1000) -- THJORAD.scr:32
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- THJORAD.scr:33
            ctx:command("getobjecthandle", "thjorad g_hobject") -- THJORAD.scr:34
            ctx:command("removeobject", "g_hobject") -- THJORAD.scr:35
            do return ctx:exit("") end -- THJORAD.scr:36
        end -- THJORAD.scr:37
    end -- THJORAD.scr:38
    ctx:hasKey(162, "keycheck") -- THJORAD.scr:41
    if ctx:condition("keycheck==0") then -- THJORAD.scr:42
        ctx:giveKey("", 162) -- THJORAD.scr:44
        ctx:command("set", "keydata, 162") -- THJORAD.scr:45
        ctx:giveItem(197) -- THJORAD.scr:46
        ctx:giveExp(1000) -- THJORAD.scr:47
        ctx:command("getobjecthandle", "thjorad g_hobject") -- THJORAD.scr:48
        ctx:command("removeobject", "g_hobject") -- THJORAD.scr:49
    end -- THJORAD.scr:50
    do return ctx:exit("") end -- THJORAD.scr:53
end

script.labels["Init"] = function(ctx)
    -- THJORAD.scr:57
    -- turn Thjorad on when player sets
    -- monks to hostile
    ctx:command("set", "On, False") -- THJORAD.scr:62
    ctx:command("getobjecthandle", "MONK_HOSTILITY, hMONK_HOSTILITY") -- THJORAD.scr:64
    if ctx:condition("hMONK_HOSTILITY!=0") then -- THJORAD.scr:65
        ctx:command("createobjectlink", "hMONK_HOSTILITY") -- THJORAD.scr:66
        ctx:command("onobjectlinkbroken", "OnTurnOn") -- THJORAD.scr:67
    end -- THJORAD.scr:68
    ctx:hasKey(31, "keycheck") -- THJORAD.scr:71
    if ctx:condition("g_ntemp==1") then -- THJORAD.scr:72
        ctx:command("getobjecthandle", "thjorad g_hobject") -- THJORAD.scr:73
        ctx:command("removeobject", "g_hobject") -- THJORAD.scr:74
        ctx:command("exitscript", "") -- THJORAD.scr:75
        do return ctx:exit("") end -- THJORAD.scr:76
    end -- THJORAD.scr:77
    ctx:hasKey(162, "keycheck") -- THJORAD.scr:79
    if ctx:condition("g_ntemp==1") then -- THJORAD.scr:80
        ctx:command("getobjecthandle", "thjorad g_hobject") -- THJORAD.scr:81
        ctx:command("removeobject", "g_hobject") -- THJORAD.scr:82
        ctx:command("exitscript", "") -- THJORAD.scr:83
        do return ctx:exit("") end -- THJORAD.scr:84
    end -- THJORAD.scr:85
    do return ctx:exit("") end -- THJORAD.scr:86
end

script.labels["OnTurnOn"] = function(ctx)
    -- THJORAD.scr:89
    ctx:command("set", "On, True") -- THJORAD.scr:92
    do return ctx:exit("") end -- THJORAD.scr:93
end

script.labels["Main"] = function(ctx)
    -- THJORAD.scr:96
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- THJORAD.scr:100
    ctx:addTrigger("TurnOn", "OnTurnOn") -- THJORAD.scr:101
    ctx:command("onpoststartworld", "Init") -- THJORAD.scr:105
    ctx:command("onpostminisaveload", "Init") -- THJORAD.scr:106
    ctx:command("onpostsaveload", "Init") -- THJORAD.scr:107
    ctx:command("wait", "1 .1 Init") -- THJORAD.scr:108
    do return ctx:exit("") end -- THJORAD.scr:110
end

return script
