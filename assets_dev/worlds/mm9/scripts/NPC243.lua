-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC243.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC243.scr
-- timmy
-- handles Brynhildr the Moneywise voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC243.scr:19
    do return ctx:exit("") end -- NPC243.scr:25
end

script.labels["OnUse"] = function(ctx)
    -- NPC243.scr:32
    ctx:playSound("voices\\NPC\\NPC_243.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC243.scr:35
    do return ctx:exit("") end -- NPC243.scr:36
end

script.labels["OnExit"] = function(ctx)
    -- NPC243.scr:39
    do return ctx:exit("") end -- NPC243.scr:42
end

script.labels["Main"] = function(ctx)
    -- NPC243.scr:45
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC243.scr:52
    ctx:addTrigger("Use", "OnUse") -- NPC243.scr:54
    do return ctx:exit("") end -- NPC243.scr:56
end

return script
