-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC199.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- NPC199.scr
-- timmy
-- handles Erik the Fish-head voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC199.scr:19
    mm9.gosub(script, ctx, "pledge") -- NPC199.scr:22
    do return ctx:exit("") end -- NPC199.scr:25
end

script.labels["OnUse"] = function(ctx)
    -- NPC199.scr:30
    ctx:command("playsound", "voices\\NPC\\NPC_199.wav, Onexit, 100, 240, FALSE, 100") -- NPC199.scr:33
    do return ctx:exit("") end -- NPC199.scr:34
end

script.labels["OnExit"] = function(ctx)
    -- NPC199.scr:37
    do return ctx:exit("") end -- NPC199.scr:40
end

script.labels["Main"] = function(ctx)
    -- NPC199.scr:43
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC199.scr:50
    ctx:addTrigger("Use", "OnUse") -- NPC199.scr:52
    do return ctx:exit("") end -- NPC199.scr:54
end

return script
