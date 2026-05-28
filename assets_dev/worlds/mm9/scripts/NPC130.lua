-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC130.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC130.scr
-- timmy
-- handles Ivan the Smart voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC130.scr:19
    mm9.gosub(script, ctx, "Trivia") -- NPC130.scr:22
    do return ctx:exit("") end -- NPC130.scr:24
end

script.labels["Trivia"] = function(ctx)
    -- NPC130.scr:28
    -- Trivia Quest
    ctx:hasKey(164, "keycheck") -- NPC130.scr:34
    if ctx:condition("keycheck==0") then -- NPC130.scr:35
        -- checks to see if they already have got the reward.
        if ctx:hasKey(60) then -- NPC130.scr:37-38
            -- checks to see if they've Beat Ivan the Smart
            ctx:giveKey(164) -- NPC130.scr:40
            ctx:giveExp(5000) -- NPC130.scr:41
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC130.scr:42
            ctx:giveItem(400) -- NPC130.scr:43
            -- gives reward
            do return ctx:exit("") end -- NPC130.scr:46
        end -- NPC130.scr:47
    end -- NPC130.scr:48
    do return ctx:exit("") end -- NPC130.scr:50
    -- End trivia quest
    do return ctx:exit("") end -- NPC130.scr:55
end

script.labels["OnUse"] = function(ctx)
    -- NPC130.scr:62
    ctx:command("playsound", "voices\\NPC\\NPC_130.wav, Onexit, 100, 240, FALSE, 100") -- NPC130.scr:65
    do return ctx:exit("") end -- NPC130.scr:66
end

script.labels["OnExit"] = function(ctx)
    -- NPC130.scr:69
    do return ctx:exit("") end -- NPC130.scr:72
end

script.labels["Main"] = function(ctx)
    -- NPC130.scr:75
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC130.scr:82
    -- Addtrigger Use, OnUse
    do return ctx:exit("") end -- NPC130.scr:86
end

return script
