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
    ctx:self():stop() -- ANIMTEST.scr:18
    do return ctx:exit("") end -- ANIMTEST.scr:19
end

script.labels["TurnAround2"] = function(ctx)
    -- ANIMTEST.scr:21
    ctx:self():stop() -- ANIMTEST.scr:22
    ctx:wait(0, 0, "DoNothing") -- ANIMTEST.scr:23
    ctx:wait(1, 0, "DoNothing") -- ANIMTEST.scr:24
    ctx:wait(2, 0, "DoNothing") -- ANIMTEST.scr:25
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:self():rotation() -- ANIMTEST.scr:27
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:rotateDir("g_dirX", "g_dirY", "g_dirZ", 180) -- ANIMTEST.scr:28
    ctx:self():faceDir("g_dirX", "g_dirY", "g_dirZ", 180) -- ANIMTEST.scr:29
    ctx:wait(0, 1, "start2") -- ANIMTEST.scr:31
    do return ctx:exit("") end -- ANIMTEST.scr:33
end

script.labels["DoAttack2"] = function(ctx)
    -- ANIMTEST.scr:35
    if ctx:condition("g_bAttack==1") then -- ANIMTEST.scr:36
        ctx:self():attack("AttackDone2") -- ANIMTEST.scr:37
    end -- ANIMTEST.scr:38
    ctx:wait(3, 0.9, "StopAttack") -- ANIMTEST.scr:40
    do return ctx:exit("") end -- ANIMTEST.scr:41
    do return ctx:exit("") end -- ANIMTEST.scr:43
end

script.labels["start2"] = function(ctx)
    -- ANIMTEST.scr:45
    ctx:self():walk() -- ANIMTEST.scr:46
    ctx:wait(1, 1.5, "DoAttack2") -- ANIMTEST.scr:47
    ctx:wait(2, 10, "TurnAround2") -- ANIMTEST.scr:48
    do return ctx:exit("") end -- ANIMTEST.scr:49
end

script.labels["WalkAgain"] = function(ctx)
    -- ANIMTEST.scr:51
    ctx:wait(1, 0.5, "DoAttack2") -- ANIMTEST.scr:52
    ctx:self():walk() -- ANIMTEST.scr:53
    do return ctx:exit("") end -- ANIMTEST.scr:54
end

script.labels["AttackDone2"] = function(ctx)
    -- ANIMTEST.scr:56
    ctx:wait(1, 1, "WalkAgain") -- ANIMTEST.scr:57
    do return ctx:exit("true") end -- ANIMTEST.scr:58
    do return ctx:exit("") end -- ANIMTEST.scr:60
end

script.labels["TurnAround"] = function(ctx)
    -- ANIMTEST.scr:62
    ctx:self():stop() -- ANIMTEST.scr:63
    ctx:wait(0, 0, "DoNothing") -- ANIMTEST.scr:64
    ctx:wait(1, 0, "DoNothing") -- ANIMTEST.scr:65
    ctx:wait(2, 0, "DoNothing") -- ANIMTEST.scr:66
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:self():rotation() -- ANIMTEST.scr:68
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:rotateDir("g_dirX", "g_dirY", "g_dirZ", 180) -- ANIMTEST.scr:69
    ctx:self():faceDir("g_dirX", "g_dirY", "g_dirZ", 180) -- ANIMTEST.scr:70
    ctx:wait(0, 1.1, "start") -- ANIMTEST.scr:72
    do return ctx:exit("") end -- ANIMTEST.scr:73
end

script.labels["AttackDone"] = function(ctx)
    -- ANIMTEST.scr:75
    ctx:wait(1, 0.5, "DoAttack") -- ANIMTEST.scr:76
    do return ctx:exit("true") end -- ANIMTEST.scr:77
end

script.labels["BlendDone"] = function(ctx)
    -- ANIMTEST.scr:79
    ctx:wait(1, 0.5, "DoAttack") -- ANIMTEST.scr:80
    do return ctx:exit("TRUE") end -- ANIMTEST.scr:81
end

script.labels["DoAttack"] = function(ctx)
    -- ANIMTEST.scr:83
    if ctx:condition("g_bAttack==1") then -- ANIMTEST.scr:84
        ctx:self():attack("AttackDone") -- ANIMTEST.scr:85
        -- BlendAnim Aware, BlendDone
    end -- ANIMTEST.scr:87
    do return ctx:exit("") end -- ANIMTEST.scr:88
end

script.labels["start"] = function(ctx)
    -- ANIMTEST.scr:91
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:self():rotation() -- ANIMTEST.scr:92
    -- RotateDir g_dirX, g_dirY, g_dirZ, 180
    -- Strafe g_dirX, g_dirY, g_dirZ, FALSE
    ctx:self():walk() -- ANIMTEST.scr:95
    ctx:wait(1, 2.0, "DoAttack") -- ANIMTEST.scr:96
    ctx:wait(2, 6, "TurnAround") -- ANIMTEST.scr:97
    ctx:self():setStat("RunVel", 100) -- ANIMTEST.scr:99
    ctx:self():setStat("WalkVel", 100) -- ANIMTEST.scr:100
    do return ctx:exit("") end -- ANIMTEST.scr:102
end

script.labels["SpawnTest"] = function(ctx)
    -- ANIMTEST.scr:104
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- ANIMTEST.scr:105
    ctx:state().g_posY = (tonumber(ctx:state().g_posY) or 0) + 100 -- ANIMTEST.scr:106
    -- Spawn g_hObject,g_posX,g_posY,g_posZ,WealthyTownGuard1 ScriptName base.scr
    do return ctx:exit("") end -- ANIMTEST.scr:108
end

script.labels["BD_DoorOpen"] = function(ctx)
    -- ANIMTEST.scr:111
    mm9.gosub(script, ctx, "BD_DoorOpen") -- ANIMTEST.scr:112
    ctx:wait(2, 3, "TurnAround") -- ANIMTEST.scr:113
    do return ctx:exit("") end -- ANIMTEST.scr:115
end

script.labels["BD_OnDoor"] = function(ctx)
    -- ANIMTEST.scr:117
    ctx:wait(0, 0, "DoNothing") -- ANIMTEST.scr:119
    ctx:wait(1, 0, "DoNothing") -- ANIMTEST.scr:120
    ctx:wait(2, 0, "DoNothing") -- ANIMTEST.scr:121
    mm9.gosub(script, ctx, "BD_OnDoor") -- ANIMTEST.scr:123
    do return ctx:exit("TRUE") end -- ANIMTEST.scr:125
end

script.labels["JitterTest2"] = function(ctx)
    -- ANIMTEST.scr:127
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():rotation() -- ANIMTEST.scr:128
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:rotateDir("g_posX", "g_posY", "g_posZ", 180) -- ANIMTEST.scr:129
    -- Strafe g_posX,0,g_posZ,FALSE
    ctx:self():loopAnimation("backpedal", 0) -- ANIMTEST.scr:131
    ctx:cprint("backpedal") -- ANIMTEST.scr:132
    ctx:wait(0, 1.4, "Jittertest1") -- ANIMTEST.scr:134
    do return ctx:exit("") end -- ANIMTEST.scr:135
end

script.labels["JitterAttackDone"] = function(ctx)
    -- ANIMTEST.scr:137
    do return ctx:exit("TRUE") end -- ANIMTEST.scr:138
end

script.labels["JitterAttack"] = function(ctx)
    -- ANIMTEST.scr:140
    ctx:wait(1, 0.2, "JitterAttack") -- ANIMTEST.scr:141
    ctx:state().g_bTemp = ctx:self():canAttack() -- ANIMTEST.scr:142
    if ctx:condition("g_bTemp==TRUE") then -- ANIMTEST.scr:143
        ctx:self():attack("JitterAttackDone") -- ANIMTEST.scr:144
    end -- ANIMTEST.scr:145
    do return ctx:exit("") end -- ANIMTEST.scr:146
end

script.labels["JitterTest1"] = function(ctx)
    -- ANIMTEST.scr:148
    -- Stop
    -- Walk
    ctx:self():loopAnimation("Walk", 0) -- ANIMTEST.scr:152
    ctx:cprint("Walk") -- ANIMTEST.scr:153
    ctx:wait(0, 1.4, "JitterTest2") -- ANIMTEST.scr:155
    do return ctx:exit("") end -- ANIMTEST.scr:156
end

script.labels["BlendTest"] = function(ctx)
    -- ANIMTEST.scr:158
    ctx:self():blendAnimation("hAttack1") -- ANIMTEST.scr:159
    ctx:wait(8, 3, "BlendTest") -- ANIMTEST.scr:160
    do return ctx:exit("") end -- ANIMTEST.scr:161
end

script.labels["BlendTestDone"] = function(ctx)
    -- ANIMTEST.scr:163
    ctx:wait(5, 2, "BlendTest") -- ANIMTEST.scr:164
    do return ctx:exit("") end -- ANIMTEST.scr:165
end

script.labels["Switch"] = function(ctx)
    -- ANIMTEST.scr:167
    -- SetModelFilenames models\\Terror.abc,sNULL
    do return ctx:exit("") end -- ANIMTEST.scr:169
end

script.labels["TestPos"] = function(ctx)
    -- ANIMTEST.scr:171
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- ANIMTEST.scr:172
    ctx:set("g_posY", "g_posY + 120") -- ANIMTEST.scr:173
    ctx:self():setPos("g_posX", "g_posY", "g_posZ") -- ANIMTEST.scr:174
    ctx:wait(1, 1, "TestPos") -- ANIMTEST.scr:175
    do return ctx:exit("") end -- ANIMTEST.scr:176
end

script.labels["Dowalk"] = function(ctx)
    -- ANIMTEST.scr:178
    ctx:self():walk() -- ANIMTEST.scr:179
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
    ctx:self():setTarget(ctx:object("g_hTarget")) -- ANIMTEST.scr:201
    do return ctx:exit("") end -- ANIMTEST.scr:202
end

script.labels["animTest2"] = function(ctx)
    -- ANIMTEST.scr:204
    ctx:self():playAnimation("hAttack1") -- ANIMTEST.scr:205
    ctx:wait(1, 0.5, "animTest") -- ANIMTEST.scr:206
    do return ctx:exit("") end -- ANIMTEST.scr:207
end

script.labels["animtest"] = function(ctx)
    -- ANIMTEST.scr:209
    ctx:wait(1, 2, "animTest2") -- ANIMTEST.scr:210
    ctx:self():setAnimationPlaying("FALSE") -- ANIMTEST.scr:211
    do return ctx:exit("") end -- ANIMTEST.scr:212
end

script.labels["animplaytest"] = function(ctx)
    -- ANIMTEST.scr:214
    ctx:self():playAnimation("hAttack1") -- ANIMTEST.scr:215
    ctx:wait(1, 1, "animtest") -- ANIMTEST.scr:216
    do return ctx:exit("") end -- ANIMTEST.scr:218
end

script.labels["Main"] = function(ctx)
    -- ANIMTEST.scr:220
    ctx:wait(1, 0.1, "animplaytest") -- ANIMTEST.scr:222
    do return ctx:exit("") end -- ANIMTEST.scr:224
    ctx:onEvent("OnFoundTarget", "OnFoundTarget") -- ANIMTEST.scr:226
    ctx:wait(1, 2, "TestPos") -- ANIMTEST.scr:228
    ctx:wait(0, 1, "dowalk") -- ANIMTEST.scr:229
    ctx:onEvent("OnLostTarget", "OnLostTarget") -- ANIMTEST.scr:231
    do return ctx:exit("") end -- ANIMTEST.scr:233
    ctx:wait(22, 5, "Switch") -- ANIMTEST.scr:235
    -- gosub JitterTest1
    -- Wait 1, 0.2, JitterAttack
    -- exit
    ctx:state().g_nTemp = 1 -- ANIMTEST.scr:241
    -- gosub BlendTest
    mm9.gosub(script, ctx, "JitterTest1") -- ANIMTEST.scr:243
    do return ctx:exit("") end -- ANIMTEST.scr:244
    ctx:wait(0, 3, "start") -- ANIMTEST.scr:246
    mm9.gosub(script, ctx, "BaseDoorInit") -- ANIMTEST.scr:248
    ctx:getParam(0, "g_bAttack") -- ANIMTEST.scr:250
    ctx:state().g_bAttack = 1 -- ANIMTEST.scr:252
    ctx:wait(5, 5, "SpawnTest") -- ANIMTEST.scr:254
    ctx:state().g_posX = 1995 -- ANIMTEST.scr:256
    ctx:set("sTemp", "The_value_of_g_posX= + g_posX") -- ANIMTEST.scr:258
    ctx:debugOut("sTemp") -- ANIMTEST.scr:259
    ctx:set("g_hTarget", "g_hMyObject") -- ANIMTEST.scr:261
    do return ctx:exit("") end -- ANIMTEST.scr:264
end

return script
