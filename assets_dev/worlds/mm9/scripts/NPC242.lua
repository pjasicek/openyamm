-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC242.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC242.scr
-- timmy
-- handles Dagfari the Peevish voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC242.scr:11
    mm9.gosub(script, ctx, "GiveBadNews") -- NPC242.scr:14
    mm9.gosub(script, ctx, "Reward") -- NPC242.scr:15
    do return ctx:exit("") end -- NPC242.scr:17
end

script.labels["Reward"] = function(ctx)
    -- NPC242.scr:22
    -- Reward Quest
    if not ctx:hasKey(321) then -- NPC242.scr:28-29
        if ctx:hasKey(320) then -- NPC242.scr:30-31
            ctx:giveKey(321) -- NPC242.scr:32
            ctx:giveExp(5000) -- NPC242.scr:33
            ctx:giveGold(5000) -- NPC242.scr:34
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC242.scr:35
            do return ctx:exit("") end -- NPC242.scr:36
        end -- NPC242.scr:37
    end -- NPC242.scr:38
    -- End BadNews Quest
    do return ctx:exit("") end -- NPC242.scr:43
end

script.labels["GiveBadNews"] = function(ctx)
    -- NPC242.scr:49
    -- BadNews Quest
    if not ctx:hasKey(317) then -- NPC242.scr:55-56
        if ctx:hasKey(316) then -- NPC242.scr:57-58
            ctx:giveItem(251) -- NPC242.scr:59
            ctx:giveKey(317) -- NPC242.scr:60
            do return ctx:exit("") end -- NPC242.scr:61
        end -- NPC242.scr:62
    end -- NPC242.scr:63
    -- End BadNews Quest
    do return ctx:exit("") end -- NPC242.scr:67
end

script.labels["OnUse"] = function(ctx)
    -- NPC242.scr:73
    ctx:command("playsound", "voices\\NPC\\NPC_242.wav, Onexit, 100, 240, FALSE, 100") -- NPC242.scr:76
    do return ctx:exit("") end -- NPC242.scr:77
end

script.labels["OnExit"] = function(ctx)
    -- NPC242.scr:80
    do return ctx:exit("") end -- NPC242.scr:83
end

script.labels["Main"] = function(ctx)
    -- NPC242.scr:86
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC242.scr:93
    ctx:addTrigger("Use", "OnUse") -- NPC242.scr:95
    do return ctx:exit("") end -- NPC242.scr:97
end

return script
