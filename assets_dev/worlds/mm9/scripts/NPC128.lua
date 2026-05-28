-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC128.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC128.scr
-- timmy
-- handles Tjolnir the Super-neat voice and quest stuff
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC128.scr:34
    mm9.gosub(script, ctx, "Promocheck") -- NPC128.scr:37
    mm9.gosub(script, ctx, "Nurtigan") -- NPC128.scr:38
    do return ctx:exit("") end -- NPC128.scr:41
end

script.labels["PromoteHealer"] = function(ctx)
    -- NPC128.scr:44
    -- Player has already completed the quest
    -- just check to see who gets promoted
    ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC128.scr:50
    if ctx:hasKey(437) then -- NPC128.scr:51-52
        ctx:command("givepromo", "Healer Char1") -- NPC128.scr:53
        ctx:takeKey(437) -- NPC128.scr:54
    end -- NPC128.scr:55
    if ctx:hasKey(438) then -- NPC128.scr:57-58
        ctx:command("givepromo", "Healer Char2") -- NPC128.scr:59
        ctx:takeKey(438) -- NPC128.scr:60
    end -- NPC128.scr:61
    if ctx:hasKey(439) then -- NPC128.scr:63-64
        ctx:command("givepromo", "Healer Char3") -- NPC128.scr:65
        ctx:takeKey(439) -- NPC128.scr:66
    end -- NPC128.scr:67
    if ctx:hasKey(440) then -- NPC128.scr:69-70
        ctx:command("givepromo", "Healer Char4") -- NPC128.scr:71
        ctx:takeKey(440) -- NPC128.scr:72
    end -- NPC128.scr:73
    do return ctx:exit("") end -- NPC128.scr:74
end

script.labels["Promocheck"] = function(ctx)
    -- NPC128.scr:78
    if ctx:hasKey(206) then -- NPC128.scr:81-82
        do return ctx:exit("") end -- NPC128.scr:83
    end -- NPC128.scr:84
    if ctx:hasKey(437) then -- NPC128.scr:86-87
        ctx:giveKey(206) -- NPC128.scr:88
        do return ctx:exit("") end -- NPC128.scr:89
    end -- NPC128.scr:90
    if ctx:hasKey(438) then -- NPC128.scr:92-93
        ctx:giveKey(206) -- NPC128.scr:94
        do return ctx:exit("") end -- NPC128.scr:95
    end -- NPC128.scr:96
    if ctx:hasKey(439) then -- NPC128.scr:98-99
        ctx:giveKey(206) -- NPC128.scr:100
        do return ctx:exit("") end -- NPC128.scr:101
    end -- NPC128.scr:102
    if ctx:hasKey(440) then -- NPC128.scr:104-105
        ctx:giveKey(206) -- NPC128.scr:106
        do return ctx:exit("") end -- NPC128.scr:107
    end -- NPC128.scr:108
end

script.labels["Nurtigan"] = function(ctx)
    -- NPC128.scr:111
    -- Nurtigan Quest
    if not ctx:hasKey(213) then -- NPC128.scr:117-118
        if ctx:hasKey(212) then -- NPC128.scr:119-120
            ctx:giveKey(213) -- NPC128.scr:121
            ctx:giveExp(24500) -- NPC128.scr:122
            ctx:giveGold(1000) -- NPC128.scr:123
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC128.scr:124
            mm9.gosub(script, ctx, "PromoteHealer") -- NPC128.scr:125
            do return ctx:exit("") end -- NPC128.scr:126
        end -- NPC128.scr:127
    end -- NPC128.scr:128
    -- End Nurtigan quest
    do return ctx:exit("") end -- NPC128.scr:132
end

script.labels["OnUse"] = function(ctx)
    -- NPC128.scr:138
    ctx:command("playsound", "voices\\NPC\\NPC_128.wav, Onexit, 100, 240, FALSE, 100") -- NPC128.scr:142
    do return ctx:exit("") end -- NPC128.scr:143
end

script.labels["OnExit"] = function(ctx)
    -- NPC128.scr:146
    do return ctx:exit("") end -- NPC128.scr:149
end

script.labels["Main"] = function(ctx)
    -- NPC128.scr:152
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC128.scr:159
    ctx:addTrigger("Use", "OnUse") -- NPC128.scr:161
    do return ctx:exit("") end -- NPC128.scr:163
end

return script
