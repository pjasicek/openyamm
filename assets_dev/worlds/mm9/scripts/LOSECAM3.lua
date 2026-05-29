-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LOSECAM3.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- Losecam1.scr
-- By Timmy
-- 12/20
-- handles losegame cutscene
script.labels["OnPlay"] = function(ctx)
    -- LOSECAM3.scr:27
    ctx:getParam(0, "hTriggeredMe") -- LOSECAM3.scr:30
    ctx:state().MyX, ctx:state().MyY, ctx:state().MyZ = ctx:self():pos() -- LOSECAM3.scr:33
    ctx:state().g_htarget = ctx:objectOrNil("sTarget") -- LOSECAM3.scr:35
    ctx:self():setTarget(ctx:object("g_htarget")) -- LOSECAM3.scr:36
    ctx:wait(1, 2, "OnPan") -- LOSECAM3.scr:37
    -- gosub OnPan
    do return ctx:exit("") end -- LOSECAM3.scr:39
end

script.labels["OnPan"] = function(ctx)
    -- LOSECAM3.scr:42
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("sCamera"):pos() -- LOSECAM3.scr:45-46
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", 100, "OnArrive1") -- LOSECAM3.scr:47
    do return ctx:exit("") end -- LOSECAM3.scr:48
end

script.labels["OnArrive1"] = function(ctx)
    -- LOSECAM3.scr:51
    ctx:wait(1, 3, "Reset") -- LOSECAM3.scr:55
    do return ctx:exit("") end -- LOSECAM3.scr:56
end

script.labels["Reset"] = function(ctx)
    -- LOSECAM3.scr:59
    ctx:self():setPos("MyX", "MyY", "MyZ") -- LOSECAM3.scr:62
    do return ctx:exit("") end -- LOSECAM3.scr:63
end

script.labels["Main"] = function(ctx)
    -- LOSECAM3.scr:66
    -- TraceOn ;DELETE ME!!
    ctx:getParam(0, "sCamera") -- LOSECAM3.scr:71
    ctx:getParam(1, "sTarget") -- LOSECAM3.scr:72
    ctx:addTrigger("Play", "OnPlay") -- LOSECAM3.scr:73
    do return ctx:exit("") end -- LOSECAM3.scr:74
end

return script
