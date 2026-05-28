-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC244.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC244.scr
-- timmy
-- handles Bikki Yrsadotir voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC244.scr:19
    mm9.gosub(script, ctx, "Prize") -- NPC244.scr:22
    do return ctx:exit("") end -- NPC244.scr:25
end

script.labels["Prize"] = function(ctx)
    -- NPC244.scr:32
    -- Prize Quest
    ctx:hasKey(186, "keycheck") -- NPC244.scr:38
    if ctx:condition("keycheck==0") then -- NPC244.scr:39
        -- checks to see if they already have got the reward.
        if ctx:hasKey(95) then -- NPC244.scr:41-42
            -- checks to see if they've given the prize
            ctx:giveKey(186) -- NPC244.scr:44
            ctx:giveExp(53000) -- NPC244.scr:45
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC244.scr:46
            ctx:takeItem(395) -- NPC244.scr:47
            -- gives reward
            do return ctx:exit("") end -- NPC244.scr:50
        end -- NPC244.scr:51
    end -- NPC244.scr:52
    do return ctx:exit("") end -- NPC244.scr:54
    -- End Prize Quest
    do return ctx:exit("") end -- NPC244.scr:59
end

script.labels["OnUse"] = function(ctx)
    -- NPC244.scr:65
    ctx:command("playsound", "voices\\NPC\\NPC_244.wav, Onexit, 100, 240, FALSE, 100") -- NPC244.scr:68
    do return ctx:exit("") end -- NPC244.scr:69
end

script.labels["OnExit"] = function(ctx)
    -- NPC244.scr:72
    do return ctx:exit("") end -- NPC244.scr:75
end

script.labels["Main"] = function(ctx)
    -- NPC244.scr:78
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC244.scr:85
    ctx:addTrigger("Use", "OnUse") -- NPC244.scr:87
    do return ctx:exit("") end -- NPC244.scr:89
end

return script
