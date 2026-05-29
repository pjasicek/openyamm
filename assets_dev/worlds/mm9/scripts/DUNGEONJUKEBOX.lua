-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DUNGEONJUKEBOX.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 17, path = "BaseGlobals.inc" }

-- DungeonJukebox.scr
-- by SJR
-- 10-15-01
-- Purpose:play spooky sound
-- effects behind
-- the player
-- Triggers:
-- "Play"	= play random sound effect behind player
-- "Off"	= turn all sfx off
-- "On"	= turn back on (default)
-- "RandomOff"	= turn off randomly timed sounds
-- "RandomOn"	= allow randomly timed sounds (default)
script.labels["Main"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:43
    ctx:wait(0, 5, "InitDungeonJukebox") -- DUNGEONJUKEBOX.scr:45
    mm9.gosub(script, ctx, "InitStrings") -- DUNGEONJUKEBOX.scr:47
    mm9.gosub(script, ctx, "CacheAllSounds") -- DUNGEONJUKEBOX.scr:48
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:50
end

script.labels["InitDungeonJukebox"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:53
    ctx:state().bActive = true -- DUNGEONJUKEBOX.scr:55
    ctx:state().bRandom = true -- DUNGEONJUKEBOX.scr:56
    ctx:addTrigger("Play", "PlaySound") -- DUNGEONJUKEBOX.scr:61
    ctx:addTrigger("RandomOff", "TurnRandomOff") -- DUNGEONJUKEBOX.scr:62
    ctx:addTrigger("RandomOn", "TurnRandomOn") -- DUNGEONJUKEBOX.scr:63
    ctx:addTrigger("On", "TurnOn") -- DUNGEONJUKEBOX.scr:64
    ctx:addTrigger("Off", "TurnOff") -- DUNGEONJUKEBOX.scr:65
    mm9.gosub(script, ctx, "StartPlayLoop") -- DUNGEONJUKEBOX.scr:67
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:69
end

script.labels["StartPlayLoop"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:72
    ctx:randomInt(2, 8, "dt") -- DUNGEONJUKEBOX.scr:74
    ctx:set("dt", "dt * 60") -- DUNGEONJUKEBOX.scr:75
    ctx:wait(0, "dt", "PlayLoop") -- DUNGEONJUKEBOX.scr:76
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:77
end

script.labels["PlayLoop"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:80
    if ctx:condition("bRandom==FALSE") then -- DUNGEONJUKEBOX.scr:82
        do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:83
    end -- DUNGEONJUKEBOX.scr:84
    mm9.gosub(script, ctx, "PlaySound") -- DUNGEONJUKEBOX.scr:85
    mm9.gosub(script, ctx, "StartPlayLoop") -- DUNGEONJUKEBOX.scr:86
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:87
end

script.labels["PlaySound"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:90
    if ctx:condition("bActive==FALSE") then -- DUNGEONJUKEBOX.scr:92
        do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:93
    end -- DUNGEONJUKEBOX.scr:94
    mm9.gosub(script, ctx, "UpdatePOS") -- DUNGEONJUKEBOX.scr:95
    ctx:randomInt(0, "nCounter", "nRandom") -- DUNGEONJUKEBOX.scr:96
    ctx:arrayGet("spSoundArray", "nRandom", "sFilename") -- DUNGEONJUKEBOX.scr:97
    ctx:playSound("sFileName", "DoNothing", 1, 500, "FALSE", 100) -- DUNGEONJUKEBOX.scr:98
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:99
end

script.labels["UpdatePOS"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:102
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:player():rotation() -- DUNGEONJUKEBOX.scr:104
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- DUNGEONJUKEBOX.scr:105
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:player():pos() -- DUNGEONJUKEBOX.scr:106
    ctx:set("x", "x - dx") -- DUNGEONJUKEBOX.scr:107
    ctx:set("y", "y - dy") -- DUNGEONJUKEBOX.scr:108
    ctx:set("z", "z - dz") -- DUNGEONJUKEBOX.scr:109
    ctx:self():setPos("x", "y", "z") -- DUNGEONJUKEBOX.scr:110
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:111
end

script.labels["TurnOn"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:114
    ctx:state().bActive = true -- DUNGEONJUKEBOX.scr:116
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:117
end

script.labels["TurnOff"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:120
    ctx:state().bActive = false -- DUNGEONJUKEBOX.scr:122
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:123
end

script.labels["TurnRandomOn"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:126
    ctx:state().bRandom = true -- DUNGEONJUKEBOX.scr:128
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:129
end

script.labels["TurnRandomOff"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:132
    ctx:state().bRandom = false -- DUNGEONJUKEBOX.scr:134
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:135
end

script.labels["InitStrings"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:138
    ctx:arrayPut("spSoundArray", 0, "sounds\\Door\\Doorcreak02.wav") -- DUNGEONJUKEBOX.scr:140
    ctx:arrayPut("spSoundArray", 1, "sounds\\Ambient\\Owl02.wav") -- DUNGEONJUKEBOX.scr:141
    ctx:arrayPut("spSoundArray", 2, "sounds\\Ambient\\Thunderdistant02.wav") -- DUNGEONJUKEBOX.scr:142
    ctx:arrayPut("spSoundArray", 3, "sounds\\Events\\rockscrumblingloop.wav") -- DUNGEONJUKEBOX.scr:143
    ctx:arrayPut("spSoundArray", 4, "sounds\\Events\\WoodCreak1.wav") -- DUNGEONJUKEBOX.scr:144
    ctx:arrayPut("spSoundArray", 5, "sounds\\AnimSounds\\lichkingTaunt.wav") -- DUNGEONJUKEBOX.scr:145
    ctx:arrayPut("spSoundArray", 6, "sounds\\Ambient\\cricket.wav") -- DUNGEONJUKEBOX.scr:146
    ctx:arrayPut("spSoundArray", 7, "sounds\\AnimSounds\\gopherwince.wav") -- DUNGEONJUKEBOX.scr:147
    ctx:arrayPut("spSoundArray", 8, "sounds\\PickupItems\\Shield\\Metal01.wav") -- DUNGEONJUKEBOX.scr:148
    ctx:arrayPut("spSoundArray", 9, "sounds\\Events\\WoodCreak1.wav") -- DUNGEONJUKEBOX.scr:149
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:150
end

script.labels["CacheAllSounds"] = function(ctx)
    -- DUNGEONJUKEBOX.scr:153
    ctx:state().nCounter = 0 -- DUNGEONJUKEBOX.scr:155
    while ctx:condition("nCounter<NUMSOUNDS") do -- DUNGEONJUKEBOX.scr:156
        ctx:arrayGet("spSoundArray", "nCounter", "sFileName") -- DUNGEONJUKEBOX.scr:157
        ctx:cacheSound("sFileName") -- DUNGEONJUKEBOX.scr:158
        ctx:set("nCounter", "nCounter + 1") -- DUNGEONJUKEBOX.scr:159
    end -- DUNGEONJUKEBOX.scr:160
    ctx:set("nCounter", "nCounter - 1") -- DUNGEONJUKEBOX.scr:161
    do return ctx:exit("TRUE") end -- DUNGEONJUKEBOX.scr:162
end

return script
