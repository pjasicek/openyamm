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
    ctx:command("setvelocity", "g_hMyObject, 200, 0, 0") -- CAMERATEST.scr:38
    ctx:command("wait", "5, VelocityTest2") -- CAMERATEST.scr:40
    do return ctx:exit("") end -- CAMERATEST.scr:42
end

script.labels["VelocityTest2"] = function(ctx)
    -- CAMERATEST.scr:45
    ctx:command("setvelocity", "g_hMyObject, 0, 0, 100") -- CAMERATEST.scr:48
    ctx:command("wait", "5, VelocityTest3") -- CAMERATEST.scr:50
    do return ctx:exit("") end -- CAMERATEST.scr:52
end

script.labels["VelocityTest3"] = function(ctx)
    -- CAMERATEST.scr:55
    ctx:command("setvelocity", "g_hMyObject, -100, 0, 0") -- CAMERATEST.scr:58
    ctx:command("wait", "5, VelocityTest4") -- CAMERATEST.scr:60
    do return ctx:exit("") end -- CAMERATEST.scr:62
end

script.labels["VelocityTest4"] = function(ctx)
    -- CAMERATEST.scr:65
    ctx:command("setvelocity", "g_hMyObject, 0, 0, -100") -- CAMERATEST.scr:68
    ctx:command("wait", "5, StopCamera") -- CAMERATEST.scr:70
    do return ctx:exit("") end -- CAMERATEST.scr:72
end

script.labels["StopCamera"] = function(ctx)
    -- CAMERATEST.scr:75
    ctx:command("setvelocity", "g_hMyObject, 0,0,0") -- CAMERATEST.scr:78
    ctx:trigger("g_hMyObject", "OFF") -- CAMERATEST.scr:79
    do return ctx:exit("") end -- CAMERATEST.scr:81
end

script.labels["RotationTest1"] = function(ctx)
    -- CAMERATEST.scr:84
    ctx:command("debugout", "RotationTest1 executing!!") -- CAMERATEST.scr:87
    -- FaceDir 0,1,0,45
    -- Rotate 1,0,1,90,45
    ctx:command("rotate", "0,1,0,90,45") -- CAMERATEST.scr:91
    ctx:command("wait", "5, RotationTest2") -- CAMERATEST.scr:93
    do return ctx:exit("") end -- CAMERATEST.scr:95
end

script.labels["RotationTest2"] = function(ctx)
    -- CAMERATEST.scr:98
    ctx:command("debugout", "RotationTest2 executing!!") -- CAMERATEST.scr:101
    -- FaceDir 0,0,1,45
    -- Rotate -1,0,-1,90,45
    ctx:command("rotate", "0,1,0,-90,45") -- CAMERATEST.scr:105
    ctx:command("wait", "5, StopCamera") -- CAMERATEST.scr:107
    do return ctx:exit("") end -- CAMERATEST.scr:109
end

script.labels["FollowPlayerTest"] = function(ctx)
    -- CAMERATEST.scr:112
    ctx:command("getplayerhandle", "hPlayerObject, 2000") -- CAMERATEST.scr:115
    if ctx:condition("hPlayerObject!=0") then -- CAMERATEST.scr:117
        ctx:command("target", "hPlayerObject") -- CAMERATEST.scr:118
        -- Wait 20, StopCamera
    end -- CAMERATEST.scr:120
    do return ctx:exit("") end -- CAMERATEST.scr:123
end

script.labels["FollowPlayerTest2"] = function(ctx)
    -- CAMERATEST.scr:126
    mm9.gosub(script, ctx, "FollowPlayerTest2Tick") -- CAMERATEST.scr:129
    ctx:command("wait", "0.01, FollowPlayerTest2Tick") -- CAMERATEST.scr:130
    do return ctx:exit("") end -- CAMERATEST.scr:131
end

script.labels["FollowPlayerTest2Tick"] = function(ctx)
    -- CAMERATEST.scr:134
    ctx:command("faceobject", "hPlayerObject, 45") -- CAMERATEST.scr:137
    ctx:command("wait", "0.01, FollowPlayerTest2Tick") -- CAMERATEST.scr:138
    do return ctx:exit("") end -- CAMERATEST.scr:140
end

script.labels["MoveTest"] = function(ctx)
    -- CAMERATEST.scr:145
    ctx:command("getpos", "g_hMyObject, nPosX,nPosY,nPosZ") -- CAMERATEST.scr:148
    ctx:command("add", "nPosY, 100") -- CAMERATEST.scr:149
    ctx:command("movetopos", "nPosX,nPosY,nPosZ,100,MoveTest2") -- CAMERATEST.scr:151
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
    ctx:command("debugout", "Follow Path Done! Stopping Camera!") -- CAMERATEST.scr:171
    mm9.gosub(script, ctx, "StopCamera") -- CAMERATEST.scr:173
    do return ctx:exit(0) end -- CAMERATEST.scr:175
end

script.labels["OpenDoor"] = function(ctx)
    -- CAMERATEST.scr:178
    -- Parameters:
    -- p1	- name of door
    ctx:getParam(0, "g_sTemp") -- CAMERATEST.scr:184
    ctx:command("getobjecthandle", "g_sTemp, hTestObject") -- CAMERATEST.scr:186
    if ctx:condition("hTestObject!=0") then -- CAMERATEST.scr:188
        ctx:trigger("hTestObject", "UNLOCK") -- CAMERATEST.scr:189
        ctx:trigger("hTestObject", "USE") -- CAMERATEST.scr:190
    end -- CAMERATEST.scr:191
    do return ctx:exit("") end -- CAMERATEST.scr:193
end

script.labels["OpenDoors"] = function(ctx)
    -- CAMERATEST.scr:196
    ctx:command("getobjects", "Door, 500, 20, hDoorArray, nDoorArrayCount") -- CAMERATEST.scr:199
    ctx:command("debugout", "OpeningDoors!!!!") -- CAMERATEST.scr:201
    if ctx:condition("nDoorArrayCount==0") then -- CAMERATEST.scr:203
        ctx:command("debugout", "What? NO DOORS?????") -- CAMERATEST.scr:204
        do return ctx:exit("") end -- CAMERATEST.scr:205
    end -- CAMERATEST.scr:206
    ctx:command("debugout", "Total of:") -- CAMERATEST.scr:208
    ctx:command("debugout", "nDoorArrayCount") -- CAMERATEST.scr:209
    ctx:command("debugout", "doors") -- CAMERATEST.scr:210
    ctx:command("set", "g_nCounter, 0") -- CAMERATEST.scr:212
end

script.labels["OpenDoorLoop"] = function(ctx)
    -- CAMERATEST.scr:214
    ctx:command("arrayget", "hDoorArray, g_nCounter, hTestObject") -- CAMERATEST.scr:216
    if ctx:condition("hTestObject==0") then -- CAMERATEST.scr:218
        do return ctx:exit("") end -- CAMERATEST.scr:219
    end -- CAMERATEST.scr:220
    ctx:trigger("hTestObject", "UNLOCK") -- CAMERATEST.scr:222
    ctx:trigger("hTestObject", "USE") -- CAMERATEST.scr:223
    ctx:command("add", "g_nCounter, 1") -- CAMERATEST.scr:225
    if ctx:condition("g_nCounter >= nDoorArrayCount") then -- CAMERATEST.scr:227
        do return ctx:exit("") end -- CAMERATEST.scr:228
    end -- CAMERATEST.scr:229
    do return mm9.gotoLabel(script, ctx, "OpenDoorLoop") end -- CAMERATEST.scr:231
    ctx:command("setparam", "0, Door0") -- CAMERATEST.scr:235
    mm9.gosub(script, ctx, "OpenDoor") -- CAMERATEST.scr:236
    ctx:command("setparam", "0, RotatingDoor0") -- CAMERATEST.scr:238
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
    ctx:command("set", "g_sFollowPathName, CameraPath") -- CAMERATEST.scr:259
    ctx:command("set", "g_nFollowPathSpeed, 120") -- CAMERATEST.scr:260
    ctx:command("set", "g_nFollowPathCallback, 0") -- CAMERATEST.scr:261
    ctx:command("set", "g_nFollowPathDoneCallback, 1") -- CAMERATEST.scr:262
    ctx:command("setcallback", "g_nFollowPathCallback, FollowPathWayPoint") -- CAMERATEST.scr:264
    ctx:command("setcallback", "g_nFollowPathDoneCallback, FollowPathDone") -- CAMERATEST.scr:265
    mm9.gosub(script, ctx, "FollowPath") -- CAMERATEST.scr:267
    do return ctx:exit("") end -- CAMERATEST.scr:269
end

script.labels["Trigger_ON"] = function(ctx)
    -- CAMERATEST.scr:272
    ctx:command("setpos", "g_hMyObject,nStartPosX,nStartPosY,nStartPosZ") -- CAMERATEST.scr:275
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
    ctx:command("debugout", "TriggerOFF!!!") -- CAMERATEST.scr:303
    do return ctx:exit(0) end -- CAMERATEST.scr:304
end

script.labels["Main"] = function(ctx)
    -- CAMERATEST.scr:307
    ctx:addTrigger("ON", "Trigger_ON") -- CAMERATEST.scr:310
    ctx:addTrigger("OFF", "Trigger_OFF") -- CAMERATEST.scr:311
    ctx:command("getmyhandle", "g_hMyObject") -- CAMERATEST.scr:313
    ctx:command("getpos", "g_hMyObject,nStartPosX,nStartPosY,nStartPosZ") -- CAMERATEST.scr:315
    -- ConsoleCommand ShowFrameRate 1
    do return ctx:exit("") end -- CAMERATEST.scr:320
end

return script
