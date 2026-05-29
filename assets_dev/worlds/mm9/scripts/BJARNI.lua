-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BJARNI.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "United.inc" }

-- Bjarni.scr
-- By Timmy
-- gives the player reward for all of Bjarni's quest madness.
-- and the related key
-- Bjarni's RudeID is 45
-- Love Letter is item 247
-- edited by Bones 03/25/03
-- TELP Patch 1.3 -- delays Bjarni's return
-- flag variables
-- promo variables
script.labels["Init"] = function(ctx)
    -- BJARNI.scr:30
    ctx:self():loopAnimation("Sit", 0, "DoNothing") -- BJARNI.scr:33
    if ctx:hasKey(40) then -- BJARNI.scr:34-35
        ctx:state().bVanish = true -- BJARNI.scr:36
        mm9.gosub(script, ctx, "vanish") -- BJARNI.scr:37
    end -- BJARNI.scr:38
    if ctx:hasKey(108) then -- BJARNI.scr:40-41
        ctx:state().bVanish = false -- BJARNI.scr:42
        mm9.gosub(script, ctx, "Vanish") -- BJARNI.scr:43
    end -- BJARNI.scr:44
    do return ctx:exit("") end -- BJARNI.scr:45
end

script.labels["Vanish"] = function(ctx)
    -- BJARNI.scr:50
    ctx:state().g_hobject = ctx:self() -- BJARNI.scr:53
    if ctx:condition("bVanish==TRUE") then -- BJARNI.scr:55
        ctx:self():setFlag("visible", false) -- BJARNI.scr:56
        ctx:self():setFlag("solid", false) -- BJARNI.scr:57
        ctx:self():setFlag("gravity", false) -- BJARNI.scr:58
        do return ctx:exit("") end -- BJARNI.scr:59
    else -- BJARNI.scr:60
        ctx:self():setFlag("visible", true) -- BJARNI.scr:61
        ctx:self():setFlag("solid", true) -- BJARNI.scr:62
        ctx:self():setFlag("gravity", true) -- BJARNI.scr:63
        do return ctx:exit("") end -- BJARNI.scr:64
    end -- BJARNI.scr:65
    do return ctx:exit("") end -- BJARNI.scr:67
end

script.labels["OnRude"] = function(ctx)
    -- BJARNI.scr:70
    mm9.gosub(script, ctx, "ivsar") -- BJARNI.scr:73
    mm9.gosub(script, ctx, "loveletter") -- BJARNI.scr:74
    mm9.gosub(script, ctx, "loveletter2") -- BJARNI.scr:75
    mm9.gosub(script, ctx, "anskram") -- BJARNI.scr:76
    mm9.gosub(script, ctx, "united") -- BJARNI.scr:77
    do return ctx:exit("") end -- BJARNI.scr:79
end

script.labels["Ivsar"] = function(ctx)
    -- BJARNI.scr:85
    -- Ivsar quest
    ctx:hasKey(117, "keycheck") -- BJARNI.scr:90
    if ctx:condition("keycheck==0") then -- BJARNI.scr:91
        -- checks to see if they already have got the reward.
        if ctx:hasKey(21) then -- BJARNI.scr:93-94
            -- checks to see if they've rescued Ivsar
            ctx:giveKey(117) -- BJARNI.scr:96
            ctx:giveExp(42000) -- BJARNI.scr:97
            ctx:giveGold(3500) -- BJARNI.scr:98
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- BJARNI.scr:99
            -- gives reward
            ctx:object("Ivsar"):trigger("stop") -- BJARNI.scr:101-102
            do return ctx:exit("") end -- BJARNI.scr:104
        end -- BJARNI.scr:105
    end -- BJARNI.scr:106
    do return ctx:exit("") end -- BJARNI.scr:108
end

-- End Ivsar quest
script.labels["Loveletter"] = function(ctx)
    -- BJARNI.scr:114
    -- Love Letter quest
    -- Gives love letter
    ctx:hasKey(22, "Keycheck") -- BJARNI.scr:123
    if ctx:condition("Keycheck==1") then -- BJARNI.scr:124
        ctx:hasKey(150, "Keycheck") -- BJARNI.scr:125
        if ctx:condition("keycheck==0") then -- BJARNI.scr:126
            ctx:giveItem(247) -- BJARNI.scr:127
            ctx:giveKey(150) -- BJARNI.scr:128
            do return ctx:exit("") end -- BJARNI.scr:129
        end -- BJARNI.scr:130
    end -- BJARNI.scr:131
end

script.labels["loveletter2"] = function(ctx)
    -- BJARNI.scr:135
    -- give reward for love letter
    ctx:hasKey(24, "keycheck") -- BJARNI.scr:141
    if ctx:condition("keycheck==1") then -- BJARNI.scr:142
        ctx:hasKey(151, "keycheck") -- BJARNI.scr:143
        if ctx:condition("keycheck==0") then -- BJARNI.scr:144
            ctx:giveExp(15200) -- BJARNI.scr:145
            ctx:giveGold(2000) -- BJARNI.scr:146
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- BJARNI.scr:147
            ctx:giveKey(151) -- BJARNI.scr:148
            do return ctx:exit("") end -- BJARNI.scr:149
        end -- BJARNI.scr:150
    end -- BJARNI.scr:151
    ctx:hasKey(25, "keycheck") -- BJARNI.scr:153
    if ctx:condition("keycheck==1") then -- BJARNI.scr:154
        ctx:hasKey(151, "keycheck") -- BJARNI.scr:155
        if ctx:condition("keycheck==0") then -- BJARNI.scr:156
            ctx:giveExp(15200) -- BJARNI.scr:157
            ctx:giveGold(2000) -- BJARNI.scr:158
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- BJARNI.scr:159
            ctx:giveKey(151) -- BJARNI.scr:160
            do return ctx:exit("") end -- BJARNI.scr:161
        end -- BJARNI.scr:162
    end -- BJARNI.scr:163
    do return ctx:exit("") end -- BJARNI.scr:166
end

-- End Loveletter Quest
script.labels["Anskram"] = function(ctx)
    -- BJARNI.scr:172
    -- Anskram Keep quest
    ctx:hasKey(149, "keycheck") -- BJARNI.scr:179
    if ctx:condition("keycheck==TRUE") then -- BJARNI.scr:180
        do return ctx:exit("") end -- BJARNI.scr:181
    end -- BJARNI.scr:182
    -- checks to see if they already have got the reward.
    if ctx:hasKey(41) then -- BJARNI.scr:186-187
        -- checks to see if they've cleared Anskram
        ctx:giveKey(149) -- BJARNI.scr:189
        ctx:giveExp(20000) -- BJARNI.scr:190
        ctx:giveGold(3000) -- BJARNI.scr:191
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- BJARNI.scr:192
        -- gives reward
        do return ctx:exit("") end -- BJARNI.scr:194
    end -- BJARNI.scr:195
    -- End Anskram Keep Quest
    do return ctx:exit("") end -- BJARNI.scr:201
end

script.labels["OnUse"] = function(ctx)
    -- BJARNI.scr:205
    if ctx:hasItem(380) then -- BJARNI.scr:208-209
        if ctx:hasKey(214) then -- BJARNI.scr:210-211
            ctx:giveKey(215) -- BJARNI.scr:212
        end -- BJARNI.scr:213
    end -- BJARNI.scr:214
    if ctx:hasItem(591) then -- BJARNI.scr:217-218
        if ctx:hasKey(214) then -- BJARNI.scr:219-220
            ctx:giveKey(215) -- BJARNI.scr:221
        end -- BJARNI.scr:222
    end -- BJARNI.scr:223
    ctx:playSound("voices\\NPC\\NPC_045.wav", "Onexit", 100, 240, "FALSE", 100) -- BJARNI.scr:225
    mm9.gosub(script, ctx, "OnCheck") -- BJARNI.scr:226
    do return ctx:exit("") end -- BJARNI.scr:228
end

script.labels["OnExit"] = function(ctx)
    -- BJARNI.scr:231
    do return ctx:exit("") end -- BJARNI.scr:234
end

script.labels["Main"] = function(ctx)
    -- BJARNI.scr:236
    -- TraceOn ;DELETE ME!!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- BJARNI.scr:240
    ctx:addTrigger("Use", "OnUse") -- BJARNI.scr:241
    ctx:self():loopAnimation("listen", 0, "Onexit") -- BJARNI.scr:242
    ctx:set("Jarl", "Bjarni") -- BJARNI.scr:243
    mm9.gosub(script, ctx, "UnitedInit") -- BJARNI.scr:244
    ctx:onEvent("OnPostStartWorld", "Init") -- BJARNI.scr:245
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- BJARNI.scr:246
    ctx:onEvent("OnPostSaveLoad", "Init") -- BJARNI.scr:247
    ctx:wait(1, .1, "Init") -- BJARNI.scr:248
    do return ctx:exit("") end -- BJARNI.scr:249
end

return script
