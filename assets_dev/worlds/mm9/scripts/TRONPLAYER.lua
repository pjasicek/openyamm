-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRONPLAYER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }

-- TronPlayer.scr
-- by SJR
-- 12-12-01
-- Purpose:play the TronGame like
-- a total loser.
script.labels["Main"] = function(ctx)
    -- TRONPLAYER.scr:25
    ctx:getParam(0, "sPieceName") -- TRONPLAYER.scr:27
    ctx:getParam(1, "nTemp") -- TRONPLAYER.scr:28
    -- register this name
    ctx:command("getmyhandle", "hTron") -- TRONPLAYER.scr:31
    ctx:command("getobjectname", "hTron, sMyName") -- TRONPLAYER.scr:32
    ctx:setConsoleStrVar("TRON_PLAYER", "sMyName") -- TRONPLAYER.scr:33
    ctx:command("numsquares", "= nTemp * nTemp - 1") -- TRONPLAYER.scr:35
    ctx:command("onpoststartworld", "InitTronPlayer") -- TRONPLAYER.scr:37
    do return ctx:exit("TRUE") end -- TRONPLAYER.scr:39
end

script.labels["InitTronPlayer"] = function(ctx)
    -- TRONPLAYER.scr:42
    ctx:getConsoleStrVar("TRON_NAME", "sTronName") -- TRONPLAYER.scr:44
    ctx:command("getobjecthandle", "sTronName, hTron") -- TRONPLAYER.scr:45
    ctx:addTrigger("PlacePiece", "SelectPiece") -- TRONPLAYER.scr:47
    do return ctx:exit("TRUE") end -- TRONPLAYER.scr:49
end

script.labels["SelectPiece"] = function(ctx)
    -- TRONPLAYER.scr:52
    ctx:command("getrandomint", "0, NUMSQUARES, nTemp") -- TRONPLAYER.scr:54
    ctx:command("stemp", "= sPieceName + nTemp") -- TRONPLAYER.scr:55
    ctx:command("getobjecthandle", "sTemp, hPiece") -- TRONPLAYER.scr:56
    -- if( hPiece!=0 )
    -- GetRandomInt STALL_MIN, STALL_MAX, nTemp
    -- Wait 0, nTemp, PlacePiece
    -- endif
    mm9.gosub(script, ctx, "PlacePiece") -- TRONPLAYER.scr:63
    do return ctx:exit("TRUE") end -- TRONPLAYER.scr:65
end

script.labels["PlacePiece"] = function(ctx)
    -- TRONPLAYER.scr:68
    -- use a piece like the player would
    ctx:trigger("hPiece", "use") -- TRONPLAYER.scr:71
    do return ctx:exit("TRUE") end -- TRONPLAYER.scr:73
end

return script
