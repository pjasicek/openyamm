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
    ctx:self():stop() -- NPC48.scr:26
    mm9.gosub(script, ctx, "BasewanderStop") -- NPC48.scr:27
    ctx:getParam(0, "g_hobject") -- NPC48.scr:28
    ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- NPC48.scr:29
    ctx:playSound("voices\\NPC\\NPC_048.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC48.scr:31
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
        ctx:self():stop() -- NPC48.scr:57
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
    ctx:state().bStealing = true -- NPC48.scr:70
    mm9.gosub(script, ctx, "basewanderinit") -- NPC48.scr:71
    do return ctx:exit("") end -- NPC48.scr:72
end

script.labels["StopStealing"] = function(ctx)
    -- NPC48.scr:75
    ctx:state().bStealing = false -- NPC48.scr:78
    do return ctx:exit("") end -- NPC48.scr:79
end

script.labels["OnHome"] = function(ctx)
    -- NPC48.scr:82
    if ctx:condition("bStealing==TRUE") then -- NPC48.scr:85
        do return ctx:exit("") end -- NPC48.scr:86
    end -- NPC48.scr:87
    ctx:self():stop() -- NPC48.scr:89
    mm9.gosub(script, ctx, "BasewanderStop") -- NPC48.scr:90
    ctx:state().g_hobject = ctx:objectOrNil("HatlatiHome") -- NPC48.scr:91
    ctx:self():walkTo(ctx:object("g_hobject"), 8, "DoNothing") -- NPC48.scr:92
    do return ctx:exit("") end -- NPC48.scr:94
end

script.labels["OnJail"] = function(ctx)
    -- NPC48.scr:97
    mm9.gosub(script, ctx, "followstop") -- NPC48.scr:100
    ctx:state().g_hobject = ctx:objectOrNil("PrisonMarker") -- NPC48.scr:101
    ctx:self():walkTo(ctx:object("g_hobject"), 8, "close") -- NPC48.scr:102
    do return ctx:exit("") end -- NPC48.scr:103
end

script.labels["Close"] = function(ctx)
    -- NPC48.scr:106
    local object = ctx:object("Jaildoor") -- NPC48.scr:109
    object:trigger("close") -- NPC48.scr:110
    object:trigger("lock") -- NPC48.scr:111
    ctx:state().g_hobject = ctx:objectOrNil("Chair9") -- NPC48.scr:112
    ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- NPC48.scr:113
    ctx:self():stop() -- NPC48.scr:115
    mm9.gosub(script, ctx, "BaseWanderStop") -- NPC48.scr:116
    ctx:self():setStat("WanderON", "false") -- NPC48.scr:120
    -- setparam 0 \voices\npc\NPC_048.wav
    -- runscript shopkeeper.scr
    -- exitscript
    do return ctx:exit("") end -- NPC48.scr:124
end

script.labels["Init"] = function(ctx)
    -- NPC48.scr:127
    if ctx:hasKey(154) then -- NPC48.scr:132-133
        ctx:self():stop() -- NPC48.scr:134
        ctx:state().xPos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("PrisonMarker"):pos() -- NPC48.scr:135-136
        ctx:self():setPos("xPos", "yPos", "zPos") -- NPC48.scr:138
        ctx:state().g_hobject = ctx:objectOrNil("Chair9") -- NPC48.scr:139
        ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- NPC48.scr:140
        ctx:giveKey(5009) -- NPC48.scr:141
        ctx:self():stop() -- NPC48.scr:143
        mm9.gosub(script, ctx, "BaseWanderStop") -- NPC48.scr:144
        ctx:self():setStat("WanderON", "false") -- NPC48.scr:147
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
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC48.scr:165
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC48.scr:166
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC48.scr:167
    ctx:wait(1, .1, "Init") -- NPC48.scr:168
    ctx:atTime(12, 0, "OnWander", "OnWander") -- NPC48.scr:169
    ctx:atTime(4, 0, "StopStealing", "StopStealing") -- NPC48.scr:170
    do return ctx:exit("") end -- NPC48.scr:172
end

return script
