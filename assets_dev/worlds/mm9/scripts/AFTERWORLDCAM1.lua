-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AFTERWORLDCAM1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- AfterWorldCam1.scr
-- 1/5/02
-- timmy
-- does battlefield camera
script.labels["OnPlay"] = function(ctx)
    -- AFTERWORLDCAM1.scr:26
    ctx:command("getobjecthandle", "sMarker g_hobject") -- AFTERWORLDCAM1.scr:29
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- AFTERWORLDCAM1.scr:30
    ctx:command("movetopos", "xpos Ypos Zpos nSpeed OnArrive") -- AFTERWORLDCAM1.scr:31
    do return ctx:exit("") end -- AFTERWORLDCAM1.scr:32
end

script.labels["OnArrive"] = function(ctx)
    -- AFTERWORLDCAM1.scr:35
    ctx:command("getobjecthandle", "Skraelos0 g_hobject") -- AFTERWORLDCAM1.scr:38
    ctx:trigger("g_hobject", "Done") -- AFTERWORLDCAM1.scr:39
    do return ctx:exit("") end -- AFTERWORLDCAM1.scr:40
end

script.labels["Main"] = function(ctx)
    -- AFTERWORLDCAM1.scr:42
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- AFTERWORLDCAM1.scr:47
    ctx:getParam(0, "sMarker") -- AFTERWORLDCAM1.scr:48
    ctx:getParam(1, "nSpeed") -- AFTERWORLDCAM1.scr:49
    do return ctx:exit("") end -- AFTERWORLDCAM1.scr:50
end

return script
