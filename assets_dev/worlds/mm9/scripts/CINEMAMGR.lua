-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CINEMAMGR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 56, path = "BaseGlobals.inc" }

-- TO DO:
-- FIX SNAPTO
-- FIX CURVED PATH
-- INCORPORATE FADE TO OTHER STUFF
-- CinemaMgr.scr
-- by SJR
-- 10-16-01
-- See also: EffectsMgr.scr
-- Purpose:incorporates cool
-- camera effects.
-- Must be run by
-- a camera object.
-- ScriptParams are:
-- p0 = will receive "CinemaDone" on return to player
-- p1-p4 = objects possible to switch between during the level
-- Triggers:
-- "StartZoom"			= executes a zoom using all current settings
-- "StartPan"			= executes a camera pan using all current settings
-- "StartPanHere"		= pans to triggerer
-- PanEffects
-- "Pan180"			= pans a 180 in front of player
-- "Pan135"			= pans a 135
-- "Pan90"				= pans a 90
-- "Pan[Fast\Medium\Slow]	= sets speed of pan (3,6,9 seconds)
-- "PanToZoom"			= executes zoom directly after the pan
-- ZoomEffects
-- "BasicZoom"			= snapback, smooth, fast, short
-- "LinkOn"			= chain all remaining targets continuously
-- "LinkOff"			= disable linking
-- "CamSmooth"			= zooms in and out smoothly
-- "CamRough"			= zooms in and out roughly
-- "CamSpin"			= zooms in and out really roughly (w/ rotations)
-- "CamSnapto"			= goes to object instantaneously
-- "CamSnapback"		= returns to player instantaneously
-- "CamPullback"		= zooms out to player
-- "Cam[Fast\Medium\Slow]	= sets speed of zoom-in (1,2,4 seconds of travel)
-- "Cam[Long\Short\Instant]"	= sets duration of watch (6,3,1/2 seconds)
-- "CamTarget[1\2\3\4]"	= changes target to p[1\2\3\4]
-- For spincam
-- Time to stay at target
-- Player\camera POS
-- Directions
-- Duration
-- For curved path following
-- Pan settings
-- TEMP UNTIL GETRIGHTDIR IS WORKING
script.labels["Main"] = function(ctx)
    -- CINEMAMGR.scr:126
    ctx:getParam(0, "sNotifyName") -- CINEMAMGR.scr:128
    ctx:getParam(1, "sFocus0Name") -- CINEMAMGR.scr:130
    ctx:getParam(2, "sFocus1Name") -- CINEMAMGR.scr:131
    ctx:getParam(3, "sFocus2Name") -- CINEMAMGR.scr:132
    ctx:getParam(4, "sFocus3Name") -- CINEMAMGR.scr:133
    ctx:getParam(5, "sPanNodeName0") -- CINEMAMGR.scr:135
    ctx:getParam(6, "sPanNodeName1") -- CINEMAMGR.scr:136
    ctx:wait(0, 1, "InitCinemaMgr") -- CINEMAMGR.scr:138
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:139
end

script.labels["InitCinemaMgr"] = function(ctx)
    -- CINEMAMGR.scr:142
    mm9.gosub(script, ctx, "SetupAllTriggers") -- CINEMAMGR.scr:144
    ctx:addTrigger("StartZoom", "StartZoom") -- CINEMAMGR.scr:146
    ctx:addTrigger("StartPan", "StartPan") -- CINEMAMGR.scr:147
    ctx:addTrigger("StartPanHere", "StartPanHere") -- CINEMAMGR.scr:148
    ctx:addTrigger("TurnOff", "CameraOff") -- CINEMAMGR.scr:149
    ctx:state().hTarget = ctx:objectOrNil("sFocus0Name") -- CINEMAMGR.scr:150
    ctx:state().hPanNode0 = ctx:objectOrNil("sPanNodeName0") -- CINEMAMGR.scr:151
    ctx:state().hPanNode1 = ctx:objectOrNil("sPanNodeName1") -- CINEMAMGR.scr:152
    ctx:state().hNotify = ctx:objectOrNil("sNotifyName") -- CINEMAMGR.scr:153
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:157
end

script.labels["StartPanHere"] = function(ctx)
    -- CINEMAMGR.scr:160
    -- pans from hPanNode0 to hPanNode1
    ctx:getParam(0, "hPanNode0") -- CINEMAMGR.scr:163
    mm9.gosub(script, ctx, "AlignCamera") -- CINEMAMGR.scr:164
    mm9.gosub(script, ctx, "CameraOn") -- CINEMAMGR.scr:165
    ctx:self():faceObject(ctx:object("hPanNode0"), 180, "StopMoving") -- CINEMAMGR.scr:166
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:167
end

script.labels["StartPan"] = function(ctx)
    -- CINEMAMGR.scr:170
    -- pans from hPanNode0 to hPanNode1
    mm9.gosub(script, ctx, "AlignCamera") -- CINEMAMGR.scr:173
    mm9.gosub(script, ctx, "SetupPan") -- CINEMAMGR.scr:174
    ctx:self():faceObject(ctx:object("hPanNode0"), 0, "DoNothing") -- CINEMAMGR.scr:175
    mm9.gosub(script, ctx, "ExecutePan") -- CINEMAMGR.scr:176
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:177
end

script.labels["ExecutePan"] = function(ctx)
    -- CINEMAMGR.scr:180
    -- pans from current dir to hPanNode1
    mm9.gosub(script, ctx, "CameraOn") -- CINEMAMGR.scr:183
    ctx:self():faceObject(ctx:object("hPanNode1"), "nPanSpeed", "EndPan") -- CINEMAMGR.scr:184
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:185
end

script.labels["EndPan"] = function(ctx)
    -- CINEMAMGR.scr:188
    if ctx:condition("bDoZoom==TRUE") then -- CINEMAMGR.scr:190
        ctx:wait(0, 1, "ExecuteZoom") -- CINEMAMGR.scr:191
    else -- CINEMAMGR.scr:192
        ctx:wait(0, 1, "CameraOff") -- CINEMAMGR.scr:193
    end -- CINEMAMGR.scr:194
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:195
end

script.labels["StartZoom"] = function(ctx)
    -- CINEMAMGR.scr:198
    -- zooms to hTarget from hPlayer
    if ctx:condition("hTarget!=NULL") then -- CINEMAMGR.scr:201
        if ctx:condition("bSnapTo==TRUE") then -- CINEMAMGR.scr:203
            ctx:self():faceObject(ctx:object("hTarget"), 720, "MoveCameraForward") -- CINEMAMGR.scr:204
            ctx:wait(9, "dt", "CameraOn") -- CINEMAMGR.scr:205
        else -- CINEMAMGR.scr:206
            mm9.gosub(script, ctx, "AlignCamera") -- CINEMAMGR.scr:207
            mm9.gosub(script, ctx, "ExecuteZoom") -- CINEMAMGR.scr:208
        end -- CINEMAMGR.scr:209
    end -- CINEMAMGR.scr:210
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:212
end

script.labels["ExecuteZoom"] = function(ctx)
    -- CINEMAMGR.scr:215
    -- zooms to hTarget from current pos
    ctx:state().dirScale = 1 -- CINEMAMGR.scr:218
    ctx:self():faceObject(ctx:object("hTarget"), 200, "MoveCameraForward") -- CINEMAMGR.scr:219
    mm9.gosub(script, ctx, "CameraOn") -- CINEMAMGR.scr:220
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:221
end

script.labels["MoveCameraForward"] = function(ctx)
    -- CINEMAMGR.scr:224
    -- zooms in current direction for
    -- distance to hTarget using current options
    mm9.gosub(script, ctx, "SetupZoom") -- CINEMAMGR.scr:228
    if ctx:condition("bSmooth==FALSE") then -- CINEMAMGR.scr:229
        mm9.gosub(script, ctx, "ShakeCamera") -- CINEMAMGR.scr:230
    end -- CINEMAMGR.scr:231
    if ctx:condition("bSpin==TRUE") then -- CINEMAMGR.scr:232
        mm9.gosub(script, ctx, "SpinCamera") -- CINEMAMGR.scr:233
    end -- CINEMAMGR.scr:234
    mm9.gosub(script, ctx, "FollowCurve") -- CINEMAMGR.scr:235
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecScale("dx", "dy", "dz", "dirScale") -- CINEMAMGR.scr:236
    if ctx:condition("DirScale<0") then -- CINEMAMGR.scr:237
        ctx:self():moveDir("dx", "dy", "dz", "dist", "nSpeed", "CameraOff") -- CINEMAMGR.scr:238
    else -- CINEMAMGR.scr:239
        ctx:self():moveDir("dx", "dy", "dz", "dist", "nSpeed", "EndZoom") -- CINEMAMGR.scr:240
    end -- CINEMAMGR.scr:241
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:242
end

script.labels["EndZoom"] = function(ctx)
    -- CINEMAMGR.scr:245
    -- checks for targetlinks and zoomout
    ctx:self():stop() -- CINEMAMGR.scr:248
    ctx:state().bArrived = true -- CINEMAMGR.scr:249
    if ctx:condition("bLink==TRUE") then -- CINEMAMGR.scr:250
        if ctx:condition("nCurTarget>=3") then -- CINEMAMGR.scr:251
            ctx:wait(7, "tLinger", "CameraOff") -- CINEMAMGR.scr:252
        else -- CINEMAMGR.scr:253
            mm9.gosub(script, ctx, "GetNextTarget") -- CINEMAMGR.scr:254
            ctx:wait(7, "tLinger", "ExecuteZoom") -- CINEMAMGR.scr:255
        end -- CINEMAMGR.scr:256
        mm9.gosub(script, ctx, "SetCamInstant") -- CINEMAMGR.scr:257
    else -- CINEMAMGR.scr:258
        if ctx:condition("bSnapback==TRUE") then -- CINEMAMGR.scr:259
            ctx:wait(7, "tLinger", "CameraOff") -- CINEMAMGR.scr:260
        else -- CINEMAMGR.scr:261
            mm9.gosub(script, ctx, "ReverseDirections") -- CINEMAMGR.scr:262
            ctx:wait(7, "tLinger", "MoveCameraForward") -- CINEMAMGR.scr:263
        end -- CINEMAMGR.scr:264
    end -- CINEMAMGR.scr:265
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:266
end

script.labels["FollowCurve"] = function(ctx)
    -- CINEMAMGR.scr:269
    -- basically, get the player's face vector(scaled up or down),
    -- head that direction towards projected midpoint, and reverse direction
    -- when we get to that midpoint. Just a sketch, fix this!
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:274
    if ctx:condition("bArrived==TRUE") then -- CINEMAMGR.scr:275
        do return ctx:exit("TRUE") end -- CINEMAMGR.scr:276
    end -- CINEMAMGR.scr:277
    ctx:state().xPathNorm, ctx:state().yPathNorm, ctx:state().yPathNorm = ctx:self():rightDir() -- CINEMAMGR.scr:279
    ctx:state().xPathNorm, ctx:state().yPathNorm, ctx:state().zPathNorm = ctx:vecNorm("xPathNorm", "yPathNorm", "zPathNorm") -- CINEMAMGR.scr:280
    ctx:state().xPathNorm, ctx:state().yPathNorm, ctx:state().zPathNorm = ctx:vecScale("xPathNorm", "yPathNorm", "zPathNorm", "dirScale") -- CINEMAMGR.scr:281
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:player():rotation() -- CINEMAMGR.scr:283
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:vecNorm("x", "y", "z") -- CINEMAMGR.scr:284
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:vecScale("x", "y", "z", "dist") -- CINEMAMGR.scr:285
    ctx:state().xPathNorm, ctx:state().yPathNorm, ctx:state().zPathNorm = ctx:vecScale("xPathNorm", "yPathNorm", "zPathNorm", "v1dist") -- CINEMAMGR.scr:287
    ctx:state().nPathDist = ctx:vecDist("xPathNorm", "yPathNorm", "zPathNorm", "x", "y", "z") -- CINEMAMGR.scr:288
    ctx:set("nPathSpeed", "nPathDist / dt") -- CINEMAMGR.scr:290
    ctx:set("nPathDist", "nPathDist / 2") -- CINEMAMGR.scr:291
    ctx:self():moveDir("xPathNorm", "yPathNorm", "zPathNorm", "nPathDist", "nSpeed", "FollowCurve") -- CINEMAMGR.scr:292
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:293
end

script.labels["ShakeCamera"] = function(ctx)
    -- CINEMAMGR.scr:296
    -- vibrates camera as it zooms
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:299
    if ctx:condition("bArrived==TRUE") then -- CINEMAMGR.scr:300
        do return ctx:exit("TRUE") end -- CINEMAMGR.scr:301
    end -- CINEMAMGR.scr:302
    ctx:randomInt(-35, 35, "rand") -- CINEMAMGR.scr:304
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:self():rightDir() -- CINEMAMGR.scr:305
    ctx:set("x", "x + rand") -- CINEMAMGR.scr:306
    ctx:set("z", "z + rand") -- CINEMAMGR.scr:307
    ctx:set("rand", "20 / nSpeed") -- CINEMAMGR.scr:308
    ctx:wait(6, "rand", "ShakeCamera") -- CINEMAMGR.scr:309
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:310
end

script.labels["SpinCamera"] = function(ctx)
    -- CINEMAMGR.scr:313
    -- rotates camera as it zooms
    ctx:self():rotate("dx", "dy", "dz", "nAngle", "nAngSpeed", "DoNothing") -- CINEMAMGR.scr:316
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:317
end

-- Generic routines
script.labels["AlignCamera"] = function(ctx)
    -- CINEMAMGR.scr:325
    -- sets pos and dir to player's
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:player():pos() -- CINEMAMGR.scr:328
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:player():rotation() -- CINEMAMGR.scr:329
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- CINEMAMGR.scr:330
    ctx:set("y", "y + 38") -- CINEMAMGR.scr:331
    ctx:self():setPos("x", "y", "z") -- CINEMAMGR.scr:332
    ctx:self():faceDir("dx", "dy", "dz", 0, "DoNothing") -- CINEMAMGR.scr:333
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:334
end

script.labels["ReverseDirections"] = function(ctx)
    -- CINEMAMGR.scr:337
    ctx:state().dirScale = -1 -- CINEMAMGR.scr:339
    ctx:state().bArrived = false -- CINEMAMGR.scr:340
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:341
end

script.labels["SetupPan"] = function(ctx)
    -- CINEMAMGR.scr:344
    -- prepares pan vars:
    -- pan angle, turn speed
    -- GetPOS hPanNode1, x,y,z
    -- GetAngleToPOS x,y,z, nPanWidth
    ctx:set("nPanSpeed", "nPanWidth / nPanTime") -- CINEMAMGR.scr:350
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:351
end

script.labels["SetupZoom"] = function(ctx)
    -- CINEMAMGR.scr:354
    -- prepares zoom vars:
    -- dir, speed, rotation, distance
    ctx:self():setTarget(ctx:object("hTarget")) -- CINEMAMGR.scr:358
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:self():rotation() -- CINEMAMGR.scr:359
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- CINEMAMGR.scr:360
    ctx:state().dist = ctx:self():distanceTo(ctx:object("hTarget")) -- CINEMAMGR.scr:361
    ctx:set("dist", "dist - 100") -- CINEMAMGR.scr:362
    ctx:set("nSpeed", "dist / dt") -- CINEMAMGR.scr:363
    ctx:set("nAngle", "180 * dirScale") -- CINEMAMGR.scr:364
    ctx:set("nAngSpeed", "nAngle / dt") -- CINEMAMGR.scr:365
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:366
end

script.labels["CameraOn"] = function(ctx)
    -- CINEMAMGR.scr:369
    ctx:trigger("hMe", "On") -- CINEMAMGR.scr:371
    ctx:letterBox("TRUE") -- CINEMAMGR.scr:372
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:373
end

script.labels["CameraOff"] = function(ctx)
    -- CINEMAMGR.scr:376
    ctx:self():setTarget(nil) -- CINEMAMGR.scr:378
    ctx:state().bArrived = false -- CINEMAMGR.scr:379
    ctx:trigger("hMe", "Off") -- CINEMAMGR.scr:380
    ctx:letterBox("FALSE") -- CINEMAMGR.scr:381
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:382
end

script.labels["SetupAllTriggers"] = function(ctx)
    -- CINEMAMGR.scr:385
    ctx:setCallback(0, "ChangeTarget0") -- CINEMAMGR.scr:387
    ctx:setCallback(1, "ChangeTarget1") -- CINEMAMGR.scr:388
    ctx:setCallback(2, "ChangeTarget2") -- CINEMAMGR.scr:389
    ctx:setCallback(3, "ChangeTarget3") -- CINEMAMGR.scr:390
    ctx:addTrigger("Pan180", "SetPanFull") -- CINEMAMGR.scr:392
    ctx:addTrigger("Pan135", "SetPanHalf") -- CINEMAMGR.scr:393
    ctx:addTrigger("Pan90", "SetPanQuarter") -- CINEMAMGR.scr:394
    ctx:addTrigger("PanFast", "SetPanFast") -- CINEMAMGR.scr:396
    ctx:addTrigger("PanMedium", "SetPanMedium") -- CINEMAMGR.scr:397
    ctx:addTrigger("PanSlow", "SetPanSlow") -- CINEMAMGR.scr:398
    ctx:addTrigger("PanToZoom", "SetPanToZoom") -- CINEMAMGR.scr:400
    ctx:addTrigger("CamSnapto", "SetCamSnapto") -- CINEMAMGR.scr:402
    ctx:addTrigger("CamSnapback", "SetCamSnapback") -- CINEMAMGR.scr:403
    ctx:addTrigger("CamPullback", "SetCamPullback") -- CINEMAMGR.scr:404
    ctx:addTrigger("CamSmooth", "SetCamSmooth") -- CINEMAMGR.scr:406
    ctx:addTrigger("CamRough", "SetCamRough") -- CINEMAMGR.scr:407
    ctx:addTrigger("CamSpin", "SetCamSpin") -- CINEMAMGR.scr:408
    ctx:addTrigger("CamFast", "SetCamFast") -- CINEMAMGR.scr:410
    ctx:addTrigger("CamMedium", "SetCamMedium") -- CINEMAMGR.scr:411
    ctx:addTrigger("CamSlow", "SetCamSlow") -- CINEMAMGR.scr:412
    ctx:addTrigger("CamLong", "SetCamLong") -- CINEMAMGR.scr:414
    ctx:addTrigger("CamShort", "SetCamShort") -- CINEMAMGR.scr:415
    ctx:addTrigger("CamInstant", "SetCamInstant") -- CINEMAMGR.scr:416
    ctx:addTrigger("CamTarget1", "ChangeTarget0") -- CINEMAMGR.scr:418
    ctx:addTrigger("CamTarget2", "ChangeTarget1") -- CINEMAMGR.scr:419
    ctx:addTrigger("CamTarget3", "ChangeTarget2") -- CINEMAMGR.scr:420
    ctx:addTrigger("CamTarget4", "ChangeTarget3") -- CINEMAMGR.scr:421
    ctx:addTrigger("BasicZoom", "SetBasicZoom") -- CINEMAMGR.scr:423
    ctx:addTrigger("LinkOn", "SetCamLink") -- CINEMAMGR.scr:424
    ctx:addTrigger("LinkOff", "DisableCamLink") -- CINEMAMGR.scr:425
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:427
end

script.labels["GetNextTarget"] = function(ctx)
    -- CINEMAMGR.scr:429
    ctx:set("nCurTarget", "nCurTarget + 1") -- CINEMAMGR.scr:430
    ctx:doCallback("nCurTarget") -- CINEMAMGR.scr:431
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:432
end

script.labels["SetCamLink"] = function(ctx)
    -- CINEMAMGR.scr:433
    ctx:state().bLink = true -- CINEMAMGR.scr:434
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:435
end

script.labels["DisableCamLink"] = function(ctx)
    -- CINEMAMGR.scr:436
    ctx:state().bLink = false -- CINEMAMGR.scr:437
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:438
end

script.labels["SetPanFull"] = function(ctx)
    -- CINEMAMGR.scr:439
    ctx:state().nPanWidth = 180 -- CINEMAMGR.scr:440
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:441
end

script.labels["SetPanHalf"] = function(ctx)
    -- CINEMAMGR.scr:442
    ctx:state().nPanWidth = 135 -- CINEMAMGR.scr:443
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:444
end

script.labels["SetPanQuarter"] = function(ctx)
    -- CINEMAMGR.scr:445
    ctx:state().nPanWidth = 90 -- CINEMAMGR.scr:446
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:447
end

script.labels["SetPanFast"] = function(ctx)
    -- CINEMAMGR.scr:448
    ctx:state().nPanTime = 3 -- CINEMAMGR.scr:449
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:450
end

script.labels["SetPanMedium"] = function(ctx)
    -- CINEMAMGR.scr:451
    ctx:state().nPanTime = 6 -- CINEMAMGR.scr:452
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:453
end

script.labels["SetPanSlow"] = function(ctx)
    -- CINEMAMGR.scr:454
    ctx:state().nPanTime = 9 -- CINEMAMGR.scr:455
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:456
end

script.labels["SetPanToZoom"] = function(ctx)
    -- CINEMAMGR.scr:457
    ctx:state().bDoZoom = true -- CINEMAMGR.scr:458
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:459
end

script.labels["SetBasicZoom"] = function(ctx)
    -- CINEMAMGR.scr:460
    mm9.gosub(script, ctx, "SetCamSnapback") -- CINEMAMGR.scr:461
    mm9.gosub(script, ctx, "SetCamSmooth") -- CINEMAMGR.scr:462
    mm9.gosub(script, ctx, "SetCamFast") -- CINEMAMGR.scr:463
    mm9.gosub(script, ctx, "SetCamShort") -- CINEMAMGR.scr:464
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:465
end

script.labels["SetCamSnapto"] = function(ctx)
    -- CINEMAMGR.scr:466
    ctx:state().bSnapto = true -- CINEMAMGR.scr:467
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:468
end

script.labels["SetCamSnapback"] = function(ctx)
    -- CINEMAMGR.scr:469
    ctx:state().bSnapback = true -- CINEMAMGR.scr:470
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:471
end

script.labels["SetCamPullback"] = function(ctx)
    -- CINEMAMGR.scr:472
    ctx:state().bSnapback = false -- CINEMAMGR.scr:473
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:474
end

script.labels["SetCamSmooth"] = function(ctx)
    -- CINEMAMGR.scr:475
    ctx:state().bSmooth = true -- CINEMAMGR.scr:476
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:477
end

script.labels["SetCamRough"] = function(ctx)
    -- CINEMAMGR.scr:478
    ctx:state().bSmooth = false -- CINEMAMGR.scr:479
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:480
end

script.labels["SetCamSpin"] = function(ctx)
    -- CINEMAMGR.scr:481
    ctx:state().bSpin = true -- CINEMAMGR.scr:482
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:483
end

script.labels["SetCamFast"] = function(ctx)
    -- CINEMAMGR.scr:484
    ctx:set("dt", .5) -- CINEMAMGR.scr:485
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:486
end

script.labels["SetCamMedium"] = function(ctx)
    -- CINEMAMGR.scr:487
    ctx:state().dt = 2 -- CINEMAMGR.scr:488
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:489
end

script.labels["SetCamSlow"] = function(ctx)
    -- CINEMAMGR.scr:490
    ctx:state().dt = 4 -- CINEMAMGR.scr:491
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:492
end

script.labels["SetCamLong"] = function(ctx)
    -- CINEMAMGR.scr:493
    ctx:state().tLinger = 6 -- CINEMAMGR.scr:494
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:495
end

script.labels["SetCamShort"] = function(ctx)
    -- CINEMAMGR.scr:496
    ctx:state().tLinger = 3 -- CINEMAMGR.scr:497
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:498
end

script.labels["SetCamInstant"] = function(ctx)
    -- CINEMAMGR.scr:499
    ctx:set("tLinger", .5) -- CINEMAMGR.scr:500
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:501
end

script.labels["ChangeTarget0"] = function(ctx)
    -- CINEMAMGR.scr:502
    ctx:state().nCurTarget = 0 -- CINEMAMGR.scr:503
    ctx:state().hTarget = ctx:objectOrNil("sFocus0Name") -- CINEMAMGR.scr:504
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:505
end

script.labels["ChangeTarget1"] = function(ctx)
    -- CINEMAMGR.scr:506
    ctx:state().nCurTarget = 1 -- CINEMAMGR.scr:507
    ctx:state().hTarget = ctx:objectOrNil("sFocus1Name") -- CINEMAMGR.scr:508
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:509
end

script.labels["ChangeTarget2"] = function(ctx)
    -- CINEMAMGR.scr:510
    ctx:state().nCurTarget = 2 -- CINEMAMGR.scr:511
    ctx:state().hTarget = ctx:objectOrNil("sFocus2Name") -- CINEMAMGR.scr:512
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:513
end

script.labels["ChangeTarget3"] = function(ctx)
    -- CINEMAMGR.scr:514
    ctx:state().nCurTarget = 3 -- CINEMAMGR.scr:515
    ctx:state().hTarget = ctx:objectOrNil("sFocus3Name") -- CINEMAMGR.scr:516
    do return ctx:exit("TRUE") end -- CINEMAMGR.scr:517
end

return script
