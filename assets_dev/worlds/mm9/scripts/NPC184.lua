-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC184.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC184.scr
-- timmy
-- handles Brewmaster Smith voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC184.scr:11
    mm9.gosub(script, ctx, "givekeg") -- NPC184.scr:14
    mm9.gosub(script, ctx, "Reward") -- NPC184.scr:15
    mm9.gosub(script, ctx, "BadReward") -- NPC184.scr:16
    do return ctx:exit("") end -- NPC184.scr:17
end

script.labels["GiveKeg"] = function(ctx)
    -- NPC184.scr:21
    -- GiveKeg Quest
    if not ctx:hasKey(303) then -- NPC184.scr:27-28
        if ctx:hasKey(302) then -- NPC184.scr:29-30
            ctx:giveKey(303) -- NPC184.scr:31
            ctx:giveItem(249) -- NPC184.scr:32
            do return ctx:exit("") end -- NPC184.scr:33
        end -- NPC184.scr:34
    end -- NPC184.scr:35
    do return ctx:exit("") end -- NPC184.scr:36
    -- End GiveKeg quest
    do return ctx:exit("") end -- NPC184.scr:41
end

script.labels["Reward"] = function(ctx)
    -- NPC184.scr:45
    -- Reward Quest
    if not ctx:hasKey(308) then -- NPC184.scr:51-52
        if ctx:hasKey(307) then -- NPC184.scr:53-54
            ctx:giveKey(308) -- NPC184.scr:55
            ctx:giveExp(20000) -- NPC184.scr:56
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC184.scr:57
            do return ctx:exit("") end -- NPC184.scr:58
        end -- NPC184.scr:59
    end -- NPC184.scr:60
    do return ctx:exit("") end -- NPC184.scr:61
    -- End Reward Quest
    do return ctx:exit("") end -- NPC184.scr:67
end

script.labels["BadReward"] = function(ctx)
    -- NPC184.scr:70
    -- Reward Quest
    if not ctx:hasKey(310) then -- NPC184.scr:76-77
        if ctx:hasKey(309) then -- NPC184.scr:78-79
            ctx:giveKey(310) -- NPC184.scr:80
            ctx:giveExp(2000) -- NPC184.scr:81
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC184.scr:82
            ctx:giveGold(200) -- NPC184.scr:83
            ctx:takeItem(249) -- NPC184.scr:84
            do return ctx:exit("") end -- NPC184.scr:85
        end -- NPC184.scr:86
    end -- NPC184.scr:87
    do return ctx:exit("") end -- NPC184.scr:88
    -- End Reward Quest
    do return ctx:exit("") end -- NPC184.scr:94
end

script.labels["OnUse"] = function(ctx)
    -- NPC184.scr:100
    ctx:command("playsound", "voices\\NPC\\NPC_184.wav, Onexit, 100, 240, FALSE, 100") -- NPC184.scr:103
    do return ctx:exit("") end -- NPC184.scr:104
end

script.labels["OnExit"] = function(ctx)
    -- NPC184.scr:107
    do return ctx:exit("") end -- NPC184.scr:110
end

script.labels["Main"] = function(ctx)
    -- NPC184.scr:113
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC184.scr:120
    ctx:addTrigger("Use", "OnUse") -- NPC184.scr:122
    do return ctx:exit("") end -- NPC184.scr:124
end

return script
