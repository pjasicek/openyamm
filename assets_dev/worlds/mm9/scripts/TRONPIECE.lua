-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRONPIECE.scr"
script.includes = {}
script.labels = {}


-- TronPiece.scr
-- by SJR
-- 12-12-01
-- Purpose:message TronGame.scr
-- when 'use'd
script.labels["Main"] = function(ctx)
    -- TRONPIECE.scr:14
    ctx:getParam(0, "nMyIndex") -- TRONPIECE.scr:16
    ctx:onEvent("OnPostStartWorld", "InitTronPiece") -- TRONPIECE.scr:18
    do return ctx:exit(1) end -- TRONPIECE.scr:20
end

script.labels["InitTronPiece"] = function(ctx)
    -- TRONPIECE.scr:23
    ctx:addTrigger("use", "OnUse") -- TRONPIECE.scr:25
    ctx:addTrigger("white", "TurnWhite") -- TRONPIECE.scr:26
    ctx:addTrigger("black", "TurnBlack") -- TRONPIECE.scr:27
    ctx:getConsoleStrVar("TRON_NAME", "sTronName") -- TRONPIECE.scr:29
    ctx:state().hTron = ctx:objectOrNil("sTronName") -- TRONPIECE.scr:30
    do return ctx:exit(1) end -- TRONPIECE.scr:32
end

script.labels["OnUse"] = function(ctx)
    -- TRONPIECE.scr:35
    ctx:setConsoleNumVar("TRON_INDEX", "nMyIndex") -- TRONPIECE.scr:37
    if ctx:condition("hTron!=0") then -- TRONPIECE.scr:39
        ctx:trigger("hTron", "move") -- TRONPIECE.scr:40
    end -- TRONPIECE.scr:41
    do return ctx:exit(1) end -- TRONPIECE.scr:43
end

script.labels["TurnWhite"] = function(ctx)
    -- TRONPIECE.scr:46
    ctx:self():setModelFilenames("models\\gibs\\stone.abc", "skins\\gibs\\yellow.dtx") -- TRONPIECE.scr:48
    do return ctx:exit(1) end -- TRONPIECE.scr:49
end

script.labels["TurnBlack"] = function(ctx)
    -- TRONPIECE.scr:52
    ctx:self():setModelFilenames("models\\gibs\\stone.abc", "skins\\gibs\\blue.dtx") -- TRONPIECE.scr:54
    do return ctx:exit(1) end -- TRONPIECE.scr:55
end

return script
