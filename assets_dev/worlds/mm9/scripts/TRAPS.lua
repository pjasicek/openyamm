-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRAPS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- traps.scr
-- John Machin
-- This script will handle certain trap
-- types.
-- Spike Trap Vars
script.labels["TrapsSpike"] = function(ctx)
    -- TRAPS.scr:24
    if ctx:condition("g_bMoving == TRUE") then -- TRAPS.scr:26
        do return ctx:exit("") end -- TRAPS.scr:27
    end -- TRAPS.scr:28
    ctx:getParam(1, "X") -- TRAPS.scr:30
    ctx:getParam(2, "Y") -- TRAPS.scr:31
    ctx:getParam(3, "Z") -- TRAPS.scr:32
    ctx:getParam(4, "g_nDist") -- TRAPS.scr:33
    ctx:getParam(5, "g_nRate") -- TRAPS.scr:34
    ctx:getParam(6, "g_nReturnRate") -- TRAPS.scr:35
    ctx:getParam(7, "g_nTrapRecycle") -- TRAPS.scr:36
    ctx:playSound("sounds\\gibs\\GIB_IMPACT1.WAV") -- TRAPS.scr:38
    ctx:self():moveDir("X", "Y", "Z", "g_nDist", "g_nRate", "TrapsSpikeMoveDone") -- TRAPS.scr:39
    ctx:state().g_bMoving = true -- TRAPS.scr:41
    do return ctx:exit("") end -- TRAPS.scr:43
end

script.labels["TrapsSpikeMoveDone"] = function(ctx)
    -- TRAPS.scr:46
    -- Now move the spikes back to where they came from
    ctx:self():moveToPos("g_posX", "g_posY", "g_posZ", "g_nReturnRate", "TrapsMoveBackDone") -- TRAPS.scr:49
    do return ctx:exit("") end -- TRAPS.scr:51
end

script.labels["TrapsMoveBackDone"] = function(ctx)
    -- TRAPS.scr:54
    ctx:wait("g_nTrapRecycle", "g_nTrapRecycle", "TrapsMoveWaitDone") -- TRAPS.scr:56
    do return ctx:exit("") end -- TRAPS.scr:58
end

script.labels["TrapsMoveWaitDone"] = function(ctx)
    -- TRAPS.scr:61
    ctx:state().g_bMoving = false -- TRAPS.scr:63
    do return ctx:exit("") end -- TRAPS.scr:65
end

script.labels["Main"] = function(ctx)
    -- TRAPS.scr:68
    -- First Get my objects handle
    -- Get the position of the object
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- TRAPS.scr:74
    -- Traps we currently support
    ctx:addTrigger("Spikes", "TrapsSpike") -- TRAPS.scr:77
    do return ctx:exit("") end -- TRAPS.scr:79
end

return script
