-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC5.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC5.scr
-- timmy
-- handles Gunnar Thjorsmith voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC5.scr:17
    mm9.gosub(script, ctx, "thjorad") -- NPC5.scr:20
    mm9.gosub(script, ctx, "Refinery") -- NPC5.scr:21
    do return ctx:exit("") end -- NPC5.scr:23
end

script.labels["Thjorad"] = function(ctx)
    -- NPC5.scr:27
    if not ctx:hasKey(464) then -- NPC5.scr:30-31
        do return ctx:exit("") end -- NPC5.scr:32
    end -- NPC5.scr:33
    if ctx:hasKey(399) then -- NPC5.scr:35-36
        ctx:takeItem(359) -- NPC5.scr:37
        ctx:giveGold(700) -- NPC5.scr:38
    end -- NPC5.scr:39
    if ctx:hasKey(400) then -- NPC5.scr:41-42
        ctx:takeItem(360) -- NPC5.scr:43
        ctx:giveGold(1500) -- NPC5.scr:44
    end -- NPC5.scr:45
    if ctx:hasKey(463) then -- NPC5.scr:47-48
        ctx:takeItem(361) -- NPC5.scr:49
        ctx:giveGold(3000) -- NPC5.scr:50
    end -- NPC5.scr:51
    ctx:takeKey(395) -- NPC5.scr:53
    ctx:takeKey(396) -- NPC5.scr:54
    ctx:takeKey(397) -- NPC5.scr:55
    ctx:takeKey(398) -- NPC5.scr:56
    ctx:takeKey(399) -- NPC5.scr:57
    ctx:takeKey(400) -- NPC5.scr:58
    ctx:takeKey(463) -- NPC5.scr:59
    ctx:takeKey(464) -- NPC5.scr:60
    do return ctx:exit("") end -- NPC5.scr:61
end

script.labels["Refinery"] = function(ctx)
    -- NPC5.scr:65
    -- Refinery Quest
    if not ctx:hasKey(9514) then -- NPC5.scr:70-71
        if ctx:hasKey(9513) then -- NPC5.scr:72-73
            ctx:takeItem(398) -- NPC5.scr:74
            ctx:giveItem(399) -- NPC5.scr:75
            ctx:giveKey(9514) -- NPC5.scr:76
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC5.scr:77
            do return ctx:exit("") end -- NPC5.scr:78
        end -- NPC5.scr:79
    end -- NPC5.scr:80
    do return ctx:exit("") end -- NPC5.scr:81
    -- End Refinery Quest
    do return ctx:exit("") end -- NPC5.scr:87
end

script.labels["OnUse"] = function(ctx)
    -- NPC5.scr:93
    if ctx:hasItem(359) then -- NPC5.scr:96-97
        ctx:giveKey(395) -- NPC5.scr:98
        ctx:giveKey(396) -- NPC5.scr:99
    end -- NPC5.scr:100
    if ctx:hasItem(360) then -- NPC5.scr:102-103
        ctx:giveKey(395) -- NPC5.scr:104
        ctx:giveKey(397) -- NPC5.scr:105
    end -- NPC5.scr:106
    if ctx:hasItem(361) then -- NPC5.scr:108-109
        ctx:giveKey(395) -- NPC5.scr:110
        ctx:giveKey(398) -- NPC5.scr:111
    end -- NPC5.scr:112
    ctx:command("playsound", "voices\\NPC\\NPC_005.wav, DoNothing, 100, 240, FALSE, 100") -- NPC5.scr:114
    do return ctx:exit("") end -- NPC5.scr:115
end

script.labels["Main"] = function(ctx)
    -- NPC5.scr:120
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC5.scr:127
    ctx:addTrigger("Use", "OnUse") -- NPC5.scr:129
    do return ctx:exit("") end -- NPC5.scr:131
end

return script
