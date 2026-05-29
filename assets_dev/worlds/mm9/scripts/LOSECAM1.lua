-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LOSECAM1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- Losecam1.scr
-- By Timmy
-- 12/20
-- handles losegame cutscene
script.labels["OnPlay"] = function(ctx)
    -- LOSECAM1.scr:24
    ctx:getParam(0, "hTriggeredMe") -- LOSECAM1.scr:27
    ctx:state().MyX, ctx:state().MyY, ctx:state().MyZ = ctx:self():pos() -- LOSECAM1.scr:30
    ctx:letterBox("True") -- LOSECAM1.scr:32
    ctx:trigger("g_hmyobject", "On") -- LOSECAM1.scr:34
    ctx:screenFadeIn(1) -- LOSECAM1.scr:35
    ctx:state().g_htarget = ctx:objectOrNil("CameraMarker1") -- LOSECAM1.scr:36
    ctx:self():setTarget(ctx:object("g_htarget")) -- LOSECAM1.scr:37
    ctx:wait(1, .2, "OnPan") -- LOSECAM1.scr:38
    -- gosub OnPan
    do return ctx:exit("") end -- LOSECAM1.scr:40
end

script.labels["OnPan"] = function(ctx)
    -- LOSECAM1.scr:43
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("CameraMarker0"):pos() -- LOSECAM1.scr:46-47
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 100, "OnArrive1") -- LOSECAM1.scr:48
    do return ctx:exit("") end -- LOSECAM1.scr:49
end

script.labels["OnArrive1"] = function(ctx)
    -- LOSECAM1.scr:52
    -- getobjecthandle hTriggeredMe g_hobject
    ctx:trigger("hTriggeredMe", "Cam2") -- LOSECAM1.scr:56
    ctx:wait(1, 2, "Reset") -- LOSECAM1.scr:57
    do return ctx:exit("") end -- LOSECAM1.scr:58
end

script.labels["Reset"] = function(ctx)
    -- LOSECAM1.scr:61
    ctx:self():setPos("MyX", "MyY", "MyZ") -- LOSECAM1.scr:64
    do return ctx:exit("") end -- LOSECAM1.scr:65
end

script.labels["Main"] = function(ctx)
    -- LOSECAM1.scr:68
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Play", "OnPlay") -- LOSECAM1.scr:73
    do return ctx:exit("") end -- LOSECAM1.scr:74
end

return script
