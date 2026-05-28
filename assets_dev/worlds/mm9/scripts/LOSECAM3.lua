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
    ctx:command("getmyhandle", "g_hmyobject") -- LOSECAM3.scr:32
    ctx:command("getpos", "g_hmyobject MyX MyY MyZ") -- LOSECAM3.scr:33
    ctx:command("getobjecthandle", "sTarget g_htarget") -- LOSECAM3.scr:35
    ctx:command("target", "g_htarget") -- LOSECAM3.scr:36
    ctx:command("wait", "1 2 OnPan") -- LOSECAM3.scr:37
    -- gosub OnPan
    do return ctx:exit("") end -- LOSECAM3.scr:39
end

script.labels["OnPan"] = function(ctx)
    -- LOSECAM3.scr:42
    ctx:command("getobjecthandle", "sCamera g_hobject") -- LOSECAM3.scr:45
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- LOSECAM3.scr:46
    ctx:command("movetopos", "xpos Ypos Zpos 100 OnArrive1") -- LOSECAM3.scr:47
    do return ctx:exit("") end -- LOSECAM3.scr:48
end

script.labels["OnArrive1"] = function(ctx)
    -- LOSECAM3.scr:51
    ctx:command("wait", "1 3 Reset") -- LOSECAM3.scr:55
    do return ctx:exit("") end -- LOSECAM3.scr:56
end

script.labels["Reset"] = function(ctx)
    -- LOSECAM3.scr:59
    ctx:command("setpos", "g_hmyobject MyX MyY MyZ DoNothing") -- LOSECAM3.scr:62
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
