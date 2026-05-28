-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MOONWATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "globals.inc" }

script.labels["TonyWater.scr"] = function(ctx)
    -- MOONWATER.scr:2
end

-- Tony Evans
-- This script can be used to sink and fill water...
-- Parameters:
-- p1	- How far to move in pixels
-- p2	- Fill Rate
script.labels["RaiseWater"] = function(ctx)
    -- MOONWATER.scr:36
    -- Raises Water and increments the Fill Rate
    if ctx:condition("bWaterSunk==1") then -- MOONWATER.scr:42
        ctx:command("set", "nDestPosY, nOrigPosY") -- MOONWATER.scr:43
        ctx:command("add", "nDestPosY, nMoveDistance") -- MOONWATER.scr:44
        ctx:command("set", "bWaterSunk, 0") -- MOONWATER.scr:45
    end -- MOONWATER.scr:46
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- MOONWATER.scr:48
    if ctx:condition("g_bTemp==TRUE") then -- MOONWATER.scr:49
        ctx:command("playsound", "sFillSound, 1000, TRUE, 100, hWaterSound") -- MOONWATER.scr:50
    end -- MOONWATER.scr:51
    ctx:command("add", "nFillRateTotal, nWaterFillRate") -- MOONWATER.scr:53
    ctx:command("movetopos", "nOrigPosX, nDestPosY, nOrigPosZ, nFillRateTotal, LowerWater") -- MOONWATER.scr:54
    do return ctx:exit("") end -- MOONWATER.scr:56
end

script.labels["LowerWater"] = function(ctx)
    -- MOONWATER.scr:60
    -- Lowers the water
    ctx:command("killsound", "hWaterSound") -- MOONWATER.scr:65
    ctx:command("issounddone", "hWaterSound, g_bTemp") -- MOONWATER.scr:66
    if ctx:condition("g_bTemp==TRUE") then -- MOONWATER.scr:67
        ctx:command("playsound", "sSinkSound, 1000, TRUE, 100, hWaterSound") -- MOONWATER.scr:68
    end -- MOONWATER.scr:69
    ctx:command("set", "bWaterSunk, 1") -- MOONWATER.scr:71
    ctx:command("movetopos", "nOrigPosX, nOrigPosY, nOrigPosZ, 32, WaterDone") -- MOONWATER.scr:73
    do return ctx:exit("") end -- MOONWATER.scr:75
end

script.labels["WaterDone"] = function(ctx)
    -- MOONWATER.scr:78
    ctx:command("killsound", "hWaterSound") -- MOONWATER.scr:80
    ctx:command("getobjecthandle", "WaterWheel1, g_hobject") -- MOONWATER.scr:82
    ctx:trigger("g_hobject", "unlock") -- MOONWATER.scr:83
    ctx:command("getobjecthandle", "WaterWheel2, g_hobject") -- MOONWATER.scr:84
    ctx:trigger("g_hobject", "unlock") -- MOONWATER.scr:85
    ctx:command("getobjecthandle", "WaterWheel3, g_hobject") -- MOONWATER.scr:86
    ctx:trigger("g_hobject", "unlock") -- MOONWATER.scr:87
    ctx:command("getobjecthandle", "WaterWheel4, g_hobject") -- MOONWATER.scr:88
    ctx:trigger("g_hobject", "unlock") -- MOONWATER.scr:89
    if ctx:condition("bWaterSunk==1") then -- MOONWATER.scr:91
        ctx:command("set", "nFillRateTotal, 0") -- MOONWATER.scr:92
    end -- MOONWATER.scr:93
    do return ctx:exit("") end -- MOONWATER.scr:94
end

script.labels["ToggleWater"] = function(ctx)
    -- MOONWATER.scr:97
    if ctx:condition("bWaterSunk==TRUE") then -- MOONWATER.scr:100
        mm9.gosub(script, ctx, "RaiseWater") -- MOONWATER.scr:101
    else -- MOONWATER.scr:102
        mm9.gosub(script, ctx, "LowerWater") -- MOONWATER.scr:103
    end -- MOONWATER.scr:104
    do return ctx:exit("") end -- MOONWATER.scr:106
end

script.labels["Main"] = function(ctx)
    -- MOONWATER.scr:109
    -- TRACEON
    -- get the position of the volume brush
    ctx:command("getmyhandle", "g_hMyObject") -- MOONWATER.scr:117
    ctx:command("getpos", "g_hMyObject, nOrigPosX, nOrigPosY, nOrigPosZ") -- MOONWATER.scr:118
    -- set up triggers
    ctx:addTrigger("SinkWater", "LowerWater") -- MOONWATER.scr:121
    ctx:addTrigger("FillWater", "RaiseWater") -- MOONWATER.scr:122
    ctx:addTrigger("ToggleWater", "ToggleWater") -- MOONWATER.scr:123
    -- get the parameters
    ctx:getParam(0, "g_nTemp") -- MOONWATER.scr:126
    if ctx:condition("g_nTemp!=0") then -- MOONWATER.scr:128
        ctx:command("set", "nMoveDistance, g_nTemp") -- MOONWATER.scr:129
    end -- MOONWATER.scr:130
    ctx:getParam(1, "g_nTemp") -- MOONWATER.scr:132
    if ctx:condition("g_nTemp!=0") then -- MOONWATER.scr:134
        ctx:command("set", "nWaterFillRate, g_nTemp") -- MOONWATER.scr:135
    end -- MOONWATER.scr:136
    do return ctx:exit("") end -- MOONWATER.scr:138
end

return script
