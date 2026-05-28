-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARDSOUNDS.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- Guardsounds.inc
-- timmy
-- 10/30
-- randomizes guard idle sounds.
script.labels["OnStand"] = function(ctx)
    -- GUARDSOUNDS.inc:16
    if ctx:condition("Is_Playing==TRUE") then -- GUARDSOUNDS.inc:19
        do return ctx:exit("") end -- GUARDSOUNDS.inc:20
    end -- GUARDSOUNDS.inc:21
    ctx:command("getrandomint", "1, 20, G_ntemp") -- GUARDSOUNDS.inc:23
    if ctx:condition("g_ntemp==1") then -- GUARDSOUNDS.inc:25
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Stand1.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:26
        ctx:command("set", "Is_Playing, TRUE") -- GUARDSOUNDS.inc:27
        ctx:command("wait", "1 1.2, OnStop") -- GUARDSOUNDS.inc:28
        do return ctx:exit("") end -- GUARDSOUNDS.inc:29
    end -- GUARDSOUNDS.inc:30
    if ctx:condition("g_ntemp==2") then -- GUARDSOUNDS.inc:32
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Stand2.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:33
        ctx:command("set", "Is_Playing, TRUE") -- GUARDSOUNDS.inc:34
        ctx:command("wait", "1 1.2, OnStop") -- GUARDSOUNDS.inc:35
        do return ctx:exit("") end -- GUARDSOUNDS.inc:36
    end -- GUARDSOUNDS.inc:37
    if ctx:condition("g_ntemp==3") then -- GUARDSOUNDS.inc:39
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Stand3.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:40
        ctx:command("set", "Is_Playing, TRUE") -- GUARDSOUNDS.inc:41
        ctx:command("wait", "1 1.2, OnStop") -- GUARDSOUNDS.inc:42
        do return ctx:exit("") end -- GUARDSOUNDS.inc:43
    end -- GUARDSOUNDS.inc:44
    if ctx:condition("g_ntemp==4") then -- GUARDSOUNDS.inc:46
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Stand4.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:47
        ctx:command("set", "Is_Playing, TRUE") -- GUARDSOUNDS.inc:48
        ctx:command("wait", "1 1.2, OnStop") -- GUARDSOUNDS.inc:49
        do return ctx:exit("") end -- GUARDSOUNDS.inc:50
    end -- GUARDSOUNDS.inc:51
    if ctx:condition("g_ntemp==5") then -- GUARDSOUNDS.inc:53
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Stand5.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:54
        ctx:command("set", "Is_Playing, TRUE") -- GUARDSOUNDS.inc:55
        ctx:command("wait", "1 1.2, OnStop") -- GUARDSOUNDS.inc:56
        do return ctx:exit("") end -- GUARDSOUNDS.inc:57
    end -- GUARDSOUNDS.inc:58
    if ctx:condition("g_ntemp==6") then -- GUARDSOUNDS.inc:60
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Stand6.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:61
        ctx:command("set", "Is_Playing, TRUE") -- GUARDSOUNDS.inc:62
        ctx:command("wait", "1 1.2, OnStop") -- GUARDSOUNDS.inc:63
        do return ctx:exit("") end -- GUARDSOUNDS.inc:64
    end -- GUARDSOUNDS.inc:65
    if ctx:condition("g_ntemp==7") then -- GUARDSOUNDS.inc:67
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Stand7.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:68
        ctx:command("set", "Is_Playing, TRUE") -- GUARDSOUNDS.inc:69
        ctx:command("wait", "1 1.2, OnStop") -- GUARDSOUNDS.inc:70
        do return ctx:exit("") end -- GUARDSOUNDS.inc:71
    end -- GUARDSOUNDS.inc:72
    if ctx:condition("g_ntemp>7") then -- GUARDSOUNDS.inc:74
        ctx:command("set", "Is_Playing, TRUE") -- GUARDSOUNDS.inc:76
        ctx:command("wait", "1 50, ONStop") -- GUARDSOUNDS.inc:77
        do return ctx:exit("") end -- GUARDSOUNDS.inc:78
    end -- GUARDSOUNDS.inc:79
    do return ctx:exit("") end -- GUARDSOUNDS.inc:81
end

script.labels["OnSleep"] = function(ctx)
    -- GUARDSOUNDS.inc:84
    if ctx:condition("Is_Sleeping==TRUE") then -- GUARDSOUNDS.inc:87
        do return ctx:exit("") end -- GUARDSOUNDS.inc:88
    end -- GUARDSOUNDS.inc:89
    ctx:command("getrandomint", "1, 4, G_ntemp") -- GUARDSOUNDS.inc:91
    if ctx:condition("g_ntemp==1") then -- GUARDSOUNDS.inc:93
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Sleep1.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:94
        ctx:command("set", "Is_Sleeping, TRUE") -- GUARDSOUNDS.inc:95
        ctx:command("wait", "1 5, OnStop") -- GUARDSOUNDS.inc:96
        do return ctx:exit("") end -- GUARDSOUNDS.inc:97
    end -- GUARDSOUNDS.inc:98
    if ctx:condition("g_ntemp==2") then -- GUARDSOUNDS.inc:100
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Sleep2.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:101
        ctx:command("set", "Is_Sleeping, TRUE") -- GUARDSOUNDS.inc:102
        ctx:command("wait", "1 5, OnStop") -- GUARDSOUNDS.inc:103
        do return ctx:exit("") end -- GUARDSOUNDS.inc:104
    end -- GUARDSOUNDS.inc:105
    if ctx:condition("g_ntemp==3") then -- GUARDSOUNDS.inc:107
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Sleep3.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:108
        ctx:command("set", "Is_Sleeping, TRUE") -- GUARDSOUNDS.inc:109
        ctx:command("wait", "1 5, OnStop") -- GUARDSOUNDS.inc:110
        do return ctx:exit("") end -- GUARDSOUNDS.inc:111
    end -- GUARDSOUNDS.inc:112
    if ctx:condition("g_ntemp==4") then -- GUARDSOUNDS.inc:114
        ctx:command("playsound", "Sounds\\AnimSounds\\Guard\\Sleep4.wav, DoNothing, innerRadius, outerRadius, FALSE, 100") -- GUARDSOUNDS.inc:115
        ctx:command("set", "Is_Sleeping, TRUE") -- GUARDSOUNDS.inc:116
        ctx:command("wait", "1 7, OnStop") -- GUARDSOUNDS.inc:117
        do return ctx:exit("") end -- GUARDSOUNDS.inc:118
    end -- GUARDSOUNDS.inc:119
    if ctx:condition("g_ntemp>4") then -- GUARDSOUNDS.inc:121
        ctx:command("set", "Is_Sleeping, TRUE") -- GUARDSOUNDS.inc:122
        ctx:command("wait", "1 10, ONStop") -- GUARDSOUNDS.inc:123
        do return ctx:exit("") end -- GUARDSOUNDS.inc:124
    end -- GUARDSOUNDS.inc:125
    do return ctx:exit("") end -- GUARDSOUNDS.inc:126
end

script.labels["OnStop"] = function(ctx)
    -- GUARDSOUNDS.inc:129
    ctx:command("set", "Is_Playing, FALSE") -- GUARDSOUNDS.inc:132
    ctx:command("set", "Is_Sleeping, FALSE") -- GUARDSOUNDS.inc:133
    do return ctx:exit("") end -- GUARDSOUNDS.inc:134
end

script.labels["GS_Init"] = function(ctx)
    -- GUARDSOUNDS.inc:137
    -- traceon
    ctx:command("addmodelkey", "Stand OnStand") -- GUARDSOUNDS.inc:141
    ctx:command("addmodelkey", "Sleep, OnSleep") -- GUARDSOUNDS.inc:142
    do return ctx:exit("") end -- GUARDSOUNDS.inc:144
end

return script
