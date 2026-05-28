-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STONESSQUARE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "flags.inc" }

-- StonesSquare.scr
-- by SJR
-- 12-12-01
-- Purpose:
script.labels["Main"] = function(ctx)
    -- STONESSQUARE.scr:19
    ctx:getParam(0, "sPieceName") -- STONESSQUARE.scr:21
    ctx:getParam(1, "nMyIndex") -- STONESSQUARE.scr:22
    ctx:command("onpoststartworld", "InitStonesSquare") -- STONESSQUARE.scr:24
    ctx:command("onpostminisaveload", "InitStonesSquare") -- STONESSQUARE.scr:25
    do return ctx:exit(1) end -- STONESSQUARE.scr:27
end

script.labels["InitStonesSquare"] = function(ctx)
    -- STONESSQUARE.scr:30
    ctx:command("getobjecthandle", "sPieceName, hPiece") -- STONESSQUARE.scr:32
    ctx:getConsoleStrVar("STONES_GAME", "sMgrName") -- STONESSQUARE.scr:34
    ctx:command("getobjecthandle", "sMgrName, hMgr") -- STONESSQUARE.scr:35
    ctx:addTrigger("use", "RequestMove") -- STONESSQUARE.scr:37
    ctx:addTrigger("white", "TurnPieceWhite") -- STONESSQUARE.scr:38
    ctx:addTrigger("black", "TurnPieceBlack") -- STONESSQUARE.scr:39
    ctx:addTrigger("clear", "TurnPieceClear") -- STONESSQUARE.scr:40
    do return ctx:exit(1) end -- STONESSQUARE.scr:42
end

script.labels["RequestMove"] = function(ctx)
    -- STONESSQUARE.scr:45
    if ctx:condition("hMgr!=0") then -- STONESSQUARE.scr:47
        ctx:setConsoleNumVar("STONES_INDEX", "nMyIndex") -- STONESSQUARE.scr:48
        ctx:trigger("hMgr", "move") -- STONESSQUARE.scr:49
    end -- STONESSQUARE.scr:50
    do return ctx:exit(1) end -- STONESSQUARE.scr:52
end

script.labels["TurnPieceWhite"] = function(ctx)
    -- STONESSQUARE.scr:55
    if ctx:condition("hPiece!=0") then -- STONESSQUARE.scr:57
        ctx:command("setflag", "hPiece, FLAG_VISIBLE") -- STONESSQUARE.scr:58
        ctx:trigger("hPiece", "white") -- STONESSQUARE.scr:59
    end -- STONESSQUARE.scr:60
    do return ctx:exit(1) end -- STONESSQUARE.scr:62
end

script.labels["TurnPieceBlack"] = function(ctx)
    -- STONESSQUARE.scr:65
    if ctx:condition("hPiece!=0") then -- STONESSQUARE.scr:67
        ctx:command("setflag", "hPiece, FLAG_VISIBLE") -- STONESSQUARE.scr:68
        ctx:trigger("hPiece", "black") -- STONESSQUARE.scr:69
    end -- STONESSQUARE.scr:70
    do return ctx:exit(1) end -- STONESSQUARE.scr:72
end

script.labels["TurnPieceClear"] = function(ctx)
    -- STONESSQUARE.scr:75
    if ctx:condition("hPiece!=0") then -- STONESSQUARE.scr:77
        ctx:command("clearflag", "hPiece, FLAG_VISIBLE") -- STONESSQUARE.scr:78
    end -- STONESSQUARE.scr:79
    do return ctx:exit(1) end -- STONESSQUARE.scr:81
end

return script
