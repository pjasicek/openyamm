-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPCBASE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 20, path = "basewander.inc" }
script.includes[#script.includes + 1] = { line = 21, path = "baserun.inc" }

-- NPCBASE.INC
-- Jeff Leggett
-- 08/09/2001
-- Behavior:
-- - Wander around using basewander script.  If the USE
-- key is used on us, then this script will be paused.
-- And the RUDE system will take over....
-- - If projectiles have been used near us, or we've been
-- damaged, then we'll run away from the attacker.
-- - Occasionally, we'll look for another NPC to walk over
-- and talk to.
-- How fast / often to look for someone to chat with?
-- #number				MAX_SOCIALIZE_WAIT = 60
-- #number				MIN_SOCIALIZE_WAIT = 15
-- Once you are looking, how long to look for?
-- Now that you're chatting, how long to chat for?
script.labels["EnableWandering"] = function(ctx)
    -- NPCBASE.inc:52
    -- Do all things necessary to enable
    -- Wandering...
    mm9.gosub(script, ctx, "BaseWanderStart") -- NPCBASE.inc:59
    do return ctx:exit("") end -- NPCBASE.inc:61
end

script.labels["DisableWandering"] = function(ctx)
    -- NPCBASE.inc:64
    mm9.gosub(script, ctx, "BaseWanderStop") -- NPCBASE.inc:66
    ctx:command("onobstacle", "") -- NPCBASE.inc:67
    ctx:command("onstuckdone", "") -- NPCBASE.inc:68
    ctx:command("onstuck", "") -- NPCBASE.inc:69
    do return ctx:exit("") end -- NPCBASE.inc:71
end

script.labels["CancelChat"] = function(ctx)
    -- NPCBASE.inc:75
    ctx:command("gettarget", "g_hTarget") -- NPCBASE.inc:78
    if ctx:condition("g_hTarget!=NULL") then -- NPCBASE.inc:80
        ctx:trigger("g_hTarget", "GoodBye") -- NPCBASE.inc:81
    end -- NPCBASE.inc:82
    ctx:command("g_bchatting", "= FALSE") -- NPCBASE.inc:84
    ctx:command("target", "NULL") -- NPCBASE.inc:86
    ctx:command("g_htarget", "= NULL") -- NPCBASE.inc:87
    ctx:command("wait", "SOCIALIZE_WAIT, 0, DoNothing") -- NPCBASE.inc:90
    do return ctx:exit("") end -- NPCBASE.inc:92
end

script.labels["EnableChat"] = function(ctx)
    -- NPCBASE.inc:95
    ctx:command("g_bchatenabled", "= TRUE") -- NPCBASE.inc:98
    if ctx:condition("g_bSocializeEnabled==TRUE") then -- NPCBASE.inc:100
        mm9.gosub(script, ctx, "SetupNextChat") -- NPCBASE.inc:101
    end -- NPCBASE.inc:102
    do return ctx:exit("") end -- NPCBASE.inc:104
end

script.labels["DisableChat"] = function(ctx)
    -- NPCBASE.inc:108
    mm9.gosub(script, ctx, "CancelChat") -- NPCBASE.inc:111
    mm9.gosub(script, ctx, "LookForPersonOff") -- NPCBASE.inc:112
    ctx:command("g_bchatenabled", "= FALSE") -- NPCBASE.inc:113
    do return ctx:exit("") end -- NPCBASE.inc:115
end

script.labels["OnGoToLocArrival"] = function(ctx)
    -- NPCBASE.inc:119
    ctx:command("current_marker", "= NULL") -- NPCBASE.inc:123
    ctx:command("stop", "") -- NPCBASE.inc:124
    ctx:command("setidle", "") -- NPCBASE.inc:125
    mm9.gosub(script, ctx, "EnableChat") -- NPCBASE.inc:127
    mm9.gosub(script, ctx, "EnableWandering") -- NPCBASE.inc:128
    ctx:trigger("g_hObject", "HasArrived") -- NPCBASE.inc:129
    do return ctx:exit("") end -- NPCBASE.inc:131
end

script.labels["OnWarpToLoc"] = function(ctx)
    -- NPCBASE.inc:134
    mm9.gosub(script, ctx, "DisableWandering") -- NPCBASE.inc:139
    mm9.gosub(script, ctx, "DisableChat") -- NPCBASE.inc:140
    ctx:command("stop", "") -- NPCBASE.inc:141
    ctx:command("setidle", "") -- NPCBASE.inc:142
    ctx:command("getstatstr", "g_hMyObject, PARAM, dest") -- NPCBASE.inc:144
    ctx:command("getobjecthandle", "dest, current_marker") -- NPCBASE.inc:145
    ctx:command("getpos", "current_marker, current_marker_xpos, current_marker_ypos, current_marker_zpos") -- NPCBASE.inc:146
    ctx:command("setpos", "g_hMyObject, current_marker_xpos, current_marker_ypos, current_marker_zpos") -- NPCBASE.inc:147
    mm9.gosub(script, ctx, "OnGoToLocArrival") -- NPCBASE.inc:148
    do return ctx:exit("") end -- NPCBASE.inc:150
end

script.labels["OnGoToLoc"] = function(ctx)
    -- NPCBASE.inc:153
    mm9.gosub(script, ctx, "DisableWandering") -- NPCBASE.inc:156
    mm9.gosub(script, ctx, "DisableChat") -- NPCBASE.inc:157
    ctx:command("stop", "") -- NPCBASE.inc:159
    ctx:command("setidle", "") -- NPCBASE.inc:160
    ctx:command("getstatstr", "g_hMyObject, PARAM, dest") -- NPCBASE.inc:162
    ctx:command("getobjecthandle", "dest, current_marker") -- NPCBASE.inc:163
    ctx:command("walkto", "current_marker, 0, OnGoToLocArrival") -- NPCBASE.inc:164
    do return ctx:exit("") end -- NPCBASE.inc:166
end

script.labels["BuggerOff"] = function(ctx)
    -- NPCBASE.inc:169
    -- Assumes g_hObject is filled with someone attempting to
    -- chat with us...
    ctx:command("debugout", "BuggerOff!!!") -- NPCBASE.inc:176
    ctx:trigger("g_hObject", "LeaveMeAlone") -- NPCBASE.inc:178
    do return ctx:exit("") end -- NPCBASE.inc:180
end

script.labels["OnHello"] = function(ctx)
    -- NPCBASE.inc:183
    -- p0 - handle of trigger sender...
    -- DebugOut OnHello
    ctx:getParam(0, "g_hObject") -- NPCBASE.inc:190
    ctx:command("gettarget", "g_hTarget") -- NPCBASE.inc:191
    if ctx:condition("g_bChatEnabled==FALSE") then -- NPCBASE.inc:193
        mm9.gosub(script, ctx, "BuggerOff") -- NPCBASE.inc:194
        do return ctx:exit("") end -- NPCBASE.inc:195
    end -- NPCBASE.inc:196
    if ctx:condition("g_hTarget!=NULL") then -- NPCBASE.inc:198
        if ctx:condition("g_hTarget!=g_hObject") then -- NPCBASE.inc:199
            mm9.gosub(script, ctx, "BuggerOff") -- NPCBASE.inc:200
            do return ctx:exit("") end -- NPCBASE.inc:201
        end -- NPCBASE.inc:202
    end -- NPCBASE.inc:203
    ctx:command("g_bchatting", "= TRUE") -- NPCBASE.inc:205
    mm9.gosub(script, ctx, "LookForPersonOff") -- NPCBASE.inc:207
    ctx:command("set", "g_hTarget, g_hObject") -- NPCBASE.inc:209
    ctx:command("target", "g_hTarget, FALSE") -- NPCBASE.inc:210
    ctx:trigger("g_hTarget", "LetsTalk") -- NPCBASE.inc:212
    mm9.gosub(script, ctx, "DisableWandering") -- NPCBASE.inc:214
    ctx:command("stop", "") -- NPCBASE.inc:215
    ctx:command("setidle", "") -- NPCBASE.inc:216
    ctx:command("wait", "SOCIALIZE_WAIT, 20, OnChatGiveUp") -- NPCBASE.inc:218
    do return ctx:exit("") end -- NPCBASE.inc:220
end

script.labels["OnGoodBye"] = function(ctx)
    -- NPCBASE.inc:223
    -- DebugOut OnGoodBye
    ctx:command("gettarget", "g_hTarget") -- NPCBASE.inc:228
    ctx:getParam(0, "g_hObject") -- NPCBASE.inc:230
    if ctx:condition("g_hTarget!=g_hObject") then -- NPCBASE.inc:232
        do return ctx:exit("") end -- NPCBASE.inc:233
    end -- NPCBASE.inc:234
    ctx:command("g_bchatting", "= FALSE") -- NPCBASE.inc:236
    mm9.gosub(script, ctx, "SetupNextChat") -- NPCBASE.inc:238
    mm9.gosub(script, ctx, "LeaveChat") -- NPCBASE.inc:239
    do return ctx:exit("") end -- NPCBASE.inc:241
end

script.labels["OnChatGiveUp"] = function(ctx)
    -- NPCBASE.inc:244
    -- Give up waiting after sending / receiving the Hello message
    -- DebugOut OnChatGiveUP
    mm9.gosub(script, ctx, "CancelChat") -- NPCBASE.inc:251
    mm9.gosub(script, ctx, "SetupNextChat") -- NPCBASE.inc:252
    do return ctx:exit("") end -- NPCBASE.inc:254
end

script.labels["OnConverseDone"] = function(ctx)
    -- NPCBASE.inc:257
    -- DebugOut OnConverseDone
    ctx:command("setidle", "") -- NPCBASE.inc:261
    if ctx:condition("g_bChatting==TRUE") then -- NPCBASE.inc:263
        ctx:trigger("g_hTarget", "YourTurn") -- NPCBASE.inc:264
    end -- NPCBASE.inc:265
    do return ctx:exit("") end -- NPCBASE.inc:267
end

script.labels["OnChatBegin"] = function(ctx)
    -- NPCBASE.inc:271
    -- Stop and look at the guy who's talking to us...
    -- DebugOut OnChatBegin
    ctx:getParam(0, "g_hObject") -- NPCBASE.inc:279
    ctx:command("gettarget", "g_hTarget") -- NPCBASE.inc:280
    if ctx:condition("g_hTarget!=NULL") then -- NPCBASE.inc:282
        if ctx:condition("g_hObject!=g_hTarget") then -- NPCBASE.inc:284
            ctx:trigger("g_hObject", "LeaveMeAlone") -- NPCBASE.inc:285
        end -- NPCBASE.inc:286
    end -- NPCBASE.inc:288
    ctx:command("g_bchatting", "= TRUE") -- NPCBASE.inc:290
    mm9.gosub(script, ctx, "DisableWandering") -- NPCBASE.inc:292
    ctx:command("stop", "") -- NPCBASE.inc:294
    ctx:command("setidle", "") -- NPCBASE.inc:295
    ctx:command("set", "g_hTarget, g_hObject") -- NPCBASE.inc:297
    ctx:command("target", "g_hTarget, FALSE") -- NPCBASE.inc:298
    ctx:command("faceobject", "g_hTarget, 180") -- NPCBASE.inc:300
    ctx:command("wait", "SOCIALIZE_WAIT, 0, DoNothing") -- NPCBASE.inc:302
    do return ctx:exit("") end -- NPCBASE.inc:305
end

script.labels["OnLookAtMe"] = function(ctx)
    -- NPCBASE.inc:308
    -- p0 - who triggered us.
    -- Useful for certain things....
    ctx:getParam(0, "g_hObject") -- NPCBASE.inc:315
    ctx:command("ismoving", "g_bTemp") -- NPCBASE.inc:317
    if ctx:condition("g_bTemp==TRUE") then -- NPCBASE.inc:318
        do return ctx:exit("") end -- NPCBASE.inc:319
    end -- NPCBASE.inc:320
    if ctx:condition("g_hTarget!=NULL") then -- NPCBASE.inc:322
        if ctx:condition("g_hTarget!=g_hObject") then -- NPCBASE.inc:323
            do return ctx:exit("") end -- NPCBASE.inc:324
        end -- NPCBASE.inc:325
    end -- NPCBASE.inc:326
    ctx:command("faceobject", "g_hObject, 180") -- NPCBASE.inc:328
    do return ctx:exit("") end -- NPCBASE.inc:330
end

script.labels["EndChat"] = function(ctx)
    -- NPCBASE.inc:333
    -- DebugOut EndChat
    mm9.gosub(script, ctx, "CancelChat") -- NPCBASE.inc:338
    mm9.gosub(script, ctx, "SetupNextChat") -- NPCBASE.inc:339
    mm9.gosub(script, ctx, "LeaveChat") -- NPCBASE.inc:340
    do return ctx:exit("") end -- NPCBASE.inc:342
end

script.labels["LeaveChat"] = function(ctx)
    -- NPCBASE.inc:346
    ctx:command("g_bchatting", "= FALSE") -- NPCBASE.inc:349
    ctx:command("getfacedir", "g_hMyObject, g_dirX, g_dirY, g_dirZ") -- NPCBASE.inc:351
    ctx:command("rotatedir", "g_dirX, g_dirY, g_dirZ, 180") -- NPCBASE.inc:352
    ctx:command("getrandomfloat", "-45, 45, g_nRandom") -- NPCBASE.inc:354
    ctx:command("rotatedir", "g_dirX, g_dirY, g_dirZ, g_nRandom") -- NPCBASE.inc:355
    if ctx:condition("current_marker==NULL") then -- NPCBASE.inc:357
        ctx:command("facedir", "g_dirX, g_dirY, g_dirZ, 180, AboutFaceDone") -- NPCBASE.inc:358
    end -- NPCBASE.inc:359
    if ctx:condition("current_marker!=NULL") then -- NPCBASE.inc:361
        ctx:command("walkto", "current_marker, 0, OnGoToLocArrival") -- NPCBASE.inc:362
    end -- NPCBASE.inc:363
    do return ctx:exit("") end -- NPCBASE.inc:365
end

script.labels["AboutFaceDone"] = function(ctx)
    -- NPCBASE.inc:368
    mm9.gosub(script, ctx, "BaseWanderGo") -- NPCBASE.inc:370
    do return ctx:exit("") end -- NPCBASE.inc:371
end

script.labels["OnChatArrival"] = function(ctx)
    -- NPCBASE.inc:374
    ctx:command("stop", "") -- NPCBASE.inc:376
    ctx:command("setidle", "") -- NPCBASE.inc:377
    ctx:trigger("g_hTarget", "ChatBegin") -- NPCBASE.inc:378
    ctx:command("converse", "-1, OnConverseDone") -- NPCBASE.inc:379
    ctx:command("getrandomint", "CHAT_MIN, CHAT_MAX, g_nRandom") -- NPCBASE.inc:381
    ctx:command("wait", "SOCIALIZE_WAIT, g_nRandom, EndChat") -- NPCBASE.inc:382
    do return ctx:exit("") end -- NPCBASE.inc:384
end

script.labels["GoChat"] = function(ctx)
    -- NPCBASE.inc:388
    -- Walk to our target and begin the chit-chat process....
    ctx:command("target", "g_hTarget, TRUE") -- NPCBASE.inc:393
    mm9.gosub(script, ctx, "DisableWandering") -- NPCBASE.inc:394
    ctx:command("walkto", "g_hTarget, 0, OnChatArrival") -- NPCBASE.inc:395
    ctx:command("g_bchatting", "= TRUE") -- NPCBASE.inc:397
    ctx:command("getrandomfloat", "4,10,g_nRandom") -- NPCBASE.inc:399
    ctx:command("wait", "SOCIALIZE_WAIT, g_nRandom, OnChatGiveUp") -- NPCBASE.inc:401
    do return ctx:exit("") end -- NPCBASE.inc:403
end

script.labels["OnLetsTalk"] = function(ctx)
    -- NPCBASE.inc:406
    -- p0 - handle of trigger sender...
    ctx:getParam(0, "g_hObject") -- NPCBASE.inc:410
    if ctx:condition("g_hObject!=g_hTarget") then -- NPCBASE.inc:412
        ctx:trigger("g_hObject", "LeaveMeAlone") -- NPCBASE.inc:413
        do return ctx:exit("") end -- NPCBASE.inc:414
    end -- NPCBASE.inc:415
    mm9.gosub(script, ctx, "GoChat") -- NPCBASE.inc:417
    do return ctx:exit("") end -- NPCBASE.inc:419
end

script.labels["OnLeaveMeAlone"] = function(ctx)
    -- NPCBASE.inc:422
    -- p0 - handle of trigger sender...
    ctx:getParam(0, "g_hObject") -- NPCBASE.inc:426
    if ctx:condition("g_hObject!=g_hTarget") then -- NPCBASE.inc:428
        do return ctx:exit("") end -- NPCBASE.inc:429
    end -- NPCBASE.inc:430
    ctx:command("set", "g_hTarget, NULL") -- NPCBASE.inc:432
    ctx:command("target", "NULL") -- NPCBASE.inc:433
    mm9.gosub(script, ctx, "SetupNextChat") -- NPCBASE.inc:435
    do return ctx:exit("") end -- NPCBASE.inc:437
end

script.labels["OnYourTurn"] = function(ctx)
    -- NPCBASE.inc:440
    -- Play my anim and then tell them we're done...
    if ctx:condition("g_bChatting==FALSE") then -- NPCBASE.inc:445
        do return ctx:exit("") end -- NPCBASE.inc:446
    end -- NPCBASE.inc:447
    ctx:command("converse", "-1, OnConverseDone") -- NPCBASE.inc:449
    do return ctx:exit("") end -- NPCBASE.inc:451
end

script.labels["OnFoundTarget"] = function(ctx)
    -- NPCBASE.inc:454
    -- p0 - hTarget
    if ctx:condition("g_bChatEnabled==FALSE") then -- NPCBASE.inc:459
        do return ctx:exit("") end -- NPCBASE.inc:460
    end -- NPCBASE.inc:461
    -- Set him as our target.
    if ctx:condition("g_bSocializeEnabled==FALSE") then -- NPCBASE.inc:464
        do return ctx:exit("") end -- NPCBASE.inc:465
    end -- NPCBASE.inc:466
    ctx:getParam(0, "g_hTarget") -- NPCBASE.inc:468
    ctx:command("target", "g_hTarget, FALSE") -- NPCBASE.inc:469
    mm9.gosub(script, ctx, "LookForPersonOff") -- NPCBASE.inc:471
    ctx:trigger("g_hTarget", "Hello") -- NPCBASE.inc:473
    ctx:command("wait", "SOCIALIZE_WAIT, 3, OnChatGiveUp") -- NPCBASE.inc:475
    do return ctx:exit("") end -- NPCBASE.inc:477
end

script.labels["LookForPersonOn"] = function(ctx)
    -- NPCBASE.inc:480
    ctx:command("onfoundtarget", "OnFoundTarget") -- NPCBASE.inc:483
    -- Figure out how long to wait for someone to show up...
    ctx:command("getrandomint", "MIN_CHAT_SEARCH, MAX_CHAT_SEARCH, g_nRandom") -- NPCBASE.inc:486
    ctx:command("wait", "SOCIALIZE_WAIT, g_nRandom, SetupNextChat") -- NPCBASE.inc:487
    do return ctx:exit("") end -- NPCBASE.inc:489
end

script.labels["LookForPersonOff"] = function(ctx)
    -- NPCBASE.inc:492
    ctx:command("onfoundtarget", "") -- NPCBASE.inc:495
    do return ctx:exit("") end -- NPCBASE.inc:497
end

script.labels["SetupNextChat"] = function(ctx)
    -- NPCBASE.inc:500
    ctx:command("target", "NULL") -- NPCBASE.inc:503
    ctx:command("set", "g_hTarget, NULL") -- NPCBASE.inc:504
    ctx:command("stop", "") -- NPCBASE.inc:506
    ctx:command("setidle", "") -- NPCBASE.inc:507
    mm9.gosub(script, ctx, "EnableWandering") -- NPCBASE.inc:508
    mm9.gosub(script, ctx, "LookForPersonOff") -- NPCBASE.inc:509
    ctx:command("getrandomint", "MIN_SOCIALIZE_WAIT, MAX_SOCIALIZE_WAIT, g_nRandom") -- NPCBASE.inc:510
    ctx:command("wait", "SOCIALIZE_WAIT, g_nRandom, LookForPersonOn") -- NPCBASE.inc:511
    do return ctx:exit("") end -- NPCBASE.inc:513
end

script.labels["OnUse"] = function(ctx)
    -- NPCBASE.inc:516
    -- Let's cancel anything we were doing so we can chill with the
    -- player...
    ctx:getParam(0, "g_hObject") -- NPCBASE.inc:522
    ctx:command("getfacedir", "g_hMyObject,g_dirX,g_dirY,g_dirZ") -- NPCBASE.inc:524
    mm9.gosub(script, ctx, "DisableChat") -- NPCBASE.inc:526
    mm9.gosub(script, ctx, "DisableWandering") -- NPCBASE.inc:527
    ctx:command("stop", "") -- NPCBASE.inc:529
    ctx:command("setidle", "") -- NPCBASE.inc:530
    ctx:command("g_htarget", "= g_hObject") -- NPCBASE.inc:532
    ctx:command("target", "g_hTarget, FALSE") -- NPCBASE.inc:533
    do return ctx:exit("FALSE") end -- NPCBASE.inc:535
end

script.labels["OnRUDEExit"] = function(ctx)
    -- NPCBASE.inc:538
    ctx:command("set", "g_hTarget, NULL") -- NPCBASE.inc:540
    ctx:command("target", "NULL") -- NPCBASE.inc:541
    if ctx:condition("current_marker == NULL") then -- NPCBASE.inc:543
        mm9.gosub(script, ctx, "EnableWandering") -- NPCBASE.inc:544
        mm9.gosub(script, ctx, "EnableChat") -- NPCBASE.inc:545
        ctx:command("facedir", "g_dirX,g_dirY,g_dirZ,180") -- NPCBASE.inc:546
    else -- NPCBASE.inc:547
        ctx:command("walkto", "current_marker, 0, OnGoToLocArrival") -- NPCBASE.inc:548
    end -- NPCBASE.inc:549
    do return ctx:exit("") end -- NPCBASE.inc:551
end

script.labels["Startup"] = function(ctx)
    -- NPCBASE.inc:554
    -- Until level design does this for all NPCs, we'll just
    -- force all NPCs to do simple wander...
    -- if ( bWanderEnabled==FALSE )
    -- gosub BaseWanderForceStartUp
    -- endif
    if ctx:condition("g_bSocializeEnabled==TRUE") then -- NPCBASE.inc:565
        if ctx:condition("g_bChatEnabled==TRUE") then -- NPCBASE.inc:566
            mm9.gosub(script, ctx, "SetupNextChat") -- NPCBASE.inc:567
        end -- NPCBASE.inc:568
    end -- NPCBASE.inc:569
    do return ctx:exit("") end -- NPCBASE.inc:571
end

script.labels["OnDamage"] = function(ctx)
    -- NPCBASE.inc:574
    -- store who hit us...
    -- p0 = hAttacker
    -- p1 = HitPoints
    -- p2 = DamageType
    if ctx:condition("g_hTarget!=NULL") then -- NPCBASE.inc:583
        ctx:command("isplayer", "g_hTarget, g_bTemp") -- NPCBASE.inc:584
        if ctx:condition("g_bTemp==TRUE") then -- NPCBASE.inc:585
            do return ctx:exit("") end -- NPCBASE.inc:586
        end -- NPCBASE.inc:587
    end -- NPCBASE.inc:588
    ctx:command("target", "NULL") -- NPCBASE.inc:590
    ctx:getParam(0, "g_hTarget") -- NPCBASE.inc:592
    ctx:command("target", "g_hTarget, FALSE") -- NPCBASE.inc:593
    mm9.gosub(script, ctx, "RunAway") -- NPCBASE.inc:595
    do return ctx:exit("") end -- NPCBASE.inc:597
end

script.labels["OnDamageDone"] = function(ctx)
    -- NPCBASE.inc:600
    -- Run Forest Run....
    do return ctx:exit("") end -- NPCBASE.inc:605
end

script.labels["OnProjectile"] = function(ctx)
    -- NPCBASE.inc:609
    -- Run for help!
    -- p0	- hProjectile
    -- p1	- hLaunchedFrom
    -- p2	- dist
    if ctx:condition("g_hTarget!=NULL") then -- NPCBASE.inc:619
        ctx:command("isplayer", "g_hTarget, g_bTemp") -- NPCBASE.inc:620
        if ctx:condition("g_bTemp==TRUE") then -- NPCBASE.inc:621
            do return ctx:exit("") end -- NPCBASE.inc:622
        end -- NPCBASE.inc:623
    end -- NPCBASE.inc:624
    ctx:command("target", "NULL") -- NPCBASE.inc:626
    ctx:getParam(1, "g_hTarget") -- NPCBASE.inc:628
    ctx:command("target", "g_hTarget, FALSE") -- NPCBASE.inc:629
    mm9.gosub(script, ctx, "RunAway") -- NPCBASE.inc:631
    do return ctx:exit("") end -- NPCBASE.inc:633
end

script.labels["RunAway"] = function(ctx)
    -- NPCBASE.inc:636
    if ctx:condition("g_hTarget==NULL") then -- NPCBASE.inc:641
        do return ctx:exit("") end -- NPCBASE.inc:642
    end -- NPCBASE.inc:643
    ctx:command("onprojectile", "") -- NPCBASE.inc:645
    mm9.gosub(script, ctx, "DisableWandering") -- NPCBASE.inc:647
    ctx:command("stop", "") -- NPCBASE.inc:649
    ctx:command("setidle", "") -- NPCBASE.inc:650
    -- Cancel some timers...
    ctx:command("wait", "SOCIALIZE_WAIT, 0, DoNothing") -- NPCBASE.inc:654
    mm9.gosub(script, ctx, "BaseRunAway") -- NPCBASE.inc:656
    do return ctx:exit("") end -- NPCBASE.inc:658
end

script.labels["BaseRunCancel"] = function(ctx)
    -- NPCBASE.inc:661
    -- We're overloading the function here....
    ctx:command("debugout", "NPCBase RUN Cancel!") -- NPCBASE.inc:667
    mm9.gosub(script, ctx, "BaseRunCancel") -- NPCBASE.inc:668
    ctx:command("set", "g_hTarget, NULL") -- NPCBASE.inc:670
    ctx:command("target", "NULL") -- NPCBASE.inc:671
    ctx:command("stop", "") -- NPCBASE.inc:672
    mm9.gosub(script, ctx, "EnableWandering") -- NPCBASE.inc:674
    mm9.gosub(script, ctx, "EnableChat") -- NPCBASE.inc:675
    ctx:command("onprojectile", "OnProjectile, 200") -- NPCBASE.inc:677
    do return ctx:exit("") end -- NPCBASE.inc:679
end

script.labels["BaseRunFindHidingPlace"] = function(ctx)
    -- NPCBASE.inc:682
    -- Overload this so we can find a guard...
    mm9.gosub(script, ctx, "BaseRunFindHidingPlace") -- NPCBASE.inc:698
    if ctx:condition("g_hHidingPlace!=NULL") then -- NPCBASE.inc:700
        do return ctx:exit("") end -- NPCBASE.inc:701
    end -- NPCBASE.inc:702
    ctx:command("getobjects", "GuardBase, 1600, 5, hGuardTemp, nGuards") -- NPCBASE.inc:704
    if ctx:condition("nGuards == 0") then -- NPCBASE.inc:706
        do return ctx:exit("") end -- NPCBASE.inc:707
    end -- NPCBASE.inc:708
    ctx:command("g_ntemp", "= 0") -- NPCBASE.inc:710
    ctx:command("nvalidguards", "= 0") -- NPCBASE.inc:711
    ctx:command("getpos", "g_hTarget,g_posX,g_posY,g_posZ") -- NPCBASE.inc:713
    while ctx:condition("g_nTemp < nGuards") do -- NPCBASE.inc:715
        ctx:command("arrayget", "hGuardTemp, g_nTemp, g_hObject") -- NPCBASE.inc:716
        ctx:command("canreachobject", "g_hObject, g_bTemp") -- NPCBASE.inc:717
        if ctx:condition("g_bTemp==TRUE") then -- NPCBASE.inc:718
            ctx:command("getpos", "g_hObject,guardX,guardY,guardZ") -- NPCBASE.inc:720
            ctx:command("vecdist", "guardX,guardY,guardZ,g_posX,g_posY,g_posZ,g_nTemp") -- NPCBASE.inc:722
            if ctx:condition("g_nTemp > 500") then -- NPCBASE.inc:724
                ctx:command("arrayput", "hGuardArray,nValidGuards,g_hObject") -- NPCBASE.inc:725
                ctx:command("add", "nValidGuards,1") -- NPCBASE.inc:726
            end -- NPCBASE.inc:727
        end -- NPCBASE.inc:728
        ctx:command("add", "g_nTemp,1") -- NPCBASE.inc:730
    end -- NPCBASE.inc:732
    if ctx:condition("nValidGuards>0") then -- NPCBASE.inc:734
        ctx:command("sub", "nValidGuards,1") -- NPCBASE.inc:735
        ctx:command("getrandomint", "0,nValidGuards,g_nRandom") -- NPCBASE.inc:736
        ctx:command("arrayget", "hGuardArray,g_nRandom,g_hHidingPlace") -- NPCBASE.inc:737
        ctx:command("debugout", "Found Guard!  Set him as our hiding place....") -- NPCBASE.inc:738
        mm9.gosub(script, ctx, "BaseRunHide") -- NPCBASE.inc:739
        do return ctx:exit("") end -- NPCBASE.inc:740
    end -- NPCBASE.inc:741
    ctx:command("g_hhidingplace", "= NULL") -- NPCBASE.inc:743
    do return ctx:exit("") end -- NPCBASE.inc:745
end

script.labels["BaseRunAway"] = function(ctx)
    -- NPCBASE.inc:748
    if ctx:condition("current_marker!=NULL") then -- NPCBASE.inc:751
        -- If we're trying to runaway, just run to
        -- our marker...
        ctx:command("target", "NULL") -- NPCBASE.inc:754
        ctx:command("g_htarget", "= NULL") -- NPCBASE.inc:755
        ctx:command("runto", "current_marker, 0, OnGoToLocArrival") -- NPCBASE.inc:756
        do return ctx:exit("") end -- NPCBASE.inc:757
    end -- NPCBASE.inc:758
    ctx:command("htemp", "= g_hTarget") -- NPCBASE.inc:762
    mm9.gosub(script, ctx, "DisableWandering") -- NPCBASE.inc:764
    mm9.gosub(script, ctx, "DisableChat") -- NPCBASE.inc:765
    ctx:command("g_htarget", "= hTemp") -- NPCBASE.inc:767
    ctx:command("target", "g_hTarget,FALSE") -- NPCBASE.inc:768
    mm9.gosub(script, ctx, "BaseRunAway") -- NPCBASE.inc:770
    do return ctx:exit("") end -- NPCBASE.inc:772
end

script.labels["BaseWanderStartup"] = function(ctx)
    -- NPCBASE.inc:775
    mm9.gosub(script, ctx, "BaseWanderStartup") -- NPCBASE.inc:778
    if ctx:condition("bWanderEnabled==FALSE") then -- NPCBASE.inc:780
        ctx:command("g_bsocializeenabled", "= FALSE") -- NPCBASE.inc:781
    end -- NPCBASE.inc:782
    if ctx:condition("nWanderPathCount!=0") then -- NPCBASE.inc:784
        ctx:command("g_bsocializeenabled", "= FALSE") -- NPCBASE.inc:785
    end -- NPCBASE.inc:786
    if ctx:condition("nWanderLeash!=0") then -- NPCBASE.inc:788
        ctx:command("g_bsocializeenabled", "= FALSE") -- NPCBASE.inc:789
    end -- NPCBASE.inc:790
    do return ctx:exit("") end -- NPCBASE.inc:792
end

script.labels["NPCBaseInit"] = function(ctx)
    -- NPCBASE.inc:795
    mm9.gosub(script, ctx, "BaseWanderInit") -- NPCBASE.inc:798
    ctx:command("wait", "0, 0.1, Startup") -- NPCBASE.inc:799
    ctx:addTrigger("Hello", "OnHello") -- NPCBASE.inc:801
    ctx:addTrigger("LetsTalk", "OnLetsTalk") -- NPCBASE.inc:802
    ctx:addTrigger("LeaveMeAlone", "OnLeaveMeAlone") -- NPCBASE.inc:803
    ctx:addTrigger("GoodBye", "OnGoodBye") -- NPCBASE.inc:804
    ctx:addTrigger("YourTurn", "OnYourTurn") -- NPCBASE.inc:805
    ctx:addTrigger("LookAtMe", "OnLookAtMe") -- NPCBASE.inc:806
    ctx:addTrigger("ChatBegin", "OnChatBegin") -- NPCBASE.inc:807
    ctx:addTrigger("Use", "OnUse") -- NPCBASE.inc:808
    ctx:addTrigger("GoToLoc", "OnGoToLoc") -- NPCBASE.inc:809
    ctx:addTrigger("WarpToLoc", "OnWarpToLoc") -- NPCBASE.inc:810
    ctx:onRudeExit("OnRudeExit", script.labels["OnRudeExit"]) -- NPCBASE.inc:812
    ctx:command("onprojectile", "OnProjectile, 200") -- NPCBASE.inc:814
    ctx:command("ondamagedone", "OnDamageDone") -- NPCBASE.inc:815
    ctx:command("ondamage", "OnDamage") -- NPCBASE.inc:816
    ctx:command("set", "g_bAskForHelp, TRUE") -- NPCBASE.inc:818
    -- 100 feet...
    ctx:command("set", "MIN_RUNAWAY_DIST, 1200") -- NPCBASE.inc:820
    ctx:command("addfriend", "NPC") -- NPCBASE.inc:822
    ctx:command("addfriend", "Player") -- NPCBASE.inc:823
    ctx:command("addfriend", "GuardBase") -- NPCBASE.inc:824
    mm9.gosub(script, ctx, "BaseRunInit") -- NPCBASE.inc:826
    do return ctx:exit("") end -- NPCBASE.inc:828
end

return script
