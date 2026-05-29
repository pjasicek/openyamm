-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PLATEAUJUKEBOX.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "BaseGlobals.inc" }

-- PlateauJukebox.scr
-- by SJR
-- 12-11-01
-- Purpose:play soft, windy sound
-- effects near the player
-- Triggers:
-- "Play"	= play random sound effect behind player
-- "Off"	= turn all sfx off
-- "On"	= turn back on (default)
-- "RandomOff"	= turn off randomly timed sounds
-- "RandomOn"	= allow randomly timed sounds (default)
script.labels["Main"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:37
    ctx:wait(0, 5, "InitDungeonJukebox") -- PLATEAUJUKEBOX.scr:39
    mm9.gosub(script, ctx, "InitStrings") -- PLATEAUJUKEBOX.scr:41
    mm9.gosub(script, ctx, "CacheAllSounds") -- PLATEAUJUKEBOX.scr:42
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:44
end

script.labels["InitDungeonJukebox"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:47
    ctx:addTrigger("On", "TurnOn") -- PLATEAUJUKEBOX.scr:52
    ctx:addTrigger("Off", "TurnOff") -- PLATEAUJUKEBOX.scr:53
    mm9.gosub(script, ctx, "StartPlayLoop") -- PLATEAUJUKEBOX.scr:55
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:57
end

script.labels["StartPlayLoop"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:60
    ctx:randomInt(2, 8, "dt") -- PLATEAUJUKEBOX.scr:62
    ctx:set("dt", "dt * 60") -- PLATEAUJUKEBOX.scr:63
    ctx:wait(0, "dt", "PlaySound") -- PLATEAUJUKEBOX.scr:64
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:66
end

script.labels["PlaySound"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:69
    if ctx:condition("bActive==FALSE") then -- PLATEAUJUKEBOX.scr:71
        do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:72
    end -- PLATEAUJUKEBOX.scr:73
    mm9.gosub(script, ctx, "UpdatePOS") -- PLATEAUJUKEBOX.scr:74
    ctx:randomInt(0, "nCounter", "nRandom") -- PLATEAUJUKEBOX.scr:75
    ctx:arrayGet("spSoundArray", "nRandom", "sFilename") -- PLATEAUJUKEBOX.scr:76
    ctx:playSound("sFileName", "StartPlayLoop", 1, 500, "FALSE", 100) -- PLATEAUJUKEBOX.scr:77
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:79
end

script.labels["UpdatePOS"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:82
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:player():pos() -- PLATEAUJUKEBOX.scr:84
    ctx:self():setPos("x", "y", "z") -- PLATEAUJUKEBOX.scr:85
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:86
end

script.labels["TurnOn"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:89
    ctx:state().bActive = true -- PLATEAUJUKEBOX.scr:91
    mm9.gosub(script, ctx, "StartPlayLoop") -- PLATEAUJUKEBOX.scr:92
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:93
end

script.labels["TurnOff"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:96
    ctx:state().bActive = false -- PLATEAUJUKEBOX.scr:98
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:99
end

script.labels["InitStrings"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:102
    ctx:arrayPut("spSoundArray", 0, "sounds\\") -- PLATEAUJUKEBOX.scr:104
    ctx:arrayPut("spSoundArray", 1, "sounds\\") -- PLATEAUJUKEBOX.scr:105
    ctx:arrayPut("spSoundArray", 2, "sounds\\") -- PLATEAUJUKEBOX.scr:106
    ctx:arrayPut("spSoundArray", 3, "sounds\\") -- PLATEAUJUKEBOX.scr:107
    ctx:arrayPut("spSoundArray", 4, "sounds\\") -- PLATEAUJUKEBOX.scr:108
    ctx:arrayPut("spSoundArray", 5, "sounds\\") -- PLATEAUJUKEBOX.scr:109
    ctx:arrayPut("spSoundArray", 6, "sounds\\") -- PLATEAUJUKEBOX.scr:110
    ctx:arrayPut("spSoundArray", 7, "sounds\\") -- PLATEAUJUKEBOX.scr:111
    ctx:arrayPut("spSoundArray", 8, "sounds\\") -- PLATEAUJUKEBOX.scr:112
    ctx:arrayPut("spSoundArray", 9, "sounds\\") -- PLATEAUJUKEBOX.scr:113
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:115
end

script.labels["CacheAllSounds"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:118
    ctx:state().nCounter = 0 -- PLATEAUJUKEBOX.scr:120
    while ctx:condition("nCounter<NUMSOUNDS") do -- PLATEAUJUKEBOX.scr:121
        ctx:arrayGet("spSoundArray", "nCounter", "sFileName") -- PLATEAUJUKEBOX.scr:122
        ctx:cacheSound("sFileName") -- PLATEAUJUKEBOX.scr:123
        ctx:set("nCounter", "nCounter + 1") -- PLATEAUJUKEBOX.scr:124
    end -- PLATEAUJUKEBOX.scr:125
    ctx:set("nCounter", "nCounter - 1") -- PLATEAUJUKEBOX.scr:126
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:128
end

return script
