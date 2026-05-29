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
    ctx:object("Jeff"):trigger("GoThrowBones") -- ISLEOFASHESACTOR.scr:28-29
    ctx:state().g_hTarget = ctx:player() -- ISLEOFASHESACTOR.scr:31
    ctx:self():setTarget(ctx:object("g_hTarget")) -- ISLEOFASHESACTOR.scr:32
    -- now we wait for the signal...
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:36
end

script.labels["DoBoneThrow"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:39
    -- Throw the bone object here...
    ctx:getTime("g_nTemp") -- ISLEOFASHESACTOR.scr:48
    ctx:sub("g_nTemp", "lastBoneThrow") -- ISLEOFASHESACTOR.scr:50
    if ctx:condition("g_nTemp < 0.35") then -- ISLEOFASHESACTOR.scr:52
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:53
    end -- ISLEOFASHESACTOR.scr:54
    ctx:getTime("lastBoneThrow") -- ISLEOFASHESACTOR.scr:56
    ctx:set("sSkull", "TheBone + boneNbr") -- ISLEOFASHESACTOR.scr:58
    if ctx:condition("boneNbr==0") then -- ISLEOFASHESACTOR.scr:60
        ctx:state().boneNbr = 1 -- ISLEOFASHESACTOR.scr:61
    else -- ISLEOFASHESACTOR.scr:62
        ctx:state().boneNbr = 0 -- ISLEOFASHESACTOR.scr:63
    end -- ISLEOFASHESACTOR.scr:64
    ctx:state().g_hObject = ctx:objectOrNil("sSkull") -- ISLEOFASHESACTOR.scr:66
    if ctx:condition("g_hObject==NULL") then -- ISLEOFASHESACTOR.scr:68
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:69
    end -- ISLEOFASHESACTOR.scr:70
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():socketPos("RHand1") -- ISLEOFASHESACTOR.scr:72
    ctx:object("g_hObject"):setPos("g_posX", "g_posY", "g_posZ") -- ISLEOFASHESACTOR.scr:73
    ctx:trigger("g_hObject", "ThrowAtPlayer") -- ISLEOFASHESACTOR.scr:75
    ctx:wait("ATTACK_CHECK_WAIT", "MIN_THROW_TIME", "ThrowBoneCheck") -- ISLEOFASHESACTOR.scr:77
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:79
end

script.labels["OnPropLauncherDone"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:83
    ctx:state().g_bThrowing = false -- ISLEOFASHESACTOR.scr:85
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:87
end

script.labels["ThrowBoneCheck"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:89
    -- traceON
    mm9.gosub(script, ctx, "ThrowBoneCheck2") -- ISLEOFASHESACTOR.scr:91
    ctx:traceOff() -- ISLEOFASHESACTOR.scr:92
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:93
end

script.labels["ThrowBoneCheck2"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:96
    ctx:wait("ATTACK_CHECK_WAIT", 0.4, "ThrowBoneCheck") -- ISLEOFASHESACTOR.scr:100
    if ctx:condition("g_bThrowing==TRUE") then -- ISLEOFASHESACTOR.scr:102
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:103
    end -- ISLEOFASHESACTOR.scr:104
    ctx:state().hPlayer = ctx:self():aiDistanceTo(ctx:self()) -- ISLEOFASHESACTOR.scr:106
    if ctx:condition("g_nDist1 > MAX_THROW_DIST") then -- ISLEOFASHESACTOR.scr:108
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:109
    end -- ISLEOFASHESACTOR.scr:110
    ctx:state().g_bTemp, ctx:state().g_hObject = ctx:self():isClearShot(ctx:player()) -- ISLEOFASHESACTOR.scr:113
    if ctx:condition("g_bTemp==FALSE") then -- ISLEOFASHESACTOR.scr:115
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:116
    end -- ISLEOFASHESACTOR.scr:117
    -- g_bThrowing = TRUE
    ctx:self():rangeAttack() -- ISLEOFASHESACTOR.scr:121
    -- Wait 28,0.4,OnPropLauncherDone
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:125
end

script.labels["AtBoneThrowMarker"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:129
    -- Trigger the other 2 skeletoids to go after
    -- player.
    ctx:self():stop() -- ISLEOFASHESACTOR.scr:136
    ctx:self():setTarget(ctx:player()) -- ISLEOFASHESACTOR.scr:139
    -- JSL--> Now that we are the new SkullThrower
    -- Object, we no longer need to use the
    -- PropLauncher stuff.  Just run the
    -- BaseRange script..
    ctx:self():setNumberProperty("RangeAttackType", 2) -- ISLEOFASHESACTOR.scr:147
    ctx:runScript("BaseRange.Scr") -- ISLEOFASHESACTOR.scr:148
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:150
    ctx:addModelKey("Rattack", "DoBoneThrow") -- ISLEOFASHESACTOR.scr:152
    ctx:wait("ATTACK_CHECK_WAIT", 0.25, "ThrowBoneCheck") -- ISLEOFASHESACTOR.scr:154
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:156
end

script.labels["TemporaryHack"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:159
    ctx:state().g_hObject = ctx:objectOrNil("BoneThrowMarker") -- ISLEOFASHESACTOR.scr:162
    ctx:self():stop() -- ISLEOFASHESACTOR.scr:164
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:object("g_hObject"):pos() -- ISLEOFASHESACTOR.scr:165
    ctx:self():setPos("g_posX", "g_posY", "g_posZ") -- ISLEOFASHESACTOR.scr:166
    mm9.gosub(script, ctx, "AtBoneThrowMarker") -- ISLEOFASHESACTOR.scr:168
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:170
end

script.labels["GoThrowBones"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:173
    ctx:removeTrigger("GoThrowBones") -- ISLEOFASHESACTOR.scr:176
    ctx:state().g_hObject = ctx:objectOrNil("BoneThrowMarker") -- ISLEOFASHESACTOR.scr:178
    if ctx:condition("g_hObject==NULL") then -- ISLEOFASHESACTOR.scr:179
        do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:180
    end -- ISLEOFASHESACTOR.scr:181
    ctx:self():runTo(ctx:object("g_hObject"), 0, "AtBoneThrowMarker") -- ISLEOFASHESACTOR.scr:183
    -- remove when ramp has been smoothed out..
    -- Wait 25,2,TemporaryHack
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:188
end

script.labels["GoAfterPlayer"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:191
    ctx:state().g_hTarget = ctx:player() -- ISLEOFASHESACTOR.scr:193
    ctx:self():setTarget(ctx:object("g_hTarget")) -- ISLEOFASHESACTOR.scr:194
    mm9.gosub(script, ctx, "RunNormalScript") -- ISLEOFASHESACTOR.scr:195
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:196
end

script.labels["RunNormalScript"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:199
    -- GetPlayerHandle g_hTarget
    -- Target g_hTarget,TRUE
    ctx:self():stop() -- ISLEOFASHESACTOR.scr:204
    ctx:self():setStat("WalkRunMode", "WALKRUNMODE_FORWARD") -- ISLEOFASHESACTOR.scr:206
    ctx:state().g_sTemp = ctx:self():stringProperty("ScriptName") -- ISLEOFASHESACTOR.scr:207
    ctx:runScript("g_sTemp") -- ISLEOFASHESACTOR.scr:209
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:211
end

script.labels["OnLostTarget"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:214
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:216
end

script.labels["MacAtRunAwaySpot"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:219
    ctx:self():stop() -- ISLEOFASHESACTOR.scr:221
    -- Don't need this callback now...
    ctx:onEvent("OnDeath") -- ISLEOFASHESACTOR.scr:224
    mm9.gosub(script, ctx, "DoMacTriggers") -- ISLEOFASHESACTOR.scr:226
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:object("hMarker"):rotation() -- ISLEOFASHESACTOR.scr:228
    ctx:self():faceDir("g_dirX", 0, "g_dirZ", 360, "RunNormalScript") -- ISLEOFASHESACTOR.scr:229
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:231
end

script.labels["DoMacTriggers"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:234
    ctx:state().g_hObject = ctx:objectOrNil("Jeff") -- ISLEOFASHESACTOR.scr:236
    if ctx:condition("g_hObject!=NULL") then -- ISLEOFASHESACTOR.scr:237
        ctx:trigger("g_hObject", "GoThrowBones") -- ISLEOFASHESACTOR.scr:238
    end -- ISLEOFASHESACTOR.scr:239
    ctx:state().g_hObject = ctx:objectOrNil("JK") -- ISLEOFASHESACTOR.scr:241
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
    ctx:self():setStat("WalkRunMode", "WALKRUNMODE_FORWARD") -- ISLEOFASHESACTOR.scr:259
    ctx:self():stop() -- ISLEOFASHESACTOR.scr:261
    ctx:state().hMarker = ctx:objectOrNil("MacRunAwaySpot") -- ISLEOFASHESACTOR.scr:263
    ctx:self():runTo(ctx:object("hMarker"), 50, "MacAtRunAwaySpot") -- ISLEOFASHESACTOR.scr:264
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:265
end

script.labels["OnMacFoundPlayer"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:268
    ctx:onEvent("OnFoundPlayer") -- ISLEOFASHESACTOR.scr:270
    ctx:onEvent("OnDamage") -- ISLEOFASHESACTOR.scr:271
    ctx:removeTrigger("MacRunAway") -- ISLEOFASHESACTOR.scr:272
    ctx:state().hMarker = ctx:objectOrNil("MacRunAwaySpot") -- ISLEOFASHESACTOR.scr:274
    ctx:self():setTarget(ctx:player()) -- ISLEOFASHESACTOR.scr:278
    ctx:self():setStat("WalkRunMode", "WALKRUNMODE_TARGET") -- ISLEOFASHESACTOR.scr:280
    mm9.gosub(script, ctx, "BaseWanderStop") -- ISLEOFASHESACTOR.scr:282
    ctx:state().bWanderDisabled = true -- ISLEOFASHESACTOR.scr:283
    ctx:self():stop() -- ISLEOFASHESACTOR.scr:285
    ctx:self():walkTo(ctx:object("hMarker"), 50, "MacAtRunAwaySpot") -- ISLEOFASHESACTOR.scr:287
    ctx:self():blendAnimation("Taunt") -- ISLEOFASHESACTOR.scr:288
    ctx:wait(29, 1, "MacTauntDone") -- ISLEOFASHESACTOR.scr:291
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:293
end

script.labels["JeffFoundPlayer"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:296
    ctx:onEvent("OnFoundPlayer") -- ISLEOFASHESACTOR.scr:298
    ctx:onEvent("OnAlert") -- ISLEOFASHESACTOR.scr:299
    ctx:onEvent("OnDamage") -- ISLEOFASHESACTOR.scr:300
    mm9.gosub(script, ctx, "GoThrowBones") -- ISLEOFASHESACTOR.scr:302
    do return ctx:exit("TRUE") end -- ISLEOFASHESACTOR.scr:303
end

script.labels["CacheFiles"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:306
    ctx:cacheScript("BaseRange.Scr") -- ISLEOFASHESACTOR.scr:308
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:309
end

script.labels["Main"] = function(ctx)
    -- ISLEOFASHESACTOR.scr:312
    ctx:state().sMyName = ctx:self():name() -- ISLEOFASHESACTOR.scr:315
    ctx:addTrigger("RunNormalScript", "RunNormalScript") -- ISLEOFASHESACTOR.scr:317
    ctx:onEvent("OnLostTarget", "OnLostTarget") -- ISLEOFASHESACTOR.scr:319
    if ctx:condition("sMyName==Mac") then -- ISLEOFASHESACTOR.scr:321
        ctx:onEvent("OnDamage", "OnMacFoundPlayer") -- ISLEOFASHESACTOR.scr:322
        ctx:onEvent("OnFoundPlayer", "OnMacFoundPlayer") -- ISLEOFASHESACTOR.scr:323
        ctx:onEvent("OnDeath", "OnMacDeath") -- ISLEOFASHESACTOR.scr:324
        ctx:addTrigger("MacRunAway", "OnMacFoundPlayer") -- ISLEOFASHESACTOR.scr:325
        ctx:addTrigger("GoAfterPlayer", "GoAfterPlayer") -- ISLEOFASHESACTOR.scr:326
        mm9.gosub(script, ctx, "BaseWanderInit") -- ISLEOFASHESACTOR.scr:327
    end -- ISLEOFASHESACTOR.scr:328
    if ctx:condition("sMyName==Jeff") then -- ISLEOFASHESACTOR.scr:330
        ctx:addTrigger("GoThrowBones", "GoThrowBones") -- ISLEOFASHESACTOR.scr:331
        -- AddTrigger PropLauncherDone,OnPropLauncherDone
        ctx:hidePiece("DaggerMagic") -- ISLEOFASHESACTOR.scr:333
        ctx:onEvent("OnFoundPlayer", "JeffFoundPlayer") -- ISLEOFASHESACTOR.scr:334
        ctx:onEvent("OnAlert", "JeffFoundPlayer") -- ISLEOFASHESACTOR.scr:335
        ctx:onEvent("OnDamage", "JeffFoundPlayer") -- ISLEOFASHESACTOR.scr:336
        ctx:onEvent("OnCacheFiles", "CacheFiles") -- ISLEOFASHESACTOR.scr:337
        ctx:state().g_nTemp = ctx:self():getStat("SightDistance") -- ISLEOFASHESACTOR.scr:338
        ctx:self():setNumberProperty("HearingRange", "g_nTemp") -- ISLEOFASHESACTOR.scr:339
    end -- ISLEOFASHESACTOR.scr:340
    do return ctx:exit("") end -- ISLEOFASHESACTOR.scr:342
end

return script
