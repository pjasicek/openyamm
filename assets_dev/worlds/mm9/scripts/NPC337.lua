-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC337.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC337.scr
-- timmy
-- handles Fre voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC337.scr:12
    mm9.gosub(script, ctx, "GoldenHonk") -- NPC337.scr:15
    do return ctx:exit("") end -- NPC337.scr:18
end

script.labels["GoldenHonk"] = function(ctx)
    -- NPC337.scr:22
    -- GoldenHonk Quest
    if not ctx:hasKey(347) then -- NPC337.scr:28-29
        if ctx:hasKey(346) then -- NPC337.scr:30-31
            ctx:giveGold(10000) -- NPC337.scr:32
            ctx:giveExp(80000) -- NPC337.scr:33
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC337.scr:34
            ctx:takeItem(369) -- NPC337.scr:35
            ctx:giveKey(347) -- NPC337.scr:36
            do return ctx:exit("") end -- NPC337.scr:37
        end -- NPC337.scr:38
    end -- NPC337.scr:39
    -- End GoldenHonk Quest
    do return ctx:exit("") end -- NPC337.scr:44
end

script.labels["OnUse"] = function(ctx)
    -- NPC337.scr:50
    ctx:command("playsound", "voices\\NPC\\NPC_337.wav, Onexit, 100, 240, FALSE, 100") -- NPC337.scr:53
    do return ctx:exit("") end -- NPC337.scr:54
end

script.labels["OnExit"] = function(ctx)
    -- NPC337.scr:57
    do return ctx:exit("") end -- NPC337.scr:60
end

script.labels["Main"] = function(ctx)
    -- NPC337.scr:63
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC337.scr:70
    ctx:addTrigger("Use", "OnUse") -- NPC337.scr:72
    do return ctx:exit("") end -- NPC337.scr:74
end

return script
