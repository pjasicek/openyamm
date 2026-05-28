-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC96.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC96.scr
-- timmy
-- handles Greudach A'Dorad voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC96.scr:19
    mm9.gosub(script, ctx, "thjorad") -- NPC96.scr:22
    mm9.gosub(script, ctx, "Refinery") -- NPC96.scr:23
    do return ctx:exit("") end -- NPC96.scr:25
end

script.labels["Thjorad"] = function(ctx)
    -- NPC96.scr:29
    -- Thjorad Quest
    -- End thjorad quest
    do return ctx:exit("") end -- NPC96.scr:40
end

script.labels["Refinery"] = function(ctx)
    -- NPC96.scr:44
    -- Refinery Quest
    -- End Refinery Quest
    do return ctx:exit("") end -- NPC96.scr:55
end

script.labels["OnUse"] = function(ctx)
    -- NPC96.scr:61
    ctx:command("playsound", "voices\\NPC\\NPC_096.wav, Onexit, 100, 240, FALSE, 100") -- NPC96.scr:64
    do return ctx:exit("") end -- NPC96.scr:65
end

script.labels["OnExit"] = function(ctx)
    -- NPC96.scr:68
    do return ctx:exit("") end -- NPC96.scr:71
end

script.labels["Main"] = function(ctx)
    -- NPC96.scr:74
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC96.scr:81
    ctx:addTrigger("Use", "OnUse") -- NPC96.scr:83
    do return ctx:exit("") end -- NPC96.scr:85
end

return script
