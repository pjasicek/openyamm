-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOTMOVE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "botGlobals.inc" }

-- BotMove.inc
-- Bot movement code... (During combat...)
-- Strafe Directions
script.labels["BM_ProjectileAvoidDone"] = function(ctx)
    -- BOTMOVE.inc:29
    ctx:command("stop", "") -- BOTMOVE.inc:33
    -- todo--> Do user callback here...
    -- OnProjectile BB_OnProjectile, 200
    do return ctx:exit("") end -- BOTMOVE.inc:37
end

script.labels["BM_AvoidProjectile"] = function(ctx)
    -- BOTMOVE.inc:40
    -- See which way it's coming and strafe
    -- away from it....
    ctx:command("getvelocity", "hProjectile, velX, velY, velZ") -- BOTMOVE.inc:47
    ctx:command("vecnorm", "velX, velY, velZ") -- BOTMOVE.inc:48
    ctx:command("set", "g_nTemp, 90") -- BOTMOVE.inc:50
    ctx:command("getrandomint", "0,1, g_nRandom") -- BOTMOVE.inc:51
    if ctx:condition("g_nRandom==1") then -- BOTMOVE.inc:53
        ctx:command("mul", "g_nTemp, -1") -- BOTMOVE.inc:54
    end -- BOTMOVE.inc:55
    ctx:command("rotatedir", "velX, velY,velZ, g_nTemp") -- BOTMOVE.inc:57
    ctx:command("facedir", "velX, velY, velZ") -- BOTMOVE.inc:59
    ctx:command("onprojectile", "") -- BOTMOVE.inc:60
    ctx:command("run", "") -- BOTMOVE.inc:61
    ctx:command("wait", "EVADE_WAIT, 0.3, BM_ProjectileAvoidDone") -- BOTMOVE.inc:62
    do return ctx:exit("") end -- BOTMOVE.inc:64
end

script.labels["BM_DoStrafe"] = function(ctx)
    -- BOTMOVE.inc:68
    -- Looks at the strafe code and then
    -- does the strafe in the correct direction
    if ctx:condition("bm_strafeLR==SD_NONE") then -- BOTMOVE.inc:74
        ctx:command("set", "dirX, 0") -- BOTMOVE.inc:75
        ctx:command("set", "dirY, 0") -- BOTMOVE.inc:76
        ctx:command("set", "dirZ, 0") -- BOTMOVE.inc:77
    else -- BOTMOVE.inc:78
        if ctx:condition("bm_strafeLR==SD_LEFT") then -- BOTMOVE.inc:79
            ctx:command("getleftdir", "dirX, dirY, dirZ") -- BOTMOVE.inc:80
        else -- BOTMOVE.inc:81
            ctx:command("getrightdir", "dirX, dirY, dirZ") -- BOTMOVE.inc:82
        end -- BOTMOVE.inc:83
    end -- BOTMOVE.inc:84
    if ctx:condition("bm_strafeFB==SD_NONE") then -- BOTMOVE.inc:86
        ctx:command("set", "bm_strafeDirX, 0") -- BOTMOVE.inc:87
        ctx:command("set", "bm_strafeDirY, 0") -- BOTMOVE.inc:88
        ctx:command("set", "bm_strafeDirZ, 0") -- BOTMOVE.inc:89
    else -- BOTMOVE.inc:90
        if ctx:condition("bm_strafeFB==SD_FORWARD") then -- BOTMOVE.inc:91
            ctx:command("getforwarddir", "bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ") -- BOTMOVE.inc:92
        else -- BOTMOVE.inc:93
            ctx:command("getreversedir", "bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ") -- BOTMOVE.inc:94
        end -- BOTMOVE.inc:95
    end -- BOTMOVE.inc:96
    ctx:command("vecadd", "bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ, dirX, dirY, dirZ") -- BOTMOVE.inc:98
    ctx:command("vecnorm", "bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ") -- BOTMOVE.inc:99
    ctx:command("strafe", "bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ, TRUE") -- BOTMOVE.inc:100
    do return ctx:exit("") end -- BOTMOVE.inc:102
end

script.labels["BM_MoveTick"] = function(ctx)
    -- BOTMOVE.inc:105
    -- See if we need to move closer or
    -- farther away from the target...
    -- Decide if we want to move forward or back...
    ctx:command("set", "bm_strafeFB, SD_NONE") -- BOTMOVE.inc:115
    if ctx:condition("g_hTarget!=NULL") then -- BOTMOVE.inc:117
        ctx:command("aigetdistance", "g_hTarget, g_nTemp") -- BOTMOVE.inc:118
        if ctx:condition("g_nTemp > 320") then -- BOTMOVE.inc:119
            ctx:command("set", "bm_strafeFB, SD_FORWARD") -- BOTMOVE.inc:120
        end -- BOTMOVE.inc:121
        if ctx:condition("g_nTemp < 140") then -- BOTMOVE.inc:123
            ctx:command("set", "bm_strafeFB, SD_BACK") -- BOTMOVE.inc:124
        end -- BOTMOVE.inc:125
    end -- BOTMOVE.inc:126
    ctx:command("wait", "EVADE_MOVE_WAIT, 0.4, BM_MoveTick") -- BOTMOVE.inc:128
    do return ctx:exit("") end -- BOTMOVE.inc:130
end

script.labels["BM_EvadeTick"] = function(ctx)
    -- BOTMOVE.inc:133
    if ctx:condition("bm_strafeLR==SD_LEFT") then -- BOTMOVE.inc:136
        ctx:command("set", "bm_strafeLR, SD_RIGHT") -- BOTMOVE.inc:137
    else -- BOTMOVE.inc:138
        if ctx:condition("bm_strafeLR==SD_RIGHT") then -- BOTMOVE.inc:139
            ctx:command("set", "bm_strafeLR, SD_LEFT") -- BOTMOVE.inc:140
        end -- BOTMOVE.inc:141
    end -- BOTMOVE.inc:142
    mm9.gosub(script, ctx, "BM_DoStrafe") -- BOTMOVE.inc:144
    ctx:command("wait", "EVADE_WAIT, 0.8, BM_EvadeTick") -- BOTMOVE.inc:146
    do return ctx:exit("") end -- BOTMOVE.inc:148
end

script.labels["BM_SetupEvade"] = function(ctx)
    -- BOTMOVE.inc:151
    -- For now, just keep strafing back and
    -- forth...
    -- SetCrouch TRUE
    ctx:command("getrandomint", "SD_LEFT,SD_RIGHT, bm_strafeLR") -- BOTMOVE.inc:159
    mm9.gosub(script, ctx, "BM_EvadeTick") -- BOTMOVE.inc:161
    mm9.gosub(script, ctx, "BM_MoveTick") -- BOTMOVE.inc:162
    do return ctx:exit("") end -- BOTMOVE.inc:164
end

script.labels["BM_CancelEvade"] = function(ctx)
    -- BOTMOVE.inc:167
    -- Just stop our wait tick...
    ctx:command("wait", "EVADE_WAIT, 0, DoNothing") -- BOTMOVE.inc:172
    do return ctx:exit("") end -- BOTMOVE.inc:174
end

return script
