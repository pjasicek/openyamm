-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LOSECAM2.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- Losecam1.scr
-- By Timmy
-- 12/20
-- handles losegame cutscene
script.labels["OnPlay"] = function(ctx)
    -- LOSECAM2.scr:23
    ctx:getParam(0, "hTriggeredMe") -- LOSECAM2.scr:26
    ctx:command("getmyhandle", "g_hmyobject") -- LOSECAM2.scr:28
    ctx:command("getpos", "g_hmyobject MyX MyY MyZ") -- LOSECAM2.scr:29
    ctx:command("getmyhandle", "g_hmyobject") -- LOSECAM2.scr:31
    ctx:trigger("g_hmyobject", "On") -- LOSECAM2.scr:32
    ctx:command("screenfadein", "1") -- LOSECAM2.scr:33
    ctx:command("getobjecthandle", "loseman g_htarget") -- LOSECAM2.scr:34
    ctx:command("target", "g_htarget") -- LOSECAM2.scr:35
    mm9.gosub(script, ctx, "Onpan") -- LOSECAM2.scr:36
    do return ctx:exit("") end -- LOSECAM2.scr:37
end

script.labels["OnPan"] = function(ctx)
    -- LOSECAM2.scr:40
    ctx:command("getobjecthandle", "CameraMarker2 g_hobject") -- LOSECAM2.scr:43
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- LOSECAM2.scr:44
    ctx:command("movetopos", "xpos Ypos Zpos 150 OnArrive1") -- LOSECAM2.scr:45
    do return ctx:exit("") end -- LOSECAM2.scr:46
end

script.labels["OnArrive1"] = function(ctx)
    -- LOSECAM2.scr:49
    -- getobjecthandle hTriggeredMe g_hobject
    ctx:trigger("hTriggeredMe", "Cam3") -- LOSECAM2.scr:53
    ctx:command("wait", "1 1 Reset") -- LOSECAM2.scr:54
    do return ctx:exit("") end -- LOSECAM2.scr:55
end

script.labels["Reset"] = function(ctx)
    -- LOSECAM2.scr:58
    ctx:command("setpos", "g_hmyobject MyX MyY MyZ DoNothing") -- LOSECAM2.scr:61
    do return ctx:exit("") end -- LOSECAM2.scr:62
end

script.labels["Main"] = function(ctx)
    -- LOSECAM2.scr:65
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Play", "OnPlay") -- LOSECAM2.scr:70
    do return ctx:exit("") end -- LOSECAM2.scr:71
end

return script
