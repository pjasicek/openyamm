-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TONYWATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "globals.inc" }

script.labels["TonyWater.scr"] = function(ctx)
    -- TONYWATER.scr:2
end

-- Tony Evans
-- This script can be used to sink and fill water...
-- Parameters:
-- p1	- How many inches of water to leave (when sinking)
-- p2	- Sink Rate
-- p3	- Fill Rate
-- Default parameters
script.labels["WaterOnSink"] = function(ctx)
    -- TONYWATER.scr:42
    -- Sets the water in motion in the downward direction...
    ctx:command("getdims", "g_hMyObject, nDimsX, nDimsY, nDimsZ") -- TONYWATER.scr:47
    ctx:command("set", "nDestPosY, nOrigPosY") -- TONYWATER.scr:48
    ctx:command("sub", "nDestPosY, nDimsY") -- TONYWATER.scr:49
    ctx:command("sub", "nDestPosY, nDimsY") -- TONYWATER.scr:50
    -- Leave some water there....
    ctx:command("add", "nDestPosY, nWaterToLeave") -- TONYWATER.scr:54
    ctx:command("set", "bWaterSunk, 1") -- TONYWATER.scr:56
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- TONYWATER.scr:58
    if ctx:condition("g_bTemp==TRUE") then -- TONYWATER.scr:59
        ctx:command("playsound", "sSinkSound, 1000, TRUE, 100, hWaterSound") -- TONYWATER.scr:60
    end -- TONYWATER.scr:61
    ctx:command("movetopos", "nOrigPosX, nDestPosY, nOrigPosZ, nWaterSinkRate, WaterDoneSinking") -- TONYWATER.scr:63
    do return ctx:exit("") end -- TONYWATER.scr:65
end

script.labels["WaterDoneSinking"] = function(ctx)
    -- TONYWATER.scr:68
    ctx:command("killsound", "hWaterSound") -- TONYWATER.scr:70
    ctx:command("docallback", "1") -- TONYWATER.scr:71
    do return ctx:exit("") end -- TONYWATER.scr:72
end

script.labels["WaterDoneFilling"] = function(ctx)
    -- TONYWATER.scr:76
    ctx:command("killsound", "hWaterSound") -- TONYWATER.scr:78
    ctx:command("docallback", "2") -- TONYWATER.scr:79
    do return ctx:exit("") end -- TONYWATER.scr:80
end

script.labels["WaterOnFill"] = function(ctx)
    -- TONYWATER.scr:83
    ctx:command("set", "nDestPosY, nOrigPosY") -- TONYWATER.scr:86
    ctx:command("set", "bWaterSunk, 0") -- TONYWATER.scr:87
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- TONYWATER.scr:89
    if ctx:condition("g_bTemp==TRUE") then -- TONYWATER.scr:90
        ctx:command("playsound", "sFillSound, 1000, TRUE, 100, hWaterSound") -- TONYWATER.scr:91
    end -- TONYWATER.scr:92
    ctx:command("movetopos", "nOrigPosX, nDestPosY, nOrigPosZ, nWaterFillRate, WaterDoneFilling") -- TONYWATER.scr:94
    do return ctx:exit("") end -- TONYWATER.scr:96
end

script.labels["WaterOnToggle"] = function(ctx)
    -- TONYWATER.scr:99
    if ctx:condition("bWaterSunk==TRUE") then -- TONYWATER.scr:102
        mm9.gosub(script, ctx, "WaterOnFill") -- TONYWATER.scr:103
    else -- TONYWATER.scr:104
        mm9.gosub(script, ctx, "WaterOnSink") -- TONYWATER.scr:105
    end -- TONYWATER.scr:106
    do return ctx:exit("") end -- TONYWATER.scr:108
end

script.labels["WaterInit"] = function(ctx)
    -- TONYWATER.scr:111
    ctx:command("getmyhandle", "g_hMyObject") -- TONYWATER.scr:116
    ctx:command("getpos", "g_hMyObject, nOrigPosX, nOrigPosY, nOrigPosZ") -- TONYWATER.scr:117
    ctx:addTrigger("SinkWater", "WaterOnSink") -- TONYWATER.scr:119
    ctx:addTrigger("FillWater", "WaterOnFill") -- TONYWATER.scr:120
    ctx:addTrigger("ToggleWater", "WaterOnToggle") -- TONYWATER.scr:121
    ctx:getParam(0, "g_nTemp") -- TONYWATER.scr:123
    if ctx:condition("g_nTemp!=0") then -- TONYWATER.scr:125
        ctx:command("set", "nWaterToLeave, g_nTemp") -- TONYWATER.scr:126
    end -- TONYWATER.scr:127
    ctx:getParam(1, "g_nTemp") -- TONYWATER.scr:129
    if ctx:condition("g_nTemp!=0") then -- TONYWATER.scr:131
        ctx:command("set", "nWaterSinkRate, g_nTemp") -- TONYWATER.scr:132
    end -- TONYWATER.scr:133
    ctx:getParam(2, "g_nTemp") -- TONYWATER.scr:135
    if ctx:condition("g_nTemp!=0") then -- TONYWATER.scr:137
        ctx:command("set", "nWaterFillRate, g_nTemp") -- TONYWATER.scr:138
    end -- TONYWATER.scr:139
    do return ctx:exit("") end -- TONYWATER.scr:141
end

return script
