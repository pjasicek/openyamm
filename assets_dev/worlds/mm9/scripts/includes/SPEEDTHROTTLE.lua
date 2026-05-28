-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPEEDTHROTTLE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "baseTimers.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "baseEvade.inc" }

-- SpeedThrottle.inc
-- Jeff Leggett
-- Used for throttling the AI's speed
-- during attacks so that we can stick
-- with him if he's moving...
script.labels["SpeedThrottleStop"] = function(ctx)
    -- SPEEDTHROTTLE.inc:23
    ctx:command("wait", "SPEED_THROTTLE_WAIT, 0, DoNothing") -- SPEEDTHROTTLE.inc:25
    ctx:command("setstat", "g_hMyObject, RunVel, g_runVel") -- SPEEDTHROTTLE.inc:26
    ctx:command("setstat", "g_hMyObject, WalkVel, g_walkVel") -- SPEEDTHROTTLE.inc:27
    do return ctx:exit("") end -- SPEEDTHROTTLE.inc:29
end

script.labels["SpeedThrottleStart"] = function(ctx)
    -- SPEEDTHROTTLE.inc:32
    ctx:command("wait", "SPEED_THROTTLE_WAIT, 0.1, SpeedThrottleTick") -- SPEEDTHROTTLE.inc:34
    do return ctx:exit("") end -- SPEEDTHROTTLE.inc:35
end

script.labels["SpeedThrottleTick"] = function(ctx)
    -- SPEEDTHROTTLE.inc:38
    -- If we are within attack range, throttle
    -- our speed to match the targets...
    ctx:command("wait", "SPEED_THROTTLE_WAIT, 0.1, SpeedThrottleTick") -- SPEEDTHROTTLE.inc:44
    if ctx:condition("g_hTarget==NULL") then -- SPEEDTHROTTLE.inc:46
        do return ctx:exit("") end -- SPEEDTHROTTLE.inc:47
    end -- SPEEDTHROTTLE.inc:48
    ctx:command("ismoving", "g_bTemp") -- SPEEDTHROTTLE.inc:50
    if ctx:condition("g_bTemp==FALSE") then -- SPEEDTHROTTLE.inc:52
        do return ctx:exit("") end -- SPEEDTHROTTLE.inc:53
    end -- SPEEDTHROTTLE.inc:54
    ctx:command("g_throttlespeed", "= g_runVel") -- SPEEDTHROTTLE.inc:56
    ctx:command("getstat", "g_hMyObject, Lunging, g_bTemp") -- SPEEDTHROTTLE.inc:58
    if ctx:condition("g_bTemp==TRUE") then -- SPEEDTHROTTLE.inc:59
        -- We are lunging...
        ctx:command("mul", "g_throttleSpeed, 1.25") -- SPEEDTHROTTLE.inc:61
    end -- SPEEDTHROTTLE.inc:62
    ctx:command("aigetdistance", "g_hTarget, g_nDist") -- SPEEDTHROTTLE.inc:64
    ctx:command("g_ntemp", "= g_attackRange * 0.9") -- SPEEDTHROTTLE.inc:66
    if ctx:condition("g_nDist >= g_nTemp") then -- SPEEDTHROTTLE.inc:68
        ctx:command("setstat", "g_hMyObject, RunVel, g_throttleSpeed") -- SPEEDTHROTTLE.inc:69
        do return ctx:exit("") end -- SPEEDTHROTTLE.inc:70
    end -- SPEEDTHROTTLE.inc:71
    -- OK, let's do some throttling....
    ctx:command("getvelocity", "g_hTarget, g_velX, g_velY, g_velZ") -- SPEEDTHROTTLE.inc:76
    ctx:command("vecmag", "g_velX, g_velY, g_velZ, g_nTemp") -- SPEEDTHROTTLE.inc:77
    if ctx:condition("g_nTemp < 20") then -- SPEEDTHROTTLE.inc:79
        -- They aren't moving very fast, should we slow down?
        ctx:command("isattacking", "g_bTemp") -- SPEEDTHROTTLE.inc:82
        if ctx:condition("g_bTemp==TRUE") then -- SPEEDTHROTTLE.inc:84
            if ctx:condition("g_bAttackPerformed==FALSE") then -- SPEEDTHROTTLE.inc:85
                if ctx:condition("g_bStrafeAttack==TRUE") then -- SPEEDTHROTTLE.inc:86
                    if ctx:condition("g_bTemp==TRUE") then -- SPEEDTHROTTLE.inc:87
                        -- We're strafe attacking and haven't hit them yet....
                        -- Let's slow down a wee bit....
                        ctx:command("g_throttlespeed", "= g_runVel * 0.5") -- SPEEDTHROTTLE.inc:90
                        ctx:command("setstat", "g_hMyObject, RunVel, g_throttleSpeed") -- SPEEDTHROTTLE.inc:91
                        do return ctx:exit("") end -- SPEEDTHROTTLE.inc:92
                    end -- SPEEDTHROTTLE.inc:93
                end -- SPEEDTHROTTLE.inc:94
            end -- SPEEDTHROTTLE.inc:95
        end -- SPEEDTHROTTLE.inc:96
        ctx:command("setstat", "g_hMyObject, RunVel, g_runVel") -- SPEEDTHROTTLE.inc:98
        ctx:command("setstat", "g_hMyObject, WalkVel, g_walkVel") -- SPEEDTHROTTLE.inc:99
        do return ctx:exit("") end -- SPEEDTHROTTLE.inc:100
    end -- SPEEDTHROTTLE.inc:101
    ctx:command("g_throttlespeed", "= g_nTemp") -- SPEEDTHROTTLE.inc:104
    -- Get the angle they are moving...
    ctx:command("vecnorm", "g_velX, g_velY, g_velZ") -- SPEEDTHROTTLE.inc:109
    mm9.gosub(script, ctx, "BE_GetTargetDir") -- SPEEDTHROTTLE.inc:111
    ctx:command("vecangle", "g_targetDirX, 0, g_targetDirZ, g_velX, 0, g_velZ, g_nTemp") -- SPEEDTHROTTLE.inc:113
    if ctx:condition("g_nTemp < 0") then -- SPEEDTHROTTLE.inc:115
        ctx:command("mul", "g_nTemp, -1") -- SPEEDTHROTTLE.inc:116
    end -- SPEEDTHROTTLE.inc:117
    if ctx:condition("g_nTemp > 45") then -- SPEEDTHROTTLE.inc:119
        ctx:command("setstat", "g_hMyObject, RunVel, g_runVel") -- SPEEDTHROTTLE.inc:120
        ctx:command("setstat", "g_hMyObject, WalkVel, g_walkVel") -- SPEEDTHROTTLE.inc:121
        do return ctx:exit("") end -- SPEEDTHROTTLE.inc:122
    end -- SPEEDTHROTTLE.inc:123
    ctx:command("mul", "g_throttleSpeed, 0.95") -- SPEEDTHROTTLE.inc:125
    if ctx:condition("g_throttleSpeed < g_runVel") then -- SPEEDTHROTTLE.inc:127
        ctx:command("setstat", "g_hMyObject, RunVel, g_throttleSpeed") -- SPEEDTHROTTLE.inc:128
        ctx:command("setstat", "g_hMyObject, WalkVel, g_throttleSpeed") -- SPEEDTHROTTLE.inc:129
    else -- SPEEDTHROTTLE.inc:130
        ctx:command("setstat", "g_hMyObject, RunVel, g_runVel") -- SPEEDTHROTTLE.inc:131
        ctx:command("setstat", "g_hMyObject, WalkVel, g_walkVel") -- SPEEDTHROTTLE.inc:132
    end -- SPEEDTHROTTLE.inc:133
    do return ctx:exit("") end -- SPEEDTHROTTLE.inc:135
end

script.labels["SpeedThrottleInit"] = function(ctx)
    -- SPEEDTHROTTLE.inc:139
    ctx:command("getmyhandle", "g_hMyObject") -- SPEEDTHROTTLE.inc:141
    ctx:command("getstat", "g_hMyObject, RunVel, g_runVel") -- SPEEDTHROTTLE.inc:143
    ctx:command("getstat", "g_hMyObject, WalkVel, g_walkVel") -- SPEEDTHROTTLE.inc:144
    ctx:command("getstat", "g_hMyObject, AttackRange, g_attackRange") -- SPEEDTHROTTLE.inc:145
    do return ctx:exit("") end -- SPEEDTHROTTLE.inc:148
end

return script
