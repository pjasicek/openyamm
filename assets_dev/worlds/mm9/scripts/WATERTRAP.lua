-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WATERTRAP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "globals.inc" }

script.labels["WaterTrap.scr"] = function(ctx)
    -- WATERTRAP.scr:2
end

-- Tony Evans
-- This script can be used to sink and fill water for the Water Trap...
-- Parameters:
-- p1	- How far to move in pixels
-- p2	- Fill Rate
script.labels["RaiseWater"] = function(ctx)
    -- WATERTRAP.scr:36
    -- Raises Water and increments the Fill Rate
    if ctx:condition("bWaterSunk==1") then -- WATERTRAP.scr:42
        ctx:command("set", "nDestPosY, nOrigPosY") -- WATERTRAP.scr:43
        ctx:command("add", "nDestPosY, nMoveDistance") -- WATERTRAP.scr:44
        ctx:command("set", "bWaterSunk, 0") -- WATERTRAP.scr:45
    end -- WATERTRAP.scr:46
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- WATERTRAP.scr:48
    if ctx:condition("g_bTemp==TRUE") then -- WATERTRAP.scr:49
        ctx:command("playsound", "sFillSound, DoNothing, 1000, TRUE, 100, hWaterSound") -- WATERTRAP.scr:50
    end -- WATERTRAP.scr:51
    ctx:command("add", "nFillRateTotal, nWaterFillRate") -- WATERTRAP.scr:53
    ctx:command("movetopos", "nOrigPosX, nDestPosY, nOrigPosZ, nFillRateTotal, RaiseDone") -- WATERTRAP.scr:54
    do return ctx:exit("") end -- WATERTRAP.scr:56
end

script.labels["LowerWater"] = function(ctx)
    -- WATERTRAP.scr:60
    -- Lowers the water
    ctx:command("killsound", "hWaterSound") -- WATERTRAP.scr:65
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- WATERTRAP.scr:66
    if ctx:condition("g_bTemp==TRUE") then -- WATERTRAP.scr:67
        ctx:command("playsound", "sSinkSound, DoNothing, 1000, TRUE, 100, hWaterSound") -- WATERTRAP.scr:68
    end -- WATERTRAP.scr:69
    ctx:command("set", "bWaterSunk, 1") -- WATERTRAP.scr:71
    ctx:command("movetopos", "nOrigPosX, nOrigPosY, nOrigPosZ, 32, LowerDone") -- WATERTRAP.scr:73
    do return ctx:exit("") end -- WATERTRAP.scr:75
end

script.labels["RaiseDone"] = function(ctx)
    -- WATERTRAP.scr:78
    do return ctx:exit("") end -- WATERTRAP.scr:81
end

script.labels["LowerDone"] = function(ctx)
    -- WATERTRAP.scr:84
    ctx:command("killsound", "hWaterSound") -- WATERTRAP.scr:87
    if ctx:condition("bWaterSunk==1") then -- WATERTRAP.scr:88
        ctx:command("set", "nFillRateTotal, 0") -- WATERTRAP.scr:89
    end -- WATERTRAP.scr:90
    do return ctx:exit("") end -- WATERTRAP.scr:92
end

script.labels["ToggleWater"] = function(ctx)
    -- WATERTRAP.scr:95
    if ctx:condition("bWaterSunk==TRUE") then -- WATERTRAP.scr:98
        mm9.gosub(script, ctx, "RaiseWater") -- WATERTRAP.scr:99
    else -- WATERTRAP.scr:100
        mm9.gosub(script, ctx, "LowerWater") -- WATERTRAP.scr:101
    end -- WATERTRAP.scr:102
    do return ctx:exit("") end -- WATERTRAP.scr:104
end

script.labels["Main"] = function(ctx)
    -- WATERTRAP.scr:107
    -- TRACEON
    -- get the position of the volume brush
    ctx:command("getmyhandle", "g_hMyObject") -- WATERTRAP.scr:115
    ctx:command("getpos", "g_hMyObject, nOrigPosX, nOrigPosY, nOrigPosZ") -- WATERTRAP.scr:116
    -- set up triggers
    ctx:addTrigger("SinkWater", "LowerWater") -- WATERTRAP.scr:119
    ctx:addTrigger("FillWater", "RaiseWater") -- WATERTRAP.scr:120
    ctx:addTrigger("ToggleWater", "ToggleWater") -- WATERTRAP.scr:121
    -- get the parameters
    ctx:getParam(0, "g_nTemp") -- WATERTRAP.scr:124
    if ctx:condition("g_nTemp!=0") then -- WATERTRAP.scr:126
        ctx:command("set", "nMoveDistance, g_nTemp") -- WATERTRAP.scr:127
    end -- WATERTRAP.scr:128
    ctx:getParam(1, "g_nTemp") -- WATERTRAP.scr:130
    if ctx:condition("g_nTemp!=0") then -- WATERTRAP.scr:132
        ctx:command("set", "nWaterFillRate, g_nTemp") -- WATERTRAP.scr:133
    end -- WATERTRAP.scr:134
    do return ctx:exit("") end -- WATERTRAP.scr:136
end

return script
