-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC88.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC88.scr
-- timmy
-- handles Atli the Quick voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC88.scr:41
    mm9.gosub(script, ctx, "Promo") -- NPC88.scr:44
    do return ctx:exit("") end -- NPC88.scr:47
end

script.labels["PromoteAssassin"] = function(ctx)
    -- NPC88.scr:51
    -- Player has already completed the quest
    -- just check to see who gets promoted
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC88.scr:57
    if ctx:hasKey(405) then -- NPC88.scr:59-60
        ctx:givePromo("Assassin", "Char1") -- NPC88.scr:61
        ctx:takeKey(405) -- NPC88.scr:62
    end -- NPC88.scr:63
    if ctx:hasKey(406) then -- NPC88.scr:65-66
        ctx:givePromo("Assassin", "Char2") -- NPC88.scr:67
        ctx:takeKey(406) -- NPC88.scr:68
    end -- NPC88.scr:69
    if ctx:hasKey(407) then -- NPC88.scr:71-72
        ctx:givePromo("Assassin", "Char3") -- NPC88.scr:73
        ctx:takeKey(407) -- NPC88.scr:74
    end -- NPC88.scr:75
    if ctx:hasKey(408) then -- NPC88.scr:77-78
        ctx:givePromo("Assassin", "Char4") -- NPC88.scr:79
        ctx:takeKey(408) -- NPC88.scr:80
    end -- NPC88.scr:81
    do return ctx:exit("") end -- NPC88.scr:82
end

script.labels["promo"] = function(ctx)
    -- NPC88.scr:84
    -- Mercenary to assassin promo quest
    ctx:hasKey(227, "keycheck") -- NPC88.scr:90
    if ctx:condition("keycheck==0") then -- NPC88.scr:91
        -- checks to see if they already have got the reward.
        if ctx:hasKey(226) then -- NPC88.scr:93-94
            -- checks to see if they've rescued Ivsar
            ctx:giveKey(227) -- NPC88.scr:96
            ctx:giveExp(63000) -- NPC88.scr:97
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC88.scr:98
            ctx:giveGold(5000) -- NPC88.scr:99
            -- gives reward
            mm9.gosub(script, ctx, "PromoteAssassin") -- NPC88.scr:101
            do return ctx:exit("") end -- NPC88.scr:103
        end -- NPC88.scr:104
    end -- NPC88.scr:105
    do return ctx:exit("") end -- NPC88.scr:107
end

-- End Mercenary to assassin promo quest
script.labels["OnUse"] = function(ctx)
    -- NPC88.scr:112
    ctx:playSound("voices\\NPC\\NPC_088.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC88.scr:115
    do return ctx:exit("") end -- NPC88.scr:116
end

script.labels["OnExit"] = function(ctx)
    -- NPC88.scr:119
    do return ctx:exit("") end -- NPC88.scr:122
end

script.labels["Main"] = function(ctx)
    -- NPC88.scr:125
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC88.scr:132
    ctx:addTrigger("Use", "OnUse") -- NPC88.scr:134
    do return ctx:exit("") end -- NPC88.scr:136
end

return script
