-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FLYRANGE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "baseFly.inc" }

-- FlyRange.Inc
-- Jeff Leggett
-- 10/22/2001
-- Implements flying creatures that can shoot....
-- Still want to swoop in on target (so they can melee
-- you a little...)
-- Randomly shoot once we've backed off....
script.labels["RangeCheckSetup"] = function(ctx)
    -- FLYRANGE.inc:30
    if ctx:condition("g_hTarget==NULL") then -- FLYRANGE.inc:33
        mm9.gosub(script, ctx, "RangeCheckStop") -- FLYRANGE.inc:34
        do return ctx:exit("") end -- FLYRANGE.inc:35
    end -- FLYRANGE.inc:36
    ctx:command("getrandomfloat", "MIN_RANGE_CHECK_TIME,MAX_RANGE_CHECK_TIME, g_nRandom") -- FLYRANGE.inc:38
    ctx:command("wait", "RANGE_CHECK_WAIT, g_nRandom, RangeCheckTick") -- FLYRANGE.inc:39
    do return ctx:exit("") end -- FLYRANGE.inc:41
end

script.labels["RangeCheckStop"] = function(ctx)
    -- FLYRANGE.inc:44
    ctx:command("wait", "RANGE_CHECK_WAIT, 0, DoNothing") -- FLYRANGE.inc:47
    do return ctx:exit("") end -- FLYRANGE.inc:49
end

script.labels["RangeCheckTick"] = function(ctx)
    -- FLYRANGE.inc:52
    mm9.gosub(script, ctx, "RangeCheckSetup") -- FLYRANGE.inc:55
    mm9.gosub(script, ctx, "ShouldRangeAttack") -- FLYRANGE.inc:56
    if ctx:condition("g_bTemp==TRUE") then -- FLYRANGE.inc:58
        ctx:command("g_bswoopafterrange", "= FALSE") -- FLYRANGE.inc:59
        mm9.gosub(script, ctx, "StartRangeAttack") -- FLYRANGE.inc:60
    end -- FLYRANGE.inc:61
    do return ctx:exit("") end -- FLYRANGE.inc:63
end

script.labels["CanRangeAttack"] = function(ctx)
    -- FLYRANGE.inc:66
    ctx:command("gettime", "g_nTemp") -- FLYRANGE.inc:69
    ctx:command("g_ntemp", "= g_nTemp - g_lastRangeAttack") -- FLYRANGE.inc:71
    if ctx:condition("g_nTemp < MIN_RANGE_ATTACK_INTERVAL") then -- FLYRANGE.inc:73
        ctx:command("g_bcanrangeattack", "= FALSE") -- FLYRANGE.inc:74
        do return ctx:exit("") end -- FLYRANGE.inc:75
    end -- FLYRANGE.inc:76
    ctx:command("canrangeattack", "g_bCanRangeAttack") -- FLYRANGE.inc:78
    do return ctx:exit("") end -- FLYRANGE.inc:80
end

script.labels["RangeAttackDone"] = function(ctx)
    -- FLYRANGE.inc:83
    mm9.gosub(script, ctx, "RangeCheckSetup") -- FLYRANGE.inc:85
    if ctx:condition("g_bSwoopAfterRange==TRUE") then -- FLYRANGE.inc:87
        mm9.gosub(script, ctx, "SwoopIn") -- FLYRANGE.inc:88
    else -- FLYRANGE.inc:89
        mm9.gosub(script, ctx, "AggressiveStart") -- FLYRANGE.inc:90
    end -- FLYRANGE.inc:91
    do return ctx:exit("") end -- FLYRANGE.inc:93
end

script.labels["DoRangeAttack"] = function(ctx)
    -- FLYRANGE.inc:96
    ctx:command("gettime", "g_nLastAttackTime") -- FLYRANGE.inc:99
    mm9.gosub(script, ctx, "GetTimeToTarget") -- FLYRANGE.inc:101
    if ctx:condition("g_nTimeToTarget < 1.1") then -- FLYRANGE.inc:103
        ctx:command("stop", "") -- FLYRANGE.inc:104
    end -- FLYRANGE.inc:105
    ctx:command("gettime", "g_lastRangeAttack") -- FLYRANGE.inc:107
    ctx:command("rangeattack", "RangeAttackDone") -- FLYRANGE.inc:108
    -- Setup our next range attack check...
    mm9.gosub(script, ctx, "RangeCheckSetup") -- FLYRANGE.inc:113
    do return ctx:exit("") end -- FLYRANGE.inc:115
end

script.labels["StartRangeAttack"] = function(ctx)
    -- FLYRANGE.inc:118
    ctx:command("target", "g_hTarget, TRUE") -- FLYRANGE.inc:121
    mm9.gosub(script, ctx, "AggressiveStop") -- FLYRANGE.inc:123
    mm9.gosub(script, ctx, "DoRangeAttack") -- FLYRANGE.inc:124
    do return ctx:exit("") end -- FLYRANGE.inc:126
end

script.labels["ShouldRangeAttack"] = function(ctx)
    -- FLYRANGE.inc:130
    if ctx:condition("g_bSwooping==TRUE") then -- FLYRANGE.inc:133
        ctx:command("g_btemp", "= FALSE") -- FLYRANGE.inc:134
        do return ctx:exit("") end -- FLYRANGE.inc:135
    end -- FLYRANGE.inc:136
    if ctx:condition("g_bBackingOff==TRUE") then -- FLYRANGE.inc:138
        ctx:command("g_btemp", "= FALSE") -- FLYRANGE.inc:139
        do return ctx:exit("") end -- FLYRANGE.inc:140
    end -- FLYRANGE.inc:141
    ctx:command("getrandomint", "0,100,g_nRandom") -- FLYRANGE.inc:143
    if ctx:condition("g_nRandom < 40") then -- FLYRANGE.inc:145
        ctx:command("g_btemp", "= FALSE") -- FLYRANGE.inc:146
        do return ctx:exit("") end -- FLYRANGE.inc:147
    end -- FLYRANGE.inc:148
    ctx:command("canrangeattack", "g_bTemp") -- FLYRANGE.inc:150
    if ctx:condition("g_bTemp==FALSE") then -- FLYRANGE.inc:152
        do return ctx:exit("") end -- FLYRANGE.inc:153
    end -- FLYRANGE.inc:154
    ctx:command("estimaterangeattackhit", "g_hObject") -- FLYRANGE.inc:156
    if ctx:condition("g_hObject!=g_hTarget") then -- FLYRANGE.inc:158
        ctx:command("g_btemp", "= FALSE") -- FLYRANGE.inc:159
        do return ctx:exit("") end -- FLYRANGE.inc:160
    end -- FLYRANGE.inc:161
    ctx:command("g_btemp", "= TRUE") -- FLYRANGE.inc:163
    do return ctx:exit("") end -- FLYRANGE.inc:165
end

script.labels["BackoffDone"] = function(ctx)
    -- FLYRANGE.inc:168
    ctx:command("g_bbackingoff", "= FALSE") -- FLYRANGE.inc:171
    mm9.gosub(script, ctx, "CanRangeAttack") -- FLYRANGE.inc:173
    if ctx:condition("g_bCanRangeAttack==FALSE") then -- FLYRANGE.inc:175
        do return mm9.gotoLabel(script, ctx, "BackoffDone") end -- FLYRANGE.inc:176
    end -- FLYRANGE.inc:177
    mm9.gosub(script, ctx, "ShouldRangeAttack") -- FLYRANGE.inc:179
    if ctx:condition("g_bTemp==TRUE") then -- FLYRANGE.inc:181
        ctx:command("stop", "") -- FLYRANGE.inc:182
        ctx:command("g_bswoopafterrange", "= TRUE") -- FLYRANGE.inc:183
        mm9.gosub(script, ctx, "StartRangeAttack") -- FLYRANGE.inc:184
    else -- FLYRANGE.inc:185
        do return mm9.gotoLabel(script, ctx, "BackoffDone") end -- FLYRANGE.inc:186
    end -- FLYRANGE.inc:187
    do return ctx:exit("") end -- FLYRANGE.inc:189
end

script.labels["OnFoundTarget"] = function(ctx)
    -- FLYRANGE.inc:192
    mm9.gosub(script, ctx, "OnFoundTarget") -- FLYRANGE.inc:195
    mm9.gosub(script, ctx, "RangeCheckSetup") -- FLYRANGE.inc:197
    if ctx:condition("g_hTarget!=NULL") then -- FLYRANGE.inc:199
        mm9.gosub(script, ctx, "ShouldRangeAttack") -- FLYRANGE.inc:200
        if ctx:condition("g_bTemp==TRUE") then -- FLYRANGE.inc:201
            ctx:command("g_bswoopafterrange", "= FALSE") -- FLYRANGE.inc:202
            mm9.gosub(script, ctx, "StartRangeAttack") -- FLYRANGE.inc:203
        end -- FLYRANGE.inc:204
    end -- FLYRANGE.inc:205
    do return ctx:exit("") end -- FLYRANGE.inc:207
end

script.labels["SwoopDone"] = function(ctx)
    -- FLYRANGE.inc:210
    mm9.gosub(script, ctx, "SwoopDone") -- FLYRANGE.inc:213
    mm9.gosub(script, ctx, "RangeCheckSetup") -- FLYRANGE.inc:215
    do return ctx:exit("") end -- FLYRANGE.inc:217
end

script.labels["FlyRangeInit"] = function(ctx)
    -- FLYRANGE.inc:220
    mm9.gosub(script, ctx, "BaseFlyInit") -- FLYRANGE.inc:223
    do return ctx:exit("") end -- FLYRANGE.inc:226
end

return script
