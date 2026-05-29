-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC161.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC161.scr
-- timmy
-- handles Tymon the Nord voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC161.scr:40
    mm9.gosub(script, ctx, "ScholarCheck") -- NPC161.scr:43
    mm9.gosub(script, ctx, "ToScholar") -- NPC161.scr:44
    do return ctx:exit("") end -- NPC161.scr:45
end

script.labels["ScholarCheck"] = function(ctx)
    -- NPC161.scr:50
    -- Player has already completed the quest
    -- just check to see who gets promoted
    if ctx:hasKey(201) then -- NPC161.scr:57-58
        do return ctx:exit("") end -- NPC161.scr:59
    end -- NPC161.scr:60
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC161.scr:62
    if ctx:hasKey(425) then -- NPC161.scr:64-65
        ctx:giveKey(201) -- NPC161.scr:66
    end -- NPC161.scr:67
    if ctx:hasKey(426) then -- NPC161.scr:69-70
        ctx:giveKey(201) -- NPC161.scr:71
    end -- NPC161.scr:72
    if ctx:hasKey(427) then -- NPC161.scr:74-75
        ctx:giveKey(201) -- NPC161.scr:76
    end -- NPC161.scr:77
    if ctx:hasKey(428) then -- NPC161.scr:79-80
        ctx:giveKey(201) -- NPC161.scr:81
    end -- NPC161.scr:82
    do return ctx:exit("") end -- NPC161.scr:83
end

script.labels["PromoteScholar"] = function(ctx)
    -- NPC161.scr:85
    -- Player has already completed the quest
    -- just check to see who gets promoted
    if ctx:hasKey(425) then -- NPC161.scr:91-92
        ctx:givePromo("Scholar", "Char1") -- NPC161.scr:93
        ctx:takeKey(425) -- NPC161.scr:94
    end -- NPC161.scr:95
    if ctx:hasKey(426) then -- NPC161.scr:97-98
        ctx:givePromo("Scholar", "Char2") -- NPC161.scr:99
        ctx:takeKey(426) -- NPC161.scr:100
    end -- NPC161.scr:101
    if ctx:hasKey(427) then -- NPC161.scr:103-104
        ctx:givePromo("Scholar", "Char3") -- NPC161.scr:105
        ctx:takeKey(427) -- NPC161.scr:106
    end -- NPC161.scr:107
    if ctx:hasKey(428) then -- NPC161.scr:109-110
        ctx:givePromo("Scholar", "Char4") -- NPC161.scr:111
        ctx:takeKey(428) -- NPC161.scr:112
    end -- NPC161.scr:113
    do return ctx:exit("") end -- NPC161.scr:114
end

script.labels["ToScholar"] = function(ctx)
    -- NPC161.scr:117
    -- Initiate to Scholar Quest
    ctx:hasKey(205, "keycheck") -- NPC161.scr:123
    if ctx:condition("keycheck==0") then -- NPC161.scr:124
        ctx:hasKey(203, "keycheck") -- NPC161.scr:125
        if ctx:condition("keycheck==1") then -- NPC161.scr:126
            ctx:giveKey(205) -- NPC161.scr:127
            ctx:giveExp(24500) -- NPC161.scr:128
            ctx:giveGold(1000) -- NPC161.scr:129
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC161.scr:130
            mm9.gosub(script, ctx, "PromoteScholar") -- NPC161.scr:131
            do return ctx:exit("") end -- NPC161.scr:132
        end -- NPC161.scr:133
    end -- NPC161.scr:134
    ctx:hasKey(205, "keycheck") -- NPC161.scr:136
    if ctx:condition("keycheck==0") then -- NPC161.scr:137
        ctx:hasKey(204, "keycheck") -- NPC161.scr:138
        if ctx:condition("keycheck==1") then -- NPC161.scr:139
            ctx:giveKey(205) -- NPC161.scr:140
            ctx:giveExp(11000) -- NPC161.scr:141
            ctx:giveGold(1000) -- NPC161.scr:142
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC161.scr:143
            mm9.gosub(script, ctx, "PromoteScholar") -- NPC161.scr:144
            do return ctx:exit("") end -- NPC161.scr:145
        end -- NPC161.scr:146
    end -- NPC161.scr:147
    -- End Initiate to Scholar quest
    do return ctx:exit("") end -- NPC161.scr:152
end

script.labels["OnUse"] = function(ctx)
    -- NPC161.scr:158
    -- Playsound voices\NPC\NPC_145.wav, Onexit, 100, 240, FALSE, 100
    do return ctx:exit("") end -- NPC161.scr:162
end

script.labels["OnExit"] = function(ctx)
    -- NPC161.scr:165
    do return ctx:exit("") end -- NPC161.scr:168
end

script.labels["Main"] = function(ctx)
    -- NPC161.scr:171
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC161.scr:178
    ctx:addTrigger("Use", "OnUse") -- NPC161.scr:180
    do return ctx:exit("") end -- NPC161.scr:182
end

return script
