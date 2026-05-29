-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSFAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- ILSfan.scr
-- Timmy
-- This script makes Nagash do stuff
-- Parameters:
script.labels["OnStart"] = function(ctx)
    -- ILSFAN.scr:18
    ctx:state().g_hobject = ctx:self() -- ILSFAN.scr:21
    ctx:trigger("g_hobject", "On") -- ILSFAN.scr:22
    ctx:object("Wind0"):trigger("On") -- ILSFAN.scr:23-24
    ctx:object("Wind1"):trigger("On") -- ILSFAN.scr:25-26
    ctx:object("Trigger9"):trigger("off") -- ILSFAN.scr:27-28
    do return ctx:exit("") end -- ILSFAN.scr:29
end

script.labels["OnStop"] = function(ctx)
    -- ILSFAN.scr:32
    ctx:state().g_hobject = ctx:self() -- ILSFAN.scr:35
    ctx:trigger("g_hobject", "Off") -- ILSFAN.scr:36
    ctx:object("Wind0"):trigger("Off") -- ILSFAN.scr:37-38
    ctx:object("Wind1"):trigger("Off") -- ILSFAN.scr:39-40
    do return ctx:exit("") end -- ILSFAN.scr:42
end

script.labels["Main"] = function(ctx)
    -- ILSFAN.scr:47
    -- TRACEON
    ctx:addTrigger("start", "OnStart") -- ILSFAN.scr:52
    ctx:addTrigger("Stop", "OnStop") -- ILSFAN.scr:53
    do return ctx:exit("") end -- ILSFAN.scr:54
end

return script
