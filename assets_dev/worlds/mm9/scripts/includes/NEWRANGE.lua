-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NEWRANGE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "basecrawl.inc" }

-- NewRange.inc
-- Jeff Leggett
-- 10/17/2001
-- This script implements the type of monster that has a
-- range attack, but only uses it when the target is too
-- far away to melee or the AI cannot get to the target
-- This will work for AI that do good melee damage, and
-- their range is not as powerful...
script.labels["PreRangeAttack"] = function(ctx)
    -- NEWRANGE.inc:24
    ctx:getTime("g_lastAttackTime") -- NEWRANGE.inc:26
    ctx:self():stop() -- NEWRANGE.inc:28
    -- Make sure we face our target during the attack anim...
    ctx:self():setTarget(ctx:object("g_hTarget")) -- NEWRANGE.inc:31
    ctx:self():faceObject(ctx:object("g_hTarget"), 360) -- NEWRANGE.inc:33
    do return ctx:exit("") end -- NEWRANGE.inc:36
end

script.labels["DoRangeAttack"] = function(ctx)
    -- NEWRANGE.inc:39
    ctx:self():rangeAttack("RangeAttackDone") -- NEWRANGE.inc:42
    do return ctx:exit("") end -- NEWRANGE.inc:44
end

script.labels["PostRangeAttack"] = function(ctx)
    -- NEWRANGE.inc:47
    -- virtual function only..
    do return ctx:exit("") end -- NEWRANGE.inc:53
end

script.labels["RangeAttackDone"] = function(ctx)
    -- NEWRANGE.inc:56
    mm9.gosub(script, ctx, "AttackDone") -- NEWRANGE.inc:59
    do return ctx:exit("") end -- NEWRANGE.inc:61
end

script.labels["StartRangeAttack"] = function(ctx)
    -- NEWRANGE.inc:64
    mm9.gosub(script, ctx, "PreRangeAttack") -- NEWRANGE.inc:67
    mm9.gosub(script, ctx, "DoRangeAttack") -- NEWRANGE.inc:68
    mm9.gosub(script, ctx, "PostRangeAttack") -- NEWRANGE.inc:69
    do return ctx:exit("") end -- NEWRANGE.inc:71
end

script.labels["CheckRangeTick"] = function(ctx)
    -- NEWRANGE.inc:75
    -- See if we can range attack the target....
    ctx:randomFloat("RANGE_ATTACK_CHECK_MIN", "RANGE_ATTACK_CHECK_MAX", "g_nRandom") -- NEWRANGE.inc:81
    ctx:wait("ATTACK_CHECK_WAIT", "g_nRandom", "CheckRangeTick") -- NEWRANGE.inc:83
    if ctx:condition("g_hTarget==NULL") then -- NEWRANGE.inc:85
        do return ctx:exit("") end -- NEWRANGE.inc:86
    end -- NEWRANGE.inc:87
    ctx:state().g_bCanAttack = ctx:self():canRangeAttack() -- NEWRANGE.inc:89
    if ctx:condition("g_bCanAttack==FALSE") then -- NEWRANGE.inc:91
        do return ctx:exit("") end -- NEWRANGE.inc:92
    end -- NEWRANGE.inc:93
    ctx:self():estimateRangeAttackHit(ctx:object("g_hObject")) -- NEWRANGE.inc:95
    ctx:state().g_attackChance = 0 -- NEWRANGE.inc:97
    if ctx:condition("g_hObject==NULL") then -- NEWRANGE.inc:99
        ctx:state().g_attackChance = 20 -- NEWRANGE.inc:100
    else -- NEWRANGE.inc:101
        if ctx:condition("g_hObject==g_hTarget") then -- NEWRANGE.inc:102
            ctx:state().g_attackChance = 100 -- NEWRANGE.inc:103
        else -- NEWRANGE.inc:104
            ctx:state().g_bTemp = ctx:object("g_hObject"):isClass("AIBase") -- NEWRANGE.inc:105
            if ctx:condition("g_bTemp==TRUE") then -- NEWRANGE.inc:107
                ctx:state().g_attackChance = 0 -- NEWRANGE.inc:108
            else -- NEWRANGE.inc:109
                ctx:state().g_attackChance = 20 -- NEWRANGE.inc:110
            end -- NEWRANGE.inc:111
        end -- NEWRANGE.inc:112
    end -- NEWRANGE.inc:113
    if ctx:condition("g_attackChance==0") then -- NEWRANGE.inc:115
        do return ctx:exit("") end -- NEWRANGE.inc:116
    end -- NEWRANGE.inc:117
    ctx:randomInt(0, 100, "g_nRandom") -- NEWRANGE.inc:119
    if ctx:condition("g_nRandom > g_attackChance") then -- NEWRANGE.inc:121
        do return ctx:exit("") end -- NEWRANGE.inc:122
    end -- NEWRANGE.inc:123
    mm9.gosub(script, ctx, "StartRangeAttack") -- NEWRANGE.inc:125
    do return ctx:exit("") end -- NEWRANGE.inc:127
end

script.labels["CheckRangeAttack"] = function(ctx)
    -- NEWRANGE.inc:130
    mm9.gosub(script, ctx, "CheckRangeTick") -- NEWRANGE.inc:133
    do return ctx:exit("") end -- NEWRANGE.inc:135
end

script.labels["CheckRangeAttackStop"] = function(ctx)
    -- NEWRANGE.inc:138
    ctx:wait("ATTACK_CHECK_WAIT", 0, "DoNothing") -- NEWRANGE.inc:141
    do return ctx:exit("") end -- NEWRANGE.inc:143
end

script.labels["SetupTarget"] = function(ctx)
    -- NEWRANGE.inc:146
    mm9.gosub(script, ctx, "SetupTarget") -- NEWRANGE.inc:149
    mm9.gosub(script, ctx, "CheckRangeAttack") -- NEWRANGE.inc:150
    do return ctx:exit("") end -- NEWRANGE.inc:152
end

script.labels["ClearTarget"] = function(ctx)
    -- NEWRANGE.inc:155
    mm9.gosub(script, ctx, "ClearTarget") -- NEWRANGE.inc:158
    mm9.gosub(script, ctx, "CheckRangeAttackStop") -- NEWRANGE.inc:159
    do return ctx:exit("") end -- NEWRANGE.inc:161
end

script.labels["RangeInit"] = function(ctx)
    -- NEWRANGE.inc:164
    -- gosub BaseInit
    -- gosub BaseCrawlInit
    do return ctx:exit("") end -- NEWRANGE.inc:171
end

return script
