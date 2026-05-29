-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC192.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC192.scr
-- timmy
-- handles Goti Egilssen voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC192.scr:19
    -- Gosub pledge
    do return ctx:exit("") end -- NPC192.scr:23
end

script.labels["OnUse"] = function(ctx)
    -- NPC192.scr:27
    ctx:playSound("voices\\NPC\\NPC_192.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC192.scr:30
    do return ctx:exit("") end -- NPC192.scr:31
end

script.labels["OnExit"] = function(ctx)
    -- NPC192.scr:34
    do return ctx:exit("") end -- NPC192.scr:37
end

script.labels["Main"] = function(ctx)
    -- NPC192.scr:40
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC192.scr:47
    ctx:addTrigger("Use", "OnUse") -- NPC192.scr:49
    do return ctx:exit("") end -- NPC192.scr:51
end

return script
