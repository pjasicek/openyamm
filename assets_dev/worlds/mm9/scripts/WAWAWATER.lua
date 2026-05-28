-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WAWAWATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "globals.inc" }

script.labels["TonyWater.scr"] = function(ctx)
    -- WAWAWATER.scr:2
end

-- Tony Evans
-- This script can be used to sink and fill water...
-- Parameters:
-- p1	- How far to move in pixels
-- p2	- Fill Rate
script.labels["RaiseWater"] = function(ctx)
    -- WAWAWATER.scr:36
    -- Raises Water and increments the Fill Rate
    if ctx:condition("bWaterSunk==1") then -- WAWAWATER.scr:42
        ctx:command("set", "nDestPosY, nOrigPosY") -- WAWAWATER.scr:43
        ctx:command("add", "nDestPosY, nMoveDistance") -- WAWAWATER.scr:44
        ctx:command("set", "bWaterSunk, 0") -- WAWAWATER.scr:45
    end -- WAWAWATER.scr:46
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- WAWAWATER.scr:48
    if ctx:condition("g_bTemp==TRUE") then -- WAWAWATER.scr:49
        ctx:command("playsound", "sFillSound, 1000, TRUE, 100, hWaterSound") -- WAWAWATER.scr:50
    end -- WAWAWATER.scr:51
    ctx:command("add", "nFillRateTotal, nWaterFillRate") -- WAWAWATER.scr:53
    ctx:command("movetopos", "nOrigPosX, nDestPosY, nOrigPosZ, nFillRateTotal, WaterDoneFilling") -- WAWAWATER.scr:54
    do return ctx:exit("") end -- WAWAWATER.scr:56
end

script.labels["LowerWater"] = function(ctx)
    -- WAWAWATER.scr:60
    -- Lowers the water
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- WAWAWATER.scr:65
    if ctx:condition("g_bTemp==TRUE") then -- WAWAWATER.scr:66
        ctx:command("playsound", "sSinkSound, 1000, TRUE, 100, hWaterSound") -- WAWAWATER.scr:67
    end -- WAWAWATER.scr:68
    ctx:command("set", "bWaterSunk, 1") -- WAWAWATER.scr:70
    ctx:command("movetopos", "nOrigPosX, nOrigPosY, nOrigPosZ, 32, WaterDoneSinking") -- WAWAWATER.scr:72
    do return ctx:exit("") end -- WAWAWATER.scr:74
end

script.labels["WaterDoneSinking"] = function(ctx)
    -- WAWAWATER.scr:77
    ctx:command("killsound", "hWaterSound") -- WAWAWATER.scr:79
    ctx:command("docallback", "1") -- WAWAWATER.scr:80
    do return ctx:exit("") end -- WAWAWATER.scr:81
end

script.labels["WaterDoneFilling"] = function(ctx)
    -- WAWAWATER.scr:84
    ctx:command("killsound", "hWaterSound") -- WAWAWATER.scr:86
    ctx:command("docallback", "2") -- WAWAWATER.scr:87
    do return ctx:exit("") end -- WAWAWATER.scr:88
end

script.labels["ToggleWater"] = function(ctx)
    -- WAWAWATER.scr:91
    if ctx:condition("bWaterSunk==TRUE") then -- WAWAWATER.scr:94
        mm9.gosub(script, ctx, "RaiseWater") -- WAWAWATER.scr:95
    else -- WAWAWATER.scr:96
        mm9.gosub(script, ctx, "LowerWater") -- WAWAWATER.scr:97
    end -- WAWAWATER.scr:98
    do return ctx:exit("") end -- WAWAWATER.scr:100
end

script.labels["Main"] = function(ctx)
    -- WAWAWATER.scr:103
    -- get the position of the volume brush
    ctx:command("getmyhandle", "g_hMyObject") -- WAWAWATER.scr:109
    ctx:command("getpos", "g_hMyObject, nOrigPosX, nOrigPosY, nOrigPosZ") -- WAWAWATER.scr:110
    -- set up triggers
    ctx:addTrigger("SinkWater", "LowerWater") -- WAWAWATER.scr:113
    ctx:addTrigger("FillWater", "RaiseWater") -- WAWAWATER.scr:114
    ctx:addTrigger("ToggleWater", "ToggleWater") -- WAWAWATER.scr:115
    -- get the parameters
    ctx:getParam(0, "g_nTemp") -- WAWAWATER.scr:118
    if ctx:condition("g_nTemp!=0") then -- WAWAWATER.scr:120
        ctx:command("set", "nWaterToLeave, g_nTemp") -- WAWAWATER.scr:121
    end -- WAWAWATER.scr:122
    ctx:getParam(1, "g_nTemp") -- WAWAWATER.scr:124
    if ctx:condition("g_nTemp!=0") then -- WAWAWATER.scr:126
        ctx:command("set", "nWaterSinkRate, g_nTemp") -- WAWAWATER.scr:127
    end -- WAWAWATER.scr:128
    ctx:getParam(2, "g_nTemp") -- WAWAWATER.scr:130
    if ctx:condition("g_nTemp!=0") then -- WAWAWATER.scr:132
        ctx:command("set", "nWaterFillRate, g_nTemp") -- WAWAWATER.scr:133
    end -- WAWAWATER.scr:134
    do return ctx:exit("") end -- WAWAWATER.scr:136
end

return script
