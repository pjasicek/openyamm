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
    ctx:command("wait", "25, 3, LookForBugsTick") -- YANMIRBASE.scr:25
    do return ctx:exit("") end -- YANMIRBASE.scr:26
end

script.labels["LookForBugsTick"] = function(ctx)
    -- YANMIRBASE.scr:29
    ctx:command("getrandomfloat", "0.5,2,g_nRandom") -- YANMIRBASE.scr:34
    ctx:command("wait", "25, g_nRandom, LookForBugsTick") -- YANMIRBASE.scr:35
    ctx:command("gettarget", "g_hObject") -- YANMIRBASE.scr:37
    if ctx:condition("g_hObject!=NULL") then -- YANMIRBASE.scr:39
        do return ctx:exit("") end -- YANMIRBASE.scr:40
    end -- YANMIRBASE.scr:41
    ctx:command("getobjects", "IceLobbercicle,500,20,bugArray,bugCount") -- YANMIRBASE.scr:43
    if ctx:condition("bugCount==0") then -- YANMIRBASE.scr:45
        do return ctx:exit("") end -- YANMIRBASE.scr:46
    end -- YANMIRBASE.scr:47
    ctx:command("sub", "bugCount,1") -- YANMIRBASE.scr:49
    ctx:command("getrandomint", "0,bugCount,g_nRandom") -- YANMIRBASE.scr:50
    ctx:command("arrayget", "bugArray,g_nRandom,g_hTarget") -- YANMIRBASE.scr:52
    ctx:command("isvisible", "g_hTarget,g_bTemp") -- YANMIRBASE.scr:54
    if ctx:condition("g_bTemp==FALSE") then -- YANMIRBASE.scr:56
        ctx:command("g_htarget", "= NULL") -- YANMIRBASE.scr:57
        do return ctx:exit("") end -- YANMIRBASE.scr:58
    end -- YANMIRBASE.scr:59
    ctx:command("stop", "") -- YANMIRBASE.scr:61
    ctx:command("markersave", "= nCurrentMarker") -- YANMIRBASE.scr:63
    ctx:command("nbugattempts", "= 0") -- YANMIRBASE.scr:65
    mm9.gosub(script, ctx, "SetupTarget") -- YANMIRBASE.scr:66
    mm9.gosub(script, ctx, "AggressiveStart") -- YANMIRBASE.scr:67
    do return ctx:exit("") end -- YANMIRBASE.scr:69
end

script.labels["AttackDone"] = function(ctx)
    -- YANMIRBASE.scr:72
    mm9.gosub(script, ctx, "AttackDone") -- YANMIRBASE.scr:74
    if ctx:condition("bPlayerTargeted==FALSE") then -- YANMIRBASE.scr:76
        ctx:command("add", "nBugAttempts,1") -- YANMIRBASE.scr:77
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
    ctx:command("isplayer", "g_hTarget,bPlayerTargeted") -- YANMIRBASE.scr:99
    if ctx:condition("bPlayerTargeted==TRUE") then -- YANMIRBASE.scr:101
        ctx:command("max_chase_time", "= 45") -- YANMIRBASE.scr:102
    else -- YANMIRBASE.scr:103
        ctx:command("max_chase_time", "= 15") -- YANMIRBASE.scr:104
    end -- YANMIRBASE.scr:105
    do return mm9.gotoLabel(script, ctx, "SetupTarget") end -- YANMIRBASE.scr:107
    do return ctx:exit("") end -- YANMIRBASE.scr:109
end

script.labels["LookForBugsStop"] = function(ctx)
    -- YANMIRBASE.scr:112
    ctx:command("wait", "25, 0, DoNothing") -- YANMIRBASE.scr:114
    do return ctx:exit("") end -- YANMIRBASE.scr:115
end

script.labels["TargetPlayer"] = function(ctx)
    -- YANMIRBASE.scr:119
    ctx:command("getplayerhandle", "g_hTarget") -- YANMIRBASE.scr:121
    if ctx:condition("g_hTarget==NULL") then -- YANMIRBASE.scr:122
        ctx:command("wait", "29,0.1,TargetPlayer") -- YANMIRBASE.scr:123
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
    ctx:command("playsound", "Sounds\\Door\\stonedoorslam.wav, DoNothing, 1000, 3500, FALSE, 100") -- YANMIRBASE.scr:141
    ctx:command("getobjecthandle", "YanmirDust,hDust") -- YANMIRBASE.scr:142
    ctx:command("getsocketpos", "Rfoot,g_posX,g_posY,g_posZ") -- YANMIRBASE.scr:143
    ctx:command("setpos", "hDust,g_posX,g_posY,g_posZ") -- YANMIRBASE.scr:144
    ctx:trigger("hDust", "ON") -- YANMIRBASE.scr:145
    ctx:command("wait", "28, .25, TurnDustOff") -- YANMIRBASE.scr:146
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
    ctx:command("playanim", "KickDoor, KickDoorDone") -- YANMIRBASE.scr:169
    do return ctx:exit("") end -- YANMIRBASE.scr:171
end

script.labels["BD_OnDoor"] = function(ctx)
    -- YANMIRBASE.scr:174
    ctx:getParam(0, "g_hDoor") -- YANMIRBASE.scr:177
    ctx:command("getstat", "g_hDoor,IsClosed,g_bTemp") -- YANMIRBASE.scr:179
    if ctx:condition("g_bTemp==FALSE") then -- YANMIRBASE.scr:181
        -- door is not closed, ignore....
        do return ctx:exit("FALSE") end -- YANMIRBASE.scr:183
    end -- YANMIRBASE.scr:184
    mm9.gosub(script, ctx, "KickDoor") -- YANMIRBASE.scr:186
    ctx:command("savepath", "") -- YANMIRBASE.scr:188
    ctx:command("g_bdooropening", "= TRUE") -- YANMIRBASE.scr:190
    do return ctx:exit("TRUE") end -- YANMIRBASE.scr:193
end

script.labels["SpeedThrottleStart"] = function(ctx)
    -- YANMIRBASE.scr:196
    -- None for me thanks.
    do return ctx:exit("") end -- YANMIRBASE.scr:200
end

script.labels["DoFall"] = function(ctx)
    -- YANMIRBASE.scr:203
    ctx:command("loopanim", "Fall,0") -- YANMIRBASE.scr:205
    do return ctx:exit("") end -- YANMIRBASE.scr:207
end

script.labels["FallDown"] = function(ctx)
    -- YANMIRBASE.scr:211
    -- Time to do our fall down animation...
    ctx:command("wait", "21, 0, DoNothing") -- YANMIRBASE.scr:217
    ctx:command("stop", "") -- YANMIRBASE.scr:219
    mm9.gosub(script, ctx, "ClearTarget") -- YANMIRBASE.scr:220
    -- Make sure we're uninterested in looking for any targets...
    ctx:command("onfoundtarget", "") -- YANMIRBASE.scr:225
    ctx:command("ondamage", "") -- YANMIRBASE.scr:226
    ctx:command("onalert", "") -- YANMIRBASE.scr:227
    ctx:command("ondamagedone", "") -- YANMIRBASE.scr:228
    ctx:command("onprojectile", "") -- YANMIRBASE.scr:229
    mm9.gosub(script, ctx, "LookForBugsStop") -- YANMIRBASE.scr:231
    ctx:command("playanim", "startDie,DoFall") -- YANMIRBASE.scr:233
    do return ctx:exit("") end -- YANMIRBASE.scr:235
end

script.labels["Begin"] = function(ctx)
    -- YANMIRBASE.scr:238
    ctx:command("removetrigger", "Squish") -- YANMIRBASE.scr:240
    mm9.gosub(script, ctx, "LookForBugsStart") -- YANMIRBASE.scr:242
    mm9.gosub(script, ctx, "EnableWandering") -- YANMIRBASE.scr:243
    do return ctx:exit("") end -- YANMIRBASE.scr:245
end

script.labels["Wipe"] = function(ctx)
    -- YANMIRBASE.scr:249
    -- wipe the crap off my shoe...
    ctx:command("playanim", "Wipe, WipeDone") -- YANMIRBASE.scr:254
    do return ctx:exit("") end -- YANMIRBASE.scr:255
end

script.labels["WipeDone"] = function(ctx)
    -- YANMIRBASE.scr:257
    ctx:command("stop", "") -- YANMIRBASE.scr:258
    ctx:command("ncurrentmarker", "= markerSave") -- YANMIRBASE.scr:260
    -- subtract 1 from our current marker...
    ctx:command("sub", "nCurrentMarker,1") -- YANMIRBASE.scr:264
    if ctx:condition("nCurrentMarker<0") then -- YANMIRBASE.scr:266
        ctx:command("ncurrentmarker", "= nWanderPathCount - 1") -- YANMIRBASE.scr:267
    end -- YANMIRBASE.scr:268
    mm9.gosub(script, ctx, "EnableWandering") -- YANMIRBASE.scr:270
    do return ctx:exit("") end -- YANMIRBASE.scr:274
end

script.labels["BaseCrawlGetHim"] = function(ctx)
    -- YANMIRBASE.scr:277
    ctx:command("aigetdistance", "g_hTarget,g_nDist") -- YANMIRBASE.scr:279
    if ctx:condition("g_nDist < 720") then -- YANMIRBASE.scr:280
        ctx:command("getobjecthandle", "YanmirDoEQ,g_hObject") -- YANMIRBASE.scr:281
        ctx:command("aigetdistance", "g_hObject,g_nDist") -- YANMIRBASE.scr:282
        if ctx:condition("g_nDist < 400") then -- YANMIRBASE.scr:283
            ctx:command("getdistance", "g_hTarget,g_hObject,g_nDist") -- YANMIRBASE.scr:284
            if ctx:condition("g_nDist < 700") then -- YANMIRBASE.scr:285
                ctx:command("stop", "") -- YANMIRBASE.scr:286
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
    ctx:command("stop", "") -- YANMIRBASE.scr:315
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
        ctx:command("wait", "TAUNT_WAIT,0.2,DoWipe") -- YANMIRBASE.scr:330
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
    ctx:command("ncurrentmarker", "= 18") -- YANMIRBASE.scr:347
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
    ctx:command("stop", "") -- YANMIRBASE.scr:367
    ctx:command("getobjecthandle", "YanmirPathA18,g_hObject") -- YANMIRBASE.scr:369
    ctx:command("g_htarget", "= g_hObject") -- YANMIRBASE.scr:371
    ctx:command("target", "g_hObject,TRUE") -- YANMIRBASE.scr:372
    ctx:command("runto", "g_hObject, 0, FollowPath") -- YANMIRBASE.scr:374
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
    ctx:command("getplayerhandle", "g_hObject") -- YANMIRBASE.scr:392
    ctx:command("getcontainer", "g_hObject,0,g_hObject2") -- YANMIRBASE.scr:394
    ctx:command("g_btemp", "= TRUE") -- YANMIRBASE.scr:396
    if ctx:condition("g_hObject2!=NULL") then -- YANMIRBASE.scr:398
        -- See what rail they are on.  If they're on
        -- one that's in this room, then don't turn
        -- camera on...
        ctx:command("getstat", "g_hObject2,UserData,g_nTemp") -- YANMIRBASE.scr:403
        if ctx:condition("g_nTemp==555") then -- YANMIRBASE.scr:405
            ctx:command("cprint", "Player is within a viewable camera!!!") -- YANMIRBASE.scr:406
            do return ctx:exit("") end -- YANMIRBASE.scr:407
        end -- YANMIRBASE.scr:408
    end -- YANMIRBASE.scr:409
    ctx:command("getobjecthandle", "YanmirCamera,g_hObject") -- YANMIRBASE.scr:411
    ctx:trigger("g_hObject", "ON") -- YANMIRBASE.scr:412
    do return ctx:exit("") end -- YANMIRBASE.scr:414
end

script.labels["DestroyFloor"] = function(ctx)
    -- YANMIRBASE.scr:417
    ctx:command("getobjecthandle", "YanDstruct0,g_hObject") -- YANMIRBASE.scr:420
    ctx:trigger("g_hObject", "Destroy") -- YANMIRBASE.scr:421
    ctx:command("getobjecthandle", "FallingFloor0,g_hObject") -- YANMIRBASE.scr:423
    ctx:trigger("g_hObject", "Disappear") -- YANMIRBASE.scr:424
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
    ctx:command("removetrigger", "TimeToDie") -- YANMIRBASE.scr:446
    mm9.gosub(script, ctx, "DoCamera") -- YANMIRBASE.scr:448
    ctx:command("getobjecthandle", "CaveInDust1,g_hObject") -- YANMIRBASE.scr:450
    ctx:trigger("g_hObject", "On") -- YANMIRBASE.scr:451
    ctx:command("getobjecthandle", "CaveInDust2,g_hObject") -- YANMIRBASE.scr:453
    ctx:trigger("g_hObject", "On") -- YANMIRBASE.scr:454
    ctx:command("getobjecthandle", "CaveInDust3,g_hObject") -- YANMIRBASE.scr:456
    ctx:trigger("g_hObject", "On") -- YANMIRBASE.scr:457
    ctx:command("wait", "21, 2, FallDown") -- YANMIRBASE.scr:459
    mm9.gosub(script, ctx, "BaseRunCancel") -- YANMIRBASE.scr:461
    mm9.gosub(script, ctx, "SpeedThrottleStop") -- YANMIRBASE.scr:462
    mm9.gosub(script, ctx, "AggressiveStop") -- YANMIRBASE.scr:463
    mm9.gosub(script, ctx, "AlertStop") -- YANMIRBASE.scr:464
    ctx:command("target", "NULL") -- YANMIRBASE.scr:465
    ctx:command("onfoundtarget", "") -- YANMIRBASE.scr:466
    ctx:command("g_htarget", "= NULL") -- YANMIRBASE.scr:467
    ctx:command("getobjecthandle", "YanmirPathA4,g_hObject") -- YANMIRBASE.scr:469
    if ctx:condition("g_hObject==NULL") then -- YANMIRBASE.scr:471
        ctx:command("cprint", "Where is YanmirPathA4???") -- YANMIRBASE.scr:472
    else -- YANMIRBASE.scr:473
        ctx:command("runto", "g_hObject,0,FallDown") -- YANMIRBASE.scr:474
    end -- YANMIRBASE.scr:475
    -- TL Added for Giving the key and the XP
    ctx:command("set", "g_nPad2 8000") -- YANMIRBASE.scr:478
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
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- YANMIRBASE.scr:495
            do return ctx:exit("") end -- YANMIRBASE.scr:496
        end -- YANMIRBASE.scr:497
    end -- YANMIRBASE.scr:498
    -- did it when not on the quest
    if not ctx:hasKey(173) then -- YANMIRBASE.scr:502-503
        ctx:giveKey("", 173) -- YANMIRBASE.scr:504
        ctx:giveExp("g_nPad2") -- YANMIRBASE.scr:505
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- YANMIRBASE.scr:506
        do return ctx:exit("") end -- YANMIRBASE.scr:507
    end -- YANMIRBASE.scr:508
    do return ctx:exit("") end -- YANMIRBASE.scr:509
end

script.labels["Main"] = function(ctx)
    -- YANMIRBASE.scr:513
    mm9.gosub(script, ctx, "BaseCrawlInit") -- YANMIRBASE.scr:516
    mm9.gosub(script, ctx, "RangeInit") -- YANMIRBASE.scr:517
    ctx:command("addmodelkey", "OpenDoor,OpenDoor") -- YANMIRBASE.scr:519
    ctx:command("addmodelkey", "DestroyFloor,DestroyFloor") -- YANMIRBASE.scr:520
    ctx:command("onstuck", "OnStuck") -- YANMIRBASE.scr:522
    ctx:command("onlosttarget", "GiveupOnTarget") -- YANMIRBASE.scr:523
    mm9.gosub(script, ctx, "DisableWandering") -- YANMIRBASE.scr:525
    ctx:addTrigger("Squish", "Begin") -- YANMIRBASE.scr:526
    ctx:addTrigger("PlayerRanAway", "OnPlayerRanAway") -- YANMIRBASE.scr:527
    ctx:addTrigger("TimeToDie", "OnTimeToDie") -- YANMIRBASE.scr:528
    ctx:addTrigger("DestroyFloor", "DestroyFloor") -- YANMIRBASE.scr:529
    ctx:command("onpostminisaveload", "Reset") -- YANMIRBASE.scr:531
    ctx:command("onpostsaveload", "Reset") -- YANMIRBASE.scr:532
    mm9.gosub(script, ctx, "Reset") -- YANMIRBASE.scr:533
    do return ctx:exit("") end -- YANMIRBASE.scr:535
end

script.labels["OnDeath"] = function(ctx)
    -- YANMIRBASE.scr:539
    -- overloaded -- Bones
    ctx:command("set", "g_nPad2 5000") -- YANMIRBASE.scr:543
    mm9.gosub(script, ctx, "GiveEeps") -- YANMIRBASE.scr:544
    mm9.gosub(script, ctx, "OnDeath") -- YANMIRBASE.scr:545
    do return ctx:exit("") end -- YANMIRBASE.scr:546
end

script.labels["Reset"] = function(ctx)
    -- YANMIRBASE.scr:549
    -- Bones
    ctx:setPropNumber("CanDamage", "FALSE") -- YANMIRBASE.scr:553
    do return ctx:exit("") end -- YANMIRBASE.scr:554
end

return script
