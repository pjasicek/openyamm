-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MONKSOUNDS.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- monksounds.inc
-- timmy
-- 10/30
-- randomizes guard idle sounds.
script.labels["OnPray"] = function(ctx)
    -- MONKSOUNDS.inc:20
    if ctx:condition("Is_Playing==TRUE") then -- MONKSOUNDS.inc:23
        do return ctx:exit("") end -- MONKSOUNDS.inc:24
    end -- MONKSOUNDS.inc:25
    ctx:randomInt(1, 10, "G_ntemp") -- MONKSOUNDS.inc:27
    if ctx:condition("g_ntemp==1") then -- MONKSOUNDS.inc:29
        ctx:playSound("Sounds\\AnimSounds\\Monk\\Pray1.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", "nVolume") -- MONKSOUNDS.inc:30
        ctx:state().Is_Playing = true -- MONKSOUNDS.inc:31
        ctx:wait(1, 2.2, "OnStop") -- MONKSOUNDS.inc:32
        do return ctx:exit("") end -- MONKSOUNDS.inc:33
    end -- MONKSOUNDS.inc:34
    if ctx:condition("g_ntemp==2") then -- MONKSOUNDS.inc:36
        ctx:playSound("Sounds\\AnimSounds\\Monk\\Pray2.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", "nVolume") -- MONKSOUNDS.inc:37
        ctx:state().Is_Playing = true -- MONKSOUNDS.inc:38
        ctx:wait(1, 2.2, "OnStop") -- MONKSOUNDS.inc:39
        do return ctx:exit("") end -- MONKSOUNDS.inc:40
    end -- MONKSOUNDS.inc:41
    if ctx:condition("g_ntemp==3") then -- MONKSOUNDS.inc:43
        ctx:playSound("Sounds\\AnimSounds\\Monk\\Pray3.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", "nVolume") -- MONKSOUNDS.inc:44
        ctx:state().Is_Playing = true -- MONKSOUNDS.inc:45
        ctx:wait(1, 2.2, "OnStop") -- MONKSOUNDS.inc:46
        do return ctx:exit("") end -- MONKSOUNDS.inc:47
    end -- MONKSOUNDS.inc:48
    if ctx:condition("g_ntemp==4") then -- MONKSOUNDS.inc:50
        ctx:playSound("Sounds\\AnimSounds\\Monk\\Pray4.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", "nVolume") -- MONKSOUNDS.inc:51
        ctx:state().Is_Playing = true -- MONKSOUNDS.inc:52
        ctx:wait(1, 2.2, "OnStop") -- MONKSOUNDS.inc:53
        do return ctx:exit("") end -- MONKSOUNDS.inc:54
    end -- MONKSOUNDS.inc:55
    if ctx:condition("g_ntemp>4") then -- MONKSOUNDS.inc:59
        ctx:state().Is_Playing = true -- MONKSOUNDS.inc:61
        ctx:wait(1, 20, "ONStop") -- MONKSOUNDS.inc:62
        do return ctx:exit("") end -- MONKSOUNDS.inc:63
    end -- MONKSOUNDS.inc:64
    do return ctx:exit("") end -- MONKSOUNDS.inc:66
end

script.labels["OnSweep"] = function(ctx)
    -- MONKSOUNDS.inc:69
    if ctx:condition("Is_Sleeping==TRUE") then -- MONKSOUNDS.inc:73
        do return ctx:exit("") end -- MONKSOUNDS.inc:74
    end -- MONKSOUNDS.inc:75
    ctx:playSound("Sounds\\AnimSounds\\Monk\\Sweep.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", "nVolume") -- MONKSOUNDS.inc:77
    ctx:state().Is_Sleeping = true -- MONKSOUNDS.inc:78
    ctx:wait(1, 1, "OnStop") -- MONKSOUNDS.inc:79
    do return ctx:exit("") end -- MONKSOUNDS.inc:80
    do return ctx:exit("") end -- MONKSOUNDS.inc:84
end

script.labels["OnWash"] = function(ctx)
    -- MONKSOUNDS.inc:87
    if ctx:condition("bsoundOn==TRUE") then -- MONKSOUNDS.inc:90
        ctx:playSound("Sounds\\AnimSounds\\Monk\\Wash.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", 10) -- MONKSOUNDS.inc:92
    end -- MONKSOUNDS.inc:93
    if ctx:condition("bIsDripping==TRUE") then -- MONKSOUNDS.inc:95
        do return ctx:exit("") end -- MONKSOUNDS.inc:96
    end -- MONKSOUNDS.inc:97
    ctx:randomInt(1, 10, "G_ntemp") -- MONKSOUNDS.inc:99
    if ctx:condition("g_ntemp==1") then -- MONKSOUNDS.inc:100
        ctx:playSound("Sounds\\AnimSounds\\Monk\\WashFidget.wav", "DoNothing", "innerRadius", "outerRadius", "FALSE", "nVolume") -- MONKSOUNDS.inc:101
        ctx:state().bIsDripping = true -- MONKSOUNDS.inc:102
        ctx:wait(1, 5, "OnStop") -- MONKSOUNDS.inc:103
    end -- MONKSOUNDS.inc:104
    do return ctx:exit("") end -- MONKSOUNDS.inc:105
end

script.labels["OnStop"] = function(ctx)
    -- MONKSOUNDS.inc:108
    ctx:state().Is_Playing = false -- MONKSOUNDS.inc:111
    ctx:state().Is_Sleeping = false -- MONKSOUNDS.inc:112
    ctx:state().bIsDripping = false -- MONKSOUNDS.inc:113
    do return ctx:exit("") end -- MONKSOUNDS.inc:114
end

script.labels["MS_Init"] = function(ctx)
    -- MONKSOUNDS.inc:117
    -- traceon
    ctx:addModelKey("PrayMumble", "OnPray") -- MONKSOUNDS.inc:121
    ctx:addModelKey("Sweep", "OnSweep") -- MONKSOUNDS.inc:122
    ctx:addModelKey("Wash", "OnWash") -- MONKSOUNDS.inc:123
    do return ctx:exit("") end -- MONKSOUNDS.inc:124
end

return script
