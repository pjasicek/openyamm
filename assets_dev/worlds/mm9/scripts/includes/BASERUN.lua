-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASERUN.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "BaseTimers.inc" }
script.includes[#script.includes + 1] = { line = 16, path = "AIGlobals.Inc" }

-- BaseRun.Inc
-- Jeff Leggett
-- 08/07/2001
-- Base include for running away from the target...
-- Runs in opposite direction of the target.
-- Looks for hiding places tagged for this Actor.
-- If one is found, it runs to it....
-- You can customize these to limit how much we'll turn left and right while running away.....
-- Set this to TRUE if you want to yell for help while running away....
script.labels["CanCower"] = function(ctx)
    -- BASERUN.inc:63
    -- Sets g_bCanCower to TRUE or FALSE
    ctx:command("getanimnbr", "g_hMyObject,Cower,g_nCowerAnim") -- BASERUN.inc:68
    if ctx:condition("g_nCowerAnim==-1") then -- BASERUN.inc:70
        ctx:command("g_bcancower", "= FALSE") -- BASERUN.inc:71
    else -- BASERUN.inc:72
        ctx:command("g_bcancower", "= TRUE") -- BASERUN.inc:73
    end -- BASERUN.inc:74
    do return ctx:exit("") end -- BASERUN.inc:76
end

script.labels["BaseIsCowering"] = function(ctx)
    -- BASERUN.inc:79
    ctx:command("g_bcowering", "= FALSE") -- BASERUN.inc:82
    ctx:command("getcurranim", "g_hMyObject, g_nTemp") -- BASERUN.inc:84
    if ctx:condition("g_nTemp==g_nCowerAnim") then -- BASERUN.inc:86
        ctx:command("g_bcowering", "= TRUE") -- BASERUN.inc:87
    end -- BASERUN.inc:88
    do return ctx:exit("") end -- BASERUN.inc:90
end

script.labels["BaseRunCower"] = function(ctx)
    -- BASERUN.inc:93
    -- Go into "cower" mode...
    mm9.gosub(script, ctx, "BaseIsCowering") -- BASERUN.inc:99
    if ctx:condition("g_bCowering==FALSE") then -- BASERUN.inc:101
        ctx:command("g_bcowering", "= TRUE") -- BASERUN.inc:102
        ctx:command("loopanim", "Cower, 0") -- BASERUN.inc:103
        ctx:command("gettime", "g_nLastRunawayTime") -- BASERUN.inc:104
    end -- BASERUN.inc:105
    ctx:command("target", "g_hTarget, FALSE") -- BASERUN.inc:107
    ctx:command("wait", "RUN_AWAY_WAIT,COWER_TICK,BaseRunCowerTick") -- BASERUN.inc:109
    do return ctx:exit("") end -- BASERUN.inc:111
end

script.labels["BaseRunCowerTick"] = function(ctx)
    -- BASERUN.inc:114
    -- See if we should stop cowering...
    ctx:command("gettarget", "g_hObject") -- BASERUN.inc:120
    if ctx:condition("g_hObject==NULL") then -- BASERUN.inc:122
        do return mm9.gotoLabel(script, ctx, "BaseRunCancel") end -- BASERUN.inc:123
    end -- BASERUN.inc:124
    ctx:command("isvisible", "g_hObject,g_bTemp") -- BASERUN.inc:126
    if ctx:condition("g_bTemp==FALSE") then -- BASERUN.inc:128
        do return mm9.gotoLabel(script, ctx, "BaseRunCancel") end -- BASERUN.inc:129
    end -- BASERUN.inc:130
    ctx:command("wait", "RUN_AWAY_WAIT,COWER_TICK,BaseRunCowerTick") -- BASERUN.inc:132
    do return ctx:exit("") end -- BASERUN.inc:134
end

script.labels["BaseRunCowerStop"] = function(ctx)
    -- BASERUN.inc:137
    mm9.gosub(script, ctx, "BaseIsCowering") -- BASERUN.inc:140
    if ctx:condition("g_bCowering==TRUE") then -- BASERUN.inc:142
        ctx:command("wait", "RUN_AWAY_WAIT,0,DoNothing") -- BASERUN.inc:143
        ctx:command("stop", "") -- BASERUN.inc:144
        ctx:command("g_bcowering", "= FALSE") -- BASERUN.inc:145
    end -- BASERUN.inc:146
    do return ctx:exit("") end -- BASERUN.inc:148
end

script.labels["BaseRunLostTarget"] = function(ctx)
    -- BASERUN.inc:151
    do return ctx:exit("TRUE") end -- BASERUN.inc:154
end

script.labels["BaseRunCancel"] = function(ctx)
    -- BASERUN.inc:157
    -- Stop running away...
    -- You'll want to overload this to do your own thing,
    -- just remember to call this function (ie:gosub BaseRunCancel,1)
    mm9.gosub(script, ctx, "BaseRunCowerStop") -- BASERUN.inc:165
    ctx:command("g_brunningaway", "= FALSE") -- BASERUN.inc:167
    -- OnTargetBeyondDist 0
    ctx:command("onobstacle", "") -- BASERUN.inc:169
    ctx:command("onlosttarget", "") -- BASERUN.inc:170
    ctx:command("g_hrunawaytrigger", "= NULL") -- BASERUN.inc:172
    ctx:command("wait", "RUN_AWAY_WAIT, 0, DoNothing") -- BASERUN.inc:174
    do return ctx:exit("") end -- BASERUN.inc:176
end

script.labels["BaseRunAwayFace"] = function(ctx)
    -- BASERUN.inc:179
    -- Figure out direction to face when running away...
    if ctx:condition("g_hTarget==NULL") then -- BASERUN.inc:184
        do return ctx:exit("") end -- BASERUN.inc:185
    end -- BASERUN.inc:186
    ctx:command("getpos", "g_hTarget, g_targetX, g_targetY, g_targetZ") -- BASERUN.inc:188
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- BASERUN.inc:189
    ctx:command("vecsub", "g_posX, g_posY, g_posZ, g_targetX, g_targetY, g_targetZ") -- BASERUN.inc:191
    ctx:command("g_targety", "= 0") -- BASERUN.inc:192
    ctx:command("vecnorm", "g_posX, g_posY, g_posZ") -- BASERUN.inc:193
    ctx:command("getrandomfloat", "RUN_AWAY_TURN_MIN, RUN_AWAY_TURN_MAX, g_nRandom") -- BASERUN.inc:195
    ctx:command("getrandomfloat", "0,1, g_nTemp") -- BASERUN.inc:196
    if ctx:condition("g_nTemp==1") then -- BASERUN.inc:198
        ctx:command("g_nrandom", "= g_nRandom * -1") -- BASERUN.inc:199
    end -- BASERUN.inc:200
    ctx:command("rotatedir", "g_posX, g_posY, g_posZ, g_nRandom") -- BASERUN.inc:202
    ctx:command("castray", "g_posX, g_posY, g_posZ, 100, g_hObject, g_nTemp") -- BASERUN.inc:203
    if ctx:condition("g_hObject!=NULL") then -- BASERUN.inc:205
        ctx:command("g_nrandom", "= g_nRandom * -2") -- BASERUN.inc:206
        ctx:command("rotatedir", "g_posX, g_posY, g_posZ, g_nRandom") -- BASERUN.inc:207
        ctx:command("castray", "g_posX, g_posY, g_posZ, 100, g_hObject, g_nTemp") -- BASERUN.inc:208
        if ctx:condition("g_hObject!=NULL") then -- BASERUN.inc:209
            do return ctx:exit("") end -- BASERUN.inc:210
        end -- BASERUN.inc:211
    end -- BASERUN.inc:212
    ctx:command("facedir", "g_posX, g_posY, g_posZ, 360") -- BASERUN.inc:214
    do return ctx:exit("") end -- BASERUN.inc:216
end

script.labels["BaseShouldRun"] = function(ctx)
    -- BASERUN.inc:219
    ctx:command("g_btemp", "= FALSE") -- BASERUN.inc:221
    if ctx:condition("g_hRunAwayTrigger==g_hTarget") then -- BASERUN.inc:223
        ctx:command("g_btemp", "= TRUE") -- BASERUN.inc:224
    else -- BASERUN.inc:225
        ctx:command("shouldrunaway", "g_hTarget, g_bTemp") -- BASERUN.inc:226
    end -- BASERUN.inc:227
    if ctx:condition("g_bTemp==TRUE") then -- BASERUN.inc:229
        ctx:command("isinnorunzone", "g_bTemp") -- BASERUN.inc:230
        if ctx:condition("g_bTemp==TRUE") then -- BASERUN.inc:231
            if ctx:condition("g_hHidingPlace!=NULL") then -- BASERUN.inc:232
                ctx:command("g_btemp", "= TRUE") -- BASERUN.inc:233
            else -- BASERUN.inc:234
                ctx:command("g_btemp", "= FALSE") -- BASERUN.inc:235
            end -- BASERUN.inc:236
        else -- BASERUN.inc:237
            ctx:command("g_btemp", "= TRUE") -- BASERUN.inc:238
        end -- BASERUN.inc:239
    end -- BASERUN.inc:240
    do return ctx:exit("") end -- BASERUN.inc:242
end

script.labels["BaseRunAwayTick"] = function(ctx)
    -- BASERUN.inc:245
    -- We do our running away thinking here....
    ctx:command("gettarget", "g_hObject") -- BASERUN.inc:251
    if ctx:condition("g_hObject==NULL") then -- BASERUN.inc:252
        -- We're done!
        ctx:command("debugout", "Target Is Gone.  Done running...") -- BASERUN.inc:254
        mm9.gosub(script, ctx, "BaseRunCancel") -- BASERUN.inc:255
        do return ctx:exit("") end -- BASERUN.inc:256
    end -- BASERUN.inc:257
    mm9.gosub(script, ctx, "BaseShouldRun") -- BASERUN.inc:259
    if ctx:condition("g_bTemp==FALSE") then -- BASERUN.inc:261
        ctx:command("debugout", "ShouldRunAway says NO.") -- BASERUN.inc:262
        mm9.gosub(script, ctx, "BaseRunCancel") -- BASERUN.inc:263
        do return ctx:exit("") end -- BASERUN.inc:264
    end -- BASERUN.inc:265
    ctx:command("gettime", "g_nTemp") -- BASERUN.inc:267
    ctx:command("sub", "g_nTemp, g_nLastRunawayTime") -- BASERUN.inc:269
    if ctx:condition("g_nTemp > RUN_AWAY_MAX_TIME") then -- BASERUN.inc:271
        ctx:command("debugout", "Ran away long enough...") -- BASERUN.inc:272
        if ctx:condition("g_bCanCower==TRUE") then -- BASERUN.inc:273
            mm9.gosub(script, ctx, "BaseRunCower") -- BASERUN.inc:274
        else -- BASERUN.inc:275
            mm9.gosub(script, ctx, "BaseRunCancel") -- BASERUN.inc:276
        end -- BASERUN.inc:277
        do return ctx:exit("") end -- BASERUN.inc:278
    end -- BASERUN.inc:279
    ctx:command("aigetdistance", "g_hObject, g_dist1") -- BASERUN.inc:282
    if ctx:condition("g_hHidingPlace==NULL") then -- BASERUN.inc:284
        if ctx:condition("g_dist1 > MIN_RUNAWAY_DIST") then -- BASERUN.inc:285
            -- We're far enough away, let's quit.
            ctx:command("debugout", "Far Enough Away... Stop running!") -- BASERUN.inc:287
            mm9.gosub(script, ctx, "BaseRunCancel") -- BASERUN.inc:288
            do return ctx:exit("") end -- BASERUN.inc:289
        end -- BASERUN.inc:290
    end -- BASERUN.inc:291
    mm9.gosub(script, ctx, "BaseRunAwayFace") -- BASERUN.inc:294
    if ctx:condition("g_bAskForHelp==TRUE") then -- BASERUN.inc:296
        if ctx:condition("g_hTarget!=NULL") then -- BASERUN.inc:297
            ctx:command("help", "g_hTarget") -- BASERUN.inc:298
        end -- BASERUN.inc:299
    end -- BASERUN.inc:300
    ctx:command("run", "") -- BASERUN.inc:302
    ctx:command("getrandomfloat", "RUN_AWAY_TICK_MIN, RUN_AWAY_TICK_MAX, g_nRandom") -- BASERUN.inc:304
    ctx:command("wait", "RUN_AWAY_WAIT, g_nRandom, BaseRunAwayTick") -- BASERUN.inc:305
    do return ctx:exit("") end -- BASERUN.inc:307
end

script.labels["BaseRunAwayObstacle"] = function(ctx)
    -- BASERUN.inc:310
    -- See which way is the lesser of two evils....
    -- p0 - hObstacle
    -- p1-3 - Normal of collision...
    if ctx:condition("g_nLastRunawayObstacle!=0") then -- BASERUN.inc:318
        ctx:command("gettime", "g_nTemp") -- BASERUN.inc:319
        ctx:command("sub", "g_nTemp, g_nLastRunawayObstacle") -- BASERUN.inc:320
        if ctx:condition("g_nTemp < 1") then -- BASERUN.inc:321
            ctx:command("add", "g_nRunawayObstacles,1") -- BASERUN.inc:322
            if ctx:condition("g_nRunawayObstacles > 2") then -- BASERUN.inc:323
                if ctx:condition("g_bCanCower==TRUE") then -- BASERUN.inc:324
                    do return mm9.gotoLabel(script, ctx, "BaseRunCower") end -- BASERUN.inc:325
                else -- BASERUN.inc:326
                    ctx:command("stop", "") -- BASERUN.inc:327
                    do return mm9.gotoLabel(script, ctx, "BaseRunCancel") end -- BASERUN.inc:328
                end -- BASERUN.inc:329
            end -- BASERUN.inc:330
        else -- BASERUN.inc:331
            ctx:command("g_nrunawayobstacles", "= 0") -- BASERUN.inc:332
        end -- BASERUN.inc:333
    end -- BASERUN.inc:334
    ctx:getParam(1, "g_dirX") -- BASERUN.inc:336
    ctx:getParam(2, "g_dirY") -- BASERUN.inc:337
    ctx:getParam(3, "g_dirZ") -- BASERUN.inc:338
    ctx:command("gettime", "g_nLastRunawayObstacle") -- BASERUN.inc:340
    -- Get distance at 90 degrees of angle...
    ctx:command("rotatedir", "g_dirX, g_dirY, g_dirZ, 90") -- BASERUN.inc:343
    ctx:command("getpos", "g_hTarget, g_targetX, g_targetY, g_targetZ") -- BASERUN.inc:344
    ctx:command("vecscale", "g_dirX, g_dirY, g_dirZ, 120") -- BASERUN.inc:345
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- BASERUN.inc:346
    ctx:command("vecadd", "g_posX,g_posY,g_posZ,g_dirX,g_dirY,g_dirZ") -- BASERUN.inc:347
    ctx:command("vecdist", "g_posX,g_posY,g_posZ,g_targetX,g_targetY,g_targetZ,g_dist1") -- BASERUN.inc:348
    ctx:command("castray", "g_dirX, g_dirY, g_dirZ, 100, g_hObject, g_nTemp") -- BASERUN.inc:350
    if ctx:condition("g_hObject!=NULL") then -- BASERUN.inc:352
        ctx:command("g_dist1", "= 0") -- BASERUN.inc:353
    end -- BASERUN.inc:354
    ctx:getParam(1, "g_dirX") -- BASERUN.inc:356
    ctx:getParam(2, "g_dirY") -- BASERUN.inc:357
    ctx:getParam(3, "g_dirZ") -- BASERUN.inc:358
    -- Get distance at -90 degrees of angle...
    ctx:command("rotatedir", "g_dirX, g_dirY, g_dirZ, -90") -- BASERUN.inc:361
    ctx:command("vecscale", "g_dirX, g_dirY, g_dirZ, 120") -- BASERUN.inc:362
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- BASERUN.inc:363
    ctx:command("vecadd", "g_posX,g_posY,g_posZ,g_dirX,g_dirY,g_dirZ") -- BASERUN.inc:364
    ctx:command("vecdist", "g_posX,g_posY,g_posZ,g_targetX,g_targetY,g_targetZ,g_dist2") -- BASERUN.inc:365
    ctx:command("castray", "g_dirX, g_dirY, g_dirZ, 100, g_hObject, g_nTemp") -- BASERUN.inc:367
    if ctx:condition("g_hObject!=NULL") then -- BASERUN.inc:369
        ctx:command("g_dist2", "= 0") -- BASERUN.inc:370
    end -- BASERUN.inc:371
    ctx:getParam(1, "g_dirX") -- BASERUN.inc:373
    ctx:getParam(2, "g_dirY") -- BASERUN.inc:374
    ctx:getParam(3, "g_dirZ") -- BASERUN.inc:375
    if ctx:condition("g_dist1 > g_dist2") then -- BASERUN.inc:377
        ctx:command("rotatedir", "g_dirX, g_dirY, g_dirZ, 90") -- BASERUN.inc:378
    else -- BASERUN.inc:379
        if ctx:condition("g_dist2 > g_dist1") then -- BASERUN.inc:380
            ctx:command("rotatedir", "g_dirX, g_dirY, g_dirZ, -90") -- BASERUN.inc:381
        else -- BASERUN.inc:382
            -- Boxed in!  go the direction of the "Normal"
            -- (ie: leave g_dir alone...)
            -- Have us go in that direction for a while!
            -- DebugOut Boxed In!!!
            ctx:command("wait", "RUN_AWAY_WAIT, 3.0, BaseRunAwayTick") -- BASERUN.inc:388
        end -- BASERUN.inc:389
    end -- BASERUN.inc:390
    ctx:command("facedir", "g_dirX, g_dirY, g_dirZ, 0") -- BASERUN.inc:392
    ctx:command("run", "") -- BASERUN.inc:393
    do return ctx:exit("TRUE") end -- BASERUN.inc:395
end

script.labels["BaseRunFindHidingPlace"] = function(ctx)
    -- BASERUN.inc:398
    -- If hiding place is found, stop doing the runAway mode
    -- and just run to our hiding place...
    if ctx:condition("g_bUseHidingPlaces==FALSE") then -- BASERUN.inc:405
        ctx:command("g_hhidingplace", "= NULL") -- BASERUN.inc:406
        do return ctx:exit("") end -- BASERUN.inc:407
    end -- BASERUN.inc:408
    ctx:command("findhidingplace", "g_hHidingPlace") -- BASERUN.inc:410
    if ctx:condition("g_hHidingPlace==NULL") then -- BASERUN.inc:412
        do return ctx:exit("") end -- BASERUN.inc:413
    end -- BASERUN.inc:414
    mm9.gosub(script, ctx, "BaseRunHide") -- BASERUN.inc:416
    do return ctx:exit("") end -- BASERUN.inc:418
end

script.labels["BaseRunHideTick"] = function(ctx)
    -- BASERUN.inc:422
    if ctx:condition("g_bAskForHelp==TRUE") then -- BASERUN.inc:425
        if ctx:condition("g_hTarget!=NULL") then -- BASERUN.inc:426
            ctx:command("help", "g_hTarget") -- BASERUN.inc:427
        end -- BASERUN.inc:428
    end -- BASERUN.inc:429
    mm9.gosub(script, ctx, "BaseRunHide") -- BASERUN.inc:431
    ctx:command("wait", "HIDE_WAIT, HIDE_WAIT_TIME, BaseRunHideTick") -- BASERUN.inc:432
    do return ctx:exit("") end -- BASERUN.inc:434
end

script.labels["BaseRunHideArrival"] = function(ctx)
    -- BASERUN.inc:437
    ctx:command("wait", "HIDE_WAIT, 0, DoNothing") -- BASERUN.inc:439
    ctx:command("stop", "") -- BASERUN.inc:441
    ctx:command("setidle", "") -- BASERUN.inc:442
    ctx:command("getfacedir", "g_hMyObject, g_dirX, g_dirY, g_dirZ") -- BASERUN.inc:443
    ctx:command("rotatedir", "g_dirX, g_dirY, g_dirZ, 180") -- BASERUN.inc:445
    ctx:command("facedir", "g_dirX, g_dirY, g_dirZ, 180") -- BASERUN.inc:447
    ctx:command("gettarget", "g_hObject") -- BASERUN.inc:449
    if ctx:condition("g_hObject!=NULL") then -- BASERUN.inc:451
        ctx:command("help", "g_hTarget") -- BASERUN.inc:452
    end -- BASERUN.inc:453
    mm9.gosub(script, ctx, "BaseRunCancel") -- BASERUN.inc:455
    do return ctx:exit("") end -- BASERUN.inc:458
end

script.labels["BaseRunHide"] = function(ctx)
    -- BASERUN.inc:461
    -- Run to hiding place.
    if ctx:condition("g_hHidingPlace==NULL") then -- BASERUN.inc:467
        ctx:command("debugout", "Assert ( g_hHidingPlace!=NULL )") -- BASERUN.inc:468
        do return ctx:exit("") end -- BASERUN.inc:469
    end -- BASERUN.inc:470
    ctx:command("wait", "RUN_AWAY_WAIT, 0, DoNothing") -- BASERUN.inc:472
    -- We'll keep looking for a hiding spot....
    ctx:command("wait", "HIDE_WAIT, HIDE_WAIT_TIME, BaseRunHideTick") -- BASERUN.inc:475
    ctx:command("runto", "g_hHidingPlace,0, BaseRunHideArrival") -- BASERUN.inc:477
    do return ctx:exit("") end -- BASERUN.inc:479
end

script.labels["BaseRunRandom"] = function(ctx)
    -- BASERUN.inc:482
    mm9.gosub(script, ctx, "BaseRunAwayFace") -- BASERUN.inc:485
    -- Setup our callbacks...
    ctx:command("onobstacle", "BaseRunAwayObstacle") -- BASERUN.inc:488
    mm9.gosub(script, ctx, "BaseRunAwayFace") -- BASERUN.inc:490
    -- OnTargetBeyondDist MIN_RUNAWAY_DIST, BaseRunCancel
    ctx:command("g_brunningaway", "= TRUE") -- BASERUN.inc:492
    ctx:command("run", "") -- BASERUN.inc:494
    ctx:command("wait", "RUN_AWAY_WAIT, RUN_AWAY_TICK_TIME, BaseRunAwayTick") -- BASERUN.inc:496
    -- We'll keep looking for a hiding spot....
    ctx:command("wait", "HIDE_WAIT, HIDE_WAIT_TIME, BaseRunFindHidingPlace") -- BASERUN.inc:499
    do return ctx:exit("") end -- BASERUN.inc:501
end

script.labels["BaseRunAway"] = function(ctx)
    -- BASERUN.inc:504
    -- This assumes that g_hTarget is the handle of the one
    -- we're running away FROM.
    if ctx:condition("g_hTarget==NULL") then -- BASERUN.inc:510
        ctx:command("gettarget", "g_hTarget") -- BASERUN.inc:511
        if ctx:condition("g_hTarget==NULL") then -- BASERUN.inc:512
            do return ctx:exit("") end -- BASERUN.inc:513
        end -- BASERUN.inc:514
    end -- BASERUN.inc:515
    if ctx:condition("g_bCanCower==TRUE") then -- BASERUN.inc:517
        ctx:command("getrandomint", "0,100, g_nRandom") -- BASERUN.inc:518
        -- 10% of time, just cower without running away...
        if ctx:condition("g_nRandom < 10") then -- BASERUN.inc:522
            mm9.gosub(script, ctx, "BaseRunCower") -- BASERUN.inc:523
            do return ctx:exit("") end -- BASERUN.inc:524
        end -- BASERUN.inc:525
    end -- BASERUN.inc:526
    ctx:command("gettime", "g_nLastRunawayTime") -- BASERUN.inc:528
    -- Clear out whatever we were doing....
    ctx:command("stop", "") -- BASERUN.inc:533
    ctx:command("setidle", "") -- BASERUN.inc:534
    -- Cannot "lose" the target in this manner...
    ctx:command("onlosttarget", "BaseRunLostTarget") -- BASERUN.inc:537
    mm9.gosub(script, ctx, "BaseRunFindHidingPlace") -- BASERUN.inc:539
    if ctx:condition("g_hHidingPlace==NULL") then -- BASERUN.inc:541
        ctx:command("debugout", "No Hiding Place... Just running away.....") -- BASERUN.inc:542
        mm9.gosub(script, ctx, "BaseRunRandom") -- BASERUN.inc:543
        do return ctx:exit("") end -- BASERUN.inc:544
    else -- BASERUN.inc:545
        ctx:command("debugout", "Runing to hiding place!!") -- BASERUN.inc:546
    end -- BASERUN.inc:547
    -- We have a hiding place... Time to run to it...
    do return ctx:exit("") end -- BASERUN.inc:553
end

script.labels["BaseRunOnFear"] = function(ctx)
    -- BASERUN.inc:556
    -- See if we've had the FEAR condition set on us....
    ctx:command("debugout", "We've been hit with FEAR") -- BASERUN.inc:562
    mm9.gosub(script, ctx, "BaseRunAway") -- BASERUN.inc:564
    do return ctx:exit("") end -- BASERUN.inc:566
end

script.labels["BaseRunOnFearDone"] = function(ctx)
    -- BASERUN.inc:569
    -- See if we've had the FEAR condition set on us....
    ctx:command("debugout", "Fear is DONE... Cancel runaway...") -- BASERUN.inc:575
    mm9.gosub(script, ctx, "BaseRunCancel") -- BASERUN.inc:577
    do return ctx:exit("") end -- BASERUN.inc:579
end

script.labels["OnRunAwayFromMe"] = function(ctx)
    -- BASERUN.inc:582
    ctx:getParam(0, "g_hTarget") -- BASERUN.inc:585
    ctx:command("target", "g_hTarget, FALSE") -- BASERUN.inc:587
    ctx:command("g_hrunawaytrigger", "= g_hTarget") -- BASERUN.inc:589
    mm9.gosub(script, ctx, "BaseRunAway") -- BASERUN.inc:591
    do return ctx:exit("") end -- BASERUN.inc:593
end

script.labels["BaseRunInit"] = function(ctx)
    -- BASERUN.inc:596
    -- Set up our fear & fear done callbacks...
    ctx:command("onfear", "BaseRunOnFear") -- BASERUN.inc:603
    ctx:command("onfeardone", "BaseRunOnFearDone") -- BASERUN.inc:604
    ctx:addTrigger("RunAwayFromMe", "OnRunAwayFromMe") -- BASERUN.inc:606
    mm9.gosub(script, ctx, "CanCower") -- BASERUN.inc:608
    do return ctx:exit("") end -- BASERUN.inc:610
end

return script
