-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOATJUDGE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "ListMaker.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "ThjorgardGamesCommon.inc" }

-- BoatJudge.scr
-- by SJR
-- 12-12-01
-- Purpose:
-- a.) start the contest
-- b.) decide the winner
script.labels["Main"] = function(ctx)
    -- BOATJUDGE.scr:20
    ctx:getParam(0, "LISTNAME") -- BOATJUDGE.scr:22
    ctx:getParam(1, "LISTFIRST") -- BOATJUDGE.scr:23
    ctx:getParam(2, "LISTLAST") -- BOATJUDGE.scr:24
    ctx:command("getmyhandle", "LISTOBJECT") -- BOATJUDGE.scr:26
    ctx:command("getobjectname", "LISTOBJECT, sMyName") -- BOATJUDGE.scr:27
    ctx:setConsoleStrVar("BOAT_JUDGE", "sMyName") -- BOATJUDGE.scr:28
    ctx:onRudeExit("StartRace", script.labels["StartRace"]) -- BOATJUDGE.scr:30
    ctx:addTrigger("use", "OnUse") -- BOATJUDGE.scr:31
    do return ctx:exit("TRUE") end -- BOATJUDGE.scr:33
end

script.labels["OnUse"] = function(ctx)
    -- BOATJUDGE.scr:36
    ctx:giveKey("KEY_BOATTEXT") -- BOATJUDGE.scr:38
    do return ctx:exit("FALSE") end -- BOATJUDGE.scr:40
end

script.labels["StartRace"] = function(ctx)
    -- BOATJUDGE.scr:43
    ctx:takeKey("KEY_BOATTEXT") -- BOATJUDGE.scr:45
    ctx:hasKey("KEY_BOATRACE", "bWantsRace") -- BOATJUDGE.scr:46
    if ctx:condition("bWantsRace==FALSE") then -- BOATJUDGE.scr:47
        do return ctx:exit("TRUE") end -- BOATJUDGE.scr:48
    else -- BOATJUDGE.scr:49
        ctx:takeKey("KEY_BOATRACE") -- BOATJUDGE.scr:50
    end -- BOATJUDGE.scr:51
    mm9.gosub(script, ctx, "CheckGameTicket") -- BOATJUDGE.scr:53
    if ctx:condition("THJORGARD_RESULT==0") then -- BOATJUDGE.scr:54
        do return ctx:exit("TRUE") end -- BOATJUDGE.scr:55
    else -- BOATJUDGE.scr:56
        mm9.gosub(script, ctx, "TakeGameTicket") -- BOATJUDGE.scr:57
    end -- BOATJUDGE.scr:58
    ctx:addTrigger("CPUArrival", "AIWon") -- BOATJUDGE.scr:60
    ctx:addTrigger("PlayerArrival", "PlayerWon") -- BOATJUDGE.scr:61
    ctx:command("wait", "0, 5, SignalAiBoats") -- BOATJUDGE.scr:63
    mm9.gosub(script, ctx, "Countdown5") -- BOATJUDGE.scr:64
    do return ctx:exit("TRUE") end -- BOATJUDGE.scr:66
end

script.labels["SignalAiBoats"] = function(ctx)
    -- BOATJUDGE.scr:69
    mm9.gosub(script, ctx, "GetFirstObject") -- BOATJUDGE.scr:71
    while ctx:condition("LISTINDEX<LISTLAST") do -- BOATJUDGE.scr:73
        ctx:trigger("LISTOBJECT", "on") -- BOATJUDGE.scr:74
        mm9.gosub(script, ctx, "GetNextObject") -- BOATJUDGE.scr:75
    end -- BOATJUDGE.scr:76
    ctx:trigger("LISTOBJECT", "on") -- BOATJUDGE.scr:78
    do return ctx:exit("TRUE") end -- BOATJUDGE.scr:80
end

script.labels["DisableWinning"] = function(ctx)
    -- BOATJUDGE.scr:83
    ctx:command("removetrigger", "CPUArrival") -- BOATJUDGE.scr:85
    ctx:command("removetrigger", "PlayerArrival") -- BOATJUDGE.scr:86
    mm9.gosub(script, ctx, "SignalSubmerge") -- BOATJUDGE.scr:88
    do return ctx:exit("TRUE") end -- BOATJUDGE.scr:90
end

script.labels["AIWon"] = function(ctx)
    -- BOATJUDGE.scr:93
    mm9.gosub(script, ctx, "DisableWinning") -- BOATJUDGE.scr:95
    ctx:command("rollovertext", "TEXT_DEFEAT, 1, 3000, 2000") -- BOATJUDGE.scr:97
    do return ctx:exit("TRUE") end -- BOATJUDGE.scr:99
end

script.labels["PlayerWon"] = function(ctx)
    -- BOATJUDGE.scr:102
    ctx:command("playsound", "\"sounds\\events\\trumpets02.wav\", DoNothing, 1, 5000, FALSE, 100") -- BOATJUDGE.scr:104
    mm9.gosub(script, ctx, "DisableWinning") -- BOATJUDGE.scr:106
    mm9.gosub(script, ctx, "RecordBoatWin") -- BOATJUDGE.scr:107
    do return ctx:exit("TRUE") end -- BOATJUDGE.scr:109
end

script.labels["SignalSubmerge"] = function(ctx)
    -- BOATJUDGE.scr:112
    mm9.gosub(script, ctx, "GetFirstObject") -- BOATJUDGE.scr:114
    while ctx:condition("LISTINDEX<LISTLAST") do -- BOATJUDGE.scr:116
        ctx:trigger("LISTOBJECT", "submerge") -- BOATJUDGE.scr:117
        mm9.gosub(script, ctx, "GetNextObject") -- BOATJUDGE.scr:118
    end -- BOATJUDGE.scr:119
    ctx:trigger("LISTOBJECT", "submerge") -- BOATJUDGE.scr:121
    do return ctx:exit("TRUE") end -- BOATJUDGE.scr:123
end

return script
