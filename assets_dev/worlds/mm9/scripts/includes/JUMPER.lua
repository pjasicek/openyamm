-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "JUMPER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "AIGlobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "Flags.inc" }

-- Jumper.Inc
-- Jeff Leggett
-- 01/08/2002
-- Base script used by AI that jump off cliffs at the
-- player...
script.labels["RunNormalScript"] = function(ctx)
    -- JUMPER.inc:31
    ctx:state().g_sTemp = ctx:self():stringProperty("ScriptName") -- JUMPER.inc:33
    ctx:self():setStat("GroundTouchNotify", "FALSE") -- JUMPER.inc:34
    ctx:runScript("g_sTemp") -- JUMPER.inc:35
    do return ctx:exit("") end -- JUMPER.inc:36
end

script.labels["JumpLandHack"] = function(ctx)
    -- JUMPER.inc:39
    -- prevent the bounce?
    ctx:self():setVelocity(0, 0, 0) -- JUMPER.inc:42
    mm9.gosub(script, ctx, "RunNormalScript") -- JUMPER.inc:44
    do return ctx:exit("") end -- JUMPER.inc:46
end

script.labels["JumperHitGround"] = function(ctx)
    -- JUMPER.inc:49
    ctx:onEvent("OnTouchNotify") -- JUMPER.inc:51
    ctx:self():stop() -- JUMPER.inc:52
    ctx:self():setIdle() -- JUMPER.inc:53
    ctx:self():setPushBack("g_dirX", 0, "g_dirZ", 0) -- JUMPER.inc:54
    ctx:self():setVelocity(0, 0, 0) -- JUMPER.inc:55
    ctx:wait(22, 0.01, "JumpLandHack") -- JUMPER.inc:56
    do return ctx:exit("") end -- JUMPER.inc:58
end

script.labels["SetupTouchNotify"] = function(ctx)
    -- JUMPER.inc:61
    ctx:self():setFlag("FLAG_SOLID", true) -- JUMPER.inc:64
    ctx:self():setFlag("FLAG_GOTHRUWORLD", false) -- JUMPER.inc:65
    ctx:self():setStat("GroundTouchNotify", "TRUE") -- JUMPER.inc:67
    ctx:onEvent("OnTouchNotify", "JumperHitGround") -- JUMPER.inc:68
    do return ctx:exit("") end -- JUMPER.inc:70
end

script.labels["JumpAtTarget"] = function(ctx)
    -- JUMPER.inc:73
    ctx:self():setTarget(ctx:object("g_hTarget")) -- JUMPER.inc:76
    ctx:self():setStat("Gravity", "TRUE") -- JUMPER.inc:78
    ctx:self():playAnimSound("JumpingDown", 0) -- JUMPER.inc:80
    ctx:self():loopAnimation("JumpingDown", 0) -- JUMPER.inc:81
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:object("g_hTarget"):pos() -- JUMPER.inc:83
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- JUMPER.inc:84
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:vecSub("g_dirX", "g_dirY", "g_dirZ", "g_posX", "g_posY", "g_posZ") -- JUMPER.inc:86
    ctx:state().g_dirY = 0 -- JUMPER.inc:87
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:vecNorm("g_dirX", "g_dirY", "g_dirZ") -- JUMPER.inc:88
    ctx:state().faceX, ctx:state().faceY, ctx:state().faceZ = ctx:self():rotation() -- JUMPER.inc:90
    ctx:state().faceY = 0 -- JUMPER.inc:92
    ctx:state().g_nTemp = ctx:vecAngle("g_dirX", "g_dirY", "g_dirZ", "faceX", "faceY", "faceZ") -- JUMPER.inc:94
    if ctx:condition("g_nTemp < 0") then -- JUMPER.inc:96
        ctx:set("g_nTemp", "g_nTemp * -1") -- JUMPER.inc:97
    end -- JUMPER.inc:98
    -- if angle is too far, just jump in forward direction...
    if ctx:condition("g_nTemp > 45") then -- JUMPER.inc:101
        ctx:set("g_dirX", "faceX") -- JUMPER.inc:102
        ctx:set("g_dirZ", "faceZ") -- JUMPER.inc:103
    end -- JUMPER.inc:104
    ctx:self():setVelocity(0, 100, 0) -- JUMPER.inc:106
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:vecScale("g_dirX", "g_dirY", "g_dirZ", 250) -- JUMPER.inc:108
    ctx:self():setPushBack("g_dirX", "g_dirY", "g_dirZ", 2) -- JUMPER.inc:110
    ctx:wait(28, 0.2, "SetupTouchNotify") -- JUMPER.inc:112
    do return ctx:exit("") end -- JUMPER.inc:116
end

script.labels["ReadyToJump"] = function(ctx)
    -- JUMPER.inc:120
    ctx:wait(23, 1, "JumpAtTarget") -- JUMPER.inc:122
    -- gosub JumpAtTarget
    do return ctx:exit("") end -- JUMPER.inc:124
end

script.labels["JumperGetPlayer"] = function(ctx)
    -- JUMPER.inc:129
    -- Cancel our wait... (just in case)
    ctx:wait(9, 0, "DoNothing") -- JUMPER.inc:134
    ctx:state().g_hTarget = ctx:player() -- JUMPER.inc:136
    ctx:self():setFlag("FLAG_VISIBLE", true) -- JUMPER.inc:138
    ctx:self():loopAnimation("LyingDown", 0) -- JUMPER.inc:140
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:self():rotation() -- JUMPER.inc:142
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:vecScale("g_dirX", "g_dirY", "g_dirZ", 60) -- JUMPER.inc:144
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:vecAdd("g_dirX", "g_dirY", "g_dirZ", "startX", "startY", "startZ") -- JUMPER.inc:146
    ctx:self():moveToPos("g_dirX", "g_dirY", "g_dirZ", 50, "ReadyToJump") -- JUMPER.inc:147
    ctx:playSound("Sounds\\Events\\rubble.wav", "DoNothing", 1000, 2000) -- JUMPER.inc:149
    ctx:removeTrigger("BuddyDead") -- JUMPER.inc:151
    do return ctx:exit("") end -- JUMPER.inc:153
end

script.labels["ResetJumper"] = function(ctx)
    -- JUMPER.inc:157
    ctx:self():setStat("Gravity", "FALSE") -- JUMPER.inc:159
    ctx:self():setFlag("FLAG_SOLID", false) -- JUMPER.inc:160
    ctx:self():setFlag("FLAG_VISIBLE", false) -- JUMPER.inc:161
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- JUMPER.inc:162
    -- if ( sMyName==Jumper0 )
    -- startX		= -1700
    -- startY		= 1646
    -- startZ		= -151
    -- endif
    -- if ( sMyName==Jumper1 )
    -- startX		= -583
    -- startY		= 1760
    -- startZ		= -29
    -- endif
    ctx:self():setPos("startX", "startY", "startZ") -- JUMPER.inc:176
    ctx:self():loopAnimation("LyingDown", 0) -- JUMPER.inc:177
    do return ctx:exit("") end -- JUMPER.inc:179
end

script.labels["JumperWaitGetPlayer"] = function(ctx)
    -- JUMPER.inc:183
    ctx:randomFloat("minWait", "maxWait", "g_nRandom") -- JUMPER.inc:186
    ctx:wait(9, "g_nRandom", "JumperGetPlayer") -- JUMPER.inc:188
    do return ctx:exit("") end -- JUMPER.inc:190
end

script.labels["JumperSetupPos"] = function(ctx)
    -- JUMPER.inc:193
    ctx:state().startX, ctx:state().startY, ctx:state().startZ = ctx:self():pos() -- JUMPER.inc:196
    do return ctx:exit("") end -- JUMPER.inc:198
end

script.labels["SetupJumper"] = function(ctx)
    -- JUMPER.inc:201
    ctx:self():setStat("Gravity", "FALSE") -- JUMPER.inc:206
    ctx:self():setFlag("FLAG_SOLID", false) -- JUMPER.inc:207
    ctx:self():setFlag("FLAG_VISIBLE", false) -- JUMPER.inc:208
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- JUMPER.inc:209
    ctx:wait(29, 0.1, "ResetJumper") -- JUMPER.inc:211
    ctx:wait(28, 0.1, "JumperSetupPos") -- JUMPER.inc:212
    ctx:addTrigger("Reset", "ResetJumper") -- JUMPER.inc:214
    ctx:addTrigger("Jump", "JumperGetPlayer") -- JUMPER.inc:215
    ctx:addTrigger("GetPlayer", "JumperGetPlayer") -- JUMPER.inc:216
    ctx:addTrigger("BuddyDead", "JumperGetPlayer") -- JUMPER.inc:217
    ctx:addTrigger("WaitGetPlayer", "JumperWaitGetPlayer") -- JUMPER.inc:218
    ctx:cacheSound("sRubbleSound") -- JUMPER.inc:220
    do return ctx:exit("") end -- JUMPER.inc:222
end

return script
