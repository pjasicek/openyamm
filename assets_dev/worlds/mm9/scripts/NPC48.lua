-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC48.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "basewander.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "followplayer.inc" }

-- NPC48.scr
-- By Timmy
-- handles Hat'lati's theivery stuff
script.labels["Onblabber"] = function(ctx)
    -- NPC48.scr:21
    -- erccs blabber
    ctx:command("stop", "") -- NPC48.scr:26
    mm9.gosub(script, ctx, "BasewanderStop") -- NPC48.scr:27
    ctx:getParam(0, "g_hobject") -- NPC48.scr:28
    ctx:command("faceobject", "g_hobject 200 DoNothing") -- NPC48.scr:29
    ctx:command("playsound", "voices\\NPC\\NPC_048.wav, DoNothing, 100, 240, FALSE, 100") -- NPC48.scr:31
    do return ctx:exit("") end -- NPC48.scr:36
end

script.labels["OnRude"] = function(ctx)
    -- NPC48.scr:40
    if ctx:hasKey(5009) then -- NPC48.scr:43-44
        do return ctx:exit("") end -- NPC48.scr:45
    end -- NPC48.scr:46
    if ctx:condition("bStealing==TRUE") then -- NPC48.scr:48
        mm9.gosub(script, ctx, "Basewanderstart") -- NPC48.scr:49
        do return ctx:exit("") end -- NPC48.scr:50
    end -- NPC48.scr:51
    if ctx:hasKey(154) then -- NPC48.scr:55-56
        ctx:command("stop", "") -- NPC48.scr:57
        mm9.gosub(script, ctx, "Followstart") -- NPC48.scr:58
        do return ctx:exit("") end -- NPC48.scr:59
    end -- NPC48.scr:60
    do return ctx:exit("") end -- NPC48.scr:61
end

script.labels["OnWander"] = function(ctx)
    -- NPC48.scr:64
    if ctx:hasKey(154) then -- NPC48.scr:66-67
        do return ctx:exit("") end -- NPC48.scr:68
    end -- NPC48.scr:69
    ctx:command("set", "bStealing, True") -- NPC48.scr:70
    mm9.gosub(script, ctx, "basewanderinit") -- NPC48.scr:71
    do return ctx:exit("") end -- NPC48.scr:72
end

script.labels["StopStealing"] = function(ctx)
    -- NPC48.scr:75
    ctx:command("set", "bStealing, false") -- NPC48.scr:78
    do return ctx:exit("") end -- NPC48.scr:79
end

script.labels["OnHome"] = function(ctx)
    -- NPC48.scr:82
    if ctx:condition("bStealing==TRUE") then -- NPC48.scr:85
        do return ctx:exit("") end -- NPC48.scr:86
    end -- NPC48.scr:87
    ctx:command("stop", "") -- NPC48.scr:89
    mm9.gosub(script, ctx, "BasewanderStop") -- NPC48.scr:90
    ctx:command("getobjecthandle", "HatlatiHome g_hobject") -- NPC48.scr:91
    ctx:command("walkto", "g_hobject 8 DoNothing") -- NPC48.scr:92
    do return ctx:exit("") end -- NPC48.scr:94
end

script.labels["OnJail"] = function(ctx)
    -- NPC48.scr:97
    mm9.gosub(script, ctx, "followstop") -- NPC48.scr:100
    ctx:command("getobjecthandle", "PrisonMarker g_hobject") -- NPC48.scr:101
    ctx:command("walkto", "g_hobject 8 close") -- NPC48.scr:102
    do return ctx:exit("") end -- NPC48.scr:103
end

script.labels["Close"] = function(ctx)
    -- NPC48.scr:106
    ctx:command("getobjecthandle", "Jaildoor g_hobject") -- NPC48.scr:109
    ctx:trigger("g_hobject", "close") -- NPC48.scr:110
    ctx:trigger("g_hobject", "lock") -- NPC48.scr:111
    ctx:command("getobjecthandle", "Chair9 g_hobject") -- NPC48.scr:112
    ctx:command("faceobject", "g_hobject 200 DoNothing") -- NPC48.scr:113
    ctx:command("stop", "") -- NPC48.scr:115
    mm9.gosub(script, ctx, "BaseWanderStop") -- NPC48.scr:116
    ctx:command("getmyhandle", "g_hmyobject") -- NPC48.scr:119
    ctx:command("setstat", "g_hmyobject WanderON false") -- NPC48.scr:120
    -- setparam 0 \voices\npc\NPC_048.wav
    -- runscript shopkeeper.scr
    -- exitscript
    do return ctx:exit("") end -- NPC48.scr:124
end

script.labels["Init"] = function(ctx)
    -- NPC48.scr:127
    if ctx:hasKey(154) then -- NPC48.scr:132-133
        ctx:command("stop", "") -- NPC48.scr:134
        ctx:command("getobjecthandle", "PrisonMarker g_hobject") -- NPC48.scr:135
        ctx:command("getpos", "g_hobject xPos Ypos Zpos") -- NPC48.scr:136
        ctx:command("getmyhandle", "g_hmyobject") -- NPC48.scr:137
        ctx:command("setpos", "g_hmyobject xPos yPos zPos") -- NPC48.scr:138
        ctx:command("getobjecthandle", "Chair9 g_hobject") -- NPC48.scr:139
        ctx:command("faceobject", "g_hobject 200 DoNothing") -- NPC48.scr:140
        ctx:giveKey(5009) -- NPC48.scr:141
        ctx:command("stop", "") -- NPC48.scr:143
        mm9.gosub(script, ctx, "BaseWanderStop") -- NPC48.scr:144
        ctx:command("getmyhandle", "g_hmyobject") -- NPC48.scr:146
        ctx:command("setstat", "g_hmyobject WanderON false") -- NPC48.scr:147
        -- setparam 0 \voices\npc\NPC_048.wav
        -- runscript shopkeeper.scr
        -- exitscript
        do return ctx:exit("") end -- NPC48.scr:151
    end -- NPC48.scr:152
    do return ctx:exit("") end -- NPC48.scr:154
end

script.labels["Main"] = function(ctx)
    -- NPC48.scr:156
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onblabber") -- NPC48.scr:160
    ctx:addTrigger("Start", "OnWander") -- NPC48.scr:161
    ctx:addTrigger("GoHome", "OnHome") -- NPC48.scr:162
    ctx:addTrigger("GotoJail", "OnJail") -- NPC48.scr:163
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC48.scr:164
    ctx:command("onpoststartworld", "Init") -- NPC48.scr:165
    ctx:command("onpostminisaveload", "Init") -- NPC48.scr:166
    ctx:command("onpostsaveload", "Init") -- NPC48.scr:167
    ctx:command("wait", "1 .1 Init") -- NPC48.scr:168
    ctx:command("@m", "12 : 00 OnWander OnWander") -- NPC48.scr:169
    ctx:command("@m", "4 : 00 StopStealing StopStealing") -- NPC48.scr:170
    do return ctx:exit("") end -- NPC48.scr:172
end

return script
