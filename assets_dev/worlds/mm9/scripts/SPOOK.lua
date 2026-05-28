-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 21, path = "BaseGlobals.inc" }

-- Spook.scr
-- by SJR
-- 10-15-01
-- Purpose:play spooky sound
-- effects behind
-- the player
-- Triggers:
-- "Play"	= play random sound effect behind player
-- "PlayHere"	= play random sound effect from trigger location
-- "Off"	= turn all sfx off
-- "On"	= turn back on (default)
-- "RandomOff"	= turn off randomly timed sounds
-- "RandomOn"	= allow randomly timed sounds (default)
-- note:	for "PlayHere" achieve the desired effect, you will need
-- to route the stepped-on trigger through another, distant trigger.
script.labels["Main"] = function(ctx)
    -- SPOOK.scr:45
    ctx:command("wait", "0, .1, InitSpook") -- SPOOK.scr:47
    mm9.gosub(script, ctx, "InitStrings") -- SPOOK.scr:49
    mm9.gosub(script, ctx, "CacheAllSounds") -- SPOOK.scr:50
    do return ctx:exit("TRUE") end -- SPOOK.scr:52
end

script.labels["InitSpook"] = function(ctx)
    -- SPOOK.scr:55
    ctx:command("bactive", "= TRUE") -- SPOOK.scr:57
    ctx:command("brandom", "= TRUE") -- SPOOK.scr:58
    ctx:command("getmyhandle", "hMe") -- SPOOK.scr:60
    ctx:command("getplayerhandle", "hPlayer") -- SPOOK.scr:61
    ctx:addTrigger("Play", "PlaySound") -- SPOOK.scr:63
    ctx:addTrigger("PlayHere", "PlaySoundHere") -- SPOOK.scr:64
    ctx:addTrigger("RandomOff", "TurnRandomOff") -- SPOOK.scr:65
    ctx:addTrigger("RandomOn", "TurnRandomOn") -- SPOOK.scr:66
    ctx:addTrigger("On", "TurnOn") -- SPOOK.scr:67
    ctx:addTrigger("Off", "TurnOff") -- SPOOK.scr:68
    mm9.gosub(script, ctx, "StartPlayLoop") -- SPOOK.scr:70
    do return ctx:exit("TRUE") end -- SPOOK.scr:72
end

script.labels["StartPlayLoop"] = function(ctx)
    -- SPOOK.scr:75
    if ctx:condition("bActive==FALSE") then -- SPOOK.scr:77
        do return ctx:exit("TRUE") end -- SPOOK.scr:78
    end -- SPOOK.scr:79
    if ctx:condition("bRandom==FALSE") then -- SPOOK.scr:80
        do return ctx:exit("TRUE") end -- SPOOK.scr:81
    end -- SPOOK.scr:82
    mm9.gosub(script, ctx, "PlaySound") -- SPOOK.scr:83
    ctx:command("getrandomint", "2, 8, dt") -- SPOOK.scr:84
    ctx:command("dt", "= dt * 60") -- SPOOK.scr:85
    ctx:command("wait", "0, dt, StartPlayLoop") -- SPOOK.scr:86
    do return ctx:exit("TRUE") end -- SPOOK.scr:87
end

script.labels["PlaySoundHere"] = function(ctx)
    -- SPOOK.scr:90
    if ctx:condition("bActive==FALSE") then -- SPOOK.scr:92
        do return ctx:exit("TRUE") end -- SPOOK.scr:93
    end -- SPOOK.scr:94
    -- UpdatePOS will use the trigger as pos
    ctx:getParam(0, "hPlayer") -- SPOOK.scr:96
    mm9.gosub(script, ctx, "UpdatePOS") -- SPOOK.scr:97
    -- reset reference to player
    ctx:command("getplayerhandle", "hPlayer") -- SPOOK.scr:99
    ctx:command("getrandomint", "0, 9, nRandom") -- SPOOK.scr:100
    ctx:command("arrayget", "spSoundArray, nRandom, sFilename") -- SPOOK.scr:101
    ctx:command("playsound", "sFileName, OnSoundDone, hDummy, 500, FALSE, 100") -- SPOOK.scr:102
    do return ctx:exit("TRUE") end -- SPOOK.scr:103
end

script.labels["PlaySound"] = function(ctx)
    -- SPOOK.scr:106
    if ctx:condition("bActive==FALSE") then -- SPOOK.scr:108
        do return ctx:exit("TRUE") end -- SPOOK.scr:109
    end -- SPOOK.scr:110
    mm9.gosub(script, ctx, "UpdatePOS") -- SPOOK.scr:111
    ctx:command("getrandomint", "0, 9, nRandom") -- SPOOK.scr:112
    ctx:command("arrayget", "spSoundArray, nRandom, sFilename") -- SPOOK.scr:113
    ctx:command("playsound", "sFileName, OnSoundDone, hDummy, 500, FALSE, 100") -- SPOOK.scr:114
    do return ctx:exit("TRUE") end -- SPOOK.scr:115
end

script.labels["UpdatePOS"] = function(ctx)
    -- SPOOK.scr:118
    ctx:command("getfacedir", "hPlayer, dx,dy,dz") -- SPOOK.scr:120
    ctx:command("normalizevector", "dx,dy,dz") -- SPOOK.scr:121
    ctx:command("getpos", "hPlayer, x,y,z") -- SPOOK.scr:122
    ctx:command("x", "= x - dx") -- SPOOK.scr:123
    ctx:command("y", "= y - dy") -- SPOOK.scr:124
    ctx:command("z", "= z - dz") -- SPOOK.scr:125
    ctx:command("setpos", "hMe, x,y,z") -- SPOOK.scr:126
    do return ctx:exit("TRUE") end -- SPOOK.scr:127
end

script.labels["TurnOn"] = function(ctx)
    -- SPOOK.scr:130
    ctx:command("bactive", "= TRUE") -- SPOOK.scr:132
    do return ctx:exit("TRUE") end -- SPOOK.scr:133
end

script.labels["TurnOff"] = function(ctx)
    -- SPOOK.scr:136
    ctx:command("bactive", "= FALSE") -- SPOOK.scr:138
    do return ctx:exit("TRUE") end -- SPOOK.scr:139
end

script.labels["TurnRandomOn"] = function(ctx)
    -- SPOOK.scr:142
    ctx:command("brandom", "= TRUE") -- SPOOK.scr:144
    do return ctx:exit("TRUE") end -- SPOOK.scr:145
end

script.labels["TurnRandomOff"] = function(ctx)
    -- SPOOK.scr:148
    ctx:command("brandom", "= FALSE") -- SPOOK.scr:150
    do return ctx:exit("TRUE") end -- SPOOK.scr:151
end

script.labels["OnSoundDone"] = function(ctx)
    -- SPOOK.scr:154
    ctx:command("killsound", "hDummy") -- SPOOK.scr:156
    do return ctx:exit("TRUE") end -- SPOOK.scr:157
end

script.labels["InitStrings"] = function(ctx)
    -- SPOOK.scr:160
    ctx:command("sfilename", "= \"sounds\\Door\\Doorcreak02.wav\"") -- SPOOK.scr:162
    ctx:command("arrayput", "spSoundArray, 0, sFileName") -- SPOOK.scr:163
    ctx:command("sfilename", "= \"sounds\\Ambient\\Owl02.wav\"") -- SPOOK.scr:164
    ctx:command("arrayput", "spSoundArray, 1, sFileName") -- SPOOK.scr:165
    ctx:command("sfilename", "= \"sounds\\Ambient\\Thunderdistant02.wav\"") -- SPOOK.scr:166
    ctx:command("arrayput", "spSoundArray, 2, sFileName") -- SPOOK.scr:167
    ctx:command("sfilename", "= \"sounds\\Events\\rockscrumblingloop.wav\"") -- SPOOK.scr:168
    ctx:command("arrayput", "spSoundArray, 3, sFileName") -- SPOOK.scr:169
    ctx:command("sfilename", "= \"sounds\\Events\\WoodCreak1.wav\"") -- SPOOK.scr:170
    ctx:command("arrayput", "spSoundArray, 4, sFileName") -- SPOOK.scr:171
    ctx:command("sfilename", "= \"sounds\\AnimSounds\\lichkingTaunt.wav\"") -- SPOOK.scr:172
    ctx:command("arrayput", "spSoundArray, 5, sFileName") -- SPOOK.scr:173
    ctx:command("sfilename", "= \"sounds\\Ambient\\cricket.wav\"") -- SPOOK.scr:174
    ctx:command("arrayput", "spSoundArray, 6, sFileName") -- SPOOK.scr:175
    ctx:command("sfilename", "= \"sounds\\AnimSounds\\gopherwince.wav\"") -- SPOOK.scr:176
    ctx:command("arrayput", "spSoundArray, 7, sFileName") -- SPOOK.scr:177
    ctx:command("sfilename", "= \"sounds\\PickupItems\\Shield\\Metal01.wav\"") -- SPOOK.scr:178
    ctx:command("arrayput", "spSoundArray, 8, sFileName") -- SPOOK.scr:179
    ctx:command("sfilename", "= \"sounds\\events\\shatterpotterybig02.wav\"") -- SPOOK.scr:180
    ctx:command("arrayput", "spSoundArray, 9, sFileName") -- SPOOK.scr:181
    ctx:command("sfilename", "= \"\"") -- SPOOK.scr:182
    do return ctx:exit("TRUE") end -- SPOOK.scr:183
end

script.labels["CacheAllSounds"] = function(ctx)
    -- SPOOK.scr:186
    ctx:command("cachesound", "\"sounds\\Door\\Doorcreak02.wav\"") -- SPOOK.scr:188
    ctx:command("cachesound", "\"sounds\\Ambient\\Owl02.wav\"") -- SPOOK.scr:189
    ctx:command("cachesound", "\"sounds\\Ambient\\Thunderdistant02.wav\"") -- SPOOK.scr:190
    ctx:command("cachesound", "\"sounds\\Events\\rockscrumblingloop.wav\"") -- SPOOK.scr:191
    ctx:command("cachesound", "\"sounds\\Events\\WoodCreak1.wav\"") -- SPOOK.scr:192
    ctx:command("cachesound", "\"sounds\\AnimSounds\\lichkingTaunt.wav\"") -- SPOOK.scr:193
    ctx:command("cachesound", "\"sounds\\Ambient\\cricket.wav\"") -- SPOOK.scr:194
    ctx:command("cachesound", "\"sounds\\AnimSounds\\gopherwince.wav\"") -- SPOOK.scr:195
    ctx:command("cachesound", "\"sounds\\PickupItems\\Shield\\Metal01.wav\"") -- SPOOK.scr:196
    ctx:command("cachesound", "\"sounds\\events\\shatterpotterybig02.wav\"") -- SPOOK.scr:197
    do return ctx:exit("TRUE") end -- SPOOK.scr:199
end

return script
