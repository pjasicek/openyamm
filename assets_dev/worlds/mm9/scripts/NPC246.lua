-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC246.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC246.scr
-- timmy
-- handles Erlend the Nay-Sayer voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC246.scr:19
    mm9.gosub(script, ctx, "TakeBadNews") -- NPC246.scr:22
    do return ctx:exit("") end -- NPC246.scr:25
end

script.labels["TakeBadNews"] = function(ctx)
    -- NPC246.scr:32
    -- TakeBadNews Quest
    if not ctx:hasKey(319) then -- NPC246.scr:38-39
        if ctx:hasKey(318) then -- NPC246.scr:40-41
            ctx:giveKey(319) -- NPC246.scr:42
            ctx:takeItem(251) -- NPC246.scr:43
            do return ctx:exit("") end -- NPC246.scr:44
        end -- NPC246.scr:45
    end -- NPC246.scr:46
    -- End TakeBadNews Quest
    do return ctx:exit("") end -- NPC246.scr:50
end

script.labels["OnUse"] = function(ctx)
    -- NPC246.scr:56
    -- Playsound voices\NPC\NPC_246.wav, Onexit, 100, 240, FALSE, 100
    do return ctx:exit("") end -- NPC246.scr:60
end

script.labels["OnExit"] = function(ctx)
    -- NPC246.scr:63
    do return ctx:exit("") end -- NPC246.scr:66
end

script.labels["Main"] = function(ctx)
    -- NPC246.scr:69
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC246.scr:76
    ctx:addTrigger("Use", "OnUse") -- NPC246.scr:78
    do return ctx:exit("") end -- NPC246.scr:80
end

return script
