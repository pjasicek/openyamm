-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC183.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC183.scr
-- timmy
-- handles Skulki the Dark voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC183.scr:19
    mm9.gosub(script, ctx, "GiveLich") -- NPC183.scr:22
    do return ctx:exit("") end -- NPC183.scr:25
end

script.labels["GiveLich"] = function(ctx)
    -- NPC183.scr:29
    if ctx:hasKey(295) then -- NPC183.scr:32-33
        if ctx:hasItem(245) then -- NPC183.scr:34-35
            do return ctx:exit("") end -- NPC183.scr:36
        end -- NPC183.scr:37
        ctx:giveItem(245) -- NPC183.scr:39
        do return ctx:exit("") end -- NPC183.scr:40
    end -- NPC183.scr:41
    do return ctx:exit("") end -- NPC183.scr:42
end

script.labels["OnUse"] = function(ctx)
    -- NPC183.scr:45
    ctx:command("playsound", "voices\\NPC\\NPC_183.wav, Onexit, 100, 240, FALSE, 100") -- NPC183.scr:48
    do return ctx:exit("") end -- NPC183.scr:49
end

script.labels["OnExit"] = function(ctx)
    -- NPC183.scr:52
    do return ctx:exit("") end -- NPC183.scr:55
end

script.labels["Main"] = function(ctx)
    -- NPC183.scr:58
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC183.scr:65
    ctx:addTrigger("Use", "OnUse") -- NPC183.scr:67
    do return ctx:exit("") end -- NPC183.scr:69
end

return script
