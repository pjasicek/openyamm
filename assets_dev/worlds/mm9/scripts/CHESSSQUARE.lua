-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHESSSQUARE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 17, path = "ListMaker.inc" }

-- ChessSquare.scr
-- by SJR
-- 11-14-01
-- Purpose:chess attack puzzle
-- ScriptParams:
-- p0 = LISTNAME
-- p1 = LISTFIRST
-- p2 = LISTLAST
-- ChessSquare will ping pieces specified in p0->p2
-- when the player steps on it.
script.labels["Main"] = function(ctx)
    -- CHESSSQUARE.scr:27
    ctx:getParam(0, "LISTNAME") -- CHESSSQUARE.scr:29
    ctx:getParam(1, "LISTFIRST") -- CHESSSQUARE.scr:30
    ctx:getParam(2, "LISTLAST") -- CHESSSQUARE.scr:31
    ctx:addTrigger("off", "TurnOff") -- CHESSSQUARE.scr:33
    ctx:addTrigger("on", "TurnOn") -- CHESSSQUARE.scr:34
    ctx:onEvent("OnTouchNotify", "OnTouch") -- CHESSSQUARE.scr:36
    ctx:state().sMyName = ctx:self():name() -- CHESSSQUARE.scr:39
    do return ctx:exit("TRUE") end -- CHESSSQUARE.scr:41
end

script.labels["OnTouch"] = function(ctx)
    -- CHESSSQUARE.scr:44
    -- if player: turn me off, check danger
    if ctx:condition("hPlayer==0") then -- CHESSSQUARE.scr:47
    end -- CHESSSQUARE.scr:49
    ctx:getParam(0, "hDummy") -- CHESSSQUARE.scr:51
    if ctx:condition("hPlayer==hDummy") then -- CHESSSQUARE.scr:52
        mm9.gosub(script, ctx, "PingPieces") -- CHESSSQUARE.scr:53
        mm9.gosub(script, ctx, "UpdateInactiveSquare") -- CHESSSQUARE.scr:54
    end -- CHESSSQUARE.scr:55
    do return ctx:exit("TRUE") end -- CHESSSQUARE.scr:56
end

script.labels["UpdateInactiveSquare"] = function(ctx)
    -- CHESSSQUARE.scr:59
    -- moves the 'off'ness from previous
    -- square to this square
    mm9.gosub(script, ctx, "TurnOff") -- CHESSSQUARE.scr:63
    ctx:getConsoleStrVar("LASTSQUARE", "sLastOne") -- CHESSSQUARE.scr:64
    ctx:object("sLastOne"):trigger("on") -- CHESSSQUARE.scr:65-66
    ctx:setConsoleStrVar("LASTSQUARE", "sMyName") -- CHESSSQUARE.scr:67
    do return ctx:exit("TRUE") end -- CHESSSQUARE.scr:68
end

script.labels["PingPieces"] = function(ctx)
    -- CHESSSQUARE.scr:71
    -- send a 'CanYouAttack?' message
    -- to all the pieces
    mm9.gosub(script, ctx, "GetFirstObject") -- CHESSSQUARE.scr:75
    while ctx:condition("ARRIVEDLAST!=TRUE") do -- CHESSSQUARE.scr:76
        ctx:trigger("LISTOBJECT", "Ping") -- CHESSSQUARE.scr:77
        mm9.gosub(script, ctx, "GetNextObject") -- CHESSSQUARE.scr:78
    end -- CHESSSQUARE.scr:79
    ctx:trigger("LISTOBJECT", "Ping") -- CHESSSQUARE.scr:80
    do return ctx:exit("TRUE") end -- CHESSSQUARE.scr:81
end

script.labels["TurnOff"] = function(ctx)
    -- CHESSSQUARE.scr:84
    ctx:onEvent("OnTouchNotify", "DoNothing") -- CHESSSQUARE.scr:86
    do return ctx:exit("TRUE") end -- CHESSSQUARE.scr:87
end

script.labels["TurnOn"] = function(ctx)
    -- CHESSSQUARE.scr:89
    ctx:onEvent("OnTouchNotify", "OnTouch") -- CHESSSQUARE.scr:91
    do return ctx:exit("TRUE") end -- CHESSSQUARE.scr:92
end

return script
