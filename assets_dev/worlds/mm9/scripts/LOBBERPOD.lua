-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LOBBERPOD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "basecrawl.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "Range.inc" }

-- LobberPod.Scr
-- Jeff Leggett
-- 08/01/2001
-- LobberPod implementation...
script.labels["CanRangeAttack"] = function(ctx)
    -- LOBBERPOD.scr:18
    -- We only want 30% of the lobberPods to range
    -- attack....
    if ctx:condition("g_bIsRangeAttacker==TRUE") then -- LOBBERPOD.scr:23
        mm9.gosub(script, ctx, "CanRangeAttack") -- LOBBERPOD.scr:24
        do return ctx:exit("") end -- LOBBERPOD.scr:25
    end -- LOBBERPOD.scr:26
    ctx:state().g_bCanAttack = false -- LOBBERPOD.scr:28
    do return ctx:exit("") end -- LOBBERPOD.scr:30
end

script.labels["CancelEvade"] = function(ctx)
    -- LOBBERPOD.scr:33
    mm9.gosub(script, ctx, "BaseEvadeStop") -- LOBBERPOD.scr:36
    mm9.gosub(script, ctx, "AggressiveStart") -- LOBBERPOD.scr:37
    do return ctx:exit("") end -- LOBBERPOD.scr:39
end

script.labels["DoEvade"] = function(ctx)
    -- LOBBERPOD.scr:42
    -- Backup and/or strafe a little...
    mm9.gosub(script, ctx, "AggressiveStop") -- LOBBERPOD.scr:48
    ctx:onEvent("OnTargetBeyondDist", "g_nMaxEvadeDist", "CancelEvade") -- LOBBERPOD.scr:50
    mm9.gosub(script, ctx, "BaseEvadeStart") -- LOBBERPOD.scr:52
    ctx:state().g_nEvadeTime = 2 -- LOBBERPOD.scr:54
    ctx:set("g_nBackpedalPct", 0.4) -- LOBBERPOD.scr:55
    ctx:randomFloat(1.8, 2.2, "g_nRandom") -- LOBBERPOD.scr:57
    ctx:wait("AGGRESSIVE_WAIT", "g_nRandom", "CancelEvade") -- LOBBERPOD.scr:59
    do return ctx:exit("") end -- LOBBERPOD.scr:61
end

script.labels["AttackDone"] = function(ctx)
    -- LOBBERPOD.scr:64
    -- Lobber pods (that don't do range attacks) look cool
    -- when they evade and such...
    -- if ( g_bIsRangeAttacker==TRUE )
    -- gosub AttackDone,1
    -- Exit
    -- Endif
    ctx:isTurnBased("g_bTemp") -- LOBBERPOD.scr:76
    if ctx:condition("g_bTemp==TRUE") then -- LOBBERPOD.scr:78
        mm9.gosub(script, ctx, "AttackDone") -- LOBBERPOD.scr:79
        do return ctx:exit("") end -- LOBBERPOD.scr:80
    end -- LOBBERPOD.scr:81
    mm9.gosub(script, ctx, "AttackTickCancel") -- LOBBERPOD.scr:83
    mm9.gosub(script, ctx, "DoEvade") -- LOBBERPOD.scr:84
    do return ctx:exit("") end -- LOBBERPOD.scr:86
end

script.labels["NewTargetCheck"] = function(ctx)
    -- LOBBERPOD.scr:89
    -- Fill in g_hAttacker with the potential new target,
    -- and this function takes care of the rest....
    if ctx:condition("g_hAttacker==g_hTarget") then -- LOBBERPOD.scr:96
        do return mm9.gotoLabel(script, ctx, "NewTargetCheck") end -- LOBBERPOD.scr:97
    end -- LOBBERPOD.scr:98
    ctx:state().g_bTemp = ctx:object("g_hAttacker"):isClass("Lobber") -- LOBBERPOD.scr:100
    if ctx:condition("g_bTemp==FALSE") then -- LOBBERPOD.scr:101
        do return mm9.gotoLabel(script, ctx, "NewTargetCheck") end -- LOBBERPOD.scr:102
    end -- LOBBERPOD.scr:103
    ctx:state().g_bTemp = ctx:self():isFriend(ctx:object("g_hAttacker")) -- LOBBERPOD.scr:105
    if ctx:condition("g_bTemp==TRUE") then -- LOBBERPOD.scr:107
        do return ctx:exit("TRUE") end -- LOBBERPOD.scr:108
    end -- LOBBERPOD.scr:109
    ctx:state().g_sTemp = ctx:object("g_hAttacker"):className() -- LOBBERPOD.scr:111
    ctx:set("g_sTemp", "g_sTemp + <---AttackerClass") -- LOBBERPOD.scr:113
    -- CPrint g_sTemp
    ctx:set("g_hTarget", "g_hAttacker") -- LOBBERPOD.scr:117
    ctx:state().g_hAttacker = nil -- LOBBERPOD.scr:118
    mm9.gosub(script, ctx, "SetupTarget") -- LOBBERPOD.scr:119
    ctx:self():setTarget(ctx:object("g_hTarget")) -- LOBBERPOD.scr:120
    mm9.gosub(script, ctx, "AggressiveStart") -- LOBBERPOD.scr:121
    do return ctx:exit("TRUE") end -- LOBBERPOD.scr:123
end

script.labels["ShouldRunAfter"] = function(ctx)
    -- LOBBERPOD.scr:126
    -- if we're NOT a range attacker, ignore the range.inc
    -- version...
    if ctx:condition("g_bIsRangeAttacker==FALSE") then -- LOBBERPOD.scr:133
        mm9.gosub(script, ctx, "ShouldRunAfter") -- LOBBERPOD.scr:134
        do return ctx:exit("") end -- LOBBERPOD.scr:135
    end -- LOBBERPOD.scr:136
    mm9.gosub(script, ctx, "ShouldRunAfter") -- LOBBERPOD.scr:138
    do return ctx:exit("") end -- LOBBERPOD.scr:140
end

script.labels["Main"] = function(ctx)
    -- LOBBERPOD.scr:143
    mm9.gosub(script, ctx, "BaseCrawlInit") -- LOBBERPOD.scr:147
    mm9.gosub(script, ctx, "RangeInit") -- LOBBERPOD.scr:148
    ctx:randomInt(0, 100, "g_nRandom") -- LOBBERPOD.scr:150
    -- jsl->2/11/02 --> They no longer want lobberpods to range attack.
    -- if ( g_nRandom < 30 )
    -- g_bIsRangeAttacker = TRUE
    -- endif
    do return ctx:exit("") end -- LOBBERPOD.scr:158
end

return script
