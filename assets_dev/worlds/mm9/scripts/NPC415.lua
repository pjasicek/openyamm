-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC415.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC415.scr
-- timmy
-- handles The Dook's voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC415.scr:19
    mm9.gosub(script, ctx, "thjorad") -- NPC415.scr:22
    mm9.gosub(script, ctx, "Refinery") -- NPC415.scr:23
    do return ctx:exit("") end -- NPC415.scr:25
end

script.labels["Thjorad"] = function(ctx)
    -- NPC415.scr:29
    -- Thjorad Quest
    -- End thjorad quest
    do return ctx:exit("") end -- NPC415.scr:40
end

script.labels["Refinery"] = function(ctx)
    -- NPC415.scr:44
    -- Refinery Quest
    -- End Refinery Quest
    do return ctx:exit("") end -- NPC415.scr:55
end

script.labels["OnUse"] = function(ctx)
    -- NPC415.scr:61
    -- Playsound voices\NPC\NPC_128.wav, Onexit, 100, 240, FALSE, 100
    ctx:doRude(415) -- NPC415.scr:65
    do return ctx:exit("") end -- NPC415.scr:66
end

script.labels["OnExit"] = function(ctx)
    -- NPC415.scr:69
    do return ctx:exit("") end -- NPC415.scr:72
end

script.labels["Main"] = function(ctx)
    -- NPC415.scr:75
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC415.scr:82
    ctx:addTrigger("Use", "OnUse") -- NPC415.scr:84
    do return ctx:exit("") end -- NPC415.scr:86
end

return script
