-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC181.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC181.scr
-- timmy
-- handles Fenja Tree-friend voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- promo variables
script.labels["OnRude"] = function(ctx)
    -- NPC181.scr:40
    mm9.gosub(script, ctx, "Ranger") -- NPC181.scr:43
    do return ctx:exit("") end -- NPC181.scr:46
end

script.labels["Ranger"] = function(ctx)
    -- NPC181.scr:50
    -- Ranger Quest
    if not ctx:hasKey(249) then -- NPC181.scr:56-57
        if ctx:hasKey(248) then -- NPC181.scr:58-59
            ctx:giveExp(63000) -- NPC181.scr:60
            ctx:giveGold(5000) -- NPC181.scr:61
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC181.scr:62
            ctx:giveKey(249) -- NPC181.scr:63
            mm9.gosub(script, ctx, "PromoteRanger") -- NPC181.scr:64
            do return ctx:exit("") end -- NPC181.scr:65
        end -- NPC181.scr:66
    end -- NPC181.scr:67
    -- End RAnger quest
    do return ctx:exit("") end -- NPC181.scr:71
end

script.labels["PromoteRanger"] = function(ctx)
    -- NPC181.scr:76
    -- Player has already completed the quest
    -- just check to see who gets promoted
    if ctx:hasKey(417) then -- NPC181.scr:82-83
        ctx:command("givepromo", "Ranger Char1") -- NPC181.scr:84
        ctx:takeKey(417) -- NPC181.scr:85
    end -- NPC181.scr:86
    if ctx:hasKey(418) then -- NPC181.scr:88-89
        ctx:command("givepromo", "Ranger Char2") -- NPC181.scr:90
        ctx:takeKey(418) -- NPC181.scr:91
    end -- NPC181.scr:92
    if ctx:hasKey(419) then -- NPC181.scr:94-95
        ctx:command("givepromo", "Ranger Char3") -- NPC181.scr:96
        ctx:takeKey(419) -- NPC181.scr:97
    end -- NPC181.scr:98
    if ctx:hasKey(420) then -- NPC181.scr:100-101
        ctx:command("givepromo", "Ranger Char4") -- NPC181.scr:102
        ctx:takeKey(420) -- NPC181.scr:103
    end -- NPC181.scr:104
    do return ctx:exit("") end -- NPC181.scr:105
end

script.labels["OnUse"] = function(ctx)
    -- NPC181.scr:109
    if ctx:hasItem(184) then -- NPC181.scr:112-113
        ctx:giveKey(241) -- NPC181.scr:114
    end -- NPC181.scr:115
    ctx:command("playsound", "voices\\NPC\\NPC_181.wav, Onexit, 100, 240, FALSE, 100") -- NPC181.scr:117
    do return ctx:exit("") end -- NPC181.scr:118
end

script.labels["OnExit"] = function(ctx)
    -- NPC181.scr:121
    do return ctx:exit("") end -- NPC181.scr:124
end

script.labels["Main"] = function(ctx)
    -- NPC181.scr:127
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC181.scr:134
    ctx:addTrigger("Use", "OnUse") -- NPC181.scr:136
    do return ctx:exit("") end -- NPC181.scr:138
end

return script
