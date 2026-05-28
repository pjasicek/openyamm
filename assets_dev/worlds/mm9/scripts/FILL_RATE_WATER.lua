-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FILL_RATE_WATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "globals.inc" }

script.labels["fill_rate_water.scr"] = function(ctx)
    -- FILL_RATE_WATER.scr:2
end

-- Tony Evans
-- This script is used to raise water and dynamically change the fill
-- rate in the prison room of the Grand Temple of the Moon.
-- Parameters:
-- p1	- How many inches of water to leave
-- p2	- Fill Rate
-- starting positions
-- dynamic positions
-- dimensions of volume brush
-- Default parameters
script.labels["OnRaiseWater"] = function(ctx)
    -- FILL_RATE_WATER.scr:44
    ctx:command("getdims", "g_hMyObject, nDimsX, nDimsY, nDimsZ") -- FILL_RATE_WATER.scr:47
    ctx:command("set", "nDestPosY, nOrigPosY") -- FILL_RATE_WATER.scr:48
    ctx:command("add", "nDestPosY, nDimsY") -- FILL_RATE_WATER.scr:49
    -- Leave some water there....
    ctx:command("sub", "nDestPosY, nWaterToLeave") -- FILL_RATE_WATER.scr:53
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- FILL_RATE_WATER.scr:55
    if ctx:condition("g_bTemp==TRUE") then -- FILL_RATE_WATER.scr:56
        ctx:command("playsound", "sFillSound, 1000, TRUE, 100, hWaterSound") -- FILL_RATE_WATER.scr:57
    end -- FILL_RATE_WATER.scr:58
    ctx:command("movetopos", "nOrigPosX, nDestPosY, nOrigPosZ, nWaterFillRate, StopSound") -- FILL_RATE_WATER.scr:60
    do return ctx:exit("") end -- FILL_RATE_WATER.scr:62
end

script.labels["StopSound"] = function(ctx)
    -- FILL_RATE_WATER.scr:65
    ctx:command("killsound", "hWaterSound") -- FILL_RATE_WATER.scr:67
    do return ctx:exit("") end -- FILL_RATE_WATER.scr:69
end

script.labels["Main"] = function(ctx)
    -- FILL_RATE_WATER.scr:72
    ctx:command("getmyhandle", "g_hMyObject") -- FILL_RATE_WATER.scr:77
    ctx:command("getpos", "g_hMyObject, nOrigPosX, nOrigPosY, nOrigPosZ") -- FILL_RATE_WATER.scr:78
    ctx:addTrigger("OnRaiseWater") -- FILL_RATE_WATER.scr:80
    ctx:getParam(0, "g_nTemp") -- FILL_RATE_WATER.scr:82
    if ctx:condition("g_nTemp!=0") then -- FILL_RATE_WATER.scr:84
        ctx:command("set", "nWaterToLeave, g_nTemp") -- FILL_RATE_WATER.scr:85
    end -- FILL_RATE_WATER.scr:86
    ctx:getParam(1, "g_nTemp") -- FILL_RATE_WATER.scr:88
    if ctx:condition("g_nTemp!=0") then -- FILL_RATE_WATER.scr:90
        ctx:command("set", "nWaterFillRate, g_nTemp") -- FILL_RATE_WATER.scr:91
    end -- FILL_RATE_WATER.scr:92
    do return ctx:exit("") end -- FILL_RATE_WATER.scr:94
end

return script
