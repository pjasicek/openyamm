-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ANIMTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 2, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 3, path = "BaseDoor.inc" }

script.labels["StopAttack"] = function(ctx)
    -- ANIMTEST.scr:17
    ctx:command("stop", "") -- ANIMTEST.scr:18
    do return ctx:exit("") end -- ANIMTEST.scr:19
end

script.labels["TurnAround2"] = function(ctx)
    -- ANIMTEST.scr:21
    ctx:command("stop", "") -- ANIMTEST.scr:22
    ctx:command("wait", "0, 0, DoNothing") -- ANIMTEST.scr:23
    ctx:command("wait", "1, 0, DoNothing") -- ANIMTEST.scr:24
    ctx:command("wait", "2, 0, DoNothing") -- ANIMTEST.scr:25
    ctx:command("getfacedir", "g_hMyObject, g_dirX, g_dirY, g_dirZ") -- ANIMTEST.scr:27
    ctx:command("rotatedir", "g_dirX,g_dirY,g_dirZ,180") -- ANIMTEST.scr:28
    ctx:command("facedir", "g_dirX, g_dirY, g_dirZ, 180") -- ANIMTEST.scr:29
    ctx:command("wait", "0, 1, start2") -- ANIMTEST.scr:31
    do return ctx:exit("") end -- ANIMTEST.scr:33
end

script.labels["DoAttack2"] = function(ctx)
    -- ANIMTEST.scr:35
    if ctx:condition("g_bAttack==1") then -- ANIMTEST.scr:36
        ctx:command("attack", "AttackDone2") -- ANIMTEST.scr:37
    end -- ANIMTEST.scr:38
    ctx:command("wait", "3, 0.9, StopAttack") -- ANIMTEST.scr:40
    do return ctx:exit("") end -- ANIMTEST.scr:41
    do return ctx:exit("") end -- ANIMTEST.scr:43
end

script.labels["start2"] = function(ctx)
    -- ANIMTEST.scr:45
    ctx:command("walk", "") -- ANIMTEST.scr:46
    ctx:command("wait", "1, 1.5, DoAttack2") -- ANIMTEST.scr:47
    ctx:command("wait", "2, 10, TurnAround2") -- ANIMTEST.scr:48
    do return ctx:exit("") end -- ANIMTEST.scr:49
end

script.labels["WalkAgain"] = function(ctx)
    -- ANIMTEST.scr:51
    ctx:command("wait", "1, 0.5, DoAttack2") -- ANIMTEST.scr:52
    ctx:command("walk", "") -- ANIMTEST.scr:53
    do return ctx:exit("") end -- ANIMTEST.scr:54
end

script.labels["AttackDone2"] = function(ctx)
    -- ANIMTEST.scr:56
    ctx:command("wait", "1, 1, WalkAgain") -- ANIMTEST.scr:57
    do return ctx:exit("true") end -- ANIMTEST.scr:58
    do return ctx:exit("") end -- ANIMTEST.scr:60
end

script.labels["TurnAround"] = function(ctx)
    -- ANIMTEST.scr:62
    ctx:command("stop", "") -- ANIMTEST.scr:63
    ctx:command("wait", "0, 0, DoNothing") -- ANIMTEST.scr:64
    ctx:command("wait", "1, 0, DoNothing") -- ANIMTEST.scr:65
    ctx:command("wait", "2, 0, DoNothing") -- ANIMTEST.scr:66
    ctx:command("getfacedir", "g_hMyObject, g_dirX, g_dirY, g_dirZ") -- ANIMTEST.scr:68
    ctx:command("rotatedir", "g_dirX,g_dirY,g_dirZ,180") -- ANIMTEST.scr:69
    ctx:command("facedir", "g_dirX, g_dirY, g_dirZ, 180") -- ANIMTEST.scr:70
    ctx:command("wait", "0, 1.1, start") -- ANIMTEST.scr:72
    do return ctx:exit("") end -- ANIMTEST.scr:73
end

script.labels["AttackDone"] = function(ctx)
    -- ANIMTEST.scr:75
    ctx:command("wait", "1, 0.5, DoAttack") -- ANIMTEST.scr:76
    do return ctx:exit("true") end -- ANIMTEST.scr:77
end

script.labels["BlendDone"] = function(ctx)
    -- ANIMTEST.scr:79
    ctx:command("wait", "1, 0.5, DoAttack") -- ANIMTEST.scr:80
    do return ctx:exit("TRUE") end -- ANIMTEST.scr:81
end

script.labels["DoAttack"] = function(ctx)
    -- ANIMTEST.scr:83
    if ctx:condition("g_bAttack==1") then -- ANIMTEST.scr:84
        ctx:command("attack", "AttackDone") -- ANIMTEST.scr:85
        -- BlendAnim Aware, BlendDone
    end -- ANIMTEST.scr:87
    do return ctx:exit("") end -- ANIMTEST.scr:88
end

script.labels["start"] = function(ctx)
    -- ANIMTEST.scr:91
    ctx:command("getfacedir", "g_hMyObject, g_dirX, g_dirY, g_dirZ") -- ANIMTEST.scr:92
    -- RotateDir g_dirX, g_dirY, g_dirZ, 180
    -- Strafe g_dirX, g_dirY, g_dirZ, FALSE
    ctx:command("walk", "") -- ANIMTEST.scr:95
    ctx:command("wait", "1, 2.0, DoAttack") -- ANIMTEST.scr:96
    ctx:command("wait", "2, 6, TurnAround") -- ANIMTEST.scr:97
    ctx:command("setstat", "g_hMyObject, RunVel, 100") -- ANIMTEST.scr:99
    ctx:command("setstat", "g_hMyObject, WalkVel, 100") -- ANIMTEST.scr:100
    do return ctx:exit("") end -- ANIMTEST.scr:102
end

script.labels["SpawnTest"] = function(ctx)
    -- ANIMTEST.scr:104
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- ANIMTEST.scr:105
    ctx:command("add", "g_posY, 100") -- ANIMTEST.scr:106
    -- Spawn g_hObject,g_posX,g_posY,g_posZ,WealthyTownGuard1 ScriptName base.scr
    do return ctx:exit("") end -- ANIMTEST.scr:108
end

script.labels["BD_DoorOpen"] = function(ctx)
    -- ANIMTEST.scr:111
    mm9.gosub(script, ctx, "BD_DoorOpen") -- ANIMTEST.scr:112
    ctx:command("wait", "2, 3, TurnAround") -- ANIMTEST.scr:113
    do return ctx:exit("") end -- ANIMTEST.scr:115
end

script.labels["BD_OnDoor"] = function(ctx)
    -- ANIMTEST.scr:117
    ctx:command("wait", "0, 0, DoNothing") -- ANIMTEST.scr:119
    ctx:command("wait", "1, 0, DoNothing") -- ANIMTEST.scr:120
    ctx:command("wait", "2, 0, DoNothing") -- ANIMTEST.scr:121
    mm9.gosub(script, ctx, "BD_OnDoor") -- ANIMTEST.scr:123
    do return ctx:exit("TRUE") end -- ANIMTEST.scr:125
end

script.labels["JitterTest2"] = function(ctx)
    -- ANIMTEST.scr:127
    ctx:command("getfacedir", "g_hMyObject,g_posX,g_posY,g_posZ") -- ANIMTEST.scr:128
    ctx:command("rotatedir", "g_posX,g_posY,g_posZ,180") -- ANIMTEST.scr:129
    -- Strafe g_posX,0,g_posZ,FALSE
    ctx:command("loopanim", "backpedal,0") -- ANIMTEST.scr:131
    ctx:command("cprint", "backpedal") -- ANIMTEST.scr:132
    ctx:command("wait", "0, 1.4, Jittertest1") -- ANIMTEST.scr:134
    do return ctx:exit("") end -- ANIMTEST.scr:135
end

script.labels["JitterAttackDone"] = function(ctx)
    -- ANIMTEST.scr:137
    do return ctx:exit("TRUE") end -- ANIMTEST.scr:138
end

script.labels["JitterAttack"] = function(ctx)
    -- ANIMTEST.scr:140
    ctx:command("wait", "1, 0.2, JitterAttack") -- ANIMTEST.scr:141
    ctx:command("canattack", "g_bTemp") -- ANIMTEST.scr:142
    if ctx:condition("g_bTemp==TRUE") then -- ANIMTEST.scr:143
        ctx:command("attack", "JitterAttackDone") -- ANIMTEST.scr:144
    end -- ANIMTEST.scr:145
    do return ctx:exit("") end -- ANIMTEST.scr:146
end

script.labels["JitterTest1"] = function(ctx)
    -- ANIMTEST.scr:148
    -- Stop
    -- Walk
    ctx:command("loopanim", "Walk,0") -- ANIMTEST.scr:152
    ctx:command("cprint", "Walk") -- ANIMTEST.scr:153
    ctx:command("wait", "0, 1.4, JitterTest2") -- ANIMTEST.scr:155
    do return ctx:exit("") end -- ANIMTEST.scr:156
end

script.labels["BlendTest"] = function(ctx)
    -- ANIMTEST.scr:158
    ctx:command("blendanim", "hAttack1") -- ANIMTEST.scr:159
    ctx:command("wait", "8, 3, BlendTest") -- ANIMTEST.scr:160
    do return ctx:exit("") end -- ANIMTEST.scr:161
end

script.labels["BlendTestDone"] = function(ctx)
    -- ANIMTEST.scr:163
    ctx:command("wait", "5, 2, BlendTest") -- ANIMTEST.scr:164
    do return ctx:exit("") end -- ANIMTEST.scr:165
end

script.labels["Switch"] = function(ctx)
    -- ANIMTEST.scr:167
    -- SetModelFilenames models\\Terror.abc,sNULL
    do return ctx:exit("") end -- ANIMTEST.scr:169
end

script.labels["TestPos"] = function(ctx)
    -- ANIMTEST.scr:171
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- ANIMTEST.scr:172
    ctx:command("g_posy", "= g_posY + 120") -- ANIMTEST.scr:173
    ctx:command("setpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- ANIMTEST.scr:174
    ctx:command("wait", "1,1,TestPos") -- ANIMTEST.scr:175
    do return ctx:exit("") end -- ANIMTEST.scr:176
end

script.labels["Dowalk"] = function(ctx)
    -- ANIMTEST.scr:178
    ctx:command("walk", "") -- ANIMTEST.scr:179
    -- GetPlayerHandle g_hTarget
    -- if ( g_hTarget==NULL )
    -- cprint PLAYER HANDLE IS NULL!
    -- else
    -- cprint PLAYER HANDLE VALID!
    -- endif
    -- Target g_hTarget, FALSE
    -- OnTargetWithinDist 1000, TargetWithin1000
    do return ctx:exit("") end -- ANIMTEST.scr:188
end

script.labels["TargetWithin1000"] = function(ctx)
    -- ANIMTEST.scr:190
    -- cprint TARGET within 1000!!!!
    -- OnTargetWithinDist 1000, TargetWithin1000
    do return ctx:exit("") end -- ANIMTEST.scr:193
end

script.labels["OnLostTarget"] = function(ctx)
    -- ANIMTEST.scr:195
    do return ctx:exit("TRUE") end -- ANIMTEST.scr:197
end

script.labels["OnFoundTarget"] = function(ctx)
    -- ANIMTEST.scr:199
    ctx:getParam(0, "g_hTarget") -- ANIMTEST.scr:200
    ctx:command("target", "g_hTarget, TRUE") -- ANIMTEST.scr:201
    do return ctx:exit("") end -- ANIMTEST.scr:202
end

script.labels["animTest2"] = function(ctx)
    -- ANIMTEST.scr:204
    ctx:command("playanim", "hAttack1") -- ANIMTEST.scr:205
    ctx:command("wait", "1,0.5,animTest") -- ANIMTEST.scr:206
    do return ctx:exit("") end -- ANIMTEST.scr:207
end

script.labels["animtest"] = function(ctx)
    -- ANIMTEST.scr:209
    ctx:command("wait", "1,2,animTest2") -- ANIMTEST.scr:210
    ctx:command("setanimplaying", "FALSE") -- ANIMTEST.scr:211
    do return ctx:exit("") end -- ANIMTEST.scr:212
end

script.labels["animplaytest"] = function(ctx)
    -- ANIMTEST.scr:214
    ctx:command("playanim", "hAttack1") -- ANIMTEST.scr:215
    ctx:command("wait", "1,1,animtest") -- ANIMTEST.scr:216
    do return ctx:exit("") end -- ANIMTEST.scr:218
end

script.labels["Main"] = function(ctx)
    -- ANIMTEST.scr:220
    ctx:command("getmyhandle", "g_hMyObject") -- ANIMTEST.scr:221
    ctx:command("wait", "1,0.1,animplaytest") -- ANIMTEST.scr:222
    do return ctx:exit("") end -- ANIMTEST.scr:224
    ctx:command("onfoundtarget", "OnFoundTarget") -- ANIMTEST.scr:226
    ctx:command("wait", "1, 2, TestPos") -- ANIMTEST.scr:228
    ctx:command("wait", "0,1,dowalk") -- ANIMTEST.scr:229
    ctx:command("onlosttarget", "OnLostTarget") -- ANIMTEST.scr:231
    do return ctx:exit("") end -- ANIMTEST.scr:233
    ctx:command("wait", "22, 5, Switch") -- ANIMTEST.scr:235
    -- gosub JitterTest1
    -- Wait 1, 0.2, JitterAttack
    -- exit
    ctx:command("g_ntemp", "= 1") -- ANIMTEST.scr:241
    -- gosub BlendTest
    mm9.gosub(script, ctx, "JitterTest1") -- ANIMTEST.scr:243
    do return ctx:exit("") end -- ANIMTEST.scr:244
    ctx:command("wait", "0, 3, start") -- ANIMTEST.scr:246
    mm9.gosub(script, ctx, "BaseDoorInit") -- ANIMTEST.scr:248
    ctx:getParam(0, "g_bAttack") -- ANIMTEST.scr:250
    ctx:command("set", "g_bAttack, 1") -- ANIMTEST.scr:252
    ctx:command("wait", "5, 5, SpawnTest") -- ANIMTEST.scr:254
    ctx:command("set", "g_posX, 1995") -- ANIMTEST.scr:256
    ctx:command("stemp", "= The_value_of_g_posX= + g_posX") -- ANIMTEST.scr:258
    ctx:command("debugout", "sTemp") -- ANIMTEST.scr:259
    ctx:command("g_htarget", "= g_hMyObject") -- ANIMTEST.scr:261
    do return ctx:exit("") end -- ANIMTEST.scr:264
end

return script
