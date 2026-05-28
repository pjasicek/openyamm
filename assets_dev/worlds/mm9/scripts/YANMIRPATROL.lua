-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIRPATROL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 22, path = "BaseMelee.inc" }
script.includes[#script.includes + 1] = { line = 23, path = "BaseDoor.inc" }

-- YanmirPatrol.scr
-- kd 10-26-01
-- Parameters
-- Specialized patrol script for Yanmir the giant.
-- When triggered, Yanmir runs to a SquishVictim and kills it.
-- Then he begins his routine patrol of the Fort.  He kicks
-- any closed doors. (Added Sfx with FrostDust and DoorQuakes)
-- Cool Factor = HIGH!!
-- 0 - Marker Root name  (ie for Markers Mrk0, Mrk1, Mrk2  "Mrk" is the root name)
-- 1 - Number of Markers
-- 2 - Second Root name for marker path. (Optional)
-- 3 - Number of Markers. (Optional)
-- 4 - FireObject Root Name (FrostDust in this instance)
-- 5 - EarthQuakeObject Root Name (DoorQuake in this instance)
script.labels["OnDeath"] = function(ctx)
    -- YANMIRPATROL.scr:50
    -- just in case some freak figures out a way to kill me
    -- give the completed quest key <--------TL
    ctx:giveKey(69) -- YANMIRPATROL.scr:56
    mm9.gosub(script, ctx, "OnDeath") -- YANMIRPATROL.scr:57
    do return ctx:exit("") end -- YANMIRPATROL.scr:58
end

script.labels["dn"] = function(ctx)
    -- YANMIRPATROL.scr:61
    do return ctx:exit(1) end -- YANMIRPATROL.scr:63
end

script.labels["Defeated"] = function(ctx)
    -- YANMIRPATROL.scr:65
    -- Die
    do return ctx:exit("TRUE") end -- YANMIRPATROL.scr:68
end

script.labels["AlertCall"] = function(ctx)
    -- YANMIRPATROL.scr:70
    -- PlaySound sounds\VO\Charrrge.wav, dn, hDummy, 5000, FALSE, 100
    mm9.gosub(script, ctx, "BaseInit") -- YANMIRPATROL.scr:73
    do return ctx:exit(1) end -- YANMIRPATROL.scr:74
end

script.labels["KeepMoving"] = function(ctx)
    -- YANMIRPATROL.scr:76
    -- (Optional)
    -- Stop at the start and wait for @M (Mundane time event)
    ctx:command("counter", "= counter + 1") -- YANMIRPATROL.scr:80
    ctx:command("mod", "counter, 16") -- YANMIRPATROL.scr:81
    if ctx:condition("counter == 0") then -- YANMIRPATROL.scr:82
        ctx:command("nmarker", "= 0") -- YANMIRPATROL.scr:83
        ctx:command("smarker", "= sPatrolPathA + nMarker") -- YANMIRPATROL.scr:84
        ctx:command("stop", "") -- YANMIRPATROL.scr:85
        do return ctx:exit(1) end -- YANMIRPATROL.scr:86
    else -- YANMIRPATROL.scr:87
        mm9.gosub(script, ctx, "GoToMarker") -- YANMIRPATROL.scr:88
    end -- YANMIRPATROL.scr:89
    do return ctx:exit(1) end -- YANMIRPATROL.scr:90
end

script.labels["GoToMarker"] = function(ctx)
    -- YANMIRPATROL.scr:92
    -- Main Patrol routine (Recursive with string cancatenation)
    -- Barrowed from Brett Yagi's patrol routine.
    if ctx:condition("nMarker < nMarkersA") then -- YANMIRPATROL.scr:96
        ctx:command("nmarker", "= nMarker + 1") -- YANMIRPATROL.scr:97
        ctx:command("smarker", "= sPatrolPathA + nMarker") -- YANMIRPATROL.scr:98
        ctx:command("getobjecthandle", "sMarker hMarker") -- YANMIRPATROL.scr:99
        ctx:command("walkto", "hMarker, 1, GoToMarker") -- YANMIRPATROL.scr:100
    else -- YANMIRPATROL.scr:101
        mm9.gosub(script, ctx, "WalkToLastMarker") -- YANMIRPATROL.scr:102
    end -- YANMIRPATROL.scr:103
    do return ctx:exit(1) end -- YANMIRPATROL.scr:104
end

script.labels["WalkToLastMarker"] = function(ctx)
    -- YANMIRPATROL.scr:106
    ctx:command("nmarker", "= 0") -- YANMIRPATROL.scr:108
    ctx:command("ndusting", "= 0") -- YANMIRPATROL.scr:109
    ctx:command("getobjecthandle", "YanmirSquishMarker0, hMarker") -- YANMIRPATROL.scr:110
    ctx:command("walkto", "hMarker, 0, Marker0") -- YANMIRPATROL.scr:111
    do return ctx:exit(1) end -- YANMIRPATROL.scr:112
end

script.labels["UnStuckMe"] = function(ctx)
    -- YANMIRPATROL.scr:114
    -- Barrowed from Brett Yagi's patrol routine.
    if ctx:condition("nForward == 0") then -- YANMIRPATROL.scr:117
        ctx:command("nmarker", "= nMarker - 1") -- YANMIRPATROL.scr:118
    end -- YANMIRPATROL.scr:119
    mm9.gosub(script, ctx, "GoToMarker") -- YANMIRPATROL.scr:120
    do return ctx:exit(1) end -- YANMIRPATROL.scr:121
end

script.labels["KickTheDoor"] = function(ctx)
    -- YANMIRPATROL.scr:125
    -- [Specialized grouped subroutines.]
    -- Yanmir encounters a Door Object, kicks it, opens it
    -- and we get to see stirred up FrostDust, shaking walls
    -- and door slammin' Sfx.
    ctx:getParam(0, "hDoor") -- YANMIRPATROL.scr:131
    ctx:command("playsound", "sounds\\AnimSounds\\YanmirAware.wav, dn, 1000, 2000, FALSE, 100") -- YANMIRPATROL.scr:132
    ctx:command("playanim", "Hattack2, dn") -- YANMIRPATROL.scr:133
    ctx:command("wait", "1, .8, Kicking") -- YANMIRPATROL.scr:134
    do return ctx:exit(1) end -- YANMIRPATROL.scr:135
end

script.labels["Kicking"] = function(ctx)
    -- YANMIRPATROL.scr:136
    ctx:command("sdusting", "= sDustString + nDusting") -- YANMIRPATROL.scr:137
    ctx:command("squaking", "= sDoorString + nDusting") -- YANMIRPATROL.scr:138
    ctx:command("getobjecthandle", "sDusting, hDustObject") -- YANMIRPATROL.scr:139
    ctx:command("getobjecthandle", "sQuaking, hDoorQuake") -- YANMIRPATROL.scr:140
    ctx:command("ndusting", "= nDusting + 1") -- YANMIRPATROL.scr:141
    ctx:command("playsound", "Sounds\\Door\\stonedoorslam.wav, dn, 1000, 3500, FALSE, 100") -- YANMIRPATROL.scr:142
    ctx:trigger("hDustObject", "On") -- YANMIRPATROL.scr:143
    ctx:command("nmarker", "= nMarker - 1") -- YANMIRPATROL.scr:144
    ctx:trigger("hDoor", "use") -- YANMIRPATROL.scr:145
    ctx:command("wait", "0, .25, DustMe") -- YANMIRPATROL.scr:146
    do return ctx:exit(1) end -- YANMIRPATROL.scr:147
end

script.labels["DustMe"] = function(ctx)
    -- YANMIRPATROL.scr:148
    ctx:trigger("hDustObject", "Off") -- YANMIRPATROL.scr:149
    ctx:trigger("hDoorQuake", "Trigger") -- YANMIRPATROL.scr:150
    ctx:command("playsound", "Sounds\\Door\\doorslammetal01.wav, dn, 1000, 3500, FALSE, 100") -- YANMIRPATROL.scr:151
    ctx:command("wait", "0, 1, GoToMarker") -- YANMIRPATROL.scr:152
    do return ctx:exit(1) end -- YANMIRPATROL.scr:153
end

script.labels["PlayScene"] = function(ctx)
    -- YANMIRPATROL.scr:158
    -- [Specialized grouped subroutines.]
    -- Triggered to play out the SquishVictim and PlayAnims
    -- associated with SquishVictim stuck to Yanmir's Boot.
    ctx:command("runto", "hMarker, 0, StepOn") -- YANMIRPATROL.scr:163
    do return ctx:exit(1) end -- YANMIRPATROL.scr:164
end

script.labels["StepOn"] = function(ctx)
    -- YANMIRPATROL.scr:165
    ctx:command("playsound", "sounds\\Squish.wav, dn, 100, 2000, FALSE, 100") -- YANMIRPATROL.scr:166
    ctx:command("playanim", "StepOn, Wipe") -- YANMIRPATROL.scr:167
    ctx:command("damage", "hSquishVictim, 3000, 4, FALSE") -- YANMIRPATROL.scr:168
    do return ctx:exit(1) end -- YANMIRPATROL.scr:169
end

script.labels["Wipe"] = function(ctx)
    -- YANMIRPATROL.scr:170
    ctx:command("playsound", "sounds\\Squish2.wav, dn, 100, 2000, FALSE, 100") -- YANMIRPATROL.scr:171
    -- PlaySound sounds\AnimSounds\YanmirWipe.wav, dn, 100, 1000, FALSE, 100
    ctx:command("playanim", "Wipe, Wince1") -- YANMIRPATROL.scr:173
    do return ctx:exit(1) end -- YANMIRPATROL.scr:174
end

script.labels["Wince1"] = function(ctx)
    -- YANMIRPATROL.scr:175
    ctx:command("playsound", "sounds\\AnimSounds\\YanmirWipe.wav, dn, 100, 1000, FALSE, 100") -- YANMIRPATROL.scr:176
    ctx:command("playanim", "Wince1, dn") -- YANMIRPATROL.scr:177
    ctx:command("wait", "0, 0.5, Marker0") -- YANMIRPATROL.scr:178
    do return ctx:exit(1) end -- YANMIRPATROL.scr:179
end

script.labels["Marker0"] = function(ctx)
    -- YANMIRPATROL.scr:180
    ctx:command("getobjecthandle", "YanmirPathA0, hMarker") -- YANMIRPATROL.scr:181
    ctx:command("walkto", "hMarker, 0, FirstMarker") -- YANMIRPATROL.scr:182
    do return ctx:exit(1) end -- YANMIRPATROL.scr:183
end

script.labels["FirstMarker"] = function(ctx)
    -- YANMIRPATROL.scr:184
    ctx:command("playsound", "sounds\\AnimSounds\\YanmirWipe.wav, dn, 100, 1000, FALSE, 100") -- YANMIRPATROL.scr:185
    ctx:command("playanim", "Wince1, GoToMarker") -- YANMIRPATROL.scr:186
    do return ctx:exit(1) end -- YANMIRPATROL.scr:187
end

script.labels["Main2"] = function(ctx)
    -- YANMIRPATROL.scr:192
    ctx:addTrigger("Kick", "KickTheDoor") -- YANMIRPATROL.scr:194
    ctx:addTrigger("Squish", "PlayScene") -- YANMIRPATROL.scr:195
    ctx:addTrigger("Destroy", "Defeated") -- YANMIRPATROL.scr:196
    ctx:command("getobjecthandle", "YanmirSquishMarker0, hMarker") -- YANMIRPATROL.scr:197
    ctx:command("getobjecthandle", "SquishVictim0, hSquishVictim") -- YANMIRPATROL.scr:198
    ctx:command("nmarkersa", "= nMarkersA - 1") -- YANMIRPATROL.scr:199
    do return ctx:exit(1) end -- YANMIRPATROL.scr:200
end

script.labels["Main"] = function(ctx)
    -- YANMIRPATROL.scr:202
    ctx:getParam(0, "sPatrolPathA") -- YANMIRPATROL.scr:204
    ctx:getParam(1, "nMarkersA") -- YANMIRPATROL.scr:205
    ctx:getParam(2, "sPatrolPathB") -- YANMIRPATROL.scr:206
    ctx:getParam(3, "nMarkersB") -- YANMIRPATROL.scr:207
    ctx:getParam(4, "sDustString") -- YANMIRPATROL.scr:208
    ctx:getParam(5, "sDoorString") -- YANMIRPATROL.scr:209
    ctx:command("onstuck", "UnStuckMe") -- YANMIRPATROL.scr:210
    ctx:command("ondoor", "KickTheDoor") -- YANMIRPATROL.scr:211
    ctx:command("onfoundtarget", "AlertCall") -- YANMIRPATROL.scr:212
    ctx:command("wait", "0 .1 main2") -- YANMIRPATROL.scr:213
    do return ctx:exit(1) end -- YANMIRPATROL.scr:214
end

return script
