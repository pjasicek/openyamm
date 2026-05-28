-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WPTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 2, path = "globals.inc" }

script.labels["MyTest"] = function(ctx)
    -- WPTEST.scr:4
    ctx:command("debugout", "I'm here!!!!!!!!!!!!!!!!!!!!!!!!") -- WPTEST.scr:5
    ctx:command("getobjecthandle", "ScriptObject0, g_hObject") -- WPTEST.scr:7
    ctx:trigger("g_hObject", "Test 5 6 7") -- WPTEST.scr:8
    do return ctx:exit("") end -- WPTEST.scr:10
end

script.labels["Main"] = function(ctx)
    -- WPTEST.scr:14
    -- TraceOn
    ctx:command("wait", "0.5, MyTest") -- WPTEST.scr:16
    do return ctx:exit("") end -- WPTEST.scr:17
end

return script
