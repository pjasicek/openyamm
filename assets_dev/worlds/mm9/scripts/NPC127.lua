-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC127.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "United.inc" }

-- NPC127.scr
-- timmy
-- handles Markel the Great voice and quest stuff
-- edited by Bones 03/25/03
-- TELP Patch 1.3 -- delays Markel's return
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["Init"] = function(ctx)
    -- NPC127.scr:29
    ctx:self():loopAnimation("Sit", 0, "DoNothing") -- NPC127.scr:32
    if ctx:hasKey(40) then -- NPC127.scr:33-34
        ctx:state().bVanish = true -- NPC127.scr:35
        mm9.gosub(script, ctx, "vanish") -- NPC127.scr:36
    end -- NPC127.scr:37
    if ctx:hasKey(108) then -- NPC127.scr:39-40
        ctx:state().bVanish = false -- NPC127.scr:41
        mm9.gosub(script, ctx, "Vanish") -- NPC127.scr:42
    end -- NPC127.scr:43
    do return ctx:exit("") end -- NPC127.scr:44
end

script.labels["Vanish"] = function(ctx)
    -- NPC127.scr:49
    ctx:state().g_hobject = ctx:self() -- NPC127.scr:52
    if ctx:condition("bVanish==TRUE") then -- NPC127.scr:54
        ctx:self():setFlag("visible", false) -- NPC127.scr:55
        ctx:self():setFlag("solid", false) -- NPC127.scr:56
        ctx:self():setFlag("gravity", false) -- NPC127.scr:57
        do return ctx:exit("") end -- NPC127.scr:58
    else -- NPC127.scr:59
        ctx:self():setFlag("visible", true) -- NPC127.scr:60
        ctx:self():setFlag("solid", true) -- NPC127.scr:61
        ctx:self():setFlag("gravity", true) -- NPC127.scr:62
        do return ctx:exit("") end -- NPC127.scr:63
    end -- NPC127.scr:64
    do return ctx:exit("") end -- NPC127.scr:66
end

script.labels["OnRude"] = function(ctx)
    -- NPC127.scr:69
    mm9.gosub(script, ctx, "BookofRules") -- NPC127.scr:72
    mm9.gosub(script, ctx, "Ivan") -- NPC127.scr:73
    mm9.gosub(script, ctx, "dook") -- NPC127.scr:74
    mm9.gosub(script, ctx, "united") -- NPC127.scr:75
    do return ctx:exit("") end -- NPC127.scr:76
end

script.labels["Bookofrules"] = function(ctx)
    -- NPC127.scr:80
    -- book of Rules Quest
    ctx:hasKey(167, "keycheck") -- NPC127.scr:87
    if ctx:condition("keycheck==0") then -- NPC127.scr:88
        -- checks to see if they already have got the reward.
        if ctx:hasKey(61) then -- NPC127.scr:90-91
            -- checks to see if they've Beat Ivan the Smart
            ctx:giveKey(167) -- NPC127.scr:93
            ctx:giveExp(10000) -- NPC127.scr:94
            ctx:giveGold(3000) -- NPC127.scr:95
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC127.scr:96
            ctx:takeItem(391) -- NPC127.scr:97
            -- gives reward
            do return ctx:exit("") end -- NPC127.scr:100
        end -- NPC127.scr:101
    end -- NPC127.scr:102
    do return ctx:exit("") end -- NPC127.scr:104
    -- End Book of rules quest
    do return ctx:exit("") end -- NPC127.scr:109
end

script.labels["Ivan"] = function(ctx)
    -- NPC127.scr:113
    -- Ivan the smart Quest
    ctx:hasKey(165, "keycheck") -- NPC127.scr:119
    if ctx:condition("keycheck==0") then -- NPC127.scr:120
        -- checks to see if they already have got the reward.
        if ctx:hasKey(62) then -- NPC127.scr:122-123
            -- checks to see if they've Beat Ivan the Smart
            ctx:giveKey(165) -- NPC127.scr:125
            ctx:giveExp(26000) -- NPC127.scr:126
            ctx:giveGold(3000) -- NPC127.scr:127
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC127.scr:128
            ctx:takeItem(400) -- NPC127.scr:129
            -- gives reward
            do return ctx:exit("") end -- NPC127.scr:132
        end -- NPC127.scr:133
    end -- NPC127.scr:134
    do return ctx:exit("") end -- NPC127.scr:136
    -- End Ivan the smart Quest
    do return ctx:exit("") end -- NPC127.scr:141
end

script.labels["Dook"] = function(ctx)
    -- NPC127.scr:145
    -- Dook Quest
    ctx:hasKey(168, "keycheck") -- NPC127.scr:151
    if ctx:condition("keycheck==0") then -- NPC127.scr:152
        -- checks to see if they already have got the reward.
        if ctx:hasKey(66) then -- NPC127.scr:154-155
            -- checks to see if they've Beat the Dook
            ctx:giveKey(168) -- NPC127.scr:157
            ctx:giveExp(40000) -- NPC127.scr:158
            ctx:giveGold(3000) -- NPC127.scr:159
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC127.scr:160
            -- gives reward
            do return ctx:exit("") end -- NPC127.scr:163
        end -- NPC127.scr:164
    end -- NPC127.scr:165
    do return ctx:exit("") end -- NPC127.scr:167
    -- End Dook Quest
    do return ctx:exit("") end -- NPC127.scr:172
end

script.labels["OnUse"] = function(ctx)
    -- NPC127.scr:177
    mm9.gosub(script, ctx, "Oncheck") -- NPC127.scr:180
    ctx:randomInt(1, 4, "g_ntemp") -- NPC127.scr:181
    if ctx:condition("g_ntemp==1") then -- NPC127.scr:183
        ctx:playSound("voices\\NPC\\NPC_127.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC127.scr:184
        do return ctx:exit("") end -- NPC127.scr:185
    end -- NPC127.scr:186
    if ctx:condition("g_ntemp==2") then -- NPC127.scr:188
        ctx:playSound("voices\\NPC\\NPC_127.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC127.scr:189
        do return ctx:exit("") end -- NPC127.scr:190
    end -- NPC127.scr:191
    if ctx:condition("g_ntemp==3") then -- NPC127.scr:193
        ctx:playSound("voices\\NPC\\NPC_127.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC127.scr:194
        do return ctx:exit("") end -- NPC127.scr:195
    end -- NPC127.scr:196
    if ctx:condition("g_ntemp==4") then -- NPC127.scr:198
        ctx:playSound("voices\\NPC\\NPC_127b.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC127.scr:199
        do return ctx:exit("") end -- NPC127.scr:200
    end -- NPC127.scr:201
    do return ctx:exit("") end -- NPC127.scr:205
end

script.labels["OnExit"] = function(ctx)
    -- NPC127.scr:208
    do return ctx:exit("") end -- NPC127.scr:211
end

script.labels["Main"] = function(ctx)
    -- NPC127.scr:214
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC127.scr:221
    ctx:addTrigger("Use", "OnUse") -- NPC127.scr:222
    ctx:set("Jarl", "Markel") -- NPC127.scr:223
    mm9.gosub(script, ctx, "UnitedInit") -- NPC127.scr:224
    mm9.gosub(script, ctx, "Init") -- NPC127.scr:225
    do return ctx:exit("") end -- NPC127.scr:226
end

return script
