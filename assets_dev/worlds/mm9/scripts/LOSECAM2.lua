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
    ctx:state().MyX, ctx:state().MyY, ctx:state().MyZ = ctx:self():pos() -- LOSECAM2.scr:29
    ctx:trigger("g_hmyobject", "On") -- LOSECAM2.scr:32
    ctx:screenFadeIn(1) -- LOSECAM2.scr:33
    ctx:state().g_htarget = ctx:objectOrNil("loseman") -- LOSECAM2.scr:34
    ctx:self():setTarget(ctx:object("g_htarget")) -- LOSECAM2.scr:35
    mm9.gosub(script, ctx, "Onpan") -- LOSECAM2.scr:36
    do return ctx:exit("") end -- LOSECAM2.scr:37
end

script.labels["OnPan"] = function(ctx)
    -- LOSECAM2.scr:40
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("CameraMarker2"):pos() -- LOSECAM2.scr:43-44
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 150, "OnArrive1") -- LOSECAM2.scr:45
    do return ctx:exit("") end -- LOSECAM2.scr:46
end

script.labels["OnArrive1"] = function(ctx)
    -- LOSECAM2.scr:49
    -- getobjecthandle hTriggeredMe g_hobject
    ctx:trigger("hTriggeredMe", "Cam3") -- LOSECAM2.scr:53
    ctx:wait(1, 1, "Reset") -- LOSECAM2.scr:54
    do return ctx:exit("") end -- LOSECAM2.scr:55
end

script.labels["Reset"] = function(ctx)
    -- LOSECAM2.scr:58
    ctx:self():setPos("MyX", "MyY", "MyZ") -- LOSECAM2.scr:61
    do return ctx:exit("") end -- LOSECAM2.scr:62
end

script.labels["Main"] = function(ctx)
    -- LOSECAM2.scr:65
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Play", "OnPlay") -- LOSECAM2.scr:70
    do return ctx:exit("") end -- LOSECAM2.scr:71
end

return script
