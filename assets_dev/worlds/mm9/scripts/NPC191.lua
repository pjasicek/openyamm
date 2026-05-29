-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC191.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- NPC191.scr
-- timmy
-- handles Gudrun Fyridotir voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC191.scr:19
    mm9.gosub(script, ctx, "pledge") -- NPC191.scr:22
    do return ctx:exit("") end -- NPC191.scr:23
end

script.labels["OnUse"] = function(ctx)
    -- NPC191.scr:28
    ctx:playSound("voices\\NPC\\NPC_191.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC191.scr:31
    do return ctx:exit("") end -- NPC191.scr:32
end

script.labels["OnExit"] = function(ctx)
    -- NPC191.scr:35
    do return ctx:exit("") end -- NPC191.scr:38
end

script.labels["Main"] = function(ctx)
    -- NPC191.scr:41
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC191.scr:48
    ctx:addTrigger("Use", "OnUse") -- NPC191.scr:50
    do return ctx:exit("") end -- NPC191.scr:52
end

return script
