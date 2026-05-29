-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC100.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC100.scr
-- timmy
-- handles Hlif Ingimundssen voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC100.scr:19
    do return ctx:exit("") end -- NPC100.scr:25
end

script.labels["OnUse"] = function(ctx)
    -- NPC100.scr:31
    ctx:playSound("voices\\NPC\\NPC_100.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC100.scr:34
    do return ctx:exit("") end -- NPC100.scr:35
end

script.labels["OnExit"] = function(ctx)
    -- NPC100.scr:38
    do return ctx:exit("") end -- NPC100.scr:41
end

script.labels["Main"] = function(ctx)
    -- NPC100.scr:44
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC100.scr:51
    ctx:addTrigger("Use", "OnUse") -- NPC100.scr:53
    do return ctx:exit("") end -- NPC100.scr:55
end

return script
