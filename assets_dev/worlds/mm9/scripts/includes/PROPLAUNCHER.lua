-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PROPLAUNCHER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "flags.inc" }

-- PropLauncher.Inc
-- Jeff Leggett
-- 12/06/2001
-- Script that can turn a prop (or any model) into a projectile...
-- Be sure to call PropLauncherInit in your main...
script.labels["KeepRotating"] = function(ctx)
    -- PROPLAUNCHER.inc:51
    if ctx:condition("bThrowing==TRUE") then -- PROPLAUNCHER.inc:53
        ctx:command("rotate", "rotX,rotY,rotZ,90,g_nRotationRate,KeepRotating") -- PROPLAUNCHER.inc:54
    end -- PROPLAUNCHER.inc:55
    do return ctx:exit("") end -- PROPLAUNCHER.inc:57
end

script.labels["DoRotation"] = function(ctx)
    -- PROPLAUNCHER.inc:60
    mm9.gosub(script, ctx, "KeepRotating") -- PROPLAUNCHER.inc:63
    do return ctx:exit("") end -- PROPLAUNCHER.inc:65
end

script.labels["ThrowAtTarget"] = function(ctx)
    -- PROPLAUNCHER.inc:68
    ctx:command("getpos", "g_hTarget, targetX,targetY,targetZ") -- PROPLAUNCHER.inc:70
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- PROPLAUNCHER.inc:71
    ctx:command("vecdist", "g_posX,g_posY,g_posZ,targetX,targetY,targetZ,g_nTemp") -- PROPLAUNCHER.inc:73
    if ctx:condition("g_nTemp > 60") then -- PROPLAUNCHER.inc:75
        ctx:command("getvelocity", "g_hTarget,g_velX,g_velY,g_velZ") -- PROPLAUNCHER.inc:77
        ctx:command("g_vely", "= 0") -- PROPLAUNCHER.inc:78
        ctx:command("vecmag", "g_velX,g_velY,g_velZ,velocity") -- PROPLAUNCHER.inc:80
        if ctx:condition("velocity > 20") then -- PROPLAUNCHER.inc:82
            -- adjust position based on velocity...
            -- how much time to intercept
            ctx:command("g_ntemp", "= g_nTemp / g_nThrowSpeed") -- PROPLAUNCHER.inc:87
            ctx:command("getrandomfloat", "g_nPredictOffsetMin,g_nPredictOffsetMax,g_nRandom") -- PROPLAUNCHER.inc:89
            ctx:command("g_ntemp", "= g_nTemp * g_nRandom") -- PROPLAUNCHER.inc:91
            -- VecNorm g_velX,g_velY,g_velZ
            ctx:command("vecscale", "g_velX,g_velY,g_velZ,g_nTemp") -- PROPLAUNCHER.inc:94
            ctx:command("vecadd", "targetX,targetY,targetZ,g_velX,g_velY,g_velZ") -- PROPLAUNCHER.inc:95
        end -- PROPLAUNCHER.inc:96
    end -- PROPLAUNCHER.inc:97
    ctx:command("vecsub", "targetX,targetY,targetZ,g_posX,g_posY,g_posZ") -- PROPLAUNCHER.inc:99
    ctx:command("vecnorm", "targetX,targetY,targetZ") -- PROPLAUNCHER.inc:100
    ctx:command("facedir", "targetX,targetY,targetZ") -- PROPLAUNCHER.inc:101
    ctx:command("vecscale", "targetX,targetY,targetZ,g_nThrowSpeed") -- PROPLAUNCHER.inc:102
    ctx:command("setvelocity", "g_hMyObject,targetX,targetY,targetZ") -- PROPLAUNCHER.inc:104
    ctx:command("setflag", "g_hMyObject,FLAG_VISIBLE") -- PROPLAUNCHER.inc:105
    ctx:command("bthrowing", "= TRUE") -- PROPLAUNCHER.inc:107
    ctx:command("bdiddamage", "= FALSE") -- PROPLAUNCHER.inc:108
    mm9.gosub(script, ctx, "DoRotation") -- PROPLAUNCHER.inc:110
    ctx:command("gettime", "g_lastLaunchTime") -- PROPLAUNCHER.inc:112
    ctx:command("wait", "5,5,Reset") -- PROPLAUNCHER.inc:114
    do return ctx:exit("") end -- PROPLAUNCHER.inc:116
end

script.labels["ThrowAtPlayerTrigger"] = function(ctx)
    -- PROPLAUNCHER.inc:119
    -- p0 - requester...
    ctx:getParam(0, "g_hObject") -- PROPLAUNCHER.inc:123
    if ctx:condition("g_hObject!=hRequester") then -- PROPLAUNCHER.inc:125
        if ctx:condition("hRequester!=NULL") then -- PROPLAUNCHER.inc:126
            ctx:command("breakobjectlink", "hRequester") -- PROPLAUNCHER.inc:127
        end -- PROPLAUNCHER.inc:128
        ctx:command("hrequester", "= g_hObject") -- PROPLAUNCHER.inc:129
        ctx:command("createobjectlink", "hRequester") -- PROPLAUNCHER.inc:130
    end -- PROPLAUNCHER.inc:131
    ctx:command("getplayerhandle", "g_hTarget") -- PROPLAUNCHER.inc:133
    mm9.gosub(script, ctx, "ThrowAtTarget") -- PROPLAUNCHER.inc:135
    do return ctx:exit("") end -- PROPLAUNCHER.inc:137
end

script.labels["Reset"] = function(ctx)
    -- PROPLAUNCHER.inc:140
    if ctx:condition("hRequester!=NULL") then -- PROPLAUNCHER.inc:143
        ctx:trigger("hRequester", "PropLauncherDone") -- PROPLAUNCHER.inc:144
    end -- PROPLAUNCHER.inc:145
    ctx:command("wait", "5,0,DoNothing") -- PROPLAUNCHER.inc:147
    ctx:command("clearflag", "g_hMyObject,FLAG_VISIBLE") -- PROPLAUNCHER.inc:148
    ctx:command("setvelocity", "g_hMyObject,0,0,0") -- PROPLAUNCHER.inc:149
    ctx:command("bthrowing", "= FALSE") -- PROPLAUNCHER.inc:150
    ctx:command("wait", "7,0.1,ResetPosition") -- PROPLAUNCHER.inc:151
    ctx:command("bdiddamage", "= FALSE") -- PROPLAUNCHER.inc:153
    do return ctx:exit("") end -- PROPLAUNCHER.inc:155
end

script.labels["OnTouchNotify"] = function(ctx)
    -- PROPLAUNCHER.inc:158
    ctx:getParam(0, "g_hObject") -- PROPLAUNCHER.inc:160
    if ctx:condition("g_hObject==hRequester") then -- PROPLAUNCHER.inc:162
        do return ctx:exit("FALSE") end -- PROPLAUNCHER.inc:163
    end -- PROPLAUNCHER.inc:164
    if ctx:condition("bDidDamage==FALSE") then -- PROPLAUNCHER.inc:166
        ctx:command("isclass", "g_hObject,Actor,g_bTemp") -- PROPLAUNCHER.inc:167
        if ctx:condition("g_bTemp==TRUE") then -- PROPLAUNCHER.inc:168
            ctx:command("bdiddamage", "= TRUE") -- PROPLAUNCHER.inc:169
            ctx:command("getrandomint", "g_nDamageMin,g_nDamageMax,g_nTemp") -- PROPLAUNCHER.inc:170
            ctx:command("damage", "g_hObject,g_nTemp,0") -- PROPLAUNCHER.inc:171
        else -- PROPLAUNCHER.inc:172
            ctx:command("gettime", "g_nTemp") -- PROPLAUNCHER.inc:173
            ctx:command("sub", "g_nTemp,g_lastLaunchTime") -- PROPLAUNCHER.inc:174
            if ctx:condition("g_nTemp < 0.2") then -- PROPLAUNCHER.inc:175
                -- Too soon to call it quits?
                do return ctx:exit("FALSE") end -- PROPLAUNCHER.inc:177
            end -- PROPLAUNCHER.inc:178
        end -- PROPLAUNCHER.inc:179
    end -- PROPLAUNCHER.inc:180
    -- TODO:Play sound here...
    mm9.gosub(script, ctx, "Reset") -- PROPLAUNCHER.inc:185
    do return ctx:exit("") end -- PROPLAUNCHER.inc:187
end

script.labels["ResetPosition"] = function(ctx)
    -- PROPLAUNCHER.inc:191
    ctx:command("setpos", "g_hMyObject,homeX,homeY,homeZ") -- PROPLAUNCHER.inc:194
    do return ctx:exit("") end -- PROPLAUNCHER.inc:196
end

script.labels["OnLinkBroken"] = function(ctx)
    -- PROPLAUNCHER.inc:199
    ctx:getParam(0, "g_hObject") -- PROPLAUNCHER.inc:202
    if ctx:condition("g_hObject==hRequester") then -- PROPLAUNCHER.inc:203
        ctx:command("hrequester", "= NULL") -- PROPLAUNCHER.inc:204
    end -- PROPLAUNCHER.inc:205
    do return ctx:exit("") end -- PROPLAUNCHER.inc:207
end

script.labels["PropLauncherInit"] = function(ctx)
    -- PROPLAUNCHER.inc:210
    ctx:command("getmyhandle", "g_hMyObject") -- PROPLAUNCHER.inc:213
    ctx:command("clearflag", "g_hMyObject,FLAG_VISIBLE") -- PROPLAUNCHER.inc:214
    ctx:command("clearflag", "g_hMyObject,FLAG_SOLID") -- PROPLAUNCHER.inc:215
    ctx:command("getpos", "g_hMyObject,homeX,homeY,homeZ") -- PROPLAUNCHER.inc:217
    ctx:addTrigger("ThrowAtPlayer", "ThrowAtPlayerTrigger") -- PROPLAUNCHER.inc:219
    ctx:addTrigger("GetPlayer", "ThrowAtPlayerTrigger") -- PROPLAUNCHER.inc:220
    ctx:addTrigger("ResetPosition", "ResetPosition") -- PROPLAUNCHER.inc:221
    ctx:command("ontouchnotify", "OnTouchNotify") -- PROPLAUNCHER.inc:222
    ctx:command("onobjectlinkbroken", "OnLinkBroken") -- PROPLAUNCHER.inc:223
    ctx:command("setstat", "g_hMyObject,GroundTouchNotify,TRUE") -- PROPLAUNCHER.inc:225
    do return ctx:exit("") end -- PROPLAUNCHER.inc:227
end

return script
