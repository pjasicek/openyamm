-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLE_SEAMON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseSwim.Inc" }

-- Isle_SeaMon.scr
-- Jeff Leggett
-- 12/07/2001
-- Sea Monster found in isle of ashes...
script.labels["SetupTarget"] = function(ctx)
    -- ISLE_SEAMON.scr:22
    -- Have to handle if we're going after someone...
    ctx:self():setStat("AllowRotateY", "FALSE") -- ISLE_SEAMON.scr:27
    ctx:self():setStat("FaceVelocity", "FALSE") -- ISLE_SEAMON.scr:28
    mm9.gosub(script, ctx, "SetupTarget") -- ISLE_SEAMON.scr:29
    mm9.gosub(script, ctx, "CheckForPlayerStop") -- ISLE_SEAMON.scr:30
    do return ctx:exit("") end -- ISLE_SEAMON.scr:31
end

script.labels["ClearTarget"] = function(ctx)
    -- ISLE_SEAMON.scr:34
    -- Have to handle if we're finished going after someone...
    mm9.gosub(script, ctx, "ClearTarget") -- ISLE_SEAMON.scr:39
    mm9.gosub(script, ctx, "CheckForPlayerStart") -- ISLE_SEAMON.scr:40
    ctx:self():setStat("AllowRotateY", "TRUE") -- ISLE_SEAMON.scr:42
    ctx:self():setStat("FaceVelocity", "TRUE") -- ISLE_SEAMON.scr:43
    do return ctx:exit("") end -- ISLE_SEAMON.scr:44
end

script.labels["Pause"] = function(ctx)
    -- ISLE_SEAMON.scr:47
    ctx:self():stop() -- ISLE_SEAMON.scr:50
    ctx:state().g_bPaused = true -- ISLE_SEAMON.scr:51
    mm9.gosub(script, ctx, "DisableWandering") -- ISLE_SEAMON.scr:52
    do return ctx:exit("") end -- ISLE_SEAMON.scr:53
end

script.labels["EndPause"] = function(ctx)
    -- ISLE_SEAMON.scr:56
    ctx:state().g_bPaused = false -- ISLE_SEAMON.scr:59
    mm9.gosub(script, ctx, "EnableWandering") -- ISLE_SEAMON.scr:60
    do return ctx:exit("") end -- ISLE_SEAMON.scr:61
end

script.labels["CheckForPlayerTick"] = function(ctx)
    -- ISLE_SEAMON.scr:64
    ctx:wait("PLAYER_CHECK_WAIT", "PLAYER_CHECK_INTERVAL", "CheckForPlayerTick") -- ISLE_SEAMON.scr:66
    ctx:state().g_hObject = ctx:player() -- ISLE_SEAMON.scr:68
    ctx:state().g_nDist1 = ctx:self():aiDistanceTo(ctx:object("g_hObject")) -- ISLE_SEAMON.scr:70
    if ctx:condition("g_bPaused==TRUE") then -- ISLE_SEAMON.scr:72
        if ctx:condition("g_nDist1 < MAX_WANDER_FROM_PLAYER_DIST") then -- ISLE_SEAMON.scr:73
            mm9.gosub(script, ctx, "EndPause") -- ISLE_SEAMON.scr:74
        end -- ISLE_SEAMON.scr:75
    else -- ISLE_SEAMON.scr:76
        if ctx:condition("g_nDist1 >=MAX_WANDER_FROM_PLAYER_DIST") then -- ISLE_SEAMON.scr:77
            mm9.gosub(script, ctx, "Pause") -- ISLE_SEAMON.scr:78
        end -- ISLE_SEAMON.scr:79
    end -- ISLE_SEAMON.scr:80
    do return ctx:exit("") end -- ISLE_SEAMON.scr:82
end

script.labels["CheckForPlayerStart"] = function(ctx)
    -- ISLE_SEAMON.scr:85
    ctx:wait("PLAYER_CHECK_WAIT", "PLAYER_CHECK_INTERVAL", "CheckForPlayerTick") -- ISLE_SEAMON.scr:87
    do return ctx:exit("") end -- ISLE_SEAMON.scr:88
end

script.labels["CheckForPlayerStop"] = function(ctx)
    -- ISLE_SEAMON.scr:91
    ctx:wait("PLAYER_CHECK_WAIT", 0, "DoNothing") -- ISLE_SEAMON.scr:93
    ctx:state().g_bPaused = false -- ISLE_SEAMON.scr:94
    do return ctx:exit("") end -- ISLE_SEAMON.scr:95
end

script.labels["CanReachCurrentMarker"] = function(ctx)
    -- ISLE_SEAMON.scr:98
    ctx:state().g_bTemp = true -- ISLE_SEAMON.scr:101
    do return ctx:exit("") end -- ISLE_SEAMON.scr:103
end

script.labels["SoftLanding"] = function(ctx)
    -- ISLE_SEAMON.scr:107
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:self():velocity() -- ISLE_SEAMON.scr:109
    if ctx:condition("g_velY < 0") then -- ISLE_SEAMON.scr:111
        ctx:set("g_velY", "g_velY * -1.5") -- ISLE_SEAMON.scr:112
    end -- ISLE_SEAMON.scr:113
    ctx:self():setPushBack(0, "g_velY", 0, 0.5) -- ISLE_SEAMON.scr:115
    do return ctx:exit("") end -- ISLE_SEAMON.scr:117
end

script.labels["PushForward"] = function(ctx)
    -- ISLE_SEAMON.scr:120
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:self():rotation() -- ISLE_SEAMON.scr:122
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:vecScale("g_velX", "g_velY", "g_velZ", 300) -- ISLE_SEAMON.scr:124
    ctx:state().g_velY = 0 -- ISLE_SEAMON.scr:126
    ctx:self():setPushBack("g_velX", "g_velY", "g_velZ", 1.5) -- ISLE_SEAMON.scr:128
    do return ctx:exit("") end -- ISLE_SEAMON.scr:130
end

script.labels["Jump"] = function(ctx)
    -- ISLE_SEAMON.scr:133
    ctx:self():setStat("AllowRotateY", "TRUE") -- ISLE_SEAMON.scr:135
    ctx:self():setStat("FaceVelocity", "TRUE") -- ISLE_SEAMON.scr:136
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:self():rotation() -- ISLE_SEAMON.scr:138
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:vecScale("g_velX", "g_velY", "g_velZ", 500) -- ISLE_SEAMON.scr:140
    ctx:state().g_velY = 500 -- ISLE_SEAMON.scr:141
    ctx:self():setPushBack("g_velX", "g_velY", "g_velZ", 1) -- ISLE_SEAMON.scr:143
    ctx:wait(25, 1, "PushForward") -- ISLE_SEAMON.scr:145
    -- Make sure we don't try to stop in mid-jump...
    mm9.gosub(script, ctx, "CheckForPlayerStart") -- ISLE_SEAMON.scr:148
    do return ctx:exit("") end -- ISLE_SEAMON.scr:150
end

script.labels["OnWanderAtMarker"] = function(ctx)
    -- ISLE_SEAMON.scr:154
    ctx:getParam(0, "g_hObject") -- ISLE_SEAMON.scr:157
    if ctx:condition("g_hObject!=hCurrentMarker") then -- ISLE_SEAMON.scr:158
        do return ctx:exit("") end -- ISLE_SEAMON.scr:159
    end -- ISLE_SEAMON.scr:160
    ctx:randomInt(0, 100, "g_nRandom") -- ISLE_SEAMON.scr:162
    -- 45% chance we'll jump...
    if ctx:condition("g_bFirstTime==TRUE") then -- ISLE_SEAMON.scr:168
        ctx:state().g_bFirstTime = false -- ISLE_SEAMON.scr:169
        ctx:state().g_nRandom = 0 -- ISLE_SEAMON.scr:170
    end -- ISLE_SEAMON.scr:171
    if ctx:condition("g_nRandom < 65") then -- ISLE_SEAMON.scr:173
        ctx:wait(29, 1, "Jump") -- ISLE_SEAMON.scr:174
    end -- ISLE_SEAMON.scr:175
    mm9.gosub(script, ctx, "OnWanderAtMarker") -- ISLE_SEAMON.scr:177
    do return ctx:exit("") end -- ISLE_SEAMON.scr:179
end

script.labels["Main"] = function(ctx)
    -- ISLE_SEAMON.scr:182
    -- Just use all the defaults...
    mm9.gosub(script, ctx, "BaseSwimInit") -- ISLE_SEAMON.scr:189
    mm9.gosub(script, ctx, "CheckForPlayerStart") -- ISLE_SEAMON.scr:190
    ctx:self():setStat("AllowRotateY", "TRUE") -- ISLE_SEAMON.scr:192
    ctx:self():setStat("FaceVelocity", "TRUE") -- ISLE_SEAMON.scr:193
    -- Don't want SeaMonster going to hiding places.  He may
    -- get stuck on the way and keep the GEM red.
    ctx:state().g_bUseHidingPlaces = false -- ISLE_SEAMON.scr:199
    do return ctx:exit("") end -- ISLE_SEAMON.scr:201
end

return script
