-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASEWANDER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseTimers.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "basedoor.inc" }

-- BaseWander.inc
-- Jeff Leggett
-- Handles basic wandering
-- Marker stat vars...
script.labels["OnWanderAtMarkerNext"] = function(ctx)
    -- BASEWANDER.inc:58
    -- We hit our marker.. Time to go to next one....
    ctx:self():stop() -- BASEWANDER.inc:64
    -- See if we need to use the local marker's info...
    ctx:state().g_bUseMarkerWaitTime = ctx:object("hCurrentMarker"):getStat("UseMarkerWaitTime") -- BASEWANDER.inc:69
    if ctx:condition("g_bUseMarkerWaitTime==TRUE") then -- BASEWANDER.inc:71
        ctx:state().g_nMarkerWaitMin = ctx:object("hCurrentMarker"):getStat("WanderWaitMin") -- BASEWANDER.inc:72
        ctx:state().g_nMarkerWaitMax = ctx:object("hCurrentMarker"):getStat("WanderWaitMax") -- BASEWANDER.inc:73
        if ctx:condition("g_nMarkerWaitMin==0") then -- BASEWANDER.inc:74
            ctx:set("g_nMarkerWaitMin", 0.01) -- BASEWANDER.inc:75
        end -- BASEWANDER.inc:76
        if ctx:condition("g_nMarkerWaitMax==0") then -- BASEWANDER.inc:77
            ctx:set("g_nMarkerWaitMax", 0.01) -- BASEWANDER.inc:78
        end -- BASEWANDER.inc:79
    end -- BASEWANDER.inc:81
    ctx:state().g_bTemp = ctx:object("hCurrentMarker"):getStat("UseMarkerRotation") -- BASEWANDER.inc:83
    if ctx:condition("g_bTemp==TRUE") then -- BASEWANDER.inc:84
        ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:object("hCurrentMarker"):rotation() -- BASEWANDER.inc:85
        ctx:self():faceDir("g_dirX", 0, "g_dirZ", 360) -- BASEWANDER.inc:86
    end -- BASEWANDER.inc:87
    ctx:state().g_bTemp = ctx:object("hCurrentMarker"):getStat("PlayAnim") -- BASEWANDER.inc:89
    if ctx:condition("g_bTemp==TRUE") then -- BASEWANDER.inc:91
        ctx:state().g_sTemp = ctx:object("hCurrentMarker"):stringProperty("AnimationName") -- BASEWANDER.inc:92
        ctx:self():getAnimationNumber("g_sTemp", "g_nTemp") -- BASEWANDER.inc:93
        if ctx:condition("g_nTemp!=-1") then -- BASEWANDER.inc:94
            ctx:state().g_bTemp = ctx:object("hCurrentMarker"):getStat("LoopAnim") -- BASEWANDER.inc:95
            if ctx:condition("g_bTemp==TRUE") then -- BASEWANDER.inc:96
                ctx:self():loopAnimation("g_nTemp", 0) -- BASEWANDER.inc:97
            else -- BASEWANDER.inc:98
                ctx:self():playAnimation("g_nTemp", "MarkerAnimDone") -- BASEWANDER.inc:99
            end -- BASEWANDER.inc:100
        end -- BASEWANDER.inc:101
    end -- BASEWANDER.inc:102
    ctx:state().hCurrentMarker = nil -- BASEWANDER.inc:104
    -- Do our normal wait...
    mm9.gosub(script, ctx, "BaseWanderResume") -- BASEWANDER.inc:107
    do return ctx:exit("") end -- BASEWANDER.inc:109
end

script.labels["OnWanderAtMarker"] = function(ctx)
    -- BASEWANDER.inc:112
    -- We touched a marker...
    ctx:getParam(0, "g_hObject") -- BASEWANDER.inc:118
    if ctx:condition("g_hObject==hCurrentMarker") then -- BASEWANDER.inc:120
        -- GetObjectName hCurrentMarker,g_sTemp
        -- g_sTemp = g_sTemp + ___AtMarker
        -- cprint g_sTemp
        -- debugout g_sTemp
        do return mm9.gotoLabel(script, ctx, "OnWanderAtMarkerNext") end -- BASEWANDER.inc:125
    end -- BASEWANDER.inc:126
    do return ctx:exit("TRUE") end -- BASEWANDER.inc:128
end

script.labels["MarkerAnimDone"] = function(ctx)
    -- BASEWANDER.inc:131
    -- This is here so you can potentially overload it....
    do return ctx:exit("") end -- BASEWANDER.inc:136
end

script.labels["BaseWanderGetFirstMarker"] = function(ctx)
    -- BASEWANDER.inc:139
    -- Returns handle to 1st marker
    if ctx:condition("bWanderRandom==TRUE") then -- BASEWANDER.inc:145
        mm9.gosub(script, ctx, "BaseWanderGetNextMarker") -- BASEWANDER.inc:146
        do return ctx:exit("") end -- BASEWANDER.inc:147
    end -- BASEWANDER.inc:148
    if ctx:condition("nWanderPathCount==0") then -- BASEWANDER.inc:150
        ctx:state().hCurrentMarker = nil -- BASEWANDER.inc:151
        do return ctx:exit("") end -- BASEWANDER.inc:152
    end -- BASEWANDER.inc:153
    -- Set g_sTemp,sWanderPath
    -- Add g_sTemp,nWanderPathStart
    ctx:set("g_sTemp", "sWanderPath + nWanderPathStart") -- BASEWANDER.inc:157
    ctx:state().hCurrentMarker = ctx:objectOrNil("g_sTemp") -- BASEWANDER.inc:159
    do return ctx:exit("") end -- BASEWANDER.inc:161
end

script.labels["ValidateWanderMarker"] = function(ctx)
    -- BASEWANDER.inc:164
    -- Will set bFound to FALSE if marker is not valid...
    ctx:state().g_bTemp = ctx:self():isClass("NPC") -- BASEWANDER.inc:170
    if ctx:condition("g_bTemp==FALSE") then -- BASEWANDER.inc:171
        do return ctx:exit("") end -- BASEWANDER.inc:172
    end -- BASEWANDER.inc:173
    ctx:state().g_nCounter = (tonumber(ctx:state().g_nCounter) or 0) + 1 -- BASEWANDER.inc:175
    ctx:set("g_nTemp", "nWanderPathCount * 3") -- BASEWANDER.inc:177
    if ctx:condition("g_nCounter>=g_nTemp") then -- BASEWANDER.inc:179
        -- No markers are valid.... We did our best, just punt...
        do return ctx:exit("") end -- BASEWANDER.inc:181
    end -- BASEWANDER.inc:182
    ctx:set("g_sTemp", "sWanderPath + nCurrentMarker") -- BASEWANDER.inc:184
    ctx:state().g_hObject = ctx:objectOrNil("g_sTemp") -- BASEWANDER.inc:185
    if ctx:condition("g_hObject!=NULL") then -- BASEWANDER.inc:187
        ctx:state().g_bTemp = ctx:self():canReachObject(ctx:object("g_hObject")) -- BASEWANDER.inc:188
        if ctx:condition("g_bTemp==FALSE") then -- BASEWANDER.inc:189
            ctx:state().bFound = false -- BASEWANDER.inc:190
        end -- BASEWANDER.inc:191
    end -- BASEWANDER.inc:192
    do return ctx:exit("") end -- BASEWANDER.inc:194
end

script.labels["BaseWanderGetNextMarker"] = function(ctx)
    -- BASEWANDER.inc:197
    -- Gets handle to next path
    if ctx:condition("nWanderPathCount==0") then -- BASEWANDER.inc:203
        ctx:state().hCurrentMarker = nil -- BASEWANDER.inc:204
        do return ctx:exit("") end -- BASEWANDER.inc:205
    end -- BASEWANDER.inc:206
    if ctx:condition("bWanderRandom==TRUE") then -- BASEWANDER.inc:208
        ctx:state().bFound = false -- BASEWANDER.inc:209
        ctx:state().g_nCounter = 0 -- BASEWANDER.inc:210
        while ctx:condition("bFound==FALSE") do -- BASEWANDER.inc:211
            if ctx:condition("nWanderPathCount==2") then -- BASEWANDER.inc:212
                if ctx:condition("nCurrentMarker==0") then -- BASEWANDER.inc:213
                    ctx:state().nCurrentMarker = 1 -- BASEWANDER.inc:214
                else -- BASEWANDER.inc:215
                    ctx:state().nCurrentMarker = 0 -- BASEWANDER.inc:216
                end -- BASEWANDER.inc:217
                ctx:state().bFound = true -- BASEWANDER.inc:218
            else -- BASEWANDER.inc:219
                ctx:set("g_nTemp", "nWanderPathCount - 1") -- BASEWANDER.inc:220
                ctx:randomInt(0, "g_nTemp", "g_nTemp") -- BASEWANDER.inc:221
                if ctx:condition("g_nTemp!=nCurrentMarker") then -- BASEWANDER.inc:222
                    ctx:set("nCurrentMarker", "g_nTemp") -- BASEWANDER.inc:223
                    ctx:state().bFound = true -- BASEWANDER.inc:224
                    -- will set bFound = FALSE if it's no good.
                    mm9.gosub(script, ctx, "ValidateWanderMarker") -- BASEWANDER.inc:226
                end -- BASEWANDER.inc:227
            end -- BASEWANDER.inc:228
        end -- BASEWANDER.inc:229
    else -- BASEWANDER.inc:230
        ctx:state().nCurrentMarker = (tonumber(ctx:state().nCurrentMarker) or 0) + 1 -- BASEWANDER.inc:231
        ctx:mod("nCurrentMarker", "nWanderPathCount") -- BASEWANDER.inc:232
    end -- BASEWANDER.inc:233
    -- Set g_sTemp,sWanderPath
    -- Add g_sTemp,nCurrentMarker
    ctx:set("g_sTemp", "sWanderPath + nCurrentMarker") -- BASEWANDER.inc:237
    ctx:state().hCurrentMarker = ctx:objectOrNil("g_sTemp") -- BASEWANDER.inc:239
    do return ctx:exit("") end -- BASEWANDER.inc:241
end

script.labels["BaseWanderLeashCheck"] = function(ctx)
    -- BASEWANDER.inc:245
    -- Just checks if we're beyond our leash distance...
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- BASEWANDER.inc:251
    ctx:set("g_posY", "wanderStartY") -- BASEWANDER.inc:252
    ctx:state().g_nTemp = ctx:vecDist("g_posX", "g_posY", "g_posZ", "wanderStartX", "wanderStartY", "wanderStartZ") -- BASEWANDER.inc:254
    if ctx:condition("g_nTemp >= nWanderLeash") then -- BASEWANDER.inc:256
        -- When we start again, we'll head for our start point....
        ctx:self():stop() -- BASEWANDER.inc:258
        do return ctx:exit("") end -- BASEWANDER.inc:259
    end -- BASEWANDER.inc:260
    ctx:wait("WANDER_LEASH_WAIT", 0.25, "BaseWanderLeashCheck") -- BASEWANDER.inc:262
    do return ctx:exit("") end -- BASEWANDER.inc:264
end

script.labels["BaseWanderStartWalking"] = function(ctx)
    -- BASEWANDER.inc:267
    -- We should be facing the way we want to...
    -- Walk!!!
    ctx:self():walk() -- BASEWANDER.inc:274
    ctx:randomFloat("MIN_WANDER_TIME", "MAX_WANDER_TIME", "g_nRandom") -- BASEWANDER.inc:276
    if ctx:condition("bWanderAimlessly==TRUE") then -- BASEWANDER.inc:278
        ctx:wait("WANDER_WAIT", "g_nRandom", "BaseWanderStopTick") -- BASEWANDER.inc:279
    end -- BASEWANDER.inc:280
    if ctx:condition("nWanderLeash!=0") then -- BASEWANDER.inc:282
        ctx:wait("WANDER_LEASH_WAIT", 0.25, "BaseWanderLeashCheck") -- BASEWANDER.inc:283
    end -- BASEWANDER.inc:284
    do return ctx:exit("") end -- BASEWANDER.inc:286
end

script.labels["BaseWanderObstacle"] = function(ctx)
    -- BASEWANDER.inc:289
    -- Stop, and remember the normal of our obstacle...
    if ctx:condition("hCurrentMarker!=NULL") then -- BASEWANDER.inc:296
        do return ctx:exit("FALSE") end -- BASEWANDER.inc:297
    end -- BASEWANDER.inc:298
    ctx:randomInt(0, 100, "g_nRandom") -- BASEWANDER.inc:300
    ctx:getParam(0, "g_hObject") -- BASEWANDER.inc:302
    ctx:state().g_bTemp = ctx:object("g_hObject"):isClass("Actor") -- BASEWANDER.inc:303
    if ctx:condition("g_bTemp==TRUE") then -- BASEWANDER.inc:305
        if ctx:condition("g_nRandom < 90") then -- BASEWANDER.inc:306
            do return ctx:exit("FALSE") end -- BASEWANDER.inc:307
        end -- BASEWANDER.inc:308
    else -- BASEWANDER.inc:309
        if ctx:condition("g_nRandom < 70") then -- BASEWANDER.inc:310
            do return ctx:exit("FALSE") end -- BASEWANDER.inc:311
        end -- BASEWANDER.inc:312
    end -- BASEWANDER.inc:313
    ctx:getParam(1, "normalX") -- BASEWANDER.inc:315
    ctx:getParam(2, "normalY") -- BASEWANDER.inc:316
    ctx:getParam(3, "normalZ") -- BASEWANDER.inc:317
    mm9.gosub(script, ctx, "BaseWanderPause") -- BASEWANDER.inc:319
    ctx:self():stop() -- BASEWANDER.inc:320
    ctx:wait("WANDER_LEASH_WAIT", 0, "DoNothing") -- BASEWANDER.inc:321
    ctx:state().bObstacle = true -- BASEWANDER.inc:322
    mm9.gosub(script, ctx, "BaseWanderResume") -- BASEWANDER.inc:323
    ctx:getParam(0, "g_hObject") -- BASEWANDER.inc:325
    ctx:state().g_bTemp = ctx:object("g_hObject"):isClass("Actor") -- BASEWANDER.inc:326
    if ctx:condition("g_bTemp==FALSE") then -- BASEWANDER.inc:327
        ctx:self():faceDir("normalX", 0, "normalZ", 360) -- BASEWANDER.inc:328
    end -- BASEWANDER.inc:329
    do return ctx:exit("TRUE") end -- BASEWANDER.inc:332
end

script.labels["BaseWanderStuck"] = function(ctx)
    -- BASEWANDER.inc:335
    mm9.gosub(script, ctx, "BaseWanderPause") -- BASEWANDER.inc:338
    do return ctx:exit("FALSE") end -- BASEWANDER.inc:340
end

script.labels["BaseWanderStuckDone"] = function(ctx)
    -- BASEWANDER.inc:343
    mm9.gosub(script, ctx, "BaseWanderResume") -- BASEWANDER.inc:346
    do return ctx:exit("TRUE") end -- BASEWANDER.inc:348
end

script.labels["BaseWanderPickRandomDir"] = function(ctx)
    -- BASEWANDER.inc:352
    if ctx:condition("bObstacle==TRUE") then -- BASEWANDER.inc:354
        -- We've already turned around 180 from the obstacle...
        -- Now just turn a little one way or the other...
        ctx:state().bObstacle = false -- BASEWANDER.inc:357
        ctx:randomFloat(15, 90, "g_nRandom") -- BASEWANDER.inc:358
    else -- BASEWANDER.inc:359
        ctx:randomFloat(15, 180, "g_nRandom") -- BASEWANDER.inc:360
    end -- BASEWANDER.inc:361
    ctx:randomInt("FALSE", "TRUE", "g_bTemp") -- BASEWANDER.inc:363
    if ctx:condition("g_bTemp==TRUE") then -- BASEWANDER.inc:365
        ctx:set("g_nRandom", "g_nRandom * -1") -- BASEWANDER.inc:366
    end -- BASEWANDER.inc:367
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- BASEWANDER.inc:369
    ctx:set("g_posY", "wanderStartY") -- BASEWANDER.inc:370
    ctx:state().g_nTemp = ctx:vecDist("g_posX", "g_posY", "g_posZ", "wanderStartX", "wanderStartY", "wanderStartZ") -- BASEWANDER.inc:372
    if ctx:condition("nWanderLeash!=0") then -- BASEWANDER.inc:374
        if ctx:condition("g_nTemp >= nWanderLeash") then -- BASEWANDER.inc:375
            ctx:self():facePos("wanderStartX", "wanderStartY", "wanderStartZ", 180) -- BASEWANDER.inc:376
        else -- BASEWANDER.inc:377
            ctx:self():rotate(0, 1, 0, "g_nRandom", 180) -- BASEWANDER.inc:378
        end -- BASEWANDER.inc:379
    else -- BASEWANDER.inc:380
        ctx:self():rotate(0, 1, 0, "g_nRandom", 180) -- BASEWANDER.inc:381
    end -- BASEWANDER.inc:382
    do return ctx:exit("") end -- BASEWANDER.inc:384
end

script.labels["BaseWanderPathArrived"] = function(ctx)
    -- BASEWANDER.inc:387
    -- We've hit a path point... Time to wait....
    ctx:set("g_sTemp", "hCurrentMarker") -- BASEWANDER.inc:393
    ctx:setParam(0, "g_sTemp") -- BASEWANDER.inc:394
    mm9.gosub(script, ctx, "OnWanderAtMarker") -- BASEWANDER.inc:395
    do return ctx:exit("TRUE") end -- BASEWANDER.inc:397
end

script.labels["CanReachCurrentMarker"] = function(ctx)
    -- BASEWANDER.inc:399
    ctx:state().g_bTemp = ctx:self():canReachObject(ctx:object("hCurrentMarker")) -- BASEWANDER.inc:402
    do return ctx:exit("") end -- BASEWANDER.inc:404
end

script.labels["BaseWanderNextPathDir"] = function(ctx)
    -- BASEWANDER.inc:407
    -- Get handle of next marker... Then turn towards it!
    if ctx:condition("bFirstMarker==TRUE") then -- BASEWANDER.inc:413
        ctx:state().bFirstMarker = false -- BASEWANDER.inc:414
        mm9.gosub(script, ctx, "BaseWanderGetFirstMarker") -- BASEWANDER.inc:415
    else -- BASEWANDER.inc:416
        mm9.gosub(script, ctx, "BaseWanderGetNextMarker") -- BASEWANDER.inc:417
    end -- BASEWANDER.inc:418
    if ctx:condition("hCurrentMarker==NULL") then -- BASEWANDER.inc:420
        do return ctx:exit("") end -- BASEWANDER.inc:421
    end -- BASEWANDER.inc:422
    mm9.gosub(script, ctx, "CanReachCurrentMarker") -- BASEWANDER.inc:424
    if ctx:condition("g_bTemp==FALSE") then -- BASEWANDER.inc:426
        ctx:debugOut("Cannot", "reach", "following", "marker.", "Wandering", "aimlessly!") -- BASEWANDER.inc:427
        if ctx:condition("hCurrentMarker==NULL") then -- BASEWANDER.inc:428
            ctx:debugOut("CurrentMarker", "is", "NULL!") -- BASEWANDER.inc:429
        else -- BASEWANDER.inc:430
            ctx:set("g_sTemp", "Error") -- BASEWANDER.inc:431
            ctx:state().g_sTemp = ctx:object("hCurrentMarker"):name() -- BASEWANDER.inc:432
            ctx:debugOut("g_sTemp") -- BASEWANDER.inc:433
        end -- BASEWANDER.inc:434
        ctx:state().bWanderAimlessly = true -- BASEWANDER.inc:436
        ctx:state().nWanderPathCount = 0 -- BASEWANDER.inc:437
    else -- BASEWANDER.inc:438
        -- GetObjectName hCurrentMarker,g_sTemp
        -- cprint WalkingTo
        -- cprint g_sTemp
        -- DebugOut g_sTemp
        ctx:self():walkTo(ctx:object("hCurrentMarker"), 1, "BaseWanderPathArrived") -- BASEWANDER.inc:444
    end -- BASEWANDER.inc:445
    do return ctx:exit("") end -- BASEWANDER.inc:447
end

script.labels["BD_DoorOpen"] = function(ctx)
    -- BASEWANDER.inc:450
    -- If we are currently wandering toward a marker, walk to
    -- it...
    ctx:state().g_bDoorOpening = false -- BASEWANDER.inc:456
    if ctx:condition("hCurrentMarker==NULL") then -- BASEWANDER.inc:458
        mm9.gosub(script, ctx, "BD_DoorOpen") -- BASEWANDER.inc:459
        do return ctx:exit("") end -- BASEWANDER.inc:460
    end -- BASEWANDER.inc:461
    -- GetObjectName hCurrentMarker,g_sTemp
    -- cprint WalkingTo
    -- cprint g_sTemp
    -- DebugOut g_sTemp
    ctx:self():walkTo(ctx:object("hCurrentMarker"), 1, "BaseWanderPathArrived") -- BASEWANDER.inc:468
    ctx:restorePath() -- BASEWANDER.inc:470
    do return ctx:exit("") end -- BASEWANDER.inc:472
end

script.labels["BaseWanderGo"] = function(ctx)
    -- BASEWANDER.inc:475
    -- Pick my direction and start moving....
    mm9.gosub(script, ctx, "BaseDoorInit") -- BASEWANDER.inc:481
    ctx:onEvent("OnObstacle", "BaseWanderObstacle") -- BASEWANDER.inc:482
    ctx:onEvent("OnStuckDone", "BaseWanderStuckDone") -- BASEWANDER.inc:483
    ctx:onEvent("OnStuck", "BaseWanderStuck") -- BASEWANDER.inc:484
    ctx:state().bIsWandering = true -- BASEWANDER.inc:486
    if ctx:condition("bWanderAimlessly==FALSE") then -- BASEWANDER.inc:488
        mm9.gosub(script, ctx, "BaseWanderNextPathDir") -- BASEWANDER.inc:489
        if ctx:condition("bWanderAimlessly==FALSE") then -- BASEWANDER.inc:490
            -- If BaseWanderNextPathDir determined that we cannot
            -- reach the original wander path that was setup, then
            -- we won't exit...
            do return ctx:exit("") end -- BASEWANDER.inc:494
        end -- BASEWANDER.inc:495
    end -- BASEWANDER.inc:496
    mm9.gosub(script, ctx, "BaseWanderPickRandomDir") -- BASEWANDER.inc:498
    mm9.gosub(script, ctx, "BaseWanderStartWalking") -- BASEWANDER.inc:499
    do return ctx:exit("") end -- BASEWANDER.inc:501
end

script.labels["BaseWanderResume"] = function(ctx)
    -- BASEWANDER.inc:504
    if ctx:condition("bIsWandering==FALSE") then -- BASEWANDER.inc:506
        do return ctx:exit("") end -- BASEWANDER.inc:507
    end -- BASEWANDER.inc:508
    ctx:state().bWanderPaused = false -- BASEWANDER.inc:510
    mm9.gosub(script, ctx, "BaseWanderStart") -- BASEWANDER.inc:512
    do return ctx:exit("") end -- BASEWANDER.inc:514
end

script.labels["BaseWanderPause"] = function(ctx)
    -- BASEWANDER.inc:517
    ctx:state().bWanderPaused = true -- BASEWANDER.inc:519
    ctx:wait("WANDER_WAIT", 0, "DoNothing") -- BASEWANDER.inc:520
    do return ctx:exit("") end -- BASEWANDER.inc:522
end

script.labels["BaseWanderStart"] = function(ctx)
    -- BASEWANDER.inc:525
    -- Call this to start up the wander again.  Usually after
    -- you're done attacking someone....
    ctx:onEvent("OnObstacle", "BaseWanderObstacle") -- BASEWANDER.inc:531
    ctx:onEvent("OnStuckDone", "BaseWanderStuckDone") -- BASEWANDER.inc:532
    ctx:onEvent("OnStuck", "BaseWanderStuck") -- BASEWANDER.inc:533
    if ctx:condition("g_bUseMarkerWaitTime==TRUE") then -- BASEWANDER.inc:535
        ctx:randomFloat("g_nMarkerWaitMin", "g_nMarkerWaitMax", "g_nRandom") -- BASEWANDER.inc:536
        ctx:state().g_bUseMarkerWaitTime = false -- BASEWANDER.inc:537
    else -- BASEWANDER.inc:538
        ctx:randomFloat("MIN_WANDER_WAIT", "MAX_WANDER_WAIT", "g_nRandom") -- BASEWANDER.inc:539
    end -- BASEWANDER.inc:540
    if ctx:condition("g_nRandom < 0.2") then -- BASEWANDER.inc:542
        ctx:wait("WANDER_WAIT", 0, "DoNothing") -- BASEWANDER.inc:543
        mm9.gosub(script, ctx, "BaseWanderStartTick") -- BASEWANDER.inc:544
        do return ctx:exit("") end -- BASEWANDER.inc:545
    end -- BASEWANDER.inc:546
    ctx:wait("WANDER_WAIT", "g_nRandom", "BaseWanderStartTick") -- BASEWANDER.inc:548
    do return ctx:exit("") end -- BASEWANDER.inc:550
end

script.labels["BaseWanderStop"] = function(ctx)
    -- BASEWANDER.inc:553
    -- Call this to stop wander thinking... Usually when you
    -- are busy attacking someone....
    ctx:wait("WANDER_WAIT", 0, "DoNothing") -- BASEWANDER.inc:559
    ctx:wait("WANDER_LEASH_WAIT", 0, "DoNothing") -- BASEWANDER.inc:560
    ctx:state().bObstacle = false -- BASEWANDER.inc:562
    ctx:state().bIsWandering = false -- BASEWANDER.inc:563
    ctx:state().hCurrentMarker = nil -- BASEWANDER.inc:564
    ctx:state().g_bUseMarkerWaitTime = false -- BASEWANDER.inc:565
    do return ctx:exit("") end -- BASEWANDER.inc:567
end

script.labels["CanWander"] = function(ctx)
    -- BASEWANDER.inc:570
    -- Set g_bTemp = TRUE if now's an OK time to wander...
    ctx:state().g_bTemp = true -- BASEWANDER.inc:575
    ctx:state().g_bTemp = ctx:self():getStat("CanWander") -- BASEWANDER.inc:576
    do return ctx:exit("") end -- BASEWANDER.inc:577
end

script.labels["BaseWanderStartTick"] = function(ctx)
    -- BASEWANDER.inc:580
    -- When this fires, it's time to decide if we want to start
    -- wandering....
    mm9.gosub(script, ctx, "CanWander") -- BASEWANDER.inc:587
    if ctx:condition("g_bTemp==FALSE") then -- BASEWANDER.inc:589
        ctx:randomFloat("MIN_WANDER_WAIT", "MAX_WANDER_WAIT", "g_nRandom") -- BASEWANDER.inc:590
        ctx:wait("WANDER_WAIT", "g_nRandom", "BaseWanderStartTick") -- BASEWANDER.inc:591
        do return ctx:exit("") end -- BASEWANDER.inc:592
    end -- BASEWANDER.inc:593
    mm9.gosub(script, ctx, "BaseWanderGo") -- BASEWANDER.inc:595
    do return ctx:exit("") end -- BASEWANDER.inc:597
end

script.labels["BaseWanderStopTick"] = function(ctx)
    -- BASEWANDER.inc:600
    -- When this fires, it's time to decide if we want to stop
    -- wandering....
    ctx:wait("WANDER_LEASH_WAIT", 0, "DoNothing") -- BASEWANDER.inc:607
    ctx:self():stop() -- BASEWANDER.inc:608
    mm9.gosub(script, ctx, "BaseWanderStart") -- BASEWANDER.inc:609
    do return ctx:exit("") end -- BASEWANDER.inc:611
end

script.labels["BaseWanderForceStartUp"] = function(ctx)
    -- BASEWANDER.inc:614
    -- Enable it and start it up...
    if ctx:condition("bWanderEnabled==FALSE") then -- BASEWANDER.inc:620
        ctx:state().bWanderEnabled = true -- BASEWANDER.inc:621
        mm9.gosub(script, ctx, "BaseWanderStartup") -- BASEWANDER.inc:622
        do return ctx:exit("") end -- BASEWANDER.inc:623
    end -- BASEWANDER.inc:624
    mm9.gosub(script, ctx, "BaseWanderStart") -- BASEWANDER.inc:626
    do return ctx:exit("") end -- BASEWANDER.inc:628
end

script.labels["OnWanderTrigger"] = function(ctx)
    -- BASEWANDER.inc:630
    -- We've been triggered to start wandering...
    if ctx:condition("bWanderEnabled==TRUE") then -- BASEWANDER.inc:636
        mm9.gosub(script, ctx, "BaseWanderGo") -- BASEWANDER.inc:637
    else -- BASEWANDER.inc:638
        mm9.gosub(script, ctx, "BaseWanderForceStartUp") -- BASEWANDER.inc:639
    end -- BASEWANDER.inc:640
    do return ctx:exit("") end -- BASEWANDER.inc:642
end

script.labels["BaseWanderStartup"] = function(ctx)
    -- BASEWANDER.inc:645
    ctx:state().nWanderPathCount = ctx:self():getStat("WanderPathCount") -- BASEWANDER.inc:648
    ctx:state().bWanderRandom = ctx:self():getStat("WanderPathRandom") -- BASEWANDER.inc:649
    ctx:state().nWanderLeash = ctx:self():getStat("WanderLeash") -- BASEWANDER.inc:650
    ctx:state().MIN_WANDER_WAIT = ctx:self():getStat("WanderWaitMin") -- BASEWANDER.inc:652
    ctx:state().MAX_WANDER_WAIT = ctx:self():getStat("WanderWaitMax") -- BASEWANDER.inc:653
    if ctx:condition("MIN_WANDER_WAIT==0") then -- BASEWANDER.inc:655
        ctx:set("MIN_WANDER_WAIT", 0.01) -- BASEWANDER.inc:656
    end -- BASEWANDER.inc:657
    if ctx:condition("MAX_WANDER_WAIT==0") then -- BASEWANDER.inc:658
        ctx:set("MAX_WANDER_WAIT", 0.01) -- BASEWANDER.inc:659
    end -- BASEWANDER.inc:660
    ctx:state().MIN_WANDER_TIME = ctx:self():getStat("WanderTimeMin") -- BASEWANDER.inc:662
    ctx:state().MAX_WANDER_TIME = ctx:self():getStat("WanderTimeMax") -- BASEWANDER.inc:663
    ctx:state().nWanderPathStart = ctx:self():getStat("WanderPathStart") -- BASEWANDER.inc:664
    if ctx:condition("MIN_WANDER_TIME==0") then -- BASEWANDER.inc:666
        ctx:set("MIN_WANDER_TIME", 0.01) -- BASEWANDER.inc:667
    end -- BASEWANDER.inc:668
    if ctx:condition("MAX_WANDER_TIME==0") then -- BASEWANDER.inc:669
        ctx:set("MAX_WANDER_TIME", 0.01) -- BASEWANDER.inc:670
    end -- BASEWANDER.inc:671
    ctx:state().sWanderPath = ctx:self():stringProperty("WanderPathName") -- BASEWANDER.inc:673
    if ctx:condition("nWanderPathCount<=1") then -- BASEWANDER.inc:675
        ctx:state().nWanderPathCount = 0 -- BASEWANDER.inc:676
    else -- BASEWANDER.inc:677
        -- No leash with wander paths!
        ctx:state().nWanderLeash = 0 -- BASEWANDER.inc:679
    end -- BASEWANDER.inc:680
    if ctx:condition("nWanderPathStart >= nWanderPathCount") then -- BASEWANDER.inc:682
        ctx:state().nWanderPathStart = 0 -- BASEWANDER.inc:683
    end -- BASEWANDER.inc:684
    if ctx:condition("nWanderPathCount==0") then -- BASEWANDER.inc:686
        ctx:state().bWanderAimlessly = true -- BASEWANDER.inc:687
    else -- BASEWANDER.inc:688
        -- traceON
    end -- BASEWANDER.inc:690
    ctx:state().wanderStartX, ctx:state().wanderStartY, ctx:state().wanderStartZ = ctx:self():pos() -- BASEWANDER.inc:693
    if ctx:condition("bWanderDisabled==FALSE") then -- BASEWANDER.inc:695
        mm9.gosub(script, ctx, "BaseWanderStart") -- BASEWANDER.inc:696
    end -- BASEWANDER.inc:697
    do return ctx:exit("") end -- BASEWANDER.inc:699
end

script.labels["OnWanderStopTrigger"] = function(ctx)
    -- BASEWANDER.inc:702
    -- We've been triggered to stop wandering...
    mm9.gosub(script, ctx, "BaseWanderStop") -- BASEWANDER.inc:707
    do return ctx:exit("") end -- BASEWANDER.inc:709
end

script.labels["BaseWanderInit"] = function(ctx)
    -- BASEWANDER.inc:712
    -- Don't forget to call this in your Main function...
    -- Also, you must setup g_hMyObject prior to calling this
    -- function!
    ctx:state().bWanderEnabled = false -- BASEWANDER.inc:723
    ctx:addTrigger("Wander", "OnWanderTrigger") -- BASEWANDER.inc:725
    ctx:addTrigger("WanderStop", "OnWanderStopTrigger") -- BASEWANDER.inc:726
    ctx:addTrigger("TouchedMarker", "OnWanderAtMarker") -- BASEWANDER.inc:727
    ctx:state().bWanderEnabled = ctx:self():getStat("WanderEnable") -- BASEWANDER.inc:729
    if ctx:condition("bWanderEnabled==FALSE") then -- BASEWANDER.inc:730
        -- No more to do now!
        do return ctx:exit("") end -- BASEWANDER.inc:732
    end -- BASEWANDER.inc:733
    -- Wait a little and then startup.. (so all the names are in...)
    ctx:wait(9, 1, "BaseWanderStartup") -- BASEWANDER.inc:736
    do return ctx:exit("") end -- BASEWANDER.inc:738
end

return script
