-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BATTLEJUKEBOX.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "BaseGlobals.inc" }

-- BattleJukebox.scr
-- by SJR
-- 10-23-01
-- Purpose:handle all the sound
-- effects for a huge
-- battle. Attach to
-- ScriptObject.
-- Triggers:
-- "Play" = start the play loop
-- "Stop" = stop the loop
script.labels["Main"] = function(ctx)
    -- BATTLEJUKEBOX.scr:27
    ctx:wait(0, 1, "InitBattleJukebox") -- BATTLEJUKEBOX.scr:29
    mm9.gosub(script, ctx, "InitStrings") -- BATTLEJUKEBOX.scr:31
    mm9.gosub(script, ctx, "CacheAllSounds") -- BATTLEJUKEBOX.scr:32
    do return ctx:exit("TRUE") end -- BATTLEJUKEBOX.scr:34
end

script.labels["InitBattleJukebox"] = function(ctx)
    -- BATTLEJUKEBOX.scr:37
    ctx:state().bPlaying = false -- BATTLEJUKEBOX.scr:39
    ctx:state().nCurSound = 0 -- BATTLEJUKEBOX.scr:40
    ctx:addTrigger("Play", "StartPlayLoop") -- BATTLEJUKEBOX.scr:42
    ctx:addTrigger("Stop", "StopPlayLoop") -- BATTLEJUKEBOX.scr:43
    do return ctx:exit("TRUE") end -- BATTLEJUKEBOX.scr:45
end

script.labels["StartPlayLoop"] = function(ctx)
    -- BATTLEJUKEBOX.scr:48
    ctx:state().bPlaying = true -- BATTLEJUKEBOX.scr:50
    mm9.gosub(script, ctx, "PlayLoop") -- BATTLEJUKEBOX.scr:51
    do return ctx:exit("TRUE") end -- BATTLEJUKEBOX.scr:52
end

script.labels["PlayLoop"] = function(ctx)
    -- BATTLEJUKEBOX.scr:55
    if ctx:condition("bPlaying==FALSE") then -- BATTLEJUKEBOX.scr:57
        do return ctx:exit("TRUE") end -- BATTLEJUKEBOX.scr:58
    end -- BATTLEJUKEBOX.scr:59
    ctx:randomInt(0, "nCounter", "nCurSound") -- BATTLEJUKEBOX.scr:60
    ctx:arrayGet("spSounds", "nCurSound", "sTemp") -- BATTLEJUKEBOX.scr:61
    ctx:playSound("sTemp", "DoNothing", 1, 1000, "FALSE", 100) -- BATTLEJUKEBOX.scr:62
    ctx:randomFloat(0, 1, "nWait") -- BATTLEJUKEBOX.scr:63
    -- loop the sound
    ctx:wait(1, "nWait", "PlayLoop") -- BATTLEJUKEBOX.scr:65
    do return ctx:exit("TRUE") end -- BATTLEJUKEBOX.scr:66
end

script.labels["StopPlayLoop"] = function(ctx)
    -- BATTLEJUKEBOX.scr:69
    ctx:state().bPlaying = false -- BATTLEJUKEBOX.scr:71
    do return ctx:exit("TRUE") end -- BATTLEJUKEBOX.scr:72
end

script.labels["CacheAllSounds"] = function(ctx)
    -- BATTLEJUKEBOX.scr:75
    ctx:state().nCounter = 0 -- BATTLEJUKEBOX.scr:77
    while ctx:condition("nCounter<NUMSOUNDS") do -- BATTLEJUKEBOX.scr:78
        ctx:arrayGet("spSounds", "nCounter", "sTemp") -- BATTLEJUKEBOX.scr:79
        ctx:cacheSound("sTemp") -- BATTLEJUKEBOX.scr:80
        ctx:set("nCounter", "nCounter + 1") -- BATTLEJUKEBOX.scr:81
    end -- BATTLEJUKEBOX.scr:82
    ctx:set("nCounter", "nCounter - 1") -- BATTLEJUKEBOX.scr:83
    do return ctx:exit("TRUE") end -- BATTLEJUKEBOX.scr:84
end

script.labels["InitStrings"] = function(ctx)
    -- BATTLEJUKEBOX.scr:87
    ctx:arrayPut("spSounds", 0, "sounds\\Weapons\\nmetalhollow.wav") -- BATTLEJUKEBOX.scr:89
    ctx:arrayPut("spSounds", 1, "sounds\\Weapons\\SwordClang.wav") -- BATTLEJUKEBOX.scr:90
    ctx:arrayPut("spSounds", 2, "sounds\\Weapons\\ArrowImpact01.wav") -- BATTLEJUKEBOX.scr:91
    ctx:arrayPut("spSounds", 3, "sounds\\Weapons\\FleshHit01.wav") -- BATTLEJUKEBOX.scr:92
    ctx:arrayPut("spSounds", 4, "sounds\\Weapons\\FleshHit03.wav") -- BATTLEJUKEBOX.scr:93
    ctx:arrayPut("spSounds", 5, "sounds\\Weapons\\carmorchain.wav") -- BATTLEJUKEBOX.scr:94
    ctx:arrayPut("spSounds", 6, "sounds\\Weapons\\LargeMeleeSwish.wav") -- BATTLEJUKEBOX.scr:95
    ctx:arrayPut("spSounds", 7, "sounds\\Weapons\\cmetalsolid.wav") -- BATTLEJUKEBOX.scr:96
    ctx:arrayPut("spSounds", 8, "sounds\\AnimSounds\\SoldierWattack1.wav") -- BATTLEJUKEBOX.scr:97
    ctx:arrayPut("spSounds", 9, "sounds\\events\\metalhitmetal02.wav") -- BATTLEJUKEBOX.scr:98
    ctx:arrayPut("spSounds", 10, "sounds\\AnimSounds\\TrellborgWattack1.wav") -- BATTLEJUKEBOX.scr:99
    ctx:arrayPut("spSounds", 11, "sounds\\AnimSounds\\TrellborgWattack2.wav") -- BATTLEJUKEBOX.scr:100
    ctx:arrayPut("spSounds", 12, "sounds\\events\\metalmetal01.wav") -- BATTLEJUKEBOX.scr:101
    do return ctx:exit("TRUE") end -- BATTLEJUKEBOX.scr:103
end

return script
