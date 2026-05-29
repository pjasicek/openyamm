-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHESSPIECE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 18, path = "ListMaker.inc" }
script.includes[#script.includes + 1] = { line = 19, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 20, path = "flags.inc" }

-- ChessPiece.scr
-- by SJR
-- 11-14-01
-- Purpose:pieces attack you when
-- when you walk on a square
-- that they are guarding.
-- Works for any N x N board
-- ScriptParams:
-- p0 = root name of square script objects
-- p1 = root name of square world objects
-- p2 = size of board (N in NxN)
-- p3 = index of starting square
-- p4 = type of piece (0 pawn,1 knight,2 bishop)
script.labels["Main"] = function(ctx)
    -- CHESSPIECE.scr:50
    ctx:getParam(0, "sSquareName") -- CHESSPIECE.scr:52
    ctx:getParam(1, "sFloorName") -- CHESSPIECE.scr:53
    ctx:getParam(2, "BOARDSIZE") -- CHESSPIECE.scr:54
    ctx:getParam(3, "nLocation") -- CHESSPIECE.scr:55
    ctx:getParam(4, "nPieceType") -- CHESSPIECE.scr:56
    -- convert 1-D coordinates to 2-D
    while ctx:condition("nLocation>=BOARDSIZE") do -- CHESSPIECE.scr:59
        ctx:set("nLocation", "nLocation - BOARDSIZE") -- CHESSPIECE.scr:60
        ctx:set("zMe", "zMe + 1") -- CHESSPIECE.scr:61
    end -- CHESSPIECE.scr:62
    ctx:set("xMe", "nLocation") -- CHESSPIECE.scr:63
    ctx:set("nLocation", "BOARDSIZE * zMe + xMe") -- CHESSPIECE.scr:64
    ctx:set("LISTNAME", "sSquareName") -- CHESSPIECE.scr:66
    ctx:state().LISTFIRST = 0 -- CHESSPIECE.scr:67
    ctx:set("LISTLAST", "BOARDSIZE * BOARDSIZE - 1") -- CHESSPIECE.scr:68
    ctx:set("SIZEINDEX", "BOARDSIZE - 1") -- CHESSPIECE.scr:69
    ctx:onEvent("OnPostStartWorld", "InitChessPiece") -- CHESSPIECE.scr:71
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:73
end

script.labels["InitChessPiece"] = function(ctx)
    -- CHESSPIECE.scr:79
    ctx:setCallback("TYPE_PAWN", "CheckPawnPath") -- CHESSPIECE.scr:81
    ctx:setCallback("TYPE_KNIGHT", "CheckKnightPath") -- CHESSPIECE.scr:82
    ctx:setCallback("TYPE_BISHOP", "CheckBishopPath") -- CHESSPIECE.scr:83
    ctx:setConsoleNumVar("CLAIM_ATTACK", "FALSE") -- CHESSPIECE.scr:85
    -- message to check our danger zones
    ctx:addTrigger("Ping", "CheckBoard") -- CHESSPIECE.scr:88
    ctx:state().hCamera = ctx:objectOrNil("CinemaMgr") -- CHESSPIECE.scr:90
    ctx:state().nTemp, ctx:state().cy, ctx:state().nTemp = ctx:self():pos() -- CHESSPIECE.scr:92
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:94
end

script.labels["CheckBoard"] = function(ctx)
    -- CHESSPIECE.scr:97
    ctx:getParam(0, "hTrigger") -- CHESSPIECE.scr:99
    ctx:doCallback("nPieceType") -- CHESSPIECE.scr:100
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:102
end

script.labels["HostileMove"] = function(ctx)
    -- CHESSPIECE.scr:105
    -- attack hTrigger pos,
    -- update xMe,zMe,nLocation
    -- check to see if someone else is attacking already
    ctx:getConsoleNumVar("CLAIM_ATTACK", "nTemp") -- CHESSPIECE.scr:110
    if ctx:condition("nTemp==TRUE") then -- CHESSPIECE.scr:111
        -- somebody else is attacking
        do return ctx:exit("TRUE") end -- CHESSPIECE.scr:113
    else -- CHESSPIECE.scr:114
        -- register as the attacker
        ctx:setConsoleNumVar("CLAIM_ATTACK", "TRUE") -- CHESSPIECE.scr:116
    end -- CHESSPIECE.scr:117
    ctx:removeTrigger("Ping") -- CHESSPIECE.scr:118
    mm9.gosub(script, ctx, "StartAttack") -- CHESSPIECE.scr:119
    ctx:set("nLocation", "LISTINDEX") -- CHESSPIECE.scr:120
    ctx:state().zMe = 0 -- CHESSPIECE.scr:121
    -- convert 1-D coordinates to 2-D
    while ctx:condition("nLocation>=BOARDSIZE") do -- CHESSPIECE.scr:123
        ctx:set("nLocation", "nLocation - BOARDSIZE") -- CHESSPIECE.scr:124
        ctx:set("zMe", "zMe + 1") -- CHESSPIECE.scr:125
    end -- CHESSPIECE.scr:126
    ctx:set("xMe", "nLocation") -- CHESSPIECE.scr:127
    ctx:set("nLocation", "LISTINDEX") -- CHESSPIECE.scr:128
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:130
end

script.labels["StartAttack"] = function(ctx)
    -- CHESSPIECE.scr:133
    ctx:trigger("hCamera", "StartPanHere") -- CHESSPIECE.scr:135
    ctx:self():setFlag("FLAG_SOLID", false) -- CHESSPIECE.scr:136
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- CHESSPIECE.scr:137
    ctx:playSound("sounds\\door\\doorslidestone.wav", "DoNothing", 1000, 2000, "FALSE", 100) -- CHESSPIECE.scr:138
    if ctx:condition("hPlayer==0") then -- CHESSPIECE.scr:139
    end -- CHESSPIECE.scr:141
    ctx:state().cx, ctx:state().nTemp, ctx:state().cz = ctx:player():pos() -- CHESSPIECE.scr:142
    ctx:self():moveToPos("cx", "cy", "cz", 128, "FinishAttack") -- CHESSPIECE.scr:143
    mm9.gosub(script, ctx, "RemoveFloor") -- CHESSPIECE.scr:144
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:145
end

script.labels["RemoveFloor"] = function(ctx)
    -- CHESSPIECE.scr:148
    ctx:set("LISTNAME", "sFloorName") -- CHESSPIECE.scr:150
    mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSPIECE.scr:151
    ctx:set("hTrigger", "LISTOBJECT") -- CHESSPIECE.scr:152
    ctx:object("hTrigger"):setFlag("FLAG_SOLID", false) -- CHESSPIECE.scr:153
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:154
end

script.labels["FinishAttack"] = function(ctx)
    -- CHESSPIECE.scr:157
    ctx:player():setVelocity(0, -1, 0) -- CHESSPIECE.scr:159
    ctx:trigger("hCamera", "TurnOff") -- CHESSPIECE.scr:160
    ctx:self():setFlag("FLAG_SOLID", true) -- CHESSPIECE.scr:161
    ctx:self():setFlag("FLAG_GOTHRUWORLD", false) -- CHESSPIECE.scr:162
    ctx:set("LISTNAME", "sSquareName") -- CHESSPIECE.scr:163
    ctx:state().cx, ctx:state().nTemp, ctx:state().cz = ctx:object("hTrigger"):pos() -- CHESSPIECE.scr:164
    ctx:self():setPos("cx", "cy", "cz") -- CHESSPIECE.scr:165
    ctx:addTrigger("Ping", "CheckBoard") -- CHESSPIECE.scr:166
    ctx:object("hTrigger"):setFlag("FLAG_SOLID", true) -- CHESSPIECE.scr:167
    if ctx:condition("nPieceType==TYPE_PAWN") then -- CHESSPIECE.scr:168
        mm9.gosub(script, ctx, "CheckForQueen") -- CHESSPIECE.scr:169
    end -- CHESSPIECE.scr:170
    -- allow attacks again
    ctx:setConsoleNumVar("CLAIM_ATTACK", "FALSE") -- CHESSPIECE.scr:172
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:173
end

script.labels["CheckPawnPath"] = function(ctx)
    -- CHESSPIECE.scr:176
    -- check 2 diag squares in front (front = +z)
    if ctx:condition("zMe>=BOARDSIZE") then -- CHESSPIECE.scr:179
        do return ctx:exit("TRUE") end -- CHESSPIECE.scr:180
    end -- CHESSPIECE.scr:181
    -- (((( zMe + 1 ) * BOARDSIZE ) + xMe ) - 1 )
    ctx:set("LISTINDEX", "zMe + 1 * BOARDSIZE + xMe - 1") -- CHESSPIECE.scr:184
    if ctx:condition("xMe!=0") then -- CHESSPIECE.scr:185
        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSPIECE.scr:186
        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSPIECE.scr:187
            mm9.gosub(script, ctx, "HostileMove") -- CHESSPIECE.scr:188
            -- if we dont exit here, a different LISTOBJECT may
            -- be made solid\nonsolid than the one we move to
            -- by the time we get to that point
            do return ctx:exit("TRUE") end -- CHESSPIECE.scr:192
        end -- CHESSPIECE.scr:193
    end -- CHESSPIECE.scr:194
    if ctx:condition("xMe!=SIZEINDEX") then -- CHESSPIECE.scr:195
        ctx:set("LISTINDEX", "LISTINDEX + 2") -- CHESSPIECE.scr:196
        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSPIECE.scr:197
        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSPIECE.scr:198
            mm9.gosub(script, ctx, "HostileMove") -- CHESSPIECE.scr:199
            do return ctx:exit("TRUE") end -- CHESSPIECE.scr:200
        end -- CHESSPIECE.scr:201
    end -- CHESSPIECE.scr:202
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:203
end

script.labels["CheckKnightPath"] = function(ctx)
    -- CHESSPIECE.scr:208
    -- check 8 knight squares
    ctx:state().nSquares = 8 -- CHESSPIECE.scr:211
    ctx:state().dx = 1 -- CHESSPIECE.scr:212
    ctx:state().dz = 2 -- CHESSPIECE.scr:213
    -- 4 passes checking 2 squares at a time
    while ctx:condition("nSquares>0") do -- CHESSPIECE.scr:216
        -- change to second z after we checked
        -- all 4 x's for the first z
        if ctx:condition("nSquares==4") then -- CHESSPIECE.scr:219
            ctx:state().dx = 2 -- CHESSPIECE.scr:220
            ctx:state().dz = 1 -- CHESSPIECE.scr:221
        end -- CHESSPIECE.scr:222
        ctx:set("zTemp", "zMe + dz") -- CHESSPIECE.scr:224
        -- check z boundaries of board
        if ctx:condition("zTemp<BOARDSIZE") then -- CHESSPIECE.scr:226
            if ctx:condition("zTemp>=0") then -- CHESSPIECE.scr:227
                -- ping the first x square at this z
                ctx:set("xTemp", "xMe + dx") -- CHESSPIECE.scr:229
                -- check x boundaries of board
                if ctx:condition("xTemp<BOARDSIZE") then -- CHESSPIECE.scr:231
                    if ctx:condition("xTemp >= 0") then -- CHESSPIECE.scr:232
                        -- change index coords to plane coords
                        ctx:set("LISTINDEX", "BOARDSIZE * zTemp + xMe + dx") -- CHESSPIECE.scr:234
                        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSPIECE.scr:235
                        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSPIECE.scr:236
                            mm9.gosub(script, ctx, "HostileMove") -- CHESSPIECE.scr:237
                            do return ctx:exit("TRUE") end -- CHESSPIECE.scr:238
                        end -- CHESSPIECE.scr:239
                    end -- CHESSPIECE.scr:240
                end -- CHESSPIECE.scr:241
                ctx:set("xTemp", "xMe - dx") -- CHESSPIECE.scr:243
                -- ping the second x square at this z
                -- check x boundaries of board
                if ctx:condition("xTemp<BOARDSIZE") then -- CHESSPIECE.scr:246
                    if ctx:condition("xTemp>=0") then -- CHESSPIECE.scr:247
                        -- change index coords to plane coords
                        ctx:set("LISTINDEX", "BOARDSIZE * zTemp + xMe - dx") -- CHESSPIECE.scr:249
                        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSPIECE.scr:250
                        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSPIECE.scr:251
                            mm9.gosub(script, ctx, "HostileMove") -- CHESSPIECE.scr:252
                            do return ctx:exit("TRUE") end -- CHESSPIECE.scr:253
                        end -- CHESSPIECE.scr:254
                    end -- CHESSPIECE.scr:255
                end -- CHESSPIECE.scr:256
            end -- CHESSPIECE.scr:257
        end -- CHESSPIECE.scr:258
        -- check the same x's, but on the other side
        ctx:set("dz", "dz * -1") -- CHESSPIECE.scr:261
        ctx:set("nSquares", "nSquares - 2") -- CHESSPIECE.scr:263
    end -- CHESSPIECE.scr:265
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:267
end

script.labels["CheckBishopPath"] = function(ctx)
    -- CHESSPIECE.scr:270
    -- calls CheckDiagonal twice
    -- check the (0,0)->(N,N) direction
    ctx:state().nCheckDir = 1 -- CHESSPIECE.scr:274
    mm9.gosub(script, ctx, "CheckDiagonal") -- CHESSPIECE.scr:275
    -- check the (0,N)->(N,0) direction
    ctx:state().nCheckDir = -1 -- CHESSPIECE.scr:278
    mm9.gosub(script, ctx, "CheckDiagonal") -- CHESSPIECE.scr:279
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:281
end

script.labels["CheckDiagonal"] = function(ctx)
    -- CHESSPIECE.scr:285
    -- shifts pos of piece to
    -- sides of board and checks
    -- diagonal from there
    mm9.gosub(script, ctx, "NormalizeDiagonal") -- CHESSPIECE.scr:290
    -- diagonal boardlength adjusted for direction
    ctx:set("DIAGSIZE", "BOARDSIZE * nCheckDir + 1") -- CHESSPIECE.scr:293
    ctx:set("LISTINDEX", "zTemp * BOARDSIZE + xTemp") -- CHESSPIECE.scr:294
    while ctx:condition("nSquares>0") do -- CHESSPIECE.scr:296
        ctx:set("nSquares", "nSquares - 1") -- CHESSPIECE.scr:297
        if ctx:condition("LISTINDEX!=nLocation") then -- CHESSPIECE.scr:299
            mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSPIECE.scr:300
            if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSPIECE.scr:301
                mm9.gosub(script, ctx, "HostileMove") -- CHESSPIECE.scr:302
            end -- CHESSPIECE.scr:303
        end -- CHESSPIECE.scr:304
        -- shift to next diagonal
        ctx:set("LISTINDEX", "LISTINDEX + DIAGSIZE") -- CHESSPIECE.scr:307
    end -- CHESSPIECE.scr:308
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:310
end

script.labels["NormalizeDiagonal"] = function(ctx)
    -- CHESSPIECE.scr:313
    -- shifts the pos of the piece
    -- to the sides of the board
    ctx:set("xTemp", "xMe") -- CHESSPIECE.scr:317
    ctx:set("zTemp", "zMe") -- CHESSPIECE.scr:318
    if ctx:condition("nCheckDir>0") then -- CHESSPIECE.scr:320
        if ctx:condition("xTemp==zTemp") then -- CHESSPIECE.scr:321
            ctx:state().xTemp = 0 -- CHESSPIECE.scr:322
            ctx:state().zTemp = 0 -- CHESSPIECE.scr:323
        end -- CHESSPIECE.scr:324
        if ctx:condition("xTemp>zTemp") then -- CHESSPIECE.scr:325
            ctx:set("xTemp", "xTemp - zTemp") -- CHESSPIECE.scr:326
            ctx:state().zTemp = 0 -- CHESSPIECE.scr:327
        end -- CHESSPIECE.scr:328
        if ctx:condition("xTemp<zTemp") then -- CHESSPIECE.scr:329
            ctx:set("zTemp", "zTemp - xTemp") -- CHESSPIECE.scr:330
            ctx:state().xTemp = 0 -- CHESSPIECE.scr:331
        end -- CHESSPIECE.scr:332
    end -- CHESSPIECE.scr:333
    if ctx:condition("nCheckDir<0") then -- CHESSPIECE.scr:334
        ctx:set("nTemp", "SIZEINDEX - xTemp - zTemp") -- CHESSPIECE.scr:335
        if ctx:condition("nTemp == 0") then -- CHESSPIECE.scr:336
            ctx:state().xTemp = 0 -- CHESSPIECE.scr:337
            ctx:set("zTemp", "SIZEINDEX") -- CHESSPIECE.scr:338
        end -- CHESSPIECE.scr:339
        if ctx:condition("nTemp<0") then -- CHESSPIECE.scr:340
            ctx:set("xTemp", "xTemp - BOARDSIZE + zTemp + 1") -- CHESSPIECE.scr:341
            ctx:set("zTemp", "SIZEINDEX") -- CHESSPIECE.scr:342
        end -- CHESSPIECE.scr:343
        if ctx:condition("nTemp>0") then -- CHESSPIECE.scr:344
            ctx:set("zTemp", "xTemp + zTemp") -- CHESSPIECE.scr:345
            if ctx:condition("zTemp<0") then -- CHESSPIECE.scr:346
                ctx:set("zTemp", "zTemp * -1") -- CHESSPIECE.scr:347
            end -- CHESSPIECE.scr:348
            ctx:state().xTemp = 0 -- CHESSPIECE.scr:349
        end -- CHESSPIECE.scr:350
    end -- CHESSPIECE.scr:351
    if ctx:condition("xTemp==0") then -- CHESSPIECE.scr:352
        ctx:set("nSquares", "BOARDSIZE - zTemp") -- CHESSPIECE.scr:353
    end -- CHESSPIECE.scr:354
    if ctx:condition("zTemp==0") then -- CHESSPIECE.scr:355
        ctx:set("nSquares", "BOARDSIZE - xTemp") -- CHESSPIECE.scr:356
    end -- CHESSPIECE.scr:357
    if ctx:condition("zTemp==SIZEINDEX") then -- CHESSPIECE.scr:358
        ctx:set("nSquares", "BOARDSIZE - xTemp") -- CHESSPIECE.scr:359
    end -- CHESSPIECE.scr:360
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:362
end

script.labels["CheckForQueen"] = function(ctx)
    -- CHESSPIECE.scr:366
    if ctx:condition("zMe==SIZEINDEX") then -- CHESSPIECE.scr:368
        ctx:state().xMe, ctx:state().yMe, ctx:state().zMe = ctx:self():pos() -- CHESSPIECE.scr:369
        ctx:state().hDummy = ctx:spawn("xMe", "yMe", "zMe", "Eye") -- CHESSPIECE.scr:370
        ctx:self():remove() -- CHESSPIECE.scr:371
    end -- CHESSPIECE.scr:372
    do return ctx:exit("TRUE") end -- CHESSPIECE.scr:373
end

return script
