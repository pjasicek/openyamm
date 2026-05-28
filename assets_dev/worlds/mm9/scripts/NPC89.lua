-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC89.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- NPC89.scr
-- timmy
-- handles Keith Bloodaxe voice and quest stuff
-- Dolly is item 370
-- Herbs is item 372
-- plow is item 371
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC89.scr:35
    mm9.gosub(script, ctx, "crusaderpromo") -- NPC89.scr:38
    do return ctx:exit("") end -- NPC89.scr:40
end

script.labels["crusaderpromo"] = function(ctx)
    -- NPC89.scr:44
    -- crusaderpromo Quest
    if ctx:hasKey(136) then -- NPC89.scr:50-51
        -- checks to see if player took atli where he goes
        if not ctx:hasKey(137) then -- NPC89.scr:53-54
            -- checks to see if player has already completed quest
            ctx:giveKey(137) -- NPC89.scr:56
            ctx:giveGold(5000) -- NPC89.scr:57
            ctx:giveExp(24500) -- NPC89.scr:58
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC89.scr:59
            mm9.gosub(script, ctx, "PromoteCrusader") -- NPC89.scr:60
            -- gives key and reward.
            do return ctx:exit("") end -- NPC89.scr:62
        end -- NPC89.scr:63
    end -- NPC89.scr:64
    do return ctx:exit("") end -- NPC89.scr:65
    -- End crusaderpromo quest
    do return ctx:exit("") end -- NPC89.scr:72
end

script.labels["PromoteCrusader"] = function(ctx)
    -- NPC89.scr:77
    -- Player has already completed the quest
    -- just check to see who gets promoted
    if ctx:hasKey(413) then -- NPC89.scr:83-84
        ctx:command("givepromo", "Crusader Char1") -- NPC89.scr:85
        ctx:takeKey(413) -- NPC89.scr:86
    end -- NPC89.scr:87
    if ctx:hasKey(414) then -- NPC89.scr:89-90
        ctx:command("givepromo", "Crusader Char2") -- NPC89.scr:91
        ctx:takeKey(414) -- NPC89.scr:92
    end -- NPC89.scr:93
    if ctx:hasKey(415) then -- NPC89.scr:95-96
        ctx:command("givepromo", "Crusader Char3") -- NPC89.scr:97
        ctx:takeKey(415) -- NPC89.scr:98
    end -- NPC89.scr:99
    if ctx:hasKey(416) then -- NPC89.scr:101-102
        ctx:command("givepromo", "Crusader Char4") -- NPC89.scr:103
        ctx:takeKey(416) -- NPC89.scr:104
    end -- NPC89.scr:105
    do return ctx:exit("") end -- NPC89.scr:106
end

script.labels["OnUse"] = function(ctx)
    -- NPC89.scr:110
    ctx:command("playsound", "voices\\NPC\\NPC_089.wav, Onexit, 100, 240, FALSE, 100") -- NPC89.scr:113
    do return ctx:exit("") end -- NPC89.scr:114
end

script.labels["OnExit"] = function(ctx)
    -- NPC89.scr:117
    do return ctx:exit("") end -- NPC89.scr:120
end

script.labels["Main"] = function(ctx)
    -- NPC89.scr:123
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC89.scr:130
    ctx:addTrigger("Use", "OnUse") -- NPC89.scr:132
    do return ctx:exit("") end -- NPC89.scr:134
end

return script
