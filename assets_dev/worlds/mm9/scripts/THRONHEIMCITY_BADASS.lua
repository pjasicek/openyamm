-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THRONHEIMCITY_BADASS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 20, path = "BaseMelee.inc" }

-- ThronHeimCity_BadAss.scr
-- Jeff Leggett
-- 12/18/2001
-- BadAss is a DesertTerror who is locked away
-- He breaks out of prison and chases NPCs
-- Guards eventually take him down...
-- Note:
-- It is designed that we do this the 2nd time we're
-- in the level and AFTER the silly speech....
-- edited by Bones 3/30/03
-- TELP Patch 1.3 -- prevents stalling at the broken wall
script.labels["GetExtraGuard"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:33
    ctx:command("getobjecthandle", "GuardSpawn1,g_hObject") -- THRONHEIMCITY_BADASS.scr:35
    ctx:trigger("g_hObject", "Default") -- THRONHEIMCITY_BADASS.scr:36
    ctx:command("getobjecthandle", "Guard1,g_hObject") -- THRONHEIMCITY_BADASS.scr:38
    ctx:trigger("g_hObject", "OpenEyes") -- THRONHEIMCITY_BADASS.scr:39
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:41
end

script.labels["Taunt3Done"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:44
    ctx:command("getobjecthandle", "Ben,g_hObject") -- THRONHEIMCITY_BADASS.scr:46
    ctx:command("target", "g_hObject, TRUE") -- THRONHEIMCITY_BADASS.scr:48
    ctx:command("bwanderenabled", "= TRUE") -- THRONHEIMCITY_BADASS.scr:50
    mm9.gosub(script, ctx, "BaseInit") -- THRONHEIMCITY_BADASS.scr:52
    ctx:command("wait", "26, 1.5, SendRunAway2") -- THRONHEIMCITY_BADASS.scr:54
    ctx:command("wait", "27, 6, GetExtraGuard") -- THRONHEIMCITY_BADASS.scr:55
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:57
end

script.labels["TellBenToRunAway"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:60
    ctx:command("toldben", "= TRUE") -- THRONHEIMCITY_BADASS.scr:62
    ctx:command("getobjecthandle", "Ben,g_hObject") -- THRONHEIMCITY_BADASS.scr:63
    ctx:trigger("g_hObject", "RunAwayFromMe") -- THRONHEIMCITY_BADASS.scr:64
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:65
end

script.labels["DoTaunt3"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:68
    ctx:command("wait", "26,0.3,TellBenToRunAway") -- THRONHEIMCITY_BADASS.scr:70
    ctx:command("taunt", "Taunt3Done") -- THRONHEIMCITY_BADASS.scr:72
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:74
end

script.labels["Taunt2Done"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:77
    ctx:command("getfacedir", "g_hMyObject,g_dirX,g_dirY,g_dirZ") -- THRONHEIMCITY_BADASS.scr:79
    ctx:command("rotatedir", "g_dirX,g_dirY,g_dirZ,180") -- THRONHEIMCITY_BADASS.scr:80
    ctx:command("facedir", "g_dirX,g_dirY,g_dirZ,360,DoTaunt3") -- THRONHEIMCITY_BADASS.scr:81
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:82
end

script.labels["DoTaunt2"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:85
    ctx:command("taunt", "Taunt2Done") -- THRONHEIMCITY_BADASS.scr:87
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:88
end

script.labels["DoTaunts"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:91
    ctx:command("stop", "") -- THRONHEIMCITY_BADASS.scr:94
    ctx:command("getfacedir", "hWallMarker,g_dirX,g_dirY,g_dirZ") -- THRONHEIMCITY_BADASS.scr:95
    ctx:command("rotatedir", "g_dirX,g_dirY,g_dirZ,-90") -- THRONHEIMCITY_BADASS.scr:96
    ctx:command("facedir", "g_dirX,g_dirY,g_dirZ,360,DoTaunt2") -- THRONHEIMCITY_BADASS.scr:97
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:99
end

script.labels["OnObstacle"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:102
    ctx:command("stop", "") -- THRONHEIMCITY_BADASS.scr:105
    ctx:command("onobstacle", "") -- THRONHEIMCITY_BADASS.scr:107
    ctx:command("wait", "0,0,DoNothing") -- THRONHEIMCITY_BADASS.scr:108
    mm9.gosub(script, ctx, "DoTaunts") -- THRONHEIMCITY_BADASS.scr:110
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:112
end

script.labels["KillShmoeDone"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:115
    mm9.gosub(script, ctx, "SendRunAway") -- THRONHEIMCITY_BADASS.scr:118
    ctx:command("getfacedir", "hWallMarker,g_dirX,g_dirY,g_dirZ") -- THRONHEIMCITY_BADASS.scr:120
    ctx:command("facedir", "g_dirX,g_dirY,g_dirZ,360") -- THRONHEIMCITY_BADASS.scr:121
    ctx:command("onobstacle", "OnObstacle") -- THRONHEIMCITY_BADASS.scr:122
    ctx:command("run", "") -- THRONHEIMCITY_BADASS.scr:123
    ctx:command("wait", "0,2.5,DoTaunts") -- THRONHEIMCITY_BADASS.scr:124
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:126
end

script.labels["KillShmoe"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:129
    ctx:command("run", "") -- THRONHEIMCITY_BADASS.scr:132
    ctx:command("attack", "KillShmoeDone") -- THRONHEIMCITY_BADASS.scr:133
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:135
end

script.labels["SendRunAway2"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:138
    -- this is done every second or so once we're on our
    -- rampage...
    ctx:command("runawaydist", "= 500") -- THRONHEIMCITY_BADASS.scr:144
    mm9.gosub(script, ctx, "SendRunAway") -- THRONHEIMCITY_BADASS.scr:145
    ctx:command("wait", "21, 1.5, SendRunAway2") -- THRONHEIMCITY_BADASS.scr:146
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:147
end

script.labels["SendRunAway"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:151
    ctx:command("getobjects", "NPC,runAwayDist,20,hRunAway,g_nTemp") -- THRONHEIMCITY_BADASS.scr:156
    ctx:command("counter", "= 0") -- THRONHEIMCITY_BADASS.scr:158
    if ctx:condition("g_nTemp==0") then -- THRONHEIMCITY_BADASS.scr:160
        do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:161
    end -- THRONHEIMCITY_BADASS.scr:162
    while ctx:condition("counter < g_nTemp") do -- THRONHEIMCITY_BADASS.scr:164
        ctx:command("arrayget", "hRunAway,counter,g_hObject") -- THRONHEIMCITY_BADASS.scr:165
        ctx:command("getobjectname", "g_hObject,g_sTemp") -- THRONHEIMCITY_BADASS.scr:166
        if ctx:condition("g_sTemp!=Ben") then -- THRONHEIMCITY_BADASS.scr:167
            ctx:trigger("g_hObject", "RunAwayFromMe") -- THRONHEIMCITY_BADASS.scr:168
        else -- THRONHEIMCITY_BADASS.scr:169
            if ctx:condition("toldBen==TRUE") then -- THRONHEIMCITY_BADASS.scr:170
                ctx:trigger("g_hObject", "RunAwayFromMe") -- THRONHEIMCITY_BADASS.scr:171
            end -- THRONHEIMCITY_BADASS.scr:172
        end -- THRONHEIMCITY_BADASS.scr:173
        ctx:command("add", "counter,1") -- THRONHEIMCITY_BADASS.scr:174
    end -- THRONHEIMCITY_BADASS.scr:175
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:177
end

script.labels["Taunt1Done"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:181
    ctx:command("getobjecthandle", "Shmoe,g_hTarget") -- THRONHEIMCITY_BADASS.scr:184
    ctx:command("target", "g_hTarget,TRUE") -- THRONHEIMCITY_BADASS.scr:186
    ctx:command("runto", "g_hTarget, 75, KillShmoe") -- THRONHEIMCITY_BADASS.scr:188
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:190
end

script.labels["WallBroken"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:194
    ctx:command("getobjecthandle", "Shmoe,g_hObject") -- THRONHEIMCITY_BADASS.scr:196
    ctx:trigger("g_hObject", "HereComesBadAss") -- THRONHEIMCITY_BADASS.scr:197
    ctx:command("getobjecthandle", "Ben,g_hObject") -- THRONHEIMCITY_BADASS.scr:199
    ctx:trigger("g_hObject", "HereComesBadAss") -- THRONHEIMCITY_BADASS.scr:200
    ctx:command("taunt", "Taunt1Done") -- THRONHEIMCITY_BADASS.scr:202
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:204
end

script.labels["DestroyWall"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:207
    ctx:command("removemodelkey", "Rattack") -- THRONHEIMCITY_BADASS.scr:209
    ctx:command("getobjecthandle", "PrisonWall, hPrisonWall") -- THRONHEIMCITY_BADASS.scr:211
    if ctx:condition("hPrisonWall==NULL") then -- THRONHEIMCITY_BADASS.scr:213
        ctx:command("debugout", "ASSERT!! No prison wall?") -- THRONHEIMCITY_BADASS.scr:214
        do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:215
    end -- THRONHEIMCITY_BADASS.scr:216
    ctx:trigger("hPrisonWall", "Destroy") -- THRONHEIMCITY_BADASS.scr:218
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:220
end

script.labels["AttackWall"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:223
    ctx:command("addmodelkey", "Rattack,DestroyWall") -- THRONHEIMCITY_BADASS.scr:226
    ctx:command("attack", "WallBroken") -- THRONHEIMCITY_BADASS.scr:227
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:229
end

script.labels["AtWallMarker"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:232
    ctx:command("stop", "") -- THRONHEIMCITY_BADASS.scr:234
    ctx:command("getfacedir", "hWallMarker,g_dirX,g_dirY,g_dirZ") -- THRONHEIMCITY_BADASS.scr:235
    ctx:command("facedir", "g_dirX,g_dirY,g_dirZ,360,AttackWall") -- THRONHEIMCITY_BADASS.scr:236
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_BADASS.scr:238
end

script.labels["BreakoutCheck"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:241
    ctx:command("wait", "17,1,BreakoutCheck") -- THRONHEIMCITY_BADASS.scr:245
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:246
end

script.labels["OnBreakOut"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:249
    ctx:command("removetrigger", "BreakOut") -- THRONHEIMCITY_BADASS.scr:252
    ctx:command("getobjecthandle", "PrisonWall, hPrisonWall") -- THRONHEIMCITY_BADASS.scr:254
    if ctx:condition("hPrisonWall==NULL") then -- THRONHEIMCITY_BADASS.scr:256
        ctx:command("debugout", "ASSERT!! No prison wall?") -- THRONHEIMCITY_BADASS.scr:257
    end -- THRONHEIMCITY_BADASS.scr:258
    ctx:command("stop", "") -- THRONHEIMCITY_BADASS.scr:260
    ctx:command("getobjecthandle", "BadAssWander1,hWallMarker") -- THRONHEIMCITY_BADASS.scr:262
    ctx:command("walkto", "hWallMarker,0,AtWallMarker") -- THRONHEIMCITY_BADASS.scr:263
    ctx:command("setstat", "g_hMyObject,HitPoints,250") -- THRONHEIMCITY_BADASS.scr:265
    ctx:command("setstat", "g_hMyObject,GaveTreasure,1") -- THRONHEIMCITY_BADASS.scr:266
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:269
end

script.labels["OnDamage"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:272
    -- p0 - hHeHitMe
    -- p1 - how much damage..
    ctx:getParam(0, "g_hObject") -- THRONHEIMCITY_BADASS.scr:277
    ctx:command("isplayer", "g_hObject,g_bTemp") -- THRONHEIMCITY_BADASS.scr:278
    ctx:getParam(1, "g_nRandom") -- THRONHEIMCITY_BADASS.scr:279
    ctx:command("getstat", "g_hMyObject,HitPoints,g_nTemp") -- THRONHEIMCITY_BADASS.scr:280
    if ctx:condition("g_bTemp==TRUE") then -- THRONHEIMCITY_BADASS.scr:282
        -- Don't let the player kill us...
        ctx:command("add", "g_nTemp,g_nRandom") -- THRONHEIMCITY_BADASS.scr:284
        ctx:command("setstat", "g_hMyObject,HitPoints,g_nTemp") -- THRONHEIMCITY_BADASS.scr:285
    end -- THRONHEIMCITY_BADASS.scr:286
    mm9.gosub(script, ctx, "OnDamage") -- THRONHEIMCITY_BADASS.scr:288
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:290
end

script.labels["OnTest"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:294
    mm9.gosub(script, ctx, "OnBreakOut") -- THRONHEIMCITY_BADASS.scr:296
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:298
end

script.labels["SetupBadAss"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:301
    ctx:addTrigger("BreakOut", "OnBreakOut") -- THRONHEIMCITY_BADASS.scr:304
    ctx:addTrigger("test", "OnTest") -- THRONHEIMCITY_BADASS.scr:305
    ctx:command("removeenemy", "NPC") -- THRONHEIMCITY_BADASS.scr:306
    ctx:command("addfriend", "NPC") -- THRONHEIMCITY_BADASS.scr:307
    ctx:command("setstat", "g_hMyObject,GaveTreasure,TRUE") -- THRONHEIMCITY_BADASS.scr:309
    ctx:command("setstat", "g_hMyObject,AC,20") -- THRONHEIMCITY_BADASS.scr:310
    -- OnDamage OnDamage
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:314
end

script.labels["Main"] = function(ctx)
    -- THRONHEIMCITY_BADASS.scr:318
    ctx:command("getmyhandle", "g_hMyObject") -- THRONHEIMCITY_BADASS.scr:321
    ctx:command("wait", "0 1 SetupBadAss") -- THRONHEIMCITY_BADASS.scr:323
    do return ctx:exit("") end -- THRONHEIMCITY_BADASS.scr:325
end

return script
