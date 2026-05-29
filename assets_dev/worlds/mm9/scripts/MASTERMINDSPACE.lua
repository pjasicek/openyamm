-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MASTERMINDSPACE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "BaseGlobals.inc" }

-- MastermindColor.scr
-- by SJR
-- 12-18-01
-- Purpose:when the player uses this,
-- it changes color and notifies
-- mastermind.scr
-- ScriptParams:
-- p0 = index of slot, (0,1,2,3)
script.labels["Main"] = function(ctx)
    -- MASTERMINDSPACE.scr:22
    ctx:getParam(0, "nIndex") -- MASTERMINDSPACE.scr:24
    ctx:onEvent("OnPostStartWorld", "InitMastermindSpace") -- MASTERMINDSPACE.scr:26
    ctx:onEvent("OnPostMiniSaveLoad", "InitMastermindSpace") -- MASTERMINDSPACE.scr:27
    do return ctx:exit("TRUE") end -- MASTERMINDSPACE.scr:29
end

script.labels["InitMastermindSpace"] = function(ctx)
    -- MASTERMINDSPACE.scr:32
    mm9.gosub(script, ctx, "InitColors") -- MASTERMINDSPACE.scr:34
    ctx:addTrigger("use", "UpdateColor") -- MASTERMINDSPACE.scr:36
    ctx:getConsoleStrVar("MASTERMIND_NAME", "sMastermindName") -- MASTERMINDSPACE.scr:38
    ctx:state().hMastermind = ctx:objectOrNil("sMastermindName") -- MASTERMINDSPACE.scr:39
    do return ctx:exit("TRUE") end -- MASTERMINDSPACE.scr:41
end

script.labels["UpdateColor"] = function(ctx)
    -- MASTERMINDSPACE.scr:44
    ctx:setConsoleNumVar("MASTERMIND_INDEX", "nIndex") -- MASTERMINDSPACE.scr:46
    ctx:getConsoleNumVar("MASTERMIND_COLOR", "nColor") -- MASTERMINDSPACE.scr:47
    if ctx:condition("hMastermind!=0") then -- MASTERMINDSPACE.scr:49
        ctx:trigger("hMastermind", "update") -- MASTERMINDSPACE.scr:50
    end -- MASTERMINDSPACE.scr:51
    mm9.gosub(script, ctx, "ChangeColor") -- MASTERMINDSPACE.scr:53
    do return ctx:exit("TRUE") end -- MASTERMINDSPACE.scr:55
end

script.labels["ChangeColor"] = function(ctx)
    -- MASTERMINDSPACE.scr:58
    -- change our color
    ctx:playSound("sounds\\door\\doorlatch01.wav", "DoNothing", 1, 500, "FALSE", 100) -- MASTERMINDSPACE.scr:61
    ctx:arrayGet("spSkins", "nColor", "sSkin") -- MASTERMINDSPACE.scr:63
    ctx:self():setModelFilenames("models\\gibs\\stone.abc", "sSkin") -- MASTERMINDSPACE.scr:64
    do return ctx:exit("TRUE") end -- MASTERMINDSPACE.scr:66
end

script.labels["InitColors"] = function(ctx)
    -- MASTERMINDSPACE.scr:69
    ctx:arrayPut("spSkins", 0, "skins\\gibs\\red.dtx") -- MASTERMINDSPACE.scr:71
    ctx:arrayPut("spSkins", 1, "skins\\gibs\\blue.dtx") -- MASTERMINDSPACE.scr:72
    ctx:arrayPut("spSkins", 2, "skins\\gibs\\yellow.dtx") -- MASTERMINDSPACE.scr:73
    ctx:arrayPut("spSkins", 3, "skins\\gibs\\orange.dtx") -- MASTERMINDSPACE.scr:74
    ctx:arrayPut("spSkins", 4, "skins\\gibs\\green.dtx") -- MASTERMINDSPACE.scr:75
    do return ctx:exit("TRUE") end -- MASTERMINDSPACE.scr:77
end

return script
