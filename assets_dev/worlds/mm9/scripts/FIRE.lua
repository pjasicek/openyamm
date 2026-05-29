-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FIRE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 2, path = "globals.inc" }

script.labels["OnUse"] = function(ctx)
    -- FIRE.scr:9
    ctx:trigger("g_hMyObject", "ON") -- FIRE.scr:11
    ctx:state().g_hObject = ctx:objectOrNil("ScriptObject0") -- FIRE.scr:13
    ctx:set("g_sOut", "Test") -- FIRE.scr:15
    ctx:set("g_sTemp", "FlameId") -- FIRE.scr:16
    ctx:add("g_sOut", "nTemp") -- FIRE.scr:17
    ctx:trigger("g_hObject", "g_sOut") -- FIRE.scr:19
    ctx:debugOut("g_sOut") -- FIRE.scr:20
    do return ctx:exit("") end -- FIRE.scr:23
end

script.labels["Main"] = function(ctx)
    -- FIRE.scr:25
    -- TraceOn
    ctx:addTrigger("Use", "OnUse") -- FIRE.scr:30
    ctx:getParam(0, "FlameId") -- FIRE.scr:32
    do return ctx:exit("") end -- FIRE.scr:34
end

return script
