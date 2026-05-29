-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AITEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "aiglobals.inc" }

-- AITEST.SCR
script.labels["Test2"] = function(ctx)
    -- AITEST.scr:16
    ctx:self():walkTo(ctx:object("g_hMarker2"), 0, "Test1") -- AITEST.scr:19
    do return ctx:exit("TRUE") end -- AITEST.scr:20
end

script.labels["Test1"] = function(ctx)
    -- AITEST.scr:23
    ctx:self():walkTo(ctx:object("g_hMarker1"), 0, "Test2") -- AITEST.scr:26
    do return ctx:exit("TRUE") end -- AITEST.scr:27
end

script.labels["init"] = function(ctx)
    -- AITEST.scr:31
    ctx:state().g_hMarker1 = ctx:objectOrNil("TerrorMarker0") -- AITEST.scr:34
    ctx:state().g_hMarker2 = ctx:objectOrNil("TerrorMarker1") -- AITEST.scr:35
    mm9.gosub(script, ctx, "Test1") -- AITEST.scr:37
    do return ctx:exit("") end -- AITEST.scr:39
end

script.labels["OnDamage"] = function(ctx)
    -- AITEST.scr:42
    ctx:getParam(0, "g_hObject") -- AITEST.scr:45
    ctx:self():setTarget(ctx:object("g_hObject")) -- AITEST.scr:46
    ctx:runScript("g_sDefaultScript") -- AITEST.scr:47
    do return ctx:exit("") end -- AITEST.scr:48
end

script.labels["Main"] = function(ctx)
    -- AITEST.scr:51
    ctx:onEvent("OnDamage", "OnDamage") -- AITEST.scr:54
    ctx:state().g_sDefaultScript = ctx:self():stringProperty("ScriptName") -- AITEST.scr:56
    ctx:cacheScript("g_sDefaultScript") -- AITEST.scr:57
    ctx:wait(0, 1, "init") -- AITEST.scr:59
    do return ctx:exit("") end -- AITEST.scr:63
end

return script
