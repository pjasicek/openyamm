-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DINGTHEBELL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 5, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 6, path = "ThjorgardGamesCommon.inc" }

-- DingTheBell.scr
-- by SJR
script.labels["Main"] = function(ctx)
    -- DINGTHEBELL.scr:15
    ctx:addTrigger("use", "HitBell") -- DINGTHEBELL.scr:17
    ctx:addTrigger("ring", "CheckWin") -- DINGTHEBELL.scr:18
    ctx:setConsoleNumVar("GAME_BELL_HEIGHT", 0) -- DINGTHEBELL.scr:20
    do return ctx:exit("TRUE") end -- DINGTHEBELL.scr:22
end

script.labels["HitBell"] = function(ctx)
    -- DINGTHEBELL.scr:25
    mm9.gosub(script, ctx, "CheckGameTicket") -- DINGTHEBELL.scr:27
    if ctx:condition("THJORGARD_RESULT==FALSE") then -- DINGTHEBELL.scr:28
        do return ctx:exit("TRUE") end -- DINGTHEBELL.scr:29
    else -- DINGTHEBELL.scr:30
        mm9.gosub(script, ctx, "TakeGameTicket") -- DINGTHEBELL.scr:31
    end -- DINGTHEBELL.scr:32
    ctx:command("removetrigger", "use") -- DINGTHEBELL.scr:34
    ctx:addTrigger("use", "BlockUse") -- DINGTHEBELL.scr:35
    ctx:command("getrandomint", "60, 80, nDingValue") -- DINGTHEBELL.scr:37
    ctx:command("getrandomint", "40, 60, nTimingValue") -- DINGTHEBELL.scr:38
    ctx:command("getattribute", "0, nPlayerStrength") -- DINGTHEBELL.scr:39
    ctx:command("ntimingvalue", "= nTimingValue + nPlayerStrength") -- DINGTHEBELL.scr:40
    ctx:command("ntemp", "= nTimingValue / nDingValue") -- DINGTHEBELL.scr:42
    ctx:setConsoleNumVar("GAME_BELL_HEIGHT", "nTemp") -- DINGTHEBELL.scr:43
    do return ctx:exit("FALSE") end -- DINGTHEBELL.scr:45
end

script.labels["CheckWin"] = function(ctx)
    -- DINGTHEBELL.scr:48
    if ctx:condition("nTimingValue>nDingValue") then -- DINGTHEBELL.scr:50
        ctx:command("playsound", "\"sounds\\events\\dingbell.wav\", DoNothing, 1, 500, FALSE, 100") -- DINGTHEBELL.scr:51
        mm9.gosub(script, ctx, "RecordBellWin") -- DINGTHEBELL.scr:52
    else -- DINGTHEBELL.scr:53
        ctx:command("rollovertext", "TEXT_DEFEAT, 1, 3000, 2000") -- DINGTHEBELL.scr:54
    end -- DINGTHEBELL.scr:55
    ctx:command("wait", "0, 3, AllowUse") -- DINGTHEBELL.scr:57
    do return ctx:exit("TRUE") end -- DINGTHEBELL.scr:59
end

script.labels["BlockUse"] = function(ctx)
    -- DINGTHEBELL.scr:62
    do return ctx:exit("TRUE") end -- DINGTHEBELL.scr:64
end

script.labels["AllowUse"] = function(ctx)
    -- DINGTHEBELL.scr:67
    ctx:command("removetrigger", "use") -- DINGTHEBELL.scr:69
    ctx:addTrigger("use", "HitBell") -- DINGTHEBELL.scr:70
    do return ctx:exit("TRUE") end -- DINGTHEBELL.scr:72
end

return script
