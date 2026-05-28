-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLEOFASHESACTOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "AIGlobals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "BaseTimers.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "BaseWander.inc" }

-- IsleOfAshesActor.scr
-- Jeff Leggett
-- Used by scripted actors in IsleOfAshes...
script.labels["FacingJeff"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:26
    ctx:command("getobjecthandle", "Jeff,g_hObject") -- ISLEOFASHESACTOR.scr:28
    ctx:trigger("g_hObject", "GoThrowBones") -- ISLEOFASHESACTOR.scr:29
    ctx:command("getplayerhandle", "g_hTarget") -- ISLEOFASHESACTOR.scr:31
    ctx:command("target", "g_hTarget, TRUE") -- ISLEOFASHESACTOR.scr:32
    -- now we wait for the signal...
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:36
end

script.labels["DoBoneThrow"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:39
    -- Throw the bone object here...
    ctx:command("gettime", "g_nTemp") -- ISLEOFASHESACTOR.scr:48
    ctx:command("sub", "g_nTemp,lastBoneThrow") -- ISLEOFASHESACTOR.scr:50
    if ctx:condition("g_nTemp < 0.35") then -- ISLEOFASHESACTOR.scr:52
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:53
    end -- ISLEOFASHESACTOR.scr:54
    ctx:command("gettime", "lastBoneThrow") -- ISLEOFASHESACTOR.scr:56
    ctx:command("sskull", "= TheBone + boneNbr") -- ISLEOFASHESACTOR.scr:58
    if ctx:condition("boneNbr==0") then -- ISLEOFASHESACTOR.scr:60
        ctx:command("bonenbr", "= 1") -- ISLEOFASHESACTOR.scr:61
    else -- ISLEOFASHESACTOR.scr:62
        ctx:command("bonenbr", "= 0") -- ISLEOFASHESACTOR.scr:63
    end -- ISLEOFASHESACTOR.scr:64
    ctx:command("getobjecthandle", "sSkull,g_hObject") -- ISLEOFASHESACTOR.scr:66
    if ctx:condition("g_hObject==NULL") then -- ISLEOFASHESACTOR.scr:68
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:69
    end -- ISLEOFASHESACTOR.scr:70
    ctx:command("getsocketpos", "RHand1,g_posX,g_posY,g_posZ") -- ISLEOFASHESACTOR.scr:72
    ctx:command("setpos", "g_hObject,g_posX,g_posY,g_posZ") -- ISLEOFASHESACTOR.scr:73
    ctx:trigger("g_hObject", "ThrowAtPlayer") -- ISLEOFASHESACTOR.scr:75
    ctx:command("wait", "ATTACK_CHECK_WAIT,MIN_THROW_TIME,ThrowBoneCheck") -- ISLEOFASHESACTOR.scr:77
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:79
end

script.labels["OnPropLauncherDone"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:83
    ctx:command("g_bthrowing", "= false") -- ISLEOFASHESACTOR.scr:85
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:87
end

script.labels["ThrowBoneCheck"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:89
    -- traceON
    mm9.gosub(script, ctx, "ThrowBoneCheck2") -- ISLEOFASHESACTOR.scr:91
    ctx:command("traceoff", "") -- ISLEOFASHESACTOR.scr:92
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:93
end

script.labels["ThrowBoneCheck2"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:96
    ctx:command("wait", "ATTACK_CHECK_WAIT,0.4,ThrowBoneCheck") -- ISLEOFASHESACTOR.scr:100
    if ctx:condition("g_bThrowing==TRUE") then -- ISLEOFASHESACTOR.scr:102
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:103
    end -- ISLEOFASHESACTOR.scr:104
    ctx:command("aigetdistance", "g_hMyObject,hPlayer,g_nDist1") -- ISLEOFASHESACTOR.scr:106
    if ctx:condition("g_nDist1 > MAX_THROW_DIST") then -- ISLEOFASHESACTOR.scr:108
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:109
    end -- ISLEOFASHESACTOR.scr:110
    ctx:command("getplayerhandle", "hPlayer") -- ISLEOFASHESACTOR.scr:112
    ctx:command("isclearshot", "hPlayer, g_bTemp, g_hObject") -- ISLEOFASHESACTOR.scr:113
    if ctx:condition("g_bTemp==FALSE") then -- ISLEOFASHESACTOR.scr:115
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:116
    end -- ISLEOFASHESACTOR.scr:117
    -- g_bThrowing = TRUE
    ctx:command("rangeattack", "") -- ISLEOFASHESACTOR.scr:121
    -- Wait 28,0.4,OnPropLauncherDone
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:125
end

script.labels["AtBoneThrowMarker"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:129
    -- Trigger the other 2 skeletoids to go after
    -- player.
    ctx:command("stop", "") -- ISLEOFASHESACTOR.scr:136
    ctx:command("getplayerhandle", "hPlayer") -- ISLEOFASHESACTOR.scr:138
    ctx:command("target", "hPlayer,TRUE") -- ISLEOFASHESACTOR.scr:139
    -- JSL--> Now that we are the new SkullThrower
    -- Object, we no longer need to use the
    -- PropLauncher stuff.  Just run the
    -- BaseRange script..
    ctx:setPropNumber("RangeAttackType", 2) -- ISLEOFASHESACTOR.scr:147
    ctx:command("runscript", "BaseRange.Scr") -- ISLEOFASHESACTOR.scr:148
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:150
    ctx:command("addmodelkey", "Rattack,DoBoneThrow") -- ISLEOFASHESACTOR.scr:152
    ctx:command("wait", "ATTACK_CHECK_WAIT,0.25,ThrowBoneCheck") -- ISLEOFASHESACTOR.scr:154
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:156
end

script.labels["TemporaryHack"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:159
    ctx:command("getobjecthandle", "BoneThrowMarker,g_hObject") -- ISLEOFASHESACTOR.scr:162
    ctx:command("stop", "") -- ISLEOFASHESACTOR.scr:164
    ctx:command("getpos", "g_hObject,g_posX,g_posY,g_posZ") -- ISLEOFASHESACTOR.scr:165
    ctx:command("setpos", "g_hMyObject,g_posX,g_posY,g_posZ") -- ISLEOFASHESACTOR.scr:166
    mm9.gosub(script, ctx, "AtBoneThrowMarker") -- ISLEOFASHESACTOR.scr:168
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:170
end

script.labels["GoThrowBones"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:173
    ctx:command("removetrigger", "GoThrowBones") -- ISLEOFASHESACTOR.scr:176
    ctx:command("getobjecthandle", "BoneThrowMarker,g_hObject") -- ISLEOFASHESACTOR.scr:178
    if ctx:condition("g_hObject==NULL") then -- ISLEOFASHESACTOR.scr:179
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:180
    end -- ISLEOFASHESACTOR.scr:181
    ctx:command("runto", "g_hObject,0,AtBoneThrowMarker") -- ISLEOFASHESACTOR.scr:183
    -- remove when ramp has been smoothed out..
    -- Wait 25,2,TemporaryHack
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:188
end

script.labels["GoAfterPlayer"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:191
    ctx:command("getplayerhandle", "g_hTarget") -- ISLEOFASHESACTOR.scr:193
    ctx:command("target", "g_hTarget,TRUE") -- ISLEOFASHESACTOR.scr:194
    mm9.gosub(script, ctx, "RunNormalScript") -- ISLEOFASHESACTOR.scr:195
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:196
end

script.labels["RunNormalScript"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:199
    -- GetPlayerHandle g_hTarget
    -- Target g_hTarget,TRUE
    ctx:command("stop", "") -- ISLEOFASHESACTOR.scr:204
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_FORWARD") -- ISLEOFASHESACTOR.scr:206
    ctx:command("getstatstr", "g_hMyObject,ScriptName,g_sTemp") -- ISLEOFASHESACTOR.scr:207
    ctx:command("runscript", "g_sTemp") -- ISLEOFASHESACTOR.scr:209
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:211
end

script.labels["OnLostTarget"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:214
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:216
end

script.labels["MacAtRunAwaySpot"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:219
    ctx:command("stop", "") -- ISLEOFASHESACTOR.scr:221
    -- Don't need this callback now...
    ctx:command("ondeath", "") -- ISLEOFASHESACTOR.scr:224
    mm9.gosub(script, ctx, "DoMacTriggers") -- ISLEOFASHESACTOR.scr:226
    ctx:command("getfacedir", "hMarker, g_dirX,g_dirY,g_dirZ") -- ISLEOFASHESACTOR.scr:228
    ctx:command("facedir", "g_dirX, 0, g_dirZ, 360, RunNormalScript") -- ISLEOFASHESACTOR.scr:229
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:231
end

script.labels["DoMacTriggers"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:234
    ctx:command("getobjecthandle", "Jeff,g_hObject") -- ISLEOFASHESACTOR.scr:236
    if ctx:condition("g_hObject!=NULL") then -- ISLEOFASHESACTOR.scr:237
        ctx:trigger("g_hObject", "GoThrowBones") -- ISLEOFASHESACTOR.scr:238
    end -- ISLEOFASHESACTOR.scr:239
    ctx:command("getobjecthandle", "JK,g_hObject") -- ISLEOFASHESACTOR.scr:241
    if ctx:condition("g_hObject!=NULL") then -- ISLEOFASHESACTOR.scr:242
        ctx:trigger("g_hObject", "GetPlayer") -- ISLEOFASHESACTOR.scr:243
    end -- ISLEOFASHESACTOR.scr:244
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:246
end

script.labels["OnMacDeath"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:249
    mm9.gosub(script, ctx, "DoMacTriggers") -- ISLEOFASHESACTOR.scr:251
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:253
end

script.labels["MacTauntDone"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:257
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_FORWARD") -- ISLEOFASHESACTOR.scr:259
    ctx:command("stop", "") -- ISLEOFASHESACTOR.scr:261
    ctx:command("getobjecthandle", "MacRunAwaySpot,hMarker") -- ISLEOFASHESACTOR.scr:263
    ctx:command("runto", "hMarker,50,MacAtRunAwaySpot") -- ISLEOFASHESACTOR.scr:264
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:265
end

script.labels["OnMacFoundPlayer"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:268
    ctx:command("onfoundplayer", "") -- ISLEOFASHESACTOR.scr:270
    ctx:command("ondamage", "") -- ISLEOFASHESACTOR.scr:271
    ctx:command("removetrigger", "MacRunAway") -- ISLEOFASHESACTOR.scr:272
    ctx:command("getobjecthandle", "MacRunAwaySpot,hMarker") -- ISLEOFASHESACTOR.scr:274
    ctx:command("getplayerhandle", "hPlayer") -- ISLEOFASHESACTOR.scr:276
    ctx:command("target", "hPlayer, TRUE") -- ISLEOFASHESACTOR.scr:278
    ctx:command("setstat", "g_hMyObject,WalkRunMode,WALKRUNMODE_TARGET") -- ISLEOFASHESACTOR.scr:280
    mm9.gosub(script, ctx, "BaseWanderStop") -- ISLEOFASHESACTOR.scr:282
    ctx:command("bwanderdisabled", "= TRUE") -- ISLEOFASHESACTOR.scr:283
    ctx:command("stop", "") -- ISLEOFASHESACTOR.scr:285
    ctx:command("walkto", "hMarker,50,MacAtRunAwaySpot") -- ISLEOFASHESACTOR.scr:287
    ctx:command("blendanim", "Taunt") -- ISLEOFASHESACTOR.scr:288
    ctx:command("wait", "29,1,MacTauntDone") -- ISLEOFASHESACTOR.scr:291
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:293
end

script.labels["JeffFoundPlayer"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:296
    ctx:command("onfoundplayer", "") -- ISLEOFASHESACTOR.scr:298
    ctx:command("onalert", "") -- ISLEOFASHESACTOR.scr:299
    ctx:command("ondamage", "") -- ISLEOFASHESACTOR.scr:300
    mm9.gosub(script, ctx, "GoThrowBones") -- ISLEOFASHESACTOR.scr:302
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:303
end

script.labels["CacheFiles"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:306
    ctx:command("cachescript", "BaseRange.Scr") -- ISLEOFASHESACTOR.scr:308
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:309
end

script.labels["Main"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:312
    ctx:command("getmyhandle", "g_hMyObject") -- ISLEOFASHESACTOR.scr:314
    ctx:command("getobjectname", "g_hMyObject,sMyName") -- ISLEOFASHESACTOR.scr:315
    ctx:addTrigger("RunNormalScript", "RunNormalScript") -- ISLEOFASHESACTOR.scr:317
    ctx:command("onlosttarget", "OnLostTarget") -- ISLEOFASHESACTOR.scr:319
    if ctx:condition("sMyName==Mac") then -- ISLEOFASHESACTOR.scr:321
        ctx:command("ondamage", "OnMacFoundPlayer") -- ISLEOFASHESACTOR.scr:322
        ctx:command("onfoundplayer", "OnMacFoundPlayer") -- ISLEOFASHESACTOR.scr:323
        ctx:command("ondeath", "OnMacDeath") -- ISLEOFASHESACTOR.scr:324
        ctx:addTrigger("MacRunAway", "OnMacFoundPlayer") -- ISLEOFASHESACTOR.scr:325
        ctx:addTrigger("GoAfterPlayer", "GoAfterPlayer") -- ISLEOFASHESACTOR.scr:326
        mm9.gosub(script, ctx, "BaseWanderInit") -- ISLEOFASHESACTOR.scr:327
    end -- ISLEOFASHESACTOR.scr:328
    if ctx:condition("sMyName==Jeff") then -- ISLEOFASHESACTOR.scr:330
        ctx:addTrigger("GoThrowBones", "GoThrowBones") -- ISLEOFASHESACTOR.scr:331
        -- AddTrigger PropLauncherDone,OnPropLauncherDone
        ctx:command("hidepiece", "DaggerMagic") -- ISLEOFASHESACTOR.scr:333
        ctx:command("onfoundplayer", "JeffFoundPlayer") -- ISLEOFASHESACTOR.scr:334
        ctx:command("onalert", "JeffFoundPlayer") -- ISLEOFASHESACTOR.scr:335
        ctx:command("ondamage", "JeffFoundPlayer") -- ISLEOFASHESACTOR.scr:336
        ctx:command("oncachefiles", "CacheFiles") -- ISLEOFASHESACTOR.scr:337
        ctx:command("getstat", "g_hMyObject,SightDistance,g_nTemp") -- ISLEOFASHESACTOR.scr:338
        ctx:setPropNumber("HearingRange", "g_nTemp") -- ISLEOFASHESACTOR.scr:339
    end -- ISLEOFASHESACTOR.scr:340
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:342
end

return script
