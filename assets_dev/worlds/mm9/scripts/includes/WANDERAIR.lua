-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WANDERAIR.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "aiglobals.inc" }

-- WanderAir.inc
-- Jeff Leggett
-- 2/22/2000
-- Include file used by creatures that fly around.... (wander)
script.labels["WanderAirObstacle"] = function(ctx)
    -- WANDERAIR.inc:26
    -- p0		- handle to obstacle
    -- p1-3	- Normal of the collision...
    -- For now, just go the opposite direction +- a little..
    ctx:getParam(1, "g_rotX") -- WANDERAIR.inc:33
    ctx:getParam(2, "g_rotY") -- WANDERAIR.inc:34
    ctx:getParam(3, "g_rotZ") -- WANDERAIR.inc:35
    ctx:randomFloat(-0.20, 0.20, "g_nRandom") -- WANDERAIR.inc:37
    ctx:add("g_rotX", "g_nRandom") -- WANDERAIR.inc:38
    ctx:randomFloat(-0.20, 0.20, "g_nRandom") -- WANDERAIR.inc:40
    ctx:add("g_rotZ", "g_nRandom") -- WANDERAIR.inc:41
    ctx:self():faceDir("g_rotX", "g_rotY", "g_rotZ", 90) -- WANDERAIR.inc:43
    ctx:self():walk() -- WANDERAIR.inc:44
    ctx:randomFloat(3, 10, "g_nRandom") -- WANDERAIR.inc:46
    ctx:wait(0, "g_nRandom", "WanderAirGo") -- WANDERAIR.inc:47
    do return ctx:exit("TRUE") end -- WANDERAIR.inc:49
end

script.labels["WanderAirGo"] = function(ctx)
    -- WANDERAIR.inc:52
    -- Picks a direction and goes...
    ctx:randomFloat(15, 90, "g_turnDeg") -- WANDERAIR.inc:57
    -- GetRandomFloat 20, 50, g_turnRate
    ctx:set("g_turnRate", "g_turnDeg") -- WANDERAIR.inc:60
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- WANDERAIR.inc:62
    ctx:state().g_dist = ctx:vecDist("g_posX", "g_posY", "g_posZ", "g_startX", "g_startY", "g_startZ") -- WANDERAIR.inc:64
    if ctx:condition("g_dist>MAX_DIST_FROM_STARTPOINT") then -- WANDERAIR.inc:66
        -- Too far away from original starting point!!
        ctx:self():facePos("g_startX", "g_startY", "g_startZ", 180) -- WANDERAIR.inc:68
    else -- WANDERAIR.inc:69
        ctx:randomInt(0, 1, "g_nRandom") -- WANDERAIR.inc:70
        if ctx:condition("g_nRandom==0") then -- WANDERAIR.inc:72
            ctx:state().g_turnDeg = (tonumber(ctx:state().g_turnDeg) or 0) * -1 -- WANDERAIR.inc:73
        end -- WANDERAIR.inc:74
        ctx:self():rotate(0, 1, 0, "g_turnDeg", "g_turnRate") -- WANDERAIR.inc:76
    end -- WANDERAIR.inc:77
    ctx:self():walk() -- WANDERAIR.inc:79
    ctx:randomFloat(3, 10, "g_nRandom") -- WANDERAIR.inc:81
    ctx:wait(0, "g_nRandom", "WanderAirGo") -- WANDERAIR.inc:82
    do return ctx:exit("") end -- WANDERAIR.inc:84
end

script.labels["WanderAirStuck"] = function(ctx)
    -- WANDERAIR.inc:87
    mm9.gosub(script, ctx, "WanderAirGo") -- WANDERAIR.inc:90
    do return ctx:exit("TRUE") end -- WANDERAIR.inc:91
end

script.labels["WanderAirStartup"] = function(ctx)
    -- WANDERAIR.inc:94
    ctx:state().g_startX, ctx:state().g_startY, ctx:state().g_startZ = ctx:self():pos() -- WANDERAIR.inc:97
    ctx:state().g_bTemp = ctx:self():isOnGround() -- WANDERAIR.inc:99
    if ctx:condition("g_bTemp==TRUE") then -- WANDERAIR.inc:101
        ctx:self():launch("WanderAirGo", "g_defaultLaunchAlt") -- WANDERAIR.inc:102
    else -- WANDERAIR.inc:103
        mm9.gosub(script, ctx, "WanderAirGo") -- WANDERAIR.inc:104
    end -- WANDERAIR.inc:105
    do return ctx:exit("TRUE") end -- WANDERAIR.inc:107
end

script.labels["WanderAirInit"] = function(ctx)
    -- WANDERAIR.inc:110
    ctx:onEvent("OnObstacle", "WanderAirObstacle") -- WANDERAIR.inc:114
    ctx:onEvent("OnStuck", "WanderAirStuck") -- WANDERAIR.inc:115
    -- Must Wait 0, and do some stuff after initial execution...
    ctx:wait(0, 0.1, "WanderAirStartup") -- WANDERAIR.inc:118
    do return ctx:exit("") end -- WANDERAIR.inc:120
end

return script
