-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SCRIPTOBJECTTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- scriptobjecttest.scr
-- Jeff Leggett
script.labels["Output"] = function(ctx)
    -- SCRIPTOBJECTTEST.scr:12
    ctx:set("g_sOut", "g_nTemp") -- SCRIPTOBJECTTEST.scr:15
    ctx:set("g_sTemp", "Param--->") -- SCRIPTOBJECTTEST.scr:16
    ctx:add("g_sTemp", "g_sOut") -- SCRIPTOBJECTTEST.scr:17
    ctx:debugOut("g_sTemp") -- SCRIPTOBJECTTEST.scr:19
    do return ctx:exit("") end -- SCRIPTOBJECTTEST.scr:21
end

script.labels["MyTest"] = function(ctx)
    -- SCRIPTOBJECTTEST.scr:24
    ctx:getParam(1, "g_nTemp") -- SCRIPTOBJECTTEST.scr:27
    mm9.gosub(script, ctx, "Output") -- SCRIPTOBJECTTEST.scr:28
    ctx:getParam(2, "g_nTemp") -- SCRIPTOBJECTTEST.scr:30
    mm9.gosub(script, ctx, "Output") -- SCRIPTOBJECTTEST.scr:31
    ctx:getParam(3, "g_nTemp") -- SCRIPTOBJECTTEST.scr:33
    mm9.gosub(script, ctx, "Output") -- SCRIPTOBJECTTEST.scr:34
    do return ctx:exit("") end -- SCRIPTOBJECTTEST.scr:37
end

script.labels["Main"] = function(ctx)
    -- SCRIPTOBJECTTEST.scr:40
    -- TraceOn
    ctx:addTrigger("Test", "MyTest") -- SCRIPTOBJECTTEST.scr:44
    do return ctx:exit("") end -- SCRIPTOBJECTTEST.scr:47
end

return script
