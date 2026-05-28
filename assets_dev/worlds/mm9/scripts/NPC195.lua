-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC195.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- NPC195.scr
-- timmy
-- handles Tjorvi the bold voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC195.scr:19
    mm9.gosub(script, ctx, "pledge") -- NPC195.scr:22
    do return ctx:exit("") end -- NPC195.scr:24
end

script.labels["OnUse"] = function(ctx)
    -- NPC195.scr:30
    ctx:command("playsound", "voices\\NPC\\NPC_195.wav, Onexit, 100, 240, FALSE, 100") -- NPC195.scr:33
    do return ctx:exit("") end -- NPC195.scr:34
end

script.labels["OnExit"] = function(ctx)
    -- NPC195.scr:37
    do return ctx:exit("") end -- NPC195.scr:40
end

script.labels["Main"] = function(ctx)
    -- NPC195.scr:43
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC195.scr:50
    ctx:addTrigger("Use", "OnUse") -- NPC195.scr:52
    do return ctx:exit("") end -- NPC195.scr:54
end

return script
