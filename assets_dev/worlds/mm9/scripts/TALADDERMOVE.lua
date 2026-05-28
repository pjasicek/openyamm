-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TALADDERMOVE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

script.labels["TAladdermove.scr"] = function(ctx)
    -- TALADDERMOVE.scr:2
end

-- Timmy
-- moves the ladder object up and down for Training Arena 1
-- Parameters:
-- p1	- How far to go
-- p2	- Drop Wait Rate
-- Default parameters
script.labels["OnRaiseLadder"] = function(ctx)
    -- TALADDERMOVE.scr:41
    do return ctx:exit("") end -- TALADDERMOVE.scr:44
end

script.labels["OnlowerLadder"] = function(ctx)
    -- TALADDERMOVE.scr:47
    ctx:command("getdims", "g_hMyObject, nDimsX, nDimsY, nDimsZ") -- TALADDERMOVE.scr:50
    ctx:command("set", "nDestPosY, nOrigPosY") -- TALADDERMOVE.scr:51
    ctx:command("sub", "nDestPosY, Distance") -- TALADDERMOVE.scr:52
    ctx:command("movetopos", "nOrigPosX, nDestPosY, nOrigPosZ, Rate") -- TALADDERMOVE.scr:56
    do return ctx:exit("") end -- TALADDERMOVE.scr:58
end

script.labels["StopSound"] = function(ctx)
    -- TALADDERMOVE.scr:65
    ctx:command("killsound", "hWaterSound") -- TALADDERMOVE.scr:67
    do return ctx:exit("") end -- TALADDERMOVE.scr:69
end

script.labels["Main"] = function(ctx)
    -- TALADDERMOVE.scr:72
    -- TRACEON
    ctx:command("getmyhandle", "g_hMyObject") -- TALADDERMOVE.scr:79
    ctx:command("getpos", "g_hMyObject, nOrigPosX, nOrigPosY, nOrigPosZ") -- TALADDERMOVE.scr:80
    ctx:addTrigger("Lower", "OnLowerladder") -- TALADDERMOVE.scr:82
    ctx:addTrigger("Raise", "OnRaiseLadder") -- TALADDERMOVE.scr:83
    ctx:getParam(0, "g_nTemp") -- TALADDERMOVE.scr:86
    if ctx:condition("g_nTemp!=0") then -- TALADDERMOVE.scr:88
        ctx:command("set", "Distance, g_nTemp") -- TALADDERMOVE.scr:89
    end -- TALADDERMOVE.scr:90
    ctx:getParam(1, "g_nTemp") -- TALADDERMOVE.scr:92
    if ctx:condition("g_nTemp!=0") then -- TALADDERMOVE.scr:94
        ctx:command("set", "Rate, g_nTemp") -- TALADDERMOVE.scr:95
    end -- TALADDERMOVE.scr:96
    do return ctx:exit("") end -- TALADDERMOVE.scr:98
end

return script
