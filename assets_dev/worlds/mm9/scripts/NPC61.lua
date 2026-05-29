-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC61.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- NPC61.scr
-- By Timmy
-- gives the player reward for all of Bjarni's quest madness.
-- and the related key
-- Bjarni's RudeID is 45
-- Love Letter is item 247
-- flag variables
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC61.scr:47
    mm9.gosub(script, ctx, "Gladiator") -- NPC61.scr:51
    mm9.gosub(script, ctx, "Shield") -- NPC61.scr:52
    do return ctx:exit("") end -- NPC61.scr:53
end

script.labels["Shield"] = function(ctx)
    -- NPC61.scr:57
    if ctx:hasKey(219) then -- NPC61.scr:60-61
        if ctx:hasItem(375) then -- NPC61.scr:62-63
            ctx:takeItem(375) -- NPC61.scr:64
            do return ctx:exit("") end -- NPC61.scr:65
        end -- NPC61.scr:66
    end -- NPC61.scr:67
    do return ctx:exit("") end -- NPC61.scr:68
end

script.labels["Gladiator"] = function(ctx)
    -- NPC61.scr:72
    -- Mercenary to Gladiator promo quest
    ctx:hasKey(221, "keycheck") -- NPC61.scr:78
    if ctx:condition("keycheck==0") then -- NPC61.scr:79
        -- checks to see if they already have got the reward.
        if ctx:hasKey(26) then -- NPC61.scr:81-82
            -- checks to see if they've rescued Ivsar
            ctx:giveKey(221) -- NPC61.scr:84
            ctx:giveExp(63000) -- NPC61.scr:85
            ctx:giveGold(5000) -- NPC61.scr:86
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC61.scr:87
            -- gives reward
            mm9.gosub(script, ctx, "PromoteGladiator") -- NPC61.scr:89
            do return ctx:exit("") end -- NPC61.scr:91
        end -- NPC61.scr:92
    end -- NPC61.scr:93
    do return ctx:exit("") end -- NPC61.scr:95
end

-- End Mercenary to Gladiator promo quest
script.labels["PromoteGladiator"] = function(ctx)
    -- NPC61.scr:102
    -- Player has already completed the quest
    -- just check to see who gets promoted
    if ctx:hasKey(409) then -- NPC61.scr:110-111
        ctx:givePromo("Gladiator", "Char1") -- NPC61.scr:112
        ctx:takeKey(409) -- NPC61.scr:113
    end -- NPC61.scr:114
    if ctx:hasKey(410) then -- NPC61.scr:116-117
        ctx:givePromo("Gladiator", "Char2") -- NPC61.scr:118
        ctx:takeKey(410) -- NPC61.scr:119
    end -- NPC61.scr:120
    if ctx:hasKey(411) then -- NPC61.scr:122-123
        ctx:givePromo("Gladiator", "Char3") -- NPC61.scr:124
        ctx:takeKey(411) -- NPC61.scr:125
    end -- NPC61.scr:126
    if ctx:hasKey(412) then -- NPC61.scr:128-129
        ctx:givePromo("Gladiator", "Char4") -- NPC61.scr:130
        ctx:takeKey(412) -- NPC61.scr:131
    end -- NPC61.scr:132
    do return ctx:exit("") end -- NPC61.scr:133
end

script.labels["OnUse"] = function(ctx)
    -- NPC61.scr:137
    if ctx:hasItem(380) then -- NPC61.scr:140-141
        if ctx:hasKey(214) then -- NPC61.scr:142-143
            ctx:giveKey(215) -- NPC61.scr:144
        end -- NPC61.scr:145
    end -- NPC61.scr:146
    if ctx:hasItem(591) then -- NPC61.scr:149-150
        if ctx:hasKey(214) then -- NPC61.scr:151-152
            ctx:giveKey(215) -- NPC61.scr:153
        end -- NPC61.scr:154
    end -- NPC61.scr:155
    -- Playsound voices\NPC\NPC_045.wav, Onexit, 100, 240, FALSE, 100
    do return ctx:exit("") end -- NPC61.scr:160
end

script.labels["OnExit"] = function(ctx)
    -- NPC61.scr:163
    do return ctx:exit("") end -- NPC61.scr:166
end

script.labels["Main"] = function(ctx)
    -- NPC61.scr:168
    -- TraceOn ;DELETE ME!!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC61.scr:172
    ctx:addTrigger("Use", "OnUse") -- NPC61.scr:173
    do return ctx:exit("") end -- NPC61.scr:175
end

return script
