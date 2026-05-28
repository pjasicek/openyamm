-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HEN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "wander.inc" }

-- hen.scr
-- John Machin
-- Default script for wanderers
script.labels["OnSpecial"] = function(ctx)
    -- HEN.scr:24
    ctx:command("getrandomint", "1, 10, g_nRandom") -- HEN.scr:26
    if ctx:condition("g_nRandom < 8") then -- HEN.scr:27
        ctx:command("playanim", "Fidget2, OnPeck1Done") -- HEN.scr:28
    else -- HEN.scr:29
        ctx:command("getrandomint", "5, 15, g_nRandom") -- HEN.scr:30
        ctx:command("loopanim", "sit, g_nRandom, OnSpecialDone") -- HEN.scr:31
        ctx:command("set", "g_bIsSitting, TRUE") -- HEN.scr:32
    end -- HEN.scr:33
    ctx:command("wait", "0, 0, DoNothing") -- HEN.scr:35
    do return ctx:exit("") end -- HEN.scr:37
end

script.labels["OnPeck1Done"] = function(ctx)
    -- HEN.scr:40
    ctx:command("playanim", "Fidget2, OnPeck2Done") -- HEN.scr:42
    do return ctx:exit("") end -- HEN.scr:44
end

script.labels["OnPeck2Done"] = function(ctx)
    -- HEN.scr:47
    ctx:command("playanim", "Fidget3, OnPeck3Done") -- HEN.scr:49
    do return ctx:exit("") end -- HEN.scr:51
end

script.labels["OnPeck3Done"] = function(ctx)
    -- HEN.scr:54
    ctx:command("playanim", "Fidget2") -- HEN.scr:56
    ctx:command("wait", "0, 2, WanderTick") -- HEN.scr:58
    do return ctx:exit("") end -- HEN.scr:60
end

script.labels["OnSpecialDone"] = function(ctx)
    -- HEN.scr:64
    -- Were done startup the ticker again...
    ctx:command("set", "g_bIsSitting, FALSE") -- HEN.scr:67
    mm9.gosub(script, ctx, "WanderTick") -- HEN.scr:68
    do return ctx:exit("") end -- HEN.scr:70
end

script.labels["DoNothing"] = function(ctx)
    -- HEN.scr:73
    -- Do nothing here...
    do return ctx:exit("") end -- HEN.scr:77
end

script.labels["OnRun"] = function(ctx)
    -- HEN.scr:80
    ctx:command("getfacedir", "hAttacker, g_posX, g_posY, g_posZ") -- HEN.scr:83
    ctx:command("facedir", "g_PosX, g_PosY, g_PosZ, 180") -- HEN.scr:85
    -- This will cause a more erratic running behavior
    ctx:command("set", "g_IdleCheckMin, 1") -- HEN.scr:88
    ctx:command("set", "g_IdleCheckMax, 1") -- HEN.scr:89
    -- Set turn degree min max for more erratic movement
    ctx:command("set", "g_TurnDegreeMin, 60") -- HEN.scr:92
    ctx:command("set", "g_TurnDegreeMax, 90") -- HEN.scr:93
    ctx:command("run", "") -- HEN.scr:95
    ctx:command("set", "g_IsRunning, TRUE") -- HEN.scr:97
    do return ctx:exit("") end -- HEN.scr:99
end

script.labels["OnRunning"] = function(ctx)
    -- HEN.scr:102
    -- We want to continue sending Alerts to nearby AI while running
    ctx:command("sendalert", "hAttacker") -- HEN.scr:105
    do return ctx:exit("") end -- HEN.scr:107
end

script.labels["OnStopRunning"] = function(ctx)
    -- HEN.scr:110
    -- Setup our stuff back to normal
    ctx:command("set", "g_IdleCheckMin, 7") -- HEN.scr:113
    ctx:command("set", "g_IdleCheckMax, 7") -- HEN.scr:114
    ctx:command("set", "g_TurnDegreeMin 15") -- HEN.scr:116
    ctx:command("set", "g_TurnDegreeMax 90") -- HEN.scr:117
    ctx:command("set", "g_IsRunning, FALSE") -- HEN.scr:119
    do return ctx:exit("") end -- HEN.scr:121
end

script.labels["HenOnDamage"] = function(ctx)
    -- HEN.scr:124
    -- Figure out who hit us
    ctx:getParam(0, "hAttacker") -- HEN.scr:127
    ctx:command("getclassname", "hAttacker, sAttacker") -- HEN.scr:129
    -- Get last amount of damage done
    ctx:getParam(1, "g_nLastDamage") -- HEN.scr:132
    -- Alert nearby AI
    ctx:command("sendalert", "hAttacker") -- HEN.scr:135
    ctx:command("gettime", "g_StopRunTime") -- HEN.scr:137
    ctx:command("add", "g_StopRunTime, 15") -- HEN.scr:138
    if ctx:condition("g_nLastDamage == 0") then -- HEN.scr:140
        mm9.gosub(script, ctx, "HenOnDamageDone") -- HEN.scr:141
    end -- HEN.scr:142
    do return ctx:exit("FALSE") end -- HEN.scr:144
end

script.labels["HenOnDamageDone"] = function(ctx)
    -- HEN.scr:147
    mm9.gosub(script, ctx, "OnRun") -- HEN.scr:149
    do return ctx:exit("") end -- HEN.scr:151
end

script.labels["HenOnTouchNotify"] = function(ctx)
    -- HEN.scr:154
    -- Figure out who hit us
    ctx:getParam(0, "hTouchedBy") -- HEN.scr:157
    ctx:command("isplayer", "hTouchedBy, g_bIsPlayer") -- HEN.scr:159
    if ctx:condition("g_bIsPlayer == TRUE") then -- HEN.scr:161
        -- Get the direction player is facing
        ctx:command("getfacedir", "hTouchedBy, g_posX, g_posY, g_posZ") -- HEN.scr:163
        -- HACK randomly change the way the hen will turn
        ctx:command("getrandomfloat", "-0.30, 0.30, g_nRandom") -- HEN.scr:166
        ctx:command("add", "g_rotX, g_nRandom") -- HEN.scr:167
        ctx:command("getrandomfloat", "-0.30, 0.30, g_nRandom") -- HEN.scr:169
        ctx:command("add", "g_rotZ, g_nRandom") -- HEN.scr:170
        -- Face the modified opposite direction of player
        ctx:command("facedir", "g_posX, g_posY, g_posZ, 180") -- HEN.scr:173
        ctx:command("run", "") -- HEN.scr:175
        ctx:command("wait", "0, 2, HenOnTouchRunDone") -- HEN.scr:177
    end -- HEN.scr:179
    do return ctx:exit("") end -- HEN.scr:181
end

script.labels["HenOnTouchRunDone"] = function(ctx)
    -- HEN.scr:184
    if ctx:condition("g_bIsRunning == TRUE") then -- HEN.scr:186
        ctx:command("run", "") -- HEN.scr:187
    else -- HEN.scr:188
        ctx:command("walk", "") -- HEN.scr:189
    end -- HEN.scr:190
    do return ctx:exit("") end -- HEN.scr:192
end

script.labels["OnFeeding"] = function(ctx)
    -- HEN.scr:195
    if ctx:condition("g_IsRunning == FALSE") then -- HEN.scr:197
        ctx:getParam(0, "g_hFeeder") -- HEN.scr:198
        ctx:command("runto", "g_hFeeder, 100, OnAtFeeder") -- HEN.scr:200
    end -- HEN.scr:201
    do return ctx:exit("") end -- HEN.scr:203
end

script.labels["OnAtFeeder"] = function(ctx)
    -- HEN.scr:206
    ctx:command("setidle", "") -- HEN.scr:208
    -- Wait 0, 6, WanderTick
    do return ctx:exit("") end -- HEN.scr:212
end

script.labels["OnWalk"] = function(ctx)
    -- HEN.scr:216
    ctx:command("walk", "") -- HEN.scr:219
    do return ctx:exit("") end -- HEN.scr:221
end

script.labels["InitHen"] = function(ctx)
    -- HEN.scr:225
    -- Set the hens roaming distance
    ctx:getParam(1, "g_nDistance") -- HEN.scr:228
    if ctx:condition("g_nDistance != 0") then -- HEN.scr:230
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, g_nDistance") -- HEN.scr:231
    else -- HEN.scr:232
        ctx:command("set", "MAX_DIST_FROM_STARTPOINT, 350") -- HEN.scr:233
    end -- HEN.scr:234
    -- Set how often we stop at an obstacle
    ctx:command("set", "g_nStopAtObstacle, 2") -- HEN.scr:237
    -- Set how often hen is idle 1 equals 10% valid numbers are 1 to 10
    ctx:command("set", "g_IdleFrequency, 5") -- HEN.scr:240
    -- Set max time in seconds before idle check
    ctx:command("set", "g_IdleCheckMin, 4") -- HEN.scr:243
    ctx:command("set", "g_IdleCheckMax, 4") -- HEN.scr:244
    -- Set how often special anim is played valid numbers are 1 to 10
    ctx:command("set", "g_SpecialAnimFrequency, 8") -- HEN.scr:247
    -- Set how fast to turn around when we hit an obstacle
    ctx:command("set", "g_wanderObstacleRotRate, 180") -- HEN.scr:250
    do return ctx:exit("") end -- HEN.scr:252
end

script.labels["Main"] = function(ctx)
    -- HEN.scr:255
    -- Initialize Hen vars
    mm9.gosub(script, ctx, "InitHen") -- HEN.scr:259
    -- Monitor these callbacks
    ctx:command("ontouchnotify", "HenOnTouchNotify") -- HEN.scr:262
    ctx:command("ondamagedone", "HenOnDamageDone") -- HEN.scr:263
    ctx:command("ondamage", "HenOnDamage") -- HEN.scr:264
    -- Handle these triggers
    ctx:addTrigger("SpecialAnim", "OnSpecial") -- HEN.scr:267
    ctx:addTrigger("StopRunning", "OnStopRunning") -- HEN.scr:268
    ctx:addTrigger("Running", "OnRunning") -- HEN.scr:269
    ctx:addTrigger("Walk", "OnWalk") -- HEN.scr:270
    -- AddTrigger Feeding,		OnFeeding
    mm9.gosub(script, ctx, "WanderInit") -- HEN.scr:273
    do return ctx:exit("") end -- HEN.scr:275
end

return script
