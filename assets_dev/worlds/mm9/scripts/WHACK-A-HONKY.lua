-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WHACK-A-HONKY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "ListMaker.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "ThjorgardGamesCommon.inc" }

-- Mastermind.scr
-- by SJR
-- 12-20-01
-- Purpose:chuckEcheese whack a mole
-- give script to each whackee.
-- 10 whacks in 10 seconds
script.labels["Main"] = function(ctx)
    -- WHACK-A-HONKY.scr:27
    ctx:getParam(0, "nMyIndex") -- WHACK-A-HONKY.scr:29
    ctx:getParam(1, "LISTNAME") -- WHACK-A-HONKY.scr:30
    ctx:getParam(2, "LISTFIRST") -- WHACK-A-HONKY.scr:31
    ctx:getParam(3, "LISTLAST") -- WHACK-A-HONKY.scr:32
    ctx:addTrigger("start", "StartGame") -- WHACK-A-HONKY.scr:34
    ctx:addTrigger("popup", "ReceivePopup") -- WHACK-A-HONKY.scr:35
    ctx:addTrigger("reset", "ResetPOS") -- WHACK-A-HONKY.scr:36
    -- global counter
    ctx:setConsoleNumVar("WHACK_COUNTER", 0) -- WHACK-A-HONKY.scr:39
    ctx:state().xMe, ctx:state().yMe, ctx:state().zMe = ctx:self():pos() -- WHACK-A-HONKY.scr:42
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:44
end

script.labels["StartGame"] = function(ctx)
    -- WHACK-A-HONKY.scr:47
    mm9.gosub(script, ctx, "CheckGameTicket") -- WHACK-A-HONKY.scr:49
    if ctx:condition("THJORGARD_RESULT==0") then -- WHACK-A-HONKY.scr:50
        do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:51
    else -- WHACK-A-HONKY.scr:52
        mm9.gosub(script, ctx, "TakeGameTicket") -- WHACK-A-HONKY.scr:53
    end -- WHACK-A-HONKY.scr:54
    -- set game in progress
    ctx:setConsoleNumVar("WHACK_RUNNING", "TRUE") -- WHACK-A-HONKY.scr:57
    mm9.gosub(script, ctx, "ResetPOS") -- WHACK-A-HONKY.scr:59
    -- timers for start and win
    mm9.gosub(script, ctx, "Countdown5") -- WHACK-A-HONKY.scr:62
    ctx:wait(0, 5, "ReceivePopup") -- WHACK-A-HONKY.scr:63
    ctx:wait(19, 15, "EndGame") -- WHACK-A-HONKY.scr:64
    mm9.gosub(script, ctx, "DisableInput") -- WHACK-A-HONKY.scr:66
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:68
end

script.labels["EndGame"] = function(ctx)
    -- WHACK-A-HONKY.scr:71
    -- what to do when player won\lost
    -- set game not in progress
    ctx:setConsoleNumVar("WHACK_RUNNING", "FALSE") -- WHACK-A-HONKY.scr:75
    ctx:getConsoleNumVar("WHACK_COUNTER", "nWhackCounter") -- WHACK-A-HONKY.scr:77
    if ctx:condition("nWhackCounter>=WIN_CONDITION") then -- WHACK-A-HONKY.scr:78
        mm9.gosub(script, ctx, "RecordHonkyWin") -- WHACK-A-HONKY.scr:79
    else -- WHACK-A-HONKY.scr:80
        ctx:rolloverText("TEXT_DEFEAT", 1, 3000, 2000) -- WHACK-A-HONKY.scr:81
    end -- WHACK-A-HONKY.scr:82
    -- reset counters
    ctx:setConsoleNumVar("WHACK_COUNTER", 0) -- WHACK-A-HONKY.scr:85
    ctx:state().nWhackCounter = 0 -- WHACK-A-HONKY.scr:86
    mm9.gosub(script, ctx, "EnableInput") -- WHACK-A-HONKY.scr:88
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:90
end

script.labels["ReceivePopup"] = function(ctx)
    -- WHACK-A-HONKY.scr:93
    -- received popup message
    -- raise me, allow whacking
    -- check if game running
    ctx:getConsoleNumVar("WHACK_RUNNING", "nTemp") -- WHACK-A-HONKY.scr:98
    if ctx:condition("nTemp==FALSE") then -- WHACK-A-HONKY.scr:99
        do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:100
    end -- WHACK-A-HONKY.scr:101
    -- enable user input
    ctx:addTrigger("use", "OnDamage") -- WHACK-A-HONKY.scr:104
    ctx:state().bSent = false -- WHACK-A-HONKY.scr:106
    ctx:self():moveDir(0, 1, 0, 20, 100, "OnFinishedRaise") -- WHACK-A-HONKY.scr:108
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:110
end

script.labels["OnDamage"] = function(ctx)
    -- WHACK-A-HONKY.scr:113
    -- play sound, check victory
    -- increment global counter
    ctx:getConsoleNumVar("WHACK_COUNTER", "nWhackCounter") -- WHACK-A-HONKY.scr:117
    ctx:set("nWhackCounter", "nWhackCounter + 1") -- WHACK-A-HONKY.scr:118
    ctx:setConsoleNumVar("WHACK_COUNTER", "nWhackCounter") -- WHACK-A-HONKY.scr:119
    ctx:playSound("sounds\\animsounds\\hen\\fidget01.wav", "DoNothing", 1, 1000, "FALSE", 100) -- WHACK-A-HONKY.scr:121
    mm9.gosub(script, ctx, "SendPopup") -- WHACK-A-HONKY.scr:123
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:125
end

script.labels["SendPopup"] = function(ctx)
    -- WHACK-A-HONKY.scr:128
    -- trigger another to raise
    -- lower me, and disable whacking
    -- only go down once
    if ctx:condition("bSent==TRUE") then -- WHACK-A-HONKY.scr:133
        do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:134
    else -- WHACK-A-HONKY.scr:135
        ctx:state().bSent = true -- WHACK-A-HONKY.scr:136
    end -- WHACK-A-HONKY.scr:137
    -- disable user input until finished
    ctx:removeTrigger("use") -- WHACK-A-HONKY.scr:140
    ctx:self():moveToPos("xMe", "yMe", "zMe", 100, "OnFinishedLower") -- WHACK-A-HONKY.scr:142
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:144
end

script.labels["OnFinishedRaise"] = function(ctx)
    -- WHACK-A-HONKY.scr:147
    -- wait before returning
    ctx:randomFloat(.5, 1, "dt") -- WHACK-A-HONKY.scr:150
    -- wait at top for a bit
    ctx:wait(0, "dt", "SendPopup") -- WHACK-A-HONKY.scr:153
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:155
end

script.labels["OnFinishedLower"] = function(ctx)
    -- WHACK-A-HONKY.scr:158
    -- trigger next random mole
    ctx:randomInt("LISTFIRST", "LISTLAST", "LISTINDEX") -- WHACK-A-HONKY.scr:161
    -- make sure we dont psych ourselves out
    while ctx:condition("LISTINDEX==nMyIndex") do -- WHACK-A-HONKY.scr:163
        ctx:randomInt("LISTFIRST", "LISTLAST", "LISTINDEX") -- WHACK-A-HONKY.scr:164
    end -- WHACK-A-HONKY.scr:165
    mm9.gosub(script, ctx, "GetCurrentObject") -- WHACK-A-HONKY.scr:167
    ctx:trigger("LISTOBJECT", "popup") -- WHACK-A-HONKY.scr:168
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:170
end

script.labels["DisableInput"] = function(ctx)
    -- WHACK-A-HONKY.scr:173
    ctx:removeTrigger("start") -- WHACK-A-HONKY.scr:175
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:177
end

script.labels["EnableInput"] = function(ctx)
    -- WHACK-A-HONKY.scr:180
    ctx:addTrigger("start", "StartGame") -- WHACK-A-HONKY.scr:182
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:184
end

script.labels["ResetPOS"] = function(ctx)
    -- WHACK-A-HONKY.scr:187
    ctx:self():setPos("xMe", "yMe", "zMe") -- WHACK-A-HONKY.scr:189
    do return ctx:exit("TRUE") end -- WHACK-A-HONKY.scr:191
end

return script
