-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ALTCINEMAMGR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 33, path = "ListMaker.inc" }
script.includes[#script.includes + 1] = { line = 34, path = "BaseGlobals.inc" }

-- CinemaMgr.scr
-- by SJR
-- 10-16-01
-- Purpose:Must be run by a camera
-- object. Handles cut scenes
-- ScriptParams are:
-- p0 = root name of locations
-- p1 = root name of targets
-- p2 = root name of notifys (notify gets triggered each scene)
-- p3 = number of scenes
-- Triggers:
-- "StartCam"			= looks at target until triggered otherwise
-- "StartZoom"			= executes a zoom using all current settings
-- "StartPan"			= executes a camera pan using all current settings
-- "AdvanceCam"		= moves to next location and target
-- "StopCam"			= turns camera off
-- ZoomEffects
-- "CamSnapback"		= returns to player instantaneously
-- "CamPullback"		= zooms out to player
-- "Cam[Fast\Medium\Slow]	= sets speed of zoom-in (1,2,4 seconds of travel)
-- "Cam[Long\Short\Instant]"	= sets duration of watch (6,3,1/2 seconds)
-- Time to stay at target
-- camera POS
-- Directions
script.labels["Main"] = function(ctx)
    -- ALTCINEMAMGR.scr:68
    ctx:getParam(0, "sLocationName") -- ALTCINEMAMGR.scr:70
    ctx:getParam(1, "sTargetName") -- ALTCINEMAMGR.scr:71
    ctx:getParam(2, "sNotifyName") -- ALTCINEMAMGR.scr:72
    ctx:getParam(3, "LISTLAST") -- ALTCINEMAMGR.scr:74
    ctx:set("LISTLAST", "LISTLAST - 1") -- ALTCINEMAMGR.scr:76
    ctx:state().LISTFIRST = 0 -- ALTCINEMAMGR.scr:77
    ctx:wait(0, 4, "InitCinemaMgr") -- ALTCINEMAMGR.scr:79
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:81
end

script.labels["InitCinemaMgr"] = function(ctx)
    -- ALTCINEMAMGR.scr:84
    mm9.gosub(script, ctx, "SetupAllTriggers") -- ALTCINEMAMGR.scr:86
    ctx:addTrigger("StartZoom", "StartZoom") -- ALTCINEMAMGR.scr:88
    -- get last one, then wrap to first
    mm9.gosub(script, ctx, "GetLastObject") -- ALTCINEMAMGR.scr:91
    mm9.gosub(script, ctx, "GetNextLocation") -- ALTCINEMAMGR.scr:92
    ctx:state().hNotify = ctx:objectOrNil("sNotifyName") -- ALTCINEMAMGR.scr:94
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:97
end

script.labels["AdvanceCam"] = function(ctx)
    -- ALTCINEMAMGR.scr:100
    mm9.gosub(script, ctx, "GetNextLocation") -- ALTCINEMAMGR.scr:102
    mm9.gosub(script, ctx, "StartCam") -- ALTCINEMAMGR.scr:103
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:104
end

script.labels["StartCam"] = function(ctx)
    -- ALTCINEMAMGR.scr:107
    if ctx:condition("hTarget==0") then -- ALTCINEMAMGR.scr:109
        mm9.gosub(script, ctx, "CameraOff") -- ALTCINEMAMGR.scr:110
    end -- ALTCINEMAMGR.scr:111
    mm9.gosub(script, ctx, "AlignCamera") -- ALTCINEMAMGR.scr:112
    ctx:self():setTarget(ctx:object("hTarget")) -- ALTCINEMAMGR.scr:113
    ctx:trigger("hNotify", "trigger") -- ALTCINEMAMGR.scr:114
    mm9.gosub(script, ctx, "CameraOn") -- ALTCINEMAMGR.scr:115
    ctx:wait(0, 5, "AdvanceCam") -- ALTCINEMAMGR.scr:116
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:117
end

script.labels["StartZoom"] = function(ctx)
    -- ALTCINEMAMGR.scr:120
    -- zooms to hTarget from hPlayer
    if ctx:condition("bSnapTo==TRUE") then -- ALTCINEMAMGR.scr:123
        ctx:self():faceObject(ctx:object("hTarget"), 720, "MoveCameraForward") -- ALTCINEMAMGR.scr:124
        ctx:wait(9, "dt", "CameraOn") -- ALTCINEMAMGR.scr:125
    else -- ALTCINEMAMGR.scr:126
        mm9.gosub(script, ctx, "AlignCamera") -- ALTCINEMAMGR.scr:127
        mm9.gosub(script, ctx, "ExecuteZoom") -- ALTCINEMAMGR.scr:128
    end -- ALTCINEMAMGR.scr:129
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:130
end

script.labels["ExecuteZoom"] = function(ctx)
    -- ALTCINEMAMGR.scr:133
    -- zooms to hTarget from current pos
    ctx:state().dirScale = 1 -- ALTCINEMAMGR.scr:136
    ctx:self():faceObject(ctx:object("hTarget"), 360, "MoveCameraForward") -- ALTCINEMAMGR.scr:137
    mm9.gosub(script, ctx, "CameraOn") -- ALTCINEMAMGR.scr:138
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:139
end

script.labels["MoveCameraForward"] = function(ctx)
    -- ALTCINEMAMGR.scr:142
    -- zooms in current direction for
    -- distance to hTarget using current options
    mm9.gosub(script, ctx, "SetupZoom") -- ALTCINEMAMGR.scr:146
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecScale("dx", "dy", "dz", "dirScale") -- ALTCINEMAMGR.scr:147
    if ctx:condition("DirScale<0") then -- ALTCINEMAMGR.scr:148
        ctx:self():moveDir("dx", "dy", "dz", "ds", "nSpeed", "CameraOff") -- ALTCINEMAMGR.scr:149
    else -- ALTCINEMAMGR.scr:150
        ctx:self():moveDir("dx", "dy", "dz", "ds", "nSpeed", "EndZoom") -- ALTCINEMAMGR.scr:151
    end -- ALTCINEMAMGR.scr:152
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:153
end

script.labels["EndZoom"] = function(ctx)
    -- ALTCINEMAMGR.scr:156
    -- checks for zoomout
    ctx:self():stop() -- ALTCINEMAMGR.scr:159
    ctx:state().bArrived = true -- ALTCINEMAMGR.scr:160
    if ctx:condition("bSnapback==TRUE") then -- ALTCINEMAMGR.scr:161
        ctx:wait(7, "tLinger", "CameraOff") -- ALTCINEMAMGR.scr:162
    else -- ALTCINEMAMGR.scr:163
        mm9.gosub(script, ctx, "ReverseDirection") -- ALTCINEMAMGR.scr:164
        ctx:wait(7, "tLinger", "MoveCameraForward") -- ALTCINEMAMGR.scr:165
    end -- ALTCINEMAMGR.scr:166
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:167
end

-- Generic routines
script.labels["GetNextLocation"] = function(ctx)
    -- ALTCINEMAMGR.scr:174
    ctx:set("LISTNAME", "sLocationName") -- ALTCINEMAMGR.scr:176
    mm9.gosub(script, ctx, "GetNextObject") -- ALTCINEMAMGR.scr:177
    ctx:set("hLocation", "LISTOBJECT") -- ALTCINEMAMGR.scr:178
    ctx:set("LISTNAME", "sTargetName") -- ALTCINEMAMGR.scr:179
    mm9.gosub(script, ctx, "GetCurrentObject") -- ALTCINEMAMGR.scr:180
    ctx:set("hTarget", "LISTOBJECT") -- ALTCINEMAMGR.scr:181
    ctx:set("LISTNAME", "sNotifyName") -- ALTCINEMAMGR.scr:182
    mm9.gosub(script, ctx, "GetCurrentObject") -- ALTCINEMAMGR.scr:183
    ctx:set("hNotify", "LISTOBJECT") -- ALTCINEMAMGR.scr:184
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:186
end

script.labels["AlignCamera"] = function(ctx)
    -- ALTCINEMAMGR.scr:189
    -- sets pos to and dir to hLocation
    ctx:state().xCam, ctx:state().yCam, ctx:state().zCam = ctx:object("hLocation"):pos() -- ALTCINEMAMGR.scr:192
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:object("hLocation"):rotation() -- ALTCINEMAMGR.scr:193
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- ALTCINEMAMGR.scr:194
    ctx:set("yCam", "yCam + 38") -- ALTCINEMAMGR.scr:195
    ctx:self():setPos("xCam", "yCam", "zCam") -- ALTCINEMAMGR.scr:196
    ctx:self():faceDir("dx", "dy", "dz", 0, "DoNothing") -- ALTCINEMAMGR.scr:197
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:198
end

script.labels["ReverseDirection"] = function(ctx)
    -- ALTCINEMAMGR.scr:201
    ctx:state().dirScale = -1 -- ALTCINEMAMGR.scr:203
    ctx:state().bArrived = false -- ALTCINEMAMGR.scr:204
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:205
end

script.labels["SetupZoom"] = function(ctx)
    -- ALTCINEMAMGR.scr:208
    -- prepares zoom vars:
    -- dir, speed, rotation, distance
    ctx:self():setTarget(ctx:object("hTarget")) -- ALTCINEMAMGR.scr:212
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:self():rotation() -- ALTCINEMAMGR.scr:213
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- ALTCINEMAMGR.scr:214
    ctx:state().ds = ctx:self():distanceTo(ctx:object("hTarget")) -- ALTCINEMAMGR.scr:215
    ctx:set("ds", "ds - 100") -- ALTCINEMAMGR.scr:216
    ctx:set("nSpeed", "ds / dt") -- ALTCINEMAMGR.scr:217
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:218
end

script.labels["CameraOn"] = function(ctx)
    -- ALTCINEMAMGR.scr:221
    ctx:trigger("hMe", "On") -- ALTCINEMAMGR.scr:223
    ctx:letterBox("TRUE") -- ALTCINEMAMGR.scr:224
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:225
end

script.labels["CameraOff"] = function(ctx)
    -- ALTCINEMAMGR.scr:228
    ctx:self():setTarget(nil) -- ALTCINEMAMGR.scr:230
    ctx:state().bArrived = false -- ALTCINEMAMGR.scr:231
    ctx:trigger("hMe", "Off") -- ALTCINEMAMGR.scr:232
    ctx:trigger("hNotify", "trigger") -- ALTCINEMAMGR.scr:233
    ctx:letterBox("FALSE") -- ALTCINEMAMGR.scr:234
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:235
end

script.labels["SetupAllTriggers"] = function(ctx)
    -- ALTCINEMAMGR.scr:238
    ctx:addTrigger("StartCam", "StartCam") -- ALTCINEMAMGR.scr:240
    ctx:addTrigger("StopCam", "CameraOff") -- ALTCINEMAMGR.scr:241
    ctx:addTrigger("AdvanceCam", "AdvanceCam") -- ALTCINEMAMGR.scr:242
    ctx:addTrigger("CamSnapback", "SetCamSnapback") -- ALTCINEMAMGR.scr:244
    ctx:addTrigger("CamPullback", "SetCamPullback") -- ALTCINEMAMGR.scr:245
    ctx:addTrigger("CamFast", "SetCamFast") -- ALTCINEMAMGR.scr:247
    ctx:addTrigger("CamMedium", "SetCamMedium") -- ALTCINEMAMGR.scr:248
    ctx:addTrigger("CamSlow", "SetCamSlow") -- ALTCINEMAMGR.scr:249
    ctx:addTrigger("CamLong", "SetCamLong") -- ALTCINEMAMGR.scr:251
    ctx:addTrigger("CamShort", "SetCamShort") -- ALTCINEMAMGR.scr:252
    ctx:addTrigger("CamInstant", "SetCamInstant") -- ALTCINEMAMGR.scr:253
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:255
end

script.labels["SetCamSnapback"] = function(ctx)
    -- ALTCINEMAMGR.scr:257
    ctx:state().bSnapback = true -- ALTCINEMAMGR.scr:258
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:259
end

script.labels["SetCamPullback"] = function(ctx)
    -- ALTCINEMAMGR.scr:260
    ctx:state().bSnapback = false -- ALTCINEMAMGR.scr:261
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:262
end

script.labels["SetCamFast"] = function(ctx)
    -- ALTCINEMAMGR.scr:264
    ctx:set("dt", .5) -- ALTCINEMAMGR.scr:265
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:266
end

script.labels["SetCamMedium"] = function(ctx)
    -- ALTCINEMAMGR.scr:267
    ctx:state().dt = 2 -- ALTCINEMAMGR.scr:268
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:269
end

script.labels["SetCamSlow"] = function(ctx)
    -- ALTCINEMAMGR.scr:270
    ctx:state().dt = 4 -- ALTCINEMAMGR.scr:271
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:272
end

script.labels["SetCamLong"] = function(ctx)
    -- ALTCINEMAMGR.scr:274
    ctx:state().tLinger = 6 -- ALTCINEMAMGR.scr:275
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:276
end

script.labels["SetCamShort"] = function(ctx)
    -- ALTCINEMAMGR.scr:277
    ctx:state().tLinger = 3 -- ALTCINEMAMGR.scr:278
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:279
end

script.labels["SetCamInstant"] = function(ctx)
    -- ALTCINEMAMGR.scr:280
    ctx:set("tLinger", .5) -- ALTCINEMAMGR.scr:281
    do return ctx:exit("TRUE") end -- ALTCINEMAMGR.scr:282
end

return script
