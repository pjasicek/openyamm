-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC196.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- NPC196.scr
-- timmy
-- handles Isht'ool De'orcan voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC196.scr:19
    mm9.gosub(script, ctx, "pledge") -- NPC196.scr:22
    do return ctx:exit("") end -- NPC196.scr:23
end

script.labels["OnUse"] = function(ctx)
    -- NPC196.scr:29
    ctx:command("playsound", "voices\\NPC\\NPC_196.wav, Onexit, 100, 240, FALSE, 100") -- NPC196.scr:32
    do return ctx:exit("") end -- NPC196.scr:33
end

script.labels["OnExit"] = function(ctx)
    -- NPC196.scr:36
    do return ctx:exit("") end -- NPC196.scr:39
end

script.labels["Main"] = function(ctx)
    -- NPC196.scr:42
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC196.scr:49
    ctx:addTrigger("Use", "OnUse") -- NPC196.scr:51
    do return ctx:exit("") end -- NPC196.scr:53
end

return script
