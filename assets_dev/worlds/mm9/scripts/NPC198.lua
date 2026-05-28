-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC198.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC198.scr
-- timmy
-- handles Fyri the Black-heart voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC198.scr:19
    do return ctx:exit("") end -- NPC198.scr:24
end

script.labels["OnUse"] = function(ctx)
    -- NPC198.scr:29
    ctx:command("playsound", "voices\\NPC\\NPC_198.wav, Onexit, 100, 240, FALSE, 100") -- NPC198.scr:32
    do return ctx:exit("") end -- NPC198.scr:33
end

script.labels["OnExit"] = function(ctx)
    -- NPC198.scr:36
    do return ctx:exit("") end -- NPC198.scr:39
end

script.labels["Main"] = function(ctx)
    -- NPC198.scr:42
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC198.scr:49
    ctx:addTrigger("Use", "OnUse") -- NPC198.scr:51
    do return ctx:exit("") end -- NPC198.scr:53
end

return script
