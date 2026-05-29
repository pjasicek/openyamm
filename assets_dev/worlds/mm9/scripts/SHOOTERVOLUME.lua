-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SHOOTERVOLUME.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- ShooterVolume.scr
-- Tony Evans
-- This script turns a shooter on if you are inside a
-- volume brush and turns it off if you are outside
-- Parameters:
-- p0 = The name of the Shooter object
-- p1 = The name of the Volume Brush object
-- Volume Dims Variables
-- Volume Object Variables
-- Player dim Variables
-- Name of Shooter object and Volume Brush
script.labels["Init"] = function(ctx)
    -- SHOOTERVOLUME.scr:48
    -- Get coords for Volume brush
    ctx:state().g_hobject = ctx:objectOrNil("ShooterVolumeBrush") -- SHOOTERVOLUME.scr:52
    ctx:state().VolumeMinX, ctx:state().VolumeMinY, ctx:state().VolumeMinZ, ctx:state().VolumeMaxX, ctx:state().VolumeMaxY, ctx:state().VolumeMaxZ = ctx:object("g_hobject"):minMax() -- SHOOTERVOLUME.scr:53
    ctx:state().VolumeX, ctx:state().VolumeY, ctx:state().VolumeZ = ctx:object("g_hobject"):pos() -- SHOOTERVOLUME.scr:54
    do return ctx:exit("") end -- SHOOTERVOLUME.scr:55
end

script.labels["CheckPlayerLoop"] = function(ctx)
    -- SHOOTERVOLUME.scr:58
    -- Get the coordinates of all nearby players and store them in an array
    ctx:getPlayersWithinDist("VolumeX", "VolumeY", "VolumeZ", 512, "PlayerIds", 8, "Playercount") -- SHOOTERVOLUME.scr:62
    if ctx:condition("Playercount==0") then -- SHOOTERVOLUME.scr:64
        mm9.gosub(script, ctx, "ShutOff") -- SHOOTERVOLUME.scr:65
        do return ctx:exit("") end -- SHOOTERVOLUME.scr:66
    end -- SHOOTERVOLUME.scr:67
    ctx:state().loopcounter = 0 -- SHOOTERVOLUME.scr:69
end

script.labels["CheckPlayerLoop2"] = function(ctx)
    -- SHOOTERVOLUME.scr:72
    ctx:arrayGet("PlayerIds", "loopCounter", "g_hobject") -- SHOOTERVOLUME.scr:75
    mm9.gosub(script, ctx, "CheckPlayer") -- SHOOTERVOLUME.scr:76
    ctx:state().loopcounter = (tonumber(ctx:state().loopcounter) or 0) + 1 -- SHOOTERVOLUME.scr:77
    if ctx:condition("loopcounter<Playercount") then -- SHOOTERVOLUME.scr:78
        do return mm9.gotoLabel(script, ctx, "CheckPlayerLoop2") end -- SHOOTERVOLUME.scr:79
    end -- SHOOTERVOLUME.scr:80
    do return ctx:exit("") end -- SHOOTERVOLUME.scr:81
end

script.labels["CheckPlayer"] = function(ctx)
    -- SHOOTERVOLUME.scr:84
    -- Gets the dims of Player
    ctx:state().PlayerX, ctx:state().PlayerY, ctx:state().PlayerZ = ctx:object("g_hobject"):pos() -- SHOOTERVOLUME.scr:89
    ctx:state().outside = false -- SHOOTERVOLUME.scr:90
    if ctx:condition("PlayerX<VolumeMinX") then -- SHOOTERVOLUME.scr:92
        ctx:state().outside = true -- SHOOTERVOLUME.scr:93
    end -- SHOOTERVOLUME.scr:94
    if ctx:condition("PlayerX>VolumeMaxX") then -- SHOOTERVOLUME.scr:95
        ctx:state().outside = true -- SHOOTERVOLUME.scr:96
    end -- SHOOTERVOLUME.scr:97
    if ctx:condition("PlayerY<VolumeMinY") then -- SHOOTERVOLUME.scr:98
        ctx:state().outside = true -- SHOOTERVOLUME.scr:99
    end -- SHOOTERVOLUME.scr:100
    if ctx:condition("PlayerY>VolumeMaxY") then -- SHOOTERVOLUME.scr:101
        ctx:state().outside = true -- SHOOTERVOLUME.scr:102
    end -- SHOOTERVOLUME.scr:103
    if ctx:condition("PlayerZ<VolumeMinZ") then -- SHOOTERVOLUME.scr:104
        ctx:state().outside = true -- SHOOTERVOLUME.scr:105
    end -- SHOOTERVOLUME.scr:106
    if ctx:condition("PlayerZ>VolumeMaxZ") then -- SHOOTERVOLUME.scr:107
        ctx:state().outside = true -- SHOOTERVOLUME.scr:108
    end -- SHOOTERVOLUME.scr:109
    if ctx:condition("outside==TRUE") then -- SHOOTERVOLUME.scr:110
        mm9.gosub(script, ctx, "ShutOff") -- SHOOTERVOLUME.scr:111
        do return ctx:exit("") end -- SHOOTERVOLUME.scr:112
    end -- SHOOTERVOLUME.scr:113
    ctx:wait(1, 1, "CheckPlayerLoop") -- SHOOTERVOLUME.scr:115
    do return ctx:exit("") end -- SHOOTERVOLUME.scr:117
end

script.labels["HandleTouchNotify"] = function(ctx)
    -- SHOOTERVOLUME.scr:120
    mm9.gosub(script, ctx, "TurnOn") -- SHOOTERVOLUME.scr:123
    do return ctx:exit("") end -- SHOOTERVOLUME.scr:124
end

script.labels["TurnOn"] = function(ctx)
    -- SHOOTERVOLUME.scr:127
    mm9.gosub(script, ctx, "Init") -- SHOOTERVOLUME.scr:130
    -- turn shooter on
    ctx:object("Shooter"):trigger("on") -- SHOOTERVOLUME.scr:133-134
    -- turn touchnotify off
    ctx:onEvent("OnTouchNotify") -- SHOOTERVOLUME.scr:137
    ctx:wait(1, 1, "CheckplayerLoop") -- SHOOTERVOLUME.scr:139
    do return ctx:exit("") end -- SHOOTERVOLUME.scr:141
end

script.labels["ShutOff"] = function(ctx)
    -- SHOOTERVOLUME.scr:144
    ctx:object("Shooter"):trigger("off") -- SHOOTERVOLUME.scr:147-148
    ctx:onEvent("OnTouchNotify", "HandleTouchNotify") -- SHOOTERVOLUME.scr:149
    do return ctx:exit("") end -- SHOOTERVOLUME.scr:151
end

script.labels["Main"] = function(ctx)
    -- SHOOTERVOLUME.scr:154
    ctx:wait(0.1, 0.1, "init") -- SHOOTERVOLUME.scr:157
    -- Get parameters
    ctx:getParam(0, "Shooter") -- SHOOTERVOLUME.scr:160
    ctx:getParam(1, "ShooterVolumeBrush") -- SHOOTERVOLUME.scr:161
    ctx:onEvent("OnTouchNotify", "HandleTouchNotify") -- SHOOTERVOLUME.scr:163
    do return ctx:exit("") end -- SHOOTERVOLUME.scr:165
end

return script
