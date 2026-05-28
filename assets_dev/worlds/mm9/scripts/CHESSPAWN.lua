-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHESSPAWN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "ChessBase.inc" }

-- ChessPawn.scr
-- by SJR
-- Purpose:Pawn
script.labels["Main"] = function(ctx)
    -- CHESSPAWN.scr:10
    ctx:getParam(0, "sSquareName") -- CHESSPAWN.scr:12
    ctx:getParam(1, "sFloorName") -- CHESSPAWN.scr:13
    ctx:getParam(2, "BOARDSIZE") -- CHESSPAWN.scr:14
    ctx:getParam(3, "nLocation") -- CHESSPAWN.scr:15
    ctx:command("bshouldqueen", "= TRUE") -- CHESSPAWN.scr:17
    ctx:command("onpoststartworld", "InitChessBase") -- CHESSPAWN.scr:19
    do return ctx:exit("TRUE") end -- CHESSPAWN.scr:21
end

script.labels["PreAttackRoutine"] = function(ctx)
    -- CHESSPAWN.scr:24
    mm9.gosub(script, ctx, "BeginAttack") -- CHESSPAWN.scr:26
    do return ctx:exit("TRUE") end -- CHESSPAWN.scr:28
end

script.labels["CheckPath"] = function(ctx)
    -- CHESSPAWN.scr:31
    -- check 2 diag squares in front (front = +zMe)
    if ctx:condition("zMe>=BOARDSIZE") then -- CHESSPAWN.scr:34
        do return ctx:exit("TRUE") end -- CHESSPAWN.scr:35
    end -- CHESSPAWN.scr:36
    ctx:getParam(0, "hTrigger") -- CHESSPAWN.scr:38
    ctx:command("listindex", "= zMe + 1 * BOARDSIZE + xMe - 1") -- CHESSPAWN.scr:40
    if ctx:condition("xMe!=0") then -- CHESSPAWN.scr:41
        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSPAWN.scr:42
        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSPAWN.scr:43
            mm9.gosub(script, ctx, "PreAttackRoutine") -- CHESSPAWN.scr:44
            do return ctx:exit("TRUE") end -- CHESSPAWN.scr:45
        end -- CHESSPAWN.scr:46
    end -- CHESSPAWN.scr:47
    ctx:command("listindex", "= LISTINDEX + 2") -- CHESSPAWN.scr:49
    if ctx:condition("xMe!=SIZEINDEX") then -- CHESSPAWN.scr:50
        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSPAWN.scr:51
        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSPAWN.scr:52
            mm9.gosub(script, ctx, "PreAttackRoutine") -- CHESSPAWN.scr:53
            do return ctx:exit("TRUE") end -- CHESSPAWN.scr:54
        end -- CHESSPAWN.scr:55
    end -- CHESSPAWN.scr:56
    do return ctx:exit("TRUE") end -- CHESSPAWN.scr:58
end

return script
