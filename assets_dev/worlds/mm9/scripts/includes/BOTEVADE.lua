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
    ctx:self():stop() -- BOTEVADE.inc:18
    ctx:onEvent("OnProjectile", "BB_OnProjectile") -- BOTEVADE.inc:19
    do return ctx:exit("") end -- BOTEVADE.inc:21
end

script.labels["BE_AvoidProjectile"] = function(ctx)
    -- BOTEVADE.inc:24
    -- See which way it's coming and strafe
    -- away from it....
    ctx:state().velX, ctx:state().velY, ctx:state().velZ = ctx:object("hProjectile"):velocity() -- BOTEVADE.inc:31
    ctx:state().velX, ctx:state().velY, ctx:state().velZ = ctx:vecNorm("velX", "velY", "velZ") -- BOTEVADE.inc:32
    ctx:state().g_nTemp = 90 -- BOTEVADE.inc:34
    ctx:randomInt(0, 1, "g_nRandom") -- BOTEVADE.inc:35
    if ctx:condition("g_nRandom==1") then -- BOTEVADE.inc:37
        ctx:state().g_nTemp = (tonumber(ctx:state().g_nTemp) or 0) * -1 -- BOTEVADE.inc:38
    end -- BOTEVADE.inc:39
    ctx:state().velX, ctx:state().velY, ctx:state().velZ = ctx:rotateDir("velX", "velY", "velZ", "g_nTemp") -- BOTEVADE.inc:41
    ctx:self():faceDir("velX", "velY", "velZ") -- BOTEVADE.inc:43
    ctx:onEvent("OnProjectile") -- BOTEVADE.inc:44
    ctx:self():run() -- BOTEVADE.inc:45
    ctx:wait("EVADE_WAIT", 0.3, "BE_ProjectileAvoidDone") -- BOTEVADE.inc:46
    do return ctx:exit("") end -- BOTEVADE.inc:48
end

script.labels["BE_StrafeRight"] = function(ctx)
    -- BOTEVADE.inc:52
    ctx:state().dirX, ctx:state().dirY, ctx:state().dirZ = ctx:self():rightDir() -- BOTEVADE.inc:54
    ctx:self():strafe("dirX", "dirY", "dirZ", "TRUE") -- BOTEVADE.inc:55
    ctx:wait("EVADE_WAIT", 0.8, "BE_EvadeRightTick") -- BOTEVADE.inc:56
    do return ctx:exit("") end -- BOTEVADE.inc:58
end

script.labels["BE_StrafeLeft"] = function(ctx)
    -- BOTEVADE.inc:61
    ctx:state().dirX, ctx:state().dirY, ctx:state().dirZ = ctx:self():leftDir() -- BOTEVADE.inc:63
    ctx:self():strafe("dirX", "dirY", "dirZ", "TRUE") -- BOTEVADE.inc:64
    ctx:wait("EVADE_WAIT", 0.8, "BE_EvadeLeftTick") -- BOTEVADE.inc:65
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
    ctx:wait("EVADE_WAIT", 0, "DoNothing") -- BOTEVADE.inc:101
    do return ctx:exit("") end -- BOTEVADE.inc:103
end

return script
