-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC221.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basewander.inc" }

-- NPC221.scr
-- timmy
-- handles The Green Man voice and quest stuff
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC221.scr:32
    mm9.gosub(script, ctx, "promo") -- NPC221.scr:35
    do return ctx:exit("") end -- NPC221.scr:38
end

script.labels["Promo"] = function(ctx)
    -- NPC221.scr:41
    if not ctx:hasKey(280) then -- NPC221.scr:44-45
        if ctx:hasKey(279) then -- NPC221.scr:46-47
            ctx:giveKey(280) -- NPC221.scr:48
            ctx:giveExp(63000) -- NPC221.scr:49
            ctx:giveGold(5000) -- NPC221.scr:50
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC221.scr:51
            ctx:giveItem(213) -- NPC221.scr:52
            mm9.gosub(script, ctx, "PromoteDruid") -- NPC221.scr:53
            -- givepromo
            do return ctx:exit("") end -- NPC221.scr:55
        end -- NPC221.scr:56
    end -- NPC221.scr:57
    do return ctx:exit("") end -- NPC221.scr:59
end

script.labels["PromoteDruid"] = function(ctx)
    -- NPC221.scr:62
    -- Player has already completed the quest
    -- just check to see who gets promoted
    if ctx:hasKey(445) then -- NPC221.scr:68-69
        ctx:givePromo("Druid", "Char1") -- NPC221.scr:70
        ctx:takeKey(445) -- NPC221.scr:71
    end -- NPC221.scr:72
    if ctx:hasKey(446) then -- NPC221.scr:74-75
        ctx:givePromo("Druid", "Char2") -- NPC221.scr:76
        ctx:takeKey(446) -- NPC221.scr:77
    end -- NPC221.scr:78
    if ctx:hasKey(447) then -- NPC221.scr:80-81
        ctx:givePromo("Druid", "Char3") -- NPC221.scr:82
        ctx:takeKey(447) -- NPC221.scr:83
    end -- NPC221.scr:84
    if ctx:hasKey(448) then -- NPC221.scr:86-87
        ctx:givePromo("Druid", "Char4") -- NPC221.scr:88
        ctx:takeKey(448) -- NPC221.scr:89
    end -- NPC221.scr:90
    do return ctx:exit("") end -- NPC221.scr:91
end

script.labels["OnUse"] = function(ctx)
    -- NPC221.scr:94
    ctx:playSound("voices\\NPC\\NPC_221.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC221.scr:97
    do return ctx:exit("") end -- NPC221.scr:98
end

script.labels["OnExit"] = function(ctx)
    -- NPC221.scr:101
    do return ctx:exit("") end -- NPC221.scr:104
end

script.labels["Main"] = function(ctx)
    -- NPC221.scr:107
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC221.scr:114
    ctx:addTrigger("Use", "OnUse") -- NPC221.scr:116
    mm9.gosub(script, ctx, "basewanderinit") -- NPC221.scr:117
    do return ctx:exit("") end -- NPC221.scr:118
end

return script
