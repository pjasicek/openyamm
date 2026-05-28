-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC197.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- NPC197.scr
-- timmy
-- handles Rannveig the Elvish voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC197.scr:19
    mm9.gosub(script, ctx, "pledge") -- NPC197.scr:22
    do return ctx:exit("") end -- NPC197.scr:24
end

script.labels["OnUse"] = function(ctx)
    -- NPC197.scr:28
    ctx:command("playsound", "voices\\NPC\\NPC_197.wav, Onexit, 100, 240, FALSE, 100") -- NPC197.scr:31
    do return ctx:exit("") end -- NPC197.scr:32
end

script.labels["OnExit"] = function(ctx)
    -- NPC197.scr:35
    do return ctx:exit("") end -- NPC197.scr:38
end

script.labels["Main"] = function(ctx)
    -- NPC197.scr:41
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC197.scr:48
    ctx:addTrigger("Use", "OnUse") -- NPC197.scr:50
    do return ctx:exit("") end -- NPC197.scr:52
end

return script
