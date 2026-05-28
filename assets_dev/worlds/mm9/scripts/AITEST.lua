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
    ctx:command("walkto", "g_hMarker2,0,Test1") -- AITEST.scr:19
    do return ctx:exit("TRUE") end -- AITEST.scr:20
end

script.labels["Test1"] = function(ctx)
    -- AITEST.scr:23
    ctx:command("walkto", "g_hMarker1,0,Test2") -- AITEST.scr:26
    do return ctx:exit("TRUE") end -- AITEST.scr:27
end

script.labels["init"] = function(ctx)
    -- AITEST.scr:31
    ctx:command("getobjecthandle", "TerrorMarker0, g_hMarker1") -- AITEST.scr:34
    ctx:command("getobjecthandle", "TerrorMarker1, g_hMarker2") -- AITEST.scr:35
    mm9.gosub(script, ctx, "Test1") -- AITEST.scr:37
    do return ctx:exit("") end -- AITEST.scr:39
end

script.labels["OnDamage"] = function(ctx)
    -- AITEST.scr:42
    ctx:getParam(0, "g_hObject") -- AITEST.scr:45
    ctx:command("target", "g_hObject") -- AITEST.scr:46
    ctx:command("runscript", "g_sDefaultScript") -- AITEST.scr:47
    do return ctx:exit("") end -- AITEST.scr:48
end

script.labels["Main"] = function(ctx)
    -- AITEST.scr:51
    ctx:command("ondamage", "OnDamage") -- AITEST.scr:54
    ctx:command("getmyhandle", "g_hMyObject") -- AITEST.scr:55
    ctx:command("getstatstr", "g_hMyObject,ScriptName,g_sDefaultScript") -- AITEST.scr:56
    ctx:command("cachescript", "g_sDefaultScript") -- AITEST.scr:57
    ctx:command("wait", "0,1,init") -- AITEST.scr:59
    do return ctx:exit("") end -- AITEST.scr:63
end

return script
