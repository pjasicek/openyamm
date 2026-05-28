-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC416.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC416.scr
-- timmy
-- handles Harris Willington voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC416.scr:19
    do return ctx:exit("") end -- NPC416.scr:23
end

script.labels["OnDeath"] = function(ctx)
    -- NPC416.scr:30
    -- Prize Quest
    ctx:giveKey(233) -- NPC416.scr:36
    do return ctx:exit("") end -- NPC416.scr:37
    -- End Prize Quest
    do return ctx:exit("") end -- NPC416.scr:42
end

script.labels["OnUse"] = function(ctx)
    -- NPC416.scr:48
    ctx:command("playsound", "voices\\NPC\\NPC_088.wav, Onexit, 100, 240, FALSE, 100") -- NPC416.scr:51
    do return ctx:exit("") end -- NPC416.scr:52
end

script.labels["OnExit"] = function(ctx)
    -- NPC416.scr:55
    do return ctx:exit("") end -- NPC416.scr:58
end

script.labels["Main"] = function(ctx)
    -- NPC416.scr:61
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC416.scr:68
    ctx:command("ondeath", "Ondeath") -- NPC416.scr:69
    ctx:addTrigger("Use", "OnUse") -- NPC416.scr:70
    do return ctx:exit("") end -- NPC416.scr:72
end

return script
