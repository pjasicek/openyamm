-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FOLLOWCAM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- FollowCam.scr
-- Just hovers over the passed object
-- 10 feet
script.labels["Tick"] = function(ctx)
    -- FOLLOWCAM.scr:15
    ctx:command("getpos", "hFollowObj, g_posX, g_posY, g_posZ") -- FOLLOWCAM.scr:16
    ctx:command("add", "g_posY, nHeight") -- FOLLOWCAM.scr:18
    ctx:command("setpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- FOLLOWCAM.scr:20
    ctx:command("wait", "0.01, Tick") -- FOLLOWCAM.scr:22
    do return ctx:exit("") end -- FOLLOWCAM.scr:24
end

script.labels["Dummy"] = function(ctx)
    -- FOLLOWCAM.scr:26
    do return ctx:exit("") end -- FOLLOWCAM.scr:27
end

script.labels["TurnOn"] = function(ctx)
    -- FOLLOWCAM.scr:29
    -- TraceON
    ctx:getParam(1, "sObjName") -- FOLLOWCAM.scr:31
    ctx:getParam(2, "g_nTemp") -- FOLLOWCAM.scr:32
    if ctx:condition("g_nTemp > 0") then -- FOLLOWCAM.scr:34
        ctx:command("set", "nHeight, g_nTemp") -- FOLLOWCAM.scr:35
    end -- FOLLOWCAM.scr:36
    ctx:command("getobjecthandle", "sObjName, hFollowObj") -- FOLLOWCAM.scr:38
    if ctx:condition("hFollowObj==NULL") then -- FOLLOWCAM.scr:40
        ctx:command("set", "g_sOut, sObjName") -- FOLLOWCAM.scr:41
        ctx:command("add", "g_sOut, <--- is an invalid object name...") -- FOLLOWCAM.scr:42
        ctx:command("debugout", "g_sOut") -- FOLLOWCAM.scr:43
        do return ctx:exit("TRUE") end -- FOLLOWCAM.scr:44
    end -- FOLLOWCAM.scr:45
    mm9.gosub(script, ctx, "Tick") -- FOLLOWCAM.scr:47
    ctx:command("traceoff", "") -- FOLLOWCAM.scr:49
    do return ctx:exit("FALSE") end -- FOLLOWCAM.scr:51
end

script.labels["TurnOff"] = function(ctx)
    -- FOLLOWCAM.scr:53
    ctx:command("wait", "0, Dummy") -- FOLLOWCAM.scr:54
    do return ctx:exit("FALSE") end -- FOLLOWCAM.scr:55
end

script.labels["Main"] = function(ctx)
    -- FOLLOWCAM.scr:58
    ctx:command("getmyhandle", "g_hMyObject") -- FOLLOWCAM.scr:60
    ctx:addTrigger("Off", "TurnOff") -- FOLLOWCAM.scr:62
    ctx:addTrigger("ON", "TurnOn") -- FOLLOWCAM.scr:63
    do return ctx:exit("") end -- FOLLOWCAM.scr:66
end

return script
