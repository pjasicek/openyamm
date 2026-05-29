-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "JEFFCAMERATEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "globals.inc" }

script.labels["WatchMe"] = function(ctx)
    -- JEFFCAMERATEST.scr:4
    ctx:getParam(0, "g_hObject") -- JEFFCAMERATEST.scr:5
    ctx:self():faceObject(ctx:object("g_hObject"), 0) -- JEFFCAMERATEST.scr:6
    do return ctx:exit("") end -- JEFFCAMERATEST.scr:7
end

script.labels["Main"] = function(ctx)
    -- JEFFCAMERATEST.scr:10
    ctx:addTrigger("Watchme", "WatchMe") -- JEFFCAMERATEST.scr:12
    do return ctx:exit("") end -- JEFFCAMERATEST.scr:14
end

return script
