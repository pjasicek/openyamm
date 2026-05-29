-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC417.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC417.scr
-- timmy
-- handles Chadwick Boorsley voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC417.scr:13
    mm9.gosub(script, ctx, "Secrets") -- NPC417.scr:16
    do return ctx:exit("") end -- NPC417.scr:17
end

script.labels["Secrets"] = function(ctx)
    -- NPC417.scr:21
    -- secrets Quest
    if not ctx:hasKey(247) then -- NPC417.scr:27-28
        if ctx:hasKey(246) then -- NPC417.scr:29-30
            ctx:giveExp(10000) -- NPC417.scr:31
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NPC417.scr:32
            ctx:giveKey(247) -- NPC417.scr:33
            do return ctx:exit("") end -- NPC417.scr:34
        end -- NPC417.scr:35
    end -- NPC417.scr:36
    do return ctx:exit("") end -- NPC417.scr:37
    -- End secrets quest
    do return ctx:exit("") end -- NPC417.scr:41
end

script.labels["OnTrap"] = function(ctx)
    -- NPC417.scr:45
    if ctx:hasKey(243) then -- NPC417.scr:47-48
        ctx:state().Trap = true -- NPC417.scr:49
        ctx:giveKey(244) -- NPC417.scr:50
        do return ctx:exit("") end -- NPC417.scr:51
    end -- NPC417.scr:52
    do return ctx:exit("") end -- NPC417.scr:53
end

script.labels["OnRemove"] = function(ctx)
    -- NPC417.scr:56
    if ctx:hasKey(243) then -- NPC417.scr:60-61
        ctx:takeKey(244) -- NPC417.scr:62
        ctx:state().Trap = false -- NPC417.scr:63
        do return ctx:exit("") end -- NPC417.scr:64
    end -- NPC417.scr:65
    do return ctx:exit("") end -- NPC417.scr:66
end

script.labels["OnFinish"] = function(ctx)
    -- NPC417.scr:69
    if ctx:hasKey(243) then -- NPC417.scr:71-72
        if ctx:condition("Trap==false") then -- NPC417.scr:73
            ctx:giveKey(245) -- NPC417.scr:74
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NPC417.scr:75
            do return ctx:exit("") end -- NPC417.scr:76
        end -- NPC417.scr:77
    end -- NPC417.scr:78
    do return ctx:exit("") end -- NPC417.scr:79
end

script.labels["OnUse"] = function(ctx)
    -- NPC417.scr:82
    ctx:playSound("voices\\NPC\\NPC_189.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC417.scr:85
    do return ctx:exit("") end -- NPC417.scr:86
end

script.labels["Init"] = function(ctx)
    -- NPC417.scr:89
    -- gosub OnRemove
    ctx:takeKey(243) -- NPC417.scr:95
    ctx:takeKey(244) -- NPC417.scr:96
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC417.scr:98
    ctx:addTrigger("Use", "OnUse") -- NPC417.scr:99
    ctx:addTrigger("DoTrap", "OnTrap") -- NPC417.scr:100
    ctx:addTrigger("RemoveTrap", "OnRemove") -- NPC417.scr:101
    ctx:addTrigger("done", "OnFinish") -- NPC417.scr:102
    do return ctx:exit("") end -- NPC417.scr:103
end

script.labels["Init2"] = function(ctx)
    -- NPC417.scr:106
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC417.scr:111
    ctx:addTrigger("Use", "OnUse") -- NPC417.scr:112
    ctx:addTrigger("DoTrap", "OnTrap") -- NPC417.scr:113
    ctx:addTrigger("RemoveTrap", "OnRemove") -- NPC417.scr:114
    ctx:addTrigger("done", "OnFinish") -- NPC417.scr:115
    do return ctx:exit("") end -- NPC417.scr:116
end

script.labels["Main"] = function(ctx)
    -- NPC417.scr:119
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC417.scr:125
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC417.scr:126
    ctx:onEvent("OnPostSaveLoad", "Init2") -- NPC417.scr:127
    ctx:wait(1, .1, "Init") -- NPC417.scr:128
    do return ctx:exit("") end -- NPC417.scr:131
end

return script
