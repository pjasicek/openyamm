-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC182.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC182.scr
-- timmy
-- handles Menja Ketildotir voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC182.scr:19
    do return ctx:exit("") end -- NPC182.scr:24
end

script.labels["OnUse"] = function(ctx)
    -- NPC182.scr:29
    ctx:playSound("voices\\NPC\\NPC_182.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC182.scr:32
    do return ctx:exit("") end -- NPC182.scr:33
end

script.labels["OnExit"] = function(ctx)
    -- NPC182.scr:36
    do return ctx:exit("") end -- NPC182.scr:39
end

script.labels["Main"] = function(ctx)
    -- NPC182.scr:42
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC182.scr:49
    ctx:addTrigger("Use", "OnUse") -- NPC182.scr:51
    do return ctx:exit("") end -- NPC182.scr:53
end

return script
