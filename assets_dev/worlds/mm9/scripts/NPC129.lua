-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC129.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC129.scr
-- timmy
-- handles Gray Slemnir voice and quest stuff
-- promo variables
script.labels["PromotePriest"] = function(ctx)
    -- NPC129.scr:35
    -- Player has already completed the quest
    -- just check to see who gets promoted
    ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC129.scr:40
    if ctx:hasKey(441) then -- NPC129.scr:41-42
        ctx:command("givepromo", "Priest Char1") -- NPC129.scr:43
        ctx:takeKey(441) -- NPC129.scr:44
    end -- NPC129.scr:45
    if ctx:hasKey(442) then -- NPC129.scr:47-48
        ctx:command("givepromo", "Priest Char2") -- NPC129.scr:49
        ctx:takeKey(442) -- NPC129.scr:50
    end -- NPC129.scr:51
    if ctx:hasKey(443) then -- NPC129.scr:53-54
        ctx:command("givepromo", "Priest Char3") -- NPC129.scr:55
        ctx:takeKey(443) -- NPC129.scr:56
    end -- NPC129.scr:57
    if ctx:hasKey(444) then -- NPC129.scr:59-60
        ctx:command("givepromo", "Priest Char4") -- NPC129.scr:61
        ctx:takeKey(444) -- NPC129.scr:62
    end -- NPC129.scr:63
    do return ctx:exit("") end -- NPC129.scr:64
end

script.labels["OnRude"] = function(ctx)
    -- NPC129.scr:70
    mm9.gosub(script, ctx, "Givequest") -- NPC129.scr:74
    mm9.gosub(script, ctx, "priest") -- NPC129.scr:75
    do return ctx:exit("") end -- NPC129.scr:78
end

script.labels["Givequest"] = function(ctx)
    -- NPC129.scr:82
    if ctx:hasKey(441) then -- NPC129.scr:85-86
        ctx:giveKey(250) -- NPC129.scr:87
        ctx:giveKey(251) -- NPC129.scr:88
        ctx:giveKey(252) -- NPC129.scr:89
        do return ctx:exit("") end -- NPC129.scr:90
    end -- NPC129.scr:91
    if ctx:hasKey(442) then -- NPC129.scr:93-94
        ctx:giveKey(250) -- NPC129.scr:95
        ctx:giveKey(251) -- NPC129.scr:96
        ctx:giveKey(252) -- NPC129.scr:97
        do return ctx:exit("") end -- NPC129.scr:98
    end -- NPC129.scr:99
    if ctx:hasKey(443) then -- NPC129.scr:101-102
        ctx:giveKey(250) -- NPC129.scr:103
        ctx:giveKey(251) -- NPC129.scr:104
        ctx:giveKey(252) -- NPC129.scr:105
        do return ctx:exit("") end -- NPC129.scr:106
    end -- NPC129.scr:107
    if ctx:hasKey(444) then -- NPC129.scr:109-110
        ctx:giveKey(250) -- NPC129.scr:111
        ctx:giveKey(251) -- NPC129.scr:112
        ctx:giveKey(252) -- NPC129.scr:113
        do return ctx:exit("") end -- NPC129.scr:114
    end -- NPC129.scr:115
end

script.labels["priest"] = function(ctx)
    -- NPC129.scr:118
    -- priest Quest
    if not ctx:hasKey(261) then -- NPC129.scr:124-125
        if ctx:hasKey(260) then -- NPC129.scr:126-127
            ctx:giveExp(63000) -- NPC129.scr:128
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC129.scr:129
            ctx:giveGold(5000) -- NPC129.scr:130
            ctx:giveKey(261) -- NPC129.scr:131
            ctx:takeItem(241) -- NPC129.scr:132
            ctx:takeItem(430) -- NPC129.scr:133
            mm9.gosub(script, ctx, "PromotePriest") -- NPC129.scr:134
            do return ctx:exit("") end -- NPC129.scr:135
        end -- NPC129.scr:136
    end -- NPC129.scr:137
    do return ctx:exit("") end -- NPC129.scr:138
    -- End priest quest
    do return ctx:exit("") end -- NPC129.scr:143
end

script.labels["OnUse"] = function(ctx)
    -- NPC129.scr:149
    ctx:command("playsound", "voices\\NPC\\NPC_129.wav, Onexit, 100, 240, FALSE, 100") -- NPC129.scr:152
    do return ctx:exit("") end -- NPC129.scr:153
end

script.labels["OnExit"] = function(ctx)
    -- NPC129.scr:156
    do return ctx:exit("") end -- NPC129.scr:159
end

script.labels["Main"] = function(ctx)
    -- NPC129.scr:162
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC129.scr:169
    ctx:addTrigger("Use", "OnUse") -- NPC129.scr:171
    do return ctx:exit("") end -- NPC129.scr:173
end

return script
