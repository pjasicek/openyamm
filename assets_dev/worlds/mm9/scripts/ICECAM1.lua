-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ICECAM1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- IceCam1.scr
-- By Timmy
-- Controls the Ice Camera movement
-- 1/2/02
script.labels["OnStart"] = function(ctx)
    -- ICECAM1.scr:18
    ctx:command("wait", "1 1 OnPan") -- ICECAM1.scr:21
    do return ctx:exit("") end -- ICECAM1.scr:22
end

script.labels["OnPan"] = function(ctx)
    -- ICECAM1.scr:25
    ctx:command("getobjecthandle", "IceMarker1 g_hobject") -- ICECAM1.scr:28
    ctx:command("target", "g_hobject") -- ICECAM1.scr:29
    do return ctx:exit("") end -- ICECAM1.scr:30
end

script.labels["OnMove"] = function(ctx)
    -- ICECAM1.scr:33
    ctx:getParam(0, "g_hTarget") -- ICECAM1.scr:36
    ctx:command("getobjecthandle", "IceMarker2 g_hobject") -- ICECAM1.scr:37
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- ICECAM1.scr:38
    ctx:command("movetopos", "xpos Ypos Zpos 150 OnArrive") -- ICECAM1.scr:39
    do return ctx:exit("") end -- ICECAM1.scr:40
end

script.labels["OnArrive"] = function(ctx)
    -- ICECAM1.scr:43
    ctx:trigger("g_htarget", "Cam3") -- ICECAM1.scr:46
    do return ctx:exit("") end -- ICECAM1.scr:47
end

script.labels["Main"] = function(ctx)
    -- ICECAM1.scr:49
    -- TraceOn ;delete me!!
    ctx:addTrigger("Start", "OnStart") -- ICECAM1.scr:53
    ctx:addTrigger("Move", "OnMove") -- ICECAM1.scr:54
    ctx:getParam(0, "sCamera") -- ICECAM1.scr:55
    do return ctx:exit("") end -- ICECAM1.scr:56
end

return script
