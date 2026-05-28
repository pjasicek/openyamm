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
    ctx:command("getstatstr", "g_hMyObject,ScriptName,g_sTemp") -- JUMPER.inc:33
    ctx:command("setstat", "g_hMyObject,GroundTouchNotify,FALSE") -- JUMPER.inc:34
    ctx:command("runscript", "g_sTemp") -- JUMPER.inc:35
    do return ctx:exit("") end -- JUMPER.inc:36
end

script.labels["JumpLandHack"] = function(ctx)
    -- JUMPER.inc:39
    -- prevent the bounce?
    ctx:command("setvelocity", "g_hMyObject,0,0,0") -- JUMPER.inc:42
    mm9.gosub(script, ctx, "RunNormalScript") -- JUMPER.inc:44
    do return ctx:exit("") end -- JUMPER.inc:46
end

script.labels["JumperHitGround"] = function(ctx)
    -- JUMPER.inc:49
    ctx:command("ontouchnotify", "") -- JUMPER.inc:51
    ctx:command("stop", "") -- JUMPER.inc:52
    ctx:command("setidle", "") -- JUMPER.inc:53
    ctx:command("setpushback", "g_dirX,0,g_dirZ,0") -- JUMPER.inc:54
    ctx:command("setvelocity", "g_hMyObject,0,0,0") -- JUMPER.inc:55
    ctx:command("wait", "22,0.01,JumpLandHack") -- JUMPER.inc:56
    do return ctx:exit("") end -- JUMPER.inc:58
end

script.labels["SetupTouchNotify"] = function(ctx)
    -- JUMPER.inc:61
    ctx:command("setflag", "g_hMyObject,FLAG_SOLID") -- JUMPER.inc:64
    ctx:command("clearflag", "g_hMyObject,FLAG_GOTHRUWORLD") -- JUMPER.inc:65
    ctx:command("setstat", "g_hMyObject,GroundTouchNotify,TRUE") -- JUMPER.inc:67
    ctx:command("ontouchnotify", "JumperHitGround") -- JUMPER.inc:68
    do return ctx:exit("") end -- JUMPER.inc:70
end

script.labels["JumpAtTarget"] = function(ctx)
    -- JUMPER.inc:73
    ctx:command("target", "g_hTarget, TRUE") -- JUMPER.inc:76
    ctx:command("setstat", "g_hMyObject,Gravity,TRUE") -- JUMPER.inc:78
    ctx:command("playanimsound", "JumpingDown,0") -- JUMPER.inc:80
    ctx:command("loopanim", "JumpingDown,0") -- JUMPER.inc:81
    ctx:command("getpos", "g_hTarget,g_dirX,g_dirY,g_dirZ") -- JUMPER.inc:83
    ctx:command("getpos", "g_hMyObject,g_posX,g_posY,g_posZ") -- JUMPER.inc:84
    ctx:command("vecsub", "g_dirX,g_dirY,g_dirZ,g_posX,g_posY,g_posZ") -- JUMPER.inc:86
    ctx:command("g_diry", "= 0") -- JUMPER.inc:87
    ctx:command("vecnorm", "g_dirX,g_dirY,g_dirZ") -- JUMPER.inc:88
    ctx:command("getfacedir", "g_hMyObject,faceX,faceY,faceZ") -- JUMPER.inc:90
    ctx:command("facey", "= 0") -- JUMPER.inc:92
    ctx:command("vecangle", "g_dirX,g_dirY,g_dirZ,faceX,faceY,faceZ,g_nTemp") -- JUMPER.inc:94
    if ctx:condition("g_nTemp < 0") then -- JUMPER.inc:96
        ctx:command("g_ntemp", "= g_nTemp * -1") -- JUMPER.inc:97
    end -- JUMPER.inc:98
    -- if angle is too far, just jump in forward direction...
    if ctx:condition("g_nTemp > 45") then -- JUMPER.inc:101
        ctx:command("g_dirx", "= faceX") -- JUMPER.inc:102
        ctx:command("g_dirz", "= faceZ") -- JUMPER.inc:103
    end -- JUMPER.inc:104
    ctx:command("setvelocity", "g_hMyObject,0,100,0") -- JUMPER.inc:106
    ctx:command("vecscale", "g_dirX,g_dirY,g_dirZ,250") -- JUMPER.inc:108
    ctx:command("setpushback", "g_dirX,g_dirY,g_dirZ,2") -- JUMPER.inc:110
    ctx:command("wait", "28,0.2,SetupTouchNotify") -- JUMPER.inc:112
    do return ctx:exit("") end -- JUMPER.inc:116
end

script.labels["ReadyToJump"] = function(ctx)
    -- JUMPER.inc:120
    ctx:command("wait", "23, 1, JumpAtTarget") -- JUMPER.inc:122
    -- gosub JumpAtTarget
    do return ctx:exit("") end -- JUMPER.inc:124
end

script.labels["JumperGetPlayer"] = function(ctx)
    -- JUMPER.inc:129
    -- Cancel our wait... (just in case)
    ctx:command("wait", "9, 0, DoNothing") -- JUMPER.inc:134
    ctx:command("getplayerhandle", "g_hTarget") -- JUMPER.inc:136
    ctx:command("setflag", "g_hMyObject,FLAG_VISIBLE") -- JUMPER.inc:138
    ctx:command("loopanim", "LyingDown,0") -- JUMPER.inc:140
    ctx:command("getfacedir", "g_hMyObject,g_dirX,g_dirY,g_dirZ") -- JUMPER.inc:142
    ctx:command("vecscale", "g_dirX,g_dirY,g_dirZ,60") -- JUMPER.inc:144
    ctx:command("vecadd", "g_dirX,g_dirY,g_dirZ,startX,startY,startZ") -- JUMPER.inc:146
    ctx:command("movetopos", "g_dirX,g_dirY,g_dirZ,50,ReadyToJump") -- JUMPER.inc:147
    ctx:command("playsound", "Sounds\\Events\\rubble.wav,DoNothing,1000,2000") -- JUMPER.inc:149
    ctx:command("removetrigger", "BuddyDead") -- JUMPER.inc:151
    do return ctx:exit("") end -- JUMPER.inc:153
end

script.labels["ResetJumper"] = function(ctx)
    -- JUMPER.inc:157
    ctx:command("setstat", "g_hMyObject,Gravity,FALSE") -- JUMPER.inc:159
    ctx:command("clearflag", "g_hMyObject,FLAG_SOLID") -- JUMPER.inc:160
    ctx:command("clearflag", "g_hMyObject,FLAG_VISIBLE") -- JUMPER.inc:161
    ctx:command("setflag", "g_hMyObject,FLAG_GOTHRUWORLD") -- JUMPER.inc:162
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
    ctx:command("setpos", "g_hMyObject,startX,startY,startZ") -- JUMPER.inc:176
    ctx:command("loopanim", "LyingDown,0") -- JUMPER.inc:177
    do return ctx:exit("") end -- JUMPER.inc:179
end

script.labels["JumperWaitGetPlayer"] = function(ctx)
    -- JUMPER.inc:183
    ctx:command("getrandomfloat", "minWait,maxWait,g_nRandom") -- JUMPER.inc:186
    ctx:command("wait", "9, g_nRandom, JumperGetPlayer") -- JUMPER.inc:188
    do return ctx:exit("") end -- JUMPER.inc:190
end

script.labels["JumperSetupPos"] = function(ctx)
    -- JUMPER.inc:193
    ctx:command("getpos", "g_hMyObject,startX,startY,startZ") -- JUMPER.inc:196
    do return ctx:exit("") end -- JUMPER.inc:198
end

script.labels["SetupJumper"] = function(ctx)
    -- JUMPER.inc:201
    ctx:command("getmyhandle", "g_hMyObject") -- JUMPER.inc:203
    ctx:command("setstat", "g_hMyObject,Gravity,FALSE") -- JUMPER.inc:206
    ctx:command("clearflag", "g_hMyObject,FLAG_SOLID") -- JUMPER.inc:207
    ctx:command("clearflag", "g_hMyObject,FLAG_VISIBLE") -- JUMPER.inc:208
    ctx:command("setflag", "g_hMyObject,FLAG_GOTHRUWORLD") -- JUMPER.inc:209
    ctx:command("wait", "29,0.1,ResetJumper") -- JUMPER.inc:211
    ctx:command("wait", "28,0.1,JumperSetupPos") -- JUMPER.inc:212
    ctx:addTrigger("Reset", "ResetJumper") -- JUMPER.inc:214
    ctx:addTrigger("Jump", "JumperGetPlayer") -- JUMPER.inc:215
    ctx:addTrigger("GetPlayer", "JumperGetPlayer") -- JUMPER.inc:216
    ctx:addTrigger("BuddyDead", "JumperGetPlayer") -- JUMPER.inc:217
    ctx:addTrigger("WaitGetPlayer", "JumperWaitGetPlayer") -- JUMPER.inc:218
    ctx:command("cachesound", "sRubbleSound") -- JUMPER.inc:220
    do return ctx:exit("") end -- JUMPER.inc:222
end

return script
