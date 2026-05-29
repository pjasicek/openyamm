-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WYVERN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }

-- WyvernAir.scr
-- Quick-and-dirty script for wyvern...
script.labels["HandleObstacle"] = function(ctx)
    -- WYVERN.scr:16
    -- p0		- handle to obstacle
    -- p1-3	- Normal of the collision...
    -- For now, just go the opposite direction +- a little..
    ctx:getParam(1, "g_rotX") -- WYVERN.scr:23
    ctx:getParam(2, "g_rotY") -- WYVERN.scr:24
    ctx:getParam(3, "g_rotZ") -- WYVERN.scr:25
    ctx:randomFloat(-0.20, 0.20, "g_nRandom") -- WYVERN.scr:27
    ctx:add("g_rotX", "g_nRandom") -- WYVERN.scr:28
    ctx:randomFloat(-0.20, 0.20, "g_nRandom") -- WYVERN.scr:30
    ctx:add("g_rotZ", "g_nRandom") -- WYVERN.scr:31
    ctx:self():faceDir("g_rotX", "g_rotY", "g_rotZ", 90) -- WYVERN.scr:33
    ctx:self():walk() -- WYVERN.scr:34
    ctx:randomFloat(3, 10, "g_nRandom") -- WYVERN.scr:36
    ctx:wait(0, "g_nRandom", "Pause") -- WYVERN.scr:37
    do return ctx:exit("TRUE") end -- WYVERN.scr:39
end

script.labels["Pause"] = function(ctx)
    -- WYVERN.scr:42
    -- Stop, and go into idle mode for a while...
    ctx:self():setIdle() -- WYVERN.scr:48
    ctx:self():stop() -- WYVERN.scr:49
    ctx:randomFloat(3, 10, "g_nRandom") -- WYVERN.scr:51
    ctx:wait(0, "g_nRandom", "PickADirectionAndWalk") -- WYVERN.scr:53
    do return ctx:exit("TRUE") end -- WYVERN.scr:55
end

script.labels["PickADirectionAndWalk"] = function(ctx)
    -- WYVERN.scr:58
    ctx:randomFloat(15, 90, "turnDeg") -- WYVERN.scr:61
    -- GetRandomFloat 20, 50, turnRate
    ctx:set("turnRate", "turnDeg") -- WYVERN.scr:64
    ctx:randomInt(0, 1, "g_nRandom") -- WYVERN.scr:66
    if ctx:condition("g_nRandom==0") then -- WYVERN.scr:68
        ctx:state().turnDeg = (tonumber(ctx:state().turnDeg) or 0) * -1 -- WYVERN.scr:69
    end -- WYVERN.scr:70
    ctx:self():rotate(0, 1, 0, "turnDeg", "turnRate") -- WYVERN.scr:72
    ctx:self():walk() -- WYVERN.scr:73
    ctx:randomFloat(3, 10, "g_nRandom") -- WYVERN.scr:75
    ctx:wait(0, "g_nRandom", "Pause") -- WYVERN.scr:76
    do return ctx:exit("") end -- WYVERN.scr:78
end

script.labels["HandleTouch"] = function(ctx)
    -- WYVERN.scr:81
    -- Time to fly!
    do return ctx:exit("FALSE") end -- WYVERN.scr:86
end

script.labels["HandleStuck"] = function(ctx)
    -- WYVERN.scr:89
    mm9.gosub(script, ctx, "PickADirectionAndWalk") -- WYVERN.scr:92
    do return ctx:exit("TRUE") end -- WYVERN.scr:93
end

script.labels["LaunchDone"] = function(ctx)
    -- WYVERN.scr:96
    do return ctx:exit("TRUE") end -- WYVERN.scr:101
end

script.labels["WaitCancel"] = function(ctx)
    -- WYVERN.scr:104
end

script.labels["DamageDone"] = function(ctx)
    -- WYVERN.scr:108
    ctx:state().g_bTemp = ctx:self():isOnGround() -- WYVERN.scr:111
    if ctx:condition("g_bTemp==TRUE") then -- WYVERN.scr:113
        ctx:self():launch("LaunchDone", 2000) -- WYVERN.scr:114
    else -- WYVERN.scr:115
        ctx:self():land() -- WYVERN.scr:116
    end -- WYVERN.scr:117
    do return ctx:exit("TRUE") end -- WYVERN.scr:119
end

script.labels["Main"] = function(ctx)
    -- WYVERN.scr:122
    -- TraceON
    ctx:onEvent("OnDamageDone", "DamageDone") -- WYVERN.scr:128
    ctx:self():setIdle() -- WYVERN.scr:129
    do return ctx:exit("") end -- WYVERN.scr:131
    ctx:onEvent("OnObstacle", "HandleObstacle") -- WYVERN.scr:133
    ctx:onEvent("OnStuck", "HandleStuck") -- WYVERN.scr:134
    ctx:onEvent("OnTouchNotify", "HandleTouch") -- WYVERN.scr:135
    ctx:randomFloat(1, 15, "g_nRandom") -- WYVERN.scr:137
    mm9.gosub(script, ctx, "Pause") -- WYVERN.scr:139
    do return ctx:exit("") end -- WYVERN.scr:141
end

return script
