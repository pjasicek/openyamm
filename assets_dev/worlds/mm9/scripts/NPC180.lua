-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC180.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "United.inc" }

-- NPC180.scr
-- timmy
-- handles tryygva Ravenlocks voice and quest stuff
-- edited by Bones -- 6/11/03
-- TELP Patch 1.3 -- corrected improper use of variable;
-- probably no bug effects
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["Init"] = function(ctx)
    -- NPC180.scr:30
    ctx:self():loopAnimation("Sit", 0, "DoNothing") -- NPC180.scr:32
    if ctx:hasKey(104) then -- NPC180.scr:35-36
        ctx:state().bVanish = true -- NPC180.scr:37
        mm9.gosub(script, ctx, "vanish") -- NPC180.scr:38
    end -- NPC180.scr:39
    if ctx:hasKey(40) then -- NPC180.scr:42-43
        ctx:state().bVanish = true -- NPC180.scr:44
        mm9.gosub(script, ctx, "vanish") -- NPC180.scr:45
    end -- NPC180.scr:46
    if ctx:hasKey(108) then -- NPC180.scr:48-49
        ctx:state().bVanish = false -- NPC180.scr:50
        mm9.gosub(script, ctx, "Vanish") -- NPC180.scr:51
    end -- NPC180.scr:52
    do return ctx:exit("") end -- NPC180.scr:53
end

script.labels["Vanish"] = function(ctx)
    -- NPC180.scr:58
    ctx:state().g_hobject = ctx:self() -- NPC180.scr:61
    if ctx:condition("bVanish==TRUE") then -- NPC180.scr:63
        ctx:self():setFlag("visible", false) -- NPC180.scr:64
        ctx:self():setFlag("solid", false) -- NPC180.scr:65
        ctx:self():setFlag("gravity", false) -- NPC180.scr:66
        do return ctx:exit("") end -- NPC180.scr:67
    else -- NPC180.scr:68
        ctx:self():setFlag("visible", true) -- NPC180.scr:69
        ctx:self():setFlag("solid", true) -- NPC180.scr:70
        ctx:self():setFlag("gravity", true) -- NPC180.scr:71
        do return ctx:exit("") end -- NPC180.scr:72
    end -- NPC180.scr:73
    do return ctx:exit("") end -- NPC180.scr:75
end

script.labels["OnRude"] = function(ctx)
    -- NPC180.scr:77
    mm9.gosub(script, ctx, "Yanmir") -- NPC180.scr:80
    mm9.gosub(script, ctx, "Breakice") -- NPC180.scr:81
    mm9.gosub(script, ctx, "united") -- NPC180.scr:82
    do return ctx:exit("") end -- NPC180.scr:84
end

script.labels["Yanmir"] = function(ctx)
    -- NPC180.scr:88
    -- Yanmir the frost giant Quest
    ctx:hasKey(172, "keycheck") -- NPC180.scr:94
    if ctx:condition("keycheck==0") then -- NPC180.scr:95
        -- checks to see if they already have got the reward.
        if ctx:hasKey(70) then -- NPC180.scr:97-98
            -- checks to see if they've Beat the frost giant
            ctx:giveKey(172) -- NPC180.scr:100
            ctx:giveExp(58000) -- NPC180.scr:101
            ctx:giveGold(10000) -- NPC180.scr:102
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC180.scr:103
            -- gives reward
            do return ctx:exit("") end -- NPC180.scr:106
        end -- NPC180.scr:107
    end -- NPC180.scr:108
    do return ctx:exit("") end -- NPC180.scr:110
    -- End Yanmir the frost giant quest
    do return ctx:exit("") end -- NPC180.scr:116
end

script.labels["Breakice"] = function(ctx)
    -- NPC180.scr:120
    -- break the ice Quest
    ctx:hasKey(175, "keycheck") -- NPC180.scr:127
    if ctx:condition("keycheck==0") then -- NPC180.scr:128
        -- checks to see if they already have got the reward.
        if ctx:hasKey(73) then -- NPC180.scr:130-131
            -- checks to see if they've Beat the frost giant
            ctx:giveKey(175) -- NPC180.scr:133
            ctx:giveExp(30000) -- NPC180.scr:134
            ctx:giveGold(3000) -- NPC180.scr:135
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC180.scr:136
            -- gives reward
            do return ctx:exit("") end -- NPC180.scr:139
        end -- NPC180.scr:140
    end -- NPC180.scr:141
    do return ctx:exit("") end -- NPC180.scr:143
    -- End break the ice Quest
    do return ctx:exit("") end -- NPC180.scr:147
end

script.labels["OnUse"] = function(ctx)
    -- NPC180.scr:153
    ctx:playSound("voices\\NPC\\NPC_180.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC180.scr:159
    mm9.gosub(script, ctx, "Oncheck") -- NPC180.scr:160
    do return ctx:exit("") end -- NPC180.scr:162
end

script.labels["OnExit"] = function(ctx)
    -- NPC180.scr:165
    do return ctx:exit("") end -- NPC180.scr:168
end

script.labels["Main"] = function(ctx)
    -- NPC180.scr:171
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC180.scr:178
    ctx:addTrigger("Use", "OnUse") -- NPC180.scr:179
    ctx:set("Jarl", "Tryygva") -- NPC180.scr:180
    mm9.gosub(script, ctx, "UnitedInit") -- NPC180.scr:181
    mm9.gosub(script, ctx, "Init") -- NPC180.scr:182
    do return ctx:exit("") end -- NPC180.scr:183
end

return script
