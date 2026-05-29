-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WATER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "globals.inc" }

script.labels["Water.inc"] = function(ctx)
    -- WATER.inc:2
end

-- Jeff Leggett
-- This script can be used to sink and fill water...
-- Parameters:
-- p1	- How many inches of water to leave (when sinking)
-- p2	- Sink Rate
-- p3	- Fill Rate
-- Default parameters
script.labels["WaterOnSink"] = function(ctx)
    -- WATER.inc:42
    -- Sets the water in motion in the downward direction...
    ctx:state().nDimsX, ctx:state().nDimsY, ctx:state().nDimsZ = ctx:self():dims() -- WATER.inc:47
    ctx:set("nDestPosY", "nOrigPosY") -- WATER.inc:48
    ctx:sub("nDestPosY", "nDimsY") -- WATER.inc:49
    ctx:sub("nDestPosY", "nDimsY") -- WATER.inc:50
    -- Leave some water there....
    ctx:add("nDestPosY", "nWaterToLeave") -- WATER.inc:54
    ctx:state().bWaterSunk = 1 -- WATER.inc:56
    ctx:isSoundDone("hWaterSound", "g_bTemp") -- WATER.inc:58
    if ctx:condition("g_bTemp==TRUE") then -- WATER.inc:59
        ctx:playSoundHandle("sSinkSound", "hWaterSound", 1000, "TRUE", 100) -- WATER.inc:60
    end -- WATER.inc:61
    ctx:self():moveToPos("nOrigPosX", "nDestPosY", "nOrigPosZ", "nWaterSinkRate", "WaterDoneSinking") -- WATER.inc:63
    do return ctx:exit("") end -- WATER.inc:65
end

script.labels["WaterDoneSinking"] = function(ctx)
    -- WATER.inc:68
    ctx:killSound("hWaterSound") -- WATER.inc:70
    ctx:doCallback(1) -- WATER.inc:71
    do return ctx:exit("") end -- WATER.inc:72
end

script.labels["WaterDoneFilling"] = function(ctx)
    -- WATER.inc:76
    ctx:killSound("hWaterSound") -- WATER.inc:78
    ctx:doCallback(2) -- WATER.inc:79
    do return ctx:exit("") end -- WATER.inc:80
end

script.labels["WaterOnFill"] = function(ctx)
    -- WATER.inc:83
    ctx:set("nDestPosY", "nOrigPosY") -- WATER.inc:86
    ctx:state().bWaterSunk = 0 -- WATER.inc:87
    ctx:isSoundDone("hWaterSound", "g_bTemp") -- WATER.inc:89
    if ctx:condition("g_bTemp==TRUE") then -- WATER.inc:90
        ctx:playSoundHandle("sFillSound", "hWaterSound", 1000, "TRUE", 100) -- WATER.inc:91
    end -- WATER.inc:92
    ctx:self():moveToPos("nOrigPosX", "nDestPosY", "nOrigPosZ", "nWaterFillRate", "WaterDoneFilling") -- WATER.inc:94
    do return ctx:exit("") end -- WATER.inc:96
end

script.labels["WaterOnToggle"] = function(ctx)
    -- WATER.inc:99
    if ctx:condition("bWaterSunk==TRUE") then -- WATER.inc:102
        mm9.gosub(script, ctx, "WaterOnFill") -- WATER.inc:103
    else -- WATER.inc:104
        mm9.gosub(script, ctx, "WaterOnSink") -- WATER.inc:105
    end -- WATER.inc:106
    do return ctx:exit("") end -- WATER.inc:108
end

script.labels["WaterInit"] = function(ctx)
    -- WATER.inc:111
    ctx:state().nOrigPosX, ctx:state().nOrigPosY, ctx:state().nOrigPosZ = ctx:self():pos() -- WATER.inc:117
    ctx:addTrigger("SinkWater", "WaterOnSink") -- WATER.inc:119
    ctx:addTrigger("FillWater", "WaterOnFill") -- WATER.inc:120
    ctx:addTrigger("ToggleWater", "WaterOnToggle") -- WATER.inc:121
    ctx:getParam(0, "g_nTemp") -- WATER.inc:123
    if ctx:condition("g_nTemp!=0") then -- WATER.inc:125
        ctx:set("nWaterToLeave", "g_nTemp") -- WATER.inc:126
    end -- WATER.inc:127
    ctx:getParam(1, "g_nTemp") -- WATER.inc:129
    if ctx:condition("g_nTemp!=0") then -- WATER.inc:131
        ctx:set("nWaterSinkRate", "g_nTemp") -- WATER.inc:132
    end -- WATER.inc:133
    ctx:getParam(2, "g_nTemp") -- WATER.inc:135
    if ctx:condition("g_nTemp!=0") then -- WATER.inc:137
        ctx:set("nWaterFillRate", "g_nTemp") -- WATER.inc:138
    end -- WATER.inc:139
    do return ctx:exit("") end -- WATER.inc:141
end

return script
