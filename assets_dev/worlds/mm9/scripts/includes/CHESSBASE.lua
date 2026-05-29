-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHESSBASE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "ListMaker.inc" }

-- ChessBase.inc
-- by SJR
-- Purpose:base include. all the
-- stuff every piece does
-- must set these before calling initchessbase
script.labels["InitChessBase"] = function(ctx)
    -- CHESSBASE.inc:35
    -- sets up everything
    ctx:addTrigger("ping", "CheckPath") -- CHESSBASE.inc:38
    ctx:state().LISTFIRST = 0 -- CHESSBASE.inc:40
    ctx:set("LISTLAST", "BOARDSIZE * BOARDSIZE - 1") -- CHESSBASE.inc:41
    ctx:set("SIZEINDEX", "BOARDSIZE - 1") -- CHESSBASE.inc:42
    ctx:set("LISTNAME", "sSquareName") -- CHESSBASE.inc:43
    ctx:state().nTemp, ctx:state().yHeight, ctx:state().nTemp = ctx:self():pos() -- CHESSBASE.inc:46
    ctx:self():setStat("gravity", 0) -- CHESSBASE.inc:47
    ctx:getConsoleStrVar("CHESS_CAM", "sCameraName") -- CHESSBASE.inc:48
    ctx:state().hCamera = ctx:objectOrNil("sCameraName") -- CHESSBASE.inc:49
    mm9.gosub(script, ctx, "Create2DCoordinates") -- CHESSBASE.inc:51
    do return ctx:exit(1) end -- CHESSBASE.inc:53
end

script.labels["BeginAttack"] = function(ctx)
    -- CHESSBASE.inc:56
    -- if no other piece attacking, attack
    -- must set LISTINDEX prior to this
    -- must set hTrigger prior to this
    ctx:getConsoleNumVar("CLAIM_ATTACK", "nTemp") -- CHESSBASE.inc:61
    if ctx:condition("nTemp==1") then -- CHESSBASE.inc:62
        do return ctx:exit(1) end -- CHESSBASE.inc:63
    end -- CHESSBASE.inc:64
    ctx:set("nLocation", "LISTINDEX") -- CHESSBASE.inc:66
    mm9.gosub(script, ctx, "LockBoard") -- CHESSBASE.inc:68
    mm9.gosub(script, ctx, "Create2DCoordinates") -- CHESSBASE.inc:69
    mm9.gosub(script, ctx, "StartCamera") -- CHESSBASE.inc:70
    mm9.gosub(script, ctx, "AttackSquare") -- CHESSBASE.inc:71
    ctx:self():setFlag("8192", false) -- CHESSBASE.inc:73
    ctx:self():setFlag("2097152", true) -- CHESSBASE.inc:74
    do return ctx:exit(1) end -- CHESSBASE.inc:76
end

-- private
script.labels["Create2DCoordinates"] = function(ctx)
    -- CHESSBASE.inc:83
    -- changes (index) to (x,z)
    ctx:state().zMe = 0 -- CHESSBASE.inc:86
    while ctx:condition("nLocation>=BOARDSIZE") do -- CHESSBASE.inc:87
        ctx:set("nLocation", "nLocation - BOARDSIZE") -- CHESSBASE.inc:88
        ctx:set("zMe", "zMe + 1") -- CHESSBASE.inc:89
    end -- CHESSBASE.inc:90
    ctx:set("xMe", "nLocation") -- CHESSBASE.inc:91
    mm9.gosub(script, ctx, "Create1DCoordinates") -- CHESSBASE.inc:93
    do return ctx:exit(1) end -- CHESSBASE.inc:95
end

script.labels["Create1DCoordinates"] = function(ctx)
    -- CHESSBASE.inc:98
    -- changes (x,z) to (index)
    ctx:set("nLocation", "BOARDSIZE * zMe + xMe") -- CHESSBASE.inc:101
    do return ctx:exit(1) end -- CHESSBASE.inc:103
end

script.labels["LockBoard"] = function(ctx)
    -- CHESSBASE.inc:106
    -- register attack, disable input
    ctx:setConsoleNumVar("CLAIM_ATTACK", 1) -- CHESSBASE.inc:109
    ctx:removeTrigger("ping") -- CHESSBASE.inc:110
    do return ctx:exit(1) end -- CHESSBASE.inc:112
end

script.labels["UnlockBoard"] = function(ctx)
    -- CHESSBASE.inc:115
    -- unregister attack, enable input
    ctx:setConsoleNumVar("CLAIM_ATTACK", 0) -- CHESSBASE.inc:118
    ctx:addTrigger("ping", "CheckPath") -- CHESSBASE.inc:119
    do return ctx:exit(1) end -- CHESSBASE.inc:121
end

script.labels["CheckPath"] = function(ctx)
    -- CHESSBASE.inc:124
    -- override this to check spaces
    do return ctx:exit(1) end -- CHESSBASE.inc:127
end

script.labels["AttackSquare"] = function(ctx)
    -- CHESSBASE.inc:130
    -- moves to space
    ctx:state().nSpeed = ctx:self():distanceTo(ctx:object("hTrigger")) -- CHESSBASE.inc:133
    ctx:set("nSpeed", "nSpeed / 2") -- CHESSBASE.inc:134
    ctx:state().xSpace, ctx:state().nTemp, ctx:state().zSpace = ctx:object("hTrigger"):pos() -- CHESSBASE.inc:135
    ctx:self():moveToPos("xSpace", "yHeight", "zSpace", "nSpeed", "FinishAttack") -- CHESSBASE.inc:136
    ctx:playSound("sounds\\door\\doorslidestone.wav", "DoNothing", 1000, 2000, 0, 100) -- CHESSBASE.inc:138
    do return ctx:exit(1) end -- CHESSBASE.inc:140
end

script.labels["FinishAttack"] = function(ctx)
    -- CHESSBASE.inc:143
    -- snap to POS, check for pawn->queen, unlock board
    ctx:self():setPos("xSpace", "yHeight", "zSpace") -- CHESSBASE.inc:146
    mm9.gosub(script, ctx, "EndCamera") -- CHESSBASE.inc:148
    mm9.gosub(script, ctx, "PawnToQueen") -- CHESSBASE.inc:149
    mm9.gosub(script, ctx, "UnlockBoard") -- CHESSBASE.inc:150
    ctx:self():setFlag("8192", true) -- CHESSBASE.inc:152
    ctx:self():setFlag("2097152", false) -- CHESSBASE.inc:153
    ctx:set("LISTNAME", "sSquareName") -- CHESSBASE.inc:155
    do return ctx:exit(1) end -- CHESSBASE.inc:157
end

script.labels["PawnToQueen"] = function(ctx)
    -- CHESSBASE.inc:160
    -- if at the end of the board, change to queen
    if ctx:condition("zMe==SIZEINDEX") then -- CHESSBASE.inc:163
        if ctx:condition("bShouldQueen==1") then -- CHESSBASE.inc:164
            ctx:state().xSpace, ctx:state().yHeight, ctx:state().zSpace = ctx:self():pos() -- CHESSBASE.inc:165
            ctx:state().hTrigger = ctx:spawn("xSpace", "yHeight", "zSpace", "Terror") -- CHESSBASE.inc:166
            if ctx:condition("hTrigger!=0") then -- CHESSBASE.inc:167
                ctx:object("hTrigger"):setStat("HitPoints", 1069) -- CHESSBASE.inc:168
                ctx:object("hTrigger"):setStat("AC", 80) -- CHESSBASE.inc:169
                ctx:object("hTrigger"):doClientFx("fireblue", 0, 1) -- CHESSBASE.inc:170
            end -- CHESSBASE.inc:171
            ctx:self():remove() -- CHESSBASE.inc:172
        end -- CHESSBASE.inc:173
    end -- CHESSBASE.inc:174
    do return ctx:exit(1) end -- CHESSBASE.inc:176
end

script.labels["StartCamera"] = function(ctx)
    -- CHESSBASE.inc:179
    if ctx:condition("hCamera!=0") then -- CHESSBASE.inc:181
        ctx:trigger("hCamera", "look") -- CHESSBASE.inc:182
    end -- CHESSBASE.inc:183
    do return ctx:exit(1) end -- CHESSBASE.inc:185
end

script.labels["EndCamera"] = function(ctx)
    -- CHESSBASE.inc:188
    if ctx:condition("hCamera!=0") then -- CHESSBASE.inc:190
        ctx:trigger("hCamera", "turnoff") -- CHESSBASE.inc:191
    end -- CHESSBASE.inc:192
    do return ctx:exit(1) end -- CHESSBASE.inc:194
end

script.labels["DoNothing"] = function(ctx)
    -- CHESSBASE.inc:197
    do return ctx:exit(1) end -- CHESSBASE.inc:199
end

return script
