-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSMINOTAURCAGE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "base.inc" }

-- ILSMinotaurcage.scr
-- Timmy
-- This script makes Minotaur's exit cages and then run the base ai script
-- Parameters:
-- P0 nav point
script.labels["OnStart"] = function(ctx)
    -- ILSMINOTAURCAGE.scr:22
    ctx:state().g_hobject = ctx:objectOrNil("param0") -- ILSMINOTAURCAGE.scr:26
    ctx:debugOut("g_hobject") -- ILSMINOTAURCAGE.scr:27
    ctx:self():faceObject(ctx:object("g_hobject"), 80, "walk") -- ILSMINOTAURCAGE.scr:28
    do return ctx:exit("") end -- ILSMINOTAURCAGE.scr:29
end

script.labels["Stuck"] = function(ctx)
    -- ILSMINOTAURCAGE.scr:35
    ctx:state().g_hobject = ctx:objectOrNil("param0") -- ILSMINOTAURCAGE.scr:39
    ctx:self():faceObject(ctx:object("g_hobject"), 30, "walk") -- ILSMINOTAURCAGE.scr:41
    do return ctx:exit("") end -- ILSMINOTAURCAGE.scr:42
end

script.labels["Walk"] = function(ctx)
    -- ILSMINOTAURCAGE.scr:46
    ctx:state().g_hobject = ctx:objectOrNil("param0") -- ILSMINOTAURCAGE.scr:49
    ctx:self():runTo(ctx:object("g_hobject"), 16, "Alert") -- ILSMINOTAURCAGE.scr:50
    do return ctx:exit("") end -- ILSMINOTAURCAGE.scr:51
end

script.labels["Alert"] = function(ctx)
    -- ILSMINOTAURCAGE.scr:55
    mm9.gosub(script, ctx, "InitBase") -- ILSMINOTAURCAGE.scr:58
    do return ctx:exit("") end -- ILSMINOTAURCAGE.scr:59
end

script.labels["Main"] = function(ctx)
    -- ILSMINOTAURCAGE.scr:63
    -- TRACEON
    ctx:getParam(0, "param0") -- ILSMINOTAURCAGE.scr:70
    ctx:addTrigger("Start", "Onstart") -- ILSMINOTAURCAGE.scr:71
    ctx:onEvent("OnStuck", "") -- ILSMINOTAURCAGE.scr:72
    do return ctx:exit("") end -- ILSMINOTAURCAGE.scr:73
end

return script
