-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC309.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC309.scr
-- timmy
-- handles Tamur Leng voice and quest stuff
-- flag variables
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC309.scr:21
    mm9.gosub(script, ctx, "StopTamur") -- NPC309.scr:24
    do return ctx:exit("") end -- NPC309.scr:27
end

script.labels["StopTamur"] = function(ctx)
    -- NPC309.scr:31
    -- Stop Tamur Quest
    if not ctx:hasKey(190) then -- NPC309.scr:39-40
        -- checks to see if they already have got the reward.
        if ctx:hasKey(106) then -- NPC309.scr:42-43
            -- checks to see if they've spoken to Krohn
            ctx:giveKey(190) -- NPC309.scr:46
            ctx:giveExp(412000) -- NPC309.scr:47
            ctx:addNpc(309, "g_hobject") -- NPC309.scr:48
            ctx:object("g_hobject"):setFlag("visible", false) -- NPC309.scr:50
            ctx:object("g_hobject"):setFlag("Solid", false) -- NPC309.scr:51
            ctx:object("g_hobject"):setFlag("gravity", false) -- NPC309.scr:52
            ctx:wait(1, 1, "Delete") -- NPC309.scr:53
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC309.scr:54
            -- gives reward
            do return ctx:exit("") end -- NPC309.scr:57
        end -- NPC309.scr:58
    end -- NPC309.scr:59
    do return ctx:exit("") end -- NPC309.scr:61
    -- End stop tamur quest
    do return ctx:exit("") end -- NPC309.scr:66
end

script.labels["Delete"] = function(ctx)
    -- NPC309.scr:69
    ctx:object("Thorolf2"):trigger("appear") -- NPC309.scr:71-72
    ctx:self():remove() -- NPC309.scr:73
    do return ctx:exit("") end -- NPC309.scr:74
end

script.labels["Vanish"] = function(ctx)
    -- NPC309.scr:77
    ctx:state().g_hobject = ctx:self() -- NPC309.scr:80
    ctx:self():setFlag("visible", false) -- NPC309.scr:81
    ctx:self():setFlag("solid", false) -- NPC309.scr:82
    ctx:self():setFlag("gravity", false) -- NPC309.scr:83
    do return ctx:exit("") end -- NPC309.scr:84
end

script.labels["OnAppear"] = function(ctx)
    -- NPC309.scr:87
    ctx:state().g_hobject = ctx:self() -- NPC309.scr:90
    ctx:self():setFlag("visible", true) -- NPC309.scr:91
    ctx:self():setFlag("solid", true) -- NPC309.scr:92
    ctx:self():setFlag("gravity", true) -- NPC309.scr:93
    do return ctx:exit("") end -- NPC309.scr:95
end

script.labels["Main"] = function(ctx)
    -- NPC309.scr:98
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC309.scr:105
    ctx:addTrigger("Appear", "OnAppear") -- NPC309.scr:106
    mm9.gosub(script, ctx, "Vanish") -- NPC309.scr:107
    do return ctx:exit("") end -- NPC309.scr:109
end

return script
