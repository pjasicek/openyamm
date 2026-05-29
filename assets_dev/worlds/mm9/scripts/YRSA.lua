-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YRSA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "basewander.inc" }

-- yrsa.scr
-- By Timmy
-- handles Yrsa's stuff
script.labels["OnRude"] = function(ctx)
    -- YRSA.scr:15
    mm9.gosub(script, ctx, "Key") -- YRSA.scr:18
    mm9.gosub(script, ctx, "dragonfly") -- YRSA.scr:19
    mm9.gosub(script, ctx, "Mainline") -- YRSA.scr:20
    do return ctx:exit("") end -- YRSA.scr:21
end

script.labels["Key"] = function(ctx)
    -- YRSA.scr:24
    if ctx:hasItem(568) then -- YRSA.scr:26-27
        do return ctx:exit("") end -- YRSA.scr:28
    end -- YRSA.scr:29
    if ctx:hasKey(469) then -- YRSA.scr:31-32
        ctx:giveItem(568) -- YRSA.scr:33
        do return ctx:exit("") end -- YRSA.scr:34
    end -- YRSA.scr:35
    do return ctx:exit("") end -- YRSA.scr:37
end

script.labels["Mainline"] = function(ctx)
    -- YRSA.scr:39
    if not ctx:hasKey(367) then -- YRSA.scr:43-44
        if ctx:hasKey(1) then -- YRSA.scr:45-46
            ctx:giveExp(2000) -- YRSA.scr:47
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- YRSA.scr:48
            ctx:giveKey(367) -- YRSA.scr:49
            do return ctx:exit("") end -- YRSA.scr:50
        end -- YRSA.scr:51
    end -- YRSA.scr:52
    do return ctx:exit("") end -- YRSA.scr:53
end

script.labels["dragonfly"] = function(ctx)
    -- YRSA.scr:56
    if not ctx:hasKey(366) then -- YRSA.scr:60-61
        if ctx:hasKey(27) then -- YRSA.scr:62-63
            ctx:giveExp(2000) -- YRSA.scr:64
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- YRSA.scr:65
            ctx:giveKey(366) -- YRSA.scr:66
            do return ctx:exit("") end -- YRSA.scr:67
        end -- YRSA.scr:68
    end -- YRSA.scr:69
    do return ctx:exit("") end -- YRSA.scr:70
end

script.labels["OnUse"] = function(ctx)
    -- YRSA.scr:75
    ctx:giveKey(480) -- YRSA.scr:78
    if not ctx:hasKey(365) then -- YRSA.scr:81-82
        ctx:giveKey(365) -- YRSA.scr:83
        ctx:giveExp(800) -- YRSA.scr:84
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- YRSA.scr:85
        -- found Yrsa for the first time
    end -- YRSA.scr:87
    ctx:state().Talking = true -- YRSA.scr:92
    ctx:self():stop() -- YRSA.scr:93
    mm9.gosub(script, ctx, "BasewanderStop") -- YRSA.scr:94
    ctx:getParam(0, "g_hobject") -- YRSA.scr:95
    ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- YRSA.scr:96
    -- DoRude 1
    ctx:playSound("voices\\NPC\\NPC_001.wav", "Onexit", 100, 240, "FALSE", 100) -- YRSA.scr:98
    do return ctx:exit("") end -- YRSA.scr:102
end

script.labels["Init"] = function(ctx)
    -- YRSA.scr:106
    if ctx:hasKey(29) then -- YRSA.scr:109-110
        ctx:self():remove() -- YRSA.scr:112
        do return ctx:exit("") end -- YRSA.scr:113
    end -- YRSA.scr:114
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- YRSA.scr:117
    do return ctx:exit("") end -- YRSA.scr:118
end

script.labels["Onexit"] = function(ctx)
    -- YRSA.scr:123
    ctx:state().talking = false -- YRSA.scr:126
    do return ctx:exit("") end -- YRSA.scr:127
end

script.labels["Main"] = function(ctx)
    -- YRSA.scr:130
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "OnUse") -- YRSA.scr:135
    mm9.gosub(script, ctx, "basewanderinit") -- YRSA.scr:136
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- YRSA.scr:137
    mm9.gosub(script, ctx, "Init") -- YRSA.scr:138
    ctx:wait(1, .1, "Init") -- YRSA.scr:139
    do return ctx:exit("") end -- YRSA.scr:140
end

return script
