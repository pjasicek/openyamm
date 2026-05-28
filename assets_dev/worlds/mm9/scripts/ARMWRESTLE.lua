-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARMWRESTLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "ThjorgardGamesCommon.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }

-- ArmWrestle.scr
-- by SJR
-- Purpose:armwrestler in the thing.
script.labels["Main"] = function(ctx)
    -- ARMWRESTLE.scr:15
    ctx:getParam(0, "nMight") -- ARMWRESTLE.scr:17
    ctx:addTrigger("use", "OnUse") -- ARMWRESTLE.scr:19
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:21
end

script.labels["OnUse"] = function(ctx)
    -- ARMWRESTLE.scr:24
    mm9.gosub(script, ctx, "CheckGameTicket") -- ARMWRESTLE.scr:26
    if ctx:condition("THJORGARD_RESULT==0") then -- ARMWRESTLE.scr:27
        do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:28
    else -- ARMWRESTLE.scr:29
        mm9.gosub(script, ctx, "TakeGameTicket") -- ARMWRESTLE.scr:30
    end -- ARMWRESTLE.scr:31
    mm9.gosub(script, ctx, "RemoveUse") -- ARMWRESTLE.scr:33
    mm9.gosub(script, ctx, "StartMightGame") -- ARMWRESTLE.scr:34
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:36
end

script.labels["StartMightGame"] = function(ctx)
    -- ARMWRESTLE.scr:39
    ctx:command("getrandomint", "1, 40 nRandom") -- ARMWRESTLE.scr:41
    ctx:command("my_might", "= nMight + nRandom") -- ARMWRESTLE.scr:42
    ctx:command("getattribute", "0, PLAYER_MIGHT") -- ARMWRESTLE.scr:44
    ctx:command("getrandomint", "9, 50, nRandom") -- ARMWRESTLE.scr:45
    ctx:command("player_might", "= PLAYER_MIGHT + nRandom") -- ARMWRESTLE.scr:46
    if ctx:condition("PLAYER_MIGHT>=MY_MIGHT") then -- ARMWRESTLE.scr:48
        mm9.gosub(script, ctx, "StartCower") -- ARMWRESTLE.scr:49
        mm9.gosub(script, ctx, "RecordMightWin") -- ARMWRESTLE.scr:50
    else -- ARMWRESTLE.scr:51
        mm9.gosub(script, ctx, "LoopTaunt") -- ARMWRESTLE.scr:52
        ctx:command("rollovertext", "TEXT_DEFEAT, 1, 3000, 2000") -- ARMWRESTLE.scr:53
    end -- ARMWRESTLE.scr:54
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:56
end

script.labels["LoopTaunt"] = function(ctx)
    -- ARMWRESTLE.scr:59
    mm9.gosub(script, ctx, "RestoreUse") -- ARMWRESTLE.scr:61
    -- LoopAnim CowerStart, 2, RestoreUse
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:64
end

script.labels["StartCower"] = function(ctx)
    -- ARMWRESTLE.scr:67
    ctx:command("playanim", "\"cowerstart\", LoopCower") -- ARMWRESTLE.scr:69
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:71
end

script.labels["LoopCower"] = function(ctx)
    -- ARMWRESTLE.scr:74
    ctx:command("loopanim", "\"cower\", 5, FinishCower") -- ARMWRESTLE.scr:76
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:78
end

script.labels["FinishCower"] = function(ctx)
    -- ARMWRESTLE.scr:81
    ctx:command("playanim", "\"cowerstop\", RestoreUse") -- ARMWRESTLE.scr:83
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:85
end

script.labels["RemoveUse"] = function(ctx)
    -- ARMWRESTLE.scr:88
    ctx:command("removetrigger", "use") -- ARMWRESTLE.scr:90
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:92
end

script.labels["RestoreUse"] = function(ctx)
    -- ARMWRESTLE.scr:95
    ctx:addTrigger("use", "OnUse") -- ARMWRESTLE.scr:97
    do return ctx:exit("TRUE") end -- ARMWRESTLE.scr:99
end

return script
