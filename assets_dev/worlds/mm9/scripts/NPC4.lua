-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC4.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC4.scr
-- timmy
-- handles Johannes Bem voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC4.scr:40
    mm9.gosub(script, ctx, "toMageOne") -- NPC4.scr:44
    mm9.gosub(script, ctx, "reward") -- NPC4.scr:45
    do return ctx:exit("") end -- NPC4.scr:46
end

script.labels["toMageOne"] = function(ctx)
    -- NPC4.scr:50
    if ctx:hasKey(288) then -- NPC4.scr:53-54
        do return ctx:exit("") end -- NPC4.scr:55
    end -- NPC4.scr:56
    if ctx:hasKey(293) then -- NPC4.scr:59-60
        ctx:takeItem(242) -- NPC4.scr:61
        ctx:giveItem(244) -- NPC4.scr:62
        ctx:giveKey(288) -- NPC4.scr:63
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC4.scr:64
        do return ctx:exit("") end -- NPC4.scr:65
    end -- NPC4.scr:66
    do return ctx:exit("") end -- NPC4.scr:67
end

script.labels["Reward"] = function(ctx)
    -- NPC4.scr:71
    if not ctx:hasKey(294) then -- NPC4.scr:78-79
        if ctx:hasKey(493) then -- NPC4.scr:80-81
            ctx:takeItem(243) -- NPC4.scr:82
            ctx:giveKey(294) -- NPC4.scr:83
            ctx:giveGold(5000) -- NPC4.scr:84
            ctx:giveExp(63000) -- NPC4.scr:85
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC4.scr:86
            mm9.gosub(script, ctx, "PromoteMage") -- NPC4.scr:87
            do return ctx:exit("") end -- NPC4.scr:88
        end -- NPC4.scr:89
    end -- NPC4.scr:90
    do return ctx:exit("") end -- NPC4.scr:91
end

script.labels["PromoteMage"] = function(ctx)
    -- NPC4.scr:95
    -- Player has already completed the quest
    -- just check to see who gets promoted
    if ctx:hasKey(429) then -- NPC4.scr:101-102
        ctx:command("givepromo", "Mage Char1") -- NPC4.scr:103
        ctx:takeKey(429) -- NPC4.scr:104
    end -- NPC4.scr:105
    if ctx:hasKey(430) then -- NPC4.scr:107-108
        ctx:command("givepromo", "Mage Char2") -- NPC4.scr:109
        ctx:takeKey(430) -- NPC4.scr:110
    end -- NPC4.scr:111
    if ctx:hasKey(431) then -- NPC4.scr:113-114
        ctx:command("givepromo", "Mage Char3") -- NPC4.scr:115
        ctx:takeKey(431) -- NPC4.scr:116
    end -- NPC4.scr:117
    if ctx:hasKey(432) then -- NPC4.scr:119-120
        ctx:command("givepromo", "Mage Char4") -- NPC4.scr:121
        ctx:takeKey(432) -- NPC4.scr:122
    end -- NPC4.scr:123
    do return ctx:exit("") end -- NPC4.scr:124
end

script.labels["OnUse"] = function(ctx)
    -- NPC4.scr:129
    ctx:command("playsound", "voices\\NPC\\NPC_004.wav, Onexit, 100, 240, FALSE, 100") -- NPC4.scr:132
    do return ctx:exit("") end -- NPC4.scr:133
end

script.labels["OnExit"] = function(ctx)
    -- NPC4.scr:136
    do return ctx:exit("") end -- NPC4.scr:139
end

script.labels["Main"] = function(ctx)
    -- NPC4.scr:142
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC4.scr:149
    ctx:addTrigger("Use", "OnUse") -- NPC4.scr:151
    do return ctx:exit("") end -- NPC4.scr:153
end

return script
