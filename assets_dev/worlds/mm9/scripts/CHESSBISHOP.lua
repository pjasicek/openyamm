-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHESSBISHOP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "ChessBase.inc" }

-- ChessBishop.scr
-- by SJR
-- Purpose:Bishop
script.labels["Main"] = function(ctx)
    -- CHESSBISHOP.scr:10
    ctx:getParam(0, "sSquareName") -- CHESSBISHOP.scr:12
    ctx:getParam(1, "sFloorName") -- CHESSBISHOP.scr:13
    ctx:getParam(2, "BOARDSIZE") -- CHESSBISHOP.scr:14
    ctx:getParam(3, "nLocation") -- CHESSBISHOP.scr:15
    ctx:command("onpoststartworld", "InitChessBase") -- CHESSBISHOP.scr:17
    do return ctx:exit("TRUE") end -- CHESSBISHOP.scr:19
end

script.labels["PreAttackRoutine"] = function(ctx)
    -- CHESSBISHOP.scr:28
    mm9.gosub(script, ctx, "BeginAttack") -- CHESSBISHOP.scr:30
    do return ctx:exit("TRUE") end -- CHESSBISHOP.scr:32
end

script.labels["CheckPath"] = function(ctx)
    -- CHESSBISHOP.scr:35
    -- check the (0,0)->(N,N) direction
    -- check the (0,N)->(N,0) direction
    ctx:command("battacked", "= FALSE") -- CHESSBISHOP.scr:39
    ctx:getParam(0, "hTrigger") -- CHESSBISHOP.scr:40
    ctx:command("diag_dir", "= 1") -- CHESSBISHOP.scr:42
    mm9.gosub(script, ctx, "CheckDiagonal") -- CHESSBISHOP.scr:43
    if ctx:condition("bAttacked==FALSE") then -- CHESSBISHOP.scr:45
        ctx:command("diag_dir", "= -1") -- CHESSBISHOP.scr:46
        mm9.gosub(script, ctx, "CheckDiagonal") -- CHESSBISHOP.scr:47
    end -- CHESSBISHOP.scr:48
    do return ctx:exit("TRUE") end -- CHESSBISHOP.scr:50
end

script.labels["CheckDiagonal"] = function(ctx)
    -- CHESSBISHOP.scr:53
    -- shifts pos of piece to
    -- sides of board and checks
    -- diagonal from there
    mm9.gosub(script, ctx, "NormalizeDiagonal") -- CHESSBISHOP.scr:58
    -- diagonal boardlength adjusted for direction
    ctx:command("diag_size", "= BOARDSIZE * DIAG_DIR + 1") -- CHESSBISHOP.scr:61
    ctx:command("listindex", "= zTemp * BOARDSIZE + xTemp") -- CHESSBISHOP.scr:62
    while ctx:condition("nSquares>0") do -- CHESSBISHOP.scr:64
        ctx:command("nsquares", "= nSquares - 1") -- CHESSBISHOP.scr:65
        if ctx:condition("LISTINDEX!=nLocation") then -- CHESSBISHOP.scr:67
            mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSBISHOP.scr:68
            if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSBISHOP.scr:69
                mm9.gosub(script, ctx, "PreAttackRoutine") -- CHESSBISHOP.scr:70
                ctx:command("battacked", "= TRUE") -- CHESSBISHOP.scr:71
                do return ctx:exit("TRUE") end -- CHESSBISHOP.scr:72
            end -- CHESSBISHOP.scr:73
        end -- CHESSBISHOP.scr:74
        -- shift to next diagonal
        ctx:command("listindex", "= LISTINDEX + DIAG_SIZE") -- CHESSBISHOP.scr:77
    end -- CHESSBISHOP.scr:78
    do return ctx:exit("TRUE") end -- CHESSBISHOP.scr:80
end

script.labels["NormalizeDiagonal"] = function(ctx)
    -- CHESSBISHOP.scr:83
    -- shifts the pos of the piece
    -- to the sides of the board
    ctx:command("xtemp", "= xMe") -- CHESSBISHOP.scr:87
    ctx:command("ztemp", "= zMe") -- CHESSBISHOP.scr:88
    if ctx:condition("DIAG_DIR>0") then -- CHESSBISHOP.scr:90
        if ctx:condition("xTemp==zTemp") then -- CHESSBISHOP.scr:91
            ctx:command("xtemp", "= 0") -- CHESSBISHOP.scr:92
            ctx:command("ztemp", "= 0") -- CHESSBISHOP.scr:93
        end -- CHESSBISHOP.scr:94
        if ctx:condition("xTemp>zTemp") then -- CHESSBISHOP.scr:95
            ctx:command("xtemp", "= xTemp - zTemp") -- CHESSBISHOP.scr:96
            ctx:command("ztemp", "= 0") -- CHESSBISHOP.scr:97
        end -- CHESSBISHOP.scr:98
        if ctx:condition("xTemp<zTemp") then -- CHESSBISHOP.scr:99
            ctx:command("ztemp", "= zTemp - xTemp") -- CHESSBISHOP.scr:100
            ctx:command("xtemp", "= 0") -- CHESSBISHOP.scr:101
        end -- CHESSBISHOP.scr:102
    end -- CHESSBISHOP.scr:103
    if ctx:condition("DIAG_DIR<0") then -- CHESSBISHOP.scr:104
        ctx:command("ntemp", "=\tSIZEINDEX - xTemp - zTemp") -- CHESSBISHOP.scr:105
        if ctx:condition("nTemp == 0") then -- CHESSBISHOP.scr:106
            ctx:command("xtemp", "= 0") -- CHESSBISHOP.scr:107
            ctx:command("ztemp", "= SIZEINDEX") -- CHESSBISHOP.scr:108
        end -- CHESSBISHOP.scr:109
        if ctx:condition("nTemp<0") then -- CHESSBISHOP.scr:110
            ctx:command("xtemp", "= xTemp - BOARDSIZE + zTemp + 1") -- CHESSBISHOP.scr:111
            ctx:command("ztemp", "= SIZEINDEX") -- CHESSBISHOP.scr:112
        end -- CHESSBISHOP.scr:113
        if ctx:condition("nTemp>0") then -- CHESSBISHOP.scr:114
            ctx:command("ztemp", "= xTemp + zTemp") -- CHESSBISHOP.scr:115
            if ctx:condition("zTemp<0") then -- CHESSBISHOP.scr:116
                ctx:command("ztemp", "= zTemp * -1") -- CHESSBISHOP.scr:117
            end -- CHESSBISHOP.scr:118
            ctx:command("xtemp", "= 0") -- CHESSBISHOP.scr:119
        end -- CHESSBISHOP.scr:120
    end -- CHESSBISHOP.scr:121
    if ctx:condition("xTemp==0") then -- CHESSBISHOP.scr:122
        ctx:command("nsquares", "= BOARDSIZE - zTemp") -- CHESSBISHOP.scr:123
    end -- CHESSBISHOP.scr:124
    if ctx:condition("zTemp==0") then -- CHESSBISHOP.scr:125
        ctx:command("nsquares", "= BOARDSIZE - xTemp") -- CHESSBISHOP.scr:126
    end -- CHESSBISHOP.scr:127
    if ctx:condition("zTemp==SIZEINDEX") then -- CHESSBISHOP.scr:128
        ctx:command("nsquares", "= BOARDSIZE - xTemp") -- CHESSBISHOP.scr:129
    end -- CHESSBISHOP.scr:130
    do return ctx:exit("TRUE") end -- CHESSBISHOP.scr:132
end

script.labels["CheckCollision"] = function(ctx)
    -- CHESSBISHOP.scr:135
    -- checks for pieces in the way
    -- GetPOS hTrigger, xSpace, nTemp, zSpace
    -- VecDist xSpace, 0, zSpace, xMe, 0, zMe, nTemp
    -- dx =
    -- CastRay <dirX>,0,<dirZ>,<dist>,<hHit>,<nHitdist>
    -- nTemp = 0
    do return ctx:exit(1) end -- CHESSBISHOP.scr:145
end

return script
