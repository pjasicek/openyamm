-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PLEDGE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- pledge.inc
-- timmy
-- handles checking to see if the party got 7 pledges
script.labels["reward"] = function(ctx)
    -- PLEDGE.inc:20
    -- gives reward for uniting the clans
    if not ctx:hasKey(277) then -- PLEDGE.inc:27-28
        ctx:giveKey(277) -- PLEDGE.inc:29
        ctx:giveExp(5000) -- PLEDGE.inc:30
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- PLEDGE.inc:31
        ctx:state().BeenDone = true -- PLEDGE.inc:32
        do return ctx:exit("") end -- PLEDGE.inc:33
    end -- PLEDGE.inc:34
    do return ctx:exit("") end -- PLEDGE.inc:35
end

script.labels["Pledge"] = function(ctx)
    -- PLEDGE.inc:38
    if not ctx:hasKey(265) then -- PLEDGE.inc:41-42
        do return ctx:exit("") end -- PLEDGE.inc:43
    else -- PLEDGE.inc:44
        if not ctx:hasKey(277) then -- PLEDGE.inc:46-47
            if ctx:hasKey(269) then -- PLEDGE.inc:49-50
                ctx:arrayPut("PledgeArray", 0, 1) -- PLEDGE.inc:51
            end -- PLEDGE.inc:52
            if ctx:hasKey(270) then -- PLEDGE.inc:54-55
                ctx:arrayPut("PledgeArray", 1, 1) -- PLEDGE.inc:56
            end -- PLEDGE.inc:57
            if ctx:hasKey(271) then -- PLEDGE.inc:59-60
                ctx:arrayPut("PledgeArray", 2, 1) -- PLEDGE.inc:61
            end -- PLEDGE.inc:62
            if ctx:hasKey(272) then -- PLEDGE.inc:64-65
                ctx:arrayPut("PledgeArray", 3, 1) -- PLEDGE.inc:66
            end -- PLEDGE.inc:67
            if ctx:hasKey(273) then -- PLEDGE.inc:69-70
                ctx:arrayPut("PledgeArray", 4, 1) -- PLEDGE.inc:71
            end -- PLEDGE.inc:72
            if ctx:hasKey(274) then -- PLEDGE.inc:74-75
                ctx:arrayPut("PledgeArray", 5, 1) -- PLEDGE.inc:76
            end -- PLEDGE.inc:77
            if ctx:hasKey(275) then -- PLEDGE.inc:79-80
                ctx:arrayPut("PledgeArray", 6, 1) -- PLEDGE.inc:81
            end -- PLEDGE.inc:82
            if ctx:hasKey(276) then -- PLEDGE.inc:84-85
                ctx:arrayPut("PledgeArray", 7, 1) -- PLEDGE.inc:86
            end -- PLEDGE.inc:87
        end -- PLEDGE.inc:88
    end -- PLEDGE.inc:89
    mm9.gosub(script, ctx, "CheckAllNPC") -- PLEDGE.inc:90
    do return ctx:exit("") end -- PLEDGE.inc:91
end

script.labels["CheckAllNPC"] = function(ctx)
    -- PLEDGE.inc:94
    if ctx:condition("BeenDone==true") then -- PLEDGE.inc:98
        do return ctx:exit("") end -- PLEDGE.inc:99
    end -- PLEDGE.inc:100
    ctx:state().counter = 0 -- PLEDGE.inc:102
    ctx:state().NoDice = 0 -- PLEDGE.inc:103
end

script.labels["CheckAllNPCloop"] = function(ctx)
    -- PLEDGE.inc:107
    if ctx:condition("NODice>1") then -- PLEDGE.inc:110
        do return ctx:exit("") end -- PLEDGE.inc:111
    end -- PLEDGE.inc:112
    ctx:arrayGet("PledgeArray", "counter", "GivePledge") -- PLEDGE.inc:115
    if ctx:condition("GivePledge==false") then -- PLEDGE.inc:116
        ctx:state().NoDice = (tonumber(ctx:state().NoDice) or 0) + 1 -- PLEDGE.inc:117
    end -- PLEDGE.inc:118
    ctx:state().Counter = (tonumber(ctx:state().Counter) or 0) + 1 -- PLEDGE.inc:120
    if ctx:condition("counter<7") then -- PLEDGE.inc:122
        do return mm9.gotoLabel(script, ctx, "CheckAllNPCloop") end -- PLEDGE.inc:123
    end -- PLEDGE.inc:124
    -- ...........success.............
    mm9.gosub(script, ctx, "reward") -- PLEDGE.inc:129
    do return ctx:exit("") end -- PLEDGE.inc:130
end

return script
