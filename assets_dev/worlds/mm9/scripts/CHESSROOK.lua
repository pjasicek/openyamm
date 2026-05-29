-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHESSROOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "ChessBase.inc" }

-- ChessRook.scr
-- by SJR
-- Purpose:Rook
script.labels["Main"] = function(ctx)
    -- CHESSROOK.scr:10
    ctx:getParam(0, "sSquareName") -- CHESSROOK.scr:12
    ctx:getParam(1, "sFloorName") -- CHESSROOK.scr:13
    ctx:getParam(2, "BOARDSIZE") -- CHESSROOK.scr:14
    ctx:getParam(3, "nLocation") -- CHESSROOK.scr:15
    ctx:onEvent("OnPostStartWorld", "InitChessBase") -- CHESSROOK.scr:17
    do return ctx:exit("TRUE") end -- CHESSROOK.scr:19
end

script.labels["CheckPath"] = function(ctx)
    -- CHESSROOK.scr:23
    ctx:getParam(0, "hTrigger") -- CHESSROOK.scr:25
    -- check vertical
    ctx:set("LISTINDEX", "xMe") -- CHESSROOK.scr:28
    while ctx:condition("LISTINDEX<=LISTLAST") do -- CHESSROOK.scr:29
        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSROOK.scr:30
        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSROOK.scr:31
            mm9.gosub(script, ctx, "BeginAttack") -- CHESSROOK.scr:32
            do return ctx:exit("TRUE") end -- CHESSROOK.scr:33
        end -- CHESSROOK.scr:34
        ctx:set("LISTINDEX", "LISTINDEX + BOARDSIZE") -- CHESSROOK.scr:36
    end -- CHESSROOK.scr:37
    -- check horizontal
    ctx:set("LISTINDEX", "nLocation - xMe") -- CHESSROOK.scr:40
    ctx:set("nTemp", "LISTINDEX + BOARDSIZE") -- CHESSROOK.scr:41
    while ctx:condition("LISTINDEX<nTemp") do -- CHESSROOK.scr:42
        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSROOK.scr:43
        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSROOK.scr:44
            mm9.gosub(script, ctx, "BeginAttack") -- CHESSROOK.scr:45
            do return ctx:exit("TRUE") end -- CHESSROOK.scr:46
        end -- CHESSROOK.scr:47
        ctx:set("LISTINDEX", "LISTINDEX + 1") -- CHESSROOK.scr:49
    end -- CHESSROOK.scr:50
    do return ctx:exit("TRUE") end -- CHESSROOK.scr:52
end

return script
