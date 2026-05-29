-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CAMERATEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "FollowPath.inc" }

-- CameraTest.scr
-- Jeff Leggett
-- Parameters:
-- none
script.labels["VelocityTest1"] = function(ctx)
    -- CAMERATEST.scr:35
    ctx:self():setVelocity(200, 0, 0) -- CAMERATEST.scr:38
    ctx:wait(5, 5, "VelocityTest2") -- CAMERATEST.scr:40
    do return ctx:exit("") end -- CAMERATEST.scr:42
end

script.labels["VelocityTest2"] = function(ctx)
    -- CAMERATEST.scr:45
    ctx:self():setVelocity(0, 0, 100) -- CAMERATEST.scr:48
    ctx:wait(5, 5, "VelocityTest3") -- CAMERATEST.scr:50
    do return ctx:exit("") end -- CAMERATEST.scr:52
end

script.labels["VelocityTest3"] = function(ctx)
    -- CAMERATEST.scr:55
    ctx:self():setVelocity(-100, 0, 0) -- CAMERATEST.scr:58
    ctx:wait(5, 5, "VelocityTest4") -- CAMERATEST.scr:60
    do return ctx:exit("") end -- CAMERATEST.scr:62
end

script.labels["VelocityTest4"] = function(ctx)
    -- CAMERATEST.scr:65
    ctx:self():setVelocity(0, 0, -100) -- CAMERATEST.scr:68
    ctx:wait(5, 5, "StopCamera") -- CAMERATEST.scr:70
    do return ctx:exit("") end -- CAMERATEST.scr:72
end

script.labels["StopCamera"] = function(ctx)
    -- CAMERATEST.scr:75
    ctx:self():setVelocity(0, 0, 0) -- CAMERATEST.scr:78
    ctx:trigger("g_hMyObject", "OFF") -- CAMERATEST.scr:79
    do return ctx:exit("") end -- CAMERATEST.scr:81
end

script.labels["RotationTest1"] = function(ctx)
    -- CAMERATEST.scr:84
    ctx:debugOut("RotationTest1", "executing!!") -- CAMERATEST.scr:87
    -- FaceDir 0,1,0,45
    -- Rotate 1,0,1,90,45
    ctx:self():rotate(0, 1, 0, 90, 45) -- CAMERATEST.scr:91
    ctx:wait(5, 5, "RotationTest2") -- CAMERATEST.scr:93
    do return ctx:exit("") end -- CAMERATEST.scr:95
end

script.labels["RotationTest2"] = function(ctx)
    -- CAMERATEST.scr:98
    ctx:debugOut("RotationTest2", "executing!!") -- CAMERATEST.scr:101
    -- FaceDir 0,0,1,45
    -- Rotate -1,0,-1,90,45
    ctx:self():rotate(0, 1, 0, -90, 45) -- CAMERATEST.scr:105
    ctx:wait(5, 5, "StopCamera") -- CAMERATEST.scr:107
    do return ctx:exit("") end -- CAMERATEST.scr:109
end

script.labels["FollowPlayerTest"] = function(ctx)
    -- CAMERATEST.scr:112
    ctx:state().hPlayerObject = ctx:player() -- CAMERATEST.scr:115
    if ctx:condition("hPlayerObject!=0") then -- CAMERATEST.scr:117
        ctx:self():setTarget(ctx:object("hPlayerObject")) -- CAMERATEST.scr:118
        -- Wait 20, StopCamera
    end -- CAMERATEST.scr:120
    do return ctx:exit("") end -- CAMERATEST.scr:123
end

script.labels["FollowPlayerTest2"] = function(ctx)
    -- CAMERATEST.scr:126
    mm9.gosub(script, ctx, "FollowPlayerTest2Tick") -- CAMERATEST.scr:129
    ctx:wait(0.01, 0.01, "FollowPlayerTest2Tick") -- CAMERATEST.scr:130
    do return ctx:exit("") end -- CAMERATEST.scr:131
end

script.labels["FollowPlayerTest2Tick"] = function(ctx)
    -- CAMERATEST.scr:134
    ctx:self():faceObject(ctx:object("hPlayerObject"), 45) -- CAMERATEST.scr:137
    ctx:wait(0.01, 0.01, "FollowPlayerTest2Tick") -- CAMERATEST.scr:138
    do return ctx:exit("") end -- CAMERATEST.scr:140
end

script.labels["MoveTest"] = function(ctx)
    -- CAMERATEST.scr:145
    ctx:state().nPosX, ctx:state().nPosY, ctx:state().nPosZ = ctx:self():pos() -- CAMERATEST.scr:148
    ctx:state().nPosY = (tonumber(ctx:state().nPosY) or 0) + 100 -- CAMERATEST.scr:149
    ctx:self():moveToPos("nPosX", "nPosY", "nPosZ", 100, "MoveTest2") -- CAMERATEST.scr:151
    do return ctx:exit("") end -- CAMERATEST.scr:153
end

script.labels["MoveTest2"] = function(ctx)
    -- CAMERATEST.scr:156
    -- Sub nPosY, 100
    -- MoveToPos nPosX,nPosY,nPosZ,100,MoveTest
    mm9.gosub(script, ctx, "StopCamera") -- CAMERATEST.scr:162
    do return ctx:exit(0) end -- CAMERATEST.scr:164
end

script.labels["FollowPathDone"] = function(ctx)
    -- CAMERATEST.scr:168
    ctx:debugOut("Follow", "Path", "Done!", "Stopping", "Camera!") -- CAMERATEST.scr:171
    mm9.gosub(script, ctx, "StopCamera") -- CAMERATEST.scr:173
    do return ctx:exit(0) end -- CAMERATEST.scr:175
end

script.labels["OpenDoor"] = function(ctx)
    -- CAMERATEST.scr:178
    -- Parameters:
    -- p1	- name of door
    ctx:getParam(0, "g_sTemp") -- CAMERATEST.scr:184
    ctx:state().hTestObject = ctx:objectOrNil("g_sTemp") -- CAMERATEST.scr:186
    if ctx:condition("hTestObject!=0") then -- CAMERATEST.scr:188
        ctx:trigger("hTestObject", "UNLOCK") -- CAMERATEST.scr:189
        ctx:trigger("hTestObject", "USE") -- CAMERATEST.scr:190
    end -- CAMERATEST.scr:191
    do return ctx:exit("") end -- CAMERATEST.scr:193
end

script.labels["OpenDoors"] = function(ctx)
    -- CAMERATEST.scr:196
    ctx:getObjects("Door", 500, 20, "hDoorArray", "nDoorArrayCount") -- CAMERATEST.scr:199
    ctx:debugOut("OpeningDoors!!!!") -- CAMERATEST.scr:201
    if ctx:condition("nDoorArrayCount==0") then -- CAMERATEST.scr:203
        ctx:debugOut("What?", "NO", "DOORS?????") -- CAMERATEST.scr:204
        do return ctx:exit("") end -- CAMERATEST.scr:205
    end -- CAMERATEST.scr:206
    ctx:debugOut("Total", "of:") -- CAMERATEST.scr:208
    ctx:debugOut("nDoorArrayCount") -- CAMERATEST.scr:209
    ctx:debugOut("doors") -- CAMERATEST.scr:210
    ctx:state().g_nCounter = 0 -- CAMERATEST.scr:212
end

script.labels["OpenDoorLoop"] = function(ctx)
    -- CAMERATEST.scr:214
    ctx:arrayGet("hDoorArray", "g_nCounter", "hTestObject") -- CAMERATEST.scr:216
    if ctx:condition("hTestObject==0") then -- CAMERATEST.scr:218
        do return ctx:exit("") end -- CAMERATEST.scr:219
    end -- CAMERATEST.scr:220
    ctx:trigger("hTestObject", "UNLOCK") -- CAMERATEST.scr:222
    ctx:trigger("hTestObject", "USE") -- CAMERATEST.scr:223
    ctx:state().g_nCounter = (tonumber(ctx:state().g_nCounter) or 0) + 1 -- CAMERATEST.scr:225
    if ctx:condition("g_nCounter >= nDoorArrayCount") then -- CAMERATEST.scr:227
        do return ctx:exit("") end -- CAMERATEST.scr:228
    end -- CAMERATEST.scr:229
    do return mm9.gotoLabel(script, ctx, "OpenDoorLoop") end -- CAMERATEST.scr:231
    ctx:setParam(0, "Door0") -- CAMERATEST.scr:235
    mm9.gosub(script, ctx, "OpenDoor") -- CAMERATEST.scr:236
    ctx:setParam(0, "RotatingDoor0") -- CAMERATEST.scr:238
    mm9.gosub(script, ctx, "OpenDoor") -- CAMERATEST.scr:239
    do return ctx:exit("") end -- CAMERATEST.scr:241
end

script.labels["FollowPathWayPoint"] = function(ctx)
    -- CAMERATEST.scr:244
    if ctx:condition("g_nFollowPathNbr==1") then -- CAMERATEST.scr:247
        mm9.gosub(script, ctx, "OpenDoors") -- CAMERATEST.scr:248
    end -- CAMERATEST.scr:249
    do return ctx:exit("") end -- CAMERATEST.scr:251
end

script.labels["FollowPathTest"] = function(ctx)
    -- CAMERATEST.scr:254
    mm9.gosub(script, ctx, "FollowPathInit") -- CAMERATEST.scr:257
    ctx:set("g_sFollowPathName", "CameraPath") -- CAMERATEST.scr:259
    ctx:state().g_nFollowPathSpeed = 120 -- CAMERATEST.scr:260
    ctx:state().g_nFollowPathCallback = 0 -- CAMERATEST.scr:261
    ctx:state().g_nFollowPathDoneCallback = 1 -- CAMERATEST.scr:262
    ctx:setCallback("g_nFollowPathCallback", "FollowPathWayPoint") -- CAMERATEST.scr:264
    ctx:setCallback("g_nFollowPathDoneCallback", "FollowPathDone") -- CAMERATEST.scr:265
    mm9.gosub(script, ctx, "FollowPath") -- CAMERATEST.scr:267
    do return ctx:exit("") end -- CAMERATEST.scr:269
end

script.labels["Trigger_ON"] = function(ctx)
    -- CAMERATEST.scr:272
    ctx:self():setPos("nStartPosX", "nStartPosY", "nStartPosZ") -- CAMERATEST.scr:275
    -- gosub VelocityTest1
    -- gosub RotationTest1
    -- gosub FollowPlayerTest
    ctx:getParam(0, "hPlayerObject") -- CAMERATEST.scr:284
    -- gosub FollowPlayerTest2
    -- if ( hPlayerObject==0 )
    -- Exit 1
    -- endif
    -- Wait 10, StopCamera
    -- gosub MoveTest
    mm9.gosub(script, ctx, "FollowPathTest") -- CAMERATEST.scr:295
    do return ctx:exit(0) end -- CAMERATEST.scr:297
end

script.labels["Trigger_OFF"] = function(ctx)
    -- CAMERATEST.scr:300
    ctx:debugOut("TriggerOFF!!!") -- CAMERATEST.scr:303
    do return ctx:exit(0) end -- CAMERATEST.scr:304
end

script.labels["Main"] = function(ctx)
    -- CAMERATEST.scr:307
    ctx:addTrigger("ON", "Trigger_ON") -- CAMERATEST.scr:310
    ctx:addTrigger("OFF", "Trigger_OFF") -- CAMERATEST.scr:311
    ctx:state().nStartPosX, ctx:state().nStartPosY, ctx:state().nStartPosZ = ctx:self():pos() -- CAMERATEST.scr:315
    -- ConsoleCommand ShowFrameRate 1
    do return ctx:exit("") end -- CAMERATEST.scr:320
end

return script
