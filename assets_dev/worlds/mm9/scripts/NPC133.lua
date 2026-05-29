-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC133.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC133.scr
-- timmy
-- handles Thorir Mouth voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC133.scr:19
    if not ctx:hasKey(490) then -- NPC133.scr:22-23
        if ctx:hasKey(488) then -- NPC133.scr:24-25
            ctx:takeItem(362) -- NPC133.scr:26
            ctx:takeItem(363) -- NPC133.scr:27
            ctx:takeItem(364) -- NPC133.scr:28
            ctx:takeItem(365) -- NPC133.scr:29
            ctx:takeItem(366) -- NPC133.scr:30
            ctx:takeItem(367) -- NPC133.scr:31
            ctx:giveKey(490) -- NPC133.scr:32
        end -- NPC133.scr:33
    end -- NPC133.scr:34
    mm9.gosub(script, ctx, "Nicolai") -- NPC133.scr:36
    mm9.gosub(script, ctx, "Capstone") -- NPC133.scr:37
    do return ctx:exit("") end -- NPC133.scr:39
end

script.labels["Capstone"] = function(ctx)
    -- NPC133.scr:43
    if ctx:hasKey(188) then -- NPC133.scr:46-47
        do return ctx:exit("") end -- NPC133.scr:48
    end -- NPC133.scr:49
    if ctx:hasKey(488) then -- NPC133.scr:52-53
        ctx:giveItem(396) -- NPC133.scr:54
        -- gives player finished quest key
        ctx:giveKey("", 188) -- NPC133.scr:55
        ctx:giveExp(146000) -- NPC133.scr:56
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC133.scr:57
        do return ctx:exit("") end -- NPC133.scr:58
    end -- NPC133.scr:59
    do return ctx:exit("") end -- NPC133.scr:61
end

script.labels["Nicolai"] = function(ctx)
    -- NPC133.scr:64
    -- Thjorad Quest
    if ctx:hasKey(122) then -- NPC133.scr:70-71
        do return ctx:exit("") end -- NPC133.scr:72
    end -- NPC133.scr:73
    if ctx:hasKey(121) then -- NPC133.scr:75-76
        ctx:giveGold(5000) -- NPC133.scr:77
        ctx:giveExp(20000) -- NPC133.scr:78
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC133.scr:79
        ctx:giveKey(122) -- NPC133.scr:80
        do return ctx:exit("") end -- NPC133.scr:81
    end -- NPC133.scr:82
    -- End thjorad quest
    do return ctx:exit("") end -- NPC133.scr:87
end

script.labels["ItemCheck"] = function(ctx)
    -- NPC133.scr:92
    -- Checks to see if the player has all the prize set.
    ctx:state().g_ncounter = 0 -- NPC133.scr:95
    if ctx:hasItem(362) then -- NPC133.scr:97-98
        ctx:set("g_ncounter", "g_ncounter + 1") -- NPC133.scr:99
    end -- NPC133.scr:100
    if ctx:hasItem(363) then -- NPC133.scr:102-103
        ctx:set("g_ncounter", "g_ncounter + 1") -- NPC133.scr:104
    end -- NPC133.scr:105
    if ctx:hasItem(364) then -- NPC133.scr:108-109
        ctx:set("g_ncounter", "g_ncounter + 1") -- NPC133.scr:110
    end -- NPC133.scr:111
    if ctx:hasItem(365) then -- NPC133.scr:114-115
        ctx:set("g_ncounter", "g_ncounter + 1") -- NPC133.scr:116
    end -- NPC133.scr:117
    if ctx:hasItem(366) then -- NPC133.scr:120-121
        ctx:set("g_ncounter", "g_ncounter + 1") -- NPC133.scr:122
    end -- NPC133.scr:123
    if ctx:hasItem(367) then -- NPC133.scr:126-127
        ctx:set("g_ncounter", "g_ncounter + 1") -- NPC133.scr:128
    end -- NPC133.scr:129
    if ctx:condition("g_ncounter==6") then -- NPC133.scr:131
        ctx:giveKey(487) -- NPC133.scr:132
    end -- NPC133.scr:133
    do return ctx:exit("") end -- NPC133.scr:137
end

script.labels["OnUse"] = function(ctx)
    -- NPC133.scr:139
    mm9.gosub(script, ctx, "ItemCheck") -- NPC133.scr:143
    ctx:playSound("voices\\NPC\\NPC_133.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC133.scr:145
    do return ctx:exit("") end -- NPC133.scr:146
end

script.labels["OnExit"] = function(ctx)
    -- NPC133.scr:149
    do return ctx:exit("") end -- NPC133.scr:152
end

script.labels["Main"] = function(ctx)
    -- NPC133.scr:155
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC133.scr:162
    ctx:addTrigger("Use", "OnUse") -- NPC133.scr:163
    do return ctx:exit("") end -- NPC133.scr:165
end

return script
