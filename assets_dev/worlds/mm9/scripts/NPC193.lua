-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC193.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- NPC193.scr
-- timmy
-- handles Tuathal A'Ghrie voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC193.scr:19
    mm9.gosub(script, ctx, "pledge") -- NPC193.scr:22
    do return ctx:exit("") end -- NPC193.scr:23
end

script.labels["OnUse"] = function(ctx)
    -- NPC193.scr:26
    ctx:playSound("voices\\NPC\\NPC_193.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC193.scr:29
    do return ctx:exit("") end -- NPC193.scr:30
end

script.labels["OnExit"] = function(ctx)
    -- NPC193.scr:33
    do return ctx:exit("") end -- NPC193.scr:36
end

script.labels["Main"] = function(ctx)
    -- NPC193.scr:39
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC193.scr:46
    ctx:addTrigger("Use", "OnUse") -- NPC193.scr:48
    do return ctx:exit("") end -- NPC193.scr:50
end

return script
