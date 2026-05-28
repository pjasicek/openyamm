-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC339.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC339.scr
-- timmy
-- handles Jokull the Ugly voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC339.scr:19
    mm9.gosub(script, ctx, "Bathhouse") -- NPC339.scr:22
    do return ctx:exit("") end -- NPC339.scr:25
end

script.labels["Bathhouse"] = function(ctx)
    -- NPC339.scr:29
    -- Bathhouse Quest
    if not ctx:hasKey(352) then -- NPC339.scr:35-36
        if ctx:hasKey(351) then -- NPC339.scr:37-38
            ctx:giveExp(80000) -- NPC339.scr:39
            ctx:giveGold(5000) -- NPC339.scr:40
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC339.scr:41
            ctx:giveKey(352) -- NPC339.scr:42
            do return ctx:exit("") end -- NPC339.scr:43
        end -- NPC339.scr:44
    end -- NPC339.scr:45
    -- End Bathhouse quest
    do return ctx:exit("") end -- NPC339.scr:50
end

script.labels["OnUse"] = function(ctx)
    -- NPC339.scr:57
    ctx:command("playsound", "voices\\NPC\\NPC_339.wav, Onexit, 100, 240, FALSE, 100") -- NPC339.scr:60
    do return ctx:exit("") end -- NPC339.scr:61
end

script.labels["OnExit"] = function(ctx)
    -- NPC339.scr:64
    do return ctx:exit("") end -- NPC339.scr:67
end

script.labels["Main"] = function(ctx)
    -- NPC339.scr:70
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC339.scr:77
    ctx:addTrigger("Use", "OnUse") -- NPC339.scr:79
    do return ctx:exit("") end -- NPC339.scr:81
end

return script
