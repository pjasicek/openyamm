-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STONESGAME.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "ListMaker.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "flags.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "ThjorgardGamesCommon.inc" }

-- StonesGame.scr
-- by SJR
-- 12-12-01
-- Purpose:
script.labels["Main"] = function(ctx)
    -- STONESGAME.scr:39
    ctx:getParam(0, "LISTNAME") -- STONESGAME.scr:41
    ctx:getParam(1, "BOARDSIZE") -- STONESGAME.scr:42
    ctx:state().hSquare = ctx:self() -- STONESGAME.scr:44
    ctx:state().sSquareName = ctx:object("hSquare"):name() -- STONESGAME.scr:45
    ctx:setConsoleStrVar("STONES_GAME", "sSquareName") -- STONESGAME.scr:46
    ctx:state().LISTFIRST = 0 -- STONESGAME.scr:48
    ctx:set("LISTLAST", "BOARDSIZE * BOARDSIZE - 1") -- STONESGAME.scr:49
    ctx:onEvent("OnPostStartWorld", "InitStonesGame") -- STONESGAME.scr:51
    ctx:onEvent("OnPostMiniSaveLoad", "InitStonesGame") -- STONESGAME.scr:52
    ctx:addTrigger("move", "CheckMove") -- STONESGAME.scr:54
    do return ctx:exit("TRUE") end -- STONESGAME.scr:56
end

script.labels["InitStonesGame"] = function(ctx)
    -- STONESGAME.scr:59
    ctx:getConsoleStrVar("STONES_PLAYER", "sBotName") -- STONESGAME.scr:61
    ctx:state().hBot = ctx:objectOrNil("sBotName") -- STONESGAME.scr:62
    if ctx:condition("hBot!=0") then -- STONESGAME.scr:63
        ctx:self():link(ctx:object("hBot")) -- STONESGAME.scr:64
        ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- STONESGAME.scr:65
    end -- STONESGAME.scr:66
    mm9.gosub(script, ctx, "SetupCheck") -- STONESGAME.scr:68
    mm9.gosub(script, ctx, "ResetVars") -- STONESGAME.scr:69
    mm9.gosub(script, ctx, "ResetBoard") -- STONESGAME.scr:70
    do return ctx:exit("TRUE") end -- STONESGAME.scr:72
end

script.labels["CheckMove"] = function(ctx)
    -- STONESGAME.scr:75
    -- check adjacent spaces
    if ctx:condition("bHasTicket==FALSE") then -- STONESGAME.scr:78
        mm9.gosub(script, ctx, "CheckGameTicket") -- STONESGAME.scr:79
        if ctx:condition("THJORGARD_RESULT==FALSE") then -- STONESGAME.scr:80
            do return ctx:exit("TRUE") end -- STONESGAME.scr:81
        else -- STONESGAME.scr:82
            mm9.gosub(script, ctx, "TakeGameTicket") -- STONESGAME.scr:83
            ctx:state().bHasTicket = true -- STONESGAME.scr:84
        end -- STONESGAME.scr:85
    end -- STONESGAME.scr:86
    ctx:getParam(0, "hSquare") -- STONESGAME.scr:88
    ctx:removeTrigger("move") -- STONESGAME.scr:90
    -- get the current square
    ctx:getConsoleNumVar("STONES_INDEX", "nCurSquare") -- STONESGAME.scr:93
    ctx:arrayGet("npSquares", "nCurSquare", "nTemp") -- STONESGAME.scr:94
    -- only if square is empty, check adjacent
    if ctx:condition("nTemp==COLOR_EMPTY") then -- STONESGAME.scr:96
        -- iterate around the square
        mm9.gosub(script, ctx, "CheckSurrounding") -- STONESGAME.scr:98
    else -- STONESGAME.scr:99
        ctx:state().bSpaceOk = false -- STONESGAME.scr:100
    end -- STONESGAME.scr:101
    if ctx:condition("bSpaceOk==TRUE") then -- STONESGAME.scr:104
        mm9.gosub(script, ctx, "HandleValidMove") -- STONESGAME.scr:105
    else -- STONESGAME.scr:106
        mm9.gosub(script, ctx, "HandleInvalidMove") -- STONESGAME.scr:107
    end -- STONESGAME.scr:108
    ctx:addTrigger("move", "CheckMove") -- STONESGAME.scr:110
    do return ctx:exit("TRUE") end -- STONESGAME.scr:112
end

script.labels["HandleInvalidMove"] = function(ctx)
    -- STONESGAME.scr:115
    -- havent incremented turn yet
    -- bot==white, player==black
    if ctx:condition("nMoveCount==COLOR_WHITE") then -- STONESGAME.scr:119
        if ctx:condition("hBot!=0") then -- STONESGAME.scr:120
            ctx:trigger("hBot", "play") -- STONESGAME.scr:121
        end -- STONESGAME.scr:122
    else -- STONESGAME.scr:123
        if ctx:condition("nMoveCount==COLOR_BLACK") then -- STONESGAME.scr:124
            ctx:rolloverText(233, 1, 3000, 2000) -- STONESGAME.scr:125
        end -- STONESGAME.scr:126
    end -- STONESGAME.scr:127
    do return ctx:exit("TRUE") end -- STONESGAME.scr:129
end

script.labels["HandleValidMove"] = function(ctx)
    -- STONESGAME.scr:132
    ctx:set("nMoveCount", "nMoveCount + 1") -- STONESGAME.scr:134
    ctx:mod("nMoveCount", 2) -- STONESGAME.scr:135
    if ctx:condition("nMoveCount==COLOR_WHITE") then -- STONESGAME.scr:136
        ctx:trigger("hSquare", "white") -- STONESGAME.scr:137
    else -- STONESGAME.scr:138
        ctx:set("nMoveCount", "COLOR_BLACK") -- STONESGAME.scr:139
        ctx:trigger("hSquare", "black") -- STONESGAME.scr:140
    end -- STONESGAME.scr:141
    ctx:arrayPut("npSquares", "nCurSquare", "nMoveCount") -- STONESGAME.scr:143
    mm9.gosub(script, ctx, "CheckVictory") -- STONESGAME.scr:145
    do return ctx:exit("TRUE") end -- STONESGAME.scr:147
end

script.labels["CheckVictory"] = function(ctx)
    -- STONESGAME.scr:150
    -- checks empty squares to see
    -- if they are adjacent to friendly
    ctx:state().bCanMove = false -- STONESGAME.scr:154
    ctx:state().nCurSquare = 0 -- STONESGAME.scr:155
    while ctx:condition("nCurSquare<LISTLAST") do -- STONESGAME.scr:156
        ctx:arrayGet("npSquares", "nCurSquare", "nTemp") -- STONESGAME.scr:157
        if ctx:condition("nTemp==COLOR_EMPTY") then -- STONESGAME.scr:158
            mm9.gosub(script, ctx, "CheckSurrounding") -- STONESGAME.scr:159
            if ctx:condition("bSpaceOk==TRUE") then -- STONESGAME.scr:160
                if ctx:condition("nMoveCount==COLOR_WHITE") then -- STONESGAME.scr:161
                    if ctx:condition("hBot!=0") then -- STONESGAME.scr:162
                        ctx:trigger("hBot", "play") -- STONESGAME.scr:163
                    end -- STONESGAME.scr:164
                else -- STONESGAME.scr:165
                    ctx:wait(0, 2, "DisplayMoveMessage") -- STONESGAME.scr:166
                end -- STONESGAME.scr:167
                do return ctx:exit("TRUE") end -- STONESGAME.scr:169
            end -- STONESGAME.scr:170
        end -- STONESGAME.scr:171
        ctx:set("nCurSquare", "nCurSquare + 1") -- STONESGAME.scr:173
    end -- STONESGAME.scr:174
    mm9.gosub(script, ctx, "DeclareWinner") -- STONESGAME.scr:176
    mm9.gosub(script, ctx, "ResetVars") -- STONESGAME.scr:177
    mm9.gosub(script, ctx, "ResetBoard") -- STONESGAME.scr:178
    do return ctx:exit("TRUE") end -- STONESGAME.scr:180
end

script.labels["CheckSurrounding"] = function(ctx)
    -- STONESGAME.scr:183
    ctx:state().bSpaceOk = false -- STONESGAME.scr:185
    ctx:state().nCounter = 0 -- STONESGAME.scr:187
    while ctx:condition("nCounter<8") do -- STONESGAME.scr:188
        ctx:arrayGet("npCheck", "nCounter", "nCheck") -- STONESGAME.scr:189
        ctx:set("nCheck", "nCurSquare + nCheck") -- STONESGAME.scr:190
        ctx:state().bEdge = false -- STONESGAME.scr:192
        ctx:set("nTemp", "nCurSquare + 1") -- STONESGAME.scr:194
        ctx:mod("nTemp", "BOARDSIZE") -- STONESGAME.scr:195
        -- if on the right side, skip rights
        if ctx:condition("nTemp==0") then -- STONESGAME.scr:197
            if ctx:condition("nCounter<3") then -- STONESGAME.scr:198
                ctx:state().bEdge = true -- STONESGAME.scr:199
            end -- STONESGAME.scr:200
        end -- STONESGAME.scr:201
        ctx:set("nTemp", "nCurSquare") -- STONESGAME.scr:203
        ctx:mod("nTemp", "BOARDSIZE") -- STONESGAME.scr:204
        -- if on the left side, skip lefts
        if ctx:condition("nTemp==0") then -- STONESGAME.scr:206
            if ctx:condition("nCounter>4") then -- STONESGAME.scr:207
                ctx:state().bEdge = true -- STONESGAME.scr:208
            end -- STONESGAME.scr:209
        end -- STONESGAME.scr:210
        -- make sure we didnt pass the ends
        if ctx:condition("nCheck<0") then -- STONESGAME.scr:213
            ctx:state().bEdge = true -- STONESGAME.scr:214
        end -- STONESGAME.scr:215
        if ctx:condition("nCheck>LISTLAST") then -- STONESGAME.scr:216
            ctx:state().bEdge = true -- STONESGAME.scr:217
        end -- STONESGAME.scr:218
        if ctx:condition("bEdge==FALSE") then -- STONESGAME.scr:220
            ctx:arrayGet("npSquares", "nCheck", "nCheckResult") -- STONESGAME.scr:221
            ctx:set("nTemp", "nMoveCount + 1") -- STONESGAME.scr:222
            ctx:mod("nTemp", 2) -- STONESGAME.scr:223
            -- if color nearby is the same
            if ctx:condition("nCheckResult==nTemp") then -- STONESGAME.scr:225
                ctx:state().bSpaceOk = true -- STONESGAME.scr:226
                do return ctx:exit("TRUE") end -- STONESGAME.scr:227
            else -- STONESGAME.scr:228
            end -- STONESGAME.scr:229
        end -- STONESGAME.scr:230
        ctx:set("nCounter", "nCounter + 1") -- STONESGAME.scr:232
    end -- STONESGAME.scr:233
    do return ctx:exit("TRUE") end -- STONESGAME.scr:235
end

script.labels["DeclareWinner"] = function(ctx)
    -- STONESGAME.scr:238
    if ctx:condition("nMoveCount==COLOR_WHITE") then -- STONESGAME.scr:240
        ctx:rolloverText(230, 1, 3000, 2000) -- STONESGAME.scr:241
        mm9.gosub(script, ctx, "RecordStonesWin") -- STONESGAME.scr:242
    else -- STONESGAME.scr:243
        if ctx:condition("nMoveCount==COLOR_BLACK") then -- STONESGAME.scr:244
            ctx:rolloverText(231, 1, 3000, 2000) -- STONESGAME.scr:245
        end -- STONESGAME.scr:246
    end -- STONESGAME.scr:247
    do return ctx:exit("TRUE") end -- STONESGAME.scr:249
end

script.labels["ResetVars"] = function(ctx)
    -- STONESGAME.scr:252
    -- reset counters, ticket, curcolor
    ctx:state().bHasTicket = false -- STONESGAME.scr:255
    ctx:setConsoleNumVar("STONES_COLOR", "COLOR_WHITE") -- STONESGAME.scr:256
    ctx:state().nMoveCount = 0 -- STONESGAME.scr:257
    do return ctx:exit("TRUE") end -- STONESGAME.scr:259
end

script.labels["ResetBoard"] = function(ctx)
    -- STONESGAME.scr:262
    -- clear board, array, place 1 of each color
    mm9.gosub(script, ctx, "GetFirstObject") -- STONESGAME.scr:265
    while ctx:condition("LISTINDEX!=LISTLAST") do -- STONESGAME.scr:266
        ctx:trigger("LISTOBJECT", "clear") -- STONESGAME.scr:267
        ctx:arrayPut("npSquares", "LISTINDEX", "COLOR_EMPTY") -- STONESGAME.scr:268
        mm9.gosub(script, ctx, "GetNextObject") -- STONESGAME.scr:269
    end -- STONESGAME.scr:270
    ctx:trigger("LISTOBJECT", "clear") -- STONESGAME.scr:272
    ctx:arrayPut("npSquares", "LISTINDEX", "COLOR_EMPTY") -- STONESGAME.scr:273
    -- turn one of each color on at start
    ctx:randomInt("LISTFIRST", "LISTLAST", "LISTINDEX") -- STONESGAME.scr:276
    mm9.gosub(script, ctx, "GetCurrentObject") -- STONESGAME.scr:278
    ctx:trigger("LISTOBJECT", "white") -- STONESGAME.scr:279
    ctx:arrayPut("npSquares", "LISTINDEX", "COLOR_WHITE") -- STONESGAME.scr:280
    ctx:set("LISTINDEX", "LISTLAST - LISTINDEX") -- STONESGAME.scr:282
    mm9.gosub(script, ctx, "GetCurrentObject") -- STONESGAME.scr:283
    ctx:trigger("LISTOBJECT", "black") -- STONESGAME.scr:284
    ctx:arrayPut("npSquares", "LISTINDEX", "COLOR_BLACK") -- STONESGAME.scr:285
    do return ctx:exit("TRUE") end -- STONESGAME.scr:287
end

script.labels["SetupCheck"] = function(ctx)
    -- STONESGAME.scr:290
    -- positive side
    ctx:set("nTemp", "0 - BOARDSIZE + 1") -- STONESGAME.scr:293
    ctx:arrayPut("npCheck", 0, "nTemp") -- STONESGAME.scr:294
    ctx:state().nTemp = 1 -- STONESGAME.scr:295
    ctx:arrayPut("npCheck", 1, "nTemp") -- STONESGAME.scr:296
    ctx:set("nTemp", "BOARDSIZE + 1") -- STONESGAME.scr:297
    ctx:arrayPut("npCheck", 2, "nTemp") -- STONESGAME.scr:298
    -- up-down
    ctx:set("nTemp", "0 - BOARDSIZE") -- STONESGAME.scr:301
    ctx:arrayPut("npCheck", 3, "nTemp") -- STONESGAME.scr:302
    ctx:set("nTemp", "BOARDSIZE") -- STONESGAME.scr:303
    ctx:arrayPut("npCheck", 4, "nTemp") -- STONESGAME.scr:304
    -- negative side
    ctx:set("nTemp", "0 - BOARDSIZE - 1") -- STONESGAME.scr:307
    ctx:arrayPut("npCheck", 5, "nTemp") -- STONESGAME.scr:308
    ctx:state().nTemp = -1 -- STONESGAME.scr:309
    ctx:arrayPut("npCheck", 6, "nTemp") -- STONESGAME.scr:310
    ctx:set("nTemp", "BOARDSIZE - 1") -- STONESGAME.scr:311
    ctx:arrayPut("npCheck", 7, "nTemp") -- STONESGAME.scr:312
    do return ctx:exit("TRUE") end -- STONESGAME.scr:314
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- STONESGAME.scr:317
    ctx:state().hBot = nil -- STONESGAME.scr:319
    do return ctx:exit("TRUE") end -- STONESGAME.scr:321
end

script.labels["DisplayMoveMessage"] = function(ctx)
    -- STONESGAME.scr:324
    ctx:rolloverText("TEXT_YOURMOVE", 1, 3000, 2000) -- STONESGAME.scr:326
    do return ctx:exit("TRUE") end -- STONESGAME.scr:328
end

return script
