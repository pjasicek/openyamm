-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOTEVADE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "botbase.inc" }

-- BotEvade.inc
-- Evasive maneuver functions...
-- Note:
-- Include BotGlobals.Inc prior to this inc file.
script.labels["BE_ProjectileAvoidDone"] = function(ctx)
    -- BOTEVADE.inc:13
    ctx:command("stop", "") -- BOTEVADE.inc:18
    ctx:command("onprojectile", "BB_OnProjectile, 200") -- BOTEVADE.inc:19
    do return ctx:exit("") end -- BOTEVADE.inc:21
end

script.labels["BE_AvoidProjectile"] = function(ctx)
    -- BOTEVADE.inc:24
    -- See which way it's coming and strafe
    -- away from it....
    ctx:command("getvelocity", "hProjectile, velX, velY, velZ") -- BOTEVADE.inc:31
    ctx:command("vecnorm", "velX, velY, velZ") -- BOTEVADE.inc:32
    ctx:command("set", "g_nTemp, 90") -- BOTEVADE.inc:34
    ctx:command("getrandomint", "0,1, g_nRandom") -- BOTEVADE.inc:35
    if ctx:condition("g_nRandom==1") then -- BOTEVADE.inc:37
        ctx:command("mul", "g_nTemp, -1") -- BOTEVADE.inc:38
    end -- BOTEVADE.inc:39
    ctx:command("rotatedir", "velX, velY,velZ, g_nTemp") -- BOTEVADE.inc:41
    ctx:command("facedir", "velX, velY, velZ") -- BOTEVADE.inc:43
    ctx:command("onprojectile", "") -- BOTEVADE.inc:44
    ctx:command("run", "") -- BOTEVADE.inc:45
    ctx:command("wait", "EVADE_WAIT, 0.3, BE_ProjectileAvoidDone") -- BOTEVADE.inc:46
    do return ctx:exit("") end -- BOTEVADE.inc:48
end

script.labels["BE_StrafeRight"] = function(ctx)
    -- BOTEVADE.inc:52
    ctx:command("getrightdir", "dirX, dirY, dirZ") -- BOTEVADE.inc:54
    ctx:command("strafe", "dirX, dirY, dirZ, TRUE") -- BOTEVADE.inc:55
    ctx:command("wait", "EVADE_WAIT, 0.8, BE_EvadeRightTick") -- BOTEVADE.inc:56
    do return ctx:exit("") end -- BOTEVADE.inc:58
end

script.labels["BE_StrafeLeft"] = function(ctx)
    -- BOTEVADE.inc:61
    ctx:command("getleftdir", "dirX, dirY, dirZ") -- BOTEVADE.inc:63
    ctx:command("strafe", "dirX, dirY, dirZ, TRUE") -- BOTEVADE.inc:64
    ctx:command("wait", "EVADE_WAIT, 0.8, BE_EvadeLeftTick") -- BOTEVADE.inc:65
    do return ctx:exit("") end -- BOTEVADE.inc:67
end

script.labels["BE_EvadeRightTick"] = function(ctx)
    -- BOTEVADE.inc:70
    mm9.gosub(script, ctx, "BE_StrafeLeft") -- BOTEVADE.inc:72
    do return ctx:exit("") end -- BOTEVADE.inc:73
end

script.labels["BE_EvadeLeftTick"] = function(ctx)
    -- BOTEVADE.inc:76
    mm9.gosub(script, ctx, "BE_StrafeRight") -- BOTEVADE.inc:79
    do return ctx:exit("") end -- BOTEVADE.inc:81
end

script.labels["BE_SetupEvade"] = function(ctx)
    -- BOTEVADE.inc:84
    -- For now, just keep strafing back and
    -- forth...
    -- SetCrouch TRUE
    mm9.gosub(script, ctx, "BE_StrafeLeft") -- BOTEVADE.inc:91
    do return ctx:exit("") end -- BOTEVADE.inc:93
end

script.labels["BE_CancelEvade"] = function(ctx)
    -- BOTEVADE.inc:96
    -- Just stop our wait tick...
    ctx:command("wait", "EVADE_WAIT, 0, DoNothing") -- BOTEVADE.inc:101
    do return ctx:exit("") end -- BOTEVADE.inc:103
end

return script
