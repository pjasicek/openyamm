-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ORB.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Orb.scr
-- timmy
-- handles checking to see if the party got 6 orbs of linking.
script.labels["reward"] = function(ctx)
    -- ORB.inc:20
    -- gives reward for uniting the clans
    if not ctx:hasKey(330) then -- ORB.inc:27-28
        ctx:giveKey(330) -- ORB.inc:29
        ctx:command("set", "BeenDone 1") -- ORB.inc:31
        do return ctx:exit("") end -- ORB.inc:32
    end -- ORB.inc:33
    do return ctx:exit("") end -- ORB.inc:34
end

script.labels["Orb"] = function(ctx)
    -- ORB.inc:37
    ctx:command("set", "NoDice, 0") -- ORB.inc:40
    if not ctx:hasKey(330) then -- ORB.inc:42-43
        if ctx:hasKey(323) then -- ORB.inc:45-46
            ctx:command("arrayput", "OrbArray, 0, 1") -- ORB.inc:47
        else -- ORB.inc:48
            ctx:command("add", "NoDice 1") -- ORB.inc:49
        end -- ORB.inc:50
        if ctx:hasKey(324) then -- ORB.inc:52-53
            ctx:command("arrayput", "OrbArray, 1, 1") -- ORB.inc:54
        else -- ORB.inc:55
            ctx:command("add", "NoDice 1") -- ORB.inc:56
        end -- ORB.inc:57
        if ctx:hasKey(325) then -- ORB.inc:59-60
            ctx:command("arrayput", "OrbArray, 2, 1") -- ORB.inc:61
        else -- ORB.inc:62
            ctx:command("add", "NoDice 1") -- ORB.inc:63
        end -- ORB.inc:64
        if ctx:hasKey(326) then -- ORB.inc:66-67
            ctx:command("arrayput", "OrbArray, 3, 1") -- ORB.inc:68
        else -- ORB.inc:69
            ctx:command("add", "NoDice 1") -- ORB.inc:70
        end -- ORB.inc:71
        if ctx:hasKey(327) then -- ORB.inc:73-74
            ctx:command("arrayput", "OrbArray, 4, 1") -- ORB.inc:75
        else -- ORB.inc:76
            ctx:command("add", "NoDice 1") -- ORB.inc:77
        end -- ORB.inc:78
        if ctx:hasKey(328) then -- ORB.inc:80-81
            ctx:command("arrayput", "OrbArray, 5, 1") -- ORB.inc:82
        else -- ORB.inc:83
            ctx:command("add", "NoDice 1") -- ORB.inc:84
        end -- ORB.inc:85
        if ctx:hasKey(329) then -- ORB.inc:87-88
            ctx:command("arrayput", "OrbArray, 6, 1") -- ORB.inc:89
        else -- ORB.inc:90
            ctx:command("add", "NoDice 1") -- ORB.inc:91
        end -- ORB.inc:92
    end -- ORB.inc:93
    mm9.gosub(script, ctx, "CheckAllorb") -- ORB.inc:95
    do return ctx:exit("") end -- ORB.inc:96
end

script.labels["CheckAllorb"] = function(ctx)
    -- ORB.inc:99
    if ctx:condition("NODice>=2") then -- ORB.inc:102
        do return ctx:exit("") end -- ORB.inc:103
    end -- ORB.inc:104
    if ctx:condition("BeenDone==1") then -- ORB.inc:107
        do return ctx:exit("") end -- ORB.inc:108
    end -- ORB.inc:109
    ctx:command("set", "counter, 0") -- ORB.inc:111
end

script.labels["CheckAllOrbloop"] = function(ctx)
    -- ORB.inc:116
    ctx:command("arrayget", "OrbArray, counter, GiveOrb") -- ORB.inc:121
    if ctx:condition("GiveOrb==false") then -- ORB.inc:122
    end -- ORB.inc:123
    ctx:command("add", "Counter, 1") -- ORB.inc:125
    if ctx:condition("counter<6") then -- ORB.inc:127
        do return mm9.gotoLabel(script, ctx, "CheckAllOrbloop") end -- ORB.inc:128
    end -- ORB.inc:129
    -- ...........success.............
    mm9.gosub(script, ctx, "reward") -- ORB.inc:134
    do return ctx:exit("") end -- ORB.inc:135
end

return script
