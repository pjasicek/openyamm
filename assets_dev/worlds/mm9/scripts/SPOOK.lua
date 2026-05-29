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
    ctx:wait(0, .1, "InitSpook") -- SPOOK.scr:47
    mm9.gosub(script, ctx, "InitStrings") -- SPOOK.scr:49
    mm9.gosub(script, ctx, "CacheAllSounds") -- SPOOK.scr:50
    do return ctx:exit("TRUE") end -- SPOOK.scr:52
end

script.labels["InitSpook"] = function(ctx)
    -- SPOOK.scr:55
    ctx:state().bActive = true -- SPOOK.scr:57
    ctx:state().bRandom = true -- SPOOK.scr:58
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
    ctx:randomInt(2, 8, "dt") -- SPOOK.scr:84
    ctx:set("dt", "dt * 60") -- SPOOK.scr:85
    ctx:wait(0, "dt", "StartPlayLoop") -- SPOOK.scr:86
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
    ctx:randomInt(0, 9, "nRandom") -- SPOOK.scr:100
    ctx:arrayGet("spSoundArray", "nRandom", "sFilename") -- SPOOK.scr:101
    ctx:playSound("sFileName", "OnSoundDone", "hDummy", 500, "FALSE", 100) -- SPOOK.scr:102
    do return ctx:exit("TRUE") end -- SPOOK.scr:103
end

script.labels["PlaySound"] = function(ctx)
    -- SPOOK.scr:106
    if ctx:condition("bActive==FALSE") then -- SPOOK.scr:108
        do return ctx:exit("TRUE") end -- SPOOK.scr:109
    end -- SPOOK.scr:110
    mm9.gosub(script, ctx, "UpdatePOS") -- SPOOK.scr:111
    ctx:randomInt(0, 9, "nRandom") -- SPOOK.scr:112
    ctx:arrayGet("spSoundArray", "nRandom", "sFilename") -- SPOOK.scr:113
    ctx:playSound("sFileName", "OnSoundDone", "hDummy", 500, "FALSE", 100) -- SPOOK.scr:114
    do return ctx:exit("TRUE") end -- SPOOK.scr:115
end

script.labels["UpdatePOS"] = function(ctx)
    -- SPOOK.scr:118
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:player():rotation() -- SPOOK.scr:120
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- SPOOK.scr:121
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:player():pos() -- SPOOK.scr:122
    ctx:set("x", "x - dx") -- SPOOK.scr:123
    ctx:set("y", "y - dy") -- SPOOK.scr:124
    ctx:set("z", "z - dz") -- SPOOK.scr:125
    ctx:self():setPos("x", "y", "z") -- SPOOK.scr:126
    do return ctx:exit("TRUE") end -- SPOOK.scr:127
end

script.labels["TurnOn"] = function(ctx)
    -- SPOOK.scr:130
    ctx:state().bActive = true -- SPOOK.scr:132
    do return ctx:exit("TRUE") end -- SPOOK.scr:133
end

script.labels["TurnOff"] = function(ctx)
    -- SPOOK.scr:136
    ctx:state().bActive = false -- SPOOK.scr:138
    do return ctx:exit("TRUE") end -- SPOOK.scr:139
end

script.labels["TurnRandomOn"] = function(ctx)
    -- SPOOK.scr:142
    ctx:state().bRandom = true -- SPOOK.scr:144
    do return ctx:exit("TRUE") end -- SPOOK.scr:145
end

script.labels["TurnRandomOff"] = function(ctx)
    -- SPOOK.scr:148
    ctx:state().bRandom = false -- SPOOK.scr:150
    do return ctx:exit("TRUE") end -- SPOOK.scr:151
end

script.labels["OnSoundDone"] = function(ctx)
    -- SPOOK.scr:154
    ctx:killSound("hDummy") -- SPOOK.scr:156
    do return ctx:exit("TRUE") end -- SPOOK.scr:157
end

script.labels["InitStrings"] = function(ctx)
    -- SPOOK.scr:160
    ctx:state().sFileName = "sounds\\Door\\Doorcreak02.wav" -- SPOOK.scr:162
    ctx:arrayPut("spSoundArray", 0, "sFileName") -- SPOOK.scr:163
    ctx:state().sFileName = "sounds\\Ambient\\Owl02.wav" -- SPOOK.scr:164
    ctx:arrayPut("spSoundArray", 1, "sFileName") -- SPOOK.scr:165
    ctx:state().sFileName = "sounds\\Ambient\\Thunderdistant02.wav" -- SPOOK.scr:166
    ctx:arrayPut("spSoundArray", 2, "sFileName") -- SPOOK.scr:167
    ctx:state().sFileName = "sounds\\Events\\rockscrumblingloop.wav" -- SPOOK.scr:168
    ctx:arrayPut("spSoundArray", 3, "sFileName") -- SPOOK.scr:169
    ctx:state().sFileName = "sounds\\Events\\WoodCreak1.wav" -- SPOOK.scr:170
    ctx:arrayPut("spSoundArray", 4, "sFileName") -- SPOOK.scr:171
    ctx:state().sFileName = "sounds\\AnimSounds\\lichkingTaunt.wav" -- SPOOK.scr:172
    ctx:arrayPut("spSoundArray", 5, "sFileName") -- SPOOK.scr:173
    ctx:state().sFileName = "sounds\\Ambient\\cricket.wav" -- SPOOK.scr:174
    ctx:arrayPut("spSoundArray", 6, "sFileName") -- SPOOK.scr:175
    ctx:state().sFileName = "sounds\\AnimSounds\\gopherwince.wav" -- SPOOK.scr:176
    ctx:arrayPut("spSoundArray", 7, "sFileName") -- SPOOK.scr:177
    ctx:state().sFileName = "sounds\\PickupItems\\Shield\\Metal01.wav" -- SPOOK.scr:178
    ctx:arrayPut("spSoundArray", 8, "sFileName") -- SPOOK.scr:179
    ctx:state().sFileName = "sounds\\events\\shatterpotterybig02.wav" -- SPOOK.scr:180
    ctx:arrayPut("spSoundArray", 9, "sFileName") -- SPOOK.scr:181
    ctx:state().sFileName = "" -- SPOOK.scr:182
    do return ctx:exit("TRUE") end -- SPOOK.scr:183
end

script.labels["CacheAllSounds"] = function(ctx)
    -- SPOOK.scr:186
    ctx:cacheSound("sounds\\Door\\Doorcreak02.wav") -- SPOOK.scr:188
    ctx:cacheSound("sounds\\Ambient\\Owl02.wav") -- SPOOK.scr:189
    ctx:cacheSound("sounds\\Ambient\\Thunderdistant02.wav") -- SPOOK.scr:190
    ctx:cacheSound("sounds\\Events\\rockscrumblingloop.wav") -- SPOOK.scr:191
    ctx:cacheSound("sounds\\Events\\WoodCreak1.wav") -- SPOOK.scr:192
    ctx:cacheSound("sounds\\AnimSounds\\lichkingTaunt.wav") -- SPOOK.scr:193
    ctx:cacheSound("sounds\\Ambient\\cricket.wav") -- SPOOK.scr:194
    ctx:cacheSound("sounds\\AnimSounds\\gopherwince.wav") -- SPOOK.scr:195
    ctx:cacheSound("sounds\\PickupItems\\Shield\\Metal01.wav") -- SPOOK.scr:196
    ctx:cacheSound("sounds\\events\\shatterpotterybig02.wav") -- SPOOK.scr:197
    do return ctx:exit("TRUE") end -- SPOOK.scr:199
end

return script
