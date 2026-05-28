-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NJAMTAUNT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- NjamTaunt.scr
-- By Timmy
-- Handle's Njam's Taunting Stuff for Taunt Cutscene
-- flag variables
script.labels["OnStart"] = function(ctx)
    -- NJAMTAUNT.scr:17
    ctx:command("getobjecthandle", "TauntMarker g_hobject") -- NJAMTAUNT.scr:20
    ctx:command("walkto", "g_hobject 2 OnArrive") -- NJAMTAUNT.scr:21
    do return ctx:exit("") end -- NJAMTAUNT.scr:22
end

script.labels["OnArrive"] = function(ctx)
    -- NJAMTAUNT.scr:25
    ctx:command("getobjecthandle", "TauntCamB g_hobject") -- NJAMTAUNT.scr:28
    ctx:command("faceobject", "g_hobject 10 DoNothing") -- NJAMTAUNT.scr:29
    ctx:command("getobjecthandle", "TauntMan g_hobject") -- NJAMTAUNT.scr:31
    ctx:trigger("g_hobject", "Arrive") -- NJAMTAUNT.scr:32
    ctx:command("wait", "1 1 OnText1") -- NJAMTAUNT.scr:33
    do return ctx:exit("") end -- NJAMTAUNT.scr:34
end

script.labels["OnText1"] = function(ctx)
    -- NJAMTAUNT.scr:38
    ctx:command("rollovertext", "15, 0") -- NJAMTAUNT.scr:41
    ctx:command("wait", "1 4 OnText2") -- NJAMTAUNT.scr:42
    do return ctx:exit("") end -- NJAMTAUNT.scr:45
end

script.labels["OnText2"] = function(ctx)
    -- NJAMTAUNT.scr:49
    ctx:command("rollovertext", "16, 0") -- NJAMTAUNT.scr:52
    ctx:command("wait", "1 4 OnVanish") -- NJAMTAUNT.scr:53
    do return ctx:exit("") end -- NJAMTAUNT.scr:54
end

script.labels["OnVanish"] = function(ctx)
    -- NJAMTAUNT.scr:58
    ctx:command("getobjecthandle", "TauntMan g_hobject") -- NJAMTAUNT.scr:62
    ctx:trigger("g_hobject", "VanishStart") -- NJAMTAUNT.scr:63
    ctx:command("getmyhandle", "g_hmyobject") -- NJAMTAUNT.scr:65
    -- play vanish effect here
    ctx:command("doclientfx", "g_hmyObject,GreaterDemon") -- NJAMTAUNT.scr:68
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAMTAUNT.scr:69
    ctx:command("wait", "1 1 Vanish2b") -- NJAMTAUNT.scr:70
    do return ctx:exit("") end -- NJAMTAUNT.scr:71
end

script.labels["Vanish2b"] = function(ctx)
    -- NJAMTAUNT.scr:74
    ctx:command("clearflag", "g_hmyobject visible") -- NJAMTAUNT.scr:77
    ctx:command("playsound", "\\Sounds\\magic\\teleport.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAMTAUNT.scr:78
    ctx:command("wait", "1 1 Vanish2c") -- NJAMTAUNT.scr:79
    do return ctx:exit("") end -- NJAMTAUNT.scr:80
end

script.labels["Vanish2c"] = function(ctx)
    -- NJAMTAUNT.scr:84
    ctx:command("getobjecthandle", "TauntMan g_hobject") -- NJAMTAUNT.scr:86
    ctx:trigger("g_hobject", "VanishDone") -- NJAMTAUNT.scr:87
    ctx:command("removeobject", "g_hmyobject") -- NJAMTAUNT.scr:89
    do return ctx:exit("") end -- NJAMTAUNT.scr:90
end

script.labels["Init"] = function(ctx)
    -- NJAMTAUNT.scr:94
    if ctx:hasKey(497) then -- NJAMTAUNT.scr:97-98
        ctx:command("getmyhandle", "g_hmyobject") -- NJAMTAUNT.scr:99
        ctx:command("removeobject", "g_hmyobject") -- NJAMTAUNT.scr:100
    end -- NJAMTAUNT.scr:101
    do return ctx:exit("") end -- NJAMTAUNT.scr:103
end

script.labels["Main"] = function(ctx)
    -- NJAMTAUNT.scr:107
    -- TraceOn ;delete me!!
    ctx:addTrigger("Start", "OnStart") -- NJAMTAUNT.scr:111
    ctx:command("onpoststartworld", "Init") -- NJAMTAUNT.scr:112
    ctx:command("onpostminisaveload", "Init") -- NJAMTAUNT.scr:113
    ctx:command("onpostsaveload", "Init") -- NJAMTAUNT.scr:114
    ctx:command("wait", "1 .1 Init") -- NJAMTAUNT.scr:115
    do return ctx:exit("") end -- NJAMTAUNT.scr:116
end

return script
