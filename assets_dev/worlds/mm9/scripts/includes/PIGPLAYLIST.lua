-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PIGPLAYLIST.inc"
script.includes = {}
script.labels = {}


-- PigPlaylist.inc
-- by SJR
-- 12-12-01
-- Purpose:randomly play piggy
-- sounds.
script.labels["InitPigPlaylist"] = function(ctx)
    -- PIGPLAYLIST.inc:14
    ctx:arrayPut("spSounds", 0, "sounds\\animsounds\\pig\\die1.wav") -- PIGPLAYLIST.inc:16
    ctx:arrayPut("spSounds", 1, "sounds\\animsounds\\pig\\fidget1.wav") -- PIGPLAYLIST.inc:17
    ctx:arrayPut("spSounds", 2, "sounds\\animsounds\\pig\\fidget2.wav") -- PIGPLAYLIST.inc:18
    ctx:arrayPut("spSounds", 3, "sounds\\animsounds\\pig\\rest.wav") -- PIGPLAYLIST.inc:19
    ctx:arrayPut("spSounds", 4, "sounds\\animsounds\\pig\\roll.wav") -- PIGPLAYLIST.inc:20
    ctx:arrayPut("spSounds", 5, "sounds\\animsounds\\pig\\standdown.wav") -- PIGPLAYLIST.inc:21
    ctx:arrayPut("spSounds", 6, "sounds\\animsounds\\pig\\standup.wav") -- PIGPLAYLIST.inc:22
    ctx:arrayPut("spSounds", 7, "sounds\\animsounds\\pig\\wince1.wav") -- PIGPLAYLIST.inc:23
    ctx:arrayPut("spSounds", 8, "sounds\\animsounds\\pig\\wince2.wav") -- PIGPLAYLIST.inc:24
    ctx:cacheSound("sounds\\animsounds\\pig\\die1.wav") -- PIGPLAYLIST.inc:26
    ctx:cacheSound("sounds\\animsounds\\pig\\fidget1.wav") -- PIGPLAYLIST.inc:27
    ctx:cacheSound("sounds\\animsounds\\pig\\fidget2.wav") -- PIGPLAYLIST.inc:28
    ctx:cacheSound("sounds\\animsounds\\pig\\rest.wav") -- PIGPLAYLIST.inc:29
    ctx:cacheSound("sounds\\animsounds\\pig\\roll.wav") -- PIGPLAYLIST.inc:30
    ctx:cacheSound("sounds\\animsounds\\pig\\standdown.wav") -- PIGPLAYLIST.inc:31
    ctx:cacheSound("sounds\\animsounds\\pig\\standup.wav") -- PIGPLAYLIST.inc:32
    ctx:cacheSound("sounds\\animsounds\\pig\\wince1.wav") -- PIGPLAYLIST.inc:33
    ctx:cacheSound("sounds\\animsounds\\pig\\wince2.wav") -- PIGPLAYLIST.inc:34
    do return ctx:exit(1) end -- PIGPLAYLIST.inc:36
end

script.labels["PlayRandomPig"] = function(ctx)
    -- PIGPLAYLIST.inc:39
    ctx:randomInt(0, 8, "nIndex") -- PIGPLAYLIST.inc:41
    ctx:arrayGet("spSounds", "nIndex", "sSound") -- PIGPLAYLIST.inc:42
    ctx:playSound("sSound", "DoNothing", 1, 100, 0, 100) -- PIGPLAYLIST.inc:43
    do return ctx:exit(1) end -- PIGPLAYLIST.inc:45
end

script.labels["DoNothing"] = function(ctx)
    -- PIGPLAYLIST.inc:48
    do return ctx:exit(1) end -- PIGPLAYLIST.inc:50
end

return script
