-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC194.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC194.scr
-- timmy
-- handles Hjalnek the OrcFaced voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC194.scr:19
    do return ctx:exit("") end -- NPC194.scr:24
end

script.labels["OnUse"] = function(ctx)
    -- NPC194.scr:30
    ctx:playSound("voices\\NPC\\NPC_194.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC194.scr:33
    do return ctx:exit("") end -- NPC194.scr:34
end

script.labels["OnExit"] = function(ctx)
    -- NPC194.scr:37
    do return ctx:exit("") end -- NPC194.scr:40
end

script.labels["Main"] = function(ctx)
    -- NPC194.scr:43
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC194.scr:50
    ctx:addTrigger("Use", "OnUse") -- NPC194.scr:52
    do return ctx:exit("") end -- NPC194.scr:54
end

return script
