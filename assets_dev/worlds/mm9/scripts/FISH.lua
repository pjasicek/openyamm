-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FISH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "aiglobals.inc" }

-- FISH.SCR
-- Jeff Leggett
-- 01/14/2000
-- Simple Fishy script
script.labels["Tick"] = function(ctx)
    -- FISH.scr:37
    ctx:self():walk() -- FISH.scr:40
    ctx:randomInt(0, 100, "g_nRandom") -- FISH.scr:42
    if ctx:condition("g_nRandom < 5") then -- FISH.scr:44
        -- It's time to jump... (if we're close enough to the surface...)
        if ctx:condition("hWater==NULL") then -- FISH.scr:48
            mm9.gosub(script, ctx, "GetWaterDims") -- FISH.scr:49
        end -- FISH.scr:50
        if ctx:condition("hWater!=NULL") then -- FISH.scr:52
            ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- FISH.scr:53
            ctx:set("g_nTemp", "dimY") -- FISH.scr:55
            ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) * 5 -- FISH.scr:56
            ctx:add("g_posY", "g_nTemp") -- FISH.scr:58
            -- DebugOut g_posY
            -- DebugOut maxWaterY
            if ctx:condition("g_posY > maxWaterY") then -- FISH.scr:63
                ctx:self():playAnimation("Jump", "Tick") -- FISH.scr:64
                do return ctx:exit("") end -- FISH.scr:65
            end -- FISH.scr:66
        end -- FISH.scr:67
    end -- FISH.scr:68
    ctx:randomFloat(15, 90, "turnDeg") -- FISH.scr:70
    -- GetRandomFloat 20, 50, turnRate
    ctx:set("turnRate", "turnDeg") -- FISH.scr:73
    ctx:randomInt(0, 1, "g_nRandom") -- FISH.scr:75
    if ctx:condition("g_nRandom==0") then -- FISH.scr:77
        ctx:state().turnDeg = (tonumber(ctx:state().turnDeg) or 0) * -1 -- FISH.scr:78
    end -- FISH.scr:79
    ctx:self():rotate(0, 1, 0, "turnDeg", "turnRate", "Tick") -- FISH.scr:81
    ctx:randomFloat(0.5, 1.0, "g_nRandom") -- FISH.scr:83
    ctx:wait(0, "g_nRandom", "Tick") -- FISH.scr:85
    do return ctx:exit("") end -- FISH.scr:87
end

script.labels["GetWaterDims"] = function(ctx)
    -- FISH.scr:91
    ctx:state().hWater = ctx:self():liquidContainer() -- FISH.scr:93
    if ctx:condition("hWater!=NULL") then -- FISH.scr:95
        ctx:state().minWaterX, ctx:state().minWaterY, ctx:state().minWaterZ, ctx:state().maxWaterX, ctx:state().maxWaterY, ctx:state().maxWaterZ = ctx:object("hWater"):minMax() -- FISH.scr:96
    end -- FISH.scr:97
    do return ctx:exit("") end -- FISH.scr:99
end

script.labels["Init"] = function(ctx)
    -- FISH.scr:101
    ctx:state().dimX, ctx:state().dimY, ctx:state().dimZ = ctx:self():dims() -- FISH.scr:105
    ctx:self():stop() -- FISH.scr:107
    mm9.gosub(script, ctx, "Tick") -- FISH.scr:109
    do return ctx:exit("") end -- FISH.scr:111
end

script.labels["OnTest"] = function(ctx)
    -- FISH.scr:114
    ctx:self():walk() -- FISH.scr:117
    ctx:wait(0, 1, "Tick") -- FISH.scr:118
    do return ctx:exit("") end -- FISH.scr:120
end

script.labels["HandleObstacle"] = function(ctx)
    -- FISH.scr:123
    -- p0		- handle to obstacle
    -- p1-3	- Normal of the collision...
    -- For now, just go the exact opposite direction of the collision!
    ctx:getParam(1, "g_rotX") -- FISH.scr:132
    ctx:getParam(2, "g_rotY") -- FISH.scr:133
    ctx:getParam(3, "g_rotZ") -- FISH.scr:134
    ctx:self():faceDir("g_rotX", "g_rotY", "g_rotZ", 90, "Tick") -- FISH.scr:136
    ctx:self():walk() -- FISH.scr:137
    do return ctx:exit("TRUE") end -- FISH.scr:139
end

script.labels["HandleStuck"] = function(ctx)
    -- FISH.scr:142
    mm9.gosub(script, ctx, "Tick") -- FISH.scr:145
    do return ctx:exit("TRUE") end -- FISH.scr:147
end

script.labels["Main"] = function(ctx)
    -- FISH.scr:149
    ctx:onEvent("OnObstacle", "HandleObstacle") -- FISH.scr:152
    ctx:onEvent("OnStuck", "HandleStuck") -- FISH.scr:153
    ctx:addTrigger("Test", "OnTest") -- FISH.scr:154
    ctx:wait(0, 0.5, "Init") -- FISH.scr:156
    -- TraceON
    do return ctx:exit("") end -- FISH.scr:160
end

return script
