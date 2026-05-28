-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC87.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "United.inc" }

-- NPC87.scr
-- timmy
-- handles Sigmund the Stressed voice and quest stuff
-- edited by Bones 03/25/03
-- TELP Patch 1.3 -- delays Sigmund's return
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["Init"] = function(ctx)
    -- NPC87.scr:30
    if ctx:hasKey(40) then -- NPC87.scr:32-33
        ctx:command("set", "bVanish TRUE") -- NPC87.scr:34
        mm9.gosub(script, ctx, "vanish") -- NPC87.scr:35
    end -- NPC87.scr:36
    if ctx:hasKey(108) then -- NPC87.scr:38-39
        ctx:command("set", "bVanish False") -- NPC87.scr:40
        mm9.gosub(script, ctx, "Vanish") -- NPC87.scr:41
    end -- NPC87.scr:42
    do return ctx:exit("") end -- NPC87.scr:43
end

script.labels["Vanish"] = function(ctx)
    -- NPC87.scr:48
    ctx:command("getmyhandle", "g_hobject") -- NPC87.scr:51
    if ctx:condition("bVanish==TRUE") then -- NPC87.scr:53
        ctx:command("clearflag", "g_hobject, visible") -- NPC87.scr:54
        ctx:command("clearflag", "g_hobject, solid") -- NPC87.scr:55
        ctx:command("clearflag", "g_hobject, gravity") -- NPC87.scr:56
        do return ctx:exit("") end -- NPC87.scr:57
    else -- NPC87.scr:58
        ctx:command("setflag", "g_hobject, visible") -- NPC87.scr:59
        ctx:command("setflag", "g_hobject, solid") -- NPC87.scr:60
        ctx:command("setflag", "g_hobject, gravity") -- NPC87.scr:61
        ctx:command("loopanim", "Sit 0 DoNothing") -- NPC87.scr:62
        do return ctx:exit("") end -- NPC87.scr:63
    end -- NPC87.scr:64
    do return ctx:exit("") end -- NPC87.scr:66
end

script.labels["OnRude"] = function(ctx)
    -- NPC87.scr:68
    if not ctx:hasKey(489) then -- NPC87.scr:71-72
        if ctx:hasKey(44) then -- NPC87.scr:73-74
            ctx:giveItem(596) -- NPC87.scr:75
            ctx:giveKey(489) -- NPC87.scr:76
        end -- NPC87.scr:77
    end -- NPC87.scr:78
    mm9.gosub(script, ctx, "Gossip") -- NPC87.scr:80
    mm9.gosub(script, ctx, "FortStenig") -- NPC87.scr:81
    mm9.gosub(script, ctx, "CronaKiga") -- NPC87.scr:82
    mm9.gosub(script, ctx, "united") -- NPC87.scr:83
    do return ctx:exit("") end -- NPC87.scr:84
end

script.labels["Gossip"] = function(ctx)
    -- NPC87.scr:88
    if not ctx:hasKey(300) then -- NPC87.scr:91-92
        if ctx:hasKey(55) then -- NPC87.scr:93-94
            ctx:giveKey(300) -- NPC87.scr:95
            ctx:giveExp(5000) -- NPC87.scr:96
            ctx:giveGold(5000) -- NPC87.scr:97
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC87.scr:98
            do return ctx:exit("") end -- NPC87.scr:99
        end -- NPC87.scr:100
    end -- NPC87.scr:101
    do return ctx:exit("") end -- NPC87.scr:102
end

script.labels["FortStenig"] = function(ctx)
    -- NPC87.scr:105
    -- Fort Stenig Quest
    ctx:hasKey(171, "keycheck") -- NPC87.scr:111
    if ctx:condition("keycheck==0") then -- NPC87.scr:112
        -- checks to see if they already have got the reward.
        if ctx:hasKey(49) then -- NPC87.scr:114-115
            -- checks to see if they've got cronakiga
            ctx:giveKey(171) -- NPC87.scr:117
            ctx:giveExp(32000) -- NPC87.scr:118
            ctx:giveGold(7000) -- NPC87.scr:119
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC87.scr:120
            -- gives reward
            do return ctx:exit("") end -- NPC87.scr:124
        end -- NPC87.scr:125
    end -- NPC87.scr:126
    do return ctx:exit("") end -- NPC87.scr:128
    -- End Fort stenig quest
    do return ctx:exit("") end -- NPC87.scr:133
end

script.labels["CronaKiga"] = function(ctx)
    -- NPC87.scr:137
    -- CronaKiga Quest
    ctx:hasKey(170, "keycheck") -- NPC87.scr:144
    if ctx:condition("keycheck==0") then -- NPC87.scr:145
        -- checks to see if they already have got the reward.
        if ctx:hasKey(50) then -- NPC87.scr:147-148
            -- checks to see if they've got cronakiga
            ctx:giveKey(170) -- NPC87.scr:150
            ctx:giveExp(52000) -- NPC87.scr:151
            ctx:giveGold(10000) -- NPC87.scr:152
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC87.scr:153
            ctx:takeItem(390) -- NPC87.scr:154
            -- gives reward
            do return ctx:exit("") end -- NPC87.scr:157
        end -- NPC87.scr:158
    end -- NPC87.scr:159
    do return ctx:exit("") end -- NPC87.scr:161
    -- End Crona Kiga Quest
    do return ctx:exit("") end -- NPC87.scr:166
end

script.labels["OnUse"] = function(ctx)
    -- NPC87.scr:172
    ctx:command("playsound", "voices\\NPC\\NPC_087.wav, Onexit, 100, 240, FALSE, 100") -- NPC87.scr:175
    mm9.gosub(script, ctx, "OnCheck") -- NPC87.scr:176
    do return ctx:exit("") end -- NPC87.scr:177
end

script.labels["OnExit"] = function(ctx)
    -- NPC87.scr:180
    do return ctx:exit("") end -- NPC87.scr:183
end

script.labels["Main"] = function(ctx)
    -- NPC87.scr:186
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC87.scr:191
    ctx:addTrigger("Use", "OnUse") -- NPC87.scr:192
    ctx:command("set", "Jarl, Sigmund") -- NPC87.scr:193
    mm9.gosub(script, ctx, "UnitedInit") -- NPC87.scr:194
    mm9.gosub(script, ctx, "Init") -- NPC87.scr:195
    do return ctx:exit("") end -- NPC87.scr:196
end

return script
