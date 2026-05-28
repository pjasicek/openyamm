-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STONESPIECE.scr"
script.includes = {}
script.labels = {}


-- StonesPiece.scr
-- by SJR
-- 12-12-01
-- Purpose:
script.labels["Main"] = function(ctx)
    -- STONESPIECE.scr:9
    ctx:addTrigger("white", "TurnWhite") -- STONESPIECE.scr:11
    ctx:addTrigger("black", "TurnBlack") -- STONESPIECE.scr:12
    do return ctx:exit(1) end -- STONESPIECE.scr:14
end

script.labels["TurnWhite"] = function(ctx)
    -- STONESPIECE.scr:17
    ctx:command("setmodelfilenames", "\"models\\gibs\\stone.abc\", \"skins\\gibs\\yellow.dtx\"") -- STONESPIECE.scr:19
    do return ctx:exit(1) end -- STONESPIECE.scr:21
end

script.labels["TurnBlack"] = function(ctx)
    -- STONESPIECE.scr:24
    ctx:command("setmodelfilenames", "\"models\\gibs\\stone.abc\", \"skins\\gibs\\blue.dtx\"") -- STONESPIECE.scr:26
    do return ctx:exit(1) end -- STONESPIECE.scr:28
end

return script
