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
    ctx:command("wait", "0, 5, InitDungeonJukebox") -- PLATEAUJUKEBOX.scr:39
    mm9.gosub(script, ctx, "InitStrings") -- PLATEAUJUKEBOX.scr:41
    mm9.gosub(script, ctx, "CacheAllSounds") -- PLATEAUJUKEBOX.scr:42
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:44
end

script.labels["InitDungeonJukebox"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:47
    ctx:command("getmyhandle", "hMe") -- PLATEAUJUKEBOX.scr:49
    ctx:command("getplayerhandle", "hPlayer") -- PLATEAUJUKEBOX.scr:50
    ctx:addTrigger("On", "TurnOn") -- PLATEAUJUKEBOX.scr:52
    ctx:addTrigger("Off", "TurnOff") -- PLATEAUJUKEBOX.scr:53
    mm9.gosub(script, ctx, "StartPlayLoop") -- PLATEAUJUKEBOX.scr:55
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:57
end

script.labels["StartPlayLoop"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:60
    ctx:command("getrandomint", "2, 8, dt") -- PLATEAUJUKEBOX.scr:62
    ctx:command("dt", "= dt * 60") -- PLATEAUJUKEBOX.scr:63
    ctx:command("wait", "0, dt, PlaySound") -- PLATEAUJUKEBOX.scr:64
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:66
end

script.labels["PlaySound"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:69
    if ctx:condition("bActive==FALSE") then -- PLATEAUJUKEBOX.scr:71
        do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:72
    end -- PLATEAUJUKEBOX.scr:73
    mm9.gosub(script, ctx, "UpdatePOS") -- PLATEAUJUKEBOX.scr:74
    ctx:command("getrandomint", "0, nCounter, nRandom") -- PLATEAUJUKEBOX.scr:75
    ctx:command("arrayget", "spSoundArray, nRandom, sFilename") -- PLATEAUJUKEBOX.scr:76
    ctx:command("playsound", "sFileName, StartPlayLoop, 1, 500, FALSE, 100") -- PLATEAUJUKEBOX.scr:77
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:79
end

script.labels["UpdatePOS"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:82
    ctx:command("getpos", "hPlayer, x,y,z") -- PLATEAUJUKEBOX.scr:84
    ctx:command("setpos", "hMe, x,y,z") -- PLATEAUJUKEBOX.scr:85
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:86
end

script.labels["TurnOn"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:89
    ctx:command("bactive", "= TRUE") -- PLATEAUJUKEBOX.scr:91
    mm9.gosub(script, ctx, "StartPlayLoop") -- PLATEAUJUKEBOX.scr:92
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:93
end

script.labels["TurnOff"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:96
    ctx:command("bactive", "= FALSE") -- PLATEAUJUKEBOX.scr:98
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:99
end

script.labels["InitStrings"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:102
    ctx:command("arrayput", "spSoundArray, 0, sounds\\") -- PLATEAUJUKEBOX.scr:104
    ctx:command("arrayput", "spSoundArray, 1, sounds\\") -- PLATEAUJUKEBOX.scr:105
    ctx:command("arrayput", "spSoundArray, 2, sounds\\") -- PLATEAUJUKEBOX.scr:106
    ctx:command("arrayput", "spSoundArray, 3, sounds\\") -- PLATEAUJUKEBOX.scr:107
    ctx:command("arrayput", "spSoundArray, 4, sounds\\") -- PLATEAUJUKEBOX.scr:108
    ctx:command("arrayput", "spSoundArray, 5, sounds\\") -- PLATEAUJUKEBOX.scr:109
    ctx:command("arrayput", "spSoundArray, 6, sounds\\") -- PLATEAUJUKEBOX.scr:110
    ctx:command("arrayput", "spSoundArray, 7, sounds\\") -- PLATEAUJUKEBOX.scr:111
    ctx:command("arrayput", "spSoundArray, 8, sounds\\") -- PLATEAUJUKEBOX.scr:112
    ctx:command("arrayput", "spSoundArray, 9, sounds\\") -- PLATEAUJUKEBOX.scr:113
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:115
end

script.labels["CacheAllSounds"] = function(ctx)
    -- PLATEAUJUKEBOX.scr:118
    ctx:command("ncounter", "= 0") -- PLATEAUJUKEBOX.scr:120
    while ctx:condition("nCounter<NUMSOUNDS") do -- PLATEAUJUKEBOX.scr:121
        ctx:command("arrayget", "spSoundArray, nCounter, sFileName") -- PLATEAUJUKEBOX.scr:122
        ctx:command("cachesound", "sFileName") -- PLATEAUJUKEBOX.scr:123
        ctx:command("ncounter", "= nCounter + 1") -- PLATEAUJUKEBOX.scr:124
    end -- PLATEAUJUKEBOX.scr:125
    ctx:command("ncounter", "= nCounter - 1") -- PLATEAUJUKEBOX.scr:126
    do return ctx:exit("TRUE") end -- PLATEAUJUKEBOX.scr:128
end

return script
