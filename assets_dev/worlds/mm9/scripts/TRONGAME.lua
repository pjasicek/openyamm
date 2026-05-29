-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRONGAME.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "ListMaker.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "flags.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "ThjorgardGamesCommon.inc" }

-- TronGame.scr
-- by SJR
-- 12-12-01
-- Purpose:
-- HowItWorks:TronPiece.scr triggers this
-- when it is 'use'd. This script
-- then does some checking and turns
-- the appropriate piece visible and colored
script.labels["Main"] = function(ctx)
    -- TRONGAME.scr:40
    ctx:getParam(0, "LISTNAME") -- TRONGAME.scr:42
    ctx:getParam(1, "BOARDSIZE") -- TRONGAME.scr:43
    -- register game name
    ctx:state().hPiece = ctx:self() -- TRONGAME.scr:46
    ctx:state().sPieceName = ctx:object("hPiece"):name() -- TRONGAME.scr:47
    ctx:setConsoleStrVar("TRON_NAME", "sPieceName") -- TRONGAME.scr:48
    ctx:state().LISTFIRST = 0 -- TRONGAME.scr:50
    ctx:set("LISTLAST", "BOARDSIZE * BOARDSIZE - 1") -- TRONGAME.scr:51
    ctx:onEvent("OnPostStartWorld", "InitTronGame") -- TRONGAME.scr:53
    do return ctx:exit("TRUE") end -- TRONGAME.scr:55
end

script.labels["InitTronGame"] = function(ctx)
    -- TRONGAME.scr:58
    ctx:getConsoleStrVar("TRON_PLAYER", "sBotName") -- TRONGAME.scr:60
    ctx:state().hBot = ctx:objectOrNil("sBotName") -- TRONGAME.scr:61
    if ctx:condition("hBot!=0") then -- TRONGAME.scr:62
        ctx:self():link(ctx:object("hBot")) -- TRONGAME.scr:63
        ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- TRONGAME.scr:64
    end -- TRONGAME.scr:65
    mm9.gosub(script, ctx, "ResetBoard") -- TRONGAME.scr:67
    ctx:addTrigger("move", "CheckMove") -- TRONGAME.scr:69
    do return ctx:exit("TRUE") end -- TRONGAME.scr:71
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- TRONGAME.scr:74
    ctx:state().hBot = nil -- TRONGAME.scr:76
    do return ctx:exit("TRUE") end -- TRONGAME.scr:78
end

script.labels["GameOver"] = function(ctx)
    -- TRONGAME.scr:81
    if ctx:condition("nMoveCount==TRON_WHITE") then -- TRONGAME.scr:83
        ctx:rolloverText(230, 1, 3000, 2000) -- TRONGAME.scr:84
        mm9.gosub(script, ctx, "RecordStonesWin") -- TRONGAME.scr:85
    else -- TRONGAME.scr:86
        if ctx:condition("nMoveCount==TRON_BLACK") then -- TRONGAME.scr:87
            ctx:rolloverText(231, 1, 3000, 2000) -- TRONGAME.scr:88
        end -- TRONGAME.scr:89
    end -- TRONGAME.scr:90
    if ctx:condition("hBot!=0") then -- TRONGAME.scr:92
        ctx:trigger("hBot", "GameOver") -- TRONGAME.scr:93
    end -- TRONGAME.scr:94
    mm9.gosub(script, ctx, "ResetBoard") -- TRONGAME.scr:96
    do return ctx:exit("TRUE") end -- TRONGAME.scr:98
end

script.labels["CheckMove"] = function(ctx)
    -- TRONGAME.scr:101
    -- check adjacent spaces
    -- check for player ticket
    if ctx:condition("bHasTicket==FALSE") then -- TRONGAME.scr:105
        mm9.gosub(script, ctx, "CheckGameTicket") -- TRONGAME.scr:106
        if ctx:condition("THJORGARD_RESULT==0") then -- TRONGAME.scr:107
            do return ctx:exit("TRUE") end -- TRONGAME.scr:108
        else -- TRONGAME.scr:109
            mm9.gosub(script, ctx, "TakeGameTicket") -- TRONGAME.scr:110
            ctx:state().bHasTicket = true -- TRONGAME.scr:111
        end -- TRONGAME.scr:112
    end -- TRONGAME.scr:113
    ctx:removeTrigger("move") -- TRONGAME.scr:115
    -- get the current square
    ctx:getConsoleNumVar("TRON_INDEX", "nCurSquare") -- TRONGAME.scr:118
    ctx:arrayGet("npSquares", "nCurSquare", "nTemp") -- TRONGAME.scr:119
    -- only if square is empty, check adjacent
    if ctx:condition("nTemp==TRON_EMPTY") then -- TRONGAME.scr:121
        -- iterate around the square
        mm9.gosub(script, ctx, "SetupCheck") -- TRONGAME.scr:123
        mm9.gosub(script, ctx, "CheckSurrounding") -- TRONGAME.scr:124
    else -- TRONGAME.scr:125
        ctx:state().bSpaceOk = false -- TRONGAME.scr:126
    end -- TRONGAME.scr:127
    if ctx:condition("bSpaceOk==TRUE") then -- TRONGAME.scr:130
        mm9.gosub(script, ctx, "Move") -- TRONGAME.scr:131
    else -- TRONGAME.scr:132
        mm9.gosub(script, ctx, "BogusMove") -- TRONGAME.scr:133
    end -- TRONGAME.scr:134
    ctx:addTrigger("Move", "CheckMove") -- TRONGAME.scr:136
    do return ctx:exit("TRUE") end -- TRONGAME.scr:138
end

script.labels["BogusMove"] = function(ctx)
    -- TRONGAME.scr:141
    -- havent incremented turn yet; bot==white
    if ctx:condition("nMoveCount==TRON_WHITE") then -- TRONGAME.scr:144
        ctx:cprint("Try", "again", "Bot") -- TRONGAME.scr:145
        if ctx:condition("hBot!=0") then -- TRONGAME.scr:146
            ctx:trigger("hBot", "PlacePiece") -- TRONGAME.scr:147
        end -- TRONGAME.scr:148
    else -- TRONGAME.scr:149
        -- havent incremented turn yet; player==black
        if ctx:condition("nMoveCount==TRON_BLACK") then -- TRONGAME.scr:151
            ctx:cprint("Try", "again", "Player") -- TRONGAME.scr:152
        end -- TRONGAME.scr:153
    end -- TRONGAME.scr:154
    do return ctx:exit("TRUE") end -- TRONGAME.scr:156
end

script.labels["Move"] = function(ctx)
    -- TRONGAME.scr:159
    -- turn the piece visible
    ctx:getParam(0, "hPiece") -- TRONGAME.scr:162
    ctx:set("nMoveCount", "nMoveCount + 1") -- TRONGAME.scr:163
    ctx:mod("nMoveCount", 2) -- TRONGAME.scr:164
    ctx:cprint("nCurSquare") -- TRONGAME.scr:165
    -- since Mod nMoveCount = 0 or 1 = black or white
    if ctx:condition("nMoveCount==TRON_WHITE") then -- TRONGAME.scr:167
        ctx:cprint("Black's", "turn") -- TRONGAME.scr:168
        ctx:trigger("hPiece", "White") -- TRONGAME.scr:169
    else -- TRONGAME.scr:170
        ctx:cprint("White's", "turn") -- TRONGAME.scr:171
        ctx:trigger("hPiece", "Black") -- TRONGAME.scr:172
    end -- TRONGAME.scr:173
    ctx:object("hPiece"):setFlag("FLAG_VISIBLE", true) -- TRONGAME.scr:175
    ctx:arrayPut("npSquares", "nCurSquare", "nMoveCount") -- TRONGAME.scr:177
    mm9.gosub(script, ctx, "CheckVictory") -- TRONGAME.scr:179
    do return ctx:exit("TRUE") end -- TRONGAME.scr:181
end

script.labels["CheckVictory"] = function(ctx)
    -- TRONGAME.scr:186
    -- checks empty squares to see
    -- if they are adjacent to friendly
    -- start off FALSE
    ctx:state().bCanMove = false -- TRONGAME.scr:191
    ctx:state().nCurSquare = 0 -- TRONGAME.scr:193
    while ctx:condition("nCurSquare<LISTLAST") do -- TRONGAME.scr:194
        ctx:arrayGet("npSquares", "nCurSquare", "nTemp") -- TRONGAME.scr:195
        -- if square is empty, check adjacent
        if ctx:condition("nTemp==TRON_EMPTY") then -- TRONGAME.scr:197
            mm9.gosub(script, ctx, "CheckSurrounding") -- TRONGAME.scr:198
            if ctx:condition("bSpaceOk==TRUE") then -- TRONGAME.scr:200
                -- if no win and white's (player's)
                -- turn, trigger bot to make move
                if ctx:condition("nMoveCount==TRON_WHITE") then -- TRONGAME.scr:203
                    ctx:cprint("Bot's", "turn") -- TRONGAME.scr:204
                    if ctx:condition("hBot!=0") then -- TRONGAME.scr:205
                        ctx:trigger("hBot", "PlacePiece") -- TRONGAME.scr:206
                    end -- TRONGAME.scr:207
                end -- TRONGAME.scr:208
                do return ctx:exit("TRUE") end -- TRONGAME.scr:210
            end -- TRONGAME.scr:211
        end -- TRONGAME.scr:212
        ctx:set("nCurSquare", "nCurSquare + 1") -- TRONGAME.scr:214
    end -- TRONGAME.scr:215
    -- if we made it past all that checking...
    mm9.gosub(script, ctx, "GameOver") -- TRONGAME.scr:218
    do return ctx:exit("TRUE") end -- TRONGAME.scr:220
end

script.labels["CheckSurrounding"] = function(ctx)
    -- TRONGAME.scr:223
    ctx:state().bSpaceOk = false -- TRONGAME.scr:225
    ctx:state().nCounter = 0 -- TRONGAME.scr:227
    while ctx:condition("nCounter<8") do -- TRONGAME.scr:228
        ctx:arrayGet("npCheck", "nCounter", "nCheck") -- TRONGAME.scr:229
        ctx:set("nCheck", "nCurSquare + nCheck") -- TRONGAME.scr:230
        ctx:state().bEdge = false -- TRONGAME.scr:232
        ctx:set("nTemp", "nCurSquare + 1") -- TRONGAME.scr:234
        ctx:mod("nTemp", "BOARDSIZE") -- TRONGAME.scr:235
        -- if on the right side, skip rights
        if ctx:condition("nTemp==0") then -- TRONGAME.scr:237
            if ctx:condition("nCounter<3") then -- TRONGAME.scr:238
                ctx:state().bEdge = true -- TRONGAME.scr:239
            end -- TRONGAME.scr:240
        end -- TRONGAME.scr:241
        ctx:set("nTemp", "nCurSquare") -- TRONGAME.scr:243
        ctx:mod("nTemp", "BOARDSIZE") -- TRONGAME.scr:244
        -- if on the left side, skip lefts
        if ctx:condition("nTemp==0") then -- TRONGAME.scr:246
            if ctx:condition("nCounter>4") then -- TRONGAME.scr:247
                ctx:state().bEdge = true -- TRONGAME.scr:248
            end -- TRONGAME.scr:249
        end -- TRONGAME.scr:250
        -- make sure we didnt pass the ends
        if ctx:condition("nCheck<0") then -- TRONGAME.scr:253
            ctx:state().bEdge = true -- TRONGAME.scr:254
        end -- TRONGAME.scr:255
        if ctx:condition("nCheck>=LISTLAST") then -- TRONGAME.scr:256
            ctx:state().bEdge = true -- TRONGAME.scr:257
        end -- TRONGAME.scr:258
        if ctx:condition("bEdge==FALSE") then -- TRONGAME.scr:260
            ctx:arrayGet("npSquares", "nCheck", "nCheckResult") -- TRONGAME.scr:261
            ctx:set("nTemp", "nMoveCount + 1") -- TRONGAME.scr:262
            ctx:mod("nTemp", 2) -- TRONGAME.scr:263
            -- if color nearby is the same
            if ctx:condition("nCheckResult==nTemp") then -- TRONGAME.scr:265
                ctx:state().bSpaceOk = true -- TRONGAME.scr:266
                do return ctx:exit("TRUE") end -- TRONGAME.scr:267
            else -- TRONGAME.scr:268
            end -- TRONGAME.scr:269
        end -- TRONGAME.scr:270
        ctx:set("nCounter", "nCounter + 1") -- TRONGAME.scr:272
    end -- TRONGAME.scr:274
    do return ctx:exit("TRUE") end -- TRONGAME.scr:276
end

script.labels["ResetBoard"] = function(ctx)
    -- TRONGAME.scr:279
    -- make all invisible, clear array
    ctx:state().bHasTicket = false -- TRONGAME.scr:282
    ctx:state().nMoveCount = 0 -- TRONGAME.scr:283
    mm9.gosub(script, ctx, "GetFirstObject") -- TRONGAME.scr:284
    while ctx:condition("LISTINDEX!=LISTLAST") do -- TRONGAME.scr:285
        ctx:object("LISTOBJECT"):setFlag("FLAG_VISIBLE", false) -- TRONGAME.scr:286
        ctx:arrayPut("npSquares", "LISTINDEX", "TRON_EMPTY") -- TRONGAME.scr:287
        mm9.gosub(script, ctx, "GetNextObject") -- TRONGAME.scr:288
    end -- TRONGAME.scr:289
    ctx:object("LISTOBJECT"):setFlag("FLAG_VISIBLE", false) -- TRONGAME.scr:291
    ctx:arrayPut("npSquares", "LISTINDEX", "TRON_EMPTY") -- TRONGAME.scr:292
    -- turn one of each color on at start
    ctx:randomInt("LISTFIRST", "LISTLAST", "LISTINDEX") -- TRONGAME.scr:295
    mm9.gosub(script, ctx, "GetCurrentObject") -- TRONGAME.scr:297
    ctx:object("LISTOBJECT"):setFlag("FLAG_VISIBLE", true) -- TRONGAME.scr:298
    ctx:trigger("LISTOBJECT", "White") -- TRONGAME.scr:299
    ctx:arrayPut("npSquares", "LISTINDEX", "TRON_WHITE") -- TRONGAME.scr:300
    ctx:set("LISTINDEX", "LISTLAST - LISTINDEX") -- TRONGAME.scr:301
    mm9.gosub(script, ctx, "GetCurrentObject") -- TRONGAME.scr:303
    ctx:object("LISTOBJECT"):setFlag("FLAG_VISIBLE", true) -- TRONGAME.scr:304
    ctx:trigger("LISTOBJECT", "Black") -- TRONGAME.scr:305
    ctx:arrayPut("npSquares", "LISTINDEX", "TRON_BLACK") -- TRONGAME.scr:306
    do return ctx:exit("TRUE") end -- TRONGAME.scr:308
end

script.labels["SetupCheck"] = function(ctx)
    -- TRONGAME.scr:311
    -- positive side
    ctx:set("nTemp", "0 - BOARDSIZE + 1") -- TRONGAME.scr:314
    ctx:arrayPut("npCheck", 0, "nTemp") -- TRONGAME.scr:315
    ctx:state().nTemp = 1 -- TRONGAME.scr:316
    ctx:arrayPut("npCheck", 1, "nTemp") -- TRONGAME.scr:317
    ctx:set("nTemp", "BOARDSIZE + 1") -- TRONGAME.scr:318
    ctx:arrayPut("npCheck", 2, "nTemp") -- TRONGAME.scr:319
    -- up-down
    ctx:set("nTemp", "0 - BOARDSIZE") -- TRONGAME.scr:322
    ctx:arrayPut("npCheck", 3, "nTemp") -- TRONGAME.scr:323
    ctx:set("nTemp", "BOARDSIZE") -- TRONGAME.scr:324
    ctx:arrayPut("npCheck", 4, "nTemp") -- TRONGAME.scr:325
    -- negative side
    ctx:set("nTemp", "0 - BOARDSIZE - 1") -- TRONGAME.scr:328
    ctx:arrayPut("npCheck", 5, "nTemp") -- TRONGAME.scr:329
    ctx:state().nTemp = -1 -- TRONGAME.scr:330
    ctx:arrayPut("npCheck", 6, "nTemp") -- TRONGAME.scr:331
    ctx:set("nTemp", "BOARDSIZE - 1") -- TRONGAME.scr:332
    ctx:arrayPut("npCheck", 7, "nTemp") -- TRONGAME.scr:333
    do return ctx:exit("TRUE") end -- TRONGAME.scr:335
end

return script
