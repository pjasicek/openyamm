-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIRBASE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "BaseCrawl.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "Range.inc" }

-- YanmirBase.Scr
-- Jeff Leggett
-- 01/02/2002
-- edited by Bones 10/16/02
-- TELP Patch 1.3 -- keep Yanmir immune to physical damage (new loads only)
-- give correct key and ExpPts for non-trap kill (all loads)
-- Puff of smoke...
script.labels["LookForBugsStart"] = function(ctx)
    -- YANMIRBASE.scr:23
    ctx:wait(25, 3, "LookForBugsTick") -- YANMIRBASE.scr:25
    do return ctx:exit("") end -- YANMIRBASE.scr:26
end

script.labels["LookForBugsTick"] = function(ctx)
    -- YANMIRBASE.scr:29
    ctx:randomFloat(0.5, 2, "g_nRandom") -- YANMIRBASE.scr:34
    ctx:wait(25, "g_nRandom", "LookForBugsTick") -- YANMIRBASE.scr:35
    ctx:state().g_hObject = ctx:self():target() -- YANMIRBASE.scr:37
    if ctx:condition("g_hObject!=NULL") then -- YANMIRBASE.scr:39
        do return ctx:exit("") end -- YANMIRBASE.scr:40
    end -- YANMIRBASE.scr:41
    ctx:getObjects("IceLobbercicle", 500, 20, "bugArray", "bugCount") -- YANMIRBASE.scr:43
    if ctx:condition("bugCount==0") then -- YANMIRBASE.scr:45
        do return ctx:exit("") end -- YANMIRBASE.scr:46
    end -- YANMIRBASE.scr:47
    ctx:state().bugCount = (tonumber(ctx:state().bugCount) or 0) - 1 -- YANMIRBASE.scr:49
    ctx:randomInt(0, "bugCount", "g_nRandom") -- YANMIRBASE.scr:50
    ctx:arrayGet("bugArray", "g_nRandom", "g_hTarget") -- YANMIRBASE.scr:52
    ctx:state().g_bTemp = ctx:object("g_hTarget"):isVisible() -- YANMIRBASE.scr:54
    if ctx:condition("g_bTemp==FALSE") then -- YANMIRBASE.scr:56
        ctx:state().g_hTarget = nil -- YANMIRBASE.scr:57
        do return ctx:exit("") end -- YANMIRBASE.scr:58
    end -- YANMIRBASE.scr:59
    ctx:self():stop() -- YANMIRBASE.scr:61
    ctx:set("markerSave", "nCurrentMarker") -- YANMIRBASE.scr:63
    ctx:state().nBugAttempts = 0 -- YANMIRBASE.scr:65
    mm9.gosub(script, ctx, "SetupTarget") -- YANMIRBASE.scr:66
    mm9.gosub(script, ctx, "AggressiveStart") -- YANMIRBASE.scr:67
    do return ctx:exit("") end -- YANMIRBASE.scr:69
end

script.labels["AttackDone"] = function(ctx)
    -- YANMIRBASE.scr:72
    mm9.gosub(script, ctx, "AttackDone") -- YANMIRBASE.scr:74
    if ctx:condition("bPlayerTargeted==FALSE") then -- YANMIRBASE.scr:76
        ctx:state().nBugAttempts = (tonumber(ctx:state().nBugAttempts) or 0) + 1 -- YANMIRBASE.scr:77
        if ctx:condition("nBugAttempts > 3") then -- YANMIRBASE.scr:78
            mm9.gosub(script, ctx, "GiveUpOnTarget") -- YANMIRBASE.scr:79
            do return ctx:exit("") end -- YANMIRBASE.scr:80
        end -- YANMIRBASE.scr:81
    end -- YANMIRBASE.scr:82
    do return ctx:exit("") end -- YANMIRBASE.scr:84
end

script.labels["ClearTarget"] = function(ctx)
    -- YANMIRBASE.scr:87
    mm9.gosub(script, ctx, "LookForBugsStart") -- YANMIRBASE.scr:89
    mm9.gosub(script, ctx, "ClearTarget") -- YANMIRBASE.scr:91
    do return ctx:exit("") end -- YANMIRBASE.scr:93
end

script.labels["SetupTarget"] = function(ctx)
    -- YANMIRBASE.scr:96
    mm9.gosub(script, ctx, "LookForBugsStop") -- YANMIRBASE.scr:98
    ctx:state().bPlayerTargeted = ctx:object("g_hTarget"):isPlayer() -- YANMIRBASE.scr:99
    if ctx:condition("bPlayerTargeted==TRUE") then -- YANMIRBASE.scr:101
        ctx:state().MAX_CHASE_TIME = 45 -- YANMIRBASE.scr:102
    else -- YANMIRBASE.scr:103
        ctx:state().MAX_CHASE_TIME = 15 -- YANMIRBASE.scr:104
    end -- YANMIRBASE.scr:105
    do return mm9.gotoLabel(script, ctx, "SetupTarget") end -- YANMIRBASE.scr:107
    do return ctx:exit("") end -- YANMIRBASE.scr:109
end

script.labels["LookForBugsStop"] = function(ctx)
    -- YANMIRBASE.scr:112
    ctx:wait(25, 0, "DoNothing") -- YANMIRBASE.scr:114
    do return ctx:exit("") end -- YANMIRBASE.scr:115
end

script.labels["TargetPlayer"] = function(ctx)
    -- YANMIRBASE.scr:119
    ctx:state().g_hTarget = ctx:player() -- YANMIRBASE.scr:121
    if ctx:condition("g_hTarget==NULL") then -- YANMIRBASE.scr:122
        ctx:wait(29, 0.1, "TargetPlayer") -- YANMIRBASE.scr:123
        do return ctx:exit("") end -- YANMIRBASE.scr:124
    end -- YANMIRBASE.scr:125
    mm9.gosub(script, ctx, "SetupTarget") -- YANMIRBASE.scr:127
    do return ctx:exit("") end -- YANMIRBASE.scr:129
end

script.labels["OnStuck"] = function(ctx)
    -- YANMIRBASE.scr:133
    mm9.gosub(script, ctx, "GiveUpOnTarget") -- YANMIRBASE.scr:135
    do return ctx:exit("TRUE") end -- YANMIRBASE.scr:136
end

script.labels["OpenDoor"] = function(ctx)
    -- YANMIRBASE.scr:139
    ctx:playSound("Sounds\\Door\\stonedoorslam.wav", "DoNothing", 1000, 3500, "FALSE", 100) -- YANMIRBASE.scr:141
    ctx:state().hDust = ctx:objectOrNil("YanmirDust") -- YANMIRBASE.scr:142
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():socketPos("Rfoot") -- YANMIRBASE.scr:143
    ctx:object("hDust"):setPos("g_posX", "g_posY", "g_posZ") -- YANMIRBASE.scr:144
    ctx:trigger("hDust", "ON") -- YANMIRBASE.scr:145
    ctx:wait(28, .25, "TurnDustOff") -- YANMIRBASE.scr:146
    ctx:trigger("g_hDoor", "Use") -- YANMIRBASE.scr:147
    do return ctx:exit("") end -- YANMIRBASE.scr:148
end

script.labels["TurnDustOff"] = function(ctx)
    -- YANMIRBASE.scr:151
    ctx:trigger("hDust", "Off") -- YANMIRBASE.scr:153
    do return ctx:exit("") end -- YANMIRBASE.scr:154
end

script.labels["KickDoorDone"] = function(ctx)
    -- YANMIRBASE.scr:157
    mm9.gosub(script, ctx, "BD_DoorOpen") -- YANMIRBASE.scr:160
    do return ctx:exit("") end -- YANMIRBASE.scr:162
end

script.labels["KickDoor"] = function(ctx)
    -- YANMIRBASE.scr:165
    -- will call OpenDoor at appropriate time...
    ctx:self():playAnimation("KickDoor", "KickDoorDone") -- YANMIRBASE.scr:169
    do return ctx:exit("") end -- YANMIRBASE.scr:171
end

script.labels["BD_OnDoor"] = function(ctx)
    -- YANMIRBASE.scr:174
    ctx:getParam(0, "g_hDoor") -- YANMIRBASE.scr:177
    ctx:state().g_bTemp = ctx:object("g_hDoor"):getStat("IsClosed") -- YANMIRBASE.scr:179
    if ctx:condition("g_bTemp==FALSE") then -- YANMIRBASE.scr:181
        -- door is not closed, ignore....
        do return ctx:exit("FALSE") end -- YANMIRBASE.scr:183
    end -- YANMIRBASE.scr:184
    mm9.gosub(script, ctx, "KickDoor") -- YANMIRBASE.scr:186
    ctx:savePath() -- YANMIRBASE.scr:188
    ctx:state().g_bDoorOpening = true -- YANMIRBASE.scr:190
    do return ctx:exit("TRUE") end -- YANMIRBASE.scr:193
end

script.labels["SpeedThrottleStart"] = function(ctx)
    -- YANMIRBASE.scr:196
    -- None for me thanks.
    do return ctx:exit("") end -- YANMIRBASE.scr:200
end

script.labels["DoFall"] = function(ctx)
    -- YANMIRBASE.scr:203
    ctx:self():loopAnimation("Fall", 0) -- YANMIRBASE.scr:205
    do return ctx:exit("") end -- YANMIRBASE.scr:207
end

script.labels["FallDown"] = function(ctx)
    -- YANMIRBASE.scr:211
    -- Time to do our fall down animation...
    ctx:wait(21, 0, "DoNothing") -- YANMIRBASE.scr:217
    ctx:self():stop() -- YANMIRBASE.scr:219
    mm9.gosub(script, ctx, "ClearTarget") -- YANMIRBASE.scr:220
    -- Make sure we're uninterested in looking for any targets...
    ctx:onEvent("OnFoundTarget") -- YANMIRBASE.scr:225
    ctx:onEvent("OnDamage") -- YANMIRBASE.scr:226
    ctx:onEvent("OnAlert") -- YANMIRBASE.scr:227
    ctx:onEvent("OnDamageDone") -- YANMIRBASE.scr:228
    ctx:onEvent("OnProjectile") -- YANMIRBASE.scr:229
    mm9.gosub(script, ctx, "LookForBugsStop") -- YANMIRBASE.scr:231
    ctx:self():playAnimation("startDie", "DoFall") -- YANMIRBASE.scr:233
    do return ctx:exit("") end -- YANMIRBASE.scr:235
end

script.labels["Begin"] = function(ctx)
    -- YANMIRBASE.scr:238
    ctx:removeTrigger("Squish") -- YANMIRBASE.scr:240
    mm9.gosub(script, ctx, "LookForBugsStart") -- YANMIRBASE.scr:242
    mm9.gosub(script, ctx, "EnableWandering") -- YANMIRBASE.scr:243
    do return ctx:exit("") end -- YANMIRBASE.scr:245
end

script.labels["Wipe"] = function(ctx)
    -- YANMIRBASE.scr:249
    -- wipe the crap off my shoe...
    ctx:self():playAnimation("Wipe", "WipeDone") -- YANMIRBASE.scr:254
    do return ctx:exit("") end -- YANMIRBASE.scr:255
end

script.labels["WipeDone"] = function(ctx)
    -- YANMIRBASE.scr:257
    ctx:self():stop() -- YANMIRBASE.scr:258
    ctx:set("nCurrentMarker", "markerSave") -- YANMIRBASE.scr:260
    -- subtract 1 from our current marker...
    ctx:state().nCurrentMarker = (tonumber(ctx:state().nCurrentMarker) or 0) - 1 -- YANMIRBASE.scr:264
    if ctx:condition("nCurrentMarker<0") then -- YANMIRBASE.scr:266
        ctx:set("nCurrentMarker", "nWanderPathCount - 1") -- YANMIRBASE.scr:267
    end -- YANMIRBASE.scr:268
    mm9.gosub(script, ctx, "EnableWandering") -- YANMIRBASE.scr:270
    do return ctx:exit("") end -- YANMIRBASE.scr:274
end

script.labels["BaseCrawlGetHim"] = function(ctx)
    -- YANMIRBASE.scr:277
    ctx:state().g_nDist = ctx:self():aiDistanceTo(ctx:object("g_hTarget")) -- YANMIRBASE.scr:279
    if ctx:condition("g_nDist < 720") then -- YANMIRBASE.scr:280
        ctx:state().g_hObject = ctx:objectOrNil("YanmirDoEQ") -- YANMIRBASE.scr:281
        ctx:state().g_nDist = ctx:self():aiDistanceTo(ctx:object("g_hObject")) -- YANMIRBASE.scr:282
        if ctx:condition("g_nDist < 400") then -- YANMIRBASE.scr:283
            ctx:state().g_nDist = ctx:object("g_hTarget"):distanceTo(ctx:object("g_hObject")) -- YANMIRBASE.scr:284
            if ctx:condition("g_nDist < 700") then -- YANMIRBASE.scr:285
                ctx:self():stop() -- YANMIRBASE.scr:286
                do return ctx:exit("") end -- YANMIRBASE.scr:287
            end -- YANMIRBASE.scr:288
        end -- YANMIRBASE.scr:289
    end -- YANMIRBASE.scr:290
    mm9.gosub(script, ctx, "BaseCrawlGetHim") -- YANMIRBASE.scr:292
    do return ctx:exit("") end -- YANMIRBASE.scr:294
end

script.labels["ShouldRunAfter"] = function(ctx)
    -- YANMIRBASE.scr:297
    if ctx:condition("bPlayerTargeted==FALSE") then -- YANMIRBASE.scr:300
        mm9.gosub(script, ctx, "ShouldRunAfter") -- YANMIRBASE.scr:301
    else -- YANMIRBASE.scr:302
        mm9.gosub(script, ctx, "ShouldRunAfter") -- YANMIRBASE.scr:303
    end -- YANMIRBASE.scr:304
    do return ctx:exit("") end -- YANMIRBASE.scr:306
end

script.labels["DoWipe"] = function(ctx)
    -- YANMIRBASE.scr:309
    -- Wipe off our shoe...
    ctx:self():stop() -- YANMIRBASE.scr:315
    mm9.gosub(script, ctx, "DisableWandering") -- YANMIRBASE.scr:316
    mm9.gosub(script, ctx, "Wipe") -- YANMIRBASE.scr:317
    do return ctx:exit("") end -- YANMIRBASE.scr:319
end

script.labels["OnTargetDead"] = function(ctx)
    -- YANMIRBASE.scr:322
    mm9.gosub(script, ctx, "ClearTarget") -- YANMIRBASE.scr:324
    ctx:getParam(0, "g_hObject") -- YANMIRBASE.scr:326
    if ctx:condition("g_hObject==g_hMyObject") then -- YANMIRBASE.scr:328
        mm9.gosub(script, ctx, "DisableWandering") -- YANMIRBASE.scr:329
        ctx:wait("TAUNT_WAIT", 0.2, "DoWipe") -- YANMIRBASE.scr:330
    end -- YANMIRBASE.scr:331
    do return ctx:exit("") end -- YANMIRBASE.scr:333
end

script.labels["OnAlert"] = function(ctx)
    -- YANMIRBASE.scr:336
    -- We don't respond to alerts...
    do return ctx:exit("") end -- YANMIRBASE.scr:341
end

script.labels["FollowPath"] = function(ctx)
    -- YANMIRBASE.scr:344
    ctx:state().nCurrentMarker = 18 -- YANMIRBASE.scr:347
    mm9.gosub(script, ctx, "ClearTarget") -- YANMIRBASE.scr:348
    do return ctx:exit("TRUE") end -- YANMIRBASE.scr:350
end

script.labels["OnPlayerRanAway"] = function(ctx)
    -- YANMIRBASE.scr:353
    if ctx:condition("g_hTarget==NULL") then -- YANMIRBASE.scr:356
        do return ctx:exit("") end -- YANMIRBASE.scr:357
    end -- YANMIRBASE.scr:358
    if ctx:condition("bPlayerTargeted==FALSE") then -- YANMIRBASE.scr:360
        do return ctx:exit("") end -- YANMIRBASE.scr:361
    end -- YANMIRBASE.scr:362
    mm9.gosub(script, ctx, "AggressiveStop") -- YANMIRBASE.scr:364
    mm9.gosub(script, ctx, "CheckRangeAttackStop") -- YANMIRBASE.scr:365
    ctx:self():stop() -- YANMIRBASE.scr:367
    ctx:state().g_hObject = ctx:objectOrNil("YanmirPathA18") -- YANMIRBASE.scr:369
    ctx:set("g_hTarget", "g_hObject") -- YANMIRBASE.scr:371
    ctx:self():setTarget(ctx:object("g_hObject")) -- YANMIRBASE.scr:372
    ctx:self():runTo(ctx:object("g_hObject"), 0, "FollowPath") -- YANMIRBASE.scr:374
    do return ctx:exit("") end -- YANMIRBASE.scr:376
end

script.labels["DoCamera"] = function(ctx)
    -- YANMIRBASE.scr:379
    -- See if we need to turn camera on..
    -- (ie: player is not somewhere where they can see the
    -- death sequence...)
    -- Note: I tagged all AIRails that are within viewing
    -- distance of the event with userdata 555.  I look for
    -- those and don't turn on the camera if the player is
    -- inside one....
    ctx:state().g_hObject = ctx:player() -- YANMIRBASE.scr:392
    ctx:state().g_hObject2 = ctx:object("g_hObject"):container(0) -- YANMIRBASE.scr:394
    ctx:state().g_bTemp = true -- YANMIRBASE.scr:396
    if ctx:condition("g_hObject2!=NULL") then -- YANMIRBASE.scr:398
        -- See what rail they are on.  If they're on
        -- one that's in this room, then don't turn
        -- camera on...
        ctx:state().g_nTemp = ctx:object("g_hObject2"):getStat("UserData") -- YANMIRBASE.scr:403
        if ctx:condition("g_nTemp==555") then -- YANMIRBASE.scr:405
            ctx:cprint("Player", "is", "within", "a", "viewable", "camera!!!") -- YANMIRBASE.scr:406
            do return ctx:exit("") end -- YANMIRBASE.scr:407
        end -- YANMIRBASE.scr:408
    end -- YANMIRBASE.scr:409
    ctx:object("YanmirCamera"):trigger("ON") -- YANMIRBASE.scr:411-412
    do return ctx:exit("") end -- YANMIRBASE.scr:414
end

script.labels["DestroyFloor"] = function(ctx)
    -- YANMIRBASE.scr:417
    ctx:object("YanDstruct0"):trigger("Destroy") -- YANMIRBASE.scr:420-421
    ctx:object("FallingFloor0"):trigger("Disappear") -- YANMIRBASE.scr:423-424
    do return ctx:exit("") end -- YANMIRBASE.scr:426
    -- GetObjectHandle EffectsMgr,g_hObject
    -- Trigger g_hObject,QuakeLong
    -- Trigger g_hObject,QuakeStrong
    -- Trigger g_hObject,StartScene
    do return ctx:exit("") end -- YANMIRBASE.scr:433
end

script.labels["OnTimeToDie"] = function(ctx)
    -- YANMIRBASE.scr:437
    ctx:getParam(0, "g_hObject") -- YANMIRBASE.scr:440
    if ctx:condition("g_hObject!=g_hMyObject") then -- YANMIRBASE.scr:442
        do return ctx:exit("") end -- YANMIRBASE.scr:443
    end -- YANMIRBASE.scr:444
    ctx:removeTrigger("TimeToDie") -- YANMIRBASE.scr:446
    mm9.gosub(script, ctx, "DoCamera") -- YANMIRBASE.scr:448
    ctx:object("CaveInDust1"):trigger("On") -- YANMIRBASE.scr:450-451
    ctx:object("CaveInDust2"):trigger("On") -- YANMIRBASE.scr:453-454
    ctx:object("CaveInDust3"):trigger("On") -- YANMIRBASE.scr:456-457
    ctx:wait(21, 2, "FallDown") -- YANMIRBASE.scr:459
    mm9.gosub(script, ctx, "BaseRunCancel") -- YANMIRBASE.scr:461
    mm9.gosub(script, ctx, "SpeedThrottleStop") -- YANMIRBASE.scr:462
    mm9.gosub(script, ctx, "AggressiveStop") -- YANMIRBASE.scr:463
    mm9.gosub(script, ctx, "AlertStop") -- YANMIRBASE.scr:464
    ctx:self():setTarget(nil) -- YANMIRBASE.scr:465
    ctx:onEvent("OnFoundTarget") -- YANMIRBASE.scr:466
    ctx:state().g_hTarget = nil -- YANMIRBASE.scr:467
    ctx:state().g_hObject = ctx:objectOrNil("YanmirPathA4") -- YANMIRBASE.scr:469
    if ctx:condition("g_hObject==NULL") then -- YANMIRBASE.scr:471
        ctx:cprint("Where", "is", "YanmirPathA4???") -- YANMIRBASE.scr:472
    else -- YANMIRBASE.scr:473
        ctx:self():runTo(ctx:object("g_hObject"), 0, "FallDown") -- YANMIRBASE.scr:474
    end -- YANMIRBASE.scr:475
    -- TL Added for Giving the key and the XP
    ctx:state().g_nPad2 = 8000 -- YANMIRBASE.scr:478
    mm9.gosub(script, ctx, "GiveEeps") -- YANMIRBASE.scr:479
    do return ctx:exit("") end -- YANMIRBASE.scr:481
end

script.labels["GiveEeps"] = function(ctx)
    -- YANMIRBASE.scr:484
end

-- (TL) gives the key and experience for killing Yanmir
script.labels[""] = function(ctx)
    -- YANMIRBASE.scr:486
    ctx:hasKey(69, "g_ntemp") -- YANMIRBASE.scr:488
    if ctx:condition("g_ntemp==FALSE") then -- YANMIRBASE.scr:490
        if ctx:hasKey(68) then -- YANMIRBASE.scr:491-492
            ctx:giveKey("", 69) -- YANMIRBASE.scr:493
            ctx:giveExp("g_nPad2") -- YANMIRBASE.scr:494
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- YANMIRBASE.scr:495
            do return ctx:exit("") end -- YANMIRBASE.scr:496
        end -- YANMIRBASE.scr:497
    end -- YANMIRBASE.scr:498
    -- did it when not on the quest
    if not ctx:hasKey(173) then -- YANMIRBASE.scr:502-503
        ctx:giveKey("", 173) -- YANMIRBASE.scr:504
        ctx:giveExp("g_nPad2") -- YANMIRBASE.scr:505
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- YANMIRBASE.scr:506
        do return ctx:exit("") end -- YANMIRBASE.scr:507
    end -- YANMIRBASE.scr:508
    do return ctx:exit("") end -- YANMIRBASE.scr:509
end

script.labels["Main"] = function(ctx)
    -- YANMIRBASE.scr:513
    mm9.gosub(script, ctx, "BaseCrawlInit") -- YANMIRBASE.scr:516
    mm9.gosub(script, ctx, "RangeInit") -- YANMIRBASE.scr:517
    ctx:addModelKey("OpenDoor", "OpenDoor") -- YANMIRBASE.scr:519
    ctx:addModelKey("DestroyFloor", "DestroyFloor") -- YANMIRBASE.scr:520
    ctx:onEvent("OnStuck", "OnStuck") -- YANMIRBASE.scr:522
    ctx:onEvent("OnLostTarget", "GiveupOnTarget") -- YANMIRBASE.scr:523
    mm9.gosub(script, ctx, "DisableWandering") -- YANMIRBASE.scr:525
    ctx:addTrigger("Squish", "Begin") -- YANMIRBASE.scr:526
    ctx:addTrigger("PlayerRanAway", "OnPlayerRanAway") -- YANMIRBASE.scr:527
    ctx:addTrigger("TimeToDie", "OnTimeToDie") -- YANMIRBASE.scr:528
    ctx:addTrigger("DestroyFloor", "DestroyFloor") -- YANMIRBASE.scr:529
    ctx:onEvent("OnPostMiniSaveLoad", "Reset") -- YANMIRBASE.scr:531
    ctx:onEvent("OnPostSaveLoad", "Reset") -- YANMIRBASE.scr:532
    mm9.gosub(script, ctx, "Reset") -- YANMIRBASE.scr:533
    do return ctx:exit("") end -- YANMIRBASE.scr:535
end

script.labels["OnDeath"] = function(ctx)
    -- YANMIRBASE.scr:539
    -- overloaded -- Bones
    ctx:state().g_nPad2 = 5000 -- YANMIRBASE.scr:543
    mm9.gosub(script, ctx, "GiveEeps") -- YANMIRBASE.scr:544
    mm9.gosub(script, ctx, "OnDeath") -- YANMIRBASE.scr:545
    do return ctx:exit("") end -- YANMIRBASE.scr:546
end

script.labels["Reset"] = function(ctx)
    -- YANMIRBASE.scr:549
    -- Bones
    ctx:self():setNumberProperty("CanDamage", "FALSE") -- YANMIRBASE.scr:553
    do return ctx:exit("") end -- YANMIRBASE.scr:554
end

return script
