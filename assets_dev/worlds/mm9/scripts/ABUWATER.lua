-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ABUWATER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "globals.inc" }

script.labels["AbuWater.scr"] = function(ctx)
    -- ABUWATER.scr:2
end

-- Tony Evans
-- This script is used to raise water for the trap in Abu Dectome's
-- burial chamber in the Tomb of a Thousand Terrors
-- Parameters:
-- p1	- How many inches of water to leave
-- p2	- Fill Rate
-- Default parameters
script.labels["OnRaiseWater"] = function(ctx)
    -- ABUWATER.scr:37
    ctx:state().nDimsX, ctx:state().nDimsY, ctx:state().nDimsZ = ctx:self():dims() -- ABUWATER.scr:40
    ctx:set("nDestPosY", "nOrigPosY") -- ABUWATER.scr:41
    ctx:add("nDestPosY", "nDimsY") -- ABUWATER.scr:42
    -- Leave some water there....
    ctx:sub("nDestPosY", "nWaterToLeave") -- ABUWATER.scr:46
    ctx:isSoundDone("hWaterSound", "g_bTemp") -- ABUWATER.scr:48
    if ctx:condition("g_bTemp==TRUE") then -- ABUWATER.scr:49
        ctx:playSound("sFillSound", 1000, "TRUE", 100, "hWaterSound") -- ABUWATER.scr:50
    end -- ABUWATER.scr:51
    ctx:self():moveToPos("nOrigPosX", "nDestPosY", "nOrigPosZ", "nWaterFillRate", "StopSound") -- ABUWATER.scr:53
    do return ctx:exit("") end -- ABUWATER.scr:55
end

script.labels["StopSound"] = function(ctx)
    -- ABUWATER.scr:58
    ctx:killSound("hWaterSound") -- ABUWATER.scr:60
    do return ctx:exit("") end -- ABUWATER.scr:62
end

script.labels["Main"] = function(ctx)
    -- ABUWATER.scr:65
    ctx:state().nOrigPosX, ctx:state().nOrigPosY, ctx:state().nOrigPosZ = ctx:self():pos() -- ABUWATER.scr:71
    ctx:addTrigger("RaiseWater", "OnRaiseWater") -- ABUWATER.scr:73
    ctx:getParam(0, "g_nTemp") -- ABUWATER.scr:75
    if ctx:condition("g_nTemp!=0") then -- ABUWATER.scr:77
        ctx:set("nWaterToLeave", "g_nTemp") -- ABUWATER.scr:78
    end -- ABUWATER.scr:79
    ctx:getParam(1, "g_nTemp") -- ABUWATER.scr:81
    if ctx:condition("g_nTemp!=0") then -- ABUWATER.scr:83
        ctx:set("nWaterFillRate", "g_nTemp") -- ABUWATER.scr:84
    end -- ABUWATER.scr:85
    do return ctx:exit("") end -- ABUWATER.scr:87
end

return script
