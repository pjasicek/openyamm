-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PIGRACER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "PigPlaylist.inc" }

-- PigRacer.scr
-- by SJR
-- 12-11-01
-- Purpose:player rides this pig
-- during Thjorgard races.
script.labels["Main"] = function(ctx)
    -- PIGRACER.scr:32
    ctx:getParam(0, "sCameraName") -- PIGRACER.scr:34
    ctx:wait(0, 3, "InitPigRacer") -- PIGRACER.scr:36
    do return ctx:exit("TRUE") end -- PIGRACER.scr:38
end

script.labels["InitPigRacer"] = function(ctx)
    -- PIGRACER.scr:41
    mm9.gosub(script, ctx, "InitPigPlaylist") -- PIGRACER.scr:43
    -- AddTrigger Use, StartRacing
    ctx:state().hCamera = ctx:objectOrNil("sCameraName") -- PIGRACER.scr:49
    ctx:state().nTemp = ctx:self():getStat("RunVel") -- PIGRACER.scr:51
    ctx:set("nTemp", "nTemp * 8") -- PIGRACER.scr:52
    ctx:self():setStat("RunVel", "nTemp") -- PIGRACER.scr:53
    do return ctx:exit("TRUE") end -- PIGRACER.scr:55
end

script.labels["StartRacing"] = function(ctx)
    -- PIGRACER.scr:58
    ctx:state().bQuit = false -- PIGRACER.scr:60
    ctx:trigger("hCamera", "start") -- PIGRACER.scr:61
    ctx:removeTrigger("Use") -- PIGRACER.scr:62
    mm9.gosub(script, ctx, "RaceLoop") -- PIGRACER.scr:63
    mm9.gosub(script, ctx, "SoundLoop") -- PIGRACER.scr:64
    ctx:wait(0, 300, "EndRace") -- PIGRACER.scr:65
    do return ctx:exit("TRUE") end -- PIGRACER.scr:67
end

script.labels["RaceLoop"] = function(ctx)
    -- PIGRACER.scr:70
    if ctx:condition("bQuit==TRUE") then -- PIGRACER.scr:72
        -- AddTrigger Use, StartRacing
        do return ctx:exit("TRUE") end -- PIGRACER.scr:74
    end -- PIGRACER.scr:75
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:player():rotation() -- PIGRACER.scr:76
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- PIGRACER.scr:77
    ctx:self():faceDir("dx", "dy", "dz", 360) -- PIGRACER.scr:78
    ctx:self():run() -- PIGRACER.scr:79
    ctx:wait(0, .05, "RaceLoop") -- PIGRACER.scr:81
    do return ctx:exit("TRUE") end -- PIGRACER.scr:83
end

script.labels["SoundLoop"] = function(ctx)
    -- PIGRACER.scr:86
    mm9.gosub(script, ctx, "PlayRandomPig") -- PIGRACER.scr:88
    ctx:wait(1, 2, "SoundLoop") -- PIGRACER.scr:90
    do return ctx:exit("TRUE") end -- PIGRACER.scr:92
end

script.labels["EndRace"] = function(ctx)
    -- PIGRACER.scr:95
    ctx:state().bQuit = true -- PIGRACER.scr:97
    do return ctx:exit("TRUE") end -- PIGRACER.scr:99
end

return script
