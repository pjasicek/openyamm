-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHESSKNIGHT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "ChessBase.inc" }

-- ChessKnight.scr
-- by SJR
-- Purpose:Knight
script.labels["Main"] = function(ctx)
    -- CHESSKNIGHT.scr:10
    ctx:getParam(0, "sSquareName") -- CHESSKNIGHT.scr:12
    ctx:getParam(1, "sFloorName") -- CHESSKNIGHT.scr:13
    ctx:getParam(2, "BOARDSIZE") -- CHESSKNIGHT.scr:14
    ctx:getParam(3, "nLocation") -- CHESSKNIGHT.scr:15
    ctx:onEvent("OnPostStartWorld", "InitChessBase") -- CHESSKNIGHT.scr:17
    do return ctx:exit("TRUE") end -- CHESSKNIGHT.scr:19
end

script.labels["PreAttackRoutine"] = function(ctx)
    -- CHESSKNIGHT.scr:27
    mm9.gosub(script, ctx, "BeginAttack") -- CHESSKNIGHT.scr:29
    do return ctx:exit("TRUE") end -- CHESSKNIGHT.scr:31
end

script.labels["CheckPath"] = function(ctx)
    -- CHESSKNIGHT.scr:34
    -- check 8 knight squares
    ctx:getParam(0, "hTrigger") -- CHESSKNIGHT.scr:37
    ctx:state().dx = 1 -- CHESSKNIGHT.scr:39
    ctx:state().dz = 2 -- CHESSKNIGHT.scr:40
    -- 4 passes checking 2 squares at a time
    ctx:state().nCounter = 4 -- CHESSKNIGHT.scr:43
    while ctx:condition("nCounter>0") do -- CHESSKNIGHT.scr:44
        -- change to second z after we checked
        -- all 4 x's for the first z
        if ctx:condition("nCounter==2") then -- CHESSKNIGHT.scr:47
            ctx:state().dx = 2 -- CHESSKNIGHT.scr:48
            ctx:state().dz = 1 -- CHESSKNIGHT.scr:49
        end -- CHESSKNIGHT.scr:50
        ctx:set("zTemp", "zMe + dz") -- CHESSKNIGHT.scr:52
        -- check z boundaries of board
        if ctx:condition("zTemp<BOARDSIZE") then -- CHESSKNIGHT.scr:54
            if ctx:condition("zTemp>=0") then -- CHESSKNIGHT.scr:55
                -- ping the first x square at this z
                ctx:set("xTemp", "xMe + dx") -- CHESSKNIGHT.scr:57
                -- check x boundaries of board
                if ctx:condition("xTemp<BOARDSIZE") then -- CHESSKNIGHT.scr:59
                    if ctx:condition("xTemp >= 0") then -- CHESSKNIGHT.scr:60
                        -- change index coords to plane coords
                        ctx:set("LISTINDEX", "BOARDSIZE * zTemp + xMe + dx") -- CHESSKNIGHT.scr:62
                        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSKNIGHT.scr:63
                        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSKNIGHT.scr:64
                            mm9.gosub(script, ctx, "PreAttackRoutine") -- CHESSKNIGHT.scr:65
                            do return ctx:exit("TRUE") end -- CHESSKNIGHT.scr:66
                        end -- CHESSKNIGHT.scr:67
                    end -- CHESSKNIGHT.scr:68
                end -- CHESSKNIGHT.scr:69
                ctx:set("xTemp", "xMe - dx") -- CHESSKNIGHT.scr:71
                -- ping the second x square at this z
                -- check x boundaries of board
                if ctx:condition("xTemp<BOARDSIZE") then -- CHESSKNIGHT.scr:74
                    if ctx:condition("xTemp>=0") then -- CHESSKNIGHT.scr:75
                        -- change index coords to plane coords
                        ctx:set("LISTINDEX", "BOARDSIZE * zTemp + xMe - dx") -- CHESSKNIGHT.scr:77
                        mm9.gosub(script, ctx, "GetCurrentObject") -- CHESSKNIGHT.scr:78
                        if ctx:condition("LISTOBJECT==hTrigger") then -- CHESSKNIGHT.scr:79
                            mm9.gosub(script, ctx, "PreAttackRoutine") -- CHESSKNIGHT.scr:80
                            do return ctx:exit("TRUE") end -- CHESSKNIGHT.scr:81
                        end -- CHESSKNIGHT.scr:82
                    end -- CHESSKNIGHT.scr:83
                end -- CHESSKNIGHT.scr:84
            end -- CHESSKNIGHT.scr:85
        end -- CHESSKNIGHT.scr:86
        -- check the same x's, but on the other side
        ctx:set("dz", "dz * -1") -- CHESSKNIGHT.scr:89
        ctx:set("nCounter", "nCounter - 1") -- CHESSKNIGHT.scr:91
    end -- CHESSKNIGHT.scr:92
    do return ctx:exit("TRUE") end -- CHESSKNIGHT.scr:94
end

return script
