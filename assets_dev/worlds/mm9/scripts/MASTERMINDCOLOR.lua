-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MASTERMINDCOLOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "BaseGlobals.inc" }

-- MastermindColor.scr
-- by SJR
-- 12-18-01
-- Purpose:when the player uses this,
-- it switches the current
-- color.
-- ScriptParams:
-- p0 = colorvalue (0,1,2,3,4)->(red,blue,yellow,orange,green)
script.labels["Main"] = function(ctx)
    -- MASTERMINDCOLOR.scr:16
    ctx:getParam(0, "nColor") -- MASTERMINDCOLOR.scr:18
    ctx:addTrigger("use", "ChangeColor") -- MASTERMINDCOLOR.scr:20
    do return ctx:exit("TRUE") end -- MASTERMINDCOLOR.scr:22
end

script.labels["ChangeColor"] = function(ctx)
    -- MASTERMINDCOLOR.scr:25
    -- sets the current color
    ctx:playSound("sounds\\door\\trapdooropen.wav", "DoNothing", 1, 100, "FALSE", 100) -- MASTERMINDCOLOR.scr:28
    ctx:setConsoleNumVar("MASTERMIND_COLOR", "nColor") -- MASTERMINDCOLOR.scr:30
    do return ctx:exit("TRUE") end -- MASTERMINDCOLOR.scr:32
end

return script
