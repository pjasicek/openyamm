-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DARKP_BRIDGEPUZZLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "DarkP_initMyStuff.inc" }

-- DarkP_bridgepuzzle.scr
-- Brett Yagi
-- 11/09/2001
-- Manager for bridge puzzle
-- Requires DarkP_initMyStuff.inc
-- Parameters
-- 0 Root name of Bridges
script.labels["MoveStuff"] = function(ctx)
    -- DARKP_BRIDGEPUZZLE.scr:36
    ctx:command("ntemp1", "= nGroup") -- DARKP_BRIDGEPUZZLE.scr:39
    ctx:command("nbridgenumber", "= 5") -- DARKP_BRIDGEPUZZLE.scr:40
    while ctx:condition("nBridgeNumber > 0") do -- DARKP_BRIDGEPUZZLE.scr:41
        ctx:command("nbridgenumber", "= nBridgeNumber - 1") -- DARKP_BRIDGEPUZZLE.scr:42
        ctx:command("ntemp2", "= nTemp1") -- DARKP_BRIDGEPUZZLE.scr:43
        ctx:command("mod", "nTemp2 nTwo") -- DARKP_BRIDGEPUZZLE.scr:45
        -- remember left to right evaluation, no precedence here
        ctx:command("ntemp1", "= nTemp1 - nTemp2 / 2") -- DARKP_BRIDGEPUZZLE.scr:48
        ctx:command("arrayget", "aBridges nBridgeNumber nPos") -- DARKP_BRIDGEPUZZLE.scr:50
        if ctx:condition("nTemp2 != nPos") then -- DARKP_BRIDGEPUZZLE.scr:51
            ctx:command("arrayput", "aBridges nBridgeNumber nTemp2") -- DARKP_BRIDGEPUZZLE.scr:52
            ctx:command("sname", "= sNameRoot + nBridgeNumber") -- DARKP_BRIDGEPUZZLE.scr:53
            ctx:command("getobjecthandle", "sName hName") -- DARKP_BRIDGEPUZZLE.scr:54
            ctx:trigger("hName", "Move") -- DARKP_BRIDGEPUZZLE.scr:55
        end -- DARKP_BRIDGEPUZZLE.scr:56
    end -- DARKP_BRIDGEPUZZLE.scr:58
    if ctx:condition("nGroup == 0") then -- DARKP_BRIDGEPUZZLE.scr:60
        ctx:command("removetrigger", "HitA") -- DARKP_BRIDGEPUZZLE.scr:61
        ctx:command("removetrigger", "HitB") -- DARKP_BRIDGEPUZZLE.scr:62
        ctx:command("removetrigger", "HitC") -- DARKP_BRIDGEPUZZLE.scr:63
        ctx:command("removetrigger", "HitD") -- DARKP_BRIDGEPUZZLE.scr:64
        ctx:command("removetrigger", "Reset") -- DARKP_BRIDGEPUZZLE.scr:65
        -- Add triggered event Here
        ctx:command("getobjecthandle", "TeleportDoor0, hDoor") -- DARKP_BRIDGEPUZZLE.scr:67
        ctx:trigger("hDoor", "Unlock") -- DARKP_BRIDGEPUZZLE.scr:68
        ctx:trigger("hDoor", "Use") -- DARKP_BRIDGEPUZZLE.scr:69
        ctx:command("ntemp1", "= 0") -- DARKP_BRIDGEPUZZLE.scr:70
        while ctx:condition("nTemp1 < 6") do -- DARKP_BRIDGEPUZZLE.scr:71
            ctx:command("sname", "= sCreatureSwitch + nTemp1") -- DARKP_BRIDGEPUZZLE.scr:72
            ctx:command("getobjecthandle", "sName hName") -- DARKP_BRIDGEPUZZLE.scr:73
            ctx:trigger("hName", "Stop") -- DARKP_BRIDGEPUZZLE.scr:74
            ctx:command("ntemp1", "= nTemp1 + 1") -- DARKP_BRIDGEPUZZLE.scr:75
        end -- DARKP_BRIDGEPUZZLE.scr:76
    end -- DARKP_BRIDGEPUZZLE.scr:77
    do return ctx:exit(1) end -- DARKP_BRIDGEPUZZLE.scr:78
end

script.labels["HitA"] = function(ctx)
    -- DARKP_BRIDGEPUZZLE.scr:81
    ctx:command("arrayget", "aA nGroup nGroup") -- DARKP_BRIDGEPUZZLE.scr:83
    mm9.gosub(script, ctx, "MoveStuff") -- DARKP_BRIDGEPUZZLE.scr:84
    do return ctx:exit(1) end -- DARKP_BRIDGEPUZZLE.scr:86
end

script.labels["HitB"] = function(ctx)
    -- DARKP_BRIDGEPUZZLE.scr:89
    ctx:command("arrayget", "aB nGroup nGroup") -- DARKP_BRIDGEPUZZLE.scr:91
    mm9.gosub(script, ctx, "MoveStuff") -- DARKP_BRIDGEPUZZLE.scr:92
    do return ctx:exit(1) end -- DARKP_BRIDGEPUZZLE.scr:94
end

script.labels["HitC"] = function(ctx)
    -- DARKP_BRIDGEPUZZLE.scr:97
    ctx:command("arrayget", "aC nGroup nGroup") -- DARKP_BRIDGEPUZZLE.scr:99
    mm9.gosub(script, ctx, "MoveStuff") -- DARKP_BRIDGEPUZZLE.scr:100
    do return ctx:exit(1) end -- DARKP_BRIDGEPUZZLE.scr:102
end

script.labels["HitD"] = function(ctx)
    -- DARKP_BRIDGEPUZZLE.scr:105
    ctx:command("arrayget", "aD nGroup nGroup") -- DARKP_BRIDGEPUZZLE.scr:107
    mm9.gosub(script, ctx, "MoveStuff") -- DARKP_BRIDGEPUZZLE.scr:108
    do return ctx:exit(1) end -- DARKP_BRIDGEPUZZLE.scr:110
end

script.labels["Reset"] = function(ctx)
    -- DARKP_BRIDGEPUZZLE.scr:113
    ctx:command("ngroup", "= 14") -- DARKP_BRIDGEPUZZLE.scr:115
    mm9.gosub(script, ctx, "MoveStuff") -- DARKP_BRIDGEPUZZLE.scr:116
    do return ctx:exit(1) end -- DARKP_BRIDGEPUZZLE.scr:118
end

script.labels["main2"] = function(ctx)
    -- DARKP_BRIDGEPUZZLE.scr:120
    mm9.gosub(script, ctx, "InitializeStuff") -- DARKP_BRIDGEPUZZLE.scr:123
    do return ctx:exit(1) end -- DARKP_BRIDGEPUZZLE.scr:125
end

script.labels["main"] = function(ctx)
    -- DARKP_BRIDGEPUZZLE.scr:128
    ctx:getParam(0, "sNameRoot") -- DARKP_BRIDGEPUZZLE.scr:131
    ctx:getParam(1, "sCreatureSwitch") -- DARKP_BRIDGEPUZZLE.scr:132
    ctx:addTrigger("HitA", "HitA") -- DARKP_BRIDGEPUZZLE.scr:133
    ctx:addTrigger("HitB", "HitB") -- DARKP_BRIDGEPUZZLE.scr:134
    ctx:addTrigger("HitC", "HitC") -- DARKP_BRIDGEPUZZLE.scr:135
    ctx:addTrigger("HitD", "HitD") -- DARKP_BRIDGEPUZZLE.scr:136
    ctx:addTrigger("Reset", "Reset") -- DARKP_BRIDGEPUZZLE.scr:137
    ctx:command("wait", "0 1 main2") -- DARKP_BRIDGEPUZZLE.scr:138
    do return ctx:exit(1) end -- DARKP_BRIDGEPUZZLE.scr:140
end

return script
