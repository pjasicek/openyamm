-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC140.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC140.scr
-- timmy
-- handles Ottar Gizurssen voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC140.scr:19
    do return ctx:exit("") end -- NPC140.scr:25
end

script.labels["OnUse"] = function(ctx)
    -- NPC140.scr:33
    ctx:playSound("voices\\NPC\\NPC_140.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC140.scr:36
    do return ctx:exit("") end -- NPC140.scr:37
end

script.labels["OnExit"] = function(ctx)
    -- NPC140.scr:40
    do return ctx:exit("") end -- NPC140.scr:43
end

script.labels["Main"] = function(ctx)
    -- NPC140.scr:46
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC140.scr:53
    ctx:addTrigger("Use", "OnUse") -- NPC140.scr:55
    do return ctx:exit("") end -- NPC140.scr:57
end

return script
